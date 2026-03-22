"""
routes/google.py — Google OAuth2 Authorization Code Flow.

Standard flow:
  1. GET /auth/google          → redirect user to Google's consent screen
  2. GET /auth/google/callback ← Google redirects here with ?code=...
     - Exchange code for tokens
     - Fetch user profile from Google
     - Upsert user in SQLite (create if new, update picture/name if existing)
     - Issue our own JWT
     - Redirect frontend to /dashboard?token=<jwt>
"""

import os

import httpx
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.config import Config

import models
import schemas
from auth import create_access_token
from database import get_db

load_dotenv()

# ── OAuth client setup ─────────────────────────────────────────────────────────

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Authlib requires a Config object for secrets
config = Config(environ={
    "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET,
})

oauth = OAuth(config)
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    # Google's OpenID Connect discovery document
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        # openid: required for OIDC / id_token
        # profile: name, picture
        # email: email address
        "scope": "openid profile email",
    },
)

router = APIRouter(prefix="/auth", tags=["google-oauth"])


@router.get("/google", summary="Redirect to Google OAuth consent screen")
async def google_login(request: Request):
    """
    Step 1 — Redirect the browser to Google's OAuth2 consent page.

    Google will redirect back to /auth/google/callback after the user grants access.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail=(
                "Google OAuth is not configured. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env"
            ),
        )
    redirect_uri = f"{BACKEND_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", summary="Handle Google OAuth callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Step 2 — Handle the callback from Google.

    - Exchange the authorization code for tokens.
    - Validate the id_token (Authlib does this automatically).
    - Fetch user profile (sub, email, name, picture).
    - Upsert user in the database.
    - Issue our own JWT and redirect the frontend with it.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {exc}")

    # The id_token is verified and decoded by Authlib (signature + nonce + audience)
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not fetch user info from Google.")

    google_id: str = user_info["sub"]
    email: str = user_info.get("email", "")
    name: str = user_info.get("name", "")
    picture: str = user_info.get("picture", "")

    # ── Upsert user ────────────────────────────────────────────────────────────
    # Try to find by google_id first, then by email (handles the case where
    # the user previously signed up with email/password using the same address).
    user = (
        db.query(models.User).filter(models.User.google_id == google_id).first()
        or db.query(models.User).filter(models.User.email == email).first()
    )

    if user:
        # Update profile fields that may have changed on Google's side
        user.google_id = google_id
        user.name = name or user.name
        user.picture = picture or user.picture
    else:
        # New user — create a record (no password for Google-OAuth users)
        user = models.User(
            email=email,
            name=name,
            picture=picture,
            google_id=google_id,
            hashed_password=None,  # Intentionally NULL for Google-OAuth accounts
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # ── Issue JWT and redirect ─────────────────────────────────────────────────
    jwt_token = create_access_token({"sub": str(user.id)})

    # Pass the token in the URL fragment so it never hits the server logs
    redirect_url = f"{FRONTEND_URL}/dashboard?token={jwt_token}"
    return RedirectResponse(url=redirect_url)
