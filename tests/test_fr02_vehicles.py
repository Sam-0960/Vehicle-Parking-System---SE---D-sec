"""FR-02 Vehicle Registration - TC03, TC04, T-03, T-05."""
from app.data.db import get_db
from tests.conftest import add_vehicle, login, post, register


def test_add_vehicle_TC03(user_client):
    resp = add_vehicle(user_client)
    assert resp.status_code == 302
    page = user_client.get("/vehicles/").get_data(as_text=True)
    assert "KA01AB1234" in page


def test_missing_vehicle_number_rejected_TC04(user_client):
    resp = add_vehicle(user_client, number="")
    assert b"Vehicle number is required" in resp.data


def test_number_is_normalised(user_client):
    add_vehicle(user_client, number="ka 02-cd 5678")
    assert b"KA02CD5678" in user_client.get("/vehicles/").data


def test_invalid_format_rejected(user_client):
    resp = add_vehicle(user_client, number="HELLO")
    assert b"valid vehicle number" in resp.data


def test_duplicate_number_rejected(user_client):
    add_vehicle(user_client)
    resp = add_vehicle(user_client)
    assert b"already registered" in resp.data


def test_sql_injection_treated_as_text_T03(app, user_client):
    resp = add_vehicle(user_client, number="KA01'; DROP TABLE vehicles;--")
    assert resp.status_code == 200
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM vehicles").fetchone()[0] == 0


def test_edit_and_delete_vehicle(app, user_client):
    add_vehicle(user_client)
    with app.app_context():
        vid = get_db().execute("SELECT id FROM vehicles").fetchone()["id"]
    resp = post(user_client, f"/vehicles/{vid}/edit", {"number": "KA01AB9999", "type": "bike",
                                                       "owner_name": "Ravi K"})
    assert resp.status_code == 302
    assert b"KA01AB9999" in user_client.get("/vehicles/").data
    post(user_client, f"/vehicles/{vid}/delete", page="/vehicles/")
    assert b"KA01AB9999" not in user_client.get("/vehicles/").data


def test_cannot_touch_another_users_vehicle_T05(app, client):
    register(client, name="Ravi", email="ravi@test.com")
    login(client)
    add_vehicle(client)
    with app.app_context():
        vid = get_db().execute("SELECT id FROM vehicles").fetchone()["id"]
    other = app.test_client()
    register(other, name="Asha", email="asha@test.com")
    login(other, "asha@test.com")
    assert other.get(f"/vehicles/{vid}/edit").status_code == 404
    post(other, f"/vehicles/{vid}/delete", page="/vehicles/")
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM vehicles").fetchone()[0] == 1
    assert b"<strong>KA01AB1234" not in other.get("/vehicles/").data


def test_requires_login_T02(client):
    resp = client.get("/vehicles/")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]
