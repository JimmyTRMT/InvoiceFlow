from flask import Blueprint, jsonify

from app.services.dashboard import get_dashboard_stats

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/dashboard/stats")
def dashboard_stats():
    return jsonify(get_dashboard_stats()), 200
