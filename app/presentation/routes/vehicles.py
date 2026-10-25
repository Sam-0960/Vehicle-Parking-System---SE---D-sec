"""Presentation: My Vehicles (FR-02)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.security import login_required
from app.services import ServiceError, vehicle_service

bp = Blueprint("vehicles", __name__, url_prefix="/vehicles")


@bp.route("/", methods=["GET", "POST"])
@login_required
def list_vehicles():
    form = request.form
    if request.method == "POST":
        try:
            vehicle_service.add(g.user["id"], form.get("number"), form.get("type"),
                                form.get("owner_name") or g.user["name"])
        except ServiceError as e:
            flash(str(e), "error")
        else:
            flash("Vehicle added.", "success")
            return redirect(url_for("vehicles.list_vehicles"))
    return render_template("vehicles/list.html", vehicles=vehicle_service.list_mine(g.user["id"]),
                           types=vehicle_service.VEHICLE_TYPES, form=form)


@bp.route("/<int:vehicle_id>/edit", methods=["GET", "POST"])
@login_required
def edit(vehicle_id):
    try:
        vehicle = vehicle_service.get_owned(g.user["id"], vehicle_id)
    except ServiceError:
        return render_template("error.html", code=404, message="Vehicle not found."), 404
    if request.method == "POST":
        f = request.form
        try:
            vehicle_service.edit(g.user["id"], vehicle_id, f.get("number"), f.get("type"), f.get("owner_name"))
        except ServiceError as e:
            flash(str(e), "error")
        else:
            flash("Vehicle updated.", "success")
            return redirect(url_for("vehicles.list_vehicles"))
    return render_template("vehicles/edit.html", vehicle=vehicle, types=vehicle_service.VEHICLE_TYPES)


@bp.route("/<int:vehicle_id>/delete", methods=["POST"])
@login_required
def delete(vehicle_id):
    try:
        vehicle_service.remove(g.user["id"], vehicle_id)
    except ServiceError as e:
        flash(str(e), "error")
    else:
        flash("Vehicle removed.", "success")
    return redirect(url_for("vehicles.list_vehicles"))
