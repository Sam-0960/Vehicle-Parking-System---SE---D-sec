"""Business Logic: Vehicle Management (FR-02).

Users can only see and change their own vehicles (TB-01).
"""
import re

from app.data import vehicle_repo
from app.services import ServiceError

VEHICLE_TYPES = ("car", "bike", "truck")
# Indian registration format, e.g. KA01AB1234, KA051234, DL3CAF1234
NUMBER_RE = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{4}$")


def normalise_number(raw: str) -> str:
    return re.sub(r"[\s\-]", "", (raw or "")).upper()


def _validate(number: str, vtype: str, owner_name: str):
    number = normalise_number(number)
    if not number:
        raise ServiceError("Vehicle number is required.")
    if not NUMBER_RE.match(number):
        raise ServiceError("Enter a valid vehicle number, for example KA01AB1234.")
    if vtype not in VEHICLE_TYPES:
        raise ServiceError("Choose a vehicle type: car, bike or truck.")
    owner_name = (owner_name or "").strip()
    if not owner_name or len(owner_name) > 80:
        raise ServiceError("Owner name is required (up to 80 characters).")
    return number, vtype, owner_name


def list_mine(user_id: int):
    return vehicle_repo.list_for_user(user_id)


def get_owned(user_id: int, vehicle_id: int):
    v = vehicle_repo.get(vehicle_id)
    if v is None or v["user_id"] != user_id:
        raise ServiceError("Vehicle not found.")
    return v


def add(user_id: int, number: str, vtype: str, owner_name: str) -> int:
    number, vtype, owner_name = _validate(number, vtype, owner_name)
    if vehicle_repo.get_by_number(number):
        raise ServiceError(f"Vehicle {number} is already registered.")
    return vehicle_repo.create(user_id, number, vtype, owner_name)


def edit(user_id: int, vehicle_id: int, number: str, vtype: str, owner_name: str) -> None:
    get_owned(user_id, vehicle_id)
    number, vtype, owner_name = _validate(number, vtype, owner_name)
    other = vehicle_repo.get_by_number(number)
    if other and other["id"] != vehicle_id:
        raise ServiceError(f"Vehicle {number} is already registered.")
    vehicle_repo.update(vehicle_id, number, vtype, owner_name)


def remove(user_id: int, vehicle_id: int) -> None:
    get_owned(user_id, vehicle_id)
    if vehicle_repo.has_history(vehicle_id):
        raise ServiceError("This vehicle has parking records and cannot be deleted.")
    vehicle_repo.delete(vehicle_id)
