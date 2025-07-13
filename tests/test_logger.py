import pytest
from unittest.mock import patch
import logging

from src.app.logger import get_logger

# This fixture will run before each test function in this file
@pytest.fixture(autouse=True)
def cleanup_logging():
    """Ensure a clean logging environment for each test."""
    manager = logging.root.manager
    for name in list(manager.loggerDict):
        logger = manager.loggerDict[name]
        if isinstance(logger, logging.Logger):
            logger.handlers = []


@patch('src.app.logger.logging.FileHandler')
@patch('src.app.logger.get_config')
def test_get_logger_configures_new_logger(mock_get_config, mock_file_handler):
    """
    Tests that a new logger is correctly configured when it has no handlers.
    """
    # Arrange
    # Patch hasHandlers on the specific logger instance that will be created
    with patch.object(logging.Logger, 'hasHandlers', return_value=False):
        mock_get_config.return_value = "INFO"
        
        # Act
        log = get_logger("a_new_logger")

        # Assert
        assert log.level == logging.INFO
        mock_get_config.assert_called_once_with("RP_LOG_LEVEL")
        mock_file_handler.assert_called_once_with("logs/app.log")
        assert len(log.handlers) == 1


@patch('src.app.logger.get_config')
def test_get_logger_returns_existing_logger(mock_get_config):
    """
    Tests that a pre-configured logger is returned without changes.
    """
    # Arrange
    # Patch hasHandlers on the specific logger instance
    with patch.object(logging.Logger, 'hasHandlers', return_value=True):
        # Even though we expect an early return, we must still mock get_config
        # because it is called unconditionally *before* the hasHandlers check.
        mock_get_config.return_value = "INFO"

        # Act
        log = get_logger("an_existing_logger")

        # Assert
        assert len(log.handlers) == 0 # No new handlers were added 