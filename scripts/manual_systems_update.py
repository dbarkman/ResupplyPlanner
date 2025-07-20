#!/usr/bin/env python
import argparse
import json
import signal
import sys
import os
from datetime import datetime
import ijson # Import the ijson library
import gzip # Import the gzip library

# Add project root to the Python path to allow importing from 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from sqlalchemy import text # Import text for executing raw SQL
from geoalchemy2.functions import ST_MakePoint
from src.app.database import get_db
from src.app.crud import bulk_upsert_systems # Import the new bulk function
from src.app.logger import get_logger
import logging # Import the logging module

# --- Globals ---
logger = get_logger(__name__)
# Add a console handler for this specific script
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(console_handler)

shutdown_flag = False
# ---------------

def signal_handler(signum, frame):
    """Signal handler to set the shutdown_flag for graceful exit."""
    global shutdown_flag
    if not shutdown_flag:
        shutdown_flag = True
        logger.info("Shutdown signal received. Finishing current batch and exiting...")

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parses the specific timestamp format from the JSON file."""
    try:
        # The timestamp might have a non-standard timezone format like '+00'
        # instead of the standard '+0000'. We correct it before parsing.
        if timestamp_str and len(timestamp_str) == 22 and timestamp_str[19] in ('+', '-'):
            timestamp_str = timestamp_str + "00"

        # The format is 'YYYY-MM-DD HH:MM:SS+0000' which strptime can handle with %z
        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S%z')
    except (ValueError, TypeError) as e:
        logger.error(f"Could not parse timestamp: '{timestamp_str}'. Error: {e}")
        return None

def run_import(db: Session, args: argparse.Namespace):
    """
    Main import logic. Reads the file and upserts records into the database.
    """
    global shutdown_flag
    processed_count = 0
    upserted_count = 0
    batch_size = 1000  # How many records to process in a single batch
    systems_batch = [] # A list to hold records for the current batch

    try:
        # Open the file using gzip.open for transparent decompression
        with gzip.open(args.file_path, 'rb') as f:
            logger.info(f"Starting import from compressed file {args.file_path}...")
            # Use ijson.items to stream the array of objects
            records = ijson.items(f, 'item')
            for record in records:
                if shutdown_flag:
                    break
                
                if args.limit and processed_count >= args.limit:
                    logger.info(f"Reached record limit of {args.limit}.")
                    break

                processed_count += 1
                
                # --- Extract and Validate Data ---
                system_address = record.get("id64")
                name = record.get("name")
                coords = record.get("coords")
                update_time_str = record.get("updateTime")
                
                if not all([system_address, name, coords, update_time_str]):
                    logger.warning(f"Skipping incomplete record on line {processed_count}: {record}")
                    continue

                update_time = parse_timestamp(update_time_str)
                if not update_time:
                    continue

                # --- Prepare data for the batch ---
                # Use sentinel values if coordinates are missing.
                coord_x = coords.get("x") if coords.get("x") is not None else 999999.999
                coord_y = coords.get("y") if coords.get("y") is not None else 999999.999
                coord_z = coords.get("z") if coords.get("z") is not None else 999999.999

                systems_batch.append({
                    "system_address": system_address,
                    "name": name,
                    "x": coord_x,
                    "y": coord_y,
                    "z": coord_z,
                    "coords": ST_MakePoint(coord_x, coord_y, coord_z, srid=0),
                    "updated_at": update_time
                })

                # If batch is full, process it
                if len(systems_batch) >= batch_size:
                    if args.dry_run:
                        # In dry-run, we just report what we would do and exit.
                        logger.info(f"[Dry Run] Would process a batch of {len(systems_batch)} records.")
                        upserted_count = len(systems_batch)
                        return processed_count, upserted_count, 0 # Return fake counts

                    rows_affected = bulk_upsert_systems(db, systems_batch)
                    db.commit() # Commit after each successful batch
                    upserted_count += rows_affected
                    logger.info(f"Processed {processed_count} records. Batch of {len(systems_batch)} sent. {rows_affected} rows affected.")
                    systems_batch = [] # Reset the batch
            
            # --- Process the final, smaller batch ---
            if systems_batch and not shutdown_flag:
                if args.dry_run:
                    logger.info(f"[Dry Run] Would process a final batch of {len(systems_batch)} records.")
                    upserted_count += len(systems_batch)
                else:
                    rows_affected = bulk_upsert_systems(db, systems_batch)
                    db.commit()
                    upserted_count += rows_affected
                    logger.info(f"Processed final batch of {len(systems_batch)}. {rows_affected} rows affected.")

    except FileNotFoundError:
        logger.error(f"Error: The file '{args.file_path}' was not found.")
        return 0, 0, 0
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        db.rollback()
    finally:
        logger.info("Import process finished.")
    
    # The number of skipped records is now inferred, not counted one-by-one
    skipped_count = processed_count - upserted_count
    return processed_count, upserted_count, skipped_count


def main():
    """Main entry point for the script."""
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Manual import of systems from a compressed JSON file.")

    parser.add_argument(
        "file_path",
        help="Path to the compressed systems.json.gz file to import."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the import of the first batch without committing to the database."
    )
    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="Limit the number of records to process."
    )

    args = parser.parse_args()

    # --- Signal Handling for Graceful Shutdown ---
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # --- Database Session and Execution ---
    processed = 0
    upserted = 0
    skipped = 0
    
    with get_db() as db:
            try:
                processed, upserted, skipped = run_import(db, args)
            except Exception as e:
                logger.error(f"A critical error occurred in the main execution block: {e}")
                db.rollback()
            finally:
                if args.dry_run:
                    logger.info("Dry run finished. Rolling back any potential changes.")
                    db.rollback()
                
                logger.info("--- Import Summary ---")
                logger.info(f"Total records reviewed: {processed}")
                logger.info(f"Records upserted:     {upserted}")
                logger.info(f"Records skipped:        {skipped}")
                logger.info("----------------------")


if __name__ == "__main__":
    main() 