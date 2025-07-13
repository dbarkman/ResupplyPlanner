import pytest
from unittest.mock import patch, MagicMock

# Import the function to be tested
from src.app.database import get_db

@patch('src.app.database.SessionLocal')
def test_get_db_closes_session_on_success(mock_session_local):
    """
    Tests that the database session is closed after the 'with' block exits successfully.
    """
    # Arrange
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    # Act
    with get_db() as db:
        # Simulate some work with the database
        assert db == mock_session
    
    # Assert
    mock_session.close.assert_called_once()

@patch('src.app.database.SessionLocal')
def test_get_db_closes_session_on_exception(mock_session_local):
    """
    Tests that the database session is closed even if an exception occurs.
    This covers the 'finally' block.
    """
    # Arrange
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    
    # Act and Assert
    with pytest.raises(ValueError, match="Test exception"):
        with get_db() as db:
            assert db == mock_session
            raise ValueError("Test exception")
            
    # Assert that close was still called
    mock_session.close.assert_called_once() 