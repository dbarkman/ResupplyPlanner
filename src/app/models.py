from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    TIMESTAMP,
    DOUBLE, # Use DOUBLE for DOUBLE PRECISION
    text,
    func, # Import func for database functions like now()
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from geoalchemy2 import Geometry

from .database import Base

class System(Base):
    """
    SQLAlchemy model representing the 'systems' table in the database.
    """
    __tablename__ = "systems"

    system_address = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    x = Column(DOUBLE, nullable=False) # Removed server_default, application should provide
    y = Column(DOUBLE, nullable=False) # Removed server_default, application should provide
    z = Column(DOUBLE, nullable=False) # Removed server_default, application should provide
    coords = Column(Geometry(geometry_type="POINTZ", srid=0), nullable=False, spatial_index=True)
    updated_at = Column(
        TIMESTAMP(timezone=True), # Use timezone=True for TIMESTAMP WITH TIME ZONE
        nullable=False,
        server_default=func.now() # Set default to current time
    )
    requires_permit = Column(Boolean, nullable=False, server_default=text("FALSE")) # Use FALSE directly

    def __repr__(self):
        return f"<System(name='{self.name}', system_address={self.system_address})>"


class Commodity(Base):
    """
    SQLAlchemy model for all unique commodity types.
    """
    __tablename__ = "commodities"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Commodity(name='{self.name}')>"


class Station(Base):
    """
    SQLAlchemy model for stations/markets.
    """
    __tablename__ = "stations"

    market_id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    system_address = Column(BigInteger, ForeignKey("systems.system_address"), nullable=True, index=True)
    prohibited = Column(ARRAY(TEXT))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    system = relationship("System")
    commodities = relationship("StationCommodity", back_populates="station", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Station(name='{self.name}', market_id={self.market_id})>"


class StationCommodity(Base):
    """
    SQLAlchemy model for commodity listings at a specific station.
    """
    __tablename__ = "station_commodities"

    id = Column(BigInteger, primary_key=True)
    station_market_id = Column(BigInteger, ForeignKey("stations.market_id", ondelete="CASCADE"), nullable=False)
    commodity_id = Column(Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False)
    buy_price = Column(Integer, nullable=False)
    sell_price = Column(Integer, nullable=False)
    demand = Column(Integer, nullable=False)
    demand_bracket = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)
    stock_bracket = Column(Integer, nullable=False)
    mean_price = Column(Integer, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)

    # Relationships
    station = relationship("Station", back_populates="commodities")
    commodity = relationship("Commodity")

    __table_args__ = (UniqueConstraint('station_market_id', 'commodity_id', name='_station_commodity_uc'),)

    def __repr__(self):
        return f"<StationCommodity(station_market_id={self.station_market_id}, commodity_id={self.commodity_id})>"

