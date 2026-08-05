"""Shared extension instances, kept apart to avoid circular imports."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
