"""Data Layer: in-app notifications."""
from app.data.db import get_db


def add(user_id: int, kind: str, message: str) -> None:
    get_db().execute(
        "INSERT INTO notifications (user_id, kind, message) VALUES (?, ?, ?)", (user_id, kind, message)
    )


def for_user(user_id: int, limit: int = 100):
    return get_db().execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
    ).fetchall()


def unread_count(user_id: int) -> int:
    return get_db().execute(
        "SELECT count(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,)
    ).fetchone()[0]


def mark_all_read(user_id: int) -> None:
    get_db().execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))


def reservations_expiring(user_id: int, now: str, soon: str):
    """Confirmed reservations ending within the warning window that haven't been warned about."""
    return get_db().execute(
        "SELECT r.id, r.end_time, s.code AS slot_code, v.number AS vehicle_number "
        "FROM reservations r JOIN slots s ON s.id = r.slot_id JOIN vehicles v ON v.id = r.vehicle_id "
        "WHERE r.user_id = ? AND r.status IN ('confirmed', 'used') AND r.expiry_notified = 0 "
        "AND r.end_time > ? AND r.end_time <= ?",
        (user_id, now, soon),
    ).fetchall()


def overstays(user_id: int, now: str):
    """Vehicles still parked after the reservation they entered on has ended."""
    return get_db().execute(
        "SELECT r.id, r.end_time, s.code AS slot_code, v.number AS vehicle_number "
        "FROM reservations r JOIN slots s ON s.id = r.slot_id JOIN vehicles v ON v.id = r.vehicle_id "
        "JOIN parking_sessions p ON p.vehicle_id = r.vehicle_id AND p.exit_time IS NULL "
        "WHERE r.user_id = ? AND r.status = 'used' AND r.expiry_notified < 2 AND r.end_time <= ?",
        (user_id, now),
    ).fetchall()


def set_expiry_notified(reservation_id: int, level: int) -> None:
    get_db().execute("UPDATE reservations SET expiry_notified = ? WHERE id = ?", (level, reservation_id))
