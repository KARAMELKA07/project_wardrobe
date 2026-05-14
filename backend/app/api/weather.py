from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..services.weather_service import WeatherService
from ..utils.auth import current_user_or_404


weather_bp = Blueprint("weather", __name__, url_prefix="/api/weather")


def parse_float_arg(name):
    value = request.args.get(name)
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@weather_bp.get("/current")
@jwt_required()
def current_weather():
    user = current_user_or_404()
    latitude = parse_float_arg("latitude")
    longitude = parse_float_arg("longitude")
    weather = WeatherService.get_current_weather(
        city=user.city,
        latitude=latitude,
        longitude=longitude,
    )
    return jsonify({"weather": weather})
