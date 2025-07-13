import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Assuming run_listener is in the src directory and tests are run from the project root
from src.run_listener import parse_and_update_system, parse_and_update_station_commodities
from src.app.models import System, Station

# Sample timestamps for testing
NOW = datetime.now(timezone.utc)
OLDER_TIMESTAMP = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
NEWER_TIMESTAMP = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

# --- Tests for parse_and_update_system ---

@patch('src.run_listener.get_system_by_address')
@patch('src.run_listener.create_or_update_system')
def test_parse_system_happy_path(mock_create_or_update, mock_get_system):
    """
    Tests that a valid system message correctly calls the CRUD function.
    """
    mock_db = Mock()
    mock_get_system.return_value = None  # No existing system

    message_body = {
        "SystemAddress": 12345,
        "StarSystem": "Sol",
        "StarPos": [0.0, 0.0, 0.0],
        "event": "FSDJump"
    }

    result = parse_and_update_system(mock_db, message_body, NEWER_TIMESTAMP)

    assert result is True
    mock_get_system.assert_called_once_with(mock_db, 12345)
    mock_create_or_update.assert_called_once_with(
        db=mock_db,
        system_address=12345,
        name="Sol",
        x=0.0,
        y=0.0,
        z=0.0,
        updated_at=NEWER_TIMESTAMP
    )

@patch('src.run_listener.get_system_by_address')
@patch('src.run_listener.create_or_update_system')
def test_parse_system_stale_data(mock_create_or_update, mock_get_system):
    """
    Tests that a stale system message is correctly ignored.
    """
    mock_db = Mock()
    # Mock an existing system with a newer timestamp
    mock_system = System(updated_at=NEWER_TIMESTAMP)
    mock_get_system.return_value = mock_system

    message_body = {"SystemAddress": 12345}

    result = parse_and_update_system(mock_db, message_body, OLDER_TIMESTAMP)

    assert result is False
    mock_get_system.assert_called_once_with(mock_db, 12345)
    mock_create_or_update.assert_not_called()


# --- Tests for parse_and_update_station_commodities ---

@patch('src.run_listener.create_or_update_station_commodities')
@patch('src.run_listener.get_or_create_station')
def test_parse_station_commodities_happy_path(mock_get_station, mock_create_commodities):
    """
    Tests that a valid commodity message correctly calls the CRUD functions.
    """
    mock_db = Mock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None # No existing station

    message_body = {
        "marketId": 67890,
        "stationName": "Jameson Memorial",
        "systemName": "Shinrarta Dezhra",
        "prohibited": ["Slaves"],
        "commodities": [{"name": "tritium", "stock": 100}]
    }

    result = parse_and_update_station_commodities(mock_db, message_body, NEWER_TIMESTAMP)

    assert result is True
    mock_get_station.assert_called_once()
    mock_create_commodities.assert_called_once()


@patch('src.run_listener.get_or_create_station')
def test_parse_station_commodities_stale_data(mock_get_station):
    """
    Tests that a stale commodity message is correctly ignored.
    """
    mock_db = Mock()
    # Mock an existing station with a newer timestamp
    mock_station = Station(updated_at=NEWER_TIMESTAMP)
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_station

    message_body = {"marketId": 67890}

    result = parse_and_update_station_commodities(mock_db, message_body, OLDER_TIMESTAMP)

    assert result is False
    mock_get_station.assert_not_called() # Should not proceed to station creation/update

def test_parse_station_commodities_bad_data():
    """
    Tests that commodity messages with missing critical keys are ignored.
    """
    mock_db = Mock()

    # --- Test cases for missing keys ---
    # Case 1: Missing marketId
    message_no_marketid = {"stationName": "A", "systemName": "B"}
    assert parse_and_update_station_commodities(mock_db, message_no_marketid, NOW) is False

    # Set up the mock to handle subsequent calls that have a marketId
    # This mock will return an object that can be checked for an 'updated_at' attribute.
    mock_station = Mock()
    mock_station.updated_at = OLDER_TIMESTAMP # Allows the '>=' comparison to work
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_station

    # Case 2: Missing stationName
    message_no_station = {"marketId": 1, "systemName": "B"}
    assert parse_and_update_station_commodities(mock_db, message_no_station, NOW) is False

    # Case 3: Missing systemName
    message_no_system = {"marketId": 1, "stationName": "A"}
    assert parse_and_update_station_commodities(mock_db, message_no_system, NOW) is False 