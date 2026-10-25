"""Business Logic: Parking Reservation Service (FR-07).

Controls: SO-03 replay protection (idempotency key), C-05 ownership checks and
unpredictable IDs, C-07 cap on open reservations per user (R-08 slot hoarding).
"""
import secrets
from datetime import datetime, timedelta

from app import clock
from app.data import reservation_repo, session_repo, slot_repo, vehicle_repo
from app.data.db import transaction
from app.services import ConflictError, ServiceError

MAX_HOURS = 24
MAX_DAYS_AHEAD = 7
MAX_OPEN_PER_USER = 3


def parse_local(value: str) -> datetime:
    """Accept the HTML datetime-local format (2026-10-26T14:30)."""
    try:
        return datetime.strptime((value or "").strip()[:16], "%Y-%m-%dT%H:%M")
    except ValueError:
        raise ServiceError("Enter a valid start and end time.")


def validate_window(start: datetime, end: datetime, now: datetime) -> None:
    if end <= start:
        raise ServiceError("End time must be after the start time.")
    if start < now - timedelta(minutes=5):
        raise ServiceError("Start time cannot be in the past.")
    if end - start > timedelta(hours=MAX_HOURS):
        raise ServiceError(f"A reservation can be at most {MAX_HOURS} hours long.")
    if start > now + timedelta(days=MAX_DAYS_AHEAD):
        raise ServiceError(f"You can reserve up to {MAX_DAYS_AHEAD} days ahead.")


def reserve(user, vehicle_id: int, slot_code: str, start_raw: str, end_raw: str, key: str):
    if key:
        existing = reservation_repo.get_by_key(key)
        if existing is not None:
            return existing, False  # replayed form: return the original, create nothing

    vehicle = vehicle_repo.get(vehicle_id)
    if vehicle is None or vehicle["user_id"] != user["id"]:
        raise ServiceError("Choose one of your vehicles.")
    slot = slot_repo.get_by_code((slot_code or "").strip().upper())
    if slot is None or not slot["is_active"]:
        raise ServiceError("Choose a valid slot.")
    if slot["slot_type"] != vehicle["type"]:
        raise ServiceError(f"Slot {slot['code']} is for {slot['slot_type']}s.")

    now = clock.now()
    start, end = parse_local(start_raw), parse_local(end_raw)
    validate_window(start, end, now)
    s, e, n = clock.to_str(start), clock.to_str(end), clock.to_str(now)

    with transaction(immediate=True) as conn:
        if reservation_repo.count_open_for_user(user["id"], n) >= MAX_OPEN_PER_USER:
            raise ServiceError(f"You can hold at most {MAX_OPEN_PER_USER} open reservations.")
        if reservation_repo.overlapping(slot["id"], s, e):
            raise ConflictError(f"Slot {slot['code']} is already reserved for part of that time.")
        if start <= now and slot_repo.is_occupied(slot["id"]):
            raise ConflictError(f"Slot {slot['code']} is occupied right now.")
        public_id = secrets.token_urlsafe(9)
        reservation_repo.insert(conn, public_id, user["id"], vehicle["id"], slot["id"], s, e, key or None)
    return reservation_repo.get_by_public_id(public_id), True


def cancel(user, public_id: str):
    r = reservation_repo.get_by_public_id(public_id or "")
    if r is None or (r["user_id"] != user["id"] and user["role"] != "admin"):
        raise ServiceError("Reservation not found.")
    if r["status"] != "confirmed":
        raise ServiceError("Only confirmed reservations can be cancelled.")
    reservation_repo.set_status(r["id"], "cancelled")
    return r


def mine(user):
    reservation_repo.expire_past(clock.to_str(clock.now()))
    return reservation_repo.for_user(user["id"])


def upcoming():
    now = clock.to_str(clock.now())
    reservation_repo.expire_past(now)
    return reservation_repo.upcoming_all(now)


def bookable_slots(vehicle_type: str):
    return [s for s in slot_repo.list_all() if s["is_active"] and s["slot_type"] == vehicle_type]


def claim_for_entry(conn, vehicle_id: int, now: str):
    """At entry, a vehicle with a reservation covering now goes to its reserved slot."""
    r = reservation_repo.active_for_vehicle(vehicle_id, now)
    if r is None:
        return None
    reservation_repo.set_status(r["id"], "used", conn)
    return slot_repo.get(r["slot_id"])
