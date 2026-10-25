"""Data Layer: vehicles."""
from app.data.db import get_db


def list_for_user(user_id: int):
    return get_db().execute(
        "SELECT v.*, EXISTS(SELECT 1 FROM parking_sessions s WHERE s.vehicle_id = v.id "
        "AND s.exit_time IS NULL) AS is_parked "
        "FROM vehicles v WHERE v.user_id = ? ORDER BY v.created_at DESC, v.id DESC",
        (user_id,),
    ).fetchall()


def get(vehicle_id: int):
    return get_db().execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()


def get_by_number(number: str):
    return get_db().execute("SELECT * FROM vehicles WHERE number = ?", (number,)).fetchone()


def create(user_id: int, number: str, vtype: str, owner_name: str) -> int:
    cur = get_db().execute(
        "INSERT INTO vehicles (user_id, number, type, owner_name) VALUES (?, ?, ?, ?)",
        (user_id, number, vtype, owner_name),
    )
    return cur.lastrowid


def update(vehicle_id: int, number: str, vtype: str, owner_name: str) -> None:
    get_db().execute(
        "UPDATE vehicles SET number = ?, type = ?, owner_name = ? WHERE id = ?",
        (number, vtype, owner_name, vehicle_id),
    )


def delete(vehicle_id: int) -> None:
    get_db().execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))


def has_history(vehicle_id: int) -> bool:
    return get_db().execute(
        "SELECT 1 FROM parking_sessions WHERE vehicle_id = ? LIMIT 1", (vehicle_id,)
    ).fetchone() is not None
