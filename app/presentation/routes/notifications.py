"""Presentation: in-app notifications (FR-11)."""
from flask import Blueprint, g, render_template

from app.security import login_required
from app.services import notification_service

bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@bp.before_app_request
def sweep_due_notifications():
    if g.get("user") is not None:
        notification_service.sweep(g.user["id"])


@bp.app_context_processor
def inject_unread():
    def unread_notifications():
        return notification_service.unread(g.user["id"]) if g.get("user") else 0
    return {"unread_notifications": unread_notifications}


@bp.route("/")
@login_required
def inbox():
    return render_template("notifications/inbox.html", notices=notification_service.inbox(g.user["id"]))
