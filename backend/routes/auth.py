"""
routes/auth.py — Email/password registration, login, and /me endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from auth import create_access_token, get_current_user, hash_password, verify_password
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with email and password.

    - Email must be unique.
    - Password is bcrypt-hashed before storage — plaintext is never persisted.
    - Returns a JWT access token so the user is immediately logged in.
    """
    # Check for duplicate email
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Hash the password — NEVER store plaintext
    user = models.User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(
        access_token=token,
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate an email/password user and return a JWT access token.

    - If the account was created via Google OAuth, they must use Google to sign in.
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    # User not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Account exists but was created via Google OAuth (no local password)
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google Sign-In. Please continue with Google.",
        )

    # Wrong password
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(
        access_token=token,
        user=schemas.UserOut.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    Requires a valid Bearer JWT in the Authorization header.
    """
    return current_user
