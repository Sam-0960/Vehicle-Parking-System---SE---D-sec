"""Command-line helpers: flask --app run <command>."""
from datetime import datetime
from pathlib import Path

import click

from app.data import db, user_repo
from app.services import ServiceError, auth_service


def register(app) -> None:
    @app.cli.command("init-db")
    def init_db_command():
        """Create tables (safe to run repeatedly)."""
        db.init_db()
        click.echo("Database ready.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_admin(name, email, password):
        """Create a parking administrator. There are no default admin accounts (C-08)."""
        try:
            uid = auth_service.register(name, email, password, password, role="admin")
        except ServiceError as e:
            raise click.ClickException(str(e))
        click.echo(f"Administrator {email} created (id {uid}).")

    @app.cli.command("promote")
    @click.argument("email")
    def promote(email):
        """Give an existing account the administrator role."""
        row = user_repo.get_auth_by_email(email.strip().lower())
        if row is None:
            raise click.ClickException("No account with that email.")
        user_repo.set_role(row["id"], "admin")
        click.echo(f"{email} is now an administrator.")

    @app.cli.command("backup")
    @click.option("--dir", "directory", default="backups", show_default=True)
    def backup(directory):
        """Write a timestamped copy of the database (NFR-03)."""
        Path(directory).mkdir(parents=True, exist_ok=True)
        path = Path(directory) / f"parking-{datetime.now():%Y%m%d-%H%M%S}.db"
        db.backup_to(str(path))
        click.echo(f"Backup written to {path}")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Load the Human Test Plan data for a demo. Never run this in production."""
        from app.services import slot_service, vehicle_service
        from app.data import slot_repo
        created = []
        for email, name in (("ravi@test.com", "Ravi"), ("admin@test.com", "Parking Admin")):
            if user_repo.get_auth_by_email(email) is None:
                auth_service.register(name, email, "Park@123", "Park@123",
                                      role="admin" if email.startswith("admin") else "user")
                created.append(email)
        for code, kind in (("A01", "car"), ("A02", "car"), ("A03", "car"), ("A04", "car"),
                           ("M01", "bike"), ("M02", "bike"), ("T01", "truck")):
            if slot_repo.get_by_code(code) is None:
                slot_service.add(code, kind)
        ravi = user_repo.get_auth_by_email("ravi@test.com")
        for number in ("KA01AB1234", "KA02CD5678", "KA03EF9012"):
            try:
                vehicle_service.add(ravi["id"], number, "car", "Ravi")
            except ServiceError:
                pass
        click.echo("Demo data loaded. Logins (password Park@123): ravi@test.com, admin@test.com")
        click.echo("Remove these accounts before any real deployment (C-08).")
