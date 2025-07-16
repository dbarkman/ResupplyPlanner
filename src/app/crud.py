from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime
from geoalchemy2.functions import ST_MakePoint # Import ST_MakePoint to create spatial points

from . import models


def bulk_upsert_systems(db: Session, systems_data: list[dict]):
    """
    Performs a bulk "upsert" for system data using PostgreSQL's
    ON CONFLICT DO UPDATE feature, with a WHERE clause to handle stale data.
    This is optimized for high-volume initial data loads.

    Args:
        db: The SQLAlchemy database session.
        systems_data: A list of dictionaries, where each dictionary represents
                      a system to be upserted.

    Returns:
        The number of rows affected by the operation.
    """
    if not systems_data:
        return 0

    stmt = pg_insert(models.System).values(systems_data)
    
    # On conflict (based on system_address), update the columns,
    # but ONLY if the new record's timestamp is newer than the existing one.
    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=['system_address'],
        set_={
            "name": stmt.excluded.name,
            "x": stmt.excluded.x,
            "y": stmt.excluded.y,
            "z": stmt.excluded.z,
            "coords": stmt.excluded.coords,
            "updated_at": stmt.excluded.updated_at,
        },
        where=(models.System.updated_at < stmt.excluded.updated_at)
    )
    
    # Execute the statement and return the number of affected rows.
    result = db.execute(on_conflict_stmt)
    return result.rowcount

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


def get_or_create_commodity(db: Session, name: str) -> models.Commodity:
    """
    Retrieves a commodity by name or creates it if it doesn't exist.
    Caches results in the session to avoid redundant database calls within a transaction.
    """
    # Check session cache first
    for obj in db.new:
        if isinstance(obj, models.Commodity) and obj.name == name:
            return obj
    
    commodity = db.query(models.Commodity).filter_by(name=name).first()
    if not commodity:
        commodity = models.Commodity(name=name)
        db.add(commodity)
        # We don't commit here; the calling function will handle the transaction.
    return commodity


def get_or_create_station(
    db: Session,
    market_id: int,
    name: str,
    system_name: str,
    prohibited: list[str] | None,
    updated_at: datetime,
) -> models.Station:
    """
    Retrieves a station by market_id or creates it. Updates existing stations.
    """
    station = db.query(models.Station).filter_by(market_id=market_id).first()
    
    # Find the parent system's address if possible
    parent_system = get_system_by_name(db, system_name)
    system_address = parent_system.system_address if parent_system else None

    if station:
        # Update existing station - name and prohibited list are overwritten
        station.name = name
        station.prohibited = prohibited
        station.updated_at = updated_at
        # Update system_address if it was previously unknown
        if not station.system_address and system_address:
            station.system_address = system_address
    else:
        # Create new station
        station = models.Station(
            market_id=market_id,
            name=name,
            system_address=system_address,
            prohibited=prohibited,
            updated_at=updated_at,
        )
        db.add(station)
    
    return station


def create_or_update_station_commodities(
    db: Session,
    market_id: int,
    commodities_data: list[dict],
    timestamp: datetime
):
    """
    Performs a bulk "upsert" for station commodity data using PostgreSQL's
    ON CONFLICT DO UPDATE feature for high efficiency.
    """
    if not commodities_data:
        return

    # 1. Get or create all necessary commodity objects first
    commodity_map = {}
    for data in commodities_data:
        commodity_name = data.get("name")
        if commodity_name and commodity_name not in commodity_map:
            commodity_map[commodity_name] = get_or_create_commodity(db, commodity_name)
    db.flush() # Flush to assign IDs to any new commodities

    # 2. Prepare data for bulk upsert
    upsert_data = []
    for data in commodities_data:
        commodity_name = data.get("name")
        if not commodity_name:
            continue
        
        commodity = commodity_map.get(commodity_name)
        if not commodity or not commodity.id:
            continue

        upsert_data.append({
            "station_market_id": market_id,
            "commodity_id": commodity.id,
            "buy_price": int(data.get("buyPrice") or 0),
            "sell_price": int(data.get("sellPrice") or 0),
            "demand": int(data.get("demand") or 0),
            "demand_bracket": int(data.get("demandBracket") or 0),
            "stock": int(data.get("stock") or 0),
            "stock_bracket": int(data.get("stockBracket") or 0),
            "mean_price": int(data.get("meanPrice") or 0),
            "updated_at": timestamp,
        })

    if not upsert_data:
        return
        
    # 3. Perform the bulk upsert
    stmt = pg_insert(models.StationCommodity).values(upsert_data)
    
    # Define what to do on conflict (unique constraint on station_market_id, commodity_id)
    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=['station_market_id', 'commodity_id'],
        set_={
            "buy_price": stmt.excluded.buy_price,
            "sell_price": stmt.excluded.sell_price,
            "demand": stmt.excluded.demand,
            "demand_bracket": stmt.excluded.demand_bracket,
            "stock": stmt.excluded.stock,
            "stock_bracket": stmt.excluded.stock_bracket,
            "mean_price": stmt.excluded.mean_price,
            "updated_at": stmt.excluded.updated_at,
        }
    )
    
    db.execute(on_conflict_stmt)
    # The calling function will handle the final db.commit()


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

    # The calling function is responsible for the commit.
    # db.refresh(system) has been removed as it's not needed here and
    # caused an error on new, non-persistent objects.
    return system