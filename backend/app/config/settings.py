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
    FASHION_AI_ENABLED = os.getenv("FASHION_AI_ENABLED", "true").lower() == "true"
    FASHION_AI_MODEL_ID = os.getenv(
        "FASHION_AI_MODEL_ID",
        "openai/clip-vit-base-patch32",
    )
    DEEPFASHION_DATASET_DIR = os.getenv(
        "DEEPFASHION_DATASET_DIR",
        str(PROJECT_ROOT / "backend" / "Category and Attribute Prediction Benchmark"),
    )
    DEEPFASHION_CHECKPOINT_PATH = os.getenv(
        "DEEPFASHION_CHECKPOINT_PATH",
        str(PROJECT_ROOT / "backend" / "model_artifacts" / "deepfashion_classifier.pt"),
    )
    DEEPFASHION_METADATA_PATH = os.getenv(
        "DEEPFASHION_METADATA_PATH",
        str(PROJECT_ROOT / "backend" / "model_artifacts" / "deepfashion_classifier.metadata.json"),
    )
    DEEPFASHION_CONFIDENCE_THRESHOLD = float(
        os.getenv("DEEPFASHION_CONFIDENCE_THRESHOLD", "0.55")
    )
