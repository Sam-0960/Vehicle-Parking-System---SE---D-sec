"""Presentation: admin slot management (FR-03)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.security import admin_required, audit
from app.services import ServiceError, slot_service

bp = Blueprint("slots", __name__, url_prefix="/admin/slots")


@bp.route("/", methods=["GET", "POST"])
@admin_required
def manage():
    f = request.form
    if request.method == "POST":
        try:
            if f.get("mode") == "range":
                n = slot_service.add_range(f.get("prefix"), int(f.get("start") or 0),
                                           int(f.get("end") or 0), f.get("slot_type"))
                audit("slot_add_range", f"{f.get('prefix')}{f.get('start')}-{f.get('end')}")
                flash(f"{n} slots added.", "success")
            else:
                slot_service.add(f.get("code"), f.get("slot_type"))
                audit("slot_add", slot_service.normalise_code(f.get("code")))
                flash("Slot added.", "success")
        except ValueError:
            flash("Start and end must be numbers.", "error")
        except ServiceError as e:
            flash(str(e), "error")
        else:
            return redirect(url_for("slots.manage"))
    return render_template("slots/manage.html", slots=slot_service.list_slots(),
                           types=slot_service.SLOT_TYPES, form=f)


@bp.route("/<int:slot_id>/update", methods=["POST"])
@admin_required
def update(slot_id):
    try:
        slot_service.update(slot_id, request.form.get("slot_type"), request.form.get("is_active") == "1")
    except ServiceError as e:
        flash(str(e), "error")
    else:
        audit("slot_update", f"slot {slot_id}")
        flash("Slot updated.", "success")
    return redirect(url_for("slots.manage"))


@bp.route("/<int:slot_id>/delete", methods=["POST"])
@admin_required
def delete(slot_id):
    try:
        outcome = slot_service.remove(slot_id)
    except ServiceError as e:
        flash(str(e), "error")
    else:
        audit("slot_remove", f"slot {slot_id} {outcome}")
        flash("Slot removed." if outcome == "deleted"
              else "Slot has past records, so it was deactivated instead of deleted.", "success")
    return redirect(url_for("slots.manage"))
