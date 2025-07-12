from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_config

# Construct the database URL from environment variables
DB_USER = get_config("RP_DB_USER")
DB_PASSWORD = get_config("RP_DB_PASSWORD")
DB_HOST = get_config("RP_DB_HOST")
DB_PORT = get_config("RP_DB_PORT")
DB_DATABASE = get_config("RP_DB_DATABASE")

SQLALCHEMY_DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Provides a database session for a single unit of work.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 