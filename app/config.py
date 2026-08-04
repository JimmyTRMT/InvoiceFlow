"""Configuration objects built from environment variables.

Every setting is read from the process environment (optionally loaded
from a local .env file) so that the same code can run on a laptop or on
a server without a single value being hard-coded in the source tree.
"""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DEFAULT_DATABASE_PATH = BASE_DIR / "instance" / "invoiceflow.db"


def _default_database_url():
    """Build the SQLite URL used when DATABASE_URL is not provided.

    The path is normalised to forward slashes because a Windows path
    with backslashes is not a valid SQLAlchemy connection string.
    """
    return "sqlite:///{}".format(DEFAULT_DATABASE_PATH.as_posix())


def _env_int(name, default):
    """Read an integer setting, falling back to a default value.

    A typo in the .env file should not stop the server from booting, so
    an unusable value is replaced rather than raised.
    """
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class BaseConfig:
    """Settings shared by every environment."""

    # A generated key keeps development working without storing a
    # secret in the repository. Production is required to provide one.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or _default_database_url()
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = _env_int("PORT", 5000)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(BaseConfig):
    """Local settings: verbose errors and automatic reloading."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Settings for automated checks, backed by a throwaway database."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Hardened settings for a deployed instance."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True


_CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    """Return the configuration class matching an environment name.

    An unknown name falls back to development so a typo in APP_ENV can
    never silently start the app with production behaviour.
    """
    key = name or os.environ.get("APP_ENV", "development")
    return _CONFIG_BY_NAME.get(key.strip().lower(), DevelopmentConfig)
