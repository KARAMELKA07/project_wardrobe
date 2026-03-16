from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import ClothingItem, Outfit, OutfitFeedback, OutfitItem
from ..schemas.outfit import (
    validate_feedback_payload,
    validate_generate_payload,
    validate_save_outfit_payload,
)
from ..services.recommendation_engine import RecommendationEngine
from ..services.weather_service import MockWeatherService
from ..utils.auth import current_user_or_404
from ..utils.errors import ApiError
from ..utils.request import get_request_payload


outfits_bp = Blueprint("outfits", __name__, url_prefix="/api/outfits")


def get_owned_outfit_or_404(user_id, outfit_id):
    outfit = Outfit.query.filter_by(id=outfit_id, user_id=user_id).first()
    if outfit is None:
        raise ApiError("Образ не найден.", 404)
    return outfit


@outfits_bp.get("")
@jwt_required()
def list_saved_outfits():
    user = current_user_or_404()
    outfits = Outfit.query.filter_by(user_id=user.id).order_by(Outfit.id.desc()).all()
    return jsonify({"outfits": [outfit.to_dict() for outfit in outfits]})


@outfits_bp.post("")
@jwt_required()
def save_outfit():
    user = current_user_or_404()
    payload = validate_save_outfit_payload(get_request_payload())

    item_ids = [entry["clothing_item_id"] for entry in payload["items"]]
    owned_items = ClothingItem.query.filter(
        ClothingItem.user_id == user.id,
        ClothingItem.id.in_(item_ids),
    ).all()
    owned_item_ids = {item.id for item in owned_items}
    if owned_item_ids != set(item_ids):
        raise ApiError(
            "Все вещи в образе должны принадлежать текущему пользователю.",
            400,
        )

    outfit = Outfit(
        user_id=user.id,
        name=payload["name"],
        event_type=payload["event_type"],
        weather_context=payload["weather_context"],
        score=payload["score"],
        explanation=payload["explanation"],
    )
    db.session.add(outfit)
    db.session.flush()

    for item_entry in payload["items"]:
        db.session.add(
            OutfitItem(
                outfit_id=outfit.id,
                clothing_item_id=item_entry["clothing_item_id"],
                role=item_entry["role"],
            )
        )

    db.session.add(
        OutfitFeedback(
            outfit_id=outfit.id,
            user_id=user.id,
            reaction="save",
        )
    )
    db.session.commit()

    saved_outfit = get_owned_outfit_or_404(user.id, outfit.id)
    return jsonify({"outfit": saved_outfit.to_dict()}), 201


@outfits_bp.get("/<int:outfit_id>")
@jwt_required()
def get_outfit(outfit_id):
    user = current_user_or_404()
    outfit = get_owned_outfit_or_404(user.id, outfit_id)
    return jsonify({"outfit": outfit.to_dict()})


@outfits_bp.post("/generate")
@jwt_required()
def generate_outfits():
    user = current_user_or_404()
    payload = validate_generate_payload(get_request_payload())

    weather_context = {
        "city": user.city,
        "temperature": payload["temperature"],
        "weather_condition": payload["weather_condition"],
        "season": None,
    }
    if payload["temperature"] is None or payload["weather_condition"] is None:
        mock_weather = MockWeatherService.get_current_weather(user.city)
        if payload["temperature"] is None:
            weather_context["temperature"] = mock_weather["temperature"]
            weather_context["season"] = mock_weather["season"]
        if payload["weather_condition"] is None:
            weather_context["weather_condition"] = mock_weather["weather_condition"]

    generation_context = {
        **payload,
        **weather_context,
    }

    items = ClothingItem.query.filter_by(user_id=user.id).all()
    if not items:
        return jsonify(
            {
                "outfits": [],
                "weather": weather_context,
                "message": "У пользователя пока недостаточно вещей для генерации образов.",
            }
        )

    engine = RecommendationEngine()
    if payload["anchor_item_id"] and not any(
        item.id == payload["anchor_item_id"] for item in items
    ):
        return jsonify(
            {
                "outfits": [],
                "weather": weather_context,
                "message": "Опорная вещь не принадлежит текущему пользователю.",
            }
        )

    candidate_outfits = engine.generate_candidate_outfits(items, generation_context)
    if not candidate_outfits:
        return jsonify(
            {
                "outfits": [],
                "weather": weather_context,
                "message": "Не удалось собрать корректные комбинации из текущего гардероба.",
            }
        )

    generated_outfits = [
        engine.evaluate_outfit(
            candidate,
            generation_context,
            user.preferences.to_dict() if user.preferences else {},
        )
        for candidate in candidate_outfits
    ]
    generated_outfits.sort(key=lambda outfit: outfit["score"], reverse=True)
    top_outfits = generated_outfits[:5]

    for index, outfit in enumerate(top_outfits, start=1):
        outfit["name"] = engine.build_outfit_name(payload["event_type"], index)

    return jsonify({"outfits": top_outfits, "weather": weather_context})


@outfits_bp.post("/<int:outfit_id>/feedback")
@jwt_required()
def add_feedback(outfit_id):
    user = current_user_or_404()
    outfit = get_owned_outfit_or_404(user.id, outfit_id)
    payload = validate_feedback_payload(get_request_payload())

    feedback = OutfitFeedback.query.filter_by(
        outfit_id=outfit.id,
        user_id=user.id,
    ).first()
    if feedback is None:
        feedback = OutfitFeedback(
            outfit_id=outfit.id,
            user_id=user.id,
            reaction=payload["reaction"],
        )
        db.session.add(feedback)
    else:
        feedback.reaction = payload["reaction"]

    db.session.commit()
    return jsonify({"feedback": feedback.to_dict()})
