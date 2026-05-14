from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..services.weather_service import MockWeatherService
from ..utils.auth import current_user_or_404


weather_bp = Blueprint("weather", __name__, url_prefix="/api/weather")


@weather_bp.get("/current")
@jwt_required()
def current_weather():
    user = current_user_or_404()
    weather = MockWeatherService.get_current_weather(user.city)
    return jsonify({"weather": weather})
