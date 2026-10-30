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


def usage_by_day(start: str, end: str):
    return get_db().execute(
        """
        SELECT date(entry_time) AS day, count(*) AS sessions,
               round(avg(CASE WHEN exit_time IS NOT NULL
                   THEN (julianday(exit_time) - julianday(entry_time)) * 1440 END)) AS avg_minutes
        FROM parking_sessions WHERE entry_time >= ? AND entry_time < ?
        GROUP BY day ORDER BY day
        """, (start, end)).fetchall()


def peak_hours(start: str, end: str, limit: int = 3):
    return get_db().execute(
        "SELECT CAST(strftime('%H', entry_time) AS INTEGER) AS hour, count(*) AS entries "
        "FROM parking_sessions WHERE entry_time >= ? AND entry_time < ? "
        "GROUP BY hour ORDER BY entries DESC, hour LIMIT ?", (start, end, limit)).fetchall()


def slot_utilisation(start: str, end: str, until: str):
    return get_db().execute(
        """
        SELECT s.code, s.slot_type, count(p.id) AS sessions,
               coalesce(round(sum((julianday(coalesce(p.exit_time, ?)) - julianday(p.entry_time)) * 24), 1), 0) AS hours
        FROM slots s LEFT JOIN parking_sessions p ON p.slot_id = s.id
             AND p.entry_time >= ? AND p.entry_time < ?
        GROUP BY s.id ORDER BY sessions DESC, s.code
        """, (until, start, end)).fetchall()


def revenue_by_day(start: str, end: str):
    return get_db().execute(
        "SELECT date(created_at) AS day, count(*) AS payments, sum(amount) AS amount FROM payments "
        "WHERE status = 'success' AND created_at >= ? AND created_at < ? GROUP BY day ORDER BY day",
        (start, end)).fetchall()


def revenue_by_method(start: str, end: str):
    return get_db().execute(
        "SELECT method, count(*) AS payments, sum(amount) AS amount FROM payments "
        "WHERE status = 'success' AND created_at >= ? AND created_at < ? GROUP BY method ORDER BY amount DESC",
        (start, end)).fetchall()


def revenue_by_vehicle_type(start: str, end: str):
    return get_db().execute(
        "SELECT v.type AS vehicle_type, count(*) AS payments, sum(pay.amount) AS amount FROM payments pay "
        "JOIN parking_sessions p ON p.id = pay.session_id JOIN vehicles v ON v.id = p.vehicle_id "
        "WHERE pay.status = 'success' AND pay.created_at >= ? AND pay.created_at < ? "
        "GROUP BY v.type ORDER BY amount DESC", (start, end)).fetchall()


def failed_payments(start: str, end: str) -> int:
    return get_db().execute(
        "SELECT count(*) FROM payments WHERE status = 'failed' AND created_at >= ? AND created_at < ?",
        (start, end)).fetchone()[0]


def vehicle_activity(start: str, end: str, until: str, limit: int = 50):
    return get_db().execute(
        """
        SELECT v.number, v.type, v.owner_name, count(p.id) AS visits,
               coalesce(round(sum((julianday(coalesce(p.exit_time, ?)) - julianday(p.entry_time)) * 24), 1), 0) AS hours,
               coalesce(sum(p.fee), 0) AS fees, max(p.entry_time) AS last_entry
        FROM parking_sessions p JOIN vehicles v ON v.id = p.vehicle_id
        WHERE p.entry_time >= ? AND p.entry_time < ?
        GROUP BY v.id ORDER BY visits DESC, hours DESC LIMIT ?
        """, (until, start, end, limit)).fetchall()
