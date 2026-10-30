"""Data Layer: connection handling and schema setup.

Only the Data Layer opens database connections (C-10). Every query uses
parameter binding, never string formatting (C-03).
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(
            current_app.config["DATABASE"],
            timeout=10,
            isolation_level=None,  # autocommit; explicit transactions via transaction()
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        g.db = conn
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


@contextmanager
def transaction(immediate: bool = False):
    """Run a block atomically.

    immediate=True takes the write lock up front, so two requests cannot both
    read "slot free" and then both claim it (NFR-08).
    """
    conn = get_db()
    conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def init_db() -> None:
    conn = get_db()
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        init_db()


def backup_to(path: str) -> None:
    """Consistent online copy of the database (NFR-03), safe while the app is running."""
    target = sqlite3.connect(path)
    try:
        get_db().backup(target)
    finally:
        target.close()
