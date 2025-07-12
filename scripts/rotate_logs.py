#!/usr/bin/env python
import os
import glob
from datetime import datetime, timedelta
from src.app.config import get_config

# Configuration
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
RETENTION_DAYS = int(get_config("RP_LOG_RETENTION_DAYS"))

def rotate_logs():
    """
    Rotates the main application log file and cleans up old logs.
    """
    print("Log rotation script started.")

    if not os.path.exists(LOG_FILE):
        print(f"Log file not found at {LOG_FILE}. Nothing to rotate.")
        return

    # 1. Rename the current log file with a timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d')
    rotated_log_path = f"{LOG_FILE}.{timestamp}"

    # Avoid overwriting if script is run multiple times a day
    if os.path.exists(rotated_log_path):
        print(f"Rotated log {rotated_log_path} already exists. Skipping rotation.")
    else:
        os.rename(LOG_FILE, rotated_log_path)
        print(f"Rotated {LOG_FILE} to {rotated_log_path}")

    # 2. Clean up old logs
    print(f"Cleaning up logs older than {RETENTION_DAYS} days.")
    log_pattern = os.path.join(LOG_DIR, 'app.log.*')
    log_files = glob.glob(log_pattern)
    
    # Sort files by date in the filename
    log_files.sort(key=lambda name: os.path.getmtime(name), reverse=True)

    if len(log_files) > RETENTION_DAYS:
        files_to_delete = log_files[RETENTION_DAYS:]
        for f in files_to_delete:
            print(f"Deleting old log file: {f}")
            os.remove(f)
    else:
        print("No old logs to delete.")

    print("Log rotation script finished.")


if __name__ == "__main__":
    rotate_logs() 