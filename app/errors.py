import logging

from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from app.exceptions import ApiError

logger = logging.getLogger(__name__)

GENERIC_MESSAGE = "The request could not be completed."


def _is_api_request():
    return request.path.startswith("/api/")


# The API answers in JSON, the browser gets the error page.
def _render(error_name, message, status_code):
    if _is_api_request():
        payload = {"error": error_name, "message": message}
        return jsonify(payload), status_code
    return render_template(
        "error.html", status_code=status_code, message=message
    ), status_code


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        if _is_api_request():
            return jsonify(error.to_dict()), error.status_code
        return _render(error.error_name, error.message, error.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return _render(error.name, error.description, error.code)

    # Anything unplanned is logged in full and reported without details.
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unhandled application error: %s", error)
        return _render("Internal Server Error", GENERIC_MESSAGE, 500)
