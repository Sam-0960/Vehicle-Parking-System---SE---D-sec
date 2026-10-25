"""Skeleton checks: app boots, schema exists, errors stay generic."""
from app.data.db import get_db


def test_home_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Park smarter" in resp.data


def test_schema_created(app):
    with app.app_context():
        tables = {r["name"] for r in get_db().execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"users", "vehicles", "slots", "parking_sessions", "reservations",
            "payments", "rates", "notifications", "audit_log"} <= tables


def test_unknown_page_gives_generic_404(client):
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    assert b"Traceback" not in resp.data


def test_post_without_csrf_rejected(client):
    assert client.post("/").status_code == 400


def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
