"""Application factory for the InvoiceFlow backend."""

import os

from flask import Flask

from app.api.clients import clients_bp
from app.api.health import health_bp
from app.cli import register_cli
from app.config import get_config
from app.database import register_database_events
from app.errors import register_error_handlers
from app.extensions import db
from app.security import register_csrf_protection


def create_app(config_name=None):
    """Create a Flask application wired for the given environment."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))

    _require_secret_key(app)
    _ensure_instance_folder(app)

    db.init_app(app)
    register_database_events(app)
    register_csrf_protection(app)
    register_error_handlers(app)
    register_cli(app)
    _register_blueprints(app)

    return app


def _require_secret_key(app):
    """Refuse to start on a generated key outside development."""
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
    app.register_blueprint(clients_bp, url_prefix="/api")
