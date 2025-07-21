#!/usr/bin/env python3

"""
Export all system names from the database to a text file for fast autocomplete.
This creates a simple, sorted list of system names that can be loaded into memory.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.database import get_db
from src.app.models import System


def export_system_names(output_file: str = "data/system_names.txt", test_mode: bool = False):
    """
    Export all system names from the database to a text file.
    
    Args:
        output_file: Path to the output file (default: data/system_names.txt)
        test_mode: If True, only export Sol for testing
    """
    # Ensure the output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Exporting system names to {output_file}...")
    if test_mode:
        print("TEST MODE: Only exporting Sol")
    
    try:
        print("Connecting to database...")
        with get_db() as db:
            print("Database connection successful")
            
            # Open file for writing
            print("Opening output file...")
            with open(output_path, 'w', encoding='utf-8') as f:
                if test_mode:
                    # Test mode: only export Sol
                    print("Querying for Sol...")
                    query = db.query(System.name).filter(System.name == "Sol")
                else:
                    # Query all system names, ordered alphabetically
                    print("Querying database for all system names...")
                    query = db.query(System.name).order_by(System.name)
                
                # Stream results and write one at a time
                print("Streaming and writing systems...")
                total_systems = 0
                for system in query.yield_per(1000):  # Process in batches of 1000
                    f.write(f"{system.name}\n")
                    total_systems += 1
                    
                    # Progress indicator every 10,000 systems
                    if total_systems % 10000 == 0:
                        print(f"  Processed {total_systems:,} systems...")
                
                print(f"Found and wrote {total_systems:,} systems")
            
            # Verify the file
            file_size = output_path.stat().st_size
            print(f"Export complete!")
            print(f"File: {output_path}")
            print(f"Size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")
            print(f"Systems: {total_systems:,}")
            
            # Show a few examples by reading the file
            print(f"\nFirst few systems in file:")
            with open(output_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i < 5:
                        print(f"  {line.strip()}")
                    else:
                        break
                if total_systems > 5 and not test_mode:
                    print(f"  ...")
                    # Read last line
                    f.seek(0)
                    lines = f.readlines()
                    if lines:
                        print(f"  {lines[-1].strip()}")
    
    except Exception as e:
        print(f"Database error: {e}")
        raise


def main():
    """Main function to run the export."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export system names for autocomplete")
    parser.add_argument(
        "--output", 
        default="data/system_names.txt",
        help="Output file path (default: data/system_names.txt)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: only export Sol"
    )
    
    args = parser.parse_args()
    
    try:
        export_system_names(args.output, args.test)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 