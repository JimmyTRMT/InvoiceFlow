"""Shared extension instances.

The extensions live in their own module so that models, blueprints and
scripts can import them without importing the application factory, which
would create a circular import.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
