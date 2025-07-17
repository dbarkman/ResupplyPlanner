import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app import crud, models
from src.app.database import Base
import unittest.mock


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

def test_get_system_by_address_mocked():
    """
    Tests that get_system_by_address constructs the correct query.
    """
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_filtered_query = mock_query.filter.return_value
    
    crud.get_system_by_address(mock_db, 12345)
    
    mock_db.query.assert_called_once_with(models.System)
    # Correctly check that filter was called with the right condition.
    # This is a bit more involved to check the actual filter expression.
    assert mock_query.filter.call_args[0][0].compare(
        models.System.system_address == 12345
    )
    mock_filtered_query.first.assert_called_once()


def test_create_or_update_system_creates_new():
    """
    Tests that a new system is created when it does not exist.
    """
    mock_db = MagicMock()
    # Simulate that the system does not exist
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    system_address = 10477373803
    name = "Eranin"
    x, y, z = 1.0, 2.0, 3.0
    ts = datetime.now(timezone.utc)

    # Use a patch to prevent ST_MakePoint from being called in the test environment
    # as it requires a real database connection or a more complex mock.
    with unittest.mock.patch('src.app.crud.ST_MakePoint') as mock_st_makepoint:
        system = crud.create_or_update_system(mock_db, system_address, name, x, y, z, ts)
        mock_st_makepoint.assert_called_once_with(x, y, z, srid=0)

    mock_db.add.assert_called_once()
    new_system = mock_db.add.call_args[0][0]
    
    assert isinstance(new_system, models.System)
    assert new_system.system_address == system_address
    assert new_system.name == name
    assert new_system.x == x
    assert new_system.y == y
    assert new_system.z == z


def test_create_or_update_system_updates_existing():
    """
    Tests that an existing system is updated.
    """
    mock_db = MagicMock()
    
    existing_system = models.System(
        system_address=10477373803,
        name="Old Name",
        x=0.0, y=0.0, z=0.0,
        updated_at=datetime(2020, 1, 1, tzinfo=timezone.utc)
    )
    # Simulate that the system exists
    mock_db.query.return_value.filter.return_value.first.return_value = existing_system
    
    new_name = "Eranin"
    new_x, new_y, new_z = 1.0, 2.0, 3.0
    new_ts = datetime.now(timezone.utc)

    with unittest.mock.patch('src.app.crud.ST_MakePoint') as mock_st_makepoint:
        system = crud.create_or_update_system(
            mock_db, existing_system.system_address, new_name, new_x, new_y, new_z, new_ts
        )
        mock_st_makepoint.assert_called_once_with(new_x, new_y, new_z, srid=0)
    
    mock_db.add.assert_not_called()
    assert system.name == new_name
    assert system.x == new_x
    assert system.y == new_y
    assert system.z == new_z
    assert system.updated_at == new_ts 


def test_get_or_create_commodity_creates_new():
    """
    Tests creating a new commodity when it doesn't exist.
    """
    mock_db = MagicMock()
    # Mock the session's 'new' attribute to be empty
    type(mock_db).new = unittest.mock.PropertyMock(return_value=[])
    # Mock the query to return no existing commodity
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    
    commodity_name = "Tritium"
    commodity = crud.get_or_create_commodity(mock_db, commodity_name)
    
    mock_db.add.assert_called_once()
    new_comm = mock_db.add.call_args[0][0]
    assert isinstance(new_comm, models.Commodity)
    assert new_comm.name == commodity_name


def test_get_or_create_commodity_returns_existing():
    """
    Tests returning an existing commodity from the database.
    """
    mock_db = MagicMock()
    type(mock_db).new = unittest.mock.PropertyMock(return_value=[])
    
    existing_commodity = models.Commodity(name="Tritium")
    mock_db.query.return_value.filter_by.return_value.first.return_value = existing_commodity
    
    commodity = crud.get_or_create_commodity(mock_db, "Tritium")
    
    mock_db.add.assert_not_called()
    assert commodity == existing_commodity


def test_get_or_create_commodity_returns_from_session():
    """
    Tests returning a commodity that is pending in the current session.
    """
    mock_db = MagicMock()
    
    # Simulate a commodity already added to the session but not committed
    pending_commodity = models.Commodity(name="Tritium")
    type(mock_db).new = unittest.mock.PropertyMock(return_value=[pending_commodity])
    
    commodity = crud.get_or_create_commodity(mock_db, "Tritium")
    
    # Neither query nor add should be called if found in session.new
    mock_db.query.assert_not_called()
    mock_db.add.assert_not_called()
    assert commodity == pending_commodity 


def test_get_or_create_station_creates_new():
    """
    Tests creating a new station when it does not exist.
    """
    mock_db = MagicMock()
    # Mock the return for the station query (station doesn't exist)
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    
    # Mock the return for the parent system query
    parent_system = models.System(name="Sol", system_address=123)
    # To mock multiple calls to query, we can use side_effect
    mock_db.query.side_effect = [
        # Result for the Station query
        MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
        # Result for the System query
        MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=parent_system))))
    ]
    
    market_id = 987
    station_name = "Gagarin Gate"
    ts = datetime.now(timezone.utc)

    station = crud.get_or_create_station(mock_db, market_id, station_name, "Sol", None, ts)
    
    mock_db.add.assert_called_once()
    new_station = mock_db.add.call_args[0][0]
    
    assert isinstance(new_station, models.Station)
    assert new_station.market_id == market_id
    assert new_station.name == station_name
    assert new_station.system_address == parent_system.system_address
    assert new_station.updated_at == ts


