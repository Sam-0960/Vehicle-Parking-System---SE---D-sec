"""Presentation: reservations (FR-07)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app import clock
from app.data import vehicle_repo
from app.security import audit, login_required, new_form_key, rate_limit
from app.services import ServiceError, notification_service, reservation_service

bp = Blueprint("reservations", __name__, url_prefix="/reservations")


@bp.route("/", methods=["GET", "POST"])
@login_required
@rate_limit("reserve", "RATE_LIMIT_WRITE")
def mine():
    if g.user["role"] == "admin":
        return render_template("reservations/all.html", reservations=reservation_service.upcoming())
    f = request.form
    if request.method == "POST":
        try:
            r, created = reservation_service.reserve(
                g.user, int(f.get("vehicle_id") or 0), f.get("slot"),
                f.get("start"), f.get("end"), f.get("form_key", ""))
        except ValueError:
            flash("Choose a vehicle.", "error")
        except ServiceError as e:
            flash(str(e), "error")
        else:
            if created:
                audit("reservation_created", f"{r['public_id']} slot {r['slot_code']}")
                _after_reserve(r)
                flash(f"Slot {r['slot_code']} reserved for {r['vehicle_number']} from "
                      f"{r['start_time'][5:16]} to {r['end_time'][5:16]}.", "success")
            else:
                flash("This reservation was already submitted.", "warning")
            return redirect(url_for("reservations.mine"))
    vehicles = vehicle_repo.list_for_user(g.user["id"])
    slots_by_type = {t: reservation_service.bookable_slots(t) for t in {v["type"] for v in vehicles}}
    now = clock.now()
    return render_template("reservations/mine.html", vehicles=vehicles, slots_by_type=slots_by_type,
                           reservations=reservation_service.mine(g.user), form=f,
                           form_key=new_form_key(),
                           default_start=now.strftime("%Y-%m-%dT%H:%M"),
                           default_end=now.replace(hour=min(now.hour + 2, 23)).strftime("%Y-%m-%dT%H:%M"))


def _after_reserve(reservation):
    notification_service.reservation_confirmed(reservation)


@bp.route("/<public_id>/cancel", methods=["POST"])
@login_required
def cancel(public_id):
    try:
        r = reservation_service.cancel(g.user, public_id)
    except ServiceError as e:
        flash(str(e), "error")
    else:
        audit("reservation_cancelled", r["public_id"])
        notification_service.reservation_cancelled(r)
        flash("Reservation cancelled.", "success")
    return redirect(url_for("reservations.mine"))
