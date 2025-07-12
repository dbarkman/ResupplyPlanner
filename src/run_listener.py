#!/usr/bin/env python
import zmq
import zlib
import json
import time
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.app.config import get_config
from .app.database import get_db
from .app.crud import get_system_by_address, create_or_update_system
from .app.logger import get_logger

# ZMQ and EDDN details
EDDN_RELAY = str(get_config("RP_EDDN_RELAY"))
TIMEOUT = int(get_config("RP_EDDN_RELAY_TIMEOUT"))

# Logger setup
logger = get_logger(__name__)

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

def main():
    """Main process loop for the EDDN listener."""
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, TIMEOUT)
    
    processed_count = 0
    accepted_count = 0

    while True:
        try:
            subscriber.connect(EDDN_RELAY)
            logger.info(f"Connected to EDDN relay at {EDDN_RELAY}")

            while True:
                try:
                    raw_message = subscriber.recv()
                    if not raw_message:
                        subscriber.disconnect(EDDN_RELAY)
                        logger.warning(f"Connection timed out, attempting to reconnect...")
                        break 

                    message = json.loads(zlib.decompress(raw_message))
                    processed_count += 1

                    schema = message.get("$schemaRef", "")
                    logger.debug(f"Received message with schema: {schema}")

                    if schema not in SUPPORTED_SCHEMAS:
                        continue
                    
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
                            continue
                    
                    with get_db() as db:
                        if parse_and_update_system(db, message_body, message_timestamp):
                            accepted_count += 1
                    # db = next(get_db())
                    # if parse_and_update_system(db, message_body, message_timestamp):
                    #     accepted_count += 1
                    
                    if processed_count % 100 == 0:
                        logger.info(f"Health Report: Processed={processed_count}, Accepted={accepted_count}")

                except zmq.ZMQError as e:
                    logger.error(f"ZMQ Error: {e}. Reconnecting...")
                    subscriber.disconnect(EDDN_RELAY)
                    time.sleep(5)
                    break
                except json.JSONDecodeError:
                    logger.warning("Failed to decode JSON from message.")
                    continue
                except Exception as e:
                    logger.error(f"An unexpected error occurred in the listener loop: {e}", exc_info=True)
                    # Optional: add a small delay to prevent rapid-fire errors
                    time.sleep(1)


        except KeyboardInterrupt:
            logger.info("Listener shutting down by user request.")
            sys.exit(0)
        except Exception as e:
            logger.critical(f"A critical error occurred: {e}. Restarting connection loop in 10 seconds.", exc_info=True)
            time.sleep(10)

if __name__ == "__main__":
    main() 