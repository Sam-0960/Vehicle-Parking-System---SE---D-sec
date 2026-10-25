"""Data Layer: users."""
from app.data.db import get_db


def get_by_id(user_id: int):
    return get_db().execute(
        "SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()


def get_auth_by_email(email: str):
    """Includes the password hash and lockout fields; never pass this row to a template."""
    return get_db().execute(
        "SELECT id, name, email, role, password_hash, failed_attempts, locked_until "
        "FROM users WHERE email = ?",
        (email,),
    ).fetchone()


def email_exists(email: str) -> bool:
    return get_db().execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone() is not None


def create(name: str, email: str, password_hash: str, role: str = "user") -> int:
    cur = get_db().execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, role),
    )
    return cur.lastrowid


def record_failed_login(user_id: int, locked_until) -> None:
    get_db().execute(
        "UPDATE users SET failed_attempts = failed_attempts + 1, locked_until = ? WHERE id = ?",
        (locked_until, user_id),
    )


def reset_failed_logins(user_id: int) -> None:
    get_db().execute(
        "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user_id,)
    )


def set_role(user_id: int, role: str) -> None:
    get_db().execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))


def open_session(token: str, user_id: int) -> None:
    get_db().execute("INSERT INTO login_sessions (token, user_id) VALUES (?, ?)", (token, user_id))


def get_by_session(token: str):
    return get_db().execute(
        "SELECT u.id, u.name, u.email, u.role FROM login_sessions s "
        "JOIN users u ON u.id = s.user_id WHERE s.token = ? AND s.revoked = 0",
        (token,),
    ).fetchone()


def revoke_session(token: str) -> None:
    get_db().execute("UPDATE login_sessions SET revoked = 1 WHERE token = ?", (token,))
