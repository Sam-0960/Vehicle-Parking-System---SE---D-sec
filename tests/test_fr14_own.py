from datetime import date

from app.services import report_service


def test_empty_range_has_zero_sessions(app):
    with app.app_context():
        r = report_service.build(date(2026, 1, 1), date(2026, 1, 2))
    assert r["usage"]["total_sessions"] == 0
    assert r["revenue"]["total"] == 0
