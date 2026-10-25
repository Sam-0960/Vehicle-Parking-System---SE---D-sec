"""Business Logic: Authentication & User Management (FR-01).

Controls: C-01 (password policy, hashing, lockout), C-09 (audit is done by caller).
"""
import re
from datetime import timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from app import clock
from app.data import user_repo
from app.services import ServiceError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Spent once on unknown emails so response time doesn't reveal which emails exist.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise ServiceError("Password must be at least 8 characters.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ServiceError("Password must contain at least one letter and one number.")
    if len(password) > 128:
        raise ServiceError("Password is too long.")


def register(name: str, email: str, password: str, confirm: str, role: str = "user") -> int:
    name = (name or "").strip()
    email = (email or "").strip().lower()
    if not name or len(name) > 80:
        raise ServiceError("Please enter your name (up to 80 characters).")
    if not EMAIL_RE.match(email) or len(email) > 120:
        raise ServiceError("Please enter a valid email address.")
    if password != confirm:
        raise ServiceError("Passwords do not match.")
    validate_password(password)
    if user_repo.email_exists(email):
        raise ServiceError("An account with this email already exists.")
    return user_repo.create(name, email, generate_password_hash(password), role)


class LoginResult:
    def __init__(self, user=None, locked=False):
        self.user = user
        self.locked = locked

    @property
    def ok(self) -> bool:
        return self.user is not None


def authenticate(email: str, password: str, max_failed: int, lockout_minutes: int) -> LoginResult:
    email = (email or "").strip().lower()
    row = user_repo.get_auth_by_email(email)
    if row is None:
        check_password_hash(_DUMMY_HASH, password or "")
        return LoginResult()

    now = clock.now()
    if row["locked_until"] and clock.parse(row["locked_until"]) > now:
        return LoginResult(locked=True)

    if not check_password_hash(row["password_hash"], password or ""):
        attempts = row["failed_attempts"] + 1
        locked_until = None
        if attempts >= max_failed:
            locked_until = clock.to_str(now + timedelta(minutes=lockout_minutes))
        user_repo.record_failed_login(row["id"], locked_until)
        return LoginResult(locked=locked_until is not None)

    user_repo.reset_failed_logins(row["id"])
    return LoginResult(user=user_repo.get_by_id(row["id"]))
