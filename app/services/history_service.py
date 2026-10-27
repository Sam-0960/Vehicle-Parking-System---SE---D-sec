"""Business Logic: Parking History Service (FR-10).

Customers see only their own sessions (SO-01, TB-01).
"""
from app.data import session_repo, vehicle_repo
from app.services import ServiceError


def fmt_duration(minutes) -> str:
    minutes = int(minutes or 0)
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def for_user(user, vehicle_id=None):
    if vehicle_id is not None:
        v = vehicle_repo.get(vehicle_id)
        if v is None or v["user_id"] != user["id"]:
            raise ServiceError("Vehicle not found.")
    rows = session_repo.history(user_id=user["id"], vehicle_id=vehicle_id)
    return _with_totals(rows)


def for_vehicle_admin(vehicle_id: int):
    return _with_totals(session_repo.history(vehicle_id=vehicle_id))


def _with_totals(rows):
    total_fee = sum(r["fee"] or 0 for r in rows)
    total_minutes = sum(r["minutes"] or 0 for r in rows)
    return {"sessions": rows, "count": len(rows), "total_fee": total_fee,
            "total_time": fmt_duration(total_minutes)}
