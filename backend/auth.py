"""
auth.py — JWT creation/verification and bcrypt password helpers.

Uses the `bcrypt` library directly (instead of passlib) to avoid the
passlib/bcrypt>=4 incompatibility on Python 3.9.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import models
from database import get_db

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────

SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# OAuth2 scheme — looks for "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Password helpers ───────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain-text password matches the bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── JWT helpers ────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create and sign a JWT access token.

    Args:
        data: Payload dict (must include a 'sub' key = user identifier).
        expires_delta: Optional custom expiry; defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    FastAPI dependency that validates the JWT and returns the User ORM object.

    Raises 401 if the token is invalid, expired, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
