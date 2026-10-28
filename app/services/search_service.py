"""Business Logic: Search Vehicle (FR-13). Admin only.

Matches vehicle number (ignoring spaces/hyphens), owner name, owner email or
the slot a vehicle is parked in.
"""
from app.data import vehicle_repo
from app.services import ServiceError, history_service
from app.services.vehicle_service import normalise_number


def search(query: str):
    term = (query or "").strip()
    if len(term) < 2:
        raise ServiceError("Type at least 2 characters to search.")
    if len(term) > 60:
        raise ServiceError("Search text is too long.")
    return vehicle_repo.search(term, normalise_number(term))


def vehicle_detail(vehicle_id: int):
    v = vehicle_repo.get(vehicle_id)
    if v is None:
        raise ServiceError("Vehicle not found.")
    return v, history_service.for_vehicle_admin(vehicle_id)
