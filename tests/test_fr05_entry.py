"""FR-05 Vehicle Entry - TC08, TC09, NFT06, T-08."""
import sqlite3
import threading

import pytest

from app.data.db import get_db
from app.services import ConflictError, parking_service
from tests.conftest import add_slot, add_vehicle, park, post, register, login


def _sessions(app):
    with app.app_context():
        return get_db().execute(
            "SELECT p.*, s.code FROM parking_sessions p JOIN slots s ON s.id = p.slot_id").fetchall()


def test_entry_records_time_and_assigns_slot_TC08(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    resp = park(user_client, app)
    assert resp.status_code == 302
    rows = _sessions(app)
    assert len(rows) == 1 and rows[0]["code"] == "A01" and rows[0]["entry_time"]
    assert b"parked in slot A01" in user_client.get("/parking/").data


def test_entry_when_full_TC09(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client, "KA01AB1234")
    add_vehicle(user_client, "KA02CD5678")
    park(user_client, app, "KA01AB1234")
    resp = park(user_client, app, "KA02CD5678")
    page = user_client.get("/parking/").get_data(as_text=True)
    assert len(_sessions(app)) == 1
    assert "No car parking slot is currently available" in page


def test_cannot_park_same_vehicle_twice(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_slot(admin_client, "A02")
    add_vehicle(user_client)
    park(user_client, app)
    park(user_client, app)
    assert len(_sessions(app)) == 1


def test_slot_type_must_match(app, admin_client, user_client):
    add_slot(admin_client, "M01", "bike")
    add_vehicle(user_client)
    park(user_client, app, slot="M01")
    assert len(_sessions(app)) == 0


def test_admin_enters_by_number(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    post(admin_client, "/parking/enter", {"number": "ka01ab1234", "slot": "A01"}, page="/parking/")
    assert _sessions(app)[0]["code"] == "A01"


def test_user_cannot_park_someone_elses_vehicle(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    other = app.test_client()
    register(other, name="Asha", email="asha@test.com")
    login(other, "asha@test.com")
    park(other, app)
    assert len(_sessions(app)) == 0


def test_database_rejects_double_assignment_NFT06(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client, "KA01AB1234")
    add_vehicle(user_client, "KA02CD5678")
    with app.app_context():
        db = get_db()
        sid = db.execute("SELECT id FROM slots").fetchone()["id"]
        v1, v2 = [r["id"] for r in db.execute("SELECT id FROM vehicles ORDER BY id")]
        db.execute("INSERT INTO parking_sessions (vehicle_id, slot_id, entry_time) VALUES (?, ?, 'x')", (v1, sid))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO parking_sessions (vehicle_id, slot_id, entry_time) VALUES (?, ?, 'x')", (v2, sid))


def test_concurrent_entries_only_one_wins_T08(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client, "KA01AB1234")
    add_vehicle(user_client, "KA02CD5678")
    with app.app_context():
        actor = dict(get_db().execute("SELECT id, role FROM users WHERE role='admin'").fetchone())
    results = []
    barrier = threading.Barrier(2)

    def attempt(number):
        with app.app_context():
            barrier.wait()
            try:
                parking_service.enter(actor, number=number, slot_code="A01")
                results.append("ok")
            except ConflictError:
                results.append("conflict")

    threads = [threading.Thread(target=attempt, args=(n,)) for n in ("KA01AB1234", "KA02CD5678")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["conflict", "ok"]
    assert len(_sessions(app)) == 1
