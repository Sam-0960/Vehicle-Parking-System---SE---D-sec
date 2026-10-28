"""FR-12 Admin Dashboard - TC19, NFT02."""
from datetime import datetime

from app import clock
from tests.conftest import add_slot, add_vehicle, park, pay, reserve, unpark


def test_dashboard_shows_occupancy_vehicles_reservations_revenue_TC19(app, admin_client, user_client):
    clock.set_now(datetime(2026, 10, 26, 9, 0, 0))
    for code in ("A01", "A02", "A03", "A04"):
        add_slot(admin_client, code)
    add_vehicle(user_client, "KA01AB1234")
    add_vehicle(user_client, "KA02CD5678")
    park(user_client, app, "KA01AB1234")
    clock.set_now(datetime(2026, 10, 26, 11, 0, 0))
    unpark(user_client, app, "KA01AB1234")
    pay(user_client, app)
    park(user_client, app, "KA02CD5678")
    reserve(user_client, app, slot="A04", start="2026-10-26T15:00", end="2026-10-26T16:00",
            number="KA01AB1234")
    page = admin_client.get("/admin/").get_data(as_text=True)
    assert "25%" in page                      # 1 of 4 slots occupied
    assert "KA02CD5678" in page               # active vehicle
    assert "Open reservations" in page and ">1<" in page
    assert "₹100.00" in page                  # revenue today
    assert "payment_success" in page          # security events feed


def test_admin_login_lands_on_dashboard(admin_client):
    resp = admin_client.get("/")
    assert resp.headers["Location"].endswith("/admin/")


def test_user_cannot_open_dashboard_NFT02(user_client):
    assert user_client.get("/admin/").status_code == 403


def test_dashboard_shows_unpaid_after_exit(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    clock.set_now(datetime(2026, 10, 26, 9, 0, 0))
    park(user_client, app)
    clock.set_now(datetime(2026, 10, 26, 11, 0, 0))
    unpark(user_client, app)
    page = admin_client.get("/admin/").get_data(as_text=True)
    assert "100.00 (1 sessions)" in page
