"""FR-09 Payment Management - TC15, TC16, T-06, T-07, T-11, T-14."""
from datetime import datetime

import pytest

from app import clock
from app.data.db import get_db
from tests.conftest import (BAD_CARD, GOOD_CARD, add_slot, add_vehicle, login, park, pay,
                            post, register, session_id_of, unpark)


@pytest.fixture
def unpaid(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    clock.set_now(datetime(2026, 10, 26, 9, 0, 0))
    park(user_client, app)
    clock.set_now(datetime(2026, 10, 26, 11, 0, 0))
    resp = unpark(user_client, app)
    assert "/payments/session/" in resp.headers["Location"]  # exit leads straight to payment
    return app, admin_client, user_client


def _payments(app):
    with app.app_context():
        return get_db().execute("SELECT * FROM payments").fetchall()


def _session_status(app):
    with app.app_context():
        return get_db().execute("SELECT status FROM parking_sessions").fetchone()["status"]


def test_successful_card_payment_TC15(unpaid):
    app, _, user = unpaid
    resp = pay(user, app)
    assert "/payments/receipt/" in resp.headers["Location"]
    rows = _payments(app)
    assert len(rows) == 1 and rows[0]["status"] == "success" and rows[0]["amount"] == 100
    assert _session_status(app) == "paid"
    receipt = user.get(resp.headers["Location"]).get_data(as_text=True)
    assert "₹100.00" in receipt and "card ****1111" in receipt


def test_upi_payment(unpaid):
    app, _, user = unpaid
    pay(user, app, {"method": "upi", "upi_id": "ravi@okbank"})
    assert _session_status(app) == "paid"


def test_declined_payment_not_marked_paid_TC16(unpaid):
    app, _, user = unpaid
    resp = pay(user, app, BAD_CARD)
    assert b"Payment failed" in resp.data
    assert _payments(app)[0]["status"] == "failed"
    assert _session_status(app) == "unpaid"
    pay(user, app)  # retry with a working card (use case alternate flow 7b)
    assert _session_status(app) == "paid"


def test_failed_upi(unpaid):
    app, _, user = unpaid
    pay(user, app, {"method": "upi", "upi_id": "fail@okbank"})
    assert _session_status(app) == "unpaid"


def test_invalid_card_rejected_before_gateway(unpaid):
    app, _, user = unpaid
    resp = pay(user, app, {**GOOD_CARD, "card_number": "1234 5678 9012 3456"})
    assert b"valid card number" in resp.data
    assert _payments(app) == []


def test_expired_card(unpaid):
    app, _, user = unpaid
    assert b"expired" in pay(user, app, {**GOOD_CARD, "expiry": "01/24"}).data


def test_tampered_amount_ignored_T06(unpaid):
    app, _, user = unpaid
    pay(user, app, {**GOOD_CARD, "amount": "1"})
    assert _payments(app)[0]["amount"] == 100


def test_replayed_payment_charges_once_T07(unpaid):
    app, _, user = unpaid
    pay(user, app, key="replay-key-1")
    pay(user, app, key="replay-key-1")
    pay(user, app)  # a fresh submit after paying is refused
    assert len(_payments(app)) == 1


def test_card_data_never_stored_T11_T14(unpaid):
    app, _, user = unpaid
    pay(user, app)
    with app.app_context():
        db = get_db()
        dump = "\n".join(db.iterdump())
    assert "4111111111111111" not in dump and "4111 1111 1111 1111" not in dump
    assert "'123'" not in dump.split("INSERT INTO \"payments\"")[-1][:500]


def test_other_user_cannot_pay_or_view(unpaid):
    app, _, user = unpaid
    other = app.test_client()
    register(other, name="Asha", email="asha@test.com")
    login(other, "asha@test.com")
    sid = session_id_of(app)
    assert other.get(f"/payments/session/{sid}").status_code == 404
    pay(user, app)
    pid = _payments(app)[0]["public_id"]
    assert other.get(f"/payments/receipt/{pid}").status_code == 404


def test_user_cannot_choose_cash(unpaid):
    app, _, user = unpaid
    pay(user, app, {"method": "cash"})
    assert _session_status(app) == "unpaid"


def test_admin_records_cash(unpaid):
    app, admin, _ = unpaid
    pay(admin, app, {"method": "cash"})
    assert _session_status(app) == "paid"


def test_pending_list(unpaid):
    app, _, user = unpaid
    assert b"KA01AB1234" in user.get("/payments/").data


def test_upi_without_at_rejected(unpaid):
    app, _, user = unpaid
    resp = pay(user, app, {"method": "upi", "upi_id": "ravi"})
    assert b"valid UPI ID" in resp.data
    assert _payments(app) == []
    assert _session_status(app) == "unpaid"
