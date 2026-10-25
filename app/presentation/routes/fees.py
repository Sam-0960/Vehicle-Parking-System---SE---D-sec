"""Presentation: tariff page and admin rate settings (FR-08, NFR-07)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.security import admin_required, audit, login_required
from app.services import ServiceError, fee_service

bp = Blueprint("fees", __name__)


@bp.route("/rates")
@login_required
def tariff():
    return render_template("fees/tariff.html", rates=fee_service.rates(), describe=fee_service.describe)


@bp.route("/admin/rates", methods=["GET", "POST"])
@admin_required
def settings():
    if request.method == "POST":
        f = request.form
        try:
            fee_service.update_rate(f.get("vehicle_type"), f.get("hourly_rate"), f.get("daily_cap"),
                                    f.get("grace_minutes"))
        except ServiceError as e:
            flash(str(e), "error")
        else:
            audit("rate_changed", f"{f.get('vehicle_type')}: {f.get('hourly_rate')}/h cap {f.get('daily_cap')}")
            flash("Rate updated.", "success")
            return redirect(url_for("fees.settings"))
    return render_template("fees/settings.html", rates=fee_service.rates())
