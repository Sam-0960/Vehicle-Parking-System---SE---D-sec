"""Business Logic: Admin Dashboard (FR-12).

Occupancy, active vehicles, reservations and revenue in one view.
"""
from datetime import timedelta

from app import clock
from app.data import audit_repo, session_repo, stats_repo
from app.services import reservation_service


def overview():
    now = clock.now()
    today = now.replace(hour=0, minute=0, second=0)
    month = today.replace(day=1)
    tomorrow = today + timedelta(days=1)
    fmt = clock.to_str

    by_type = [dict(r) for r in stats_repo.occupancy_by_type()]
    total = sum(r["total"] for r in by_type)
    occupied = sum(r["occupied"] for r in by_type)
    for r in by_type:
        r["pct"] = round(100 * r["occupied"] / r["total"]) if r["total"] else 0

    unpaid_n, unpaid_amount = stats_repo.unpaid_total()
    reservations = reservation_service.upcoming()
    active_now = [r for r in reservations if r["start_time"] <= fmt(now)]

    return {
        "occupancy": {"total": total, "occupied": occupied, "free": total - occupied,
                      "pct": round(100 * occupied / total) if total else 0, "by_type": by_type},
        "active": session_repo.all_active(),
        "reservations": {"upcoming": reservations[:10], "count": len(reservations),
                         "active_now": len(active_now)},
        "revenue": {"today": stats_repo.revenue_between(fmt(today), fmt(tomorrow)),
                    "month": stats_repo.revenue_between(fmt(month), fmt(tomorrow)),
                    "total": stats_repo.revenue_total(),
                    "unpaid_count": unpaid_n, "unpaid_amount": unpaid_amount},
        "entries_today": stats_repo.sessions_started_between(fmt(today), fmt(tomorrow)),
        "audit": audit_repo.recent(15),
    }
