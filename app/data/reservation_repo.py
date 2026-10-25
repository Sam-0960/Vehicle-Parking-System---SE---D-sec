"""Data Layer: reservations."""
from app.data.db import get_db

_SELECT = (
    "SELECT r.*, s.code AS slot_code, s.slot_type, v.number AS vehicle_number "
    "FROM reservations r JOIN slots s ON s.id = r.slot_id JOIN vehicles v ON v.id = r.vehicle_id "
)


def get_by_public_id(public_id: str):
    return get_db().execute(_SELECT + "WHERE r.public_id = ?", (public_id,)).fetchone()


def get_by_key(key: str):
    return get_db().execute(_SELECT + "WHERE r.idempotency_key = ?", (key,)).fetchone()


def for_user(user_id: int):
    return get_db().execute(
        _SELECT + "WHERE r.user_id = ? ORDER BY r.start_time DESC LIMIT 50", (user_id,)
    ).fetchall()


def upcoming_all(now: str):
    return get_db().execute(
        _SELECT + "WHERE r.status = 'confirmed' AND r.end_time > ? ORDER BY r.start_time", (now,)
    ).fetchall()


def count_open_for_user(user_id: int, now: str) -> int:
    return get_db().execute(
        "SELECT count(*) FROM reservations WHERE user_id = ? AND status = 'confirmed' AND end_time > ?",
        (user_id, now),
    ).fetchone()[0]


def overlapping(slot_id: int, start: str, end: str):
    return get_db().execute(
        "SELECT 1 FROM reservations WHERE slot_id = ? AND status = 'confirmed' "
        "AND start_time < ? AND end_time > ?",
        (slot_id, end, start),
    ).fetchone()


def active_for_vehicle(vehicle_id: int, now: str):
    return get_db().execute(
        _SELECT + "WHERE r.vehicle_id = ? AND r.status = 'confirmed' "
        "AND r.start_time <= ? AND r.end_time > ? ORDER BY r.start_time LIMIT 1",
        (vehicle_id, now, now),
    ).fetchone()


def insert(conn, public_id, user_id, vehicle_id, slot_id, start, end, key) -> None:
    conn.execute(
        "INSERT INTO reservations (public_id, user_id, vehicle_id, slot_id, start_time, end_time, "
        "idempotency_key) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (public_id, user_id, vehicle_id, slot_id, start, end, key),
    )


def set_status(reservation_id: int, status: str, conn=None) -> None:
    (conn or get_db()).execute("UPDATE reservations SET status = ? WHERE id = ?", (status, reservation_id))


def expire_past(now: str) -> int:
    return get_db().execute(
        "UPDATE reservations SET status = 'expired' WHERE status = 'confirmed' AND end_time <= ?", (now,)
    ).rowcount
