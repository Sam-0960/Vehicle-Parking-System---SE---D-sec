"""Presentation: parking history (FR-10)."""
from flask import Blueprint, g, render_template, request

from app.data import vehicle_repo
from app.security import login_required
from app.services import ServiceError, history_service

bp = Blueprint("history", __name__, url_prefix="/history")


@bp.route("/")
@login_required
def mine():
    try:
        vid = int(request.args["vehicle"]) if request.args.get("vehicle") else None
        data = history_service.for_user(g.user, vid)
    except (ValueError, ServiceError):
        return render_template("error.html", code=404, message="Vehicle not found."), 404
    return render_template("history/mine.html", data=data, selected=vid,
                           vehicles=vehicle_repo.list_for_user(g.user["id"]),
                           fmt_duration=history_service.fmt_duration)
