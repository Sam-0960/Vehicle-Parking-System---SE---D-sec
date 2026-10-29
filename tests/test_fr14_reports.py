"""FR-14 Reports - TC20."""
from datetime import datetime

import pytest

from app import clock
from tests.conftest import add_slot, add_vehicle, park, pay, unpark


@pytest.fixture
def activity(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_slot(admin_client, "M01", "bike")
    add_vehicle(user_client, "KA01AB1234")
    add_vehicle(user_client, "KA02CD5678", vtype="bike", owner="=HYPERLINK(evil)")
    for day, number, hours in ((24, "KA01AB1234", 2), (25, "KA01AB1234", 3), (25, "KA02CD5678", 1)):
        clock.set_now(datetime(2026, 10, day, 9, 0, 0))
        park(user_client, app, number)
        clock.set_now(datetime(2026, 10, day, 9 + hours, 0, 0))
        unpark(user_client, app, number)
        pay(user_client, app, number=number)
    clock.set_now(datetime(2026, 10, 26, 12, 0, 0))
    return admin_client


def test_report_generated_with_correct_figures_TC20(activity):
    page = activity.get("/admin/reports/?start=2026-10-24&end=2026-10-26").get_data(as_text=True)
    assert "₹270.00" in page          # 100 + 150 + 20
    assert ">3<" in page              # 3 sessions
    assert "09:00" in page            # peak entry hour
    assert "KA01AB1234" in page and "KA02CD5678" in page


def test_date_range_filters(activity):
    page = activity.get("/admin/reports/?start=2026-10-25&end=2026-10-25").get_data(as_text=True)
    assert "₹170.00" in page


def test_csv_exports(activity):
    resp = activity.get("/admin/reports/revenue.csv?start=2026-10-24&end=2026-10-26")
    assert resp.mimetype == "text/csv"
    body = resp.get_data(as_text=True)
    assert "2026-10-24,1,100.00" in body and "2026-10-25,2,170.00" in body
    usage = activity.get("/admin/reports/usage.csv?start=2026-10-24&end=2026-10-26").get_data(as_text=True)
    assert "A01,car,2" in usage


def test_csv_formula_injection_neutralised(activity):
    body = activity.get("/admin/reports/activity.csv?start=2026-10-24&end=2026-10-26").get_data(as_text=True)
    assert "'=HYPERLINK(evil)" in body


def test_bad_range(activity):
    page = activity.get("/admin/reports/?start=2026-10-26&end=2026-10-01").get_data(as_text=True)
    assert "end date must be on or after" in page
    assert activity.get("/admin/reports/nope.csv").status_code == 400


def test_user_cannot_see_reports(user_client):
    assert user_client.get("/admin/reports/").status_code == 403
    assert user_client.get("/admin/reports/revenue.csv").status_code == 403
