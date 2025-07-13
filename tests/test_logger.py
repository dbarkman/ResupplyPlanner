import pytest
from unittest.mock import patch
import logging

from src.app.logger import get_logger, TimedRotatingFileHandler

# This fixture will run before each test function in this file
@pytest.fixture(autouse=True)
def cleanup_logging():
    """Ensure a clean logging environment for each test."""
    manager = logging.root.manager
    for name in list(manager.loggerDict):
        # Check if the object is a logger before trying to modify it
        if isinstance(manager.loggerDict[name], logging.Logger):
            manager.loggerDict[name].handlers = []
            manager.loggerDict[name].propagate = True


@patch('src.app.logger.TimedRotatingFileHandler')
@patch('src.app.logger.get_config')
def test_get_logger_configures_new_logger(mock_get_config, mock_handler):
    """
    Tests that a new logger is correctly configured.
    """
    # Arrange
    def config_side_effect(key):
        if key == "RP_LOG_LEVEL": return "DEBUG"
        if key == "RP_LOG_RETENTION_DAYS": return "14"
        return None # Default case
    mock_get_config.side_effect = config_side_effect

    with patch.object(logging.Logger, 'hasHandlers', return_value=False):
        # Act
        log = get_logger("new_logger_for_test")

        # Assert
        assert log.level == logging.DEBUG
        assert mock_get_config.call_count == 2
        mock_handler.assert_called_once_with(
            "logs/app.log",
            when='midnight',
            interval=1,
            backupCount=14
        )
        assert len(log.handlers) == 1


@patch('src.app.logger.get_config')
def test_get_logger_returns_existing_logger(mock_get_config):
    """
    Tests that a pre-configured logger is returned without changes.
    """
    # Arrange
    with patch.object(logging.Logger, 'hasHandlers', return_value=True):
        # Still need to mock get_config as it's called before the check
        def config_side_effect(key):
            if key == "RP_LOG_LEVEL": return "INFO"
            if key == "RP_LOG_RETENTION_DAYS": return "7"
            return None
        mock_get_config.side_effect = config_side_effect

        # Act
        log = get_logger("existing_logger_for_test")

        # Assert
        # Check that no NEW handlers were added.
        # The logger instance is created by getLogger, so it will exist
        # but the hasHandlers mock prevents our code from adding to it.
        assert len(log.handlers) == 0 