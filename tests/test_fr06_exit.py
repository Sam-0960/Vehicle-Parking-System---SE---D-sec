"""FR-06 Vehicle Exit - TC10, TC11."""
from datetime import datetime

from app import clock
from app.data.db import get_db
from tests.conftest import add_slot, add_vehicle, login, park, register, session_id_of, unpark


def _setup(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    clock.set_now(datetime(2026, 10, 26, 9, 0, 0))
    park(user_client, app)


def test_exit_records_time_TC10(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    clock.set_now(datetime(2026, 10, 26, 11, 30, 0))
    assert unpark(user_client, app).status_code == 302
    with app.app_context():
        row = get_db().execute("SELECT * FROM parking_sessions").fetchone()
    assert row["exit_time"] == "2026-10-26 11:30:00"
    assert row["status"] == "unpaid"


def test_slot_released_after_exit_TC11(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    assert user_client.get("/availability/api").get_json()["counts"]["occupied"] == 1
    unpark(user_client, app)
    assert user_client.get("/availability/api").get_json()["counts"]["available"] == 1
    add_vehicle(user_client, "KA02CD5678")
    park(user_client, app, "KA02CD5678", slot="A01")  # slot is reusable
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM parking_sessions WHERE exit_time IS NULL").fetchone()[0] == 1


def test_repeated_exit_is_harmless(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    unpark(user_client, app)
    sid = session_id_of(app)
    clock.set_now(datetime(2026, 10, 26, 15, 0, 0))
    unpark(user_client, app)
    with app.app_context():
        row = get_db().execute("SELECT exit_time FROM parking_sessions WHERE id = ?", (sid,)).fetchone()
    assert row["exit_time"] == "2026-10-26 09:00:00"


def test_other_user_cannot_exit_my_vehicle(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    other = app.test_client()
    register(other, name="Asha", email="asha@test.com")
    login(other, "asha@test.com")
    unpark(other, app)
    with app.app_context():
        assert get_db().execute("SELECT exit_time FROM parking_sessions").fetchone()["exit_time"] is None


def test_admin_can_record_exit(app, admin_client, user_client):
    _setup(app, admin_client, user_client)
    unpark(admin_client, app)
    with app.app_context():
        assert get_db().execute("SELECT exit_time FROM parking_sessions").fetchone()["exit_time"]
