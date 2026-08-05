"""CSRF protection based on the double submit cookie pattern."""

import secrets

from flask import abort, request

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _tokens_match(cookie_token, header_token):
    """Compare the two tokens without leaking timing information."""
    if not cookie_token or not header_token:
        return False
    return secrets.compare_digest(
        cookie_token.encode("utf-8", "replace"),
        header_token.encode("utf-8", "replace"),
    )


def register_csrf_protection(app):
    """Check unsafe requests and hand out the token cookie."""

    @app.before_request
    def verify_csrf_token():
        """Reject any unsafe request that does not echo the token."""
        if request.method in SAFE_METHODS:
            return None
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)
        if not _tokens_match(cookie_token, header_token):
            abort(
                403,
                description=(
                    "Missing or invalid CSRF token. Reload the page and "
                    "try again."
                ),
            )
        return None

    @app.after_request
    def issue_csrf_cookie(response):
        """Give the browser a token when it does not have one yet."""
        if request.cookies.get(CSRF_COOKIE_NAME):
            return response
        response.set_cookie(
            CSRF_COOKIE_NAME,
            secrets.token_urlsafe(32),
            samesite="Strict",
            # Readable on purpose: the frontend copies the value into
            # the request header.
            httponly=False,
            secure=app.config.get("SESSION_COOKIE_SECURE", False),
        )
        return response
