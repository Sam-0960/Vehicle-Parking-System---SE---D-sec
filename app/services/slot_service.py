"""Business Logic: Parking Slot Management (FR-03). Admin only."""
import re

from app.data import slot_repo
from app.services import ServiceError

SLOT_TYPES = ("car", "bike", "truck")
CODE_RE = re.compile(r"^[A-Z]{1,3}\d{1,3}$")  # A01, B12, TR3


def normalise_code(raw: str) -> str:
    return (raw or "").strip().upper()


def list_slots():
    return slot_repo.list_all()


def add(code: str, slot_type: str) -> int:
    code = normalise_code(code)
    if not CODE_RE.match(code):
        raise ServiceError("Slot ID must look like A01 (letters then a number).")
    if slot_type not in SLOT_TYPES:
        raise ServiceError("Choose a slot type: car, bike or truck.")
    if slot_repo.get_by_code(code):
        raise ServiceError(f"Slot {code} already exists.")
    return slot_repo.create(code, slot_type)


def add_range(prefix: str, start: int, end: int, slot_type: str) -> int:
    if not (1 <= start <= end <= 999) or end - start > 100:
        raise ServiceError("Enter a range of up to 100 slots between 1 and 999.")
    created = 0
    for n in range(start, end + 1):
        code = f"{normalise_code(prefix)}{n:02d}"
        if not slot_repo.get_by_code(code):
            add(code, slot_type)
            created += 1
    return created


def update(slot_id: int, slot_type: str, is_active: bool) -> None:
    slot = slot_repo.get(slot_id)
    if slot is None:
        raise ServiceError("Slot not found.")
    if slot_type not in SLOT_TYPES:
        raise ServiceError("Choose a slot type: car, bike or truck.")
    if slot_repo.is_occupied(slot_id) and (slot_type != slot["slot_type"] or not is_active):
        raise ServiceError(f"Slot {slot['code']} is occupied. Change it after the vehicle exits.")
    slot_repo.update(slot_id, slot_type, is_active)


def remove(slot_id: int) -> str:
    """Delete an unused slot; a slot with history is deactivated instead so records stay intact (NFR-03)."""
    slot = slot_repo.get(slot_id)
    if slot is None:
        raise ServiceError("Slot not found.")
    if slot_repo.is_occupied(slot_id):
        raise ServiceError(f"Slot {slot['code']} is occupied and cannot be removed.")
    if slot_repo.has_history(slot_id):
        slot_repo.update(slot_id, slot["slot_type"], False)
        return "deactivated"
    slot_repo.delete(slot_id)
    return "deleted"
