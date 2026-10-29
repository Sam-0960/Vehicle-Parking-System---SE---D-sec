"""Data Layer: security audit log (C-09)."""
from app import clock
from app.data.db import get_db


def add(actor_id, action: str, detail: str = "", ip: str = "") -> None:
    get_db().execute(
        "INSERT INTO audit_log (actor_id, action, detail, ip, created_at) VALUES (?, ?, ?, ?, ?)",
        (actor_id, action, detail, ip, clock.to_str(clock.now())),
    )


def recent(limit: int = 50):
    return get_db().execute(
        "SELECT a.*, u.email AS actor_email FROM audit_log a "
        "LEFT JOIN users u ON u.id = a.actor_id ORDER BY a.id DESC LIMIT ?",
        (limit,),
    ).fetchall()
