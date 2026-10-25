"""Presentation: register, log in, log out (FR-01)."""
import secrets
from urllib.parse import urlparse

from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, session, url_for)

from app.data import user_repo
from app.security import audit, login_required, rate_limit
from app.services import ServiceError, auth_service

bp = Blueprint("auth", __name__)


def _safe_next(target: str) -> str:
    # Only allow relative paths, so ?next= can't send users to another site.
    if target and urlparse(target).netloc == "" and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("main.index")


@bp.route("/register", methods=["GET", "POST"])
@rate_limit("register", "RATE_LIMIT_LOGIN")
def register():
    if g.user:
        return redirect(url_for("main.index"))
    form = request.form
    if request.method == "POST":
        try:
            uid = auth_service.register(form.get("name"), form.get("email"),
                                        form.get("password"), form.get("confirm"))
        except ServiceError as e:
            flash(str(e), "error")
        else:
            audit("register", f"user {uid}", actor_id=uid)
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@rate_limit("login", "RATE_LIMIT_LOGIN")
def login():
    if g.user:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        cfg = current_app.config
        result = auth_service.authenticate(request.form.get("email"), request.form.get("password"),
                                           cfg["MAX_FAILED_LOGINS"], cfg["LOCKOUT_MINUTES"])
        if result.ok:
            session.clear()  # rotate the session on login (C-01)
            session.permanent = True
            token = secrets.token_urlsafe(32)
            user_repo.open_session(token, result.user["id"])
            session["sid"] = token
            audit("login_success", "", actor_id=result.user["id"])
            return redirect(_safe_next(request.args.get("next", "")))
        audit("login_failed", (request.form.get("email") or "")[:120])
        if result.locked:
            flash(f"Too many failed attempts. Try again in {cfg['LOCKOUT_MINUTES']} minutes.", "error")
        else:
            # Same message whether the email or the password was wrong (T-01).
            flash("Invalid email or password. Please try again.", "error")
    return render_template("auth/login.html", email=request.form.get("email", ""))


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    audit("logout")
    user_repo.revoke_session(session.get("sid", ""))
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
