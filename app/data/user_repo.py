"""Data Layer: users."""
from app.data.db import get_db


def get_by_id(user_id: int):
    return get_db().execute(
        "SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()
