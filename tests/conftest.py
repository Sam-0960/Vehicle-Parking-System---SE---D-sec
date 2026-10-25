import re

import pytest

from app import clock, create_app, security
from app.config import TestConfig


@pytest.fixture
def app(tmp_path):
    app = create_app(TestConfig, DATABASE=str(tmp_path / "test.db"))
    security.reset_rate_limits()
    yield app
    clock.set_now(None)


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_of(client, path="/"):
    """Open a page and pull the CSRF token out of it."""
    html = client.get(path).get_data(as_text=True)
    m = re.search(r'name="_csrf" value="([^"]+)"', html)
    if m:
        return m.group(1)
    with client.session_transaction() as s:
        s.setdefault("_csrf", "test-token")
        return s["_csrf"]


def post(client, path, data=None, page=None, **kw):
    data = dict(data or {})
    data["_csrf"] = csrf_of(client, page or path)
    return client.post(path, data=data, **kw)


# ---------- account helpers ----------

PASSWORD = "Park@123"  # test data from the Human Test Plan


def register(client, name="Ravi", email="ravi@test.com", password=PASSWORD):
    return post(client, "/register", {"name": name, "email": email,
                                      "password": password, "confirm": password})


def login(client, email="ravi@test.com", password=PASSWORD):
    return post(client, "/login", {"email": email, "password": password})


def logout(client):
    return post(client, "/logout", page="/")


def make_admin(app, email="admin@test.com", password=PASSWORD):
    from app.services import auth_service
    with app.app_context():
        return auth_service.register("Admin", email, password, password, role="admin")


@pytest.fixture
def user_client(app, client):
    register(client)
    login(client)
    return client


@pytest.fixture
def admin_client(app):
    make_admin(app)
    c = app.test_client()
    login(c, "admin@test.com")
    return c


def add_vehicle(client, number="KA01AB1234", vtype="car", owner="Ravi"):
    return post(client, "/vehicles/", {"number": number, "type": vtype, "owner_name": owner})


def add_slot(admin, code="A01", slot_type="car"):
    return post(admin, "/admin/slots/", {"code": code, "slot_type": slot_type})


def vehicle_id(app, number="KA01AB1234"):
    from app.data.db import get_db
    with app.app_context():
        return get_db().execute("SELECT id FROM vehicles WHERE number = ?", (number,)).fetchone()["id"]


def park(client, app, number="KA01AB1234", slot=""):
    return post(client, "/parking/enter", {"vehicle_id": vehicle_id(app, number), "slot": slot},
                page="/parking/")


def session_id_of(app, number="KA01AB1234"):
    from app.data.db import get_db
    with app.app_context():
        return get_db().execute(
            "SELECT p.id FROM parking_sessions p JOIN vehicles v ON v.id = p.vehicle_id "
            "WHERE v.number = ? ORDER BY p.id DESC", (number,)).fetchone()["id"]


def unpark(client, app, number="KA01AB1234"):
    return post(client, f"/parking/exit/{session_id_of(app, number)}", page="/parking/")
