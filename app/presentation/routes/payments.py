"""Presentation: pay for a parking session (FR-09)."""
from flask import (Blueprint, current_app, flash, g, redirect, render_template, request,
                   url_for)

from app import clock
from app.security import audit, login_required, new_form_key, rate_limit
from app.services import ConflictError, ServiceError, payment_service

bp = Blueprint("payments", __name__, url_prefix="/payments")


@bp.route("/")
@login_required
def pending():
    return render_template("payments/pending.html", sessions=payment_service.pending(g.user))


@bp.route("/session/<int:session_id>", methods=["GET", "POST"])
@login_required
@rate_limit("payment", "RATE_LIMIT_WRITE")
def pay(session_id):
    try:
        session_row = payment_service.payable_session(g.user, session_id)
    except ConflictError as e:
        flash(str(e), "warning")
        return redirect(url_for("payments.pending"))
    except ServiceError:
        return render_template("error.html", code=404, message="Parking session not found."), 404

    methods = payment_service.ADMIN_METHODS if g.user["role"] == "admin" else payment_service.USER_METHODS
    if request.method == "POST":
        f = request.form
        try:
            payment, created = payment_service.pay(
                g.user, session_id, f.get("method"),
                {"card_number": f.get("card_number"), "expiry": f.get("expiry"),
                 "cvv": f.get("cvv"), "upi_id": f.get("upi_id")},
                f.get("form_key", ""), current_app.config["GATEWAY_SECRET"], clock.now().date())
        except ServiceError as e:
            flash(str(e), "error")
        else:
            # Never log card details; only the masked reference and outcome (C-09).
            audit("payment_" + payment["status"], f"{payment['public_id']} ₹{payment['amount']:.2f} {payment['method']}")
            if payment["status"] == "success":
                _after_payment(payment, created)
                return redirect(url_for("payments.receipt", public_id=payment["public_id"]))
            _after_payment(payment, created)
            flash("Payment failed. You have not been charged. Please try again or use another method.", "error")
    return render_template("payments/pay.html", s=session_row, methods=methods, form_key=new_form_key())


def _after_payment(payment, created):
    """Hook for the Notification Service (FR-11)."""


@bp.route("/receipt/<public_id>")
@login_required
def receipt(public_id):
    try:
        p = payment_service.receipt(g.user, public_id)
    except ServiceError:
        return render_template("error.html", code=404, message="Payment not found."), 404
    return render_template("payments/receipt.html", p=p)
