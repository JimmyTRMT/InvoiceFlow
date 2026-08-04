"""Helpers shared by every model."""

from datetime import datetime, timezone

from app.extensions import db


def utcnow():
    """Return the current UTC time, without a timezone attached.

    SQLite stores no offset, so an aware datetime would silently come
    back naive. Dropping the tzinfo here makes the round trip lossless
    and keeps one rule: everything in the database is UTC.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_iso(value):
    """Render a date or a stored UTC datetime as an ISO 8601 string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat() + "Z"
    return value.isoformat()


class TimestampMixin:
    """Adds creation and last update timestamps to a model."""

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
