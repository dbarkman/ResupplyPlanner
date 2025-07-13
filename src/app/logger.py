import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from .config import get_config

LOG_FILE = "logs/app.log"

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger instance.
    This logger uses a TimedRotatingFileHandler to automatically rotate logs.
    """
    # Get configuration from environment
    log_level_str = get_config("RP_LOG_LEVEL").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    retention_days = int(get_config("RP_LOG_RETENTION_DAYS"))

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if the logger is already configured
    if logger.hasHandlers():
        return logger

    # Create a rotating file handler
    # This will rotate the log file every day at midnight and keep N backups.
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=retention_days
    )
    handler.setLevel(log_level)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger 