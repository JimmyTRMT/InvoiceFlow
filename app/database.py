"""Database bootstrap and SQLite specific setup."""

import sqlite3

from sqlalchemy import event

from app.extensions import db

# Importing the models attaches them to the SQLAlchemy metadata, which is
# how create_schema knows which tables to build.
from app import models  # noqa: F401  isort:skip


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Turn on foreign key enforcement for a SQLite connection.

    SQLite ignores foreign keys unless the pragma is set on every single
    connection, which would let orphan line items into the database.
    """
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def register_database_events(app):
    """Attach the connection listeners to this application's engine.

    Binding to the engine rather than to the global Engine class keeps
    the listeners from stacking when several apps live in one process.
    """
    with app.app_context():
        event.listen(db.engine, "connect", _enable_sqlite_foreign_keys)


def create_schema():
    """Create every missing table. Requires an application context."""
    db.create_all()
