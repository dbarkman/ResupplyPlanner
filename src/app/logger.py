import logging
import sys
from .config import get_config

LOG_FILE = "logs/app.log"

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger instance.

    This function sets up a logger that writes to a file in the logs/ directory.
    The log level is read from the environment configuration. When run by
    systemd, this output will be captured by journald.

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

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger 