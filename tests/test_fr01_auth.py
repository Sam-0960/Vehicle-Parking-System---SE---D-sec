"""FR-01 User Registration/Login - TC01, TC02, NFT02, T-01, T-02, T-11, T-12."""
from datetime import datetime

from app import clock
from app.data.db import get_db
from tests.conftest import PASSWORD, login, logout, post, register


def test_register_then_login_TC01(client):
    resp = register(client)
    assert resp.status_code == 302
    resp = login(client)
    assert resp.status_code == 302
    page = client.get("/", follow_redirects=True).get_data(as_text=True)
    assert "Ravi" in page


def test_wrong_password_rejected_TC02(client):
    register(client)
    resp = login(client, password="Wrong@999")
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data


def test_unknown_email_gets_same_message(client):
    resp = login(client, email="nobody@test.com")
    assert b"Invalid email or password" in resp.data


def test_duplicate_email_rejected(client):
    register(client)
    resp = register(client)
    assert b"already exists" in resp.data


def test_weak_password_rejected(client):
    resp = register(client, password="short")
    assert b"at least 8 characters" in resp.data


def test_password_is_hashed_T11(app, client):
    register(client)
    with app.app_context():
        row = get_db().execute("SELECT password_hash FROM users").fetchone()
    assert PASSWORD not in row["password_hash"]
    assert row["password_hash"].startswith(("scrypt:", "pbkdf2:"))


def test_lockout_after_repeated_failures_T01(app, client):
    clock.set_now(datetime(2026, 10, 26, 10, 0, 0))
    register(client)
    for _ in range(app.config["MAX_FAILED_LOGINS"]):
        login(client, password="Wrong@999")
    resp = login(client)  # correct password, but locked
    assert b"Too many failed attempts" in resp.data
    clock.set_now(datetime(2026, 10, 26, 10, 16, 0))
    assert login(client).status_code == 302
    with app.app_context():
        actions = [r["action"] for r in get_db().execute("SELECT action FROM audit_log")]
    assert actions.count("login_failed") >= app.config["MAX_FAILED_LOGINS"]


def test_logout_invalidates_session_T12(client):
    register(client)
    login(client)
    with client.session_transaction() as s:
        stolen = dict(s)  # what an attacker would have copied
    logout(client)
    with client.session_transaction() as s:
        s.update(stolen)  # replay the old cookie
    page = client.get("/").get_data(as_text=True)
    assert "Ravi" not in page  # old token is revoked server-side


def test_open_redirect_blocked(client):
    register(client)
    data = {"email": "ravi@test.com", "password": PASSWORD}
    resp = post(client, "/login?next=https://evil.example", data, page="/login")
    assert resp.headers["Location"].startswith("/")


def test_session_cookie_flags(client):
    register(client)
    resp = login(client)
    cookie = resp.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
