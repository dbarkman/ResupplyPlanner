#!/usr/bin/env python
import zmq
import zlib
import json
import time
import sys
import signal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import sdnotify
from .app.config import get_config
from .app.database import get_db
from .app.models import Station
from .app.crud import (
    get_system_by_address,
    create_or_update_system,
    get_or_create_station,
    create_or_update_station_commodities
)
from .app.logger import get_logger

# ZMQ and EDDN details
EDDN_RELAY = str(get_config("RP_EDDN_RELAY"))
TIMEOUT = int(get_config("RP_EDDN_RELAY_TIMEOUT"))

# Logger setup
logger = get_logger(__name__)

# --- Graceful Shutdown ---
shutdown_flag = False
def signal_handler(signum, frame):
    """Set the shutdown_flag to True to gracefully exit the loop."""
    global shutdown_flag
    shutdown_flag = True
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
# -------------------------

# Schemas we are interested in
SUPPORTED_SCHEMAS = {
    "https://eddn.edcd.io/schemas/journal/1",
    "https://eddn.edcd.io/schemas/fssallbodiesfound/1",
    "https://eddn.edcd.io/schemas/navroute/1",
    "https://eddn.edcd.io/schemas/approachsettlement/1",
    "https://eddn.edcd.io/schemas/codexentry/1",
    "https://eddn.edcd.io/schemas/fssbodysignals/1",
    "https://eddn.edcd.io/schemas/fssdiscoveryscan/1",
    "https://eddn.edcd.io/schemas/fsssignaldiscovered/1",
    "https://eddn.edcd.io/schemas/navbeaconscan/1",
    "https://eddn.edcd.io/schemas/scanbarycentre/1",
    "https://eddn.edcd.io/schemas/commodity/3",
}

COMMODITY_SCHEMA_REF = "https://eddn.edcd.io/schemas/commodity/3"

def parse_and_update_system(db: Session, message_body: dict, message_timestamp: datetime):
    """
    Parses a message body for system data and updates the database.
    Handles different message structures like single entries and lists (e.g., NavRoute).
    """
    system_address = message_body.get("SystemAddress")
    
    # Handle NavRoute schema which contains a list of systems
    if "Route" in message_body and isinstance(message_body["Route"], list):
        updated_count = 0
        for route_item in message_body["Route"]:
            if "SystemAddress" in route_item:
                if parse_and_update_system(db, route_item, message_timestamp):
                    updated_count += 1
        return updated_count > 0

    if not system_address:
        logger.debug(f"Skipping message (no SystemAddress). Event: {message_body.get('event')}, Keys: {list(message_body.keys())}")
        return False

    existing_system = get_system_by_address(db, system_address)

    if existing_system and existing_system.updated_at >= message_timestamp:
        logger.debug(f"Skipping update for {system_address}, data is not newer. DB: {existing_system.updated_at}, MSG: {message_timestamp}")
        return False
    
    name = message_body.get("StarSystem") or message_body.get("System")
    coords = message_body.get("StarPos")
    
    x, y, z = (coords[0], coords[1], coords[2]) if coords and len(coords) == 3 else (None, None, None)

    logger.info(f"System: {system_address}, Name: {name}, Coords: {coords}, Timestamp: {message_timestamp}")

    create_or_update_system(
        db=db,
        system_address=system_address,
        name=name,
        x=x,
        y=y,
        z=z,
        updated_at=message_timestamp,
    )
    return True

def parse_and_update_station_commodities(db: Session, message_body: dict, message_timestamp: datetime):
    """
    Parses a commodity message body for station and commodity data and updates the database.
    """
    market_id = message_body.get("marketId")
    if not market_id:
        logger.debug(f"Skipping commodity message (no marketId).")
        return False

    # Check for stale data before proceeding
    existing_station = db.query(Station).filter_by(market_id=market_id).first()
    if existing_station and existing_station.updated_at >= message_timestamp:
        logger.info(f"Skipping stale commodity data for station {market_id}. DB: {existing_station.updated_at}, MSG: {message_timestamp}")
        return False # Return False to be counted as 'ignored'
        
    station_name = message_body.get("stationName")
    system_name = message_body.get("systemName")
    prohibited = message_body.get("prohibited")
    commodities_data = message_body.get("commodities", [])

    if not station_name or not system_name:
        logger.debug(f"Skipping commodity message for market {market_id} (missing station or system name).")
        return False

    # First, create or update the station itself
    get_or_create_station(
        db=db,
        market_id=market_id,
        name=station_name,
        system_name=system_name,
        prohibited=prohibited,
        updated_at=message_timestamp,
    )

    # Next, perform the bulk upsert for all commodities at that station
    create_or_update_station_commodities(
        db=db,
        market_id=market_id,
        commodities_data=commodities_data,
        timestamp=message_timestamp,
    )
    
    # The commit is now handled by the 'with get_db()' context manager in main().
    logger.info(f"Processed {len(commodities_data)} commodities for station: {station_name}")
    return True


