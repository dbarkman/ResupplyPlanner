from sqlalchemy.orm import Session
from datetime import datetime
from geoalchemy2.functions import ST_MakePoint # Import ST_MakePoint to create spatial points

from . import models


def get_system_by_name(db: Session, name: str) -> models.System | None:
    """
    Retrieves a single system from the database by its exact name.

    Args:
        db: The SQLAlchemy database session.
        name: The name of the system to retrieve.

    Returns:
        The System object if found, otherwise None.
    """
    return db.query(models.System).filter(models.System.name == name).first()


def get_system_by_address(db: Session, address: int) -> models.System | None:
    """
    Retrieves a single system from the database by its unique system_address.

    Args:
        db: The SQLAlchemy database session.
        address: The system_address of the system to retrieve.

    Returns:
        The System object if found, otherwise None.
    """
    return db.query(models.System).filter(models.System.system_address == address).first()


def create_or_update_system(
    db: Session,
    system_address: int,
    name: str | None,
    x: float | None,
    y: float | None,
    z: float | None,
    updated_at: datetime,
) -> models.System:
    """
    Creates a new system or updates an existing one in the database.

    This function performs an "upsert" operation based on the system_address.
    If coordinates are not provided, it uses the sentinel value.

    Args:
        db: The SQLAlchemy database session.
        system_address: The unique address of the system.
        name: The name of the system.
        x: The x coordinate of the system.
        y: The y coordinate of the system.
        z: The z coordinate of the system.
        updated_at: The timestamp of the update from the EDDN message.

    Returns:
        The created or updated System object.
    """
    existing_system = get_system_by_address(db, system_address)

    # Use sentinel values if coordinates are missing.
    # These must be provided as x, y, z are NOT NULL in the model.
    coord_x = x if x is not None else 999999.999
    coord_y = y if y is not None else 999999.999
    coord_z = z if z is not None else 999999.999

    # --- CHANGE IS HERE ---
    # Create a PostGIS PointZ object using ST_MakePoint.
    # GeoAlchemy2 will handle the conversion to the database's native spatial type.
    # SRID 0 is used for the Cartesian coordinate system.
    pg_point = ST_MakePoint(coord_x, coord_y, coord_z, srid=0)
    # --------------------

    if existing_system:
        # Update existing system
        if name:
            existing_system.name = name
        existing_system.x = coord_x
        existing_system.y = coord_y
        existing_system.z = coord_z
        existing_system.coords = pg_point # Assign the GeoAlchemy2 PointZ object
        existing_system.updated_at = updated_at # Explicitly set updated_at from message
        system = existing_system
    else:
        # Create new system
        system = models.System(
            system_address=system_address,
            name=name if name else "Unknown",  # Name is not nullable
            x=coord_x,
            y=coord_y,
            z=coord_z,
            coords=pg_point, # Assign the GeoAlchemy2 PointZ object
            updated_at=updated_at, # Explicitly set updated_at from message
        )
        db.add(system)

    db.commit()
    db.refresh(system)
    return system