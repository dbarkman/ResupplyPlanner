from src.app import models

def test_system_repr():
    """Tests the __repr__ method of the System model."""
    system = models.System(name="Sol", system_address=10477373803)
    assert repr(system) == "<System(name='Sol', system_address=10477373803)>"

def test_commodity_repr():
    """Tests the __repr__ method of the Commodity model."""
    commodity = models.Commodity(name="Tritium")
    assert repr(commodity) == "<Commodity(name='Tritium')>"

def test_station_repr():
    """Tests the __repr__ method of the Station model."""
    station = models.Station(name="Jameson Memorial", market_id=3228342528)
    assert repr(station) == "<Station(name='Jameson Memorial', market_id=3228342528)>"

def test_station_commodity_repr():
    """Tests the __repr__ method of the StationCommodity model."""
    station_commodity = models.StationCommodity(station_market_id=3228342528, commodity_id=128)
    assert repr(station_commodity) == "<StationCommodity(station_market_id=3228342528, commodity_id=128)>" 