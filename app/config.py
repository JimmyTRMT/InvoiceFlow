"""Configuration objects built from environment variables."""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DEFAULT_DATABASE_PATH = BASE_DIR / "instance" / "invoiceflow.db"


def _default_database_url():
    """Build the SQLite URL, with the slashes SQLAlchemy expects."""
    return "sqlite:///{}".format(DEFAULT_DATABASE_PATH.as_posix())


def _env_int(name, default):
    """Read an integer setting, falling back if the value is unusable."""
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class BaseConfig:
    """Settings shared by every environment."""

    # Generated in development so that no secret has to live in the
    # repository, and required from the environment anywhere else.
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
    """Local settings with verbose errors and automatic reloading."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Settings for automated checks, on a throwaway database."""

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
    """Return the settings for an environment, development by default."""
    key = name or os.environ.get("APP_ENV", "development")
    return _CONFIG_BY_NAME.get(key.strip().lower(), DevelopmentConfig)
