"""Errors the API turns into a JSON response with a status code."""


class ApiError(Exception):
    """An expected failure carrying a status code and a message."""

    status_code = 500
    error_name = "Error"

    def __init__(self, message, errors=None):
        """Store the message and the optional per field details."""
        super().__init__(message)
        self.message = message
        self.errors = errors or {}

    def to_dict(self):
        """Build the JSON body sent back to the client."""
        payload = {"error": self.error_name, "message": self.message}
        if self.errors:
            payload["errors"] = self.errors
        return payload


class ValidationError(ApiError):
    """The request body was understood but its content is not usable."""

    status_code = 400
    error_name = "Validation Error"


class ConflictError(ApiError):
    """The request is valid but the current data does not allow it."""

    status_code = 409
    error_name = "Conflict"
