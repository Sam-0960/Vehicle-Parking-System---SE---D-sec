"""Business Logic: Parking Availability Service (FR-04).

Reads slot status through Parking Slot Management data (component diagram note).
"""
from app import clock
from app.data import slot_repo

STATES = ("available", "occupied", "reserved")


def snapshot(slot_type: str = ""):
    rows = slot_repo.availability(clock.to_str(clock.now()))
    if slot_type:
        rows = [r for r in rows if r["slot_type"] == slot_type]
    counts = {state: 0 for state in STATES}
    for r in rows:
        counts[r["state"]] += 1
    return {"slots": rows, "counts": counts, "total": len(rows)}


def has_free_slot(slot_type: str) -> bool:
    return snapshot(slot_type)["counts"]["available"] > 0
