"""FR-11 Notifications - reservation confirmation, parking expiry, payment status."""
from datetime import datetime

from app import clock
from app.data.db import get_db
from tests.conftest import (BAD_CARD, add_slot, add_vehicle, login, park, pay, post, register,
                            reserve, unpark)


def _messages(app):
    with app.app_context():
        return [r["message"] for r in get_db().execute("SELECT message FROM notifications ORDER BY id")]


def _setup(app, admin, user):
    clock.set_now(datetime(2026, 10, 26, 9, 0, 0))
    add_slot(admin, "A01")
    add_vehicle(user)


def test_reservation_confirmation(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    reserve(user_client, app)
    assert any("Reservation confirmed: slot A01" in m for m in _messages(app))


def test_reservation_cancellation(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    reserve(user_client, app)
    with app.app_context():
        pid = get_db().execute("SELECT public_id FROM reservations").fetchone()["public_id"]
    post(user_client, f"/reservations/{pid}/cancel", page="/reservations/")
    assert any("cancelled" in m for m in _messages(app))


def test_expiry_warning_sent_once(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    reserve(user_client, app, start="2026-10-26T10:00", end="2026-10-26T12:00")
    clock.set_now(datetime(2026, 10, 26, 11, 50, 0))
    user_client.get("/")
    user_client.get("/")
    warnings = [m for m in _messages(app) if "ends at 12:00" in m]
    assert len(warnings) == 1


def test_overstay_alert(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    clock.set_now(datetime(2026, 10, 26, 10, 0, 0))
    reserve(user_client, app, start="2026-10-26T10:00", end="2026-10-26T11:00")
    park(user_client, app)
    clock.set_now(datetime(2026, 10, 26, 11, 20, 0))
    user_client.get("/")
    assert any("Parking time for KA01AB1234" in m for m in _messages(app))


def test_payment_status_notices(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    park(user_client, app)
    clock.set_now(datetime(2026, 10, 26, 10, 30, 0))
    unpark(user_client, app)
    pay(user_client, app, BAD_CARD)
    pay(user_client, app)
    msgs = _messages(app)
    assert any("failed" in m for m in msgs)
    assert any("Payment of ₹100.00 received" in m for m in msgs)
    assert not any("4111" in m or "0002" in m for m in msgs)


def test_badge_and_inbox_marks_read(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    reserve(user_client, app)
    assert b'class="badge">1<' in user_client.get("/vehicles/").data
    assert b"Reservation confirmed" in user_client.get("/notifications/").data
    assert b'class="badge"' not in user_client.get("/vehicles/").data


def test_notifications_are_private(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    reserve(user_client, app)
    other = app.test_client()
    register(other, name="Asha", email="asha@test.com")
    login(other, "asha@test.com")
    assert b"Reservation confirmed" not in other.get("/notifications/").data
