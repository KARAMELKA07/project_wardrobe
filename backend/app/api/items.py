from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import ClothingItem
from ..schemas.item import validate_clothing_item_payload
from ..utils.auth import current_user_or_404
from ..utils.errors import ApiError
from ..utils.request import get_request_payload
from ..utils.storage import remove_local_image, save_image


items_bp = Blueprint("items", __name__, url_prefix="/api/items")


def get_owned_item_or_404(user_id, item_id):
    item = ClothingItem.query.filter_by(id=item_id, user_id=user_id).first()
    if item is None:
        raise ApiError("Вещь не найдена.", 404)
    return item


@items_bp.post("")
@jwt_required()
def create_item():
    user = current_user_or_404()
    payload = get_request_payload()

    if "image" in request.files:
        payload["image_url"] = save_image(
            request.files["image"],
            current_app.config["UPLOAD_FOLDER"],
            current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
        )

    cleaned_payload = validate_clothing_item_payload(payload)
    item = ClothingItem(user_id=user.id, **cleaned_payload)
    db.session.add(item)
    db.session.commit()

    return jsonify({"item": item.to_dict()}), 201


@items_bp.get("")
@jwt_required()
def list_items():
    user = current_user_or_404()
    items = (
        ClothingItem.query.filter_by(user_id=user.id)
        .order_by(ClothingItem.id.desc())
        .all()
    )
    return jsonify({"items": [item.to_dict() for item in items]})


@items_bp.get("/<int:item_id>")
@jwt_required()
def get_item(item_id):
    user = current_user_or_404()
    item = get_owned_item_or_404(user.id, item_id)
    return jsonify({"item": item.to_dict()})


@items_bp.put("/<int:item_id>")
@jwt_required()
def update_item(item_id):
    user = current_user_or_404()
    item = get_owned_item_or_404(user.id, item_id)
    payload = get_request_payload()

    if "image" in request.files:
        new_image_url = save_image(
            request.files["image"],
            current_app.config["UPLOAD_FOLDER"],
            current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
        )
        if item.image_url:
            remove_local_image(item.image_url, current_app.config["UPLOAD_FOLDER"])
        payload["image_url"] = new_image_url

    cleaned_payload = validate_clothing_item_payload(payload)
    for field_name, field_value in cleaned_payload.items():
        setattr(item, field_name, field_value)

    db.session.commit()
    return jsonify({"item": item.to_dict()})


@items_bp.delete("/<int:item_id>")
@jwt_required()
def delete_item(item_id):
    user = current_user_or_404()
    item = get_owned_item_or_404(user.id, item_id)

    if item.image_url:
        remove_local_image(item.image_url, current_app.config["UPLOAD_FOLDER"])

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Вещь успешно удалена."})


@items_bp.post("/upload")
@jwt_required()
def upload_item_image():
    if "image" not in request.files:
        raise ApiError("Необходимо загрузить изображение.", 400)

    image_url = save_image(
        request.files["image"],
        current_app.config["UPLOAD_FOLDER"],
        current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
    )
    return jsonify({"image_url": image_url}), 201
