"""FR-07 Parking Reservation - TC12, TC13, T-05, T-07, T-08."""
from datetime import datetime

import pytest

from app import clock
from app.data.db import get_db
from tests.conftest import add_slot, add_vehicle, login, park, post, register, reserve


@pytest.fixture
def setup(app, admin_client, user_client):
    clock.set_now(datetime(2026, 10, 26, 9, 0, 0))
    add_slot(admin_client, "A01")
    add_slot(admin_client, "A02")
    add_vehicle(user_client)
    return app, admin_client, user_client


def _reservations(app):
    with app.app_context():
        return get_db().execute("SELECT * FROM reservations").fetchall()


def test_reserve_available_slot_TC12(setup):
    app, _, user = setup
    assert reserve(user, app).status_code == 302
    rows = _reservations(app)
    assert len(rows) == 1 and rows[0]["status"] == "confirmed"
    assert len(rows[0]["public_id"]) >= 12  # unpredictable id (C-05)


def test_end_before_start_rejected_TC13(setup):
    app, _, user = setup
    resp = reserve(user, app, start="2026-10-26T12:00", end="2026-10-26T10:00")
    assert b"End time must be after the start time" in resp.data
    assert _reservations(app) == []


def test_past_start_rejected(setup):
    app, _, user = setup
    assert b"cannot be in the past" in reserve(user, app, start="2026-10-25T10:00", end="2026-10-25T12:00").data


def test_overlapping_reservation_rejected(setup):
    app, _, user = setup
    reserve(user, app)
    add_vehicle(user, "KA02CD5678")
    resp = reserve(user, app, start="2026-10-26T11:00", end="2026-10-26T13:00", number="KA02CD5678")
    assert b"already reserved" in resp.data
    assert len(_reservations(app)) == 1


def test_reserved_slot_hidden_from_others_at_entry(setup):
    app, _, user = setup
    clock.set_now(datetime(2026, 10, 26, 10, 30, 0))
    reserve(user, app, slot="A01", start="2026-10-26T10:30", end="2026-10-26T12:00")
    other = app.test_client()
    register(other, name="Asha", email="asha@test.com")
    login(other, "asha@test.com")
    add_vehicle(other, "KA03EF9012", owner="Asha")
    park(other, app, "KA03EF9012")
    with app.app_context():
        code = get_db().execute("SELECT s.code FROM parking_sessions p JOIN slots s ON s.id=p.slot_id").fetchone()["code"]
    assert code == "A02"


def test_entry_uses_reserved_slot(setup):
    app, _, user = setup
    clock.set_now(datetime(2026, 10, 26, 10, 0, 0))
    reserve(user, app, slot="A02", start="2026-10-26T10:00", end="2026-10-26T12:00")
    park(user, app)
    with app.app_context():
        db = get_db()
        code = db.execute("SELECT s.code FROM parking_sessions p JOIN slots s ON s.id=p.slot_id").fetchone()["code"]
        status = db.execute("SELECT status FROM reservations").fetchone()["status"]
    assert code == "A02" and status == "used"


def test_replayed_request_creates_one_reservation_T07(setup):
    app, _, user = setup
    reserve(user, app, key="same-key-123")
    resp = reserve(user, app, key="same-key-123")
    assert len(_reservations(app)) == 1
    assert b"already submitted" in user.get("/reservations/").data or resp.status_code == 302


def test_cancel_and_ownership_T05(setup):
    app, _, user = setup
    reserve(user, app)
    pid = _reservations(app)[0]["public_id"]
    other = app.test_client()
    register(other, name="Asha", email="asha@test.com")
    login(other, "asha@test.com")
    post(other, f"/reservations/{pid}/cancel", page="/reservations/")
    assert _reservations(app)[0]["status"] == "confirmed"
    post(user, f"/reservations/{pid}/cancel", page="/reservations/")
    assert _reservations(app)[0]["status"] == "cancelled"


def test_open_reservation_cap(setup):
    app, admin, user = setup
    add_slot(admin, "A03")
    add_slot(admin, "A04")
    for code in ("A01", "A02", "A03"):
        reserve(user, app, slot=code)
    resp = reserve(user, app, slot="A04")
    assert b"at most 3 open reservations" in resp.data


def test_past_reservations_expire(setup):
    app, _, user = setup
    reserve(user, app)
    clock.set_now(datetime(2026, 10, 26, 13, 0, 0))
    user.get("/reservations/")
    assert _reservations(app)[0]["status"] == "expired"


def test_admin_sees_upcoming(setup):
    app, admin, user = setup
    reserve(user, app)
    assert b"KA01AB1234" in admin.get("/reservations/").data
