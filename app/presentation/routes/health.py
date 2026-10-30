"""Health check for uptime monitoring (NFR-05)."""
from flask import Blueprint, jsonify

from app.data.db import get_db

bp = Blueprint("health", __name__)


@bp.route("/health")
def health():
    try:
        get_db().execute("SELECT 1").fetchone()
    except Exception:
        return jsonify(status="degraded", database="unreachable"), 503
    return jsonify(status="ok", database="ok")
