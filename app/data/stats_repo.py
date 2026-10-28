"""Data Layer: aggregate queries for the admin dashboard and reports."""
from app.data.db import get_db


def occupancy_by_type():
    return get_db().execute(
        """
        SELECT s.slot_type,
               count(*) AS total,
               sum(CASE WHEN p.id IS NOT NULL THEN 1 ELSE 0 END) AS occupied
        FROM slots s
        LEFT JOIN parking_sessions p ON p.slot_id = s.id AND p.exit_time IS NULL
        WHERE s.is_active = 1
        GROUP BY s.slot_type ORDER BY s.slot_type
        """
    ).fetchall()


def revenue_between(start: str, end: str) -> float:
    return get_db().execute(
        "SELECT coalesce(sum(amount), 0) FROM payments WHERE status = 'success' "
        "AND created_at >= ? AND created_at < ?",
        (start, end),
    ).fetchone()[0]


def revenue_total() -> float:
    return get_db().execute(
        "SELECT coalesce(sum(amount), 0) FROM payments WHERE status = 'success'"
    ).fetchone()[0]


def unpaid_total():
    row = get_db().execute(
        "SELECT count(*) AS n, coalesce(sum(fee), 0) AS amount FROM parking_sessions WHERE status = 'unpaid'"
    ).fetchone()
    return row["n"], row["amount"]


def sessions_started_between(start: str, end: str) -> int:
    return get_db().execute(
        "SELECT count(*) FROM parking_sessions WHERE entry_time >= ? AND entry_time < ?", (start, end)
    ).fetchone()[0]
