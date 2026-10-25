"""Presentation Layer: landing page."""
from flask import Blueprint, g, redirect, render_template, url_for

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if g.user is not None:
        if g.user["role"] == "admin" and "admin" in _blueprints():
            return redirect(url_for("admin.dashboard"))
        if "availability" in _blueprints():
            return redirect(url_for("availability.view"))
    return render_template("index.html")


def _blueprints():
    from flask import current_app
    return current_app.blueprints
