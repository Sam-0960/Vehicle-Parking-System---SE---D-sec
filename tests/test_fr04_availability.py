"""FR-04 Slot Availability - TC07, NFT01."""
import time

from app.data.db import get_db
from tests.conftest import add_slot, add_vehicle


def test_shows_available_and_occupied_TC07(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_slot(admin_client, "A02")
    add_vehicle(user_client)
    with app.app_context():
        db = get_db()
        vid = db.execute("SELECT id FROM vehicles").fetchone()["id"]
        sid = db.execute("SELECT id FROM slots WHERE code='A01'").fetchone()["id"]
        db.execute("INSERT INTO parking_sessions (vehicle_id, slot_id, entry_time) "
                   "VALUES (?, ?, datetime('now'))", (vid, sid))
    data = user_client.get("/availability/api").get_json()
    assert data["counts"] == {"available": 1, "occupied": 1, "reserved": 0}
    states = {s["code"]: s["state"] for s in data["slots"]}
    assert states == {"A01": "occupied", "A02": "available"}
    assert all("vehicle" not in s for s in data["slots"])  # customers don't see plates
    assert admin_client.get("/availability/api").get_json()["slots"][0]["vehicle"] == "KA01AB1234"


def test_filter_by_type(admin_client):
    add_slot(admin_client, "A01", "car")
    add_slot(admin_client, "M01", "bike")
    data = admin_client.get("/availability/api?type=bike").get_json()
    assert [s["code"] for s in data["slots"]] == ["M01"]


def test_inactive_slots_hidden(app, admin_client):
    add_slot(admin_client, "A01")
    with app.app_context():
        get_db().execute("UPDATE slots SET is_active = 0")
    assert admin_client.get("/availability/api").get_json()["total"] == 0


def test_page_shows_full_message(admin_client):
    page = admin_client.get("/availability/").get_data(as_text=True)
    assert "No parking slots are set up yet" in page


def test_loads_quickly_NFT01(admin_client):
    for i in range(1, 61):
        add_slot(admin_client, f"P{i:02d}")
    start = time.perf_counter()
    assert admin_client.get("/availability/").status_code == 200
    assert time.perf_counter() - start < 1.0
