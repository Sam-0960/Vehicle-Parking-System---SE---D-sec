"""Presentation: admin reports with CSV export (FR-14)."""
from flask import Blueprint, Response, flash, render_template, request

from app.security import admin_required, audit
from app.services import ServiceError, report_service

bp = Blueprint("reports", __name__, url_prefix="/admin/reports")


def _range():
    return report_service.parse_range(request.args.get("start", ""), request.args.get("end", ""))


@bp.route("/")
@admin_required
def index():
    try:
        start, end = _range()
    except ServiceError as e:
        flash(str(e), "error")
        start, end = report_service.parse_range("", "")
    return render_template("reports/index.html", r=report_service.build(start, end))


@bp.route("/<kind>.csv")
@admin_required
def download(kind):
    try:
        start, end = _range()
        body = report_service.to_csv(kind, report_service.build(start, end))
    except ServiceError as e:
        return render_template("error.html", code=400, message=str(e)), 400
    audit("report_export", f"{kind} {start}..{end}")
    return Response(body, mimetype="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{kind}_{start}_{end}.csv"'})