def test_get_or_create_station_updates_existing():
    """
    Tests updating an existing station.
    """
    mock_db = MagicMock()

    existing_station = models.Station(
        market_id=987,
        name="Old Name",
        system_address=None, # Simulate it was created without an address
        updated_at=datetime(2020, 1, 1, tzinfo=timezone.utc)
    )
    parent_system = models.System(name="Sol", system_address=123)

    mock_db.query.side_effect = [
        MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=existing_station)))),
        MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=parent_system))))
    ]
    
    new_station_name = "Gagarin Gate"
    new_ts = datetime.now(timezone.utc)
    prohibited_list = ["Slaves"]

    station = crud.get_or_create_station(
        mock_db, existing_station.market_id, new_station_name, "Sol", prohibited_list, new_ts
    )
    
    mock_db.add.assert_not_called()
    assert station.name == new_station_name
    assert station.system_address == parent_system.system_address # Check address gets updated
    assert station.prohibited == prohibited_list
    assert station.updated_at == new_ts


def test_create_or_update_station_commodities():
    """
    Tests the bulk upsert logic for station commodities.
    """
    mock_db = MagicMock()
    # Mock pg_insert to allow chaining
    mock_pg_insert = MagicMock()
    mock_db.execute.return_value = None
    
    # Mock the commodity lookups
    tritium = models.Commodity(id=1, name="Tritium")
    water = models.Commodity(id=2, name="Water")
    mock_db.query.return_value.filter_by.side_effect = [
        MagicMock(first=MagicMock(return_value=tritium)),
        MagicMock(first=MagicMock(return_value=water)),
    ]
    # Mock the session's 'new' attribute to be empty
    type(mock_db).new = unittest.mock.PropertyMock(return_value=[])

    commodities_data = [
        {"name": "Tritium", "buyPrice": 100, "sellPrice": 110, "demand": 1000, "stock": 500},
        {"name": "Water", "buyPrice": 10, "sellPrice": 12, "demand": 5000, "stock": 20000},
    ]
    market_id = 12345
    ts = datetime.now(timezone.utc)

    with unittest.mock.patch('src.app.crud.pg_insert') as mock_pg_insert_func:
        # Mock the chained calls for on_conflict_do_update
        mock_on_conflict = MagicMock()
        mock_values = MagicMock()
        mock_values.on_conflict_do_update.return_value = mock_on_conflict
        mock_pg_insert_func.return_value.values.return_value = mock_values

        crud.create_or_update_station_commodities(mock_db, market_id, commodities_data, ts)

        # 1. Verify pg_insert was called with the correct table
        mock_pg_insert_func.assert_called_once_with(models.StationCommodity)

        # 2. Verify the values passed to the insert statement
        insert_data = mock_pg_insert_func.return_value.values.call_args[0][0]
        assert len(insert_data) == 2
        assert insert_data[0]['commodity_id'] == tritium.id
        assert insert_data[1]['commodity_id'] == water.id
        assert insert_data[0]['buy_price'] == 100

        # 3. Verify the on_conflict_do_update configuration
        mock_values.on_conflict_do_update.assert_called_once()
        conflict_args = mock_values.on_conflict_do_update.call_args
        assert conflict_args[1]['index_elements'] == ['station_market_id', 'commodity_id']
        assert 'buy_price' in conflict_args[1]['set_']
        
        # 4. Verify the final statement was executed
        mock_db.execute.assert_called_once_with(mock_on_conflict)
        
        # 5. Verify db.flush() was called
        mock_db.flush.assert_called_once() 


def test_bulk_upsert_systems():
    """
    Tests that the bulk_upsert_systems function constructs the correct
    PostgreSQL INSERT...ON CONFLICT statement.
    """
    mock_db = MagicMock()
    systems_data = [
        {"system_address": 1, "name": "Sol", "x": 0, "y": 0, "z": 0},
    ]

    with unittest.mock.patch('src.app.crud.pg_insert') as mock_pg_insert_func:
        # Mock the chained calls for on_conflict_do_update
        mock_on_conflict = MagicMock()
        mock_values = MagicMock()
        mock_values.on_conflict_do_update.return_value = mock_on_conflict
        mock_pg_insert_func.return_value.values.return_value = mock_values

        # Call the function under test ONCE
        result = crud.bulk_upsert_systems(mock_db, systems_data)

        # 1. Verify pg_insert was called with the correct table
        mock_pg_insert_func.assert_called_once_with(models.System)

        # 2. Verify the values were passed
        mock_pg_insert_func.return_value.values.assert_called_once_with(systems_data)

        # 3. Verify the on_conflict_do_update configuration
        mock_values.on_conflict_do_update.assert_called_once()
        conflict_args = mock_values.on_conflict_do_update.call_args[1]
        
        # Check the constraint target
        assert conflict_args['index_elements'] == ['system_address']
        
        # Check the SET clause
        set_clause = conflict_args['set_']
        
        # Ensure all expected keys are in the set_clause
        assert 'name' in set_clause
        assert 'x' in set_clause
        assert 'y' in set_clause
        assert 'z' in set_clause
        assert 'coords' in set_clause
        assert 'updated_at' in set_clause
        assert 'row_updated_at' in set_clause

        # Check the WHERE clause
        where_clause = conflict_args['where']
        assert str(where_clause) == 'systems.updated_at < excluded.updated_at'

        # 4. Verify the final statement was executed
        mock_db.execute.assert_called_once_with(mock_on_conflict)

        # 5. Verify the rowcount is returned from the single call
        assert result == mock_db.execute.return_value.rowcount