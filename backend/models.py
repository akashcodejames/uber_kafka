"""
models.py — SQLAlchemy ORM models for the users table.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base


class User(Base):
    """
    Users table.

    - google_id: set only for Google-OAuth accounts (NULL for email/pass users).
    - hashed_password: set only for email/password accounts (NULL for Google users).
    - picture: profile photo URL (populated from Google; NULL for email/pass users).
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)

    # Only set for Google-OAuth users
    google_id = Column(String, unique=True, nullable=True, index=True)

    # Only set for email/password users -- bcrypt hash, never plaintext
    hashed_password = Column(String, nullable=True)

    # Ride-hailing specific fields
    role = Column(String, default="user", server_default="user", nullable=False)
    is_active_rider = Column(Integer, default=0, server_default="0", nullable=False) # Boolean represented as Integer

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
