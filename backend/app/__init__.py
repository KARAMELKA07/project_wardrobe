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
