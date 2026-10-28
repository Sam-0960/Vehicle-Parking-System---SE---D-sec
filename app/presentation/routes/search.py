"""Presentation: admin vehicle search (FR-13)."""
from flask import Blueprint, render_template, request

from app.security import admin_required, audit
from app.services import ServiceError, history_service, search_service

bp = Blueprint("search", __name__, url_prefix="/admin/search")


@bp.route("/")
@admin_required
def vehicles():
    q = request.args.get("q", "")
    results, error = None, None
    if q:
        try:
            results = search_service.search(q)
        except ServiceError as e:
            error = str(e)
        else:
            audit("vehicle_search", q[:60])
    return render_template("search/vehicles.html", q=q, results=results, error=error)


@bp.route("/vehicle/<int:vehicle_id>")
@admin_required
def detail(vehicle_id):
    try:
        vehicle, data = search_service.vehicle_detail(vehicle_id)
    except ServiceError:
        return render_template("error.html", code=404, message="Vehicle not found."), 404
    return render_template("search/detail.html", vehicle=vehicle, data=data,
                           fmt_duration=history_service.fmt_duration)
