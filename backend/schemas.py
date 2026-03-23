"""
schemas.py — Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ── Request schemas ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload for POST /auth/register (email+password signup)."""
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    """Payload for POST /auth/login."""
    email: EmailStr
    password: str


# ── Response schemas ───────────────────────────────────────────────────────────

class UserOut(BaseModel):
    """Public user representation — never exposes hashed_password."""
    id: int
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    google_id: Optional[str] = None
    role: str
    is_active_rider: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut
