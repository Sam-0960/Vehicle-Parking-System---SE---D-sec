"""Data Layer: parking slots."""
from app.data.db import get_db


def list_all():
    return get_db().execute(
        "SELECT s.*, EXISTS(SELECT 1 FROM parking_sessions p WHERE p.slot_id = s.id "
        "AND p.exit_time IS NULL) AS is_occupied "
        "FROM slots s ORDER BY s.code"
    ).fetchall()


def get(slot_id: int):
    return get_db().execute("SELECT * FROM slots WHERE id = ?", (slot_id,)).fetchone()


def get_by_code(code: str):
    return get_db().execute("SELECT * FROM slots WHERE code = ?", (code,)).fetchone()


def create(code: str, slot_type: str) -> int:
    return get_db().execute(
        "INSERT INTO slots (code, slot_type) VALUES (?, ?)", (code, slot_type)
    ).lastrowid


def update(slot_id: int, slot_type: str, is_active: bool) -> None:
    get_db().execute(
        "UPDATE slots SET slot_type = ?, is_active = ? WHERE id = ?",
        (slot_type, 1 if is_active else 0, slot_id),
    )


def delete(slot_id: int) -> None:
    get_db().execute("DELETE FROM slots WHERE id = ?", (slot_id,))


def is_occupied(slot_id: int) -> bool:
    return get_db().execute(
        "SELECT 1 FROM parking_sessions WHERE slot_id = ? AND exit_time IS NULL", (slot_id,)
    ).fetchone() is not None


def has_history(slot_id: int) -> bool:
    return get_db().execute(
        "SELECT 1 FROM parking_sessions WHERE slot_id = ? UNION ALL "
        "SELECT 1 FROM reservations WHERE slot_id = ? LIMIT 1", (slot_id, slot_id)
    ).fetchone() is not None


def availability(now: str):
    """Every active slot with its current state, in one query (NFR-01)."""
    return get_db().execute(
        """
        SELECT s.id, s.code, s.slot_type,
               p.id AS session_id, v.number AS vehicle_number, p.entry_time,
               r.public_id AS reservation_id, r.end_time AS reserved_until,
               CASE WHEN p.id IS NOT NULL THEN 'occupied'
                    WHEN r.id IS NOT NULL THEN 'reserved'
                    ELSE 'available' END AS state
        FROM slots s
        LEFT JOIN parking_sessions p ON p.slot_id = s.id AND p.exit_time IS NULL
        LEFT JOIN vehicles v ON v.id = p.vehicle_id
        LEFT JOIN reservations r ON r.slot_id = s.id AND r.status = 'confirmed'
                                 AND r.start_time <= ? AND r.end_time > ?
        WHERE s.is_active = 1
        GROUP BY s.id
        ORDER BY s.code
        """,
        (now, now),
    ).fetchall()
