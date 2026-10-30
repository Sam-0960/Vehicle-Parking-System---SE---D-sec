"""Non-functional requirements - NFR-01..08, NFT01-NFT06 and security checklist T-xx.

Requirement-specific NFR tests also live next to their features:
  NFR-01 / NFT01  tests/test_fr04_availability.py::test_loads_quickly_NFT01
  NFR-06 / NFT05  tests/test_fr13_search.py::test_search_scales_NFT05
  NFR-07          tests/test_fr08_fees.py::test_admin_changes_rate_NFR07
  NFR-08 / NFT06  tests/test_fr05_entry.py (database + concurrent booking tests)
"""
from app import create_app, security
from app.config import TestConfig
from app.data.db import get_db
from tests.conftest import add_slot, add_vehicle, login, post, register


def test_data_survives_restart_NFT04(tmp_path):
    db_path = str(tmp_path / "persist.db")
    first = create_app(TestConfig, DATABASE=db_path)
    c = first.test_client()
    register(c)
    login(c)
    add_vehicle(c)
    second = create_app(TestConfig, DATABASE=db_path)  # "restart"
    c2 = second.test_client()
    login(c2)
    assert b"<strong>KA01AB1234" in c2.get("/vehicles/").data


def test_health_endpoint_NFR05(client):
    assert client.get("/health").get_json() == {"status": "ok", "database": "ok"}


def test_backup_copy_NFR03(app, tmp_path, user_client):
    add_vehicle(user_client)
    from app.data.db import backup_to
    target = tmp_path / "copy.db"
    with app.app_context():
        backup_to(str(target))
    import sqlite3
    assert sqlite3.connect(target).execute("SELECT number FROM vehicles").fetchone()[0] == "KA01AB1234"


def test_foreign_keys_enforced_NFR03(app):
    import sqlite3
    import pytest
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute("INSERT INTO vehicles (user_id, number, type, owner_name) VALUES (999, 'X', 'car', 'x')")


def test_rate_limit_on_login_T13(tmp_path):
    app = create_app(TestConfig, DATABASE=str(tmp_path / "rl.db"), RATE_LIMIT_LOGIN=3)
    security.reset_rate_limits()
    c = app.test_client()
    codes = [post(c, "/login", {"email": "x@test.com", "password": "bad"}).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and 429 in codes[3:]
    security.reset_rate_limits()


def test_malformed_input_gives_generic_error_T10(user_client):
    resp = user_client.get("/history/?vehicle=abc")
    assert resp.status_code == 404
    assert b"Traceback" not in resp.data and b"sqlite" not in resp.data.lower()


def test_unauthenticated_access_redirects_T02(client):
    for path in ("/vehicles/", "/parking/", "/reservations/", "/payments/", "/history/", "/notifications/"):
        resp = client.get(path)
        assert resp.status_code == 302 and "/login" in resp.headers["Location"], path
    for path in ("/admin/", "/admin/slots/", "/admin/reports/", "/admin/search/", "/availability/api"):
        assert client.get(path).status_code == 302, path


def test_privilege_escalation_blocked_T04(user_client):
    for path in ("/admin/", "/admin/slots/", "/admin/rates", "/admin/reports/", "/admin/search/"):
        assert user_client.get(path).status_code == 403, path


def test_debug_off_and_no_default_accounts_T15(app):
    assert not app.debug
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM users").fetchone()[0] == 0


def test_security_headers_NFR02(client):
    h = client.get("/").headers
    assert "default-src 'self'" in h["Content-Security-Policy"]
    assert h["X-Frame-Options"] == "DENY"


def test_secrets_not_logged_T14(app, user_client):
    with app.app_context():
        details = " ".join(r["detail"] or "" for r in get_db().execute("SELECT detail FROM audit_log"))
    assert "Park@123" not in details


def test_usability_labels_NFT03(admin_client, user_client):
    add_slot(admin_client, "A01")
    add_vehicle(user_client)
    for page in (user_client.get("/vehicles/"), user_client.get("/parking/"), admin_client.get("/parking/")):
        html = page.get_data(as_text=True)
        assert "<label>" in html and "<button" in html


def test_session_cookie_samesite_lax(client):
    register(client)
    resp = login(client)
    assert "SameSite=Lax" in resp.headers.get("Set-Cookie", "")
