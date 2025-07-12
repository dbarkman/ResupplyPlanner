from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    TIMESTAMP,
    DOUBLE,
    text,
)
from geoalchemy2 import Geometry

from .database import Base


class System(Base):
    """
    SQLAlchemy model representing the 'systems' table in the database.
    """
    __tablename__ = "systems"

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    x = Column(DOUBLE, nullable=False, server_default=text("999999.999"))
    y = Column(DOUBLE, nullable=False, server_default=text("999999.999"))
    z = Column(DOUBLE, nullable=False, server_default=text("999999.999"))
    coords = Column(Geometry(geometry_type="POINT", srid=0), nullable=False, spatial_index=True)
    requires_permit = Column(Boolean, nullable=False, server_default=text("0"))
    sells_tritium = Column(Boolean, nullable=False, server_default=text("0"))
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    def __repr__(self):
        return f"<System(name='{self.name}', id={self.id})>" 