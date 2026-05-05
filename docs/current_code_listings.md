# Текущие листинги проекта

Документ содержит актуальные исходные листинги проекта.
В сборник включены исходные файлы backend и frontend, миграции, тесты, README и шаблон переменных окружения.
Из сборника исключены виртуальное окружение, node_modules, dist, кэши и бинарные медиафайлы.

## .env.example

```
SECRET_KEY=replace-with-a-random-secret
JWT_SECRET_KEY=replace-with-a-random-jwt-secret
FLASK_DEBUG=true
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
FRONTEND_URL=http://localhost:5173

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=wardrobe_mvp

UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=8388608

VITE_API_URL=http://localhost:5000/api
```

## backend\app\__init__.py

```python
import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .api import register_blueprints
from .cli import register_cli
from .config import Config
from .extensions import init_extensions
from .utils.errors import ApiError


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(
        app,
        resources={
            r"/api/*": {"origins": app.config["FRONTEND_URL"]},
            r"/uploads/*": {"origins": app.config["FRONTEND_URL"]},
        },
    )

    init_extensions(app)

    from . import models  # noqa: F401

    register_blueprints(app)
    register_cli(app)
    register_error_handlers(app)
    register_misc_routes(app)

    return app


def register_misc_routes(app):
    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok"})

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        payload = {"error": error.message}
        if error.details:
            payload["details"] = error.details
        return jsonify(payload), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": "Ресурс не найден."}), 404

    @app.errorhandler(413)
    def handle_large_file(_error):
        return jsonify({"error": "Загруженный файл слишком большой."}), 413

    @app.errorhandler(500)
    def handle_internal_error(_error):
        return jsonify({"error": "Внутренняя ошибка сервера."}), 500
```

## backend\app\api\__init__.py

```python
from .analytics import analytics_bp
from .auth import auth_bp
from .items import items_bp
from .outfits import outfits_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(outfits_bp)
    app.register_blueprint(analytics_bp)
```

## backend\app\api\analytics.py

```python
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
```

## backend\app\api\auth.py

```python
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
```

## backend\app\api\items.py

```python
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
```

## backend\app\api\outfits.py

```python
from flask import Blueprint, current_app, jsonify, request
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
from ..utils.storage import remove_local_image, save_image


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
        feature_scores=payload["feature_scores"],
        reasons=payload["reasons"],
        styled_photo_url=payload["styled_photo_url"],
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


@outfits_bp.post("/<int:outfit_id>/photo")
@jwt_required()
def upload_outfit_photo(outfit_id):
    user = current_user_or_404()
    outfit = get_owned_outfit_or_404(user.id, outfit_id)

    if "image" not in request.files:
        raise ApiError("Необходимо загрузить изображение.", 400)

    new_image_url = save_image(
        request.files["image"],
        current_app.config["UPLOAD_FOLDER"],
        current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
    )
    if outfit.styled_photo_url:
        remove_local_image(outfit.styled_photo_url, current_app.config["UPLOAD_FOLDER"])

    outfit.styled_photo_url = new_image_url
    db.session.commit()
    return jsonify({"outfit": outfit.to_dict()})


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
```

## backend\app\cli.py

```python
import click

from .extensions import db
from .models import User
from .services.demo_wardrobe_seed import (
    get_demo_wardrobe_item_count,
    seed_demo_wardrobe_for_user,
)


def register_cli(app):
    @app.cli.command("seed-demo-wardrobe")
    @click.option("--email", default="demo@wardrobe.local", show_default=True)
    @click.option("--password", default="demo12345", show_default=True)
    @click.option("--name", default="Демо пользователь", show_default=True)
    @click.option("--city", default="Москва", show_default=True)
    def seed_demo_wardrobe(email, password, name, city):
        """Создает демо-пользователя и тестовый гардероб для подбора образов."""

        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        created = user is None

        if user is None:
            user = User(email=email, name=name, city=city)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        else:
            user.name = name
            user.city = city
            user.set_password(password)
            db.session.commit()

        seed_demo_wardrobe_for_user(user, replace_existing=True)

        click.echo("Тестовый гардероб успешно заполнен.")
        click.echo(f"Пользователь создан: {'да' if created else 'нет'}")
        click.echo(f"Email: {email}")
        click.echo(f"Пароль: {password}")
        click.echo(f"Добавлено вещей: {get_demo_wardrobe_item_count()}")
```

## backend\app\config\__init__.py

```python
from .settings import Config


__all__ = ["Config"]
```

## backend\app\config\settings.py

```python
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def build_database_uri():
    explicit_uri = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if explicit_uri:
        return explicit_uri

    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    username = os.getenv("MYSQL_USER", "root")
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    database = os.getenv("MYSQL_DB", "wardrobe_mvp")
    return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-too")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    FLASK_RUN_PORT = int(os.getenv("FLASK_RUN_PORT", "5000"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(8 * 1024 * 1024)))
    UPLOAD_FOLDER = str(PROJECT_ROOT / os.getenv("UPLOAD_FOLDER", "uploads"))
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
```

## backend\app\extensions\__init__.py

```python
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
```

## backend\app\models\__init__.py

```python
from .clothing_item import ClothingItem
from .outfit import Outfit, OutfitItem
from .outfit_feedback import OutfitFeedback
from .user import User
from .user_preferences import UserPreferences


__all__ = [
    "ClothingItem",
    "Outfit",
    "OutfitFeedback",
    "OutfitItem",
    "User",
    "UserPreferences",
]
```

## backend\app\models\clothing_item.py

```python
from ..extensions import db


class ClothingItem(db.Model):
    __tablename__ = "clothing_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    image_url = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    subcategory = db.Column(db.String(100), nullable=True)
    colors = db.Column(db.JSON, nullable=False, default=list)
    styles = db.Column(db.JSON, nullable=False, default=list)
    season = db.Column(db.String(50), nullable=False, default="all-season")
    formality = db.Column(db.String(50), nullable=False, default="casual")
    fit = db.Column(db.String(50), nullable=True)
    layer_level = db.Column(db.String(50), nullable=True)
    insulation_rating = db.Column(db.Float, nullable=False, default=0.0)
    waterproof = db.Column(db.Boolean, nullable=False, default=False)
    windproof = db.Column(db.Boolean, nullable=False, default=False)
    material = db.Column(db.String(80), nullable=True)

    user = db.relationship("User", back_populates="clothing_items")
    outfit_items = db.relationship(
        "OutfitItem",
        back_populates="clothing_item",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_url": self.image_url,
            "title": self.title,
            "category": self.category,
            "subcategory": self.subcategory,
            "colors": self.colors or [],
            "styles": self.styles or [],
            "season": self.season,
            "formality": self.formality,
            "fit": self.fit,
            "layer_level": self.layer_level,
            "insulation_rating": self.insulation_rating,
            "waterproof": self.waterproof,
            "windproof": self.windproof,
            "material": self.material,
        }
```

## backend\app\models\outfit.py

```python
from ..extensions import db


class Outfit(db.Model):
    __tablename__ = "outfits"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(80), nullable=False)
    weather_context = db.Column(db.JSON, nullable=True, default=dict)
    score = db.Column(db.Float, nullable=False, default=0.0)
    explanation = db.Column(db.Text, nullable=True)
    feature_scores = db.Column(db.JSON, nullable=True, default=dict)
    reasons = db.Column(db.JSON, nullable=True, default=list)
    # Keep the Python attribute name stable while staying compatible with
    # databases where the column was previously created as `user_photo_url`.
    styled_photo_url = db.Column("user_photo_url", db.String(500), nullable=True)

    user = db.relationship("User", back_populates="outfits")
    items = db.relationship(
        "OutfitItem",
        back_populates="outfit",
        cascade="all, delete-orphan",
    )
    feedback_entries = db.relationship(
        "OutfitFeedback",
        back_populates="outfit",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "event_type": self.event_type,
            "weather_context": self.weather_context or {},
            "score": round(self.score or 0.0, 4),
            "explanation": self.explanation,
            "feature_scores": self.feature_scores or {},
            "reasons": self.reasons or [],
            "styled_photo_url": self.styled_photo_url,
            "items": [outfit_item.to_dict() for outfit_item in self.items],
        }


class OutfitItem(db.Model):
    __tablename__ = "outfit_items"

    id = db.Column(db.Integer, primary_key=True)
    outfit_id = db.Column(db.Integer, db.ForeignKey("outfits.id"), nullable=False, index=True)
    clothing_item_id = db.Column(
        db.Integer,
        db.ForeignKey("clothing_items.id"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(50), nullable=False)

    outfit = db.relationship("Outfit", back_populates="items")
    clothing_item = db.relationship("ClothingItem", back_populates="outfit_items")

    def to_dict(self):
        return {
            "id": self.id,
            "outfit_id": self.outfit_id,
            "clothing_item_id": self.clothing_item_id,
            "role": self.role,
            "clothing_item": self.clothing_item.to_dict() if self.clothing_item else None,
        }
```

## backend\app\models\outfit_feedback.py

```python
from ..extensions import db


class OutfitFeedback(db.Model):
    __tablename__ = "outfit_feedback"
    __table_args__ = (
        db.UniqueConstraint("outfit_id", "user_id", name="uq_outfit_feedback_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    outfit_id = db.Column(db.Integer, db.ForeignKey("outfits.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    reaction = db.Column(db.String(20), nullable=False)

    outfit = db.relationship("Outfit", back_populates="feedback_entries")
    user = db.relationship("User", back_populates="outfit_feedback")

    def to_dict(self):
        return {
            "id": self.id,
            "outfit_id": self.outfit_id,
            "user_id": self.user_id,
            "reaction": self.reaction,
        }
```

## backend\app\models\user.py

```python
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=True)

    preferences = db.relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    clothing_items = db.relationship(
        "ClothingItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    outfits = db.relationship(
        "Outfit",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    outfit_feedback = db.relationship(
        "OutfitFeedback",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_preferences=True):
        payload = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "city": self.city,
        }
        if include_preferences:
            payload["preferences"] = (
                self.preferences.to_dict() if self.preferences else None
            )
        return payload
```

## backend\app\models\user_preferences.py

```python
from ..extensions import db


class UserPreferences(db.Model):
    __tablename__ = "user_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    preferred_styles = db.Column(db.JSON, nullable=False, default=list)
    preferred_colors = db.Column(db.JSON, nullable=False, default=list)
    constraints = db.Column(db.JSON, nullable=False, default=list)
    disliked_items = db.Column(db.JSON, nullable=False, default=list)

    user = db.relationship("User", back_populates="preferences")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "preferred_styles": self.preferred_styles or [],
            "preferred_colors": self.preferred_colors or [],
            "constraints": self.constraints or [],
            "disliked_items": self.disliked_items or [],
        }
```

## backend\app\schemas\__init__.py

```python
# Schema helpers for request validation.
```

## backend\app\schemas\auth.py

```python
from ..utils.errors import ApiError


def validate_register_payload(payload):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    name = (payload.get("name") or "").strip()
    city = (payload.get("city") or "").strip() or None

    if not email:
        raise ApiError("Поле email обязательно.", 400)
    if "@" not in email:
        raise ApiError("Некорректный формат email.", 400)
    if len(password) < 6:
        raise ApiError("Пароль должен содержать минимум 6 символов.", 400)
    if not name:
        raise ApiError("Поле имени обязательно.", 400)

    return {
        "email": email,
        "password": password,
        "name": name,
        "city": city,
    }


def validate_login_payload(payload):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        raise ApiError("Нужно указать email и пароль.", 400)

    return {"email": email, "password": password}
```

## backend\app\schemas\item.py

```python
import json

from ..utils.errors import ApiError


ALLOWED_CATEGORIES = {"top", "bottom", "shoes", "outerwear", "accessory"}
ALLOWED_FIT_VALUES = {"fitted", "balanced", "loose", "oversized"}
ALLOWED_LAYER_LEVELS = {"base", "mid", "outer", "support"}


def parse_list_field(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        raw_value = value.strip()
        if not raw_value:
            return []
        if raw_value.startswith("["):
            try:
                parsed = json.loads(raw_value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [chunk.strip() for chunk in raw_value.split(",") if chunk.strip()]
    raise ApiError("Некорректный формат списка.", 400)


def parse_bool_field(value, default=False):
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    normalized_value = str(value).strip().lower()
    if normalized_value in {"true", "1", "yes", "on"}:
        return True
    if normalized_value in {"false", "0", "no", "off"}:
        return False
    raise ApiError("Некорректный формат логического поля.", 400)


def parse_float_field(value, default=0.0):
    if value is None or value == "":
        return float(default)
    try:
        parsed_value = float(value)
    except (TypeError, ValueError) as error:
        raise ApiError("Некорректный формат числового поля.", 400) from error
    return parsed_value


def validate_clothing_item_payload(payload):
    title = (payload.get("title") or "").strip()
    category = (payload.get("category") or "").strip().lower()
    subcategory = (payload.get("subcategory") or "").strip() or None
    season = (payload.get("season") or "all-season").strip().lower()
    formality = (payload.get("formality") or "casual").strip().lower()
    fit = (payload.get("fit") or "").strip().lower() or None
    layer_level = (payload.get("layer_level") or "").strip().lower() or None
    insulation_rating = parse_float_field(payload.get("insulation_rating"), default=0.0)
    waterproof = parse_bool_field(payload.get("waterproof"), default=False)
    windproof = parse_bool_field(payload.get("windproof"), default=False)
    material = (payload.get("material") or "").strip() or None
    image_url = (payload.get("image_url") or "").strip() or None

    if not title:
        raise ApiError("Название вещи обязательно.", 400)
    if category not in ALLOWED_CATEGORIES:
        raise ApiError(
            "Категория должна быть одной из: top, bottom, shoes, outerwear, accessory.",
            400,
        )
    if fit and fit not in ALLOWED_FIT_VALUES:
        raise ApiError(
            "Посадка должна быть одной из: fitted, balanced, loose, oversized.",
            400,
        )
    if layer_level and layer_level not in ALLOWED_LAYER_LEVELS:
        raise ApiError(
            "Слой должен быть одним из: base, mid, outer, support.",
            400,
        )
    if insulation_rating < 0 or insulation_rating > 5:
        raise ApiError("Уровень утепления должен быть в диапазоне от 0 до 5.", 400)

    return {
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "colors": parse_list_field(payload.get("colors")),
        "styles": parse_list_field(payload.get("styles")),
        "season": season or "all-season",
        "formality": formality or "casual",
        "fit": fit,
        "layer_level": layer_level,
        "insulation_rating": insulation_rating,
        "waterproof": waterproof,
        "windproof": windproof,
        "material": material,
        "image_url": image_url,
    }
```

## backend\app\schemas\outfit.py

```python
from ..utils.errors import ApiError
from .item import parse_list_field


def validate_generate_payload(payload):
    event_type = (payload.get("event_type") or "").strip().lower()
    preferred_style = (payload.get("preferred_style") or "").strip().lower() or None
    weather_condition = (
        (payload.get("weather_condition") or "").strip().lower() or None
    )
    constraints = parse_list_field(payload.get("constraints"))
    preferred_colors = parse_list_field(payload.get("preferred_colors"))

    if not event_type:
        raise ApiError("Поле event_type обязательно.", 400)

    temperature = payload.get("temperature")
    if temperature not in (None, ""):
        try:
            temperature = float(temperature)
        except (TypeError, ValueError) as error:
            raise ApiError("Поле temperature должно быть числом.", 400) from error
    else:
        temperature = None

    anchor_item_id = payload.get("anchor_item_id")
    if anchor_item_id not in (None, ""):
        try:
            anchor_item_id = int(anchor_item_id)
        except (TypeError, ValueError) as error:
            raise ApiError("Поле anchor_item_id должно быть целым числом.", 400) from error
    else:
        anchor_item_id = None

    return {
        "event_type": event_type,
        "preferred_colors": preferred_colors,
        "preferred_style": preferred_style,
        "temperature": temperature,
        "weather_condition": weather_condition,
        "anchor_item_id": anchor_item_id,
        "constraints": constraints,
    }


def validate_save_outfit_payload(payload):
    event_type = (payload.get("event_type") or "").strip().lower()
    name = (payload.get("name") or "").strip() or "Сохраненный образ"
    explanation = (payload.get("explanation") or "").strip() or None
    weather_context = payload.get("weather_context") or {}
    feature_scores = payload.get("feature_scores") or {}
    reasons = payload.get("reasons") or []
    styled_photo_url = (payload.get("styled_photo_url") or "").strip() or None
    item_entries = payload.get("items") or []

    if not event_type:
        raise ApiError("Поле event_type обязательно.", 400)
    if not isinstance(item_entries, list) or not item_entries:
        raise ApiError("Поле items должно содержать непустой список.", 400)

    cleaned_items = []
    for item in item_entries:
        clothing_item_id = item.get("clothing_item_id")
        role = (item.get("role") or "").strip().lower()
        if clothing_item_id is None or not role:
            raise ApiError(
                "Каждая вещь в сохраненном образе должна содержать id и role.",
                400,
            )
        try:
            clothing_item_id = int(clothing_item_id)
        except (TypeError, ValueError) as error:
            raise ApiError(
                "Поле clothing_item_id должно быть целым числом.",
                400,
            ) from error
        cleaned_items.append({"clothing_item_id": clothing_item_id, "role": role})

    score = payload.get("score", 0)
    try:
        score = float(score)
    except (TypeError, ValueError) as error:
        raise ApiError("Поле score должно быть числом.", 400) from error

    if not isinstance(weather_context, dict):
        raise ApiError("Поле weather_context должно быть объектом.", 400)
    if not isinstance(feature_scores, dict):
        raise ApiError("Поле feature_scores должно быть объектом.", 400)
    if not isinstance(reasons, list):
        raise ApiError("Поле reasons должно быть списком.", 400)

    cleaned_reasons = [str(reason).strip() for reason in reasons if str(reason).strip()]

    return {
        "name": name,
        "event_type": event_type,
        "weather_context": weather_context,
        "score": score,
        "explanation": explanation,
        "feature_scores": feature_scores,
        "reasons": cleaned_reasons,
        "styled_photo_url": styled_photo_url,
        "items": cleaned_items,
    }


def validate_feedback_payload(payload):
    reaction = (payload.get("reaction") or "").strip().lower()
    if reaction not in {"like", "dislike", "save"}:
        raise ApiError("Поле reaction должно быть одним из: like, dislike, save.", 400)
    return {"reaction": reaction}
```

## backend\app\services\__init__.py

```python
# Service layer package.
```

## backend\app\services\analytics_service.py

```python
from collections import Counter


class WardrobeAnalyticsService:
    @staticmethod
    def build_summary(items):
        category_counts = Counter()
        season_counts = Counter()
        style_counts = Counter()

        for item in items:
            category_counts[item.category] += 1
            season_counts[item.season] += 1
            for style in item.styles or []:
                style_counts[style] += 1

        return {
            "total_items": len(items),
            "by_category": dict(category_counts),
            "by_season": dict(season_counts),
            "by_style": dict(style_counts),
            "recommendations": WardrobeAnalyticsService.build_recommendations(
                len(items),
                category_counts,
                season_counts,
                style_counts,
            ),
        }

    @staticmethod
    def build_recommendations(total_items, category_counts, season_counts, style_counts):
        recommendations = []

        if category_counts.get("shoes", 0) < 2:
            recommendations.append("У вас мало обуви.")
        if category_counts.get("outerwear", 0) < 1:
            recommendations.append("В гардеробе мало верхней одежды.")
        if total_items and max(season_counts.values(), default=0) / total_items >= 0.6:
            recommendations.append(
                "Большинство вещей относится к одному сезону. Гардероб стоит сбалансировать."
            )

        basic_style_count = style_counts.get("basic", 0) + style_counts.get("casual", 0)
        if basic_style_count < 3:
            recommendations.append("Недостаточно универсальных базовых вещей.")

        if category_counts.get("top", 0) < 2 or category_counts.get("bottom", 0) < 2:
            recommendations.append("Добавьте больше верха или низа для новых сочетаний.")

        if not recommendations:
            recommendations.append("Состав гардероба выглядит достаточно сбалансированным.")

        return recommendations
```

## backend\app\services\demo_wardrobe_seed.py

```python
from ..extensions import db
from ..models import ClothingItem, UserPreferences


PEXELS_PHOTO_IDS = {
    "white_tshirt": "18186106",
    "black_tshirt": "8486692",
    "beige_tshirt": "6786618",
    "blue_shirt": "19189134",
    "white_polo": "8730572",
    "green_shirt": "8727445",
    "white_blouse": "8058727",
    "pink_blouse": "20107165",
    "brown_sweater": "11505332",
    "gray_sweater": "3754685",
    "blue_hoodie": "19602188",
    "beige_turtleneck": "8062965",
    "black_turtleneck": "6580564",
    "beige_cardigan": "8797760",
    "black_jeans": "2448535",
    "blue_jeans": "1082529",
    "beige_trousers": "11927534",
    "black_midi_skirt": "7391123",
    "white_shorts": "8746743",
    "gray_joggers": "10378467",
    "black_leggings": "4534648",
    "beige_skirt": "6445991",
    "black_skirt_alt": "18490258",
    "white_sneakers": "4252969",
    "black_boots": "2929281",
    "beige_loafers": "27141835",
    "winter_boots": "6608415",
    "brown_boots": "9929610",
    "white_sandals": "26954370",
    "black_flip_flops": "14934603",
    "black_pumps": "8134242",
    "black_ankle_boots": "27204301",
    "black_heeled_sandals": "7383130",
    "black_coat": "18794485",
    "beige_jacket": "14694444",
    "gray_blazer": "7653837",
    "beige_trench": "21838449",
    "windbreaker": "6778713",
    "puffer_jacket": "19426409",
    "black_blazer": "12809816",
    "olive_jacket": "13260209",
    "leather_jacket": "4750189",
    "black_bag": "6167276",
    "beige_scarf": "8121914",
    "brown_belt": "20777832",
    "white_cap": "13359665",
    "silver_jewelry": "23859401",
    "brown_backpack": "11578809",
    "beige_gloves": "9413652",
    "gold_jewelry": "8626814",
}
FIT_BY_SUBCATEGORY = {
    "t_shirt": "balanced",
    "shirt": "fitted",
    "blouse": "fitted",
    "polo": "balanced",
    "longsleeve": "balanced",
    "sweater": "loose",
    "hoodie": "oversized",
    "cardigan": "loose",
    "turtleneck": "fitted",
    "sweatshirt": "loose",
    "vest": "balanced",
    "crop_top": "fitted",
    "jeans": "balanced",
    "trousers": "fitted",
    "chinos": "balanced",
    "joggers": "loose",
    "leggings": "fitted",
    "culottes": "loose",
    "skirt": "balanced",
    "mini_skirt": "fitted",
    "midi_skirt": "balanced",
    "maxi_skirt": "loose",
    "shorts": "balanced",
    "winter_boots": "balanced",
    "felt_boots": "balanced",
    "warm_boots": "balanced",
    "demi_boots": "balanced",
    "ankle_boots": "fitted",
    "boots": "balanced",
    "closed_shoes": "fitted",
    "pumps": "fitted",
    "loafers": "fitted",
    "sneakers": "balanced",
    "summer_sneakers": "balanced",
    "sandals": "fitted",
    "espadrilles": "balanced",
    "flip_flops": "loose",
    "coat": "balanced",
    "jacket": "balanced",
    "parka": "oversized",
    "down_jacket": "oversized",
    "trench": "balanced",
    "blazer": "fitted",
    "leather_jacket": "balanced",
    "windbreaker": "loose",
    "vest_outerwear": "balanced",
    "bag": "balanced",
    "backpack": "balanced",
    "scarf": "loose",
    "hat": "balanced",
    "cap": "balanced",
    "gloves": "fitted",
    "belt": "fitted",
    "jewelry": "fitted",
}
LAYER_BY_SUBCATEGORY = {
    "t_shirt": "base",
    "shirt": "base",
    "blouse": "base",
    "polo": "base",
    "longsleeve": "base",
    "crop_top": "base",
    "turtleneck": "base",
    "sweater": "mid",
    "hoodie": "mid",
    "cardigan": "mid",
    "sweatshirt": "mid",
    "vest": "mid",
    "coat": "outer",
    "jacket": "outer",
    "parka": "outer",
    "down_jacket": "outer",
    "trench": "outer",
    "blazer": "outer",
    "leather_jacket": "outer",
    "windbreaker": "outer",
    "vest_outerwear": "outer",
    "bag": "support",
    "backpack": "support",
    "scarf": "support",
    "hat": "support",
    "cap": "support",
    "gloves": "support",
    "belt": "support",
    "jewelry": "support",
}
INSULATION_BY_SUBCATEGORY = {
    "t_shirt": 0.6,
    "shirt": 0.8,
    "blouse": 0.7,
    "polo": 0.7,
    "longsleeve": 1.0,
    "crop_top": 0.3,
    "sweater": 1.8,
    "hoodie": 1.7,
    "cardigan": 1.4,
    "turtleneck": 1.5,
    "sweatshirt": 1.5,
    "vest": 1.1,
    "jeans": 1.4,
    "trousers": 1.2,
    "chinos": 1.1,
    "joggers": 1.4,
    "leggings": 1.0,
    "culottes": 0.9,
    "skirt": 0.8,
    "mini_skirt": 0.5,
    "midi_skirt": 0.8,
    "maxi_skirt": 0.9,
    "shorts": 0.3,
    "winter_boots": 2.0,
    "felt_boots": 2.2,
    "warm_boots": 1.9,
    "demi_boots": 1.5,
    "ankle_boots": 1.4,
    "boots": 1.3,
    "closed_shoes": 1.0,
    "pumps": 0.8,
    "loafers": 0.8,
    "sneakers": 0.9,
    "summer_sneakers": 0.6,
    "sandals": 0.2,
    "espadrilles": 0.3,
    "flip_flops": 0.1,
    "coat": 2.4,
    "jacket": 1.7,
    "parka": 2.6,
    "down_jacket": 2.8,
    "trench": 1.5,
    "blazer": 1.2,
    "leather_jacket": 1.6,
    "windbreaker": 1.2,
    "vest_outerwear": 1.2,
    "scarf": 0.5,
    "hat": 0.4,
    "gloves": 0.4,
}
WATERPROOF_SUBCATEGORIES = {"trench", "parka", "down_jacket", "windbreaker", "jacket"}
WINDPROOF_SUBCATEGORIES = {"coat", "parka", "down_jacket", "windbreaker", "leather_jacket"}
WATER_RESISTANT_MATERIALS = {"leather", "nylon", "polyester", "rubber"}


def build_demo_preferences():
    return {
        "preferred_styles": ["minimal", "classic", "casual", "business"],
        "preferred_colors": ["white", "black", "beige", "gray", "cream", "navy", "olive"],
        "constraints": [],
        "disliked_items": [],
    }


def build_demo_wardrobe_items():
    return [
        _item("Белая футболка", "top", "t_shirt", ["white"], ["basic", "minimal"], "all-season", "casual", "cotton", "white_tshirt"),
        _item("Черная футболка", "top", "t_shirt", ["black"], ["casual", "basic"], "all-season", "casual", "cotton", "black_tshirt"),
        _item("Бежевая футболка", "top", "t_shirt", ["beige"], ["minimal", "basic"], "all-season", "casual", "cotton", "beige_tshirt"),
        _item("Голубая рубашка", "top", "shirt", ["blue"], ["classic", "business"], "spring", "smart", "cotton", "blue_shirt"),
        _item("Белое поло", "top", "polo", ["white"], ["classic", "casual"], "all-season", "smart", "cotton", "white_polo"),
        _item("Зеленая рубашка", "top", "shirt", ["green"], ["casual", "minimal"], "spring", "casual", "cotton", "green_shirt"),
        _item("Белая блузка", "top", "blouse", ["white"], ["romantic", "evening"], "summer", "smart", "viscose", "white_blouse"),
        _item("Розовая блузка", "top", "blouse", ["pink"], ["romantic", "fashion"], "summer", "smart", "viscose", "pink_blouse"),
        _item("Коричневый свитер", "top", "sweater", ["brown"], ["minimal", "casual"], "autumn", "smart", "knit", "brown_sweater"),
        _item("Серый свитер", "top", "sweater", ["gray"], ["minimal", "classic"], "winter", "smart", "knit", "gray_sweater"),
        _item("Синее худи", "top", "hoodie", ["blue"], ["street", "sport"], "autumn", "casual", "cotton", "blue_hoodie"),
        _item("Бежевый гольф", "top", "turtleneck", ["beige"], ["minimal", "classic"], "autumn", "smart", "knit", "beige_turtleneck"),
        _item("Черная водолазка", "top", "turtleneck", ["black"], ["minimal", "classic"], "autumn", "smart", "knit", "black_turtleneck"),
        _item("Бежевый кардиган", "top", "cardigan", ["beige"], ["classic", "minimal"], "autumn", "casual", "knit", "beige_cardigan"),

        _item("Черные джинсы", "bottom", "jeans", ["black"], ["street", "casual"], "all-season", "casual", "denim", "black_jeans"),
        _item("Синие джинсы", "bottom", "jeans", ["blue"], ["basic", "casual"], "all-season", "casual", "denim", "blue_jeans"),
        _item("Бежевые брюки", "bottom", "trousers", ["beige"], ["minimal", "classic"], "spring", "smart", "cotton", "beige_trousers"),
        _item("Черная юбка-миди", "bottom", "midi_skirt", ["black"], ["classic", "fashion"], "autumn", "smart", "cotton", "black_midi_skirt"),
        _item("Белые шорты", "bottom", "shorts", ["white"], ["minimal", "casual"], "summer", "casual", "viscose", "white_shorts"),
        _item("Серые джоггеры", "bottom", "joggers", ["gray"], ["sport", "street"], "all-season", "casual", "cotton", "gray_joggers"),
        _item("Черные леггинсы", "bottom", "leggings", ["black"], ["sport", "minimal"], "all-season", "casual", "jersey", "black_leggings"),
        _item("Бежевая юбка-миди", "bottom", "midi_skirt", ["beige"], ["romantic", "minimal"], "summer", "smart", "linen", "beige_skirt"),
        _item("Черная юбка-карандаш", "bottom", "skirt", ["black"], ["classic", "evening"], "all-season", "formal", "cotton", "black_skirt_alt"),

        _item("Белые кроссовки", "shoes", "sneakers", ["white"], ["casual", "sport"], "spring", "casual", "textile", "white_sneakers"),
        _item("Черные ботинки", "shoes", "boots", ["black"], ["classic", "casual"], "autumn", "smart", "leather", "black_boots"),
        _item("Бежевые лоферы", "shoes", "loafers", ["beige"], ["classic", "minimal"], "spring", "smart", "leather", "beige_loafers"),
        _item("Черные зимние сапоги", "shoes", "winter_boots", ["black"], ["casual"], "winter", "casual", "leather", "winter_boots"),
        _item("Коричневые демисезонные ботинки", "shoes", "demi_boots", ["brown"], ["classic", "casual"], "autumn", "smart", "leather", "brown_boots"),
        _item("Белые босоножки", "shoes", "sandals", ["white"], ["minimal", "romantic"], "summer", "smart", "leather", "white_sandals"),
        _item("Черные шлепки", "shoes", "flip_flops", ["black"], ["casual", "minimal"], "summer", "casual", "rubber", "black_flip_flops"),
        _item("Черные лодочки", "shoes", "pumps", ["black"], ["classic", "evening"], "all-season", "formal", "leather", "black_pumps"),
        _item("Черные ботильоны", "shoes", "ankle_boots", ["black"], ["classic", "evening"], "autumn", "smart", "leather", "black_ankle_boots"),
        _item("Черные босоножки на каблуке", "shoes", "sandals", ["black"], ["evening", "fashion"], "summer", "formal", "leather", "black_heeled_sandals"),

        _item("Черное пальто", "outerwear", "coat", ["black"], ["classic", "minimal"], "autumn", "formal", "wool", "black_coat"),
        _item("Бежевая куртка", "outerwear", "jacket", ["beige"], ["casual", "minimal"], "autumn", "casual", "cotton", "beige_jacket"),
        _item("Серый пиджак", "outerwear", "blazer", ["gray"], ["business", "classic"], "all-season", "smart", "wool", "gray_blazer"),
        _item("Светлый тренч", "outerwear", "trench", ["beige"], ["classic", "minimal"], "spring", "smart", "cotton", "beige_trench"),
        _item("Темная ветровка", "outerwear", "windbreaker", ["gray"], ["sport", "casual"], "autumn", "casual", "nylon", "windbreaker"),
        _item("Черный пуховик", "outerwear", "down_jacket", ["black"], ["casual"], "winter", "casual", "nylon", "puffer_jacket"),
        _item("Черный жакет", "outerwear", "blazer", ["black"], ["business", "classic"], "all-season", "formal", "wool", "black_blazer"),
        _item("Оливковая куртка", "outerwear", "jacket", ["olive"], ["casual", "street"], "autumn", "casual", "cotton", "olive_jacket"),
        _item("Черная кожаная куртка", "outerwear", "leather_jacket", ["black"], ["street", "evening"], "autumn", "smart", "leather", "leather_jacket"),

        _item("Черная сумка", "accessory", "bag", ["black"], ["minimal", "classic"], "all-season", "smart", "leather", "black_bag"),
        _item("Бежевый шарф", "accessory", "scarf", ["beige"], ["classic", "minimal"], "autumn", "casual", "cotton", "beige_scarf"),
        _item("Коричневый ремень", "accessory", "belt", ["brown"], ["classic", "business"], "all-season", "smart", "leather", "brown_belt"),
        _item("Белая кепка", "accessory", "cap", ["white"], ["sport", "casual"], "summer", "casual", "cotton", "white_cap"),
        _item("Серебристое украшение", "accessory", "jewelry", ["silver"], ["evening", "minimal"], "all-season", "formal", "metal", "silver_jewelry"),
        _item("Коричневый рюкзак", "accessory", "backpack", ["brown"], ["casual", "travel"], "all-season", "casual", "leather", "brown_backpack"),
        _item("Бежевые перчатки", "accessory", "gloves", ["beige"], ["classic", "minimal"], "winter", "casual", "knit", "beige_gloves"),
        _item("Золотое украшение", "accessory", "jewelry", ["gold"], ["evening", "classic"], "all-season", "formal", "metal", "gold_jewelry"),
    ]


def get_demo_wardrobe_item_count():
    return len(build_demo_wardrobe_items())


def seed_demo_wardrobe_for_user(user, replace_existing=True):
    if replace_existing:
        for feedback in list(user.outfit_feedback):
            db.session.delete(feedback)
        for outfit in list(user.outfits):
            db.session.delete(outfit)
        for item in list(user.clothing_items):
            db.session.delete(item)
        db.session.flush()

    preferences = build_demo_preferences()
    if user.preferences is None:
        user.preferences = UserPreferences(user_id=user.id, **preferences)
    else:
        user.preferences.preferred_styles = preferences["preferred_styles"]
        user.preferences.preferred_colors = preferences["preferred_colors"]
        user.preferences.constraints = preferences["constraints"]
        user.preferences.disliked_items = preferences["disliked_items"]

    for item_data in build_demo_wardrobe_items():
        db.session.add(ClothingItem(user_id=user.id, **item_data))

    db.session.commit()


def _item(title, category, subcategory, colors, styles, season, formality, material, image_key):
    return {
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "colors": colors,
        "styles": styles,
        "season": season,
        "formality": formality,
        "fit": FIT_BY_SUBCATEGORY.get(subcategory, "balanced"),
        "layer_level": LAYER_BY_SUBCATEGORY.get(subcategory),
        "insulation_rating": INSULATION_BY_SUBCATEGORY.get(subcategory, 0.6),
        "waterproof": subcategory in WATERPROOF_SUBCATEGORIES or material in WATER_RESISTANT_MATERIALS,
        "windproof": subcategory in WINDPROOF_SUBCATEGORIES,
        "material": material,
        "image_url": _pexels_image(image_key),
    }


def _pexels_image(image_key):
    photo_id = PEXELS_PHOTO_IDS[image_key]
    return f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=1200"
```

