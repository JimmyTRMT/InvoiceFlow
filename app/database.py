"""Database bootstrap, SQLite setup and session helpers."""

import logging
import sqlite3

from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

# Imported for its side effect: it registers the tables on the metadata.
from app import models  # noqa: F401  isort:skip

logger = logging.getLogger(__name__)


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Turn on the foreign key checks that SQLite skips by default."""
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def register_database_events(app):
    """Attach the connection listeners to this application's engine."""
    with app.app_context():
        event.listen(db.engine, "connect", _enable_sqlite_foreign_keys)


def create_schema():
    """Create every missing table, from inside an application context."""
    db.create_all()


def commit_or_rollback(action):
    """Commit the transaction, rolling back and logging on failure."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while trying to %s", action)
        raise
