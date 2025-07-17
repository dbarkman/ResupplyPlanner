#!/usr/bin/env python
import sys
import os
import gzip
import ijson
import csv
from datetime import datetime

# Add project root to allow importing from our app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.app.logger import get_logger

logger = get_logger(__name__)

def parse_timestamp(timestamp_str: str) -> str:
    """
    Parses the specific timestamp format from the JSON file and returns
    it in a format that PostgreSQL's COPY command can understand.
    """
    try:
        # Correct non-standard timezone format like '+00'
        if timestamp_str and len(timestamp_str) == 22 and timestamp_str[19] in ('+', '-'):
            timestamp_str = timestamp_str + "00"
        # Parse to datetime object
        dt_obj = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S%z')
        # Format to ISO 8601 string, which COPY handles well
        return dt_obj.isoformat()
    except (ValueError, TypeError) as e:
        logger.error(f"Could not parse timestamp: '{timestamp_str}'. Error: {e}")
        return ''

def main():
    """Main conversion logic."""
    input_file = './data/systems.json.gz'
    output_file = './data/systems.csv'
    processed_count = 0

    logger.info(f"Starting conversion of {input_file} to {output_file}...")

    try:
        with gzip.open(input_file, 'rb') as f_in, open(output_file, 'w', newline='', encoding='utf-8') as f_out:
            records = ijson.items(f_in, 'item')
            writer = csv.writer(f_out)

            for record in records:
                processed_count += 1
                if processed_count % 1000000 == 0:
                    logger.info(f"Processed {processed_count:,} records...")

                # --- Extract and Validate Data ---
                system_address = record.get("id64")
                name = record.get("name")
                coords = record.get("coords")
                update_time_str = record.get("updateTime")
                requires_permit = record.get("requiresPermit", False) # Default to false

                if not all([system_address, name, coords, update_time_str]):
                    logger.warning(f"Skipping incomplete record at count {processed_count}: {record}")
                    continue

                update_time = parse_timestamp(update_time_str)
                if not update_time:
                    continue

                # --- Prepare data for CSV ---
                coord_x = coords.get("x")
                coord_y = coords.get("y")
                coord_z = coords.get("z")

                # Format the PostGIS point in Well-Known Text (WKT) format
                # SRID=0;POINTZ(x y z)
                wkt_point = f"SRID=0;POINTZ({coord_x} {coord_y} {coord_z})"
                
                writer.writerow([
                    system_address,
                    name,
                    coord_x,
                    coord_y,
                    coord_z,
                    wkt_point,
                    requires_permit,
                    update_time
                ])

    except FileNotFoundError:
        logger.error(f"Error: The input file '{input_file}' was not found.")
        return
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return

    logger.info(f"--- Conversion Summary ---")
    logger.info(f"Total records written: {processed_count:,}")
    logger.info(f"Output file created: {output_file}")
    logger.info("--------------------------")

if __name__ == "__main__":
    main() 