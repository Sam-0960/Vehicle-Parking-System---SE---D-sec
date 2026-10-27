"""FR-10 Parking History - TC17, T-05."""
from datetime import datetime

from app import clock
from tests.conftest import add_slot, add_vehicle, login, park, pay, register, unpark, vehicle_id


def _one_session(app, admin, user):
    add_slot(admin, "A01")
    add_vehicle(user)
    clock.set_now(datetime(2026, 10, 26, 9, 0, 0))
    park(user, app)
    clock.set_now(datetime(2026, 10, 26, 10, 45, 0))
    unpark(user, app)
    pay(user, app)


def test_history_shows_entry_exit_slot_fee_TC17(app, admin_client, user_client):
    _one_session(app, admin_client, user_client)
    page = user_client.get("/history/").get_data(as_text=True)
    for expected in ("KA01AB1234", "A01", "2026-10-26 09:00", "2026-10-26 10:45", "1h 45m", "₹100.00", "paid"):
        assert expected in page


def test_active_sessions_not_in_history(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    park(user_client, app)
    assert b"No completed parking sessions" in user_client.get("/history/").data


def test_filter_by_vehicle(app, admin_client, user_client):
    _one_session(app, admin_client, user_client)
    add_vehicle(user_client, "KA02CD5678")
    vid = vehicle_id(app, "KA02CD5678")
    assert b"No completed parking sessions" in user_client.get(f"/history/?vehicle={vid}").data


def test_history_is_private_T05(app, admin_client, user_client):
    _one_session(app, admin_client, user_client)
    other = app.test_client()
    register(other, name="Asha", email="asha@test.com")
    login(other, "asha@test.com")
    assert b"<strong>KA01AB1234" not in other.get("/history/").data
    assert other.get(f"/history/?vehicle={vehicle_id(app)}").status_code == 404


def test_totals_add_up_for_two_sessions(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    for start, end in ((9, 11), (13, 14)):
        clock.set_now(datetime(2026, 10, 26, start, 0, 0))
        park(user_client, app)
        clock.set_now(datetime(2026, 10, 26, end, 0, 0))
        unpark(user_client, app)
        pay(user_client, app)
    page = user_client.get("/history/").get_data(as_text=True)
    assert "3h 00m" in page
    assert "150.00" in page
