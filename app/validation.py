"""Reusable field validators applied to every request body."""

import re
from datetime import date
from decimal import Decimal

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


def to_decimal(value):
    """Convert a JSON value into a finite Decimal, or return None."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value).strip())
    except (ArithmeticError, ValueError):
        return None
    return number if number.is_finite() else None


def _bounded_decimal(data, field, errors, minimum, maximum):
    """Read a numeric field already known to be present."""
    number = to_decimal(data.get(field))
    if number is None:
        errors[field] = "Enter a valid number."
        return None
    if minimum is not None and number < minimum:
        errors[field] = f"Must be {minimum} or more."
        return None
    if maximum is not None and number > maximum:
        errors[field] = f"Must be {maximum} or less."
        return None
    return number


def required_decimal(data, field, errors, minimum=None, maximum=None):
    """Read a mandatory numeric field within the given bounds."""
    if data.get(field) is None:
        errors[field] = "This field is required."
        return None
    return _bounded_decimal(data, field, errors, minimum, maximum)


def optional_decimal(data, field, default, errors, minimum=None,
                     maximum=None):
    """Read a numeric field, using the default when it is absent."""
    if data.get(field) is None:
        return default
    return _bounded_decimal(data, field, errors, minimum, maximum)


def date_field(data, field, errors):
    """Read a mandatory date written as YYYY-MM-DD."""
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors[field] = "This field is required."
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        errors[field] = "Use the YYYY-MM-DD format."
        return None


def choice_field(data, field, allowed, default, errors):
    """Read a field that has to be one of a fixed set of values."""
    value = data.get(field)
    if value is None:
        return default
    if isinstance(value, str) and value.strip().lower() in allowed:
        return value.strip().lower()
    errors[field] = f"Choose one of: {', '.join(allowed)}."
    return None
