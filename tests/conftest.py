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
