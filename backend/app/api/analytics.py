from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..services.analytics_service import WardrobeAnalyticsService
from ..utils.auth import current_user_or_404


analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.get("/summary")
@jwt_required()
def analytics_summary():
    user = current_user_or_404()
    items = list(user.clothing_items)
    summary = WardrobeAnalyticsService.build_summary(items)
    return jsonify(summary)