## backend\app\services\recommendation_engine.py

```python
from collections import Counter
from itertools import combinations, product


FEATURE_WEIGHTS = {
    "color_harmony": 0.15,
    "style_match": 0.15,
    "event_match": 0.15,
    "season_match": 0.1,
    "temperature_match": 0.1,
    "weather_condition_match": 0.1,
    "layering_correctness": 0.08,
    "completeness": 0.06,
    "user_preference_match": 0.06,
    "constraints_match": 0.05,
}

ROLE_ORDER = {
    "top": 0,
    "bottom": 1,
    "shoes": 2,
    "outerwear": 3,
    "accessory": 4,
}

BRIGHT_COLORS = {"red", "yellow", "orange", "lime", "fuchsia", "pink"}
COLOR_ALIASES = {
    "black": "black",
    "white": "white",
    "off_white": "white",
    "gray": "gray",
    "grey": "gray",
    "charcoal": "gray",
    "graphite": "gray",
    "beige": "beige",
    "cream": "cream",
    "ivory": "cream",
    "sand": "beige",
    "nude": "beige",
    "taupe": "taupe",
    "brown": "brown",
    "camel": "camel",
    "tan": "camel",
    "chocolate": "brown",
    "mocha": "brown",
    "red": "red",
    "burgundy": "burgundy",
    "wine": "burgundy",
    "maroon": "burgundy",
    "orange": "orange",
    "coral": "coral",
    "peach": "coral",
    "terracotta": "terracotta",
    "yellow": "yellow",
    "mustard": "mustard",
    "green": "green",
    "olive": "olive",
    "khaki": "khaki",
    "mint": "mint",
    "emerald": "green",
    "forest": "green",
    "teal": "teal",
    "turquoise": "turquoise",
    "aqua": "turquoise",
    "blue": "blue",
    "sky": "blue",
    "sky_blue": "blue",
    "cobalt": "blue",
    "navy": "navy",
    "navy_blue": "navy",
    "denim": "denim",
    "indigo": "denim",
    "purple": "purple",
    "lilac": "purple",
    "lavender": "lavender",
    "violet": "purple",
    "plum": "purple",
    "pink": "pink",
    "blush": "pink",
    "rose": "pink",
    "fuchsia": "pink",
    "gold": "gold",
    "silver": "silver",
    "bronze": "bronze",
}
COLOR_FAMILY_MAP = {
    "black": "black",
    "white": "white",
    "gray": "gray",
    "beige": "beige",
    "cream": "beige",
    "taupe": "brown",
    "brown": "brown",
    "camel": "brown",
    "red": "red",
    "burgundy": "red",
    "orange": "orange",
    "coral": "orange",
    "terracotta": "orange",
    "yellow": "yellow",
    "mustard": "yellow",
    "green": "green",
    "olive": "green",
    "khaki": "green",
    "mint": "green",
    "teal": "teal",
    "turquoise": "teal",
    "blue": "blue",
    "navy": "blue",
    "denim": "blue",
    "purple": "purple",
    "lavender": "purple",
    "pink": "pink",
    "gold": "metallic",
    "silver": "metallic",
    "bronze": "metallic",
    "unknown": "unknown",
}
NEUTRAL_COLOR_TOKENS = {
    "black",
    "white",
    "gray",
    "navy",
    "beige",
    "brown",
    "cream",
    "taupe",
    "khaki",
    "denim",
}
METALLIC_COLOR_TOKENS = {"gold", "silver", "bronze"}
ANALOGOUS_FAMILY_PAIRS = {
    frozenset({"red", "orange"}),
    frozenset({"orange", "yellow"}),
    frozenset({"yellow", "green"}),
    frozenset({"green", "teal"}),
    frozenset({"teal", "blue"}),
    frozenset({"blue", "purple"}),
    frozenset({"purple", "pink"}),
    frozenset({"pink", "red"}),
}
COMPLEMENTARY_FAMILY_PAIRS = {
    frozenset({"blue", "orange"}),
    frozenset({"red", "green"}),
    frozenset({"yellow", "purple"}),
    frozenset({"teal", "orange"}),
}
ROLE_COLOR_WEIGHTS = {
    "outerwear": 3.1,
    "top": 3.0,
    "bottom": 2.6,
    "shoes": 1.2,
    "accessory": 0.8,
    "item": 2.0,
}
COLOR_SHARE_WEIGHTS = (0.7, 0.2, 0.1)
MAX_PRIMARY_POOL = 12
MAX_OUTERWEAR_POOL = 6
MAX_ACCESSORY_POOL = 3
EVENT_LABELS = {
    "office": "офис",
    "casual": "повседневный выход",
    "evening": "вечерний выход",
    "sport": "спорт",
    "party": "вечеринка",
    "travel": "поездка",
    "date": "свидание",
}
WINTER_SHOE_TYPES = {"winter_boots", "felt_boots", "warm_boots", "snow_boots"}
COLD_SHOE_TYPES = WINTER_SHOE_TYPES | {
    "demi_boots",
    "ankle_boots",
    "boots",
    "closed_shoes",
}
MID_SHOE_TYPES = {
    "demi_boots",
    "ankle_boots",
    "boots",
    "closed_shoes",
    "sneakers",
    "loafers",
    "pumps",
    "summer_sneakers",
}
HOT_SHOE_TYPES = {
    "sandals",
    "flip_flops",
    "slippers",
    "summer_sneakers",
    "espadrilles",
    "loafers",
    "sneakers",
}
OPEN_SHOE_TYPES = {"sandals", "flip_flops", "slippers", "espadrilles"}
RAIN_SAFE_SHOE_TYPES = COLD_SHOE_TYPES | {"sneakers", "summer_sneakers"}
SNOW_SAFE_SHOE_TYPES = WINTER_SHOE_TYPES | {"demi_boots", "ankle_boots", "boots"}
WARM_TOP_TYPES = {"sweater", "hoodie", "cardigan", "turtleneck", "sweatshirt"}
LIGHT_TOP_TYPES = {"t_shirt", "shirt", "blouse", "crop_top", "polo"}
WARM_BOTTOM_TYPES = {"jeans", "trousers", "joggers", "leggings", "culottes"}
LIGHT_BOTTOM_TYPES = {"shorts", "mini_skirt"}
HEAVY_OUTERWEAR_TYPES = {"coat", "parka", "down_jacket"}
LIGHT_OUTERWEAR_TYPES = {
    "jacket",
    "trench",
    "blazer",
    "leather_jacket",
    "windbreaker",
    "vest_outerwear",
}

EVENT_RULES = {
    "casual": {
        "styles": {"casual", "basic", "minimal", "street"},
        "formalities": {"casual", "smart"},
    },
    "office": {
        "styles": {"classic", "business", "minimal"},
        "formalities": {"smart", "formal"},
    },
    "evening": {
        "styles": {"evening", "classic", "fashion", "party"},
        "formalities": {"smart", "formal"},
    },
    "sport": {
        "styles": {"sport", "athleisure", "casual"},
        "formalities": {"casual"},
    },
    "party": {
        "styles": {"party", "fashion", "statement"},
        "formalities": {"smart", "formal"},
    },
    "travel": {
        "styles": {"casual", "sport", "street"},
        "formalities": {"casual", "smart"},
    },
    "date": {
        "styles": {"minimal", "classic", "romantic"},
        "formalities": {"smart", "formal"},
    },
}

STYLE_FAMILY_MAP = {
    "basic": "minimal",
    "minimal": "minimal",
    "classic": "classic",
    "business": "classic",
    "formal": "classic",
    "casual": "casual",
    "street": "casual",
    "sport": "sport",
    "athleisure": "sport",
    "romantic": "romantic",
    "evening": "evening",
    "party": "evening",
    "fashion": "fashion",
    "statement": "fashion",
}
STYLE_COMPATIBILITY_PAIRS = {
    frozenset({"minimal", "classic"}),
    frozenset({"minimal", "casual"}),
    frozenset({"classic", "romantic"}),
    frozenset({"classic", "fashion"}),
    frozenset({"casual", "sport"}),
    frozenset({"casual", "fashion"}),
    frozenset({"casual", "romantic"}),
    frozenset({"evening", "fashion"}),
    frozenset({"classic", "evening"}),
}
SUBCATEGORY_LAYER_LEVELS = {
    "t_shirt": "base",
    "shirt": "base",
    "blouse": "base",
    "crop_top": "base",
    "polo": "base",
    "longsleeve": "base",
    "tank_top": "base",
    "sweater": "mid",
    "hoodie": "mid",
    "cardigan": "mid",
    "turtleneck": "mid",
    "sweatshirt": "mid",
    "vest_top": "mid",
    "coat": "outer",
    "parka": "outer",
    "down_jacket": "outer",
    "jacket": "outer",
    "trench": "outer",
    "blazer": "outer",
    "leather_jacket": "outer",
    "windbreaker": "outer",
    "vest_outerwear": "outer",
}
WATERPROOF_OUTERWEAR_TYPES = {"trench", "parka", "down_jacket", "windbreaker", "jacket"}
WINDPROOF_OUTERWEAR_TYPES = {"coat", "parka", "down_jacket", "windbreaker", "leather_jacket"}
WATER_RESISTANT_MATERIALS = {"leather", "nylon", "polyester", "gabardine"}
TEXTURE_ALIAS_MAP = {
    "cotton": "soft_woven",
    "linen": "soft_woven",
    "silk": "fluid",
    "viscose": "fluid",
    "wool": "knit",
    "cashmere": "knit",
    "knit": "knit",
    "jersey": "knit",
    "denim": "structured",
    "leather": "structured",
    "suede": "structured",
    "tweed": "structured",
}
SUBCATEGORY_TEXTURE_MAP = {
    "jeans": "structured",
    "coat": "structured",
    "blazer": "structured",
    "leather_jacket": "structured",
    "trench": "structured",
    "sweater": "knit",
    "cardigan": "knit",
    "hoodie": "knit",
    "turtleneck": "knit",
    "shirt": "soft_woven",
    "blouse": "fluid",
    "dress_shirt": "soft_woven",
}
FITTED_SUBCATEGORIES = {
    "shirt",
    "blouse",
    "turtleneck",
    "blazer",
    "trousers",
    "pumps",
    "loafers",
    "closed_shoes",
}
RELAXED_SUBCATEGORIES = {
    "t_shirt",
    "sweater",
    "hoodie",
    "cardigan",
    "coat",
    "parka",
    "jacket",
    "jeans",
    "joggers",
    "sneakers",
}
EVENT_DISALLOWED_STYLES = {
    "office": {"sport"},
    "evening": {"sport"},
    "party": {"sport"},
}
EVENT_DISALLOWED_SUBCATEGORIES = {
    "office": {"flip_flops", "slippers", "felt_boots", "shorts", "hoodie"},
    "evening": {"flip_flops", "slippers", "felt_boots", "joggers", "hoodie"},
    "party": {"felt_boots", "snow_boots", "flip_flops"},
    "sport": {"blazer", "coat", "pumps", "loafers"},
}


class RecommendationEngine:
    def __init__(self, weights=None):
        self.weights = {**FEATURE_WEIGHTS, **(weights or {})}

    def generate(self, clothing_items, request_context, user_preferences=None, limit=5):
        candidates = self.generate_candidate_outfits(clothing_items, request_context)
        ranked_outfits = [
            self.evaluate_outfit(candidate, request_context, user_preferences or {})
            for candidate in candidates
        ]
        ranked_outfits.sort(key=lambda outfit: outfit["score"], reverse=True)

        top_outfits = ranked_outfits[:limit]
        for index, outfit in enumerate(top_outfits, start=1):
            event_type = request_context.get("event_type", "casual")
            outfit["name"] = self.build_outfit_name(event_type, index)

        return top_outfits

    def build_outfit_name(self, event_type, index):
        event_label = EVENT_LABELS.get(self._normalize_token(event_type), "базовый")
        return f"Образ: {event_label} #{index}"

    def generate_candidate_outfits(self, clothing_items, request_context):
        categorized_items = self._categorize_items(clothing_items)
        anchor_item = self._find_anchor_item(
            clothing_items,
            request_context.get("anchor_item_id"),
        )
        if request_context.get("anchor_item_id") and anchor_item is None:
            return []

        tops = self._build_pool(categorized_items["top"], anchor_item, "top")
        bottoms = self._build_pool(categorized_items["bottom"], anchor_item, "bottom")
        shoes = self._build_pool(categorized_items["shoes"], anchor_item, "shoes")
        outerwear = self._build_pool(
            categorized_items["outerwear"],
            anchor_item,
            "outerwear",
            allow_empty=True,
        )
        accessories = self._build_pool(
            categorized_items["accessory"],
            anchor_item,
            "accessory",
            allow_empty=True,
        )

        if not tops or not bottoms or not shoes:
            return []

        constraints = self._normalize_tokens(request_context.get("constraints"))
        candidates = []
        if anchor_item and anchor_item.category == "accessory":
            accessory_pool = [anchor_item]
        else:
            accessory_pool = [item for item in accessories[:MAX_ACCESSORY_POOL] if item is not None]
            accessory_pool = [None] + accessory_pool if accessory_pool else [None]

        for top_item, bottom_item, shoes_item in product(
            tops[:MAX_PRIMARY_POOL],
            bottoms[:MAX_PRIMARY_POOL],
            shoes[:MAX_PRIMARY_POOL],
        ):
            base_candidate = [
                self._make_candidate_entry("top", top_item),
                self._make_candidate_entry("bottom", bottom_item),
                self._make_candidate_entry("shoes", shoes_item),
            ]
            for accessory_item in accessory_pool:
                candidate_with_accessory = list(base_candidate)
                if accessory_item is not None:
                    candidate_with_accessory.append(
                        self._make_candidate_entry("accessory", accessory_item)
                    )

                if (
                    (not anchor_item or anchor_item.category != "outerwear")
                    and self._is_valid_candidate(
                    candidate_with_accessory,
                    constraints,
                    request_context,
                    )
                ):
                    candidates.append(candidate_with_accessory)

                for outerwear_item in outerwear[:MAX_OUTERWEAR_POOL]:
                    if outerwear_item is None:
                        continue
                    layered_candidate = list(candidate_with_accessory) + [
                        self._make_candidate_entry("outerwear", outerwear_item)
                    ]
                    if self._is_valid_candidate(
                        layered_candidate,
                        constraints,
                        request_context,
                    ):
                        candidates.append(layered_candidate)

        return self._deduplicate_candidates(candidates)

    def evaluate_outfit(self, candidate, request_context, user_preferences=None):
        color_detail = self._evaluate_color_harmony(candidate, request_context)
        contextual_weights = self._get_contextual_weights(request_context)
        feature_scores = self.get_feature_scores(
            candidate,
            request_context,
            user_preferences or {},
            color_detail=color_detail,
        )
        total_score = self.calculate_total_score(feature_scores, contextual_weights)
        reasons, explanation = self.build_outfit_explanation(
            feature_scores,
            request_context,
            feature_details={"color_harmony": color_detail},
        )

        items = [
            self._serialize_candidate_item(entry)
            for entry in sorted(candidate, key=lambda entry: ROLE_ORDER[entry["role"]])
        ]

        return {
            "name": "",
            "event_type": request_context.get("event_type"),
            "weather_context": {
                "temperature": request_context.get("temperature"),
                "weather_condition": request_context.get("weather_condition"),
                "season": request_context.get("season"),
                "city": request_context.get("city"),
            },
            "items": items,
            "score": total_score,
            "total_score": total_score,
            "feature_scores": feature_scores,
            "scores_by_feature": feature_scores,
            "applied_weights": contextual_weights,
            "reasons": reasons,
            "explanation": explanation,
        }

    def get_feature_scores(
        self,
        candidate,
        request_context,
        user_preferences=None,
        color_detail=None,
    ):
        items = [entry["item"] for entry in candidate]
        user_preferences = user_preferences or {}
        color_detail = color_detail or self._evaluate_color_harmony(
            candidate,
            request_context,
        )

        return {
            "color_harmony": color_detail["score"],
            "style_match": self.score_style_match(items, request_context),
            "event_match": self.score_event_match(items, request_context),
            "season_match": self.score_season_match(items, request_context),
            "temperature_match": self.score_temperature_match(candidate, request_context),
            "weather_condition_match": self.score_weather_condition_match(
                candidate,
                request_context,
            ),
            "completeness": self.score_completeness(candidate, request_context),
            "layering_correctness": self.score_layering_correctness(
                candidate,
                request_context,
            ),
            "user_preference_match": self.score_user_preference_match(
                candidate,
                request_context,
                user_preferences,
            ),
            "constraints_match": self.score_constraints_match(
                candidate,
                request_context,
                user_preferences,
            ),
        }

    def calculate_total_score(self, feature_scores, weights=None):
        active_weights = weights or self.weights
        total_score = 0.0
        for feature_name, weight in active_weights.items():
            total_score += feature_scores.get(feature_name, 0.0) * weight
        return round(min(max(total_score, 0.0), 1.0), 4)

    def build_outfit_explanation(
        self,
        feature_scores,
        request_context,
        feature_details=None,
    ):
        feature_details = feature_details or {}
        color_detail = feature_details.get("color_harmony") or {}
        event_label = EVENT_LABELS.get(
            self._normalize_token(request_context.get("event_type")),
            "выбранного события",
        )
        reason_templates = {
            "color_harmony": (
                color_detail.get(
                    "reason",
                    "Цвета вещей хорошо сочетаются между собой",
                ),
                color_detail.get(
                    "fragment",
                    "цвета выглядят согласованно",
                ),
            ),
            "style_match": (
                "Стили вещей хорошо сочетаются",
                "стили вещей не конфликтуют",
            ),
            "event_match": (
                f"Образ подходит для события: {event_label}",
                "образ подходит под выбранное событие",
            ),
            "season_match": (
                "Вещи согласованы по сезону",
                "вещи подходят по сезону",
            ),
            "temperature_match": (
                "Образ соответствует заданной температуре",
                "комплект подходит под температуру",
            ),
            "weather_condition_match": (
                "Образ соответствует погодным условиям",
                "погода учтена при подборе",
            ),
            "completeness": (
                "Собран полный комплект одежды",
                "комплект выглядит полным",
            ),
            "layering_correctness": (
                "Слои подобраны логично и без конфликтов",
                "слои собраны корректно",
            ),
            "user_preference_match": (
                "Учтены предпочтения пользователя",
                "предпочтения пользователя были учтены",
            ),
            "constraints_match": (
                "Соблюдены заданные ограничения",
                "заданные ограничения соблюдены",
            ),
        }

        sorted_features = sorted(
            feature_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        best_features = [item for item in sorted_features if item[1] >= 0.75][:4]
        if not best_features:
            best_features = sorted_features[:2]

        reasons = [reason_templates[name][0] for name, _score in best_features]
        fragments = [reason_templates[name][1] for name, _score in best_features[:3]]

        if not fragments:
            explanation = "Образ собран без явных конфликтов и подходит для базового использования."
        elif len(fragments) == 1:
            explanation = f"Образ получил высокий балл, потому что {fragments[0]}."
        else:
            explanation = (
                "Образ получил высокий балл, потому что "
                f"{', '.join(fragments[:-1])} и {fragments[-1]}."
            )

        return reasons, explanation

    def score_color_harmony(self, outfit, request_context):
        return self._evaluate_color_harmony(outfit, request_context)["score"]

    def score_style_match(self, items, request_context):
        style_profiles = [
            self._get_item_style_families(item)
            for item in items
            if self._get_item_style_families(item)
        ]
        if not style_profiles:
            return 0.65

        style_counter = Counter(
            style_family
            for style_profile in style_profiles
            for style_family in style_profile
        )
        dominant_ratio = style_counter.most_common(1)[0][1] / len(style_profiles)

        pair_scores = [
            self._score_style_profile_pair(left_profile, right_profile)
            for left_profile, right_profile in combinations(style_profiles, 2)
        ]
        pairwise_score = sum(pair_scores) / len(pair_scores) if pair_scores else 0.9

        preferred_style = self._normalize_token(request_context.get("preferred_style"))
        preferred_family = STYLE_FAMILY_MAP.get(preferred_style, preferred_style)
        preferred_bonus = 0.75
        if preferred_family:
            preferred_bonus = sum(
                1.0 if preferred_family in style_profile else 0.5
                for style_profile in style_profiles
            ) / len(style_profiles)

        return round(
            min(
                1.0,
                (dominant_ratio * 0.45)
                + (pairwise_score * 0.35)
                + (preferred_bonus * 0.2),
            ),
            4,
        )

    def score_event_match(self, items, request_context):
        event_type = self._normalize_token(request_context.get("event_type")) or "casual"
        event_rule = EVENT_RULES.get(event_type, EVENT_RULES["casual"])
        if any(not self._item_matches_event_hard_rule(item, event_type) for item in items):
            return 0.0

        item_scores = [
            self._score_item_event_fit(item, event_type, event_rule)
            for item in items
        ]
        return round(sum(item_scores) / len(item_scores), 4)

    def score_season_match(self, items, request_context):
        target_season = self._normalize_token(request_context.get("season"))
        if not target_season:
            target_season = self._infer_season_from_temperature(
                request_context.get("temperature")
            )

        item_seasons = [
            self._normalize_token(item.season)
            for item in items
            if self._normalize_token(item.season)
        ]
        if not item_seasons:
            return 0.7

        target_score = 0.78
        if target_season:
            target_matches = [
                self._score_item_season_fit(item_season, target_season)
                for item_season in item_seasons
            ]
            target_score = sum(target_matches) / len(target_matches)

        filtered_seasons = [
            item_season for item_season in item_seasons if item_season != "all_season"
        ]
        internal_consistency = 1.0
        if filtered_seasons:
            internal_consistency = (
                Counter(filtered_seasons).most_common(1)[0][1] / len(filtered_seasons)
            )

        insulation_score = self._score_insulation_balance(items, request_context)
        return round(
            (target_score * 0.4)
            + (internal_consistency * 0.2)
            + (insulation_score * 0.4),
            4,
        )

    def score_temperature_match(self, candidate, request_context):
        temperature = request_context.get("temperature")
        if temperature is None:
            return 0.7

        items = [entry["item"] for entry in candidate]
        shoes = self._get_item_by_category(candidate, "shoes")
        outerwear_score = self._score_outerwear_fit(
            candidate,
            temperature,
            request_context.get("weather_condition"),
        )
        warmth_score = self._score_insulation_balance(items, request_context)
        shoes_score = self._score_shoe_temperature_fit(shoes, temperature)
        layer_score = self._score_layer_coverage(candidate, request_context)

        return round(
            (warmth_score * 0.45)
            + (shoes_score * 0.25)
            + (layer_score * 0.2)
            + (outerwear_score * 0.1),
            4,
        )

    def score_weather_condition_match(self, candidate, request_context):
        weather_condition = self._normalize_token(request_context.get("weather_condition"))
        if not weather_condition:
            return 0.7

        normalized_weather = {"clear": "sunny"}.get(weather_condition, weather_condition)
        temperature = request_context.get("temperature")
        shoes = self._get_item_by_category(candidate, "shoes")
        bottom = self._get_item_by_category(candidate, "bottom")
        protection_score = self._score_weather_protection(
            candidate,
            normalized_weather,
            temperature,
        )

        shoes_score = self._score_shoe_weather_fit(
            shoes,
            normalized_weather,
            temperature,
        )
        outerwear_score = self._score_outerwear_fit(
            candidate,
            temperature,
            normalized_weather,
        )
        bottom_score = self._score_bottom_weather_fit(
            bottom,
            normalized_weather,
            temperature,
        )

        if normalized_weather == "snow" and shoes_score < 0.45:
            return 0.0

        return round(
            (protection_score * 0.35)
            + (shoes_score * 0.3)
            + (outerwear_score * 0.2)
            + (bottom_score * 0.15),
            4,
        )

    def score_completeness(self, candidate, request_context=None):
        roles = {entry["role"] for entry in candidate}
        required_roles = {"top", "bottom", "shoes"}
        matched_roles = len(roles & required_roles)
        base_score = matched_roles / len(required_roles)
        request_context = request_context or {}
        needs_outerwear = self._requires_outerwear(request_context)
        outerwear_score = 1.0 if not needs_outerwear else 1.0 if "outerwear" in roles else 0.2
        event_type = self._normalize_token(request_context.get("event_type"))
        accessory_bonus = 0.85
        if event_type in {"office", "evening", "party", "date"}:
            accessory_bonus = 1.0 if "accessory" in roles else 0.55
        return round(
            min(1.0, (base_score * 0.75) + (outerwear_score * 0.15) + (accessory_bonus * 0.1)),
            4,
        )

    def score_layering_correctness(self, candidate, request_context):
        role_counts = Counter(entry["role"] for entry in candidate)
        if any(count > 1 for count in role_counts.values()):
            return 0.3

        roles = set(role_counts)
        if not {"top", "bottom", "shoes"}.issubset(roles):
            return 0.35

        has_outerwear = "outerwear" in roles
        temperature = request_context.get("temperature")
        weather_condition = self._normalize_token(request_context.get("weather_condition"))

        if has_outerwear and "top" not in roles:
            return 0.3
        if self._requires_outerwear(request_context) and not has_outerwear:
            return 0.2
        if temperature is not None and temperature >= 24 and has_outerwear:
            outerwear = self._get_item_by_category(candidate, "outerwear")
            if self._normalize_token(outerwear.subcategory) in HEAVY_OUTERWEAR_TYPES:
                return 0.35
            return 0.7
        if weather_condition in {"rain", "snow", "wind"} and not has_outerwear:
            return 0.35

        layer_score = self._score_layer_coverage(candidate, request_context)
        texture_score = self._score_texture_contrast(candidate)
        silhouette_score = self._score_silhouette_balance(candidate)
        return round(
            (layer_score * 0.55)
            + (texture_score * 0.2)
            + (silhouette_score * 0.25),
            4,
        )

    def score_user_preference_match(self, candidate, request_context, user_preferences):
        items = [entry["item"] for entry in candidate]
        preferred_colors = {
            self._normalize_color(color)
            for color in self._split_color_values(user_preferences.get("preferred_colors"))
        }
        preferred_colors |= {
            self._normalize_color(color)
            for color in self._split_color_values(request_context.get("preferred_colors"))
        }
        preferred_colors.discard(None)

        preferred_styles = {
            STYLE_FAMILY_MAP.get(style, style)
            for style in self._normalize_tokens(user_preferences.get("preferred_styles"))
        }
        request_style = self._normalize_token(request_context.get("preferred_style"))
        if request_style:
            preferred_styles.add(STYLE_FAMILY_MAP.get(request_style, request_style))

        colors_score = 0.75
        if preferred_colors:
            color_hits = 0
            for item in items:
                item_colors = set(self._extract_item_colors(item))
                item_families = {
                    self._get_color_family(color_token) for color_token in item_colors
                }
                if item_colors & preferred_colors:
                    color_hits += 1
                elif any(
                    self._get_color_family(color_token) in item_families
                    for color_token in preferred_colors
                ):
                    color_hits += 0.75
            colors_score = color_hits / len(items)

        styles_score = 0.75
        if preferred_styles:
            style_hits = 0
            for item in items:
                item_styles = self._get_item_style_families(item)
                if item_styles & preferred_styles:
                    style_hits += 1
            styles_score = style_hits / len(items)

        constraint_alignment = 1.0
        request_constraints = self._normalize_tokens(request_context.get("constraints"))
        if request_constraints:
            constraint_alignment = (
                1.0
                if not self._violates_hard_constraints(candidate, request_constraints)
                else 0.3
            )

        return round(
            (colors_score * 0.45)
            + (styles_score * 0.35)
            + (constraint_alignment * 0.2),
            4,
        )

    def score_constraints_match(self, candidate, request_context, user_preferences):
        constraints = self._normalize_tokens(request_context.get("constraints"))
        constraints += self._normalize_tokens(user_preferences.get("constraints"))
        disliked_items = self._normalize_tokens(user_preferences.get("disliked_items"))

        total_checks = len(constraints) + len(disliked_items)
        if total_checks == 0:
            return 1.0

        violations = 0
        for constraint in constraints:
            if self._candidate_violates_constraint(candidate, constraint):
                violations += 1

        for disliked_item in disliked_items:
            if self._candidate_has_attribute(candidate, disliked_item):
                violations += 1

        return round(max(0.0, 1 - (violations / total_checks)), 4)

    def _categorize_items(self, clothing_items):
        categorized = {
            "top": [],
            "bottom": [],
            "shoes": [],
            "outerwear": [],
            "accessory": [],
        }
        for item in clothing_items:
            if item.category in categorized:
                categorized[item.category].append(item)
        return categorized

    def _build_pool(self, items, anchor_item, category, allow_empty=False):
        if anchor_item and anchor_item.category == category:
            return [anchor_item]
        if allow_empty:
            return items or [None]
        return items

    def _find_anchor_item(self, clothing_items, anchor_item_id):
        if not anchor_item_id:
            return None
        return next((item for item in clothing_items if item.id == anchor_item_id), None)

    def _make_candidate_entry(self, role, item):
        return {"role": role, "item": item}

    def _is_valid_candidate(self, candidate, constraints, request_context):
        item_ids = [entry["item"].id for entry in candidate if entry.get("item")]
        if len(item_ids) != len(set(item_ids)):
            return False

        roles = {entry["role"] for entry in candidate}
        if not {"top", "bottom", "shoes"}.issubset(roles):
            return False

        if self._violates_hard_constraints(candidate, constraints):
            return False
        if any(
            not self._item_matches_event_hard_rule(entry["item"], self._normalize_token(request_context.get("event_type")) or "casual")
            for entry in candidate
        ):
            return False

        shoes = self._get_item_by_category(candidate, "shoes")
        bottom = self._get_item_by_category(candidate, "bottom")
        temperature = request_context.get("temperature")
        weather_condition = request_context.get("weather_condition")

        if self._score_shoe_temperature_fit(shoes, temperature) < 0.45:
            return False
        if self._score_shoe_weather_fit(shoes, weather_condition, temperature) < 0.45:
            return False
        if self._score_bottom_weather_fit(bottom, weather_condition, temperature) < 0.35:
            return False
        if self._requires_outerwear(request_context) and "outerwear" not in roles:
            return False

        return True

    def _deduplicate_candidates(self, candidates):
        unique_candidates = []
        seen = set()
        for candidate in candidates:
            key = tuple(
                sorted((entry["role"], entry["item"].id) for entry in candidate)
            )
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)
        return unique_candidates

    def _serialize_candidate_item(self, entry):
        item = entry["item"]
        payload = item.to_dict()
        payload["role"] = entry["role"]
        payload["clothing_item_id"] = item.id
        return payload

    def _normalize_tokens(self, values):
        if not values:
            return []
        normalized = []
        for value in values:
            token = self._normalize_token(value)
            if token:
                normalized.append(token)
        return normalized

    def _normalize_token(self, value):
        if value is None:
            return None
        token = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        return token or None

    def _normalize_color(self, value):
        token = self._normalize_token(value)
        if not token:
            return None

        if token in COLOR_ALIASES:
            return COLOR_ALIASES[token]

        parts = [part for part in token.split("_") if part]
        for size in range(min(3, len(parts)), 0, -1):
            for start in range(0, len(parts) - size + 1):
                candidate = "_".join(parts[start : start + size])
                if candidate in COLOR_ALIASES:
                    return COLOR_ALIASES[candidate]

        for part in parts:
            if part in COLOR_ALIASES:
                return COLOR_ALIASES[part]

        return "unknown"

    def _get_color_family(self, color_token):
        normalized_color = self._normalize_color(color_token)
        if not normalized_color:
            return "unknown"
        return COLOR_FAMILY_MAP.get(normalized_color, "unknown")

    def _is_neutral_color(self, color_token):
        normalized_color = self._normalize_color(color_token)
        return normalized_color in NEUTRAL_COLOR_TOKENS

    def _is_metallic_color(self, color_token):
        normalized_color = self._normalize_color(color_token)
        return normalized_color in METALLIC_COLOR_TOKENS

    def _coerce_outfit_entries(self, outfit):
        entries = []
        for entry in outfit or []:
            if isinstance(entry, dict) and "item" in entry:
                item = entry.get("item")
                role = self._normalize_token(entry.get("role"))
            else:
                item = entry
                role = None

            if item is None:
                continue

            entries.append(
                {
                    "role": role or self._normalize_token(getattr(item, "category", None)) or "item",
                    "item": item,
                }
            )

        return entries

    def _normalize_weights(self, weights):
        total_weight = sum(max(weight, 0.0) for weight in weights.values()) or 1.0
        return {
            feature_name: round(max(weight, 0.0) / total_weight, 4)
            for feature_name, weight in weights.items()
        }

    def _get_contextual_weights(self, request_context):
        weights = dict(self.weights)
        temperature = request_context.get("temperature")
        weather_condition = self._normalize_token(request_context.get("weather_condition"))
        event_type = self._normalize_token(request_context.get("event_type"))

        if weather_condition in {"snow", "rain", "wind"} or (
            temperature is not None and temperature <= 5
        ):
            weights["weather_condition_match"] += 0.05
            weights["temperature_match"] += 0.04
            weights["season_match"] += 0.03
            weights["layering_correctness"] += 0.03
            weights["color_harmony"] -= 0.05
            weights["style_match"] -= 0.03
            weights["user_preference_match"] -= 0.04
            weights["completeness"] -= 0.03

        if event_type in {"office", "evening", "party", "date"}:
            weights["event_match"] += 0.03
            weights["style_match"] += 0.02
            weights["color_harmony"] += 0.01
            weights["user_preference_match"] -= 0.03
            weights["constraints_match"] -= 0.03

        return self._normalize_weights(weights)

    def _get_item_style_families(self, item):
        style_families = {
            STYLE_FAMILY_MAP.get(style_token, style_token)
            for style_token in self._normalize_tokens(item.styles or [])
        }
        style_families.discard(None)

        if style_families:
            return style_families

        formality = self._normalize_token(item.formality)
        subcategory = self._normalize_token(item.subcategory)
        if formality in {"formal", "smart"} or subcategory in {"blazer", "loafers", "pumps"}:
            return {"classic"}
        if subcategory in {"hoodie", "joggers", "sneakers", "summer_sneakers"}:
            return {"casual"}
        return {"casual"}

    def _score_style_profile_pair(self, left_profile, right_profile):
        if left_profile & right_profile:
            return 1.0
        if any(
            frozenset({left_family, right_family}) in STYLE_COMPATIBILITY_PAIRS
            for left_family in left_profile
            for right_family in right_profile
        ):
            return 0.8
        return 0.45

    def _item_matches_event_hard_rule(self, item, event_type):
        disallowed_styles = EVENT_DISALLOWED_STYLES.get(event_type, set())
        if self._get_item_style_families(item) & disallowed_styles:
            return False

        subcategory = self._normalize_token(item.subcategory)
        if subcategory in EVENT_DISALLOWED_SUBCATEGORIES.get(event_type, set()):
            return False

        return True

    def _score_shoe_event_fit(self, item, event_type):
        subcategory = self._normalize_token(item.subcategory)
        if event_type == "office":
            if subcategory in {"loafers", "pumps", "closed_shoes", "boots", "ankle_boots"}:
                return 1.0
            if subcategory in {"sneakers", "summer_sneakers"}:
                return 0.7
            return 0.25

        if event_type in {"evening", "party", "date"}:
            if subcategory in {"pumps", "heels", "loafers", "closed_shoes", "boots", "ankle_boots"}:
                return 1.0
            if subcategory in {"sneakers", "summer_sneakers"}:
                return 0.65
            return 0.2

        if event_type == "sport":
            if subcategory in {"sneakers", "summer_sneakers"}:
                return 1.0
            if subcategory in {"boots", "ankle_boots"}:
                return 0.45
            return 0.2

        return 0.9 if subcategory not in {"pumps", "heels"} else 0.75

    def _score_item_event_fit(self, item, event_type, event_rule):
        allowed_styles = {
            STYLE_FAMILY_MAP.get(style_token, style_token)
            for style_token in event_rule["styles"]
        }
        style_families = self._get_item_style_families(item)
        if style_families & allowed_styles:
            style_score = 1.0
        elif any(
            frozenset({style_family, allowed_style}) in STYLE_COMPATIBILITY_PAIRS
            for style_family in style_families
            for allowed_style in allowed_styles
        ):
            style_score = 0.7
        else:
            style_score = 0.25

        formality = self._normalize_token(item.formality)
        if formality in event_rule["formalities"]:
            formality_score = 1.0
        elif formality == "smart" and "formal" in event_rule["formalities"]:
            formality_score = 0.8
        elif formality == "casual" and "smart" in event_rule["formalities"]:
            formality_score = 0.55
        else:
            formality_score = 0.25

        shoe_score = 1.0
        if self._normalize_token(item.category) == "shoes":
            shoe_score = self._score_shoe_event_fit(item, event_type)

        return round(
            (style_score * 0.45) + (formality_score * 0.35) + (shoe_score * 0.2),
            4,
        )

    def _score_item_season_fit(self, item_season, target_season):
        normalized_item_season = self._normalize_token(item_season)
        if normalized_item_season in {None, "all_season"}:
            return 0.9
        if normalized_item_season == target_season:
            return 1.0

        adjacent_seasons = {
            frozenset({"winter", "autumn"}),
            frozenset({"autumn", "spring"}),
            frozenset({"spring", "summer"}),
        }
        if frozenset({normalized_item_season, target_season}) in adjacent_seasons:
            return 0.72
        return 0.35

    def _estimate_required_insulation(self, request_context):
        temperature = request_context.get("temperature")
        target_season = self._normalize_token(request_context.get("season"))

        if temperature is not None:
            if temperature <= -15:
                return 10.2
            if temperature <= -5:
                return 8.8
            if temperature <= 5:
                return 7.1
            if temperature <= 15:
                return 5.8
            if temperature <= 24:
                return 4.3
            return 3.0

        return {
            "winter": 8.5,
            "autumn": 6.3,
            "spring": 5.7,
            "summer": 3.2,
        }.get(target_season, 5.2)

    def _score_insulation_balance(self, items, request_context):
        provided_insulation = sum(self._estimate_item_warmth(item) for item in items)
        required_insulation = self._estimate_required_insulation(request_context)
        if required_insulation <= 0:
            return 0.8

        if provided_insulation <= required_insulation:
            return round(min(provided_insulation / required_insulation, 1.0), 4)

        excess_ratio = (provided_insulation - required_insulation) / required_insulation
        return round(max(0.3, 1.0 - (excess_ratio * 0.35)), 4)

    def _infer_layer_level(self, item):
        explicit_layer_level = self._normalize_token(getattr(item, "layer_level", None))
        if explicit_layer_level in {"base", "mid", "outer", "support"}:
            return explicit_layer_level

        category = self._normalize_token(item.category)
        subcategory = self._normalize_token(item.subcategory)
        if category == "outerwear":
            return "outer"
        if subcategory in SUBCATEGORY_LAYER_LEVELS:
            return SUBCATEGORY_LAYER_LEVELS[subcategory]
        if category == "top":
            return "base"
        return None

    def _get_required_layers(self, request_context):
        temperature = request_context.get("temperature")
        weather_condition = self._normalize_token(request_context.get("weather_condition"))

        if weather_condition == "snow" or (temperature is not None and temperature <= 0):
            return {"base", "mid", "outer"}
        if weather_condition in {"rain", "wind"} or (temperature is not None and temperature <= 12):
            return {"base", "outer"}
        return {"base"}

    def _score_layer_coverage(self, candidate, request_context):
        layer_levels = {
            self._infer_layer_level(entry["item"])
            for entry in candidate
            if self._infer_layer_level(entry["item"])
        }
        required_layers = self._get_required_layers(request_context)
        coverage_score = len(layer_levels & required_layers) / len(required_layers)

        temperature = request_context.get("temperature")
        if temperature is not None and temperature >= 24 and "outer" in layer_levels:
            outerwear = self._get_item_by_category(candidate, "outerwear")
            if outerwear and self._normalize_token(outerwear.subcategory) in HEAVY_OUTERWEAR_TYPES:
                coverage_score *= 0.45

        return round(min(max(coverage_score, 0.0), 1.0), 4)

    def _get_texture_key(self, item):
        material = self._normalize_token(getattr(item, "material", None))
        subcategory = self._normalize_token(item.subcategory)
        if material in TEXTURE_ALIAS_MAP:
            return TEXTURE_ALIAS_MAP[material]
        if subcategory in SUBCATEGORY_TEXTURE_MAP:
            return SUBCATEGORY_TEXTURE_MAP[subcategory]
        category = self._normalize_token(item.category)
        return {
            "outerwear": "structured",
            "shoes": "structured",
            "accessory": "structured",
            "top": "soft_woven",
            "bottom": "structured",
        }.get(category, "soft_woven")

    def _score_texture_contrast(self, candidate):
        items = [
            entry["item"]
            for entry in candidate
            if entry["role"] in {"top", "bottom", "outerwear", "accessory"}
        ]
        if len(items) < 2:
            return 0.7

        unique_textures = {self._get_texture_key(item) for item in items}
        unique_count = len(unique_textures)
        if unique_count == 1:
            return 0.45
        if unique_count == 2:
            return 0.72
        return min(1.0, 0.82 + ((unique_count - 3) * 0.06))

    def _infer_fit_profile(self, item):
        explicit_fit = self._normalize_token(getattr(item, "fit", None))
        explicit_fit_map = {
            "fitted": "fitted",
            "balanced": "balanced",
            "loose": "loose",
            "oversized": "loose",
        }
        if explicit_fit in explicit_fit_map:
            return explicit_fit_map[explicit_fit]

        subcategory = self._normalize_token(item.subcategory)
        if subcategory in FITTED_SUBCATEGORIES:
            return "fitted"
        if subcategory in RELAXED_SUBCATEGORIES:
            return "loose"

        style_families = self._get_item_style_families(item)
        if "classic" in style_families or "romantic" in style_families:
            return "fitted"
        if "sport" in style_families or "casual" in style_families:
            return "loose"
        return "balanced"

    def _score_silhouette_balance(self, candidate):
        fit_profiles = [
            self._infer_fit_profile(entry["item"])
            for entry in candidate
            if entry["role"] in {"top", "bottom", "outerwear"}
        ]
        if not fit_profiles:
            return 0.7

        loose_count = sum(1 for fit_profile in fit_profiles if fit_profile == "loose")
        fitted_count = sum(1 for fit_profile in fit_profiles if fit_profile == "fitted")
        if loose_count == 0 and fitted_count == 0:
            return 0.7

        return round(
            1.0 - abs(loose_count - fitted_count) / (loose_count + fitted_count),
            4,
        )

    def _score_weather_protection(self, candidate, weather_condition, temperature):
        if weather_condition == "sunny":
            outerwear = self._get_item_by_category(candidate, "outerwear")
            if (
                outerwear
                and temperature is not None
                and temperature >= 24
                and self._normalize_token(outerwear.subcategory) in HEAVY_OUTERWEAR_TYPES
            ):
                return 0.4
            return 0.9

        if weather_condition == "cloudy":
            return 0.88 if not self._requires_outerwear({"temperature": temperature, "weather_condition": weather_condition}) else 0.78

        outerwear = self._get_item_by_category(candidate, "outerwear")
        if outerwear is None:
            return 0.15 if weather_condition in {"rain", "snow"} else 0.45

        outerwear_subcategory = self._normalize_token(outerwear.subcategory)
        outerwear_material = self._normalize_token(outerwear.material)
        explicit_waterproof = bool(getattr(outerwear, "waterproof", False))
        explicit_windproof = bool(getattr(outerwear, "windproof", False))

        if weather_condition == "rain":
            if (
                explicit_waterproof
                or explicit_windproof
                or outerwear_subcategory in WATERPROOF_OUTERWEAR_TYPES
                or outerwear_material in WATER_RESISTANT_MATERIALS
            ):
                return 1.0
            if outerwear_subcategory in WINDPROOF_OUTERWEAR_TYPES:
                return 0.75
            return 0.65

        if weather_condition == "snow":
            if (
                explicit_windproof
                or explicit_waterproof
                or outerwear_subcategory in HEAVY_OUTERWEAR_TYPES | WINDPROOF_OUTERWEAR_TYPES
            ):
                return 1.0
            return 0.55

        if weather_condition == "wind":
            if explicit_windproof or outerwear_subcategory in WINDPROOF_OUTERWEAR_TYPES:
                return 1.0
            if explicit_waterproof or outerwear_subcategory in WATERPROOF_OUTERWEAR_TYPES:
                return 0.82
            return 0.7

        return 0.8

    def _split_color_values(self, colors):
        if not colors:
            return []
        if isinstance(colors, str):
            raw_values = colors
            for separator in ["/", ";", "|"]:
                raw_values = raw_values.replace(separator, ",")
            return [value.strip() for value in raw_values.split(",") if value.strip()]
        return list(colors)

    def _extract_item_colors(self, item):
        colors = []
        for value in self._split_color_values(getattr(item, "colors", None)):
            normalized_color = self._normalize_color(value)
            if normalized_color and normalized_color not in colors:
                colors.append(normalized_color)
        return colors[:3]

    def _get_color_share_weights(self, color_count):
        if color_count <= 1:
            return (1.0,)
        if color_count == 2:
            return (0.78, 0.22)
        return COLOR_SHARE_WEIGHTS[:color_count]

    # Approximate palette proportions by garment role so top/bottom dominate,
    # while shoes and accessories stay softer accents.
    def _build_outfit_color_profile(self, outfit):
        entries = self._coerce_outfit_entries(outfit)
        family_weights = Counter()
        active_family_weights = Counter()
        token_weights = Counter()
        role_profiles = {}
        total_weight = 0.0
        known_weight = 0.0
        neutral_weight = 0.0
        metallic_weight = 0.0
        unknown_weight = 0.0

        for entry in entries:
            item = entry["item"]
            role = entry["role"]
            role_weight = ROLE_COLOR_WEIGHTS.get(role, ROLE_COLOR_WEIGHTS["item"])
            colors = self._extract_item_colors(item)
            role_family_weights = Counter()
            role_known_weight = 0.0
            role_neutral_weight = 0.0
            role_metallic_weight = 0.0
            role_active_families = set()
            role_families = set()

            if not colors:
                soft_unknown_weight = role_weight * 0.45
                total_weight += soft_unknown_weight
                unknown_weight += soft_unknown_weight
                role_profiles[role] = {
                    "role": role,
                    "tokens": [],
                    "families": set(),
                    "active_families": set(),
                    "family_weights": role_family_weights,
                    "known_weight": 0.0,
                    "neutral_share": 0.0,
                    "metallic_share": 0.0,
                }
                continue

            for color_token, share_weight in zip(
                colors,
                self._get_color_share_weights(len(colors)),
            ):
                color_weight = role_weight * share_weight
                family = self._get_color_family(color_token)

                total_weight += color_weight
                token_weights[color_token] += color_weight
                family_weights[family] += color_weight
                role_family_weights[family] += color_weight
                role_families.add(family)

                if family == "unknown":
                    unknown_weight += color_weight
                    continue

                known_weight += color_weight
                role_known_weight += color_weight

                if self._is_neutral_color(color_token):
                    neutral_weight += color_weight
                    role_neutral_weight += color_weight
                elif self._is_metallic_color(color_token):
                    metallic_weight += color_weight
                    role_metallic_weight += color_weight
                else:
                    active_family_weights[family] += color_weight
                    role_active_families.add(family)

            role_profiles[role] = {
                "role": role,
                "tokens": colors,
                "families": role_families,
                "active_families": role_active_families,
                "family_weights": role_family_weights,
                "known_weight": role_known_weight,
                "neutral_share": (
                    role_neutral_weight / role_known_weight if role_known_weight else 0.0
                ),
                "metallic_share": (
                    role_metallic_weight / role_known_weight if role_known_weight else 0.0
                ),
            }

        active_total = sum(active_family_weights.values())
        dominant_active_family = None
        dominant_active_share = 0.0
        if active_family_weights:
            dominant_active_family, dominant_active_weight = active_family_weights.most_common(1)[0]
            dominant_active_share = (
                dominant_active_weight / active_total if active_total else 0.0
            )

        return {
            "total_weight": total_weight,
            "known_weight": known_weight,
            "known_ratio": (known_weight / total_weight) if total_weight else 0.0,
            "neutral_weight": neutral_weight,
            "metallic_weight": metallic_weight,
            "unknown_weight": unknown_weight,
            "unknown_share": (unknown_weight / total_weight) if total_weight else 0.0,
            "neutral_share": (
                (neutral_weight + metallic_weight) / known_weight if known_weight else 0.0
            ),
            "family_weights": family_weights,
            "active_family_weights": active_family_weights,
            "token_weights": token_weights,
            "role_profiles": role_profiles,
            "dominant_family": dominant_active_family,
            "dominant_active_share": dominant_active_share,
        }

    def _score_neutral_base_scheme(self, profile):
        if profile["known_weight"] <= 0:
            return 0.62

        active_family_count = len(profile["active_family_weights"])
        neutral_share = profile["neutral_share"]

        if active_family_count == 0:
            return 0.92
        if neutral_share >= 0.55 and active_family_count == 1:
            return 0.97
        if neutral_share >= 0.45 and active_family_count <= 2:
            return 0.88
        if neutral_share >= 0.35 and active_family_count <= 3:
            return 0.76
        if neutral_share <= 0.15 and active_family_count >= 4:
            return 0.25
        if neutral_share <= 0.2 and active_family_count >= 3:
            return 0.55
        return 0.62

    def _score_monochrome_scheme(self, profile):
        active_family_weights = profile["active_family_weights"]
        if not active_family_weights:
            return 0.82

        active_family_count = len(active_family_weights)
        dominant_share = profile["dominant_active_share"]

        if active_family_count == 1:
            score = 0.96
        elif active_family_count == 2 and dominant_share >= 0.78:
            score = 0.88
        elif active_family_count <= 3 and dominant_share >= 0.7:
            score = 0.76
        else:
            score = 0.34

        if score >= 0.76 and profile["neutral_share"] >= 0.25:
            score += 0.04

        return round(min(score, 1.0), 4)

    def _score_analogous_scheme(self, profile):
        families = list(profile["active_family_weights"].keys())
        if len(families) < 2:
            return 0.35
        if len(families) > 3:
            return 0.22

        analogous_links = sum(
            1
            for left_family, right_family in combinations(families, 2)
            if frozenset({left_family, right_family}) in ANALOGOUS_FAMILY_PAIRS
        )

        if len(families) == 2:
            score = 0.9 if analogous_links == 1 else 0.32
        else:
            score = 0.88 if analogous_links >= 2 else 0.48 if analogous_links == 1 else 0.24

        if analogous_links and profile["dominant_active_share"] >= 0.5:
            score += 0.04

        return round(min(score, 1.0), 4)

    def _score_complementary_scheme(self, profile):
        active_family_weights = profile["active_family_weights"]
        active_total = sum(active_family_weights.values())
        if active_total <= 0:
            return 0.25

        best_score = 0.22
        for left_family, right_family in combinations(active_family_weights.keys(), 2):
            if frozenset({left_family, right_family}) not in COMPLEMENTARY_FAMILY_PAIRS:
                continue

            pair_weight = active_family_weights[left_family] + active_family_weights[right_family]
            dominant_share = max(
                active_family_weights[left_family],
                active_family_weights[right_family],
            ) / pair_weight
            accent_share = min(
                active_family_weights[left_family],
                active_family_weights[right_family],
            ) / pair_weight
            extra_share = max(0.0, active_total - pair_weight) / active_total

            if dominant_share >= 0.65 and accent_share <= 0.35:
                score = 0.9
            elif dominant_share >= 0.58 and accent_share <= 0.42:
                score = 0.78
            else:
                score = 0.58

            score -= extra_share * 0.45
            best_score = max(best_score, score)

        return round(min(max(best_score, 0.0), 1.0), 4)

    def _score_color_complexity(self, profile):
        active_family_weights = profile["active_family_weights"]
        active_total = sum(active_family_weights.values())
        if active_total <= 0:
            return 0.95

        active_family_count = len(active_family_weights)
        if active_family_count == 1:
            score = 0.95
        elif active_family_count == 2:
            score = 0.88
        elif active_family_count == 3:
            score = 0.78
        elif active_family_count == 4:
            score = 0.45
        else:
            score = 0.22

        coverage_top_three = (
            sum(weight for _family, weight in active_family_weights.most_common(3))
            / active_total
        )
        if active_family_count <= 3 and coverage_top_three >= 0.9:
            score += 0.04
        elif active_family_count >= 4 and coverage_top_three < 0.78:
            score -= 0.08

        if profile["unknown_share"] > 0.35:
            score -= 0.05

        return round(min(max(score, 0.0), 1.0), 4)

    def _score_color_accent_balance(self, profile):
        known_weight = profile["known_weight"]
        if known_weight <= 0:
            return 0.62

        family_shares = sorted(
            (
                weight / known_weight
                for family, weight in profile["family_weights"].items()
                if family != "unknown"
            ),
            reverse=True,
        )
        if profile["neutral_share"] >= 0.65:
            return 0.9

        significant_share_count = len([share for share in family_shares if share >= 0.12])
        if significant_share_count <= 1:
            return 0.88
        if significant_share_count == 2:
            dominant_share, secondary_share = family_shares[:2]
            imbalance = (
                (abs(dominant_share - 0.7) / 0.7)
                + (abs(secondary_share - 0.3) / 0.3)
            ) / 2
            return round(max(0.0, 1.0 - imbalance), 4)
        if significant_share_count == 3:
            dominant_share, secondary_share, accent_share = family_shares[:3]
            imbalance = (
                (abs(dominant_share - 0.5) / 0.5)
                + (abs(secondary_share - 0.3) / 0.3)
                + (abs(accent_share - 0.2) / 0.2)
            ) / 3
            return round(max(0.0, 1.0 - imbalance), 4)

        while len(family_shares) < 3:
            family_shares.append(0.0)

        dominant_share, secondary_share, accent_share = family_shares[:3]
        imbalance = (
            (abs(dominant_share - 0.6) / 0.6)
            + (abs(secondary_share - 0.3) / 0.3)
            + (abs(accent_share - 0.1) / 0.1)
        ) / 3

        if len([share for share in family_shares[:4] if share >= 0.08]) >= 4:
            imbalance += 0.18

        return round(max(0.0, 1.0 - imbalance), 4)

    def _score_preferred_colors_fit(self, profile, request_context):
        preferred_colors = []
        for value in self._split_color_values(request_context.get("preferred_colors")):
            normalized_color = self._normalize_color(value)
            if normalized_color and normalized_color != "unknown" and normalized_color not in preferred_colors:
                preferred_colors.append(normalized_color)

        if not preferred_colors:
            return 0.7

        matched_weight = 0.0
        for preferred_color in preferred_colors:
            family = self._get_color_family(preferred_color)
            if profile["token_weights"].get(preferred_color):
                matched_weight += 1.0
            elif family != "unknown" and profile["family_weights"].get(family):
                matched_weight += 0.82

        coverage = matched_weight / len(preferred_colors)
        score = 0.45 + (coverage * 0.45)
        return round(min(score, 0.92), 4)

    def _family_supported_outside_role(self, profile, role, family):
        supported_weight = 0.0
        for other_role, role_profile in profile["role_profiles"].items():
            if other_role == role:
                continue
            supported_weight += role_profile["family_weights"].get(family, 0.0)
        return supported_weight >= 0.25

    def _score_multicolor_support(self, profile):
        multicolor_profiles = [
            role_profile
            for role_profile in profile["role_profiles"].values()
            if len(role_profile["tokens"]) >= 2
        ]
        if not multicolor_profiles:
            return 0.7

        scores = []
        for role_profile in multicolor_profiles:
            known_families = [
                family
                for family in role_profile["families"]
                if family != "unknown"
            ]
            if not known_families:
                scores.append(0.62)
                continue

            support_hits = sum(
                1
                for family in known_families
                if self._family_supported_outside_role(
                    profile,
                    role_profile["role"],
                    family,
                )
            )
            if support_hits >= 2:
                scores.append(0.92)
            elif support_hits == 1:
                scores.append(0.82)
            else:
                scores.append(0.62)

        return round(sum(scores) / len(scores), 4)

    def _score_shoes_color_fit(self, profile):
        shoes_profile = profile["role_profiles"].get("shoes")
        if not shoes_profile:
            return 0.8
        if shoes_profile["known_weight"] <= 0:
            return 0.78
        if shoes_profile["neutral_share"] >= 0.5 or shoes_profile["metallic_share"] >= 0.5:
            return 0.94

        shoes_families = {
            family for family in shoes_profile["active_families"] if family != "unknown"
        }
        if not shoes_families:
            return 0.82

        repeated_family = any(
            self._family_supported_outside_role(profile, "shoes", family)
            for family in shoes_families
        )
        introduces_new_family = any(
            not self._family_supported_outside_role(profile, "shoes", family)
            for family in shoes_families
        )

        if repeated_family:
            return 0.9
        if profile["neutral_share"] >= 0.45 and len(profile["active_family_weights"]) <= 2:
            return 0.82
        if introduces_new_family and len(profile["active_family_weights"]) >= 4:
            return 0.3
        if introduces_new_family and len(profile["active_family_weights"]) >= 3:
            return 0.48
        return 0.72

    def _score_accessory_color_fit(self, profile):
        accessory_profile = profile["role_profiles"].get("accessory")
        if not accessory_profile:
            return 0.85
        if accessory_profile["known_weight"] <= 0:
            return 0.82
        if accessory_profile["metallic_share"] >= 0.5:
            return 0.96
        if accessory_profile["neutral_share"] >= 0.5:
            return 0.92

        accessory_families = {
            family
            for family in accessory_profile["active_families"]
            if family != "unknown"
        }
        if not accessory_families:
            return 0.86

        repeated_family = any(
            self._family_supported_outside_role(profile, "accessory", family)
            for family in accessory_families
        )
        introduces_new_family = any(
            not self._family_supported_outside_role(profile, "accessory", family)
            for family in accessory_families
        )

        if repeated_family:
            return 0.91
        if profile["neutral_share"] >= 0.45 and len(profile["active_family_weights"]) <= 2:
            return 0.88
        if introduces_new_family and len(profile["active_family_weights"]) >= 4:
            return 0.45
        return 0.75

    def _select_best_color_scheme(self, profile):
        if profile["known_weight"] <= 0:
            return {
                "name": "soft_unknown",
                "score": 0.62,
                "reason": "Цветовая палитра определена частично, но явных конфликтов нет",
                "fragment": "цветовая палитра выглядит достаточно спокойной",
            }

        if not profile["active_family_weights"]:
            score = self._score_neutral_base_scheme(profile)
            return {
                "name": "all_neutral",
                "score": score,
                "reason": "В образе использована спокойная нейтральная палитра",
                "fragment": "палитра построена на нейтральных базовых цветах",
            }

        candidates = [
            {
                "name": "neutral_accent",
                "score": self._score_neutral_base_scheme(profile),
                "reason": "В образе использована нейтральная база и один акцентный цвет",
                "fragment": "нейтральная база поддерживает один акцентный цвет",
            },
            {
                "name": "monochrome",
                "score": self._score_monochrome_scheme(profile),
                "reason": "Цвета собраны по монохромной схеме",
                "fragment": "палитра собрана по монохромной схеме",
            },
            {
                "name": "analogous",
                "score": self._score_analogous_scheme(profile),
                "reason": "Цвета находятся в соседних сегментах цветового круга",
                "fragment": "цвета находятся в соседних сегментах цветового круга",
            },
            {
                "name": "complementary",
                "score": self._score_complementary_scheme(profile),
                "reason": "Контрастный цвет использован как аккуратный акцент",
                "fragment": "контрастный цвет работает как аккуратный акцент",
            },
        ]

        return max(candidates, key=lambda candidate: candidate["score"])

    def _evaluate_color_harmony(self, outfit, request_context):
        profile = self._build_outfit_color_profile(outfit)
        if profile["total_weight"] <= 0:
            return {
                "score": 0.6,
                "reason": "Цветовая палитра определена частично, но явных конфликтов нет",
                "fragment": "цветовая палитра выглядит достаточно спокойной",
                "scheme": "soft_unknown",
                "subscores": {},
            }

        base_palette_score = self._score_neutral_base_scheme(profile)
        scheme = self._select_best_color_scheme(profile)
        complexity_score = self._score_color_complexity(profile)
        accent_balance_score = self._score_color_accent_balance(profile)
        preferred_colors_score = self._score_preferred_colors_fit(
            profile,
            request_context,
        )
        multicolor_support_score = self._score_multicolor_support(profile)
        base_palette_score = min(
            1.0,
            (base_palette_score * 0.82) + (multicolor_support_score * 0.18),
        )
        shoes_score = self._score_shoes_color_fit(profile)
        accessory_score = self._score_accessory_color_fit(profile)
        shoes_accessories_score = round((shoes_score + accessory_score) / 2, 4)

        total_score = (
            (base_palette_score * 0.25)
            + (scheme["score"] * 0.25)
            + (complexity_score * 0.15)
            + (accent_balance_score * 0.15)
            + (preferred_colors_score * 0.1)
            + (shoes_accessories_score * 0.10)
        )

        if profile["known_ratio"] < 0.35:
            total_score = (total_score * 0.5) + 0.62 * 0.5

        reason = scheme["reason"]
        fragment = scheme["fragment"]
        if shoes_accessories_score >= 0.93 and scheme["score"] < 0.9:
            accessory_profile = profile["role_profiles"].get("accessory")
            if accessory_profile and accessory_profile["metallic_share"] >= 0.5:
                reason = "Аксессуар не конфликтует с основными цветами"
                fragment = "аксессуар не конфликтует с основной палитрой"
            else:
                reason = "Обувь поддерживает палитру образа"
                fragment = "обувь поддерживает общую палитру"

        if profile["known_ratio"] < 0.35 and scheme["score"] < 0.75:
            reason = "Цветовая палитра определена частично, но явных конфликтов нет"
            fragment = "цветовая палитра выглядит достаточно спокойной"

        return {
            "score": round(min(max(total_score, 0.0), 1.0), 4),
            "reason": reason,
            "fragment": fragment,
            "scheme": scheme["name"],
            "subscores": {
                "base_palette_score": round(base_palette_score, 4),
                "scheme_score": round(scheme["score"], 4),
                "color_complexity_score": round(complexity_score, 4),
                "accent_balance_score": round(accent_balance_score, 4),
                "preferred_colors_score": round(preferred_colors_score, 4),
                "shoes_accessories_score": round(shoes_accessories_score, 4),
            },
        }

    def _infer_season_from_temperature(self, temperature):
        if temperature is None:
            return None
        if temperature <= 2:
            return "winter"
        if temperature <= 15:
            return "spring"
        return "summer"

    def _estimate_item_warmth(self, item):
        explicit_insulation = getattr(item, "insulation_rating", None)
        if explicit_insulation is not None:
            try:
                explicit_insulation = float(explicit_insulation)
            except (TypeError, ValueError):
                explicit_insulation = None

        base_warmth = {
            "top": 1.2,
            "bottom": 1.3,
            "shoes": 0.8,
            "outerwear": 2.8,
            "accessory": 0.3,
        }.get(item.category, 0.5)

        if explicit_insulation is not None:
            return max(0.1, explicit_insulation)

        item_subcategory = self._normalize_token(item.subcategory)
        item_season = self._normalize_token(item.season)
        if item_season == "winter":
            base_warmth += 1.0
        elif item_season == "autumn":
            base_warmth += 0.5
        elif item_season == "summer":
            base_warmth -= 0.4

        if item.category == "top":
            if item_subcategory in WARM_TOP_TYPES:
                base_warmth += 0.9
            elif item_subcategory in LIGHT_TOP_TYPES:
                base_warmth -= 0.3
        elif item.category == "bottom":
            if item_subcategory in WARM_BOTTOM_TYPES:
                base_warmth += 0.35
            elif item_subcategory in LIGHT_BOTTOM_TYPES:
                base_warmth -= 0.75
        elif item.category == "shoes":
            if item_subcategory in WINTER_SHOE_TYPES:
                base_warmth += 1.2
            elif item_subcategory in {"demi_boots", "ankle_boots", "boots", "closed_shoes"}:
                base_warmth += 0.7
            elif item_subcategory in OPEN_SHOE_TYPES:
                base_warmth -= 0.5
        elif item.category == "outerwear":
            if item_subcategory in HEAVY_OUTERWEAR_TYPES:
                base_warmth += 1.4
            elif item_subcategory in LIGHT_OUTERWEAR_TYPES:
                base_warmth += 0.7

        return max(0.2, base_warmth)

    def _get_item_by_category(self, candidate, category):
        return next((entry["item"] for entry in candidate if entry["item"].category == category), None)

    def _requires_outerwear(self, request_context):
        temperature = request_context.get("temperature")
        weather_condition = self._normalize_token(request_context.get("weather_condition"))

        if weather_condition in {"snow", "rain"}:
            return True
        if temperature is not None and temperature <= 10:
            return True
        if weather_condition == "wind" and (temperature is None or temperature <= 18):
            return True
        return False

    def _score_outerwear_fit(self, candidate, temperature, weather_condition):
        has_outerwear = any(entry["role"] == "outerwear" for entry in candidate)
        outerwear = self._get_item_by_category(candidate, "outerwear")
        normalized_weather = self._normalize_token(weather_condition)
        requires_outerwear = self._requires_outerwear(
            {
                "temperature": temperature,
                "weather_condition": normalized_weather,
            }
        )

        if requires_outerwear:
            if not has_outerwear or outerwear is None:
                return 0.0

            subcategory = self._normalize_token(outerwear.subcategory)
            if normalized_weather == "snow" or (temperature is not None and temperature <= 0):
                return 1.0 if subcategory in HEAVY_OUTERWEAR_TYPES else 0.7
            return 1.0 if subcategory in HEAVY_OUTERWEAR_TYPES | LIGHT_OUTERWEAR_TYPES else 0.75

        if not has_outerwear or outerwear is None:
            return 1.0

        subcategory = self._normalize_token(outerwear.subcategory)
        if temperature is not None and temperature >= 24 and subcategory in HEAVY_OUTERWEAR_TYPES:
            return 0.25
        if temperature is not None and temperature >= 20 and subcategory in LIGHT_OUTERWEAR_TYPES:
            return 0.7
        return 0.85

    def _score_shoe_temperature_fit(self, shoes, temperature):
        if shoes is None or temperature is None:
            return 0.7

        subcategory = self._normalize_token(shoes.subcategory)
        season = self._normalize_token(shoes.season)

        if temperature <= -5:
            if subcategory in WINTER_SHOE_TYPES:
                return 1.0
            if subcategory in {"demi_boots", "ankle_boots", "boots"} or season == "winter":
                return 0.65
            return 0.05

        if temperature <= 10:
            if subcategory in {"demi_boots", "ankle_boots", "boots", "closed_shoes", "sneakers"}:
                return 1.0
            if subcategory in WINTER_SHOE_TYPES or subcategory in {"loafers", "pumps"}:
                return 0.6
            return 0.15

        if temperature <= 20:
            if subcategory in MID_SHOE_TYPES | {"sandals", "espadrilles"}:
                return 1.0
            return 0.3

        if subcategory in HOT_SHOE_TYPES:
            return 1.0
        if subcategory in {"pumps", "closed_shoes"}:
            return 0.55
        return 0.15

    def _score_shoe_weather_fit(self, shoes, weather_condition, temperature):
        if shoes is None:
            return 0.4 if weather_condition in {"snow", "rain"} else 0.7

        normalized_weather = {"clear": "sunny"}.get(
            self._normalize_token(weather_condition),
            self._normalize_token(weather_condition),
        )
        if not normalized_weather:
            return 0.7

        subcategory = self._normalize_token(shoes.subcategory)

        if normalized_weather == "snow":
            if subcategory in WINTER_SHOE_TYPES:
                return 1.0
            if subcategory in SNOW_SAFE_SHOE_TYPES and (temperature is None or temperature <= 2):
                return 0.75
            return 0.0

        if normalized_weather == "rain":
            if subcategory in RAIN_SAFE_SHOE_TYPES:
                return 1.0
            if subcategory in {"loafers", "pumps"}:
                return 0.35
            return 0.1

        if normalized_weather == "wind":
            return 0.45 if subcategory in OPEN_SHOE_TYPES else 0.9

        if normalized_weather == "cloudy":
            if subcategory in OPEN_SHOE_TYPES and temperature is not None and temperature < 15:
                return 0.45
            return 0.9

        if normalized_weather == "sunny":
            if temperature is not None and temperature >= 22:
                if subcategory in HOT_SHOE_TYPES:
                    return 1.0
                if subcategory in {"sneakers", "loafers"}:
                    return 0.75
                return 0.4
            return 0.9 if subcategory not in WINTER_SHOE_TYPES else 0.5

        return 0.75

    def _score_bottom_weather_fit(self, bottom, weather_condition, temperature):
        if bottom is None:
            return 0.7

        subcategory = self._normalize_token(bottom.subcategory)
        normalized_weather = self._normalize_token(weather_condition)

        if temperature is not None and temperature <= 0 and subcategory in {"shorts", "mini_skirt"}:
            return 0.0
        if temperature is not None and temperature <= 10 and subcategory == "shorts":
            return 0.15
        if normalized_weather in {"snow", "rain"} and subcategory in {"shorts", "mini_skirt"}:
            return 0.25
        if temperature is not None and temperature >= 24 and subcategory in {"jeans", "joggers", "leggings"}:
            return 0.65

        return 1.0

    def _violates_hard_constraints(self, candidate, constraints):
        for constraint in constraints:
            if self._candidate_violates_constraint(candidate, constraint):
                return True
        return False

    def _candidate_violates_constraint(self, candidate, constraint):
        normalized_constraint = self._normalize_token(constraint)
        if not normalized_constraint:
            return False

        for entry in candidate:
            item = entry["item"]
            category = self._normalize_token(item.category)
            subcategory = self._normalize_token(item.subcategory)
            colors = set(self._normalize_tokens(item.colors or []))
            attributes = {
                category,
                subcategory,
                self._normalize_token(item.material),
                self._normalize_token(item.formality),
                self._normalize_token(getattr(item, "fit", None)),
                self._normalize_token(getattr(item, "layer_level", None)),
                "waterproof" if getattr(item, "waterproof", False) else None,
                "windproof" if getattr(item, "windproof", False) else None,
                *colors,
                *self._normalize_tokens(item.styles or []),
            }
            attributes.discard(None)

            if normalized_constraint in {"no_heels", "avoid_heels"}:
                if category == "shoes" and subcategory in {"heels", "high_heels", "pumps"}:
                    return True
            elif normalized_constraint in {"no_skirts", "avoid_skirts"}:
                if category == "bottom" and subcategory == "skirt":
                    return True
            elif normalized_constraint == "no_bright_colors":
                if colors & BRIGHT_COLORS:
                    return True
            elif normalized_constraint == "no_outerwear":
                if category == "outerwear":
                    return True
            elif normalized_constraint.startswith("no_"):
                if normalized_constraint[3:] in attributes:
                    return True
            elif normalized_constraint.startswith("avoid_"):
                if normalized_constraint[6:] in attributes:
                    return True
            elif normalized_constraint in attributes:
                return True

        return False

    def _candidate_has_attribute(self, candidate, attribute):
        normalized_attribute = self._normalize_token(attribute)
        for entry in candidate:
            item = entry["item"]
            tokens = {
                self._normalize_token(item.category),
                self._normalize_token(item.subcategory),
                self._normalize_token(item.material),
                self._normalize_token(item.formality),
                self._normalize_token(getattr(item, "fit", None)),
                self._normalize_token(getattr(item, "layer_level", None)),
                "waterproof" if getattr(item, "waterproof", False) else None,
                "windproof" if getattr(item, "windproof", False) else None,
                *self._normalize_tokens(item.colors or []),
                *self._normalize_tokens(item.styles or []),
            }
            tokens.discard(None)
            if normalized_attribute in tokens:
                return True
        return False
```

## backend\app\services\weather_service.py

```python
from datetime import datetime


class MockWeatherService:
    @staticmethod
    def get_current_weather(city=None):
        month = datetime.utcnow().month
        season = MockWeatherService._month_to_season(month)

        sample_weather = {
            "winter": {"temperature": -3, "weather_condition": "snow"},
            "spring": {"temperature": 12, "weather_condition": "clear"},
            "summer": {"temperature": 24, "weather_condition": "clear"},
            "autumn": {"temperature": 9, "weather_condition": "rain"},
        }

        weather = sample_weather[season]
        return {
            "city": city or "Тестовый город",
            "temperature": weather["temperature"],
            "weather_condition": weather["weather_condition"],
            "season": season,
            "source": "mock",
        }

    @staticmethod
    def _month_to_season(month):
        if month in {12, 1, 2}:
            return "winter"
        if month in {3, 4, 5}:
            return "spring"
        if month in {6, 7, 8}:
            return "summer"
        return "autumn"
```

## backend\app\utils\__init__.py

```python
# Utility helpers package.
```

## backend\app\utils\auth.py

```python
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
```

## backend\app\utils\errors.py

```python
class ApiError(Exception):
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details
```

## backend\app\utils\request.py

```python
from flask import request


def get_request_payload():
    if request.is_json:
        return request.get_json(silent=True) or {}
    if request.form:
        return request.form.to_dict(flat=True)
    return {}
```

## backend\app\utils\storage.py

```python
import os
import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

from .errors import ApiError


def save_image(file_storage, upload_folder, allowed_extensions):
    if not file_storage or not file_storage.filename:
        raise ApiError("Необходимо загрузить изображение.", 400)

    filename = secure_filename(file_storage.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in allowed_extensions:
        raise ApiError("Неподдерживаемый тип изображения.", 400)

    Path(upload_folder).mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.{extension}"
    file_path = Path(upload_folder) / stored_name
    file_storage.save(file_path)
    return f"/uploads/{stored_name}"


def remove_local_image(image_url, upload_folder):
    if not image_url or not image_url.startswith("/uploads/"):
        return

    filename = image_url.split("/uploads/", 1)[1]
    file_path = Path(upload_folder) / filename
    if file_path.exists() and file_path.is_file():
        os.remove(file_path)
```

## backend\migrations\env.py

```python
import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## backend\migrations\versions\8b1f7f3c9c2a_add_item_metadata_fields.py

```python
"""Add clothing item metadata fields

Revision ID: 8b1f7f3c9c2a
Revises: e93d24105967
Create Date: 2026-03-31 14:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8b1f7f3c9c2a"
down_revision = "e93d24105967"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("clothing_items", schema=None) as batch_op:
        batch_op.add_column(sa.Column("fit", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("layer_level", sa.String(length=50), nullable=True))
        batch_op.add_column(
            sa.Column(
                "insulation_rating",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "waterproof",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "windproof",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )


def downgrade():
    with op.batch_alter_table("clothing_items", schema=None) as batch_op:
        batch_op.drop_column("windproof")
        batch_op.drop_column("waterproof")
        batch_op.drop_column("insulation_rating")
        batch_op.drop_column("layer_level")
        batch_op.drop_column("fit")
```

## backend\migrations\versions\b1f4037c1f2a_add_outfit_presentation_fields.py

```python
"""Add saved outfit board fields

Revision ID: b7cf5f8d4a31
Revises: 8b1f7f3c9c2a
Create Date: 2026-03-31 18:20:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7cf5f8d4a31"
down_revision = "8b1f7f3c9c2a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("outfits", schema=None) as batch_op:
        batch_op.add_column(sa.Column("feature_scores", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("reasons", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("user_photo_url", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("outfits", schema=None) as batch_op:
        batch_op.drop_column("user_photo_url")
        batch_op.drop_column("reasons")
        batch_op.drop_column("feature_scores")
```

## backend\migrations\versions\e93d24105967_initial_schema.py

```python
"""Initial schema

Revision ID: e93d24105967
Revises: 
Create Date: 2026-03-16 15:58:02.440250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e93d24105967'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('city', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    op.create_table('clothing_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('image_url', sa.String(length=255), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('subcategory', sa.String(length=100), nullable=True),
    sa.Column('colors', sa.JSON(), nullable=False),
    sa.Column('styles', sa.JSON(), nullable=False),
    sa.Column('season', sa.String(length=50), nullable=False),
    sa.Column('formality', sa.String(length=50), nullable=False),
    sa.Column('material', sa.String(length=80), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('clothing_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_clothing_items_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_clothing_items_user_id'), ['user_id'], unique=False)

    op.create_table('outfits',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('event_type', sa.String(length=80), nullable=False),
    sa.Column('weather_context', sa.JSON(), nullable=True),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('outfits', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_outfits_user_id'), ['user_id'], unique=False)

    op.create_table('user_preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('preferred_styles', sa.JSON(), nullable=False),
    sa.Column('preferred_colors', sa.JSON(), nullable=False),
    sa.Column('constraints', sa.JSON(), nullable=False),
    sa.Column('disliked_items', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('outfit_feedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('outfit_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('reaction', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['outfit_id'], ['outfits.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('outfit_id', 'user_id', name='uq_outfit_feedback_user')
    )
    with op.batch_alter_table('outfit_feedback', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_outfit_feedback_outfit_id'), ['outfit_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_outfit_feedback_user_id'), ['user_id'], unique=False)

    op.create_table('outfit_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('outfit_id', sa.Integer(), nullable=False),
    sa.Column('clothing_item_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['clothing_item_id'], ['clothing_items.id'], ),
    sa.ForeignKeyConstraint(['outfit_id'], ['outfits.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('outfit_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_outfit_items_clothing_item_id'), ['clothing_item_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_outfit_items_outfit_id'), ['outfit_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('outfit_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_outfit_items_outfit_id'))
        batch_op.drop_index(batch_op.f('ix_outfit_items_clothing_item_id'))

    op.drop_table('outfit_items')
    with op.batch_alter_table('outfit_feedback', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_outfit_feedback_user_id'))
        batch_op.drop_index(batch_op.f('ix_outfit_feedback_outfit_id'))

    op.drop_table('outfit_feedback')
    op.drop_table('user_preferences')
    with op.batch_alter_table('outfits', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_outfits_user_id'))

    op.drop_table('outfits')
    with op.batch_alter_table('clothing_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_clothing_items_user_id'))
        batch_op.drop_index(batch_op.f('ix_clothing_items_category'))

    op.drop_table('clothing_items')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    # ### end Alembic commands ###
```

## backend\requirements.txt

```text
cryptography==44.0.3
Flask==3.1.0
Flask-Cors==5.0.0
Flask-JWT-Extended==4.6.0
Flask-Migrate==4.0.7
Flask-SQLAlchemy==3.1.1
PyMySQL==1.1.1
python-dotenv==1.0.1
```

## backend\run.py

```python
from app import create_app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=app.config["FLASK_RUN_HOST"],
        port=app.config["FLASK_RUN_PORT"],
        debug=app.config["DEBUG"],
    )
```

## backend\tests\__init__.py

```python
# Test package for backend recommendation engine.
```

## backend\tests\test_recommendation_engine.py

```python
import unittest
from dataclasses import dataclass
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.recommendation_engine import RecommendationEngine


@dataclass
class DummyItem:
    id: int
    title: str
    category: str
    subcategory: str
    colors: list
    styles: list
    season: str
    formality: str
    material: str
    fit: str | None = None
    layer_level: str | None = None
    insulation_rating: float = 0.0
    waterproof: bool = False
    windproof: bool = False
    image_url: str = "/uploads/placeholders/top.svg"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "subcategory": self.subcategory,
            "colors": self.colors,
            "styles": self.styles,
            "season": self.season,
            "formality": self.formality,
            "fit": self.fit,
            "layer_level": self.layer_level,
            "insulation_rating": self.insulation_rating,
            "waterproof": self.waterproof,
            "windproof": self.windproof,
            "material": self.material,
            "image_url": self.image_url,
        }


def build_item(
    item_id,
    title,
    category,
    subcategory,
    colors,
    styles,
    season,
    formality,
    **overrides,
):
    return DummyItem(
        id=item_id,
        title=title,
        category=category,
        subcategory=subcategory,
        colors=colors,
        styles=styles,
        season=season,
        formality=formality,
        material=overrides.pop("material", "cotton"),
        fit=overrides.pop("fit", None),
        layer_level=overrides.pop("layer_level", None),
        insulation_rating=overrides.pop("insulation_rating", 0.0),
        waterproof=overrides.pop("waterproof", False),
        windproof=overrides.pop("windproof", False),
        image_url=f"/uploads/placeholders/{category}.svg",
        **overrides,
    )


class RecommendationEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RecommendationEngine()
        self.request_context = {
            "event_type": "casual",
            "preferred_colors": ["white", "black", "beige"],
            "preferred_style": "minimal",
            "temperature": 12,
            "weather_condition": "cloudy",
            "anchor_item_id": None,
            "constraints": [],
            "season": "spring",
            "city": "Moscow",
        }

    def make_candidate(self, *entries):
        return [{"role": role, "item": item} for role, item in entries]

    def get_color_score(self, candidate, preferred_colors=None):
        request_context = {
            **self.request_context,
            "preferred_colors": preferred_colors
            if preferred_colors is not None
            else self.request_context["preferred_colors"],
        }
        return self.engine.score_color_harmony(candidate, request_context)

    def test_generate_candidate_outfits_builds_base_and_outerwear_variants(self):
        items = [
            build_item(1, "White tee", "top", "t-shirt", ["white"], ["casual"], "summer", "casual"),
            build_item(2, "Beige shirt", "top", "shirt", ["beige"], ["minimal"], "spring", "smart"),
            build_item(3, "Black jeans", "bottom", "jeans", ["black"], ["casual"], "all-season", "casual"),
            build_item(4, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual"),
            build_item(5, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart"),
        ]

        candidates = self.engine.generate_candidate_outfits(items, self.request_context)

        self.assertEqual(len(candidates), 4)
        self.assertTrue(any(len(candidate) == 3 for candidate in candidates))
        self.assertTrue(any(len(candidate) == 4 for candidate in candidates))

    def test_generate_returns_empty_when_required_categories_missing(self):
        items = [
            build_item(1, "White tee", "top", "t-shirt", ["white"], ["casual"], "summer", "casual"),
            build_item(2, "Black jeans", "bottom", "jeans", ["black"], ["casual"], "all-season", "casual"),
        ]

        results = self.engine.generate(items, self.request_context)

        self.assertEqual(results, [])

    def test_generate_returns_only_top_five_ranked_outfits(self):
        items = [
            build_item(1, "White tee", "top", "t-shirt", ["white"], ["casual"], "summer", "casual"),
            build_item(2, "Black tee", "top", "t-shirt", ["black"], ["casual"], "summer", "casual"),
            build_item(3, "Beige shirt", "top", "shirt", ["beige"], ["minimal"], "spring", "smart"),
            build_item(4, "Black jeans", "bottom", "jeans", ["black"], ["casual"], "all-season", "casual"),
            build_item(5, "Beige trousers", "bottom", "trousers", ["beige"], ["minimal"], "spring", "smart"),
            build_item(6, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual"),
            build_item(7, "Black boots", "shoes", "boots", ["black"], ["classic"], "autumn", "smart"),
            build_item(8, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart"),
            build_item(9, "Black coat", "outerwear", "coat", ["black"], ["minimal"], "winter", "formal"),
        ]

        results = self.engine.generate(items, self.request_context, limit=5)

        self.assertEqual(len(results), 5)
        self.assertGreaterEqual(results[0]["score"], results[-1]["score"])
        self.assertTrue(all("items" in outfit for outfit in results))

    def test_evaluate_outfit_returns_feature_scores_and_explanation(self):
        candidate = [
            {"role": "top", "item": build_item(1, "White tee", "top", "t-shirt", ["white"], ["minimal"], "summer", "casual")},
            {"role": "bottom", "item": build_item(2, "Black jeans", "bottom", "jeans", ["black"], ["casual"], "all-season", "casual")},
            {"role": "shoes", "item": build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual")},
            {"role": "outerwear", "item": build_item(4, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart")},
        ]

        outfit = self.engine.evaluate_outfit(candidate, self.request_context, {})

        self.assertEqual(len(outfit["feature_scores"]), 10)
        self.assertIn("reasons", outfit)
        self.assertIn("explanation", outfit)
        self.assertGreaterEqual(outfit["score"], 0.0)
        self.assertLessEqual(outfit["score"], 1.0)

    def test_generate_candidate_outfits_excludes_loafers_in_snow(self):
        cold_request_context = {
            **self.request_context,
            "temperature": -12,
            "weather_condition": "snow",
            "season": "winter",
        }
        items = [
            build_item(1, "Warm sweater", "top", "sweater", ["gray"], ["casual"], "winter", "casual"),
            build_item(2, "Blue jeans", "bottom", "jeans", ["blue"], ["casual"], "winter", "casual"),
            build_item(3, "Beige loafers", "shoes", "loafers", ["beige"], ["classic"], "spring", "smart"),
            build_item(4, "Black winter boots", "shoes", "winter_boots", ["black"], ["casual"], "winter", "casual"),
            build_item(5, "Black coat", "outerwear", "coat", ["black"], ["classic"], "winter", "formal"),
        ]

        candidates = self.engine.generate_candidate_outfits(items, cold_request_context)

        self.assertTrue(candidates)
        for candidate in candidates:
            shoes = next(entry["item"] for entry in candidate if entry["role"] == "shoes")
            roles = {entry["role"] for entry in candidate}
            self.assertNotEqual(shoes.subcategory, "loafers")
            self.assertIn("outerwear", roles)

    def test_generate_candidate_outfits_adds_accessory_variants(self):
        items = [
            build_item(1, "White tee", "top", "t-shirt", ["white"], ["casual"], "summer", "casual"),
            build_item(2, "Blue jeans", "bottom", "jeans", ["blue"], ["casual"], "all-season", "casual"),
            build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual"),
            build_item(4, "Black bag", "accessory", "bag", ["black"], ["minimal"], "all-season", "smart"),
        ]

        candidates = self.engine.generate_candidate_outfits(items, self.request_context)

        self.assertTrue(any("accessory" in {entry["role"] for entry in candidate} for candidate in candidates))
        self.assertTrue(any("accessory" not in {entry["role"] for entry in candidate} for candidate in candidates))

    def test_generate_candidate_outfits_filters_hoodie_for_office_event(self):
        office_request_context = {
            **self.request_context,
            "event_type": "office",
            "preferred_style": "classic",
        }
        items = [
            build_item(1, "Gray hoodie", "top", "hoodie", ["gray"], ["sport"], "spring", "casual"),
            build_item(2, "Blue shirt", "top", "shirt", ["blue"], ["classic"], "spring", "smart"),
            build_item(3, "Black trousers", "bottom", "trousers", ["black"], ["classic"], "spring", "smart"),
            build_item(4, "Black loafers", "shoes", "loafers", ["black"], ["classic"], "spring", "smart"),
        ]

        candidates = self.engine.generate_candidate_outfits(items, office_request_context)

        self.assertTrue(candidates)
        for candidate in candidates:
            top_item = next(entry["item"] for entry in candidate if entry["role"] == "top")
            self.assertNotEqual(top_item.subcategory, "hoodie")

    def test_weather_score_uses_explicit_protection_flags(self):
        rainy_context = {
            **self.request_context,
            "weather_condition": "rain",
            "temperature": 9,
        }
        protected_candidate = self.make_candidate(
            ("top", build_item(1, "White shirt", "top", "shirt", ["white"], ["classic"], "spring", "smart")),
            ("bottom", build_item(2, "Black trousers", "bottom", "trousers", ["black"], ["classic"], "spring", "smart")),
            ("shoes", build_item(3, "Black boots", "shoes", "boots", ["black"], ["classic"], "autumn", "smart")),
            ("outerwear", build_item(4, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart", waterproof=True, windproof=True)),
        )
        unprotected_candidate = self.make_candidate(
            ("top", build_item(5, "White shirt", "top", "shirt", ["white"], ["classic"], "spring", "smart")),
            ("bottom", build_item(6, "Black trousers", "bottom", "trousers", ["black"], ["classic"], "spring", "smart")),
            ("shoes", build_item(7, "Black boots", "shoes", "boots", ["black"], ["classic"], "autumn", "smart")),
            ("outerwear", build_item(8, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart")),
        )

        protected_score = self.engine.score_weather_condition_match(protected_candidate, rainy_context)
        unprotected_score = self.engine.score_weather_condition_match(unprotected_candidate, rainy_context)

        self.assertGreater(protected_score, unprotected_score)
        self.assertGreaterEqual(protected_score, 0.85)

    def test_temperature_score_uses_explicit_insulation_rating(self):
        winter_context = {
            **self.request_context,
            "temperature": -10,
            "weather_condition": "snow",
            "season": "winter",
        }
        warm_candidate = self.make_candidate(
            ("top", build_item(1, "Warm knit", "top", "sweater", ["gray"], ["casual"], "winter", "casual", insulation_rating=2.1, layer_level="mid")),
            ("bottom", build_item(2, "Warm trousers", "bottom", "trousers", ["black"], ["classic"], "winter", "smart", insulation_rating=1.6)),
            ("shoes", build_item(3, "Winter boots", "shoes", "winter_boots", ["black"], ["casual"], "winter", "casual", insulation_rating=2.2)),
            ("outerwear", build_item(4, "Parka", "outerwear", "parka", ["olive"], ["casual"], "winter", "casual", insulation_rating=2.8, layer_level="outer")),
        )
        cold_candidate = self.make_candidate(
            ("top", build_item(5, "Thin knit", "top", "sweater", ["gray"], ["casual"], "winter", "casual", insulation_rating=0.7, layer_level="base")),
            ("bottom", build_item(6, "Light trousers", "bottom", "trousers", ["black"], ["classic"], "winter", "smart", insulation_rating=0.5)),
            ("shoes", build_item(7, "Winter boots", "shoes", "winter_boots", ["black"], ["casual"], "winter", "casual", insulation_rating=0.8)),
            ("outerwear", build_item(8, "Parka", "outerwear", "parka", ["olive"], ["casual"], "winter", "casual", insulation_rating=1.0, layer_level="outer")),
        )

        warm_score = self.engine.score_temperature_match(warm_candidate, winter_context)
        cold_score = self.engine.score_temperature_match(cold_candidate, winter_context)

        self.assertGreater(warm_score, cold_score)
        self.assertGreaterEqual(warm_score, 0.85)

    def test_color_harmony_scores_all_neutral_outfit_high(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "White shirt", "top", "shirt", ["white"], ["minimal"], "spring", "smart")),
            ("bottom", build_item(2, "Black trousers", "bottom", "trousers", ["black"], ["minimal"], "spring", "smart")),
            ("shoes", build_item(3, "Beige loafers", "shoes", "loafers", ["beige"], ["classic"], "spring", "smart")),
            ("outerwear", build_item(4, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart")),
        )

        score = self.get_color_score(candidate, preferred_colors=["white", "black", "beige"])

        self.assertGreaterEqual(score, 0.84)

    def test_color_harmony_scores_neutral_base_with_one_accent_high(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Red knit", "top", "sweater", ["red"], ["minimal"], "autumn", "smart")),
            ("bottom", build_item(2, "Black trousers", "bottom", "trousers", ["black"], ["minimal"], "autumn", "smart")),
            ("shoes", build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["minimal"], "spring", "casual")),
            ("outerwear", build_item(4, "Beige coat", "outerwear", "coat", ["beige"], ["classic"], "autumn", "smart")),
        )

        score = self.get_color_score(candidate)

        self.assertGreaterEqual(score, 0.82)

    def test_color_harmony_scores_monochrome_blue_outfit_high(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Blue shirt", "top", "shirt", ["blue"], ["classic"], "spring", "smart")),
            ("bottom", build_item(2, "Navy trousers", "bottom", "trousers", ["navy"], ["classic"], "spring", "smart")),
            ("shoes", build_item(3, "Denim sneakers", "shoes", "sneakers", ["denim"], ["casual"], "spring", "casual")),
        )

        score = self.get_color_score(candidate, preferred_colors=["blue", "navy"])

        self.assertGreaterEqual(score, 0.83)

    def test_color_harmony_scores_analogous_palette_high(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Blue top", "top", "shirt", ["blue"], ["casual"], "spring", "casual")),
            ("bottom", build_item(2, "Teal skirt", "bottom", "skirt", ["teal"], ["casual"], "spring", "casual")),
            ("shoes", build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual")),
            ("accessory", build_item(4, "Green bag", "accessory", "bag", ["green"], ["casual"], "spring", "casual")),
        )

        score = self.get_color_score(candidate, preferred_colors=["blue", "teal"])

        self.assertGreaterEqual(score, 0.77)

    def test_color_harmony_scores_complementary_with_soft_accent_well(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Blue shirt", "top", "shirt", ["blue"], ["classic"], "spring", "smart")),
            ("bottom", build_item(2, "White trousers", "bottom", "trousers", ["white"], ["classic"], "spring", "smart")),
            ("shoes", build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual")),
            ("accessory", build_item(4, "Orange bag", "accessory", "bag", ["orange"], ["fashion"], "spring", "smart")),
        )

        score = self.get_color_score(candidate, preferred_colors=["blue", "orange"])

        self.assertGreaterEqual(score, 0.74)

    def test_color_harmony_penalizes_too_many_unrelated_bright_colors(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Red top", "top", "shirt", ["red"], ["fashion"], "spring", "smart")),
            ("bottom", build_item(2, "Green skirt", "bottom", "skirt", ["green"], ["fashion"], "spring", "smart")),
            ("shoes", build_item(3, "Yellow shoes", "shoes", "pumps", ["yellow"], ["fashion"], "spring", "smart")),
            ("outerwear", build_item(4, "Purple jacket", "outerwear", "jacket", ["purple"], ["fashion"], "spring", "smart")),
            ("accessory", build_item(5, "Teal bag", "accessory", "bag", ["teal"], ["fashion"], "spring", "smart")),
        )

        score = self.get_color_score(candidate, preferred_colors=[])

        self.assertLess(score, 0.55)

    def test_color_harmony_handles_neutral_shoes_and_metallic_accessory(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Cream knit", "top", "sweater", ["cream"], ["minimal"], "autumn", "smart")),
            ("bottom", build_item(2, "Taupe trousers", "bottom", "trousers", ["taupe"], ["minimal"], "autumn", "smart")),
            ("shoes", build_item(3, "Black boots", "shoes", "boots", ["black"], ["classic"], "autumn", "smart")),
            ("accessory", build_item(4, "Silver bag", "accessory", "bag", ["silver"], ["classic"], "autumn", "smart")),
        )

        score = self.get_color_score(candidate, preferred_colors=["cream", "taupe", "black"])

        self.assertGreaterEqual(score, 0.82)

    def test_preferred_colors_help_but_do_not_hide_bad_harmony(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Red top", "top", "shirt", ["red"], ["fashion"], "spring", "smart")),
            ("bottom", build_item(2, "Green skirt", "bottom", "skirt", ["green"], ["fashion"], "spring", "smart")),
            ("shoes", build_item(3, "Yellow shoes", "shoes", "pumps", ["yellow"], ["fashion"], "spring", "smart")),
            ("outerwear", build_item(4, "Purple jacket", "outerwear", "jacket", ["purple"], ["fashion"], "spring", "smart")),
        )

        base_score = self.get_color_score(candidate, preferred_colors=[])
        preferred_score = self.get_color_score(
            candidate,
            preferred_colors=["red", "green", "yellow", "purple"],
        )

        self.assertGreater(preferred_score, base_score)
        self.assertLess(preferred_score, 0.8)

    def test_color_harmony_handles_unknown_colors_without_crashing(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Mystic top", "top", "shirt", ["mystic haze"], ["casual"], "spring", "casual")),
            ("bottom", build_item(2, "Dusty bottom", "bottom", "trousers", ["dust storm"], ["casual"], "spring", "casual")),
            ("shoes", build_item(3, "White shoes", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual")),
        )

        score = self.get_color_score(candidate, preferred_colors=["white"])

        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
```

## frontend\package.json

```json
{
  "name": "wardrobe-mvp-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.30.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^5.4.11"
  }
}
```

## frontend\src\api\analyticsApi.js

```javascript
import { apiFetch } from "./client";


export function fetchAnalyticsSummary(token) {
  return apiFetch("/analytics/summary", {
    token,
  });
}
```

## frontend\src\api\authApi.js

```javascript
import { apiFetch } from "./client";


export function registerUser(payload) {
  return apiFetch("/auth/register", {
    method: "POST",
    body: payload,
  });
}


export function loginUser(payload) {
  return apiFetch("/auth/login", {
    method: "POST",
    body: payload,
  });
}


export function fetchCurrentUser(token) {
  return apiFetch("/auth/me", {
    token,
  });
}
```

## frontend\src\api\client.js

```javascript
export const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const PLACEHOLDER_BY_CATEGORY = {
  top: "/uploads/placeholders/top.svg",
  bottom: "/uploads/placeholders/bottom.svg",
  shoes: "/uploads/placeholders/shoes.svg",
  outerwear: "/uploads/placeholders/outerwear.svg",
  accessory: "/uploads/placeholders/accessory.svg",
};


export async function apiFetch(path, options = {}) {
  const {
    method = "GET",
    token,
    body,
    isFormData = false,
  } = options;

  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body
      ? isFormData
        ? body
        : JSON.stringify(body)
      : undefined,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "Не удалось выполнить запрос.");
  }

  return payload;
}


export function resolveAssetUrl(assetPath) {
  if (!assetPath) {
    return null;
  }
  if (assetPath.startsWith("http://") || assetPath.startsWith("https://")) {
    return assetPath;
  }

  const assetBaseUrl = API_URL.replace(/\/api$/, "");
  return `${assetBaseUrl}${assetPath}`;
}


export function getCategoryPlaceholderUrl(category = "top") {
  const normalizedCategory = String(category || "top").toLowerCase();
  return resolveAssetUrl(
    PLACEHOLDER_BY_CATEGORY[normalizedCategory] || PLACEHOLDER_BY_CATEGORY.top,
  );
}


export function resolveItemImageUrl(item, fallbackCategory) {
  if (item?.image_url) {
    return resolveAssetUrl(item.image_url);
  }

  return getCategoryPlaceholderUrl(item?.category || fallbackCategory);
}
```

## frontend\src\api\itemsApi.js

```javascript
import { apiFetch } from "./client";


export function fetchItems(token) {
  return apiFetch("/items", { token });
}


export function fetchItemById(token, itemId) {
  return apiFetch(`/items/${itemId}`, { token });
}


export function createItem(token, formData) {
  return apiFetch("/items", {
    method: "POST",
    token,
    body: formData,
    isFormData: true,
  });
}


export function updateItem(token, itemId, formData) {
  return apiFetch(`/items/${itemId}`, {
    method: "PUT",
    token,
    body: formData,
    isFormData: true,
  });
}


export function deleteItem(token, itemId) {
  return apiFetch(`/items/${itemId}`, {
    method: "DELETE",
    token,
  });
}
```

## frontend\src\api\outfitsApi.js

```javascript
import { apiFetch } from "./client";


export function generateOutfits(token, payload) {
  return apiFetch("/outfits/generate", {
    method: "POST",
    token,
    body: payload,
  });
}


export function fetchSavedOutfits(token) {
  return apiFetch("/outfits", {
    token,
  });
}


export function saveOutfit(token, payload) {
  return apiFetch("/outfits", {
    method: "POST",
    token,
    body: payload,
  });
}


export function uploadOutfitPhoto(token, outfitId, formData) {
  return apiFetch(`/outfits/${outfitId}/photo`, {
    method: "POST",
    token,
    body: formData,
    isFormData: true,
  });
}


export function sendOutfitFeedback(token, outfitId, reaction) {
  return apiFetch(`/outfits/${outfitId}/feedback`, {
    method: "POST",
    token,
    body: { reaction },
  });
}
```

## frontend\src\App.jsx

```jsx
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import GuestRoute from "./components/GuestRoute";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import AddClothingItemPage from "./pages/AddClothingItemPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import ClothingItemDetailsPage from "./pages/ClothingItemDetailsPage";
import DashboardPage from "./pages/DashboardPage";
import EditClothingItemPage from "./pages/EditClothingItemPage";
import LoginPage from "./pages/LoginPage";
import OutfitGeneratorPage from "./pages/OutfitGeneratorPage";
import RegisterPage from "./pages/RegisterPage";
import SavedOutfitsPage from "./pages/SavedOutfitsPage";
import WardrobePage from "./pages/WardrobePage";


function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route
            path="/login"
            element={
              <GuestRoute>
                <LoginPage />
              </GuestRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestRoute>
                <RegisterPage />
              </GuestRoute>
            }
          />

          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/wardrobe" element={<WardrobePage />} />
              <Route path="/wardrobe/add" element={<AddClothingItemPage />} />
              <Route path="/wardrobe/:itemId" element={<ClothingItemDetailsPage />} />
              <Route path="/wardrobe/:itemId/edit" element={<EditClothingItemPage />} />
              <Route path="/generate" element={<OutfitGeneratorPage />} />
              <Route path="/outfits" element={<SavedOutfitsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}


export default App;
```

## frontend\src\components\ClothingItemForm.jsx

```jsx
import { useEffect, useState } from "react";

import { resolveAssetUrl } from "../api/client";
import {
  CATEGORY_OPTIONS,
  COLOR_OPTIONS,
  FIT_OPTIONS,
  INSULATION_OPTIONS,
  LAYER_LEVEL_OPTIONS,
  STYLE_OPTIONS,
  getDefaultFitValue,
  getDefaultInsulationValue,
  getDefaultLayerLevelValue,
  getDefaultProtectionFlags,
  getSubcategoryLabel,
  getSubcategoryOptions,
  normalizeCatalogValue,
} from "../data/clothingOptions";
import {
  translateLayerLevel,
  translateFormality,
  translateFit,
  translateSeason,
} from "../utils/i18n";


const EMPTY_FORM = {
  title: "",
  category: "top",
  subcategory: "",
  colors: [],
  styles: [],
  season: "all-season",
  formality: "casual",
  fit: "balanced",
  layer_level: "base",
  insulation_rating: "0.6",
  waterproof: false,
  windproof: false,
  image_url: "",
};


function buildDefaultMetadata(category, subcategory) {
  const fit = getDefaultFitValue(subcategory);
  const layerLevel = getDefaultLayerLevelValue(subcategory, category);
  const insulationRating = getDefaultInsulationValue(subcategory);
  const protectionFlags = getDefaultProtectionFlags(subcategory);

  return {
    fit,
    layer_level: layerLevel,
    insulation_rating: insulationRating,
    waterproof: protectionFlags.waterproof,
    windproof: protectionFlags.windproof,
  };
}


function mapInitialValues(initialValues) {
  if (!initialValues) {
    return { ...EMPTY_FORM };
  }

  const category = normalizeCatalogValue(initialValues.category) || "top";
  const subcategory = normalizeCatalogValue(initialValues.subcategory);
  const defaultMetadata = buildDefaultMetadata(category, subcategory);

  return {
    title: initialValues.title || "",
    category,
    subcategory,
    colors: (initialValues.colors || []).map(normalizeCatalogValue),
    styles: (initialValues.styles || []).map(normalizeCatalogValue),
    season: initialValues.season || "all-season",
    formality: initialValues.formality || "casual",
    fit: initialValues.fit || defaultMetadata.fit,
    layer_level: initialValues.layer_level || defaultMetadata.layer_level,
    insulation_rating: String(
      initialValues.insulation_rating ?? defaultMetadata.insulation_rating,
    ),
    waterproof: Boolean(initialValues.waterproof ?? defaultMetadata.waterproof),
    windproof: Boolean(initialValues.windproof ?? defaultMetadata.windproof),
    image_url: initialValues.image_url || "",
  };
}


function toggleArrayValue(currentValues, value) {
  if (currentValues.includes(value)) {
    return currentValues.filter((entry) => entry !== value);
  }

  return [...currentValues, value];
}


export default function ClothingItemForm({
  initialValues,
  onSubmit,
  submitLabel,
  loading,
}) {
  const [formValues, setFormValues] = useState(mapInitialValues(initialValues));
  const [imageFile, setImageFile] = useState(null);

  useEffect(() => {
    setFormValues(mapInitialValues(initialValues));
    setImageFile(null);
  }, [initialValues]);

  const availableSubcategories = getSubcategoryOptions(formValues.category);

  function handleChange(event) {
    const { name, type, value, checked } = event.target;

    if (name === "category") {
      const normalizedCategory = normalizeCatalogValue(value);
      const nextSubcategories = getSubcategoryOptions(normalizedCategory);
      const currentSubcategory = normalizeCatalogValue(formValues.subcategory);
      const hasCurrentSubcategory = nextSubcategories.some(
        (entry) => entry.value === currentSubcategory,
      );

      setFormValues((currentValues) => ({
        ...currentValues,
        category: normalizedCategory,
        subcategory: hasCurrentSubcategory ? currentSubcategory : "",
        ...(hasCurrentSubcategory
          ? buildDefaultMetadata(normalizedCategory, currentSubcategory)
          : buildDefaultMetadata(normalizedCategory, "")),
      }));
      return;
    }

    if (name === "subcategory") {
      const normalizedSubcategory = normalizeCatalogValue(value);
      const defaultMetadata = buildDefaultMetadata(
        formValues.category,
        normalizedSubcategory,
      );

      setFormValues((currentValues) => ({
        ...currentValues,
        subcategory: normalizedSubcategory,
        ...defaultMetadata,
      }));
      return;
    }

    setFormValues((currentValues) => ({
      ...currentValues,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleToggle(fieldName, value) {
    const normalizedValue = normalizeCatalogValue(value);

    setFormValues((currentValues) => ({
      ...currentValues,
      [fieldName]: toggleArrayValue(currentValues[fieldName], normalizedValue),
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append("title", formValues.title);
    formData.append("category", formValues.category);
    formData.append("subcategory", formValues.subcategory);
    formData.append("colors", JSON.stringify(formValues.colors));
    formData.append("styles", JSON.stringify(formValues.styles));
    formData.append("season", formValues.season);
    formData.append("formality", formValues.formality);
    formData.append("fit", formValues.fit);
    formData.append("layer_level", formValues.layer_level);
    formData.append("insulation_rating", formValues.insulation_rating);
    formData.append("waterproof", String(formValues.waterproof));
    formData.append("windproof", String(formValues.windproof));
    formData.append("material", "");

    if (formValues.image_url) {
      formData.append("image_url", formValues.image_url);
    }

    if (imageFile) {
      formData.append("image", imageFile);
    }

    await onSubmit(formData);
  }

  return (
    <form className="card form-card" onSubmit={handleSubmit}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Гардероб</p>
          <h2>{submitLabel}</h2>
        </div>
        <p className="muted-text">
          Основные характеристики выбираются из каталога, чтобы сервису было проще
          собирать подходящие образы.
        </p>
      </div>

      <div className="form-grid">
        <label>
          Название
          <input
            className="input"
            name="title"
            value={formValues.title}
            onChange={handleChange}
            placeholder="Белая рубашка"
            required
          />
        </label>

        <label>
          Категория
          <select
            className="input"
            name="category"
            value={formValues.category}
            onChange={handleChange}
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Подкатегория
          <select
            className="input"
            name="subcategory"
            value={formValues.subcategory}
            onChange={handleChange}
            required
          >
            <option value="">Выберите подкатегорию</option>
            {availableSubcategories.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Сезон
          <select
            className="input"
            name="season"
            value={formValues.season}
            onChange={handleChange}
          >
            <option value="all-season">{translateSeason("all-season")}</option>
            <option value="spring">{translateSeason("spring")}</option>
            <option value="summer">{translateSeason("summer")}</option>
            <option value="autumn">{translateSeason("autumn")}</option>
            <option value="winter">{translateSeason("winter")}</option>
          </select>
        </label>

        <label>
          Формальность
          <select
            className="input"
            name="formality"
            value={formValues.formality}
            onChange={handleChange}
          >
            <option value="casual">{translateFormality("casual")}</option>
            <option value="smart">{translateFormality("smart")}</option>
            <option value="formal">{translateFormality("formal")}</option>
          </select>
        </label>

        <label>
          Посадка и силуэт
          <select
            className="input"
            name="fit"
            value={formValues.fit}
            onChange={handleChange}
          >
            {FIT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Роль в слоистости
          <select
            className="input"
            name="layer_level"
            value={formValues.layer_level}
            onChange={handleChange}
          >
            {LAYER_LEVEL_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Уровень утепления
          <select
            className="input"
            name="insulation_rating"
            value={formValues.insulation_rating}
            onChange={handleChange}
          >
            {INSULATION_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <div className="field-block">
          <div className="field-heading">
            <span className="field-label">Защитные свойства</span>
            <span className="field-helper">
              Отметьте, если вещь реально защищает от дождя или ветра.
            </span>
          </div>
          <div className="chip-grid">
            <label className={formValues.waterproof ? "chip-button is-selected" : "chip-button"}>
              <input
                type="checkbox"
                name="waterproof"
                checked={formValues.waterproof}
                onChange={handleChange}
                hidden
              />
              Защита от дождя
            </label>
            <label className={formValues.windproof ? "chip-button is-selected" : "chip-button"}>
              <input
                type="checkbox"
                name="windproof"
                checked={formValues.windproof}
                onChange={handleChange}
                hidden
              />
              Защита от ветра
            </label>
          </div>
        </div>

        <div className="field-block full-width">
          <div className="field-heading">
            <span className="field-label">Цвета</span>
            <span className="field-helper">Можно выбрать несколько базовых цветов.</span>
          </div>
          <div className="color-picker-grid">
            {COLOR_OPTIONS.map((option) => {
              const selected = formValues.colors.includes(option.value);
              return (
                <button
                  key={option.value}
                  type="button"
                  className={selected ? "color-swatch is-selected" : "color-swatch"}
                  onClick={() => handleToggle("colors", option.value)}
                >
                  <span
                    className="color-dot"
                    style={{
                      backgroundColor: option.hex,
                      borderColor: option.border,
                    }}
                  />
                  <span>{option.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="field-block full-width">
          <div className="field-heading">
            <span className="field-label">Стили</span>
            <span className="field-helper">Выберите один или несколько подходящих стилей.</span>
          </div>
          <div className="chip-grid">
            {STYLE_OPTIONS.map((option) => {
              const selected = formValues.styles.includes(option.value);
              return (
                <button
                  key={option.value}
                  type="button"
                  className={selected ? "chip-button is-selected" : "chip-button"}
                  onClick={() => handleToggle("styles", option.value)}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <label className="file-input-wrapper full-width">
          Изображение вещи
          <input
            className="input"
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            onChange={(event) => setImageFile(event.target.files?.[0] || null)}
          />
        </label>
      </div>

      {formValues.image_url ? (
        <div className="inline-media">
          <img
            src={resolveAssetUrl(formValues.image_url)}
            alt={formValues.title}
            className="inline-thumbnail"
          />
          <p className="muted-text">
            Текущее изображение сохранится, если не загружать новое. Подкатегория:{" "}
            {getSubcategoryLabel(formValues.subcategory)}. Посадка:{" "}
            {translateFit(formValues.fit)}. Слой:{" "}
            {translateLayerLevel(formValues.layer_level)}.
          </p>
        </div>
      ) : null}

      <button type="submit" className="primary-button" disabled={loading}>
        {loading ? "Сохранение..." : submitLabel}
      </button>
    </form>
  );
}
```

## frontend\src\components\GuestRoute.jsx

```jsx
import { Navigate } from "react-router-dom";

import useAuth from "../hooks/useAuth";


export default function GuestRoute({ children }) {
  const { token, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="page-shell">
        <div className="card centered-card">Загрузка приложения...</div>
      </div>
    );
  }

  if (token && user) {
    return <Navigate to="/" replace />;
  }

  return children;
}
```

## frontend\src\components\Layout.jsx

```jsx
import { Link, Outlet } from "react-router-dom";

import useAuth from "../hooks/useAuth";
import NavBar from "./NavBar";


export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <NavBar />

      <main className="content-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Авторизация</p>
            <h2 className="page-title">{user?.name || "Пользователь"}</h2>
            <p className="muted-text">
              {user?.email}
              {user?.city ? ` | ${user.city}` : ""}
            </p>
          </div>

          <div className="topbar-actions">
            <Link to="/wardrobe/add" className="secondary-button">
              Добавить вещь
            </Link>
            <button type="button" className="ghost-button" onClick={logout}>
              Выйти
            </button>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
```

## frontend\src\components\NavBar.jsx

```jsx
import { NavLink } from "react-router-dom";


const NAV_ITEMS = [
  { to: "/", label: "Главная" },
  { to: "/wardrobe", label: "Гардероб" },
  { to: "/generate", label: "Подбор образов" },
  { to: "/outfits", label: "Сохранённые образы" },
  { to: "/analytics", label: "Аналитика" },
];


export default function NavBar() {
  return (
    <nav className="nav-panel">
      <div>
        <p className="eyebrow">Цифровой гардероб</p>
        <h1 className="nav-title">Сервис подбора образов</h1>
      </div>

      <div className="nav-links">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              isActive ? "nav-link nav-link-active" : "nav-link"
            }
          >
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
```

## frontend\src\components\OutfitCard.jsx

```jsx
import { useMemo, useRef } from "react";
import { Link } from "react-router-dom";

import {
  getCategoryPlaceholderUrl,
  resolveAssetUrl,
  resolveItemImageUrl,
} from "../api/client";
import { translateEventType, translateRole, translateWeather } from "../utils/i18n";

const ROLE_ORDER = ["outerwear", "top", "bottom", "shoes", "accessory"];

function getRoleSortIndex(role) {
  const index = ROLE_ORDER.indexOf(String(role || "").toLowerCase());
  return index === -1 ? ROLE_ORDER.length : index;
}

function buildPhotoEntry(outfit) {
  if (!outfit?.styled_photo_url) {
    return null;
  }

  return {
    type: "photo",
    key: `photo-${outfit.id || outfit.name || "outfit"}`,
    imageUrl: resolveAssetUrl(outfit.styled_photo_url),
    title: "Вы в образе",
  };
}

function renderBoardCard(entry, slotName) {
  if (!entry) {
    return null;
  }

  if (entry.type === "photo") {
    return (
      <div key={entry.key} className="board-card board-card-photo">
        <img
          src={entry.imageUrl}
          alt={entry.title}
          className="board-card-image"
          onError={(event) => {
            event.currentTarget.style.display = "none";
          }}
        />
        <div className="board-card-caption">
          <span>Фото</span>
          <strong>{entry.title}</strong>
        </div>
      </div>
    );
  }

  const clothingItem = entry?.clothing_item || entry || {};
  const itemId = entry?.clothing_item_id || clothingItem.id;
  const itemRole = entry?.role || clothingItem.category || slotName;

  return (
    <Link
      key={`${slotName}-${itemId || clothingItem.title || "item"}`}
      to={itemId ? `/wardrobe/${itemId}` : "/wardrobe"}
      className="board-card"
    >
      <img
        src={resolveItemImageUrl(clothingItem, itemRole)}
        alt={clothingItem.title || itemRole}
        className="board-card-image"
        onError={(event) => {
          event.currentTarget.src = getCategoryPlaceholderUrl(
            clothingItem.category || itemRole,
          );
        }}
      />
      <div className="board-card-caption">
        <span>{translateRole(itemRole)}</span>
        <strong>{clothingItem.title || "Вещь"}</strong>
      </div>
    </Link>
  );
}

export default function OutfitCard({
  outfit,
  onSave,
  isSaved,
  onPhotoUpload,
  isUploadingPhoto,
  boardBadge,
  onPrevious,
  onNext,
  onClose,
}) {
  const uploadInputRef = useRef(null);

  const roleMap = useMemo(() => {
    const sortedItems = [...(outfit.items || [])].sort((leftEntry, rightEntry) => {
      const leftRole = leftEntry.role || leftEntry.clothing_item?.category;
      const rightRole = rightEntry.role || rightEntry.clothing_item?.category;
      return getRoleSortIndex(leftRole) - getRoleSortIndex(rightRole);
    });

    return sortedItems.reduce((accumulator, entry) => {
      const role = entry.role || entry.clothing_item?.category || "item";
      if (!accumulator[role]) {
        accumulator[role] = entry;
      }
      return accumulator;
    }, {});
  }, [outfit.items]);

  const boardEntries = useMemo(() => {
    const photoEntry = buildPhotoEntry(outfit);

    return [
      roleMap.outerwear ? { key: "outerwear", slotName: "outerwear", entry: roleMap.outerwear } : null,
      roleMap.top ? { key: "top", slotName: "top", entry: roleMap.top } : null,
      roleMap.accessory ? { key: "accessory", slotName: "accessory", entry: roleMap.accessory } : null,
      roleMap.bottom ? { key: "bottom", slotName: "bottom", entry: roleMap.bottom } : null,
      roleMap.shoes ? { key: "shoes", slotName: "shoes", entry: roleMap.shoes } : null,
      photoEntry ? { key: "photo", slotName: "photo", entry: photoEntry } : null,
    ].filter(Boolean);
  }, [outfit, roleMap]);

  const boardRows = useMemo(() => {
    if (boardEntries.length <= 3) {
      return [boardEntries];
    }

    if (boardEntries.length === 4) {
      return [boardEntries.slice(0, 2), boardEntries.slice(2)];
    }

    return [boardEntries.slice(0, 3), boardEntries.slice(3)];
  }, [boardEntries]);

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      onClose?.();
    }
  }

  function handlePhotoButtonClick() {
    uploadInputRef.current?.click();
  }

  function handlePhotoChange(event) {
    const file = event.target.files?.[0];
    if (!file || !onPhotoUpload || !outfit.id) {
      return;
    }

    onPhotoUpload(outfit.id, file);
    event.target.value = "";
  }

  return (
    <div className="outfit-modal-backdrop" onClick={handleBackdropClick}>
      <article className="outfit-modal-window">
        <div className="outfit-modal-top-actions">
          <button
            type="button"
            className={`favorite-button ${isSaved ? "is-active" : ""}`}
            onClick={() => onSave?.(outfit)}
            disabled={!onSave || isSaved}
            aria-label={isSaved ? "Образ уже в избранном" : "Сохранить образ в избранное"}
            title={isSaved ? "Уже в избранном" : "Сохранить в избранное"}
          >
            {isSaved ? "♥" : "♡"}
          </button>
          <button
            type="button"
            className="modal-close-button"
            onClick={onClose}
            aria-label="Закрыть просмотр"
          >
            ×
          </button>
        </div>

        <div className="outfit-modal-bottom-actions">
          <button
            type="button"
            className="arrow-button"
            onClick={onPrevious}
            aria-label="Предыдущий образ"
          >
            ←
          </button>
          <button
            type="button"
            className="arrow-button"
            onClick={onNext}
            aria-label="Следующий образ"
          >
            →
          </button>
        </div>

        <div className="outfit-modal-content">
          <section className="outfit-modal-left">
            <div className="outfit-board-canvas">
              {boardBadge ? (
                <div className="board-meta-strip">
                  <div className="board-index-chip">{boardBadge}</div>
                </div>
              ) : null}

              <div className={`board-grid board-grid-count-${boardEntries.length || 0}`}>
                {boardRows.map((row, rowIndex) => (
                  <div
                    key={`row-${rowIndex}`}
                    className={`board-row board-row-${row.length} ${
                      rowIndex === 0 ? "board-row-top" : "board-row-bottom"
                    }`}
                  >
                    {row.map(({ key, slotName, entry }) => (
                      <div
                        key={key}
                        className={`board-slot board-slot-${slotName} board-slot-active`}
                      >
                        {renderBoardCard(entry, slotName)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </section>

          <aside className="outfit-modal-sidebar">
            <div className="outfit-side-copy">
              <p className="eyebrow">Разбор образа</p>
              <h2>{outfit.name || "Собранный образ"}</h2>
              <p className="outfit-board-context">
                {translateEventType(outfit.event_type) || "Образ"}
                {outfit.weather_context?.temperature !== undefined &&
                outfit.weather_context?.temperature !== null
                  ? ` • ${outfit.weather_context.temperature}°C`
                  : ""}
                {outfit.weather_context?.weather_condition
                  ? ` • ${translateWeather(outfit.weather_context.weather_condition)}`
                  : ""}
              </p>
            </div>

            <div className="outfit-summary-card">
              <div className="score-ring">
                <strong>{Number(outfit.score || 0).toFixed(2)}</strong>
                <span>Итоговая оценка</span>
              </div>

              <p className="outfit-summary-text">{outfit.explanation}</p>
            </div>

            <div className="outfit-comments-list">
              {(outfit.reasons || []).map((reason) => (
                <div key={reason} className="outfit-comment-pill">
                  {reason}
                </div>
              ))}
            </div>

            {outfit.id && onPhotoUpload ? (
              <div className="outfit-photo-actions">
                <input
                  ref={uploadInputRef}
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={handlePhotoChange}
                />
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handlePhotoButtonClick}
                  disabled={isUploadingPhoto}
                >
                  {isUploadingPhoto
                    ? "Загрузка фото..."
                    : outfit.styled_photo_url
                      ? "Обновить фото в образе"
                      : "Добавить своё фото к образу"}
                </button>
                <p className="muted-text">
                  После сохранения можно добавить фото себя в этом образе.
                </p>
              </div>
            ) : null}
          </aside>
        </div>
      </article>
    </div>
  );
}
```

## frontend\src\components\ProtectedRoute.jsx

```jsx
import { Navigate, Outlet, useLocation } from "react-router-dom";

import useAuth from "../hooks/useAuth";


export default function ProtectedRoute() {
  const { token, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="page-shell">
        <div className="card centered-card">Загрузка приложения...</div>
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
```

## frontend\src\components\StatCard.jsx

```jsx
export default function StatCard({ label, value, helpText }) {
  return (
    <article className="stat-card">
      <p className="eyebrow">{label}</p>
      <h3>{value}</h3>
      {helpText ? <p className="muted-text">{helpText}</p> : null}
    </article>
  );
}
```

## frontend\src\context\AuthContext.jsx

```jsx
import { createContext, useEffect, useState } from "react";

import { fetchCurrentUser, loginUser, registerUser } from "../api/authApi";


const STORAGE_KEY = "wardrobe_access_token";

export const AuthContext = createContext(null);


export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem(STORAGE_KEY)));

  useEffect(() => {
    async function loadProfile() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetchCurrentUser(token);
        setUser(response.user);
      } catch (_error) {
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, [token]);

  async function login(credentials) {
    const response = await loginUser(credentials);
    localStorage.setItem(STORAGE_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    return response;
  }

  async function register(payload) {
    const response = await registerUser(payload);
    localStorage.setItem(STORAGE_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    return response;
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  async function refreshProfile() {
    if (!token) {
      return null;
    }
    const response = await fetchCurrentUser(token);
    setUser(response.user);
    return response.user;
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
```

## frontend\src\data\clothingOptions.js

```javascript
const normalizeValue = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .replace(/-/g, "_")
    .replace(/\s+/g, "_");

export const CATEGORY_OPTIONS = [
  { value: "top", label: "Верх" },
  { value: "bottom", label: "Низ" },
  { value: "shoes", label: "Обувь" },
  { value: "outerwear", label: "Верхний слой" },
  { value: "accessory", label: "Аксессуар" },
];

export const SUBCATEGORY_OPTIONS = {
  top: [
    { value: "t_shirt", label: "Футболка" },
    { value: "shirt", label: "Рубашка" },
    { value: "blouse", label: "Блузка" },
    { value: "polo", label: "Поло" },
    { value: "longsleeve", label: "Лонгслив" },
    { value: "sweater", label: "Свитер" },
    { value: "hoodie", label: "Худи" },
    { value: "cardigan", label: "Кардиган" },
    { value: "turtleneck", label: "Водолазка" },
    { value: "sweatshirt", label: "Свитшот" },
    { value: "vest", label: "Жилет" },
    { value: "crop_top", label: "Кроп-топ" },
  ],
  bottom: [
    { value: "jeans", label: "Джинсы" },
    { value: "trousers", label: "Брюки" },
    { value: "chinos", label: "Чиносы" },
    { value: "joggers", label: "Джоггеры" },
    { value: "leggings", label: "Леггинсы" },
    { value: "culottes", label: "Кюлоты" },
    { value: "skirt", label: "Юбка" },
    { value: "mini_skirt", label: "Мини-юбка" },
    { value: "midi_skirt", label: "Миди-юбка" },
    { value: "maxi_skirt", label: "Макси-юбка" },
    { value: "shorts", label: "Шорты" },
  ],
  shoes: [
    { value: "winter_boots", label: "Зимние сапоги" },
    { value: "felt_boots", label: "Валенки" },
    { value: "warm_boots", label: "Теплые ботинки" },
    { value: "demi_boots", label: "Демисезонные ботинки" },
    { value: "ankle_boots", label: "Ботильоны" },
    { value: "boots", label: "Ботинки" },
    { value: "closed_shoes", label: "Закрытые туфли" },
    { value: "pumps", label: "Туфли" },
    { value: "loafers", label: "Лоферы" },
    { value: "sneakers", label: "Кроссовки" },
    { value: "summer_sneakers", label: "Летние кроссовки" },
    { value: "sandals", label: "Босоножки" },
    { value: "espadrilles", label: "Эспадрильи" },
    { value: "flip_flops", label: "Шлепки" },
    { value: "slippers", label: "Сланцы" },
  ],
  outerwear: [
    { value: "coat", label: "Пальто" },
    { value: "jacket", label: "Куртка" },
    { value: "parka", label: "Парка" },
    { value: "down_jacket", label: "Пуховик" },
    { value: "trench", label: "Тренч" },
    { value: "blazer", label: "Пиджак" },
    { value: "leather_jacket", label: "Кожаная куртка" },
    { value: "windbreaker", label: "Ветровка" },
    { value: "vest_outerwear", label: "Жилет" },
  ],
  accessory: [
    { value: "bag", label: "Сумка" },
    { value: "backpack", label: "Рюкзак" },
    { value: "scarf", label: "Шарф" },
    { value: "hat", label: "Шапка" },
    { value: "cap", label: "Кепка" },
    { value: "gloves", label: "Перчатки" },
    { value: "belt", label: "Ремень" },
    { value: "jewelry", label: "Украшение" },
  ],
};

export const STYLE_OPTIONS = [
  { value: "basic", label: "Базовый" },
  { value: "minimal", label: "Минимализм" },
  { value: "casual", label: "Повседневный" },
  { value: "classic", label: "Классика" },
  { value: "business", label: "Деловой" },
  { value: "sport", label: "Спортивный" },
  { value: "athleisure", label: "Спорт-шик" },
  { value: "street", label: "Стритстайл" },
  { value: "romantic", label: "Романтичный" },
  { value: "evening", label: "Вечерний" },
  { value: "party", label: "Для вечеринки" },
  { value: "fashion", label: "Трендовый" },
  { value: "statement", label: "Акцентный" },
  { value: "boho", label: "Бохо" },
];

export const COLOR_OPTIONS = [
  { value: "white", label: "Белый", hex: "#f6f3ec", border: "#d8d2c7" },
  { value: "cream", label: "Кремовый", hex: "#f3e8d8", border: "#dbcab1" },
  { value: "black", label: "Черный", hex: "#171717", border: "#171717" },
  { value: "silver", label: "Серебристый", hex: "#c8ccd6", border: "#aeb5c1" },
  { value: "gray", label: "Серый", hex: "#8d939b", border: "#7b8188" },
  { value: "beige", label: "Бежевый", hex: "#dcc7a1", border: "#c2ab82" },
  { value: "camel", label: "Кэмел", hex: "#b78753", border: "#9e7141" },
  { value: "brown", label: "Коричневый", hex: "#8b5a3c", border: "#6d442c" },
  { value: "blue", label: "Синий", hex: "#4c84d9", border: "#3f6fbb" },
  { value: "navy", label: "Темно-синий", hex: "#1d3764", border: "#1d3764" },
  { value: "turquoise", label: "Бирюзовый", hex: "#48b8c7", border: "#3a9ba8" },
  { value: "green", label: "Зеленый", hex: "#4e8c62", border: "#3f724f" },
  { value: "olive", label: "Оливковый", hex: "#7b8450", border: "#697145" },
  { value: "red", label: "Красный", hex: "#cf4e4e", border: "#b43c3c" },
  { value: "burgundy", label: "Бордовый", hex: "#7a2f41", border: "#662838" },
  { value: "yellow", label: "Желтый", hex: "#ebcb53", border: "#cfb244" },
  { value: "orange", label: "Оранжевый", hex: "#ef9551", border: "#d97c37" },
  { value: "pink", label: "Розовый", hex: "#e6a6bd", border: "#cf90a7" },
  { value: "lavender", label: "Лавандовый", hex: "#b8a5df", border: "#a18acc" },
  { value: "purple", label: "Фиолетовый", hex: "#8d6bc7", border: "#7958b2" },
];

export const FIT_OPTIONS = [
  { value: "fitted", label: "Приталенная" },
  { value: "balanced", label: "Сбалансированная" },
  { value: "loose", label: "Свободная" },
  { value: "oversized", label: "Оверсайз" },
];

export const LAYER_LEVEL_OPTIONS = [
  { value: "base", label: "Базовый слой" },
  { value: "mid", label: "Утепляющий слой" },
  { value: "outer", label: "Верхний слой" },
  { value: "support", label: "Поддерживающий аксессуар" },
];

export const INSULATION_OPTIONS = [
  { value: "0.2", label: "Очень лёгкая" },
  { value: "0.6", label: "Лёгкая" },
  { value: "1.0", label: "Умеренная" },
  { value: "1.5", label: "Тёплая" },
  { value: "2.0", label: "Очень тёплая" },
  { value: "2.6", label: "Для сильного холода" },
];

const DEFAULT_FIT_BY_SUBCATEGORY = {
  t_shirt: "balanced",
  shirt: "fitted",
  blouse: "fitted",
  polo: "balanced",
  longsleeve: "balanced",
  sweater: "loose",
  hoodie: "oversized",
  cardigan: "loose",
  turtleneck: "fitted",
  sweatshirt: "loose",
  vest: "balanced",
  crop_top: "fitted",
  jeans: "balanced",
  trousers: "fitted",
  chinos: "balanced",
  joggers: "loose",
  leggings: "fitted",
  culottes: "loose",
  skirt: "balanced",
  mini_skirt: "fitted",
  midi_skirt: "balanced",
  maxi_skirt: "loose",
  shorts: "balanced",
  winter_boots: "balanced",
  felt_boots: "balanced",
  warm_boots: "balanced",
  demi_boots: "balanced",
  ankle_boots: "fitted",
  boots: "balanced",
  closed_shoes: "fitted",
  pumps: "fitted",
  loafers: "fitted",
  sneakers: "balanced",
  summer_sneakers: "balanced",
  sandals: "fitted",
  espadrilles: "balanced",
  flip_flops: "loose",
  slippers: "loose",
  coat: "balanced",
  jacket: "balanced",
  parka: "oversized",
  down_jacket: "oversized",
  trench: "balanced",
  blazer: "fitted",
  leather_jacket: "balanced",
  windbreaker: "loose",
  vest_outerwear: "balanced",
  bag: "balanced",
  backpack: "balanced",
  scarf: "loose",
  hat: "balanced",
  cap: "balanced",
  gloves: "fitted",
  belt: "fitted",
  jewelry: "fitted",
};

const DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY = {
  t_shirt: "base",
  shirt: "base",
  blouse: "base",
  polo: "base",
  longsleeve: "base",
  crop_top: "base",
  turtleneck: "base",
  sweater: "mid",
  hoodie: "mid",
  cardigan: "mid",
  sweatshirt: "mid",
  vest: "mid",
  coat: "outer",
  jacket: "outer",
  parka: "outer",
  down_jacket: "outer",
  trench: "outer",
  blazer: "outer",
  leather_jacket: "outer",
  windbreaker: "outer",
  vest_outerwear: "outer",
  bag: "support",
  backpack: "support",
  scarf: "support",
  hat: "support",
  cap: "support",
  gloves: "support",
  belt: "support",
  jewelry: "support",
};

const DEFAULT_INSULATION_BY_SUBCATEGORY = {
  t_shirt: "0.6",
  shirt: "0.8",
  blouse: "0.7",
  polo: "0.7",
  longsleeve: "1.0",
  crop_top: "0.2",
  sweater: "1.8",
  hoodie: "1.7",
  cardigan: "1.4",
  turtleneck: "1.5",
  sweatshirt: "1.5",
  vest: "1.1",
  jeans: "1.4",
  trousers: "1.2",
  chinos: "1.1",
  joggers: "1.4",
  leggings: "1.0",
  culottes: "0.9",
  skirt: "0.8",
  mini_skirt: "0.5",
  midi_skirt: "0.8",
  maxi_skirt: "0.9",
  shorts: "0.3",
  winter_boots: "2.0",
  felt_boots: "2.2",
  warm_boots: "1.9",
  demi_boots: "1.5",
  ankle_boots: "1.4",
  boots: "1.3",
  closed_shoes: "1.0",
  pumps: "0.8",
  loafers: "0.8",
  sneakers: "0.9",
  summer_sneakers: "0.6",
  sandals: "0.2",
  espadrilles: "0.3",
  flip_flops: "0.1",
  slippers: "0.1",
  coat: "2.4",
  jacket: "1.7",
  parka: "2.6",
  down_jacket: "2.8",
  trench: "1.5",
  blazer: "1.2",
  leather_jacket: "1.6",
  windbreaker: "1.2",
  vest_outerwear: "1.2",
  scarf: "0.5",
  hat: "0.4",
  gloves: "0.4",
};

const WATERPROOF_SUBCATEGORIES = new Set([
  "trench",
  "parka",
  "down_jacket",
  "windbreaker",
  "jacket",
]);

const WINDPROOF_SUBCATEGORIES = new Set([
  "coat",
  "parka",
  "down_jacket",
  "windbreaker",
  "leather_jacket",
]);

const SUBCATEGORY_LABELS = Object.values(SUBCATEGORY_OPTIONS).flat().reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

const STYLE_LABELS = STYLE_OPTIONS.reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

const COLOR_LABELS = COLOR_OPTIONS.reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

const FIT_LABELS = FIT_OPTIONS.reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

const LAYER_LEVEL_LABELS = LAYER_LEVEL_OPTIONS.reduce((acc, entry) => {
  acc[entry.value] = entry.label;
  return acc;
}, {});

export function normalizeCatalogValue(value) {
  return normalizeValue(value);
}

export function getSubcategoryOptions(category) {
  return SUBCATEGORY_OPTIONS[normalizeValue(category)] || [];
}

export function getSubcategoryLabel(value) {
  return SUBCATEGORY_LABELS[normalizeValue(value)] || value || "";
}

export function getStyleLabel(value) {
  return STYLE_LABELS[normalizeValue(value)] || value || "";
}

export function getColorLabel(value) {
  return COLOR_LABELS[normalizeValue(value)] || value || "";
}

export function getFitLabel(value) {
  return FIT_LABELS[normalizeValue(value)] || value || "";
}

export function getLayerLevelLabel(value) {
  return LAYER_LEVEL_LABELS[normalizeValue(value)] || value || "";
}

export function getDefaultFitValue(subcategory) {
  return DEFAULT_FIT_BY_SUBCATEGORY[normalizeValue(subcategory)] || "balanced";
}

export function getDefaultLayerLevelValue(subcategory, category) {
  const normalizedSubcategory = normalizeValue(subcategory);
  if (DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY[normalizedSubcategory]) {
    return DEFAULT_LAYER_LEVEL_BY_SUBCATEGORY[normalizedSubcategory];
  }

  const normalizedCategory = normalizeValue(category);
  if (normalizedCategory === "outerwear") {
    return "outer";
  }
  if (normalizedCategory === "accessory") {
    return "support";
  }
  return "base";
}

export function getDefaultInsulationValue(subcategory) {
  return DEFAULT_INSULATION_BY_SUBCATEGORY[normalizeValue(subcategory)] || "0.6";
}

export function getDefaultProtectionFlags(subcategory) {
  const normalizedSubcategory = normalizeValue(subcategory);
  return {
    waterproof: WATERPROOF_SUBCATEGORIES.has(normalizedSubcategory),
    windproof: WINDPROOF_SUBCATEGORIES.has(normalizedSubcategory),
  };
}
```

## frontend\src\hooks\useAuth.js

```javascript
import { useContext } from "react";

import { AuthContext } from "../context/AuthContext";


export default function useAuth() {
  return useContext(AuthContext);
}
```

## frontend\src\main.jsx

```jsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles/global.css";


ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

## frontend\src\pages\AddClothingItemPage.jsx

```jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createItem } from "../api/itemsApi";
import ClothingItemForm from "../components/ClothingItemForm";
import useAuth from "../hooks/useAuth";


export default function AddClothingItemPage() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(formData) {
    setLoading(true);
    setError("");

    try {
      await createItem(token, formData);
      navigate("/wardrobe");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-section">
      {error ? <p className="error-text">{error}</p> : null}
      <ClothingItemForm
        submitLabel="Создать вещь"
        onSubmit={handleSubmit}
        loading={loading}
      />
    </section>
  );
}
```

## frontend\src\pages\AnalyticsPage.jsx

```jsx
import { useEffect, useState } from "react";

import { fetchAnalyticsSummary } from "../api/analyticsApi";
import StatCard from "../components/StatCard";
import useAuth from "../hooks/useAuth";
import { translateCategory, translateSeason } from "../utils/i18n";


function renderMapEntries(data, translateValue = (value) => value) {
  const entries = Object.entries(data || {});
  if (!entries.length) {
    return <div className="list-chip">Пока нет данных</div>;
  }

  return entries.map(([label, value]) => (
    <div key={label} className="list-chip">
      {translateValue(label)}: {value}
    </div>
  ));
}


export default function AnalyticsPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSummary() {
      try {
        const response = await fetchAnalyticsSummary(token);
        setSummary(response);
      } catch (requestError) {
        setError(requestError.message);
      }
    }

    loadSummary();
  }, [token]);

  return (
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Аналитика</p>
          <h1>Сводка по гардеробу</h1>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="stats-grid">
        <StatCard
          label="Всего вещей"
          value={summary?.total_items ?? 0}
          helpText="Все вещи, добавленные текущим пользователем."
        />
        <StatCard
          label="Покрыто сезонов"
          value={Object.keys(summary?.by_season || {}).length}
          helpText="Сколько сезонов представлено в гардеробе."
        />
        <StatCard
          label="Покрыто стилей"
          value={Object.keys(summary?.by_style || {}).length}
          helpText="Сколько разных стилей есть в базе."
        />
      </div>

      <div className="two-column-grid">
        <article className="card">
          <p className="eyebrow">Категории</p>
          <h2>По категориям</h2>
          <div className="stack-list">
            {renderMapEntries(summary?.by_category, translateCategory)}
          </div>
        </article>

        <article className="card">
          <p className="eyebrow">Сезоны</p>
          <h2>По сезонам</h2>
          <div className="stack-list">
            {renderMapEntries(summary?.by_season, translateSeason)}
          </div>
        </article>

        <article className="card">
          <p className="eyebrow">Стили</p>
          <h2>По стилям</h2>
          <div className="stack-list">{renderMapEntries(summary?.by_style)}</div>
        </article>

        <article className="card">
          <p className="eyebrow">Рекомендации</p>
          <h2>Короткие выводы</h2>
          <div className="stack-list">
            {(summary?.recommendations || ["Аналитика появится после добавления вещей."]).map(
              (entry) => (
                <div key={entry} className="list-chip">
                  {entry}
                </div>
              ),
            )}
          </div>
        </article>
      </div>
    </section>
  );
}
```

## frontend\src\pages\ClothingItemDetailsPage.jsx

```jsx
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { deleteItem, fetchItemById } from "../api/itemsApi";
import {
  getCategoryPlaceholderUrl,
  resolveItemImageUrl,
} from "../api/client";
import {
  getColorLabel,
  getFitLabel,
  getLayerLevelLabel,
  getStyleLabel,
  getSubcategoryLabel,
} from "../data/clothingOptions";
import useAuth from "../hooks/useAuth";
import {
  translateCategory,
  translateFormality,
  translateSeason,
} from "../utils/i18n";

function formatItemValue(value, fallback = "Не указано") {
  return value || fallback;
}

function EditIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="item-detail-action-icon">
      <path
        d="M4 20h4.5L19 9.5 14.5 5 4 15.5V20Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M12.5 7l4.5 4.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function DeleteIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="item-detail-action-icon">
      <path
        d="M5 7h14"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M9 7V5.5C9 4.67 9.67 4 10.5 4h3c.83 0 1.5.67 1.5 1.5V7"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8 7l.7 11.2c.05.76.68 1.35 1.45 1.35h3.7c.77 0 1.4-.59 1.45-1.35L16 7"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M10 10.5v5M14 10.5v5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function ClothingItemDetailsPage() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadItem() {
      try {
        const response = await fetchItemById(token, itemId);
        setItem(response.item);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    loadItem();
  }, [itemId, token]);

  async function handleDelete() {
    if (!itemId) {
      return;
    }

    if (!window.confirm("Удалить эту вещь из гардероба?")) {
      return;
    }

    setDeleting(true);
    setError("");

    try {
      await deleteItem(token, itemId);
      navigate("/wardrobe");
    } catch (requestError) {
      setError(requestError.message);
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <section className="page-section page-narrow">
        <div className="card">Загрузка карточки вещи...</div>
      </section>
    );
  }

  if (!item) {
    return (
      <section className="page-section page-narrow">
        <div className="card empty-state">
          <p className="error-text">{error || "Вещь не найдена."}</p>
          <Link to="/wardrobe" className="secondary-button">
            Вернуться в гардероб
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="page-section page-narrow">
      {error ? <p className="error-text">{error}</p> : null}

      <div className="item-detail-card">
        <img
          src={resolveItemImageUrl(item)}
          alt={item.title}
          className="item-detail-image"
          onError={(event) => {
            event.currentTarget.src = getCategoryPlaceholderUrl(item.category);
          }}
        />

        <div className="item-detail-content">
          <div className="item-detail-header">
            <div className="item-detail-title-block">
              <h1>{item.title}</h1>
              <p className="item-detail-subtitle">
                {translateCategory(item.category)}
                {item.subcategory ? ` | ${getSubcategoryLabel(item.subcategory)}` : ""}
              </p>
            </div>
            <span className="item-detail-season">{translateSeason(item.season)}</span>
          </div>

          <div className="item-detail-meta">
            <p>
              <strong>Цвета:</strong>{" "}
              {item.colors?.length
                ? item.colors.map(getColorLabel).join(", ")
                : "Не указаны"}
            </p>
            <p>
              <strong>Стили:</strong>{" "}
              {item.styles?.length
                ? item.styles.map(getStyleLabel).join(", ")
                : "Не указаны"}
            </p>
            <p>
              <strong>Формальность:</strong> {translateFormality(item.formality)}
            </p>
            <p>
              <strong>Посадка:</strong> {formatItemValue(getFitLabel(item.fit))}
            </p>
            <p>
              <strong>Слой:</strong> {formatItemValue(getLayerLevelLabel(item.layer_level))}
            </p>
            <p>
              <strong>Утепление:</strong> {item.insulation_rating ?? 0}
            </p>
            <p>
              <strong>Дождь:</strong> {item.waterproof ? "да" : "нет"}
            </p>
            <p>
              <strong>Ветер:</strong> {item.windproof ? "да" : "нет"}
            </p>
          </div>

          <div className="item-detail-actions">
            <Link
              to={`/wardrobe/${item.id}/edit`}
              className="item-detail-icon-button"
              aria-label="Редактировать вещь"
              title="Редактировать"
            >
              <EditIcon />
            </Link>
            <button
              type="button"
              className="item-detail-icon-button item-detail-icon-button-danger"
              onClick={handleDelete}
              disabled={deleting}
              aria-label="Удалить вещь"
              title={deleting ? "Удаление..." : "Удалить"}
            >
              <DeleteIcon />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
```

## frontend\src\pages\DashboardPage.jsx

```jsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchAnalyticsSummary } from "../api/analyticsApi";
import { fetchSavedOutfits } from "../api/outfitsApi";
import StatCard from "../components/StatCard";
import useAuth from "../hooks/useAuth";


export default function DashboardPage() {
  const { token, user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [savedOutfitsCount, setSavedOutfitsCount] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [analyticsResponse, outfitsResponse] = await Promise.all([
          fetchAnalyticsSummary(token),
          fetchSavedOutfits(token),
        ]);
        setAnalytics(analyticsResponse);
        setSavedOutfitsCount(outfitsResponse.outfits.length);
      } catch (requestError) {
        setError(requestError.message);
      }
    }

    loadDashboard();
  }, [token]);

  const categoryCount = Object.keys(analytics?.by_category || {}).length;

  return (
    <section className="page-section">
      <div className="hero-card">
        <div>
          <p className="eyebrow">Главная</p>
          <h1 className="hero-title">
            {user?.name ? `${user.name}, ваш гардероб` : "Рабочее пространство гардероба"}
          </h1>
          <p className="muted-text">
            Используйте MVP для заполнения гардероба, генерации образов и проверки
            логики рекомендаций без LLM.
          </p>
        </div>

        <div className="hero-actions">
          <Link to="/wardrobe/add" className="primary-button">
            Добавить вещь
          </Link>
          <Link to="/generate" className="secondary-button">
            Подобрать образ
          </Link>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="stats-grid">
        <StatCard
          label="Вещи"
          value={analytics?.total_items ?? 0}
          helpText="Текущее количество вещей в гардеробе."
        />
        <StatCard
          label="Сохраненные образы"
          value={savedOutfitsCount}
          helpText="Количество сохраненных комбинаций."
        />
        <StatCard
          label="Категории"
          value={categoryCount}
          helpText="Сколько категорий уже представлено."
        />
      </div>

      <div className="two-column-grid">
        <article className="card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Быстрые действия</p>
              <h2>Что можно сделать дальше</h2>
            </div>
          </div>

          <div className="stack-list">
            <Link to="/wardrobe" className="list-link">
              Открыть гардероб
            </Link>
            <Link to="/generate" className="list-link">
              Запустить подбор образов
            </Link>
            <Link to="/analytics" className="list-link">
              Посмотреть аналитику
            </Link>
          </div>
        </article>

        <article className="card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Сводка</p>
              <h2>Рекомендации по гардеробу</h2>
            </div>
          </div>

          <div className="stack-list">
            {(analytics?.recommendations || ["Добавьте несколько вещей, чтобы появилась аналитика."]).map(
              (recommendation) => (
                <div key={recommendation} className="list-chip">
                  {recommendation}
                </div>
              ),
            )}
          </div>
        </article>
      </div>
    </section>
  );
}
```

## frontend\src\pages\EditClothingItemPage.jsx

```jsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchItemById, updateItem } from "../api/itemsApi";
import ClothingItemForm from "../components/ClothingItemForm";
import useAuth from "../hooks/useAuth";


export default function EditClothingItemPage() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadItem() {
      try {
        const response = await fetchItemById(token, itemId);
        setItem(response.item);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    loadItem();
  }, [itemId, token]);

  async function handleSubmit(formData) {
    setSaving(true);
    setError("");

    try {
      await updateItem(token, itemId, formData);
      navigate("/wardrobe");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="page-section">
        <div className="card">Загрузка вещи...</div>
      </section>
    );
  }

  return (
    <section className="page-section">
      {error ? <p className="error-text">{error}</p> : null}
      <ClothingItemForm
        initialValues={item}
        submitLabel="Обновить вещь"
        onSubmit={handleSubmit}
        loading={saving}
      />
    </section>
  );
}
```

## frontend\src\pages\LoginPage.jsx

```jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import useAuth from "../hooks/useAuth";


export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formValues, setFormValues] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((currentValues) => ({ ...currentValues, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      await login(formValues);
      navigate("/");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <p className="eyebrow">Цифровой гардероб</p>
        <h1>Вход</h1>
        <p className="muted-text">
          Войдите в сервис для управления гардеробом и подбора образов.
        </p>

        <label>
          Email
          <input
            className="input"
            type="email"
            name="email"
            value={formValues.email}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Пароль
          <input
            className="input"
            type="password"
            name="password"
            value={formValues.password}
            onChange={handleChange}
            required
          />
        </label>

        {error ? <p className="error-text">{error}</p> : null}

        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Вход..." : "Войти"}
        </button>

        <p className="muted-text">
          Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
        </p>
      </form>
    </div>
  );
}
```

## frontend\src\pages\OutfitGeneratorPage.jsx

```jsx
import { useEffect, useMemo, useState } from "react";

import { fetchItems } from "../api/itemsApi";
import { generateOutfits, saveOutfit, uploadOutfitPhoto } from "../api/outfitsApi";
import OutfitCard from "../components/OutfitCard";
import useAuth from "../hooks/useAuth";
import { translateCategory, translateSeason, translateWeather } from "../utils/i18n";

const INITIAL_FORM = {
  event_type: "office",
  preferred_colors: "",
  preferred_style: "",
  temperature: "",
  weather_condition: "",
  anchor_item_id: "",
  constraints: "",
};

export default function OutfitGeneratorPage() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [formValues, setFormValues] = useState(INITIAL_FORM);
  const [generatedOutfits, setGeneratedOutfits] = useState([]);
  const [weather, setWeather] = useState(null);
  const [savedKeys, setSavedKeys] = useState({});
  const [hasGenerated, setHasGenerated] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [resultMessage, setResultMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [error, setError] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    async function loadItems() {
      try {
        const response = await fetchItems(token);
        setItems(response.items || []);
      } catch (requestError) {
        setError(requestError.message);
      }
    }

    loadItems();
  }, [token]);

  const activeOutfit = useMemo(() => {
    if (!generatedOutfits.length) {
      return null;
    }

    return generatedOutfits[activeIndex] || generatedOutfits[0];
  }, [activeIndex, generatedOutfits]);

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((currentValues) => ({ ...currentValues, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResultMessage("");

    try {
      const payload = {
        ...formValues,
        anchor_item_id: formValues.anchor_item_id || null,
        temperature: formValues.temperature || null,
      };
      const response = await generateOutfits(token, payload);
      setGeneratedOutfits(response.outfits || []);
      setWeather(response.weather || null);
      setSavedKeys({});
      setHasGenerated(true);
      setResultMessage(response.message || "");
      setActiveIndex(0);
      setIsModalOpen(Boolean(response.outfits?.length));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(outfit) {
    setError("");

    try {
      const response = await saveOutfit(token, {
        name: outfit.name,
        event_type: outfit.event_type,
        weather_context: outfit.weather_context,
        score: outfit.score,
        explanation: outfit.explanation,
        feature_scores: outfit.feature_scores || {},
        reasons: outfit.reasons || [],
        items: outfit.items.map((entry) => ({
          clothing_item_id: entry.clothing_item_id || entry.id,
          role: entry.role,
        })),
      });

      const savedOutfit = response.outfit;
      setGeneratedOutfits((currentOutfits) =>
        currentOutfits.map((entry, index) =>
          index === activeIndex ? savedOutfit : entry,
        ),
      );
      setSavedKeys((currentKeys) => ({
        ...currentKeys,
        [savedOutfit.id || savedOutfit.name]: true,
      }));
      setResultMessage("Образ сохранён в избранное. Теперь можно добавить своё фото.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function handlePhotoUpload(outfitId, file) {
    setUploadingPhoto(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("image", file);
      const response = await uploadOutfitPhoto(token, outfitId, formData);
      const updatedOutfit = response.outfit;

      setGeneratedOutfits((currentOutfits) =>
        currentOutfits.map((entry) =>
          entry.id === outfitId ? updatedOutfit : entry,
        ),
      );
      setResultMessage("Фото добавлено. Доска образа обновлена.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setUploadingPhoto(false);
    }
  }

  function showPreviousOutfit() {
    setActiveIndex((currentIndex) =>
      currentIndex === 0 ? generatedOutfits.length - 1 : currentIndex - 1,
    );
  }

  function showNextOutfit() {
    setActiveIndex((currentIndex) =>
      currentIndex === generatedOutfits.length - 1 ? 0 : currentIndex + 1,
    );
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Подбор образов</p>
          <h1>Соберите подборку образов</h1>
          <p className="muted-text">
            После генерации доска откроется во всплывающем окне. Там можно листать варианты и сохранять лучший.
          </p>
        </div>
      </div>

      <form className="card form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label>
            Тип события
            <select
              className="input"
              name="event_type"
              value={formValues.event_type}
              onChange={handleChange}
            >
              <option value="office">Офис</option>
              <option value="casual">Повседневный</option>
              <option value="evening">Вечер</option>
              <option value="sport">Спорт</option>
              <option value="party">Вечеринка</option>
              <option value="travel">Поездка</option>
              <option value="date">Свидание</option>
            </select>
          </label>

          <label>
            Предпочтительные цвета
            <input
              className="input"
              name="preferred_colors"
              value={formValues.preferred_colors}
              onChange={handleChange}
              placeholder="белый, черный, бежевый"
            />
          </label>

          <label>
            Предпочтительный стиль
            <input
              className="input"
              name="preferred_style"
              value={formValues.preferred_style}
              onChange={handleChange}
              placeholder="minimal"
            />
          </label>

          <label>
            Температура
            <input
              className="input"
              name="temperature"
              type="number"
              value={formValues.temperature}
              onChange={handleChange}
              placeholder="12"
            />
          </label>

          <label>
            Погода
            <select
              className="input"
              name="weather_condition"
              value={formValues.weather_condition}
              onChange={handleChange}
            >
              <option value="">Использовать тестовую погоду</option>
              <option value="sunny">Солнечно</option>
              <option value="cloudy">Облачно</option>
              <option value="clear">Ясно</option>
              <option value="rain">Дождь</option>
              <option value="snow">Снег</option>
              <option value="wind">Ветрено</option>
            </select>
          </label>

          <label>
            Опорная вещь
            <select
              className="input"
              name="anchor_item_id"
              value={formValues.anchor_item_id}
              onChange={handleChange}
            >
              <option value="">Без опорной вещи</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title} ({translateCategory(item.category)})
                </option>
              ))}
            </select>
          </label>

          <label className="full-width">
            Ограничения
            <input
              className="input"
              name="constraints"
              value={formValues.constraints}
              onChange={handleChange}
              placeholder="no_heels, no_bright_colors"
            />
          </label>
        </div>

        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Подбор..." : "Создать образы"}
        </button>
      </form>

      {error ? <p className="error-text">{error}</p> : null}
      {resultMessage ? <p className="muted-text">{resultMessage}</p> : null}

      {weather ? (
        <div className="card weather-card">
          <p className="eyebrow">Погодный контекст</p>
          <h3>
            {weather.temperature}°C • {translateWeather(weather.weather_condition)}
          </h3>
          <p className="muted-text">
            {weather.city || "Тестовый город"}
            {weather.season ? ` • ${translateSeason(weather.season)}` : ""}
          </p>
        </div>
      ) : null}

      {!loading && hasGenerated && generatedOutfits.length > 0 && !isModalOpen ? (
        <div className="card centered-card">
          <h3>Доски образов готовы</h3>
          <p className="muted-text">
            Откройте модальное окно и пролистайте варианты стрелками.
          </p>
          <button
            type="button"
            className="primary-button"
            onClick={() => setIsModalOpen(true)}
          >
            Открыть доску образа
          </button>
        </div>
      ) : null}

      {!loading && hasGenerated && generatedOutfits.length === 0 ? (
        <div className="card empty-state">
          {resultMessage || "Для выбранных параметров не найдено подходящих сочетаний."}
        </div>
      ) : null}

      {isModalOpen && activeOutfit ? (
        <OutfitCard
          outfit={activeOutfit}
          onSave={handleSave}
          isSaved={Boolean(savedKeys[activeOutfit.id || activeOutfit.name])}
          onPhotoUpload={handlePhotoUpload}
          isUploadingPhoto={uploadingPhoto}
          boardBadge={`${activeIndex + 1}/${generatedOutfits.length}`}
          onPrevious={showPreviousOutfit}
          onNext={showNextOutfit}
          onClose={() => setIsModalOpen(false)}
        />
      ) : null}
    </section>
  );
}
```

## frontend\src\pages\RegisterPage.jsx

```jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import useAuth from "../hooks/useAuth";


export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formValues, setFormValues] = useState({
    name: "",
    email: "",
    password: "",
    city: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((currentValues) => ({ ...currentValues, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      await register(formValues);
      navigate("/");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <p className="eyebrow">Цифровой гардероб</p>
        <h1>Регистрация</h1>
        <p className="muted-text">
          Создайте аккаунт, чтобы собрать цифровой гардероб и тестировать подбор образов.
        </p>

        <label>
          Имя
          <input
            className="input"
            name="name"
            value={formValues.name}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Город
          <input
            className="input"
            name="city"
            value={formValues.city}
            onChange={handleChange}
            placeholder="Москва"
          />
        </label>

        <label>
          Email
          <input
            className="input"
            type="email"
            name="email"
            value={formValues.email}
            onChange={handleChange}
            required
          />
        </label>

        <label>
          Пароль
          <input
            className="input"
            type="password"
            name="password"
            value={formValues.password}
            onChange={handleChange}
            required
          />
        </label>

        {error ? <p className="error-text">{error}</p> : null}

        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Создание..." : "Создать аккаунт"}
        </button>

        <p className="muted-text">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </form>
    </div>
  );
}
```

## frontend\src\pages\SavedOutfitsPage.jsx

```jsx
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchSavedOutfits, uploadOutfitPhoto } from "../api/outfitsApi";
import OutfitCard from "../components/OutfitCard";
import useAuth from "../hooks/useAuth";

export default function SavedOutfitsPage() {
  const { token } = useAuth();
  const [outfits, setOutfits] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadSavedOutfits() {
      setLoading(true);
      setError("");

      try {
        const response = await fetchSavedOutfits(token);
        setOutfits(response.outfits || []);
        setActiveIndex(0);
        setIsModalOpen(Boolean(response.outfits?.length));
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    loadSavedOutfits();
  }, [token]);

  const activeOutfit = useMemo(() => {
    if (!outfits.length) {
      return null;
    }

    return outfits[activeIndex] || outfits[0];
  }, [activeIndex, outfits]);

  async function handlePhotoUpload(outfitId, file) {
    setUploadingPhoto(true);
    setError("");
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("image", file);
      const response = await uploadOutfitPhoto(token, outfitId, formData);
      const updatedOutfit = response.outfit;

      setOutfits((currentOutfits) =>
        currentOutfits.map((entry) =>
          entry.id === outfitId ? updatedOutfit : entry,
        ),
      );
      setMessage("Фото добавлено. Доска образа обновлена.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setUploadingPhoto(false);
    }
  }

  function showPreviousOutfit() {
    setActiveIndex((currentIndex) =>
      currentIndex === 0 ? outfits.length - 1 : currentIndex - 1,
    );
  }

  function showNextOutfit() {
    setActiveIndex((currentIndex) =>
      currentIndex === outfits.length - 1 ? 0 : currentIndex + 1,
    );
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Избранное</p>
          <h1>Сохранённые образы</h1>
          <p className="muted-text">
            Все сохранённые образы открываются как отдельные доски во всплывающем окне.
          </p>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {message ? <p className="muted-text">{message}</p> : null}

      {loading ? (
        <div className="card empty-state">Загружаем сохранённые образы...</div>
      ) : null}

      {!loading && !activeOutfit ? (
        <div className="card empty-state">
          <h3>Пока нет сохранённых образов</h3>
          <p className="muted-text">
            Сначала сгенерируйте образы и нажмите на сердечко, чтобы сохранить лучший вариант.
          </p>
          <Link to="/generate" className="primary-button">
            Перейти к подбору образов
          </Link>
        </div>
      ) : null}

      {!loading && activeOutfit && !isModalOpen ? (
        <div className="card centered-card">
          <h3>Сохранённые доски готовы</h3>
          <p className="muted-text">
            Откройте модальное окно, чтобы пролистать сохранённые образы.
          </p>
          <button
            type="button"
            className="primary-button"
            onClick={() => setIsModalOpen(true)}
          >
            Открыть сохранённые доски
          </button>
        </div>
      ) : null}

      {isModalOpen && activeOutfit ? (
        <OutfitCard
          outfit={activeOutfit}
          isSaved
          onPhotoUpload={handlePhotoUpload}
          isUploadingPhoto={uploadingPhoto}
          boardBadge={`${activeIndex + 1}/${outfits.length}`}
          onPrevious={showPreviousOutfit}
          onNext={showNextOutfit}
          onClose={() => setIsModalOpen(false)}
        />
      ) : null}
    </section>
  );
}
```

## frontend\src\pages\WardrobePage.jsx

```jsx
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { deleteItem, fetchItems } from "../api/itemsApi";
import {
  getCategoryPlaceholderUrl,
  resolveItemImageUrl,
} from "../api/client";
import useAuth from "../hooks/useAuth";

export default function WardrobePage() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadItems() {
      try {
        const response = await fetchItems(token);
        setItems(response.items);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    loadItems();
  }, [token]);

  async function handleDelete(itemId) {
    if (!window.confirm("Удалить эту вещь из гардероба?")) {
      return;
    }

    try {
      await deleteItem(token, itemId);
      setItems((currentItems) => currentItems.filter((item) => item.id !== itemId));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  function handleOpenItem(itemId) {
    navigate(`/wardrobe/${itemId}`);
  }

  function handleCardKeyDown(event, itemId) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleOpenItem(itemId);
    }
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Гардероб</p>
          <h1>Ваши вещи</h1>
        </div>
        <Link to="/wardrobe/add" className="primary-button">
          Добавить вещь
        </Link>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {loading ? <div className="card">Загрузка гардероба...</div> : null}

      {!loading && items.length === 0 ? (
        <div className="card empty-state">
          Пока вещей нет. Добавьте верх, низ и обувь, чтобы начать подбор образов.
        </div>
      ) : null}

      <div className="item-grid">
        {items.map((item) => (
          <article
            key={item.id}
            className="card item-card item-card-compact item-card-clickable"
            role="button"
            tabIndex={0}
            onClick={() => handleOpenItem(item.id)}
            onKeyDown={(event) => handleCardKeyDown(event, item.id)}
          >
            <img
              src={resolveItemImageUrl(item)}
              alt={item.title}
              className="item-cover"
              onError={(event) => {
                event.currentTarget.src = getCategoryPlaceholderUrl(item.category);
              }}
            />

            <div className="item-body">
              <div className="item-compact-footer">
                <h3 className="item-compact-title">{item.title}</h3>
                <div className="item-icon-actions">
                  <Link
                    to={`/wardrobe/${item.id}/edit`}
                    className="item-icon-button"
                    aria-label="Редактировать вещь"
                    title="Редактировать"
                    onClick={(event) => event.stopPropagation()}
                  >
                    ✎
                  </Link>
                  <button
                    type="button"
                    className="item-icon-button item-icon-button-danger"
                    aria-label="Удалить вещь"
                    title="Удалить"
                    onClick={(event) => {
                      event.stopPropagation();
                      handleDelete(item.id);
                    }}
                  >
                    🗑
                  </button>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
```

## frontend\src\styles\global.css

```css
@import url("https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap");

:root {
  color-scheme: light;
  font-family: "Manrope", "Segoe UI", sans-serif;
  color: #132238;
  background:
    radial-gradient(circle at top left, rgba(255, 232, 202, 0.85), transparent 30%),
    radial-gradient(circle at top right, rgba(208, 232, 255, 0.75), transparent 30%),
    linear-gradient(180deg, #f7f7f2 0%, #eef4f9 100%);
  line-height: 1.5;
  font-weight: 500;
  --surface: rgba(255, 255, 255, 0.82);
  --surface-strong: #ffffff;
  --border: rgba(19, 34, 56, 0.09);
  --primary: #1d5b79;
  --primary-dark: #15445a;
  --accent: #f29f58;
  --text-soft: #617085;
  --shadow: 0 20px 40px rgba(17, 43, 69, 0.08);
  --radius: 22px;
}

* {
  box-sizing: border-box;
}

html,
body,
#root {
  min-height: 100%;
  margin: 0;
}

body {
  min-height: 100vh;
}

a {
  color: inherit;
  text-decoration: none;
}

button,
input,
select,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

img {
  display: block;
  max-width: 100%;
}

label {
  display: grid;
  gap: 0.5rem;
  color: #203247;
  font-size: 0.95rem;
}

.field-block {
  display: grid;
  gap: 0.8rem;
}

.field-heading {
  display: grid;
  gap: 0.2rem;
}

.field-label {
  color: #203247;
  font-size: 0.95rem;
  font-weight: 600;
}

.field-helper {
  color: var(--text-soft);
  font-size: 0.85rem;
}

.app-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  min-height: 100vh;
}

.nav-panel {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 2rem;
  border-right: 1px solid var(--border);
  background: rgba(251, 249, 244, 0.85);
  backdrop-filter: blur(18px);
}

.nav-title,
.hero-title,
h1,
h2,
h3 {
  margin: 0;
  letter-spacing: -0.04em;
}

.nav-links,
.stack-list,
.outfit-items {
  display: grid;
  gap: 0.75rem;
}

.nav-link {
  padding: 0.95rem 1rem;
  border-radius: 16px;
  color: var(--text-soft);
  transition: 160ms ease;
}

.nav-link:hover,
.nav-link-active {
  background: #ffffff;
  color: var(--primary-dark);
  box-shadow: var(--shadow);
}

.content-shell {
  padding: 2rem;
}

.topbar,
.section-heading,
.outfit-header,
.item-header,
.card-actions,
.hero-card,
.hero-actions,
.topbar-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.page-section {
  display: grid;
  gap: 1.5rem;
}

.hero-card,
.card,
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  backdrop-filter: blur(14px);
}

.hero-card {
  padding: 1.75rem;
  align-items: flex-end;
}

.card,
.stat-card {
  padding: 1.4rem;
}

.form-card {
  display: grid;
  gap: 1.4rem;
}

.stats-grid,
.two-column-grid,
.feature-grid,
.item-grid,
.outfit-grid {
  display: grid;
  gap: 1rem;
}

.stats-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.two-column-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.item-grid,
.outfit-grid {
  grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.chip-grid,
.color-picker-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.chip-button,
.color-swatch {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.8rem 0.95rem;
  border-radius: 16px;
  border: 1px solid rgba(33, 65, 96, 0.12);
  background: rgba(255, 255, 255, 0.72);
  color: #25384e;
  transition: 160ms ease;
}

.chip-button:hover,
.color-swatch:hover {
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(29, 91, 121, 0.2);
}

.chip-button.is-selected,
.color-swatch.is-selected {
  background: rgba(29, 91, 121, 0.1);
  border-color: rgba(29, 91, 121, 0.34);
  color: var(--primary-dark);
  box-shadow: inset 0 0 0 1px rgba(29, 91, 121, 0.08);
}

.color-swatch {
  min-width: 132px;
  justify-content: flex-start;
}

.color-dot {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  border: 2px solid rgba(19, 34, 56, 0.14);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
}

.full-width {
  grid-column: 1 / -1;
}

.input {
  width: 100%;
  padding: 0.95rem 1rem;
  border: 1px solid rgba(33, 65, 96, 0.13);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  color: #132238;
}

.input:focus {
  outline: 2px solid rgba(29, 91, 121, 0.17);
  border-color: rgba(29, 91, 121, 0.28);
}

.primary-button,
.secondary-button,
.ghost-button,
.list-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 0.85rem 1.1rem;
  border-radius: 16px;
  border: 1px solid transparent;
  transition: 160ms ease;
}

.primary-button {
  background: var(--primary);
  color: #fff;
}

.primary-button:hover {
  background: var(--primary-dark);
}

.secondary-button {
  background: rgba(29, 91, 121, 0.08);
  color: var(--primary-dark);
  border-color: rgba(29, 91, 121, 0.1);
}

.secondary-button:hover {
  background: rgba(29, 91, 121, 0.14);
}

.ghost-button,
.list-link {
  background: transparent;
  border-color: rgba(33, 65, 96, 0.12);
  color: #25384e;
}

.ghost-button:hover,
.list-link:hover {
  background: rgba(255, 255, 255, 0.75);
}

.muted-text {
  margin: 0;
  color: var(--text-soft);
}

.eyebrow {
  margin: 0 0 0.35rem;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  font-weight: 800;
}

.stat-card h3,
.hero-title,
.page-title {
  font-size: clamp(1.6rem, 2vw, 2.3rem);
}

.badge,
.score-chip,
.feature-badge,
.list-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.7rem;
  border-radius: 999px;
  background: rgba(29, 91, 121, 0.08);
  color: var(--primary-dark);
}

.feature-grid {
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.feature-badge {
  justify-content: space-between;
}

.item-card,
.outfit-card {
  overflow: hidden;
}

.item-cover {
  width: calc(100% + 2.8rem);
  margin: -1.4rem -1.4rem 1rem;
  height: 210px;
  object-fit: cover;
  background: linear-gradient(135deg, #d9eaf7, #f4d7b8);
}

.item-cover-placeholder,
.item-thumbnail-placeholder {
  display: grid;
  place-items: center;
  color: var(--primary-dark);
  text-transform: uppercase;
  font-weight: 800;
}

.item-body {
  display: grid;
  gap: 0.6rem;
}

.item-card-clickable {
  cursor: pointer;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}

.item-card-clickable:hover {
  transform: translateY(-2px);
  border-color: rgba(29, 91, 121, 0.18);
}

.item-card-clickable:focus-visible {
  outline: 3px solid rgba(29, 91, 121, 0.16);
  outline-offset: 2px;
}

.item-card-compact {
  padding: 0;
  overflow: hidden;
}

.item-card-compact .item-cover {
  width: 100%;
  margin: 0;
  height: 280px;
  border-radius: 0;
}

.item-card-compact .item-body {
  padding: 0.9rem 1rem 1rem;
  gap: 0;
}

.item-compact-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.9rem;
}

.item-compact-title {
  margin: 0;
  font-size: 1rem;
  line-height: 1.25;
  color: #1b2f42;
}

.item-icon-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.item-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  border: 1px solid rgba(33, 65, 96, 0.1);
  background: rgba(244, 247, 251, 0.92);
  color: #23415b;
  font-size: 1.05rem;
  line-height: 1;
  transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
}

.item-icon-button:hover {
  transform: translateY(-1px);
  background: rgba(234, 241, 248, 0.98);
  border-color: rgba(29, 91, 121, 0.18);
}

.item-icon-button-danger {
  color: #8b3343;
}

.item-icon-button-danger:hover {
  background: rgba(252, 238, 240, 0.98);
  border-color: rgba(173, 69, 88, 0.18);
}

.page-narrow {
  width: min(980px, 100%);
  margin-inline: auto;
}

.item-detail-card {
  display: grid;
  grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
  align-items: stretch;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid var(--border);
  border-radius: 36px;
  box-shadow: var(--shadow);
}

.item-detail-image {
  width: 100%;
  height: 100%;
  min-height: 420px;
  aspect-ratio: 5 / 7;
  object-fit: cover;
  object-position: center;
  background: linear-gradient(135deg, #d9eaf7, #f4d7b8);
}

.item-detail-content {
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 1rem;
  align-content: stretch;
  padding: clamp(1.2rem, 3vw, 2rem);
}

.item-detail-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: flex-start;
  gap: 1rem;
}

.item-detail-title-block {
  display: grid;
  gap: 0.4rem;
}

.item-detail-title-block h1 {
  font-size: clamp(1.55rem, 3vw, 2.35rem);
  line-height: 1.02;
}

.item-detail-subtitle {
  margin: 0;
  color: var(--text-soft);
  font-size: clamp(0.8rem, 1.4vw, 0.98rem);
}

.item-detail-season {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 54px;
  padding: 0.75rem 1.3rem;
  border-radius: 999px;
  background: rgba(232, 239, 246, 0.92);
  color: #264057;
  font-size: clamp(0.78rem, 1.3vw, 0.92rem);
  white-space: nowrap;
}

.item-detail-meta {
  display: grid;
  gap: 0.75rem;
}

.item-detail-meta p {
  margin: 0;
  color: #617085;
  font-size: clamp(0.84rem, 1.4vw, 0.98rem);
  line-height: 1.34;
}

.item-detail-meta strong {
  color: #1b2f42;
  font-weight: 700;
}

.item-detail-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.85rem;
  align-self: end;
  justify-self: end;
}

.item-detail-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  border-radius: 18px;
  border: 1px solid rgba(33, 65, 96, 0.12);
  background: rgba(239, 244, 249, 0.95);
  color: #21415b;
  box-shadow: 0 12px 22px rgba(17, 43, 69, 0.08);
  transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
}

.item-detail-icon-button:hover {
  transform: translateY(-1px);
  background: rgba(232, 239, 246, 0.98);
  border-color: rgba(29, 91, 121, 0.2);
}

.item-detail-icon-button-danger {
  color: #8e3444;
}

.item-detail-icon-button-danger:hover {
  background: rgba(252, 238, 240, 0.98);
  border-color: rgba(173, 69, 88, 0.2);
}

.item-detail-icon-button:disabled {
  opacity: 0.65;
}

.item-detail-action-icon {
  width: 24px;
  height: 24px;
}

.outfit-item-row,
.inline-media {
  display: flex;
  gap: 0.9rem;
  align-items: center;
}

.item-thumbnail,
.inline-thumbnail {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  object-fit: cover;
  background: linear-gradient(135deg, #d9eaf7, #f4d7b8);
}

.inline-thumbnail {
  width: 86px;
  height: 86px;
}

.error-text {
  margin: 0;
  color: #ac3a39;
  font-weight: 700;
}

.auth-shell,
.page-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
}

.auth-card {
  width: min(460px, 100%);
  display: grid;
  gap: 1rem;
}

.centered-card,
.empty-state {
  text-align: center;
}

.weather-card {
  background: linear-gradient(135deg, rgba(29, 91, 121, 0.12), rgba(242, 159, 88, 0.12));
}

.outfit-browser-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.outfit-browser-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.arrow-button,
.favorite-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 999px;
  border: 1px solid rgba(33, 65, 96, 0.12);
  background: rgba(255, 255, 255, 0.82);
  color: var(--primary-dark);
  box-shadow: 0 12px 24px rgba(17, 43, 69, 0.08);
  transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
}

.arrow-button:hover,
.favorite-button:hover {
  transform: translateY(-1px);
  background: #ffffff;
  border-color: rgba(29, 91, 121, 0.24);
}

.favorite-button {
  font-size: 1.45rem;
}

.favorite-button.is-active {
  background: rgba(242, 159, 88, 0.16);
  border-color: rgba(242, 159, 88, 0.36);
  color: #b85f1f;
}

.favorite-button:disabled,
.arrow-button:disabled {
  cursor: default;
  opacity: 0.7;
}

.outfit-board-card {
  padding: 1rem;
  overflow: visible;
}

.outfit-board-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.95fr);
  gap: 1.2rem;
  align-items: stretch;
}

.outfit-board-stage,
.outfit-side-panel {
  min-height: 760px;
}

.outfit-board-canvas {
  position: relative;
  min-height: 760px;
  padding: 1.5rem;
  border-radius: 30px;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(255, 248, 236, 0.96), transparent 28%),
    radial-gradient(circle at bottom right, rgba(223, 236, 248, 0.92), transparent 30%),
    linear-gradient(145deg, #fbf6ee 0%, #eef4fa 100%);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.8),
    0 28px 48px rgba(17, 43, 69, 0.08);
}

.outfit-board-canvas::before {
  content: "";
  position: absolute;
  inset: 24px;
  border-radius: 26px;
  border: 1px dashed rgba(29, 91, 121, 0.12);
  pointer-events: none;
}

.board-meta-strip {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.board-title-chip,
.board-index-chip {
  display: inline-grid;
  gap: 0.2rem;
  padding: 0.85rem 1rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(33, 65, 96, 0.1);
  box-shadow: 0 14px 24px rgba(17, 43, 69, 0.06);
}

.board-title-chip span,
.board-index-chip {
  color: var(--text-soft);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 800;
}

.board-title-chip strong {
  font-size: 1.05rem;
  color: #1b2f42;
}

.board-piece,
.board-look-card {
  position: absolute;
  display: grid;
  gap: 0.65rem;
  padding: 0.85rem;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(33, 65, 96, 0.09);
  box-shadow: 0 18px 28px rgba(17, 43, 69, 0.12);
}

.board-piece {
  color: #1b2f42;
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.board-piece:hover {
  transform: translateY(-3px) rotate(0deg) scale(1.01);
  box-shadow: 0 22px 34px rgba(17, 43, 69, 0.16);
}

.board-piece-top {
  top: 110px;
  left: 34%;
  width: 220px;
  transform: rotate(-4deg);
}

.board-piece-bottom {
  top: 380px;
  left: 35%;
  width: 230px;
  transform: rotate(3deg);
}

.board-piece-shoes {
  left: 9%;
  bottom: 72px;
  width: 210px;
  transform: rotate(-5deg);
}

.board-piece-outerwear {
  left: 6%;
  top: 180px;
  width: 250px;
  transform: rotate(-7deg);
}

.board-piece-accessory {
  right: 8%;
  top: 138px;
  width: 170px;
  transform: rotate(6deg);
}

.board-piece-a {
  margin-top: 0;
}

.board-piece-b {
  margin-top: 12px;
}

.board-piece-c {
  margin-top: -8px;
}

.board-piece-image {
  width: 100%;
  height: 220px;
  object-fit: cover;
  border-radius: 22px;
  background: linear-gradient(135deg, #d9eaf7, #f4d7b8);
}

.board-piece-caption {
  display: grid;
  gap: 0.18rem;
}

.board-piece-caption span {
  color: var(--text-soft);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 800;
}

.board-piece-caption strong {
  font-size: 0.95rem;
  line-height: 1.25;
}

.board-look-card {
  right: 8%;
  bottom: 56px;
  width: 250px;
  min-height: 290px;
  padding: 0.9rem;
  transform: rotate(4deg);
}

.board-look-card.is-empty {
  place-content: start;
  background: rgba(255, 255, 255, 0.74);
}

.board-look-card.is-empty p {
  margin: 0;
  color: var(--text-soft);
  font-size: 0.92rem;
}

.board-look-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-soft);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 800;
}

.board-look-image {
  width: 100%;
  height: 285px;
  border-radius: 22px;
  object-fit: cover;
  background: linear-gradient(135deg, #d9eaf7, #f4d7b8);
}

.outfit-side-panel {
  display: grid;
  gap: 1rem;
  align-content: start;
  padding: 1.4rem;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(33, 65, 96, 0.08);
}

.outfit-side-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.outfit-score-panel {
  display: grid;
  grid-template-columns: 112px 1fr;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  border-radius: 22px;
  background: linear-gradient(145deg, rgba(29, 91, 121, 0.08), rgba(242, 159, 88, 0.08));
}

.score-ring {
  display: grid;
  place-items: center;
  width: 112px;
  height: 112px;
  padding: 1rem;
  border-radius: 999px;
  background: #ffffff;
  border: 10px solid rgba(29, 91, 121, 0.1);
  text-align: center;
}

.score-ring strong {
  font-size: 1.75rem;
  line-height: 1;
}

.score-ring span {
  color: var(--text-soft);
  font-size: 0.72rem;
}

.outfit-reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.outfit-feature-list,
.outfit-items-list {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 22px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(33, 65, 96, 0.08);
}

.feature-row,
.outfit-items-list-header,
.outfit-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
}

.feature-row {
  padding-bottom: 0.55rem;
  border-bottom: 1px solid rgba(33, 65, 96, 0.08);
}

.feature-row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.outfit-list-item {
  align-items: flex-start;
  padding: 0.85rem;
  border-radius: 18px;
  background: #ffffff;
}

.outfit-list-copy {
  flex: 1;
  display: grid;
  gap: 0.25rem;
}

.outfit-list-link {
  min-width: 92px;
}

.outfit-photo-actions {
  display: grid;
  gap: 0.65rem;
  padding: 1rem;
  border-radius: 22px;
  background: rgba(29, 91, 121, 0.06);
}

@media (max-width: 1100px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .nav-panel {
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }

  .outfit-board-layout {
    grid-template-columns: 1fr;
  }

  .outfit-board-stage,
  .outfit-side-panel,
  .outfit-board-canvas {
    min-height: auto;
  }
}

@media (max-width: 820px) {
  .content-shell,
  .nav-panel {
    padding: 1rem;
  }

  .topbar,
  .section-heading,
  .hero-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid,
  .two-column-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .item-detail-header {
    grid-template-columns: 1fr;
  }

  .item-detail-actions {
    justify-content: flex-start;
    justify-self: flex-start;
    align-self: start;
  }

  .item-detail-card {
    grid-template-columns: 1fr;
  }

  .item-detail-image {
    aspect-ratio: 5 / 7;
    min-height: 0;
    height: auto;
  }

  .item-detail-season {
    min-height: 46px;
  }

  .outfit-browser-toolbar,
  .outfit-score-panel,
  .outfit-side-header,
  .outfit-items-list-header,
  .outfit-list-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .topbar-actions,
  .hero-actions,
  .card-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .primary-button,
  .secondary-button,
  .ghost-button,
  .list-link {
    width: 100%;
  }

  .outfit-board-canvas {
    min-height: 980px;
    padding: 1rem;
  }

  .board-piece-outerwear {
    left: 3%;
    width: 44%;
    top: 160px;
  }

  .board-piece-top {
    left: 49%;
    width: 44%;
    top: 148px;
  }

  .board-piece-bottom {
    left: 28%;
    width: 44%;
    top: 415px;
  }

  .board-piece-shoes {
    left: 8%;
    width: 40%;
    bottom: 280px;
  }

  .board-piece-accessory {
    right: 6%;
    width: 34%;
    top: 620px;
  }

  .board-look-card {
    left: 10%;
    right: 10%;
    bottom: 42px;
    width: auto;
    transform: rotate(2deg);
  }
}

.outfit-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgba(15, 23, 38, 0.44);
  backdrop-filter: blur(12px);
}

.outfit-modal-window {
  position: relative;
  width: min(1280px, 100%);
  height: min(92vh, 940px);
  overflow: hidden;
  padding: 0.45rem 0.9rem 0.9rem;
  border-radius: 34px;
  background: rgba(252, 251, 247, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.86);
  box-shadow: 0 36px 80px rgba(10, 25, 41, 0.24);
}

.outfit-modal-top-actions,
.outfit-modal-bottom-actions {
  position: absolute;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  flex-shrink: 0;
}

.outfit-modal-top-actions {
  top: 0.9rem;
  right: 0.9rem;
}

.outfit-modal-bottom-actions {
  right: 0.9rem;
  bottom: 0.9rem;
}

.outfit-modal-window .arrow-button,
.outfit-modal-window .favorite-button,
.outfit-modal-window .modal-close-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(20, 36, 55, 0.94), rgba(28, 48, 72, 0.9));
  color: #f7fbff;
  box-shadow: 0 18px 34px rgba(17, 43, 69, 0.24);
  backdrop-filter: blur(14px);
  line-height: 1;
  transition:
    transform 160ms ease,
    background 160ms ease,
    box-shadow 160ms ease,
    border-color 160ms ease;
}

.outfit-modal-window .arrow-button:hover,
.outfit-modal-window .favorite-button:hover,
.outfit-modal-window .modal-close-button:hover {
  transform: translateY(-1px);
  background: linear-gradient(180deg, rgba(26, 46, 70, 0.96), rgba(35, 58, 84, 0.92));
  box-shadow: 0 22px 36px rgba(17, 43, 69, 0.28);
}

.outfit-modal-window .favorite-button {
  font-size: 1.38rem;
}

.outfit-modal-window .modal-close-button {
  font-size: 1.75rem;
}

.outfit-modal-window .favorite-button.is-active {
  background: linear-gradient(180deg, rgba(242, 159, 88, 0.98), rgba(214, 117, 36, 0.94));
  border-color: rgba(255, 230, 201, 0.3);
  color: #fff8f2;
}

.outfit-modal-window .favorite-button:disabled,
.outfit-modal-window .arrow-button:disabled,
.outfit-modal-window .modal-close-button:disabled {
  opacity: 0.72;
}

.outfit-modal-content {
  display: grid;
  grid-template-columns: minmax(0, 1.16fr) minmax(360px, 0.84fr);
  gap: 0.95rem;
  height: 100%;
}

.outfit-modal-left {
  display: flex;
  min-height: 0;
  height: 100%;
}

.outfit-modal-sidebar {
  display: grid;
  grid-template-rows: auto auto auto auto;
  gap: 0.52rem;
  align-content: start;
  min-height: 0;
  padding-top: 1.05rem;
  padding-bottom: 4.15rem;
}

.outfit-board-canvas {
  position: relative;
  flex: 1;
  height: 100%;
  min-height: 0;
  padding: 0.65rem;
  border-radius: 30px;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(255, 241, 217, 0.95), transparent 28%),
    radial-gradient(circle at bottom right, rgba(219, 236, 249, 0.92), transparent 32%),
    linear-gradient(145deg, #f8f5ef 0%, #eef4f9 100%);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.8),
    0 22px 44px rgba(17, 43, 69, 0.08);
}

.outfit-board-canvas::before {
  content: "";
  position: absolute;
  inset: 14px;
  border-radius: 26px;
  border: 1px dashed rgba(29, 91, 121, 0.12);
  pointer-events: none;
}

.board-meta-strip {
  position: absolute;
  top: 12px;
  right: 14px;
  z-index: 2;
}

.board-index-chip {
  display: inline-grid;
  gap: 0.2rem;
  padding: 0.65rem 0.85rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(33, 65, 96, 0.08);
  box-shadow: 0 16px 28px rgba(17, 43, 69, 0.08);
  color: var(--text-soft);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 800;
}

.board-grid {
  position: relative;
  z-index: 1;
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 0.72rem;
  height: 100%;
  padding: 0.9rem 0.55rem 0.55rem;
}

.board-row {
  display: grid;
  justify-content: center;
  gap: 0.72rem;
  width: 100%;
  min-height: 0;
}

.board-row-1,
.board-row-2 {
  max-width: 560px;
}

.board-row-3 {
  max-width: 860px;
}

.board-grid-count-1,
.board-grid-count-2,
.board-grid-count-3 {
  grid-template-rows: minmax(0, 1fr);
}

.board-grid-count-4,
.board-grid-count-5,
.board-grid-count-6 {
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

.board-grid-count-1 .board-row,
.board-grid-count-2 .board-row,
.board-grid-count-3 .board-row {
  height: 100%;
}

.board-grid-count-4 .board-row,
.board-grid-count-5 .board-row,
.board-grid-count-6 .board-row {
  height: 100%;
}

.board-row-1 {
  grid-template-columns: minmax(0, 1fr);
}

.board-row-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.board-row-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.board-slot {
  display: flex;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
}

.board-row-1 .board-slot {
  max-width: 260px;
}

.board-row-2 .board-slot {
  max-width: 250px;
}

.board-row-3 .board-slot {
  max-width: 240px;
}

.board-card {
  position: relative;
  display: block;
  width: 100%;
  height: 100%;
  max-height: 100%;
  aspect-ratio: auto;
  overflow: hidden;
  padding: 0;
  border-radius: 22px;
  background: transparent;
  border: 0;
  box-shadow: none;
  transition: transform 160ms ease;
}

.board-card:hover {
  transform: translateY(-2px);
}

.board-card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  border-radius: 22px;
  background: linear-gradient(135deg, #d9eaf7, #f4d7b8);
}

.board-card-photo {
  background: transparent;
}

.board-card-caption {
  position: absolute;
  left: 0.72rem;
  right: 0.72rem;
  bottom: 0.72rem;
  display: grid;
  gap: 0.04rem;
  max-width: calc(100% - 1.44rem);
  padding: 0.45rem 0.62rem 0.5rem;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 22px rgba(17, 43, 69, 0.12);
  backdrop-filter: blur(8px);
}

.board-card-caption span {
  color: var(--text-soft);
  font-size: 0.58rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 800;
}

.board-card-caption strong {
  font-size: 0.76rem;
  line-height: 1.18;
  color: #183149;
}

.outfit-side-copy {
  display: grid;
  gap: 0.12rem;
  padding: 0.12rem 0 0;
}

.outfit-side-copy-header {
  display: block;
}

.outfit-side-copy h2 {
  margin: 0;
  font-size: clamp(1.35rem, 2.1vw, 1.92rem);
  line-height: 1.03;
}

.outfit-board-context {
  margin: 0;
  color: #55657a;
  font-size: 0.78rem;
}

.outfit-summary-card {
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 0.58rem;
  align-items: center;
  padding: 0.68rem;
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(29, 91, 121, 0.08), rgba(242, 159, 88, 0.08));
}

.score-ring {
  display: grid;
  place-items: center;
  width: 88px;
  height: 88px;
  padding: 0.56rem;
  border-radius: 999px;
  background: #ffffff;
  border: 7px solid rgba(29, 91, 121, 0.08);
  text-align: center;
}

.score-ring strong {
  font-size: 1.18rem;
  line-height: 1;
}

.score-ring span {
  color: var(--text-soft);
  font-size: 0.56rem;
}

.outfit-summary-text {
  margin: 0;
  color: #55657a;
  font-size: 0.72rem;
  line-height: 1.3;
}

.outfit-comments-list {
  display: grid;
  gap: 0.34rem;
  align-content: start;
  min-height: auto;
  overflow: visible;
  padding-right: 0;
}

.outfit-comment-pill {
  padding: 0.46rem 0.68rem;
  border-radius: 16px;
  background: rgba(232, 239, 246, 0.88);
  color: #264057;
  font-size: 0.7rem;
  line-height: 1.22;
}

.outfit-photo-actions {
  display: grid;
  gap: 0.32rem;
  justify-items: stretch;
  padding: 0.58rem 0.68rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(33, 65, 96, 0.08);
  box-shadow: 0 10px 24px rgba(17, 43, 69, 0.06);
  align-self: end;
}

.outfit-photo-actions .secondary-button {
  width: 100%;
  min-height: 38px;
  padding: 0.7rem 0.9rem;
  border-radius: 14px;
}

.outfit-photo-actions .muted-text {
  font-size: 0.68rem;
  line-height: 1.22;
}

@media (max-width: 1180px) {
  .outfit-modal-window {
    width: min(1160px, 100%);
  }

  .outfit-modal-content {
    grid-template-columns: minmax(0, 1.08fr) minmax(330px, 0.92fr);
  }

  .board-grid {
    gap: 0.62rem;
  }
}

@media (max-width: 920px) {
  .outfit-modal-window {
    height: auto;
    max-height: calc(100vh - 1.5rem);
    overflow: auto;
  }

  .outfit-modal-content {
    grid-template-columns: 1fr;
    height: auto;
  }

  .outfit-modal-sidebar {
    grid-template-rows: auto;
    padding-bottom: 0;
  }
}

@media (max-width: 720px) {
  .outfit-modal-backdrop {
    padding: 0.75rem;
  }

  .outfit-modal-window {
    padding: 1rem;
    border-radius: 24px;
  }

  .outfit-modal-top-actions,
  .outfit-modal-bottom-actions {
    position: static;
    flex-wrap: wrap;
  }

  .outfit-comments-list {
    overflow: visible;
    padding-right: 0;
  }

  .outfit-side-copy-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .outfit-board-canvas {
    min-height: auto;
    display: grid;
    padding: 1rem;
  }

  .outfit-board-canvas::before {
    inset: 14px;
  }

  .board-meta-strip {
    position: static;
    flex-direction: column;
    align-items: flex-start;
  }

  .board-grid {
    height: auto;
    padding: 3rem 0.2rem 0.2rem;
  }

  .board-row {
    grid-template-columns: 1fr;
    max-width: 100%;
  }

  .board-slot,
  .board-row-1 .board-slot,
  .board-row-2 .board-slot,
  .board-row-3 .board-slot {
    width: 100%;
    max-width: none;
  }

  .board-card {
    aspect-ratio: 0.9;
  }

  .outfit-summary-card {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }
}
```

## frontend\src\utils\i18n.js

```javascript
export const CATEGORY_LABELS = {
  top: "Верх",
  bottom: "Низ",
  shoes: "Обувь",
  outerwear: "Верхний слой",
  accessory: "Аксессуар",
};

export const ROLE_LABELS = {
  top: "Верх",
  bottom: "Низ",
  shoes: "Обувь",
  outerwear: "Верхний слой",
  accessory: "Аксессуар",
};

export const SEASON_LABELS = {
  "all-season": "Всесезон",
  all_season: "Всесезон",
  spring: "Весна",
  summer: "Лето",
  autumn: "Осень",
  winter: "Зима",
};

export const FORMALITY_LABELS = {
  casual: "Повседневный",
  smart: "Смарт-кэжуал",
  formal: "Формальный",
};

export const FIT_LABELS = {
  fitted: "Приталенная",
  balanced: "Сбалансированная",
  loose: "Свободная",
  oversized: "Оверсайз",
};

export const LAYER_LEVEL_LABELS = {
  base: "Базовый слой",
  mid: "Утепляющий слой",
  outer: "Верхний слой",
  support: "Поддерживающий аксессуар",
};

export const EVENT_LABELS = {
  office: "Офис",
  casual: "Повседневный",
  evening: "Вечерний",
  sport: "Спортивный",
  party: "Вечеринка",
  travel: "Поездка",
  date: "Свидание",
};

export const WEATHER_LABELS = {
  sunny: "Солнечно",
  cloudy: "Облачно",
  clear: "Ясно",
  rain: "Дождь",
  snow: "Снег",
  wind: "Ветрено",
};

export const FEATURE_LABELS = {
  color_harmony: "Гармония цветов",
  style_match: "Сочетаемость стилей",
  event_match: "Соответствие событию",
  season_match: "Соответствие сезону",
  temperature_match: "Соответствие температуре",
  weather_condition_match: "Соответствие погоде",
  completeness: "Полнота комплекта",
  layering_correctness: "Корректность слоев",
  user_preference_match: "Учет предпочтений",
  constraints_match: "Соблюдение ограничений",
};


function translate(map, value) {
  if (!value) {
    return "";
  }

  return map[String(value)] || value;
}


export function translateCategory(value) {
  return translate(CATEGORY_LABELS, value);
}


export function translateRole(value) {
  return translate(ROLE_LABELS, value);
}


export function translateSeason(value) {
  return translate(SEASON_LABELS, value);
}


export function translateFormality(value) {
  return translate(FORMALITY_LABELS, value);
}


export function translateFit(value) {
  return translate(FIT_LABELS, value);
}


export function translateLayerLevel(value) {
  return translate(LAYER_LEVEL_LABELS, value);
}


export function translateEventType(value) {
  return translate(EVENT_LABELS, value);
}


export function translateWeather(value) {
  return translate(WEATHER_LABELS, value);
}


export function translateFeatureName(value) {
  return translate(FEATURE_LABELS, value);
}
```

## README.md

```markdown
# Project Wardrobe MVP

MVP monorepo for a diploma project:

`Development of a web service for outfit and wardrobe selection using intelligent methods`

The project does **not** use LLMs. Outfit generation is based on a transparent recommendation engine that scores combinations using 10 features.

## Stack

- Backend: Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended
- Database: MySQL
- Frontend: React, JavaScript, Vite
- Image storage: local `uploads/`

## Repository structure

```text
project-root/
  backend/
    app/
      api/
      config/
      extensions/
      models/
      schemas/
      services/
      utils/
    migrations/
    requirements.txt
    run.py
  frontend/
    src/
      api/
      components/
      context/
      hooks/
      pages/
      styles/
    index.html
    package.json
    vite.config.js
  uploads/
  .env.example
  README.md
```

## Backend setup

### 1. Create a virtual environment and install dependencies

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Create the MySQL database

Example SQL:

```sql
CREATE DATABASE wardrobe_mvp
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 3. Configure environment variables

Copy the root example file:

```powershell
cd ..
Copy-Item .env.example .env
```

Update the values in `.env`:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `FRONTEND_URL`
- `VITE_API_URL`

Note: the frontend is configured with `envDir: ".."`, so the root `.env` is used by both backend and frontend.

### 4. Initialize and run migrations

From the `backend/` directory:

```powershell
$env:FLASK_APP = "run.py"
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

After the first initialization, use only:

```powershell
flask db migrate -m "Describe your schema change"
flask db upgrade
```

### 5. Run the Flask backend

```powershell
python run.py
```

Backend default URL: [http://localhost:5000](http://localhost:5000)

Health check: [http://localhost:5000/health](http://localhost:5000/health)

## Frontend setup

### 1. Install dependencies

```powershell
cd frontend
npm install
```

### 2. Run the Vite dev server

```powershell
npm run dev
```

Frontend default URL: [http://localhost:5173](http://localhost:5173)

## Implemented MVP features

- JWT auth: register, login, current user
- Digital wardrobe CRUD with local image upload
- Outfit generation from user items
- 10-feature recommendation architecture with weighted scoring
- Explainability without LLMs
- Mock weather service
- Basic wardrobe analytics
- React dashboard, wardrobe pages, outfit generator, saved outfits, analytics

## Recommendation engine

The backend service `backend/app/services/recommendation_engine.py` contains 10 independent scoring functions:

1. `ColorHarmony`
2. `StyleMatch`
3. `EventMatch`
4. `SeasonMatch`
5. `TemperatureMatch`
6. `WeatherConditionMatch`
7. `Completeness`
8. `LayeringCorrectness`
9. `UserPreferenceMatch`
10. `ConstraintsMatch`

Each feature returns a value from `0` to `1`. The final outfit score is a weighted sum of these feature values.

## Main API routes

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/items`
- `GET /api/items`
- `GET /api/items/<id>`
- `PUT /api/items/<id>`
- `DELETE /api/items/<id>`
- `POST /api/items/upload`
- `POST /api/outfits/generate`
- `POST /api/outfits`
- `GET /api/outfits`
- `POST /api/outfits/<id>/feedback`
- `GET /api/analytics/summary`

## Notes for further development

- `MockWeatherService` can be replaced with a real weather API later.
- User preference editing can be added as a separate profile/settings module.
- The scoring rules and weights are intentionally simple and readable for an MVP and diploma extension work.
```

