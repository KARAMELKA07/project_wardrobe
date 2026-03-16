from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, jwt_required

from ..extensions import db
from ..models import User, UserPreferences
from ..schemas.auth import validate_login_payload, validate_register_payload
from ..utils.auth import current_user_or_404
from ..utils.errors import ApiError
from ..utils.request import get_request_payload


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    payload = validate_register_payload(get_request_payload())

    existing_user = User.query.filter_by(email=payload["email"]).first()
    if existing_user:
        raise ApiError("Пользователь с таким email уже существует.", 409)

    user = User(
        email=payload["email"],
        name=payload["name"],
        city=payload["city"],
    )
    user.set_password(payload["password"])
    user.preferences = UserPreferences(
        preferred_styles=[],
        preferred_colors=[],
        constraints=[],
        disliked_items=[],
    )

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    return (
        jsonify(
            {
                "access_token": access_token,
                "user": user.to_dict(),
            }
        ),
        201,
    )


@auth_bp.post("/login")
def login():
    payload = validate_login_payload(get_request_payload())

    user = User.query.filter_by(email=payload["email"]).first()
    if user is None or not user.check_password(payload["password"]):
        raise ApiError("Неверный email или пароль.", 401)

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = current_user_or_404()
    return jsonify({"user": user.to_dict()})
