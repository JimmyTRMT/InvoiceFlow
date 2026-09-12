from datetime import datetime, timezone

from app.extensions import db


# SQLite has no timezone aware type, so UTC is stored naive.
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat() + "Z"
    return value.isoformat()


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
