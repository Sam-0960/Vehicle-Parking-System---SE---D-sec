"""Data Layer: tariff settings (NFR-07)."""
from app.data.db import get_db


def all_rates():
    return get_db().execute("SELECT * FROM rates ORDER BY vehicle_type").fetchall()


def get(vehicle_type: str):
    return get_db().execute("SELECT * FROM rates WHERE vehicle_type = ?", (vehicle_type,)).fetchone()


def update(vehicle_type: str, hourly_rate: float, daily_cap: float, grace_minutes: int) -> None:
    get_db().execute(
        "UPDATE rates SET hourly_rate = ?, daily_cap = ?, grace_minutes = ? WHERE vehicle_type = ?",
        (hourly_rate, daily_cap, grace_minutes, vehicle_type),
    )
