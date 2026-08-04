"""Application factory for the InvoiceFlow backend.

Building the app inside a function instead of at import time keeps the
configuration explicit: the web server, the seed script and any future
tooling all create their own instance with the settings they need.
"""

import os

from flask import Flask

from app.api.health import health_bp
from app.config import get_config
from app.errors import register_error_handlers
from app.extensions import db


def create_app(config_name=None):
    """Create a configured Flask application.

    The optional config_name overrides the APP_ENV variable, which is
    what scripts use when they need a specific environment.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))

    _require_secret_key(app)
    _ensure_instance_folder(app)

    db.init_app(app)
    register_error_handlers(app)
    _register_blueprints(app)

    return app


def _require_secret_key(app):
    """Refuse to start outside development without a real SECRET_KEY.

    The fallback key is regenerated on every boot, which would silently
    invalidate signed cookies, so a deployed instance must provide one.
    """
    if app.debug or app.testing or os.environ.get("SECRET_KEY"):
        return
    raise RuntimeError(
        "SECRET_KEY must be set in the environment outside development."
    )


def _ensure_instance_folder(app):
    """Create the instance folder that holds the SQLite database."""
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as error:
        raise RuntimeError(
            f"Could not create the instance folder: {app.instance_path}"
        ) from error


def _register_blueprints(app):
    """Mount every API blueprint under the /api prefix."""
    app.register_blueprint(health_bp, url_prefix="/api")
