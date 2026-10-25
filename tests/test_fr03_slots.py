"""FR-03 Parking Slot Management - TC05, TC06, NFT02, T-04."""
from app.data.db import get_db
from tests.conftest import add_slot, post


def _slot_id(app, code):
    with app.app_context():
        return get_db().execute("SELECT id FROM slots WHERE code = ?", (code,)).fetchone()["id"]


def test_admin_adds_slot_TC05(admin_client):
    assert add_slot(admin_client, "A01").status_code == 302
    assert b"<strong>A01</strong>" in admin_client.get("/admin/slots/").data


def test_duplicate_slot_rejected_TC06(app, admin_client):
    add_slot(admin_client, "A01")
    resp = add_slot(admin_client, "a01")
    assert b"already exists" in resp.data
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM slots").fetchone()[0] == 1


def test_add_range(app, admin_client):
    post(admin_client, "/admin/slots/", {"mode": "range", "prefix": "B", "start": "1", "end": "5",
                                         "slot_type": "bike"})
    with app.app_context():
        codes = [r["code"] for r in get_db().execute("SELECT code FROM slots ORDER BY code")]
    assert codes == ["B01", "B02", "B03", "B04", "B05"]


def test_update_and_remove_slot(app, admin_client):
    add_slot(admin_client, "A01")
    sid = _slot_id(app, "A01")
    post(admin_client, f"/admin/slots/{sid}/update", {"slot_type": "truck", "is_active": "0"},
         page="/admin/slots/")
    with app.app_context():
        row = get_db().execute("SELECT * FROM slots WHERE id = ?", (sid,)).fetchone()
    assert row["slot_type"] == "truck" and row["is_active"] == 0
    post(admin_client, f"/admin/slots/{sid}/delete", page="/admin/slots/")
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM slots").fetchone()[0] == 0


def test_invalid_slot_code(admin_client):
    assert b"must look like A01" in add_slot(admin_client, "!!").data


def test_normal_user_cannot_manage_slots_NFT02_T04(app, user_client):
    assert user_client.get("/admin/slots/").status_code == 403
    resp = post(user_client, "/admin/slots/", {"code": "Z01", "slot_type": "car"}, page="/")
    assert resp.status_code == 403
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM slots").fetchone()[0] == 0
        logged = get_db().execute("SELECT count(*) FROM audit_log WHERE action='access_denied'").fetchone()[0]
    assert logged >= 1
