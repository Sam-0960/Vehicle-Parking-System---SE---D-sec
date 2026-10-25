"""Business Logic: Entry & Exit Management (FR-05, FR-06).

Slot allocation runs inside an IMMEDIATE transaction, and the database has a
unique index on active sessions per slot, so one slot can never hold two
vehicles even under concurrent requests (NFR-08, T-08).
"""
import sqlite3

from app import clock
from app.data import session_repo, slot_repo, vehicle_repo
from app.data.db import transaction
from app.services import fee_service, reservation_service
from app.services import ConflictError, ServiceError


def _vehicle_for(actor, vehicle_id=None, number=None):
    v = vehicle_repo.get(vehicle_id) if vehicle_id else vehicle_repo.get_by_number(number or "")
    if v is None:
        raise ServiceError("Vehicle not found. Register it first.")
    if actor["role"] != "admin" and v["user_id"] != actor["id"]:
        raise ServiceError("Vehicle not found. Register it first.")
    return v


def enter(actor, vehicle_id=None, number=None, slot_code: str = ""):
    """Record vehicle entry and allocate a slot. Returns the new session row."""
    v = _vehicle_for(actor, vehicle_id, number)
    now = clock.to_str(clock.now())

    try:
        with transaction(immediate=True) as conn:
            if session_repo.active_for_vehicle(v["id"]):
                raise ServiceError(f"{v['number']} is already parked.")

            reserved = reservation_service.claim_for_entry(conn, v["id"], now)
            slot = reserved if reserved is not None and not slot_code else _choose_slot(v, now, slot_code)
            session_id = session_repo.insert_entry(conn, v["id"], slot["id"], now)
    except sqlite3.IntegrityError:
        raise ConflictError("That slot was just taken. Please choose another slot.")
    return session_repo.get(session_id)


def _choose_slot(vehicle, now: str, slot_code: str):
    free = session_repo.free_slots(vehicle["type"], now, exclude_reserved_for_user=vehicle["user_id"])
    if slot_code:
        wanted = slot_repo.get_by_code(slot_code.strip().upper())
        if wanted is None or not wanted["is_active"]:
            raise ServiceError("That slot does not exist.")
        if wanted["slot_type"] != vehicle["type"]:
            raise ServiceError(f"Slot {wanted['code']} is for {wanted['slot_type']}s, "
                               f"but {vehicle['number']} is a {vehicle['type']}.")
        if wanted["id"] not in {s["id"] for s in free}:
            raise ConflictError(f"Slot {wanted['code']} is not available right now.")
        return wanted
    if not free:
        raise ConflictError(f"No {vehicle['type']} parking slot is currently available.")
    return free[0]


def active_sessions(actor):
    rows = session_repo.all_active() if actor["role"] == "admin" else session_repo.active_for_user(actor["id"])
    return [{**dict(r), "fee_so_far": fee_service.for_session(r)} for r in rows]


def free_slots_for(vehicle):
    return session_repo.free_slots(vehicle["type"], clock.to_str(clock.now()),
                                   exclude_reserved_for_user=vehicle["user_id"])


def _fee_for(session, exit_dt):
    return fee_service.for_session(session, exit_dt)


def leave(actor, session_id: int):
    """Record vehicle exit and release the slot. Returns the closed session row."""
    s = session_repo.get(session_id)
    if s is None or (actor["role"] != "admin" and s["user_id"] != actor["id"]):
        raise ServiceError("Parking session not found.")
    if s["exit_time"]:
        raise ServiceError(f"{s['vehicle_number']} has already exited.")
    exit_dt = clock.now()
    fee = _fee_for(s, exit_dt)
    status = "paid" if fee == 0 else "unpaid"  # grace-period stays need no payment
    with transaction(immediate=True) as conn:
        changed = session_repo.record_exit(conn, session_id, clock.to_str(exit_dt), fee, status)
    if not changed:
        raise ConflictError(f"{s['vehicle_number']} has already exited.")
    return session_repo.get(session_id)
