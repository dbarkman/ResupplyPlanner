import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from .config import get_config

LOG_FILE = "logs/app.log"

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger instance.

    This function sets up a logger that writes to both the console (stdout)
    and a file in the logs/ directory. The log level is read from the
    environment configuration.

    Args:
        name: The name of the logger, typically __name__ from the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    log_level_str = get_config("RP_LOG_LEVEL").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if logger is already configured
    if logger.hasHandlers():
        return logger

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger 