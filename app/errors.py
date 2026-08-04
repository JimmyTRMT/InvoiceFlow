"""JSON error handlers used by the whole API.

Flask answers with an HTML page when something goes wrong. The frontend
only ever reads JSON, so these handlers keep one single response shape
for expected failures (404, 400) and unexpected ones alike.
"""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Attach the JSON error handlers to an application instance."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Turn a Werkzeug HTTP error into a JSON payload."""
        payload = {"error": error.name, "message": error.description}
        return jsonify(payload), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Log the failure and return a generic message to the client.

        Internal details are kept in the server log only: an exception
        message can leak file paths or SQL fragments.
        """
        logger.exception("Unhandled application error: %s", error)
        payload = {
            "error": "Internal Server Error",
            "message": "The request could not be completed.",
        }
        return jsonify(payload), 500
