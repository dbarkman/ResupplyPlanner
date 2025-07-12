import geoalchemy2.types
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import contextlib # Import the contextlib module

from .config import get_config

# Construct the database URL from environment variables
DB_USER = get_config("RP_DB_USER")
DB_PASSWORD = get_config("RP_DB_PASSWORD")
DB_HOST = get_config("RP_DB_HOST")
DB_PORT = get_config("RP_DB_PORT")
DB_DATABASE = get_config("RP_DB_DATABASE")

# Use 'postgresql+psycopg2' dialect for PostgreSQL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@contextlib.contextmanager # Add this decorator
def get_db():
    """
    Provides a database session for a single unit of work.
    This is now a context manager for use with 'with' statements.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
