"""
database.py — SQLAlchemy engine + session setup using SQLite.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database file stored in the backend directory
SQLALCHEMY_DATABASE_URL = "sqlite:///./auth.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Required for SQLite: allows multi-threaded access
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and ensures it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
