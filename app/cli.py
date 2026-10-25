"""Command-line helpers: flask --app run <command>."""
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
