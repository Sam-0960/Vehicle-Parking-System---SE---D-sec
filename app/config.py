"""Application configuration.

Secrets come from the environment, never from source code (C-08).
"""
import os
import secrets
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("VPS_SECRET_KEY") or secrets.token_hex(32)
    DATABASE = os.environ.get("VPS_DATABASE", str(BASE_DIR / "instance" / "parking.db"))

    # Session hardening (C-01, T-12)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("VPS_SECURE_COOKIES", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Login lockout (C-01, T-01)
    MAX_FAILED_LOGINS = 5
    LOCKOUT_MINUTES = 15

    # Rate limiting (C-07, T-13): requests per window per client
    RATE_LIMIT_WINDOW_SECONDS = 60
    RATE_LIMIT_LOGIN = 10
    RATE_LIMIT_WRITE = 30

    # Mock payment gateway signing key (TB-03)
    GATEWAY_SECRET = os.environ.get("VPS_GATEWAY_SECRET") or secrets.token_hex(16)

    TESTING = False


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    GATEWAY_SECRET = "test-gateway"
    RATE_LIMIT_LOGIN = 1000
    RATE_LIMIT_WRITE = 1000
