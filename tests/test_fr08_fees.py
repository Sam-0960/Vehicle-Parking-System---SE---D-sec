"""FR-08 Parking Fee Calculation - TC14, NFR-07, T-06."""
from datetime import datetime

import pytest

from app import clock
from app.data.db import get_db
from app.services import fee_service
from tests.conftest import add_slot, add_vehicle, park, post, unpark

T0 = datetime(2026, 10, 26, 9, 0, 0)


def at(h=0, m=0, d=0):
    from datetime import timedelta
    return T0 + timedelta(days=d, hours=h, minutes=m)


@pytest.mark.parametrize("vtype,end,expected", [
    ("car", at(m=5), 0),             # inside grace period
    ("car", at(m=45), 50),           # first started hour
    ("car", at(h=2), 100),           # Test Plan sample ₹100
    ("car", at(h=2, m=1), 150),      # Test Plan sample ₹150 (third hour started)
    ("car", at(h=12), 400),          # capped at daily max
    ("car", at(d=1, h=1), 450),      # one full day + one hour
    ("bike", at(h=3), 60),
    ("truck", at(h=1, m=30), 200),
])
def test_fee_rules_TC14(app, vtype, end, expected):
    with app.app_context():
        assert fee_service.calculate(vtype, T0, end) == expected


def test_exit_charges_server_side_fee_TC14_T06(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    clock.set_now(T0)
    park(user_client, app)
    clock.set_now(at(h=2, m=30))
    with app.app_context():
        sid = get_db().execute("SELECT id FROM parking_sessions").fetchone()["id"]
    # A tampered "fee" field from the client is ignored.
    post(user_client, f"/parking/exit/{sid}", {"fee": "1"}, page="/parking/")
    with app.app_context():
        row = get_db().execute("SELECT fee, status FROM parking_sessions").fetchone()
    assert row["fee"] == 150 and row["status"] == "unpaid"


def test_grace_period_exit_needs_no_payment(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    clock.set_now(T0)
    park(user_client, app)
    clock.set_now(at(m=8))
    unpark(user_client, app)
    with app.app_context():
        row = get_db().execute("SELECT fee, status FROM parking_sessions").fetchone()
    assert row["fee"] == 0 and row["status"] == "paid"


def test_admin_changes_rate_NFR07(app, admin_client):
    resp = post(admin_client, "/admin/rates", {"vehicle_type": "car", "hourly_rate": "60",
                                              "daily_cap": "500", "grace_minutes": "0"})
    assert resp.status_code == 302
    with app.app_context():
        assert fee_service.calculate("car", T0, at(h=2)) == 120


def test_rate_validation(admin_client):
    resp = post(admin_client, "/admin/rates", {"vehicle_type": "car", "hourly_rate": "100",
                                              "daily_cap": "50", "grace_minutes": "0"})
    assert b"cannot be lower" in resp.data


def test_user_cannot_change_rates(user_client):
    assert user_client.get("/admin/rates").status_code == 403


def test_fee_so_far_shown(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    clock.set_now(T0)
    park(user_client, app)
    clock.set_now(at(h=1, m=10))
    assert "₹100.00" in user_client.get("/parking/").get_data(as_text=True)
