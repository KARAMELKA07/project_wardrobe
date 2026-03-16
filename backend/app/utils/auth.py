from flask_jwt_extended import get_jwt_identity

from ..extensions import db
from ..models import User
from .errors import ApiError


def current_user_or_404():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id is not None else None
    if user is None:
        raise ApiError("Пользователь не найден.", 404)
    return user
