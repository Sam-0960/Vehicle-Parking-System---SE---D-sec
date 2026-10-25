"""Cross-cutting security controls used by the Presentation Layer.

C-02 role checks, C-07 rate limiting, CSRF protection, C-09 audit logging.
"""
import secrets
import time
from collections import defaultdict, deque
from functools import wraps

from flask import abort, current_app, g, redirect, request, session, url_for

from app.data import audit_repo


# ---------- authentication / authorisation (C-02) ----------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user["role"] != "admin":
            audit("access_denied", f"{request.method} {request.path}")
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# ---------- CSRF ----------

def csrf_token() -> str:
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def check_csrf() -> None:
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
        if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
            abort(400, description="Invalid or missing form token. Reload the page and try again.")


# ---------- rate limiting (C-07) ----------

_hits: dict = defaultdict(deque)


def rate_limit(bucket: str, limit_key: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if request.method == "POST":
                limit = current_app.config[limit_key]
                window = current_app.config["RATE_LIMIT_WINDOW_SECONDS"]
                key = (bucket, request.remote_addr)
                now = time.monotonic()
                q = _hits[key]
                while q and now - q[0] > window:
                    q.popleft()
                if len(q) >= limit:
                    audit("rate_limited", bucket)
                    abort(429)
                q.append(now)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def reset_rate_limits() -> None:
    _hits.clear()


# ---------- idempotency (SO-03 replay protection) ----------

def new_form_key() -> str:
    return secrets.token_urlsafe(16)


# ---------- audit (C-09) ----------

def audit(action: str, detail: str = "", actor_id=None) -> None:
    if actor_id is None and g.get("user") is not None:
        actor_id = g.user["id"]
    audit_repo.add(actor_id, action, detail, request.remote_addr or "")
