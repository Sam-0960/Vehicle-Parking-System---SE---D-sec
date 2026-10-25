"""Business Logic: Fee Calculation / Billing Service (FR-08).

Rules (rates are editable by admins, NFR-07):
  * Stays within the grace period are free.
  * Otherwise every started hour is charged at the hourly rate.
  * Each full 24 hours costs at most the daily cap, and so does the remainder.

The fee is always computed on the server from recorded times; the client never
sends an amount (C-05, T-06).
"""
import math
from datetime import datetime

from app import clock
from app.data import rate_repo
from app.services import ServiceError


def calculate(vehicle_type: str, entry: datetime, exit_: datetime) -> float:
    rate = rate_repo.get(vehicle_type)
    if rate is None:
        raise ServiceError(f"No tariff configured for {vehicle_type}.")
    minutes = max(0, math.ceil((exit_ - entry).total_seconds() / 60))
    if minutes <= rate["grace_minutes"]:
        return 0.0
    days, rest = divmod(minutes, 24 * 60)
    part_day = min(math.ceil(rest / 60) * rate["hourly_rate"], rate["daily_cap"])
    return round(days * rate["daily_cap"] + part_day, 2)


def for_session(session, exit_dt: datetime = None) -> float:
    return calculate(session["vehicle_type"], clock.parse(session["entry_time"]), exit_dt or clock.now())


def describe(rate) -> str:
    return (f"₹{rate['hourly_rate']:.0f} per started hour, max ₹{rate['daily_cap']:.0f} per day, "
            f"first {rate['grace_minutes']} minutes free")


def rates():
    return rate_repo.all_rates()


def update_rate(vehicle_type: str, hourly: str, cap: str, grace: str) -> None:
    if rate_repo.get(vehicle_type) is None:
        raise ServiceError("Unknown vehicle type.")
    try:
        hourly_f, cap_f, grace_i = float(hourly), float(cap), int(grace)
    except (TypeError, ValueError):
        raise ServiceError("Rates must be numbers.")
    if not (0 < hourly_f <= 10000) or not (0 < cap_f <= 100000) or not (0 <= grace_i <= 120):
        raise ServiceError("Rates out of range.")
    if cap_f < hourly_f:
        raise ServiceError("Daily cap cannot be lower than the hourly rate.")
    rate_repo.update(vehicle_type, hourly_f, cap_f, grace_i)
