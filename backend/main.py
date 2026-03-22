"""
main.py — FastAPI application entry point.

Startup:
  - Creates all SQLite tables (if not already present).
  - Mounts CORS middleware.
  - Registers auth and Google-OAuth routers.
  - Mounts a session middleware required by Authlib for OAuth state management.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import models
from database import engine
from routes import auth as auth_router
from routes import google as google_router

load_dotenv()

# Create all database tables on startup (idempotent)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auth API",
    description="Full-stack authentication API with email/password and Google OAuth2.",
    version="1.0.0",
)

# ── Middleware ─────────────────────────────────────────────────────────────────

# Session middleware is required by Authlib to store OAuth state/nonce between
# the /auth/google redirect and the /auth/google/callback.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(auth_router.router)
app.include_router(google_router.router)


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "Auth API is running."}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
