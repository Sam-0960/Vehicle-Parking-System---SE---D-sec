"""Data Layer: parking sessions (entry, exit, fee)."""
from app.data.db import get_db

_SELECT = (
    "SELECT p.*, s.code AS slot_code, s.slot_type, v.number AS vehicle_number, "
    "v.type AS vehicle_type, v.user_id, v.owner_name "
    "FROM parking_sessions p JOIN slots s ON s.id = p.slot_id "
    "JOIN vehicles v ON v.id = p.vehicle_id "
)


def get(session_id: int):
    return get_db().execute(_SELECT + "WHERE p.id = ?", (session_id,)).fetchone()


def active_for_vehicle(vehicle_id: int):
    return get_db().execute(
        _SELECT + "WHERE p.vehicle_id = ? AND p.exit_time IS NULL", (vehicle_id,)
    ).fetchone()


def active_for_user(user_id: int):
    return get_db().execute(
        _SELECT + "WHERE v.user_id = ? AND p.exit_time IS NULL ORDER BY p.entry_time", (user_id,)
    ).fetchall()


def all_active():
    return get_db().execute(
        _SELECT + "WHERE p.exit_time IS NULL ORDER BY p.entry_time"
    ).fetchall()


def free_slots(slot_type: str, now: str, exclude_reserved_for_user=None):
    """Active, unoccupied slots of a type that nobody else has reserved right now."""
    return get_db().execute(
        """
        SELECT s.* FROM slots s
        WHERE s.is_active = 1 AND s.slot_type = ?
          AND NOT EXISTS (SELECT 1 FROM parking_sessions p WHERE p.slot_id = s.id AND p.exit_time IS NULL)
          AND NOT EXISTS (SELECT 1 FROM reservations r WHERE r.slot_id = s.id AND r.status = 'confirmed'
                          AND r.start_time <= ? AND r.end_time > ?
                          AND (? IS NULL OR r.user_id != ?))
        ORDER BY s.code
        """,
        (slot_type, now, now, exclude_reserved_for_user, exclude_reserved_for_user),
    ).fetchall()


def insert_entry(conn, vehicle_id: int, slot_id: int, entry_time: str) -> int:
    return conn.execute(
        "INSERT INTO parking_sessions (vehicle_id, slot_id, entry_time) VALUES (?, ?, ?)",
        (vehicle_id, slot_id, entry_time),
    ).lastrowid


def record_exit(conn, session_id: int, exit_time: str, fee, status: str) -> int:
    """Only closes a session that is still open, so a repeated exit request changes nothing."""
    return conn.execute(
        "UPDATE parking_sessions SET exit_time = ?, fee = ?, status = ? "
        "WHERE id = ? AND exit_time IS NULL",
        (exit_time, fee, status, session_id),
    ).rowcount


def unpaid_for_user(user_id: int):
    return get_db().execute(
        _SELECT + "WHERE v.user_id = ? AND p.status = 'unpaid' ORDER BY p.exit_time DESC", (user_id,)
    ).fetchall()


def all_unpaid():
    return get_db().execute(_SELECT + "WHERE p.status = 'unpaid' ORDER BY p.exit_time DESC").fetchall()


def history(user_id=None, vehicle_id=None, limit: int = 200):
    """Completed sessions with duration; filtered by owner and/or vehicle."""
    sql = (_SELECT.replace("SELECT p.*,", "SELECT p.*, "
           "CAST(round((julianday(p.exit_time) - julianday(p.entry_time)) * 1440) AS INTEGER) AS minutes,")
           + "WHERE p.exit_time IS NOT NULL ")
    args = []
    if user_id is not None:
        sql += "AND v.user_id = ? "
        args.append(user_id)
    if vehicle_id is not None:
        sql += "AND v.id = ? "
        args.append(vehicle_id)
    sql += "ORDER BY p.exit_time DESC LIMIT ?"
    args.append(limit)
    return get_db().execute(sql, args).fetchall()
