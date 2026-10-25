"""Presentation: live slot availability (FR-04)."""
from flask import Blueprint, g, jsonify, render_template, request

from app.security import login_required
from app.services import availability_service

bp = Blueprint("availability", __name__, url_prefix="/availability")
TYPES = ("car", "bike", "truck")


def _type_filter() -> str:
    t = request.args.get("type", "")
    return t if t in TYPES else ""


@bp.route("/")
@login_required
def view():
    t = _type_filter()
    return render_template("availability/view.html", data=availability_service.snapshot(t),
                           selected=t, types=TYPES, is_admin=g.user["role"] == "admin")


@bp.route("/api")
@login_required
def api():
    data = availability_service.snapshot(_type_filter())
    is_admin = g.user["role"] == "admin"
    # Customers see slot state only, never other people's vehicle numbers (TB-01, R-04).
    slots = [{"code": r["code"], "type": r["slot_type"], "state": r["state"],
              **({"vehicle": r["vehicle_number"]} if is_admin else {})} for r in data["slots"]]
    return jsonify(counts=data["counts"], total=data["total"], slots=slots)
