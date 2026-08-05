"""Reusable field validators applied to every request body."""

import re

from flask import request

from app.exceptions import ValidationError

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")

# Control characters never belong in a name and can slip past a display
# layer, so they are removed rather than escaped.
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def get_json_body():
    """Return the request body as a dictionary, or reject it."""
    body = request.get_json(silent=True)
    if body is None:
        raise ValidationError("The request body must be valid JSON.")
    if not isinstance(body, dict):
        raise ValidationError("The request body must be a JSON object.")
    return body


def clean_text(value):
    """Trim a string and drop its control characters."""
    return CONTROL_CHARACTERS.sub("", value).strip()


def required_string(data, field, max_length, errors):
    """Read a mandatory text field, trimmed and length checked."""
    value = data.get(field)
    if not isinstance(value, str):
        errors[field] = "This field is required."
        return None

    value = clean_text(value)
    if not value:
        errors[field] = "This field is required."
        return None
    if len(value) > max_length:
        errors[field] = f"Maximum length is {max_length} characters."
        return None
    return value


def optional_string(data, field, max_length, errors):
    """Read a text field that may be missing, null or empty."""
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        errors[field] = "This field must be text."
        return None

    value = clean_text(value)
    if not value:
        return None
    if len(value) > max_length:
        errors[field] = f"Maximum length is {max_length} characters."
        return None
    return value


def email_address(data, field, errors):
    """Read a mandatory field and check that it looks like an email."""
    value = required_string(data, field, 255, errors)
    if value is None:
        return None
    if not EMAIL_PATTERN.match(value):
        errors[field] = "Enter a valid email address."
        return None
    return value
