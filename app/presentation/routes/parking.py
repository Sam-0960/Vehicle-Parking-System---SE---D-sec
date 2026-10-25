"""Presentation: Park / Exit desk (FR-05, FR-06)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.data import vehicle_repo
from app.security import audit, login_required, rate_limit
from app.services import ServiceError, parking_service, vehicle_service

bp = Blueprint("parking", __name__, url_prefix="/parking")
PARKING_ACTIONS = {"enter"}


@bp.route("/")
@login_required
def desk():
    vehicles = [] if g.user["role"] == "admin" else vehicle_repo.list_for_user(g.user["id"])
    slot_options = {v["id"]: parking_service.free_slots_for(v) for v in vehicles if not v["is_parked"]}
    return render_template("parking/desk.html", vehicles=vehicles, slot_options=slot_options,
                           sessions=parking_service.active_sessions(g.user),
                           parking_actions=PARKING_ACTIONS)


@bp.route("/enter", methods=["POST"])
@login_required
@rate_limit("entry", "RATE_LIMIT_WRITE")
def enter():
    f = request.form
    try:
        if g.user["role"] == "admin":
            s = parking_service.enter(g.user, number=vehicle_service.normalise_number(f.get("number")),
                                      slot_code=f.get("slot", ""))
        else:
            s = parking_service.enter(g.user, vehicle_id=int(f.get("vehicle_id") or 0),
                                      slot_code=f.get("slot", ""))
    except ValueError:
        flash("Choose a vehicle.", "error")
    except ServiceError as e:
        flash(str(e), "error")
    else:
        audit("vehicle_entry", f"{s['vehicle_number']} -> {s['slot_code']}")
        flash(f"{s['vehicle_number']} parked in slot {s['slot_code']} at {s['entry_time'][11:16]}.", "success")
    return redirect(url_for("parking.desk"))
