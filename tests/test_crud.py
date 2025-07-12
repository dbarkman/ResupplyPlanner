from unittest.mock import MagicMock
from app import crud, models


def test_get_system_by_name():
    """
    Tests that get_system_by_name constructs the correct query.

    This test uses a mock database session to verify that the function calls
    the expected SQLAlchemy query methods, ensuring our data access logic
    is correct without requiring a live database connection.
    """
    # Create a mock session
    mock_db = MagicMock()

    # Create a mock query object that returns a mock result
    mock_query = mock_db.query.return_value
    mock_filtered_query = mock_query.filter.return_value

    # Call the function with the mock session
    crud.get_system_by_name(mock_db, "Sol")

    # Assert that the correct query was built
    mock_db.query.assert_called_once_with(models.System)
    mock_query.filter.assert_called_once()
    mock_filtered_query.first.assert_called_once() 