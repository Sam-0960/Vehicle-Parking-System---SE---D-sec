"""Business Logic: Reports (FR-14) - parking usage, revenue and vehicle activity."""
import csv
import io
from datetime import datetime, timedelta

from app import clock
from app.data import stats_repo
from app.services import ServiceError

KINDS = ("usage", "revenue", "activity")
MAX_DAYS = 366


def parse_range(start_raw: str, end_raw: str):
    today = clock.now().date()
    try:
        start = datetime.strptime(start_raw, "%Y-%m-%d").date() if start_raw else today - timedelta(days=6)
        end = datetime.strptime(end_raw, "%Y-%m-%d").date() if end_raw else today
    except ValueError:
        raise ServiceError("Dates must be in YYYY-MM-DD format.")
    if end < start:
        raise ServiceError("The end date must be on or after the start date.")
    if (end - start).days > MAX_DAYS:
        raise ServiceError("Reports can cover at most one year.")
    return start, end


def build(start, end):
    s = f"{start} 00:00:00"
    e = f"{end + timedelta(days=1)} 00:00:00"  # end date is inclusive
    until = min(e, clock.to_str(clock.now()))  # vehicles still parked count up to now
    usage = stats_repo.usage_by_day(s, e)
    revenue = stats_repo.revenue_by_day(s, e)
    return {
        "start": start, "end": end,
        "usage": {"by_day": usage, "total_sessions": sum(r["sessions"] for r in usage),
                  "peak_hours": stats_repo.peak_hours(s, e), "slots": stats_repo.slot_utilisation(s, e, until)},
        "revenue": {"by_day": revenue, "by_method": stats_repo.revenue_by_method(s, e),
                    "by_type": stats_repo.revenue_by_vehicle_type(s, e),
                    "total": sum(r["amount"] for r in revenue),
                    "payments": sum(r["payments"] for r in revenue),
                    "failed": stats_repo.failed_payments(s, e)},
        "activity": stats_repo.vehicle_activity(s, e, until),
    }


def to_csv(kind: str, report) -> str:
    if kind not in KINDS:
        raise ServiceError("Unknown report.")
    out = io.StringIO()
    w = csv.writer(out)
    if kind == "usage":
        w.writerow(["date", "sessions", "avg_minutes"])
        for r in report["usage"]["by_day"]:
            w.writerow([r["day"], r["sessions"], r["avg_minutes"] or ""])
        w.writerow([])
        w.writerow(["slot", "type", "sessions", "hours_occupied"])
        for r in report["usage"]["slots"]:
            w.writerow([r["code"], r["slot_type"], r["sessions"], r["hours"]])
    elif kind == "revenue":
        w.writerow(["date", "payments", "amount_inr"])
        for r in report["revenue"]["by_day"]:
            w.writerow([r["day"], r["payments"], f"{r['amount']:.2f}"])
        w.writerow([])
        w.writerow(["method", "payments", "amount_inr"])
        for r in report["revenue"]["by_method"]:
            w.writerow([r["method"], r["payments"], f"{r['amount']:.2f}"])
    else:
        w.writerow(["vehicle", "type", "owner", "visits", "hours", "fees_inr", "last_entry"])
        for r in report["activity"]:
            w.writerow([r["number"], r["type"], _safe_cell(r["owner_name"]), r["visits"], r["hours"],
                        f"{r['fees']:.2f}", r["last_entry"]])
    return out.getvalue()


def _safe_cell(value: str) -> str:
    """Stop spreadsheet formula injection from user-entered text (R-04)."""
    return "'" + value if value and value[0] in "=+-@" else value
