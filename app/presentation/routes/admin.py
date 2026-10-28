"""Presentation: administrator dashboard (FR-12)."""
from flask import Blueprint, render_template

from app.security import admin_required
from app.services import dashboard_service

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html", d=dashboard_service.overview())
