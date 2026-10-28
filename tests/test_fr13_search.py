"""FR-13 Search Vehicle - TC18, NFT05, T-03."""
import time

from app.data.db import get_db
from tests.conftest import add_slot, add_vehicle, park, vehicle_id


def test_search_by_vehicle_number_TC18(app, admin_client, user_client):
    add_vehicle(user_client, "KA01AB1234")
    add_vehicle(user_client, "KA02CD5678")
    page = admin_client.get("/admin/search/?q=KA01AB1234").get_data(as_text=True)
    assert "<strong>KA01AB1234" in page and "<strong>KA02CD5678" not in page
    assert "ravi@test.com" in page


def test_search_ignores_spacing_and_case(admin_client, user_client):
    add_vehicle(user_client, "KA01AB1234")
    assert b"<strong>KA01AB1234" in admin_client.get("/admin/search/?q=ka 01 ab").data


def test_search_by_owner_and_slot(app, admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client, "KA01AB1234", owner="Ravi Kumar")
    park(user_client, app)
    assert b"<strong>KA01AB1234" in admin_client.get("/admin/search/?q=kumar").data
    page = admin_client.get("/admin/search/?q=A01").get_data(as_text=True)
    assert "slot A01" in page


def test_wildcards_and_injection_are_literal_T03(app, admin_client, user_client):
    add_vehicle(user_client, "KA01AB1234")
    assert b"0 results" in admin_client.get("/admin/search/?q=%25%25").data
    assert b"0 results" in admin_client.get("/admin/search/?q=' OR 1=1 --").data
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM vehicles").fetchone()[0] == 1


def test_short_query_rejected(admin_client):
    assert b"at least 2 characters" in admin_client.get("/admin/search/?q=K").data


def test_vehicle_detail_page(app, admin_client, user_client):
    add_vehicle(user_client)
    assert b"KA01AB1234" in admin_client.get(f"/admin/search/vehicle/{vehicle_id(app)}").data


def test_user_cannot_search(user_client):
    assert user_client.get("/admin/search/?q=KA").status_code == 403


def test_search_scales_NFT05(app, admin_client):
    with app.app_context():
        db = get_db()
        uid = db.execute("SELECT id FROM users").fetchone()["id"]
        db.executemany("INSERT INTO vehicles (user_id, number, type, owner_name) VALUES (?, ?, 'car', ?)",
                       [(uid, f"KA{(i % 99) + 1:02d}ZZ{i:04d}", f"Owner {i}") for i in range(5000)])
    start = time.perf_counter()
    resp = admin_client.get("/admin/search/?q=KA05ZZ")
    assert resp.status_code == 200 and b"<strong>KA05ZZ" in resp.data
    assert time.perf_counter() - start < 1.0


def test_search_by_owner_email(admin_client, user_client):
    add_vehicle(user_client)
    page = admin_client.get("/admin/search/?q=ravi@test.com").get_data(as_text=True)
    assert "KA01AB1234" in page
