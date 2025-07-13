import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app import crud, models
from src.app.database import Base


def test_get_system_by_name_mocked():
    """
    Tests that get_system_by_name constructs the correct query using a mock session.
    """
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_filtered_query = mock_query.filter.return_value
    crud.get_system_by_name(mock_db, "Sol")
    mock_db.query.assert_called_once_with(models.System)
    mock_query.filter.assert_called_once()
    mock_filtered_query.first.assert_called_once() 