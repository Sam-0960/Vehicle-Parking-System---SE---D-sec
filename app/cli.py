"""Command-line helpers: flask --app run <command>."""
import click

from app.data import db


def register(app) -> None:
    @app.cli.command("init-db")
    def init_db_command():
        """Create tables (safe to run repeatedly)."""
        db.init_db()
        click.echo("Database ready.")
