# Failures the API turns into a JSON body and a status code.
class ApiError(Exception):
    status_code = 500
    error_name = "Error"

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}

    def to_dict(self):
        payload = {"error": self.error_name, "message": self.message}
        if self.errors:
            payload["errors"] = self.errors
        return payload


class ValidationError(ApiError):
    status_code = 400
    error_name = "Validation Error"


class ConflictError(ApiError):
    status_code = 409
    error_name = "Conflict"
