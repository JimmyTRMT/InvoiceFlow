"""Health check endpoint.

Used to confirm that the process is up and answering requests, both
during setup and when the frontend cannot reach the API.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """Report that the API is running, with a UTC timestamp."""
    payload = {
        "status": "ok",
        "service": "invoiceflow-api",
        "time": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload), 200
