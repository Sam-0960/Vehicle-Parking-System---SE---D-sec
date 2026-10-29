"""Data Layer: payments. Card numbers and CVV are never stored (C-06)."""
from app import clock
from app.data.db import get_db


def get_by_key(key: str):
    return get_db().execute("SELECT * FROM payments WHERE idempotency_key = ?", (key,)).fetchone()


def get_by_public_id(public_id: str):
    return get_db().execute(
        "SELECT pay.*, p.slot_id, v.number AS vehicle_number, v.user_id, s.code AS slot_code, "
        "p.entry_time, p.exit_time FROM payments pay "
        "JOIN parking_sessions p ON p.id = pay.session_id JOIN vehicles v ON v.id = p.vehicle_id "
        "JOIN slots s ON s.id = p.slot_id WHERE pay.public_id = ?",
        (public_id,),
    ).fetchone()


def for_session(session_id: int):
    return get_db().execute(
        "SELECT * FROM payments WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()


def insert(conn, public_id, session_id, amount, method, reference, status, key) -> None:
    conn.execute(
        "INSERT INTO payments (public_id, session_id, amount, method, reference, status, idempotency_key, "
        "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (public_id, session_id, amount, method, reference, status, key, clock.to_str(clock.now())),
    )


def mark_session_paid(conn, session_id: int) -> int:
    return conn.execute(
        "UPDATE parking_sessions SET status = 'paid' WHERE id = ? AND status = 'unpaid'", (session_id,)
    ).rowcount
