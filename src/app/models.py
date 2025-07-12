from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    TIMESTAMP,
    DOUBLE, # Use DOUBLE for DOUBLE PRECISION
    text,
    func # Import func for database functions like now()
)
from geoalchemy2 import Geometry # This import is correct and necessary

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
    sells_tritium = Column(Boolean, nullable=False, server_default=text("FALSE")) # Use FALSE directly


    def __repr__(self):
        return f"<System(name='{self.name}', system_address={self.system_address})>"

