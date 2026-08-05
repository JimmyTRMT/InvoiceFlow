"""JSON error handlers, so the API never answers with an HTML page."""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from app.exceptions import ApiError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Attach the JSON error handlers to an application instance."""

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        """Render an expected failure with its own status code."""
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Turn a Werkzeug HTTP error into a JSON payload."""
        payload = {"error": error.name, "message": error.description}
        return jsonify(payload), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Log the failure and answer without exposing any internals."""
        logger.exception("Unhandled application error: %s", error)
        payload = {
            "error": "Internal Server Error",
            "message": "The request could not be completed.",
        }
        return jsonify(payload), 500
