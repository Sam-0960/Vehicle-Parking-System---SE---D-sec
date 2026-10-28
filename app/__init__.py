"""Vehicle Parking System - application factory.

Layered architecture (see Documents/Architecture Justification.pdf):
  Presentation Layer   -> app/presentation  (Flask blueprints + Jinja templates)
  Business Logic Layer -> app/services      (one service per component in the component diagram)
  Data Layer           -> app/data          (SQLite schema + repositories)

Each layer only calls the layer directly beneath it.
"""
from flask import Flask, g, render_template, session

from app import security
from app.config import Config
from app.data import db, user_repo


def create_app(config_object=Config, **overrides) -> Flask:
    app = Flask(
        __name__,
        template_folder="presentation/templates",
        static_folder="presentation/static",
    )
    app.config.from_object(config_object)
    app.config.update(overrides)

    db.init_app(app)
    _register_hooks(app)  # first, so g.user is loaded before blueprint hooks run
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_cli(app)
    return app


def _register_blueprints(app: Flask) -> None:
    from app.presentation.routes import admin, auth, availability, fees, history, main, notifications, parking, payments, reservations, search, slots, vehicles
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(vehicles.bp)
    app.register_blueprint(slots.bp)
    app.register_blueprint(availability.bp)
    app.register_blueprint(parking.bp)
    app.register_blueprint(reservations.bp)
    app.register_blueprint(fees.bp)
    app.register_blueprint(payments.bp)
    app.register_blueprint(history.bp)
    app.register_blueprint(notifications.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(search.bp)


def _register_hooks(app: Flask) -> None:
    @app.before_request
    def load_user():
        sid = session.get("sid")
        g.user = user_repo.get_by_session(sid) if sid else None
        if sid and g.user is None:
            session.clear()  # revoked or unknown session token

    @app.before_request
    def csrf_protect():
        security.check_csrf()

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp

    @app.context_processor
    def inject_helpers():
        return {
            "csrf_token": security.csrf_token,
            "has_feature": lambda name: name in app.blueprints,
        }


def _register_error_handlers(app: Flask) -> None:
    # Generic messages only: no stack traces or SQL details reach the user (C-04, T-10).
    messages = {
        400: "The request could not be processed.",
        403: "You do not have permission to open this page.",
        404: "The page you were looking for does not exist.",
        409: "That action conflicts with the current state. Please refresh and try again.",
        429: "Too many requests. Please wait a minute and try again.",
        500: "Something went wrong on our side. Please try again.",
    }
    for code, text in messages.items():
        def handler(err, code=code, text=text):
            detail = getattr(err, "description", None) if code == 400 else None
            return render_template("error.html", code=code, message=detail or text), code
        app.register_error_handler(code, handler)


def _register_cli(app: Flask) -> None:
    from app import cli
    cli.register(app)
