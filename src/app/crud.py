from sqlalchemy.orm import Session

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