"""Error handlers that answer in JSON or in HTML depending on the URL."""

import logging

from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from app.exceptions import ApiError

logger = logging.getLogger(__name__)

GENERIC_MESSAGE = "The request could not be completed."


def _is_api_request():
    """Tell whether the failing request was aimed at the JSON API."""
    return request.path.startswith("/api/")


def _render(error_name, message, status_code):
    """Answer with JSON for the API and with a page for the browser."""
    if _is_api_request():
        payload = {"error": error_name, "message": message}
        return jsonify(payload), status_code
    return render_template(
        "error.html", status_code=status_code, message=message
    ), status_code


def register_error_handlers(app):
    """Attach the error handlers to an application instance."""

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        """Render an expected failure with its own status code."""
        if _is_api_request():
            return jsonify(error.to_dict()), error.status_code
        return _render(error.error_name, error.message, error.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Render a Werkzeug HTTP error such as a 404 or a 405."""
        return _render(error.name, error.description, error.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Log the failure and answer without exposing any internals."""
        logger.exception("Unhandled application error: %s", error)
        return _render("Internal Server Error", GENERIC_MESSAGE, 500)