def process_eddn_message(message: dict):
    """
    Processes a single EDDN message, handling routing and database updates.

    Args:
        message: The decoded JSON message from EDDN.

    Returns:
        A tuple (accepted: bool, ignored: bool) indicating the result.
    """
    schema = message.get("$schemaRef", "")
    logger.debug(f"Received message with schema: {schema}")

    # This block is essential and needs to be outside the routing logic
    header_body = message.get("header", {})
    message_body = message.get("message", {})
    if "timestamp" in message_body:
        message_timestamp = datetime.fromisoformat(message_body["timestamp"].replace("Z", "+00:00"))
    else:
        gateway_timestamp = header_body.get("gatewayTimestamp")
        if gateway_timestamp:
            message_timestamp = datetime.fromisoformat(gateway_timestamp.replace("Z", "+00:00"))
            logger.debug("Message body missing 'timestamp', using 'gatewayTimestamp' from header instead.")
        else:
            logger.warning("Skipping message, both 'timestamp' in body and 'gatewayTimestamp' in header are missing.")
            return False, True # Ignored

    # --- ROUTING LOGIC ---
    if schema in SUPPORTED_SCHEMAS:
        with get_db() as db:
            success = False
            if schema == COMMODITY_SCHEMA_REF:
                # Handle commodity schema
                success = parse_and_update_station_commodities(db, message_body, message_timestamp)
            else: # Other supported schemas
                # Handle other supported schemas (system updates)
                success = parse_and_update_system(db, message_body, message_timestamp)

            if success:
                db.commit()  # Commit the transaction on success
                return True, False # Accepted
            else:
                return False, True # Ignored
    else:
        return False, True # Ignored


def main():
    """Main process loop for the EDDN listener."""
    # Graceful Shutdown Setup: Handle SIGINT (Ctrl+C) and SIGTERM (systemd)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, TIMEOUT)

    # Initialize systemd notifier
    notifier = sdnotify.SystemdNotifier()

    # Connect once and let ZMQ handle reconnections automatically.
    subscriber.connect(EDDN_RELAY)
    logger.info(f"Connected to EDDN relay at {EDDN_RELAY}")

    # Initialize counters for stats and reporting
    processed_count = 0
    accepted_count = 0
    ignored_count = 0
    last_report_minute = -1  # Start with a non-minute value

    # Notify systemd we are ready
    notifier.notify("READY=1")

    while not shutdown_flag:
        try:
            # Notify systemd that the service is healthy before waiting for a message
            notifier.notify("WATCHDOG=1")

            # Use polling with a timeout to be responsive to the shutdown_flag
            if not subscriber.poll(timeout=1000):
                continue # Timeout, loop back to check shutdown_flag

            raw_message = subscriber.recv()
            if not raw_message:
                # This case is unlikely with poll but included for safety
                continue

            message = json.loads(zlib.decompress(raw_message))
            processed_count += 1

            accepted, ignored = process_eddn_message(message)
            if accepted:
                accepted_count += 1
            if ignored:
                ignored_count += 1
            
            # Time-based reporting on the quarter-hour
            now = datetime.now(timezone.utc)
            current_minute = now.minute
            
            if current_minute in [0, 15, 30, 45] and current_minute != last_report_minute:
                logger.info(f"Health Report (15m): Processed={processed_count}, Accepted={accepted_count}, Ignored={ignored_count}")
                # Reset counters for the next interval
                processed_count = 0
                accepted_count = 0
                ignored_count = 0
                last_report_minute = current_minute

        except json.JSONDecodeError:
            logger.warning("Failed to decode JSON from message.")
            continue
        except Exception as e:
            logger.error(f"An unexpected error occurred in the listener loop: {e}", exc_info=True)
            # Add a small delay to prevent rapid-fire errors if the loop processes invalid data.
            time.sleep(1)

    # --- Graceful Shutdown Cleanup ---
    logger.info("Listener loop exited. Cleaning up resources...")
    subscriber.close()
    context.term()
    logger.info("Shutdown complete.")
    sys.exit(0)


if __name__ == "__main__":
    main() 