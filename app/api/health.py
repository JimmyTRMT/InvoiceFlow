from datetime import datetime, timezone

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    payload = {
        "status": "ok",
        "service": "invoiceflow-api",
        "time": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(payload), 200
