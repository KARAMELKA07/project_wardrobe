from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from io import BytesIO

from ..utils.errors import ApiError
from ..utils.storage import save_image_bytes
from .deepfashion_classifier import DeepFashionLocalClassifier, PROJECT_ROOT


SUBCATEGORY_CANDIDATES = [
    {"subcategory": "t_shirt", "category": "top", "label": "t-shirt", "title": "Футболка"},
    {"subcategory": "shirt", "category": "top", "label": "shirt", "title": "Рубашка"},
    {"subcategory": "blouse", "category": "top", "label": "blouse", "title": "Блузка"},
    {"subcategory": "dress", "category": "dress", "label": "dress", "title": "Платье"},
    {"subcategory": "polo", "category": "top", "label": "polo shirt", "title": "Поло"},
    {"subcategory": "longsleeve", "category": "top", "label": "long sleeve top", "title": "Лонгслив"},
    {"subcategory": "sweater", "category": "top", "label": "sweater", "title": "Свитер"},
    {"subcategory": "hoodie", "category": "top", "label": "hoodie", "title": "Худи"},
    {"subcategory": "cardigan", "category": "top", "label": "cardigan", "title": "Кардиган"},
    {"subcategory": "turtleneck", "category": "top", "label": "turtleneck", "title": "Водолазка"},
    {"subcategory": "sweatshirt", "category": "top", "label": "sweatshirt", "title": "Свитшот"},
    {"subcategory": "vest", "category": "top", "label": "vest", "title": "Жилет"},
    {"subcategory": "crop_top", "category": "top", "label": "crop top", "title": "Кроп-топ"},
    {"subcategory": "jeans", "category": "bottom", "label": "jeans", "title": "Джинсы"},
    {"subcategory": "trousers", "category": "bottom", "label": "trousers", "title": "Брюки"},
    {"subcategory": "chinos", "category": "bottom", "label": "chinos", "title": "Чиносы"},
    {"subcategory": "joggers", "category": "bottom", "label": "joggers", "title": "Джоггеры"},
    {"subcategory": "leggings", "category": "bottom", "label": "leggings", "title": "Леггинсы"},
    {"subcategory": "culottes", "category": "bottom", "label": "culottes", "title": "Кюлоты"},
    {"subcategory": "skirt", "category": "bottom", "label": "skirt", "title": "Юбка"},
    {"subcategory": "mini_skirt", "category": "bottom", "label": "mini skirt", "title": "Мини-юбка"},
    {"subcategory": "midi_skirt", "category": "bottom", "label": "midi skirt", "title": "Миди-юбка"},
    {"subcategory": "maxi_skirt", "category": "bottom", "label": "maxi skirt", "title": "Макси-юбка"},
    {"subcategory": "shorts", "category": "bottom", "label": "shorts", "title": "Шорты"},
    {"subcategory": "winter_boots", "category": "shoes", "label": "winter boots", "title": "Зимние сапоги"},
    {"subcategory": "felt_boots", "category": "shoes", "label": "felt boots", "title": "Валенки"},
    {"subcategory": "warm_boots", "category": "shoes", "label": "warm boots", "title": "Теплые ботинки"},
    {"subcategory": "demi_boots", "category": "shoes", "label": "demi-season boots", "title": "Демисезонные ботинки"},
    {"subcategory": "ankle_boots", "category": "shoes", "label": "ankle boots", "title": "Ботильоны"},
    {"subcategory": "boots", "category": "shoes", "label": "boots", "title": "Ботинки"},
    {"subcategory": "closed_shoes", "category": "shoes", "label": "closed shoes", "title": "Закрытые туфли"},
    {"subcategory": "pumps", "category": "shoes", "label": "pumps", "title": "Туфли"},
    {"subcategory": "loafers", "category": "shoes", "label": "loafers", "title": "Лоферы"},
    {"subcategory": "flats", "category": "shoes", "label": "flats", "title": "Балетки"},
    {"subcategory": "sneakers", "category": "shoes", "label": "sneakers", "title": "Кроссовки"},
    {"subcategory": "summer_sneakers", "category": "shoes", "label": "summer sneakers", "title": "Летние кроссовки"},
    {"subcategory": "sandals", "category": "shoes", "label": "sandals", "title": "Босоножки"},
    {"subcategory": "espadrilles", "category": "shoes", "label": "espadrilles", "title": "Эспадрильи"},
    {"subcategory": "flip_flops", "category": "shoes", "label": "flip flops", "title": "Шлепки"},
    {"subcategory": "slippers", "category": "shoes", "label": "slippers", "title": "Сланцы"},
    {"subcategory": "coat", "category": "outerwear", "label": "coat", "title": "Пальто"},
    {"subcategory": "jacket", "category": "outerwear", "label": "jacket", "title": "Куртка"},
    {"subcategory": "parka", "category": "outerwear", "label": "parka", "title": "Парка"},
    {"subcategory": "down_jacket", "category": "outerwear", "label": "down jacket", "title": "Пуховик"},
    {"subcategory": "trench", "category": "outerwear", "label": "trench coat", "title": "Тренч"},
    {"subcategory": "blazer", "category": "outerwear", "label": "blazer", "title": "Пиджак"},
    {"subcategory": "leather_jacket", "category": "outerwear", "label": "leather jacket", "title": "Кожаная куртка"},
    {"subcategory": "windbreaker", "category": "outerwear", "label": "windbreaker", "title": "Ветровка"},
    {"subcategory": "vest_outerwear", "category": "outerwear", "label": "outerwear vest", "title": "Жилет"},
    {"subcategory": "bag", "category": "accessory", "label": "bag", "title": "Сумка"},
    {"subcategory": "backpack", "category": "accessory", "label": "backpack", "title": "Рюкзак"},
    {"subcategory": "scarf", "category": "accessory", "label": "scarf", "title": "Шарф"},
    {"subcategory": "hat", "category": "accessory", "label": "hat", "title": "Шапка"},
    {"subcategory": "cap", "category": "accessory", "label": "cap", "title": "Кепка"},
    {"subcategory": "gloves", "category": "accessory", "label": "gloves", "title": "Перчатки"},
    {"subcategory": "belt", "category": "accessory", "label": "belt", "title": "Ремень"},
    {"subcategory": "jewelry", "category": "accessory", "label": "jewelry", "title": "Украшение"},
]

FPID_COMPAT_CANDIDATES = [
    {"subcategory": "bag", "category": "accessory", "label": "bag", "title": "Сумка"},
    {"subcategory": "belt", "category": "accessory", "label": "belt", "title": "Ремень"},
    {"subcategory": "bracelet", "category": "accessory", "label": "bracelet", "title": "Браслет"},
    {"subcategory": "dress", "category": "dress", "label": "dress", "title": "Платье"},
    {"subcategory": "earrings", "category": "accessory", "label": "earrings", "title": "Серьги"},
    {"subcategory": "hat", "category": "accessory", "label": "hat", "title": "Головной убор"},
    {"subcategory": "jacket", "category": "outerwear", "label": "jacket", "title": "Куртка"},
    {"subcategory": "jeans", "category": "bottom", "label": "jeans", "title": "Джинсы"},
    {"subcategory": "jewelry", "category": "accessory", "label": "jewelry", "title": "Украшение"},
    {"subcategory": "joggers", "category": "bottom", "label": "joggers", "title": "Джоггеры"},
    {"subcategory": "kurta", "category": "top", "label": "kurta", "title": "Курта"},
    {"subcategory": "leggings", "category": "bottom", "label": "leggings", "title": "Леггинсы"},
    {"subcategory": "necklace", "category": "accessory", "label": "necklace", "title": "Ожерелье"},
    {"subcategory": "sandals", "category": "shoes", "label": "sandals", "title": "Сандалии"},
    {"subcategory": "scarf", "category": "accessory", "label": "scarf", "title": "Шарф"},
    {"subcategory": "shirt", "category": "top", "label": "shirt", "title": "Рубашка"},
    {"subcategory": "shoes", "category": "shoes", "label": "shoes", "title": "Обувь"},
    {"subcategory": "shorts", "category": "bottom", "label": "shorts", "title": "Шорты"},
    {"subcategory": "skirt", "category": "bottom", "label": "skirt", "title": "Юбка"},
    {"subcategory": "sleepwear", "category": "top", "label": "sleepwear", "title": "Одежда для сна"},
    {"subcategory": "sneakers", "category": "shoes", "label": "sneakers", "title": "Кроссовки"},
    {"subcategory": "socks", "category": "accessory", "label": "socks", "title": "Носки"},
    {"subcategory": "sunglasses", "category": "accessory", "label": "sunglasses", "title": "Солнцезащитные очки"},
    {"subcategory": "sweater", "category": "top", "label": "sweater", "title": "Свитер"},
    {"subcategory": "sweatshirt", "category": "top", "label": "sweatshirt", "title": "Свитшот"},
    {"subcategory": "t_shirt", "category": "top", "label": "t-shirt", "title": "Футболка"},
    {"subcategory": "tie", "category": "accessory", "label": "tie", "title": "Галстук"},
    {"subcategory": "top", "category": "top", "label": "top", "title": "Топ"},
    {"subcategory": "trousers", "category": "bottom", "label": "trousers", "title": "Брюки"},
    {"subcategory": "tunic", "category": "top", "label": "tunic", "title": "Туника"},
    {"subcategory": "underwear", "category": "top", "label": "underwear", "title": "Нижнее белье"},
    {"subcategory": "wallet", "category": "accessory", "label": "wallet", "title": "Кошелек"},
    {"subcategory": "watch", "category": "accessory", "label": "watch", "title": "Часы"},
]

SUBCATEGORY_LOOKUP = {
    candidate["subcategory"]: candidate for candidate in [*SUBCATEGORY_CANDIDATES, *FPID_COMPAT_CANDIDATES]
}
LABEL_LOOKUP = {
    candidate["label"]: candidate for candidate in [*SUBCATEGORY_CANDIDATES, *FPID_COMPAT_CANDIDATES]
}

COLOR_PALETTE = {
    "white": (246, 243, 236),
    "cream": (243, 232, 216),
    "black": (23, 23, 23),
    "silver": (200, 204, 214),
    "gray": (141, 147, 155),
    "beige": (220, 199, 161),
    "camel": (183, 135, 83),
    "brown": (139, 90, 60),
    "blue": (76, 132, 217),
    "sky_blue": (125, 185, 239),
    "navy": (29, 55, 100),
    "turquoise": (72, 184, 199),
    "green": (78, 140, 98),
    "olive": (123, 132, 80),
    "red": (207, 78, 78),
    "burgundy": (122, 47, 65),
    "yellow": (235, 203, 83),
    "orange": (239, 149, 81),
    "pink": (230, 166, 189),
    "lavender": (184, 165, 223),
    "purple": (141, 107, 199),
}

STYLE_SUGGESTIONS = {
    "top": ["casual"],
    "dress": ["classic", "casual"],
    "bottom": ["casual"],
    "shoes": ["casual"],
    "outerwear": ["classic"],
    "accessory": ["minimal"],
    "hoodie": ["sport", "casual"],
    "sweatshirt": ["sport", "casual"],
    "sneakers": ["casual", "sport"],
    "summer_sneakers": ["casual", "sport"],
    "sandals": ["casual"],
    "blazer": ["classic", "business"],
    "trench": ["classic", "minimal"],
    "coat": ["classic", "minimal"],
    "jewelry": ["evening", "classic"],
    "bracelet": ["evening", "classic"],
    "earrings": ["evening", "classic"],
    "necklace": ["evening", "classic"],
    "watch": ["classic", "business"],
    "bag": ["minimal", "classic"],
    "backpack": ["casual", "travel"],
    "wallet": ["minimal", "classic"],
    "tie": ["business", "classic"],
    "sunglasses": ["casual", "statement"],
    "joggers": ["sport", "casual"],
    "leggings": ["sport", "casual"],
}

FORMALITY_SUGGESTIONS = {
    "default": "casual",
    "shirt": "smart",
    "blouse": "smart",
    "trousers": "smart",
    "chinos": "smart",
    "blazer": "formal",
    "coat": "formal",
    "trench": "smart",
    "loafers": "smart",
    "pumps": "formal",
    "closed_shoes": "smart",
    "jewelry": "formal",
    "bracelet": "formal",
    "earrings": "formal",
    "necklace": "formal",
    "tie": "formal",
    "watch": "smart",
    "bag": "smart",
    "wallet": "smart",
    "dress": "smart",
}

SEASON_SUGGESTIONS = {
    "default": "all-season",
    "sandals": "summer",
    "espadrilles": "summer",
    "flip_flops": "summer",
    "slippers": "summer",
    "shorts": "summer",
    "mini_skirt": "summer",
    "winter_boots": "winter",
    "felt_boots": "winter",
    "warm_boots": "winter",
    "down_jacket": "winter",
    "parka": "winter",
    "coat": "autumn",
    "trench": "spring",
    "windbreaker": "spring",
}

FIT_SUGGESTIONS = {
    "default": "balanced",
    "shirt": "fitted",
    "blouse": "fitted",
    "turtleneck": "fitted",
    "hoodie": "oversized",
    "parka": "oversized",
    "down_jacket": "oversized",
    "joggers": "loose",
    "leggings": "fitted",
    "loafers": "fitted",
    "pumps": "fitted",
    "belt": "fitted",
    "jewelry": "fitted",
}

FIT_SUPPORTED_CATEGORIES = {"top", "dress", "bottom", "outerwear"}
LAYER_LEVEL_SUPPORTED_CATEGORIES = {"top", "dress", "outerwear"}
INSULATION_SUPPORTED_CATEGORIES = {"top", "dress", "bottom", "shoes", "outerwear"}
WATERPROOF_SUPPORTED_CATEGORIES = {"outerwear", "shoes"}
WINDPROOF_SUPPORTED_CATEGORIES = {"outerwear"}

LAYER_LEVEL_SUGGESTIONS = {
    "default": None,
    "category_top": "base",
    "category_dress": "base",
    "category_outerwear": "outer",
    "category_accessory": "support",
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
    "wallet": "support",
    "scarf": "support",
    "hat": "support",
    "cap": "support",
    "gloves": "support",
    "belt": "support",
    "jewelry": "support",
    "bracelet": "support",
    "earrings": "support",
    "necklace": "support",
    "tie": "support",
    "watch": "support",
    "sunglasses": "support",
    "socks": "support",
}

INSULATION_SUGGESTIONS = {
    "default": 0.6,
    "crop_top": 0.2,
    "shorts": 0.3,
    "dress": 0.8,
    "top": 0.5,
    "kurta": 0.8,
    "tunic": 0.8,
    "underwear": 0.2,
    "sleepwear": 0.6,
    "sandals": 0.2,
    "shoes": 0.8,
    "sneakers": 0.9,
    "flip_flops": 0.1,
    "slippers": 0.1,
    "winter_boots": 2.0,
    "felt_boots": 2.2,
    "warm_boots": 1.9,
    "down_jacket": 2.8,
    "parka": 2.6,
    "coat": 2.4,
    "sweater": 1.8,
    "hoodie": 1.7,
    "cardigan": 1.4,
    "trench": 1.5,
    "jacket": 1.7,
}

WATERPROOF_SUBCATEGORIES = {"trench", "parka", "down_jacket", "windbreaker", "jacket"}
WINDPROOF_SUBCATEGORIES = {"coat", "parka", "down_jacket", "windbreaker", "leather_jacket"}

SHOE_SUBCATEGORIES = {
    "ankle_boots",
    "boots",
    "closed_shoes",
    "demi_boots",
    "espadrilles",
    "felt_boots",
    "flats",
    "flip_flops",
    "loafers",
    "pumps",
    "sandals",
    "shoes",
    "slippers",
    "sneakers",
    "summer_sneakers",
    "warm_boots",
    "winter_boots",
}

ZAPPOS_SUSPECT_SUBCATEGORIES = {
    "bracelet",
    "earrings",
    "jewelry",
    "necklace",
    "sunglasses",
    "watch",
}

DEFAULT_DEEPFASHION_CHECKPOINT_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "deepfashion_classifier.pt"
DEFAULT_DEEPFASHION_METADATA_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "deepfashion_classifier.metadata.json"
DEFAULT_ZAPPOS_CHECKPOINT_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "zappos_classifier.pt"
DEFAULT_ZAPPOS_METADATA_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "zappos_classifier.metadata.json"
DEFAULT_FPID_CHECKPOINT_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "fpid_classifier.pt"
DEFAULT_FPID_METADATA_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "fpid_classifier.metadata.json"

MODEL_ARTIFACTS_DIR = PROJECT_ROOT / "backend" / "model_artifacts"
MODEL_LOGS_DIR = PROJECT_ROOT / "backend" / "logs"
MODEL_PREDICTIONS_LOG_PATH = MODEL_LOGS_DIR / "fashion_model_predictions.jsonl"

APPAREL_CATEGORIES = {"top", "bottom", "outerwear", "dress"}
DEEPFASHION_PRIMARY_CATEGORIES = {"top", "bottom", "outerwear"}
FPID_PRIMARY_SUBCATEGORIES = {"dress"}
FPID_PRIMARY_CATEGORIES = {"accessory"}
FPID_SHOE_HINT_SUBCATEGORIES = SHOE_SUBCATEGORIES | {"sandals", "shoes", "sneakers"}
DEEPFASHION_EARLY_PRIORITY_CATEGORIES = {"top", "bottom", "outerwear"}

FPID_ACCESSORY_SUBCATEGORIES = {
    "bag",
    "belt",
    "bracelet",
    "earrings",
    "hat",
    "jewelry",
    "necklace",
    "scarf",
    "socks",
    "sunglasses",
    "tie",
    "wallet",
    "watch",
}

FPID_COMMON_APPAREL_MISTAKES = {
    "tie",
    "scarf",
    "belt",
    "socks",
    "bracelet",
    "necklace",
    "jewelry",
    "watch",
    "sunglasses",
}

DRESS_SUPPORT_SUBCATEGORIES = {"dress", "skirt", "top", "shirt", "blouse", "tunic"}


class FashionImageService:
    def __init__(self):
        self.enabled = os.getenv("FASHION_AI_ENABLED", "true").lower() == "true"
        self.model_id = os.getenv("FASHION_AI_MODEL_ID", "openai/clip-vit-base-patch32")
        self.deepfashion_threshold = float(os.getenv("DEEPFASHION_CONFIDENCE_THRESHOLD", "0.55"))
        self.deepfashion_early_priority_threshold = float(os.getenv("DEEPFASHION_EARLY_PRIORITY_THRESHOLD", "0.30"))
        self.deepfashion_apparel_fallback_threshold = float(
            os.getenv("DEEPFASHION_APPAREL_FALLBACK_THRESHOLD", "0.18")
        )
        self.fpid_primary_confidence_threshold = float(os.getenv("FPID_PRIMARY_CONFIDENCE_THRESHOLD", "0.58"))
        self.fpid_accessory_confidence_threshold = float(os.getenv("FPID_ACCESSORY_CONFIDENCE_THRESHOLD", "0.76"))
        self.fpid_dress_hint_threshold = float(os.getenv("FPID_DRESS_HINT_THRESHOLD", "0.18"))
        self.fpid_dress_shape_threshold = float(os.getenv("FPID_DRESS_SHAPE_THRESHOLD", "0.08"))
        self.zappos_enabled = os.getenv("ZAPPOS_CLASSIFIER_ENABLED", "true").lower() == "true"
        self.zappos_top_shoe_score_threshold = float(os.getenv("ZAPPOS_TOP_SHOE_SCORE_THRESHOLD", "0.05"))
        self.zappos_fallback_confidence_threshold = float(os.getenv("ZAPPOS_FALLBACK_CONFIDENCE_THRESHOLD", "0.62"))
        self._pipeline = None

        deepfashion_checkpoint_path = os.getenv(
            "DEEPFASHION_CHECKPOINT_PATH",
            str(
                self._first_existing_path(
                    [
                        DEFAULT_DEEPFASHION_CHECKPOINT_PATH,
                        MODEL_ARTIFACTS_DIR / "deepfashion_classifier.pth",
                        MODEL_ARTIFACTS_DIR / "deepfashion_local_classifier.pt",
                    ],
                    DEFAULT_DEEPFASHION_CHECKPOINT_PATH,
                )
            ),
        )
        deepfashion_metadata_path = os.getenv(
            "DEEPFASHION_METADATA_PATH",
            str(
                self._first_existing_path(
                    [
                        DEFAULT_DEEPFASHION_METADATA_PATH,
                        MODEL_ARTIFACTS_DIR / "deepfashion_local_classifier.metadata.json",
                    ],
                    DEFAULT_DEEPFASHION_METADATA_PATH,
                )
            ),
        )
        fpid_checkpoint_path = os.getenv(
            "FPID_CHECKPOINT_PATH",
            str(
                self._first_existing_path(
                    [
                        DEFAULT_FPID_CHECKPOINT_PATH,
                        MODEL_ARTIFACTS_DIR / "fpid_classifier.pth",
                        MODEL_ARTIFACTS_DIR / "fashion_product_images_classifier.pt",
                    ],
                    DEFAULT_FPID_CHECKPOINT_PATH,
                )
            ),
        )
        fpid_metadata_path = os.getenv(
            "FPID_METADATA_PATH",
            str(
                self._first_existing_path(
                    [
                        DEFAULT_FPID_METADATA_PATH,
                        MODEL_ARTIFACTS_DIR / "fashion_product_images_classifier.metadata.json",
                    ],
                    DEFAULT_FPID_METADATA_PATH,
                )
            ),
        )
        zappos_checkpoint_path = os.getenv(
            "ZAPPOS_CHECKPOINT_PATH",
            str(
                self._first_existing_path(
                    [
                        DEFAULT_ZAPPOS_CHECKPOINT_PATH,
                        MODEL_ARTIFACTS_DIR / "zappos_classifier.pth",
                        MODEL_ARTIFACTS_DIR / "wardrobe_zappos_classifier.pt",
                    ],
                    DEFAULT_ZAPPOS_CHECKPOINT_PATH,
                )
            ),
        )
        zappos_metadata_path = os.getenv(
            "ZAPPOS_METADATA_PATH",
            str(
                self._first_existing_path(
                    [
                        DEFAULT_ZAPPOS_METADATA_PATH,
                        MODEL_ARTIFACTS_DIR / "wardrobe_zappos_classifier.metadata.json",
                    ],
                    DEFAULT_ZAPPOS_METADATA_PATH,
                )
            ),
        )

        self._deepfashion_classifier = DeepFashionLocalClassifier(
            checkpoint_path=deepfashion_checkpoint_path,
            metadata_path=deepfashion_metadata_path,
            model_slug="deepfashion-local",
            missing_model="deepfashion-local",
            default_source_dataset="DeepFashion Category and Attribute Prediction Benchmark",
        )
        self._fpid_classifier = DeepFashionLocalClassifier(
            checkpoint_path=fpid_checkpoint_path,
            metadata_path=fpid_metadata_path,
            model_slug="fpid-local",
            missing_model="fpid-local",
            default_source_dataset="Fashion Product Images",
        )
        self._shoe_classifier = DeepFashionLocalClassifier(
            checkpoint_path=zappos_checkpoint_path,
            metadata_path=zappos_metadata_path,
            model_slug="zappos-local",
            missing_model="zappos-local",
            default_source_dataset="Zappos",
        )

    @staticmethod
    def _first_existing_path(paths, fallback):
        for path in paths:
            if path.exists():
                return path
        return fallback

    def analyze_upload(self, file_storage):
        raw_image = self._read_file_storage(file_storage)
        processed_image = self._remove_background(raw_image)
        colors = self._extract_palette_colors(processed_image)
        classification = self._classify_image(processed_image, original_filename=file_storage.filename)
        suggestions = self._build_attribute_suggestions(classification.get("subcategory"), colors)

        return {
            "background_removed": True,
            "category": suggestions.get("category"),
            "subcategory": suggestions.get("subcategory"),
            "title_suggestion": suggestions.get("title_suggestion"),
            "colors": colors,
            "styles": suggestions.get("styles", []),
            "season": suggestions.get("season"),
            "formality": suggestions.get("formality"),
            "fit": suggestions.get("fit"),
            "layer_level": suggestions.get("layer_level"),
            "insulation_rating": suggestions.get("insulation_rating"),
            "waterproof": suggestions.get("waterproof"),
            "windproof": suggestions.get("windproof"),
            "confidence": classification.get("confidence"),
            "top_predictions": self._normalize_top_predictions(classification.get("top_predictions", [])),
            "model": classification.get("model") or self.model_id,
            "source_dataset": classification.get("source_dataset"),
            "classification_route": classification.get("classification_route"),
            "base_model": classification.get("base_model"),
            "base_subcategory": classification.get("base_subcategory"),
            "warnings": classification.get("warnings", []),
        }

    def process_and_store_upload(self, file_storage, upload_folder):
        raw_image = self._read_file_storage(file_storage)
        processed_image = self._remove_background(raw_image)
        return save_image_bytes(processed_image, upload_folder, extension="png")

    def _read_file_storage(self, file_storage):
        if not file_storage or not file_storage.filename:
            raise ApiError("Необходимо загрузить изображение.", 400)

        file_storage.stream.seek(0)
        image_bytes = file_storage.read()
        file_storage.stream.seek(0)
        if not image_bytes:
            raise ApiError("Не удалось прочитать изображение.", 400)
        return image_bytes

    def _remove_background(self, image_bytes):
        try:
            from rembg import remove
        except ImportError as error:
            raise ApiError(
                "Фоновое удаление недоступно. Установите зависимости rembg и onnxruntime.",
                500,
            ) from error

        try:
            result = remove(image_bytes)
        except Exception as error:  # pragma: no cover
            raise ApiError(
                "Не удалось удалить фон с изображения. Проверьте, что модель rembg доступна.",
                500,
            ) from error

        if not result:
            raise ApiError("Сервис удаления фона вернул пустой результат.", 500)
        return result

    def _classify_image(self, image_bytes, original_filename=None):
        if not self.enabled:
            return {
                "subcategory": None,
                "confidence": None,
                "top_predictions": [],
                "warnings": ["Автоматическое распознавание типа вещи отключено в настройках."],
                "model": None,
            }

        deepfashion_result = self._deepfashion_classifier.predict(image_bytes)
        fpid_result = self._fpid_classifier.predict(image_bytes)
        zero_shot_result = None
        zappos_result = None

        ensemble_result = self._classify_with_ensemble(image_bytes, deepfashion_result, fpid_result)
        if ensemble_result:
            zappos_result = ensemble_result.get("_zappos_result")
            self._log_model_predictions(
                original_filename,
                deepfashion_result,
                fpid_result,
                zappos_result,
                zero_shot_result,
                ensemble_result,
            )
            if "_zappos_result" in ensemble_result:
                ensemble_result = dict(ensemble_result)
                ensemble_result.pop("_zappos_result", None)
            return ensemble_result

        zero_shot_result = self._classify_image_zero_shot(image_bytes)
        warnings = self._merge_warnings(deepfashion_result, fpid_result)
        deepfashion_confidence = float(deepfashion_result.get("confidence") or 0.0)

        if deepfashion_result.get("subcategory") and not zero_shot_result.get("subcategory"):
            if deepfashion_confidence < self.deepfashion_threshold:
                warnings.append(
                    "Локальная DeepFashion-модель дала результат с пониженной уверенностью. Использован лучший доступный прогноз."
                )
            result = dict(deepfashion_result)
            result["warnings"] = warnings
            result["classification_route"] = result.get("classification_route") or "deepfashion_fallback"
            self._log_model_predictions(
                original_filename,
                deepfashion_result,
                fpid_result,
                zappos_result,
                zero_shot_result,
                result,
            )
            return result

        if zero_shot_result.get("subcategory"):
            if deepfashion_result.get("subcategory") and deepfashion_confidence < self.deepfashion_threshold:
                warnings.append(
                    "Локальная DeepFashion-модель дала низкую уверенность. Выполнен резервный zero-shot анализ."
                )
            zero_shot_result["warnings"] = warnings + zero_shot_result.get("warnings", [])
            zero_shot_result["classification_route"] = zero_shot_result.get("classification_route") or "zero_shot"
            self._log_model_predictions(
                original_filename,
                deepfashion_result,
                fpid_result,
                zappos_result,
                zero_shot_result,
                zero_shot_result,
            )
            return zero_shot_result

        result = dict(deepfashion_result)
        result["warnings"] = warnings + zero_shot_result.get("warnings", [])
        result["classification_route"] = result.get("classification_route") or "deepfashion_fallback"
        self._log_model_predictions(
            original_filename,
            deepfashion_result,
            fpid_result,
            zappos_result,
            zero_shot_result,
            result,
        )
        return result

    def _classify_with_ensemble(self, image_bytes, deepfashion_result, fpid_result):
        deepfashion_subcategory = deepfashion_result.get("subcategory")
        fpid_subcategory = fpid_result.get("subcategory")
        deepfashion_candidate = SUBCATEGORY_LOOKUP.get(deepfashion_subcategory) if deepfashion_subcategory else None
        fpid_candidate = SUBCATEGORY_LOOKUP.get(fpid_subcategory) if fpid_subcategory else None
        deepfashion_category = deepfashion_candidate.get("category") if deepfashion_candidate else None
        fpid_category = fpid_candidate.get("category") if fpid_candidate else None
        deepfashion_confidence = float(deepfashion_result.get("confidence") or 0.0)
        fpid_confidence = float(fpid_result.get("confidence") or 0.0)
        warnings = self._merge_warnings(deepfashion_result, fpid_result)
        metrics = self._get_object_metrics(image_bytes)
        deepfashion_bottom_like = deepfashion_category == "bottom" or deepfashion_subcategory in {
            "skirt",
            "mini_skirt",
            "midi_skirt",
            "maxi_skirt",
        }
        dress_override = self._resolve_fpid_dress_override(image_bytes, deepfashion_result, fpid_result)
        if dress_override:
            return self._build_override_result(
                fpid_result,
                subcategory="dress",
                confidence=dress_override,
                route="deepfashion_checked_by_fpid_dress",
                warnings=warnings,
                base_result=deepfashion_result,
            )

        deepfashion_is_shoe = (
            deepfashion_subcategory in SHOE_SUBCATEGORIES
            or deepfashion_category == "shoes"
        )
        fpid_is_shoe = (
            fpid_subcategory in SHOE_SUBCATEGORIES
            or fpid_category == "shoes"
        )
        deepfashion_shoe_signal = self._top_prediction_shoe_score(deepfashion_result)
        fpid_shoe_signal = self._top_prediction_shoe_score(fpid_result)
        looks_like_shoe_object = self._looks_like_shoe_object_from_metrics(metrics)

        shoe_base_result = None
        if deepfashion_is_shoe:
            shoe_base_result = deepfashion_result
        elif fpid_is_shoe:
            shoe_base_result = fpid_result
        elif (
            not deepfashion_bottom_like
            and looks_like_shoe_object
            and max(deepfashion_shoe_signal, fpid_shoe_signal) >= 0.08
            and deepfashion_confidence < 0.82
        ):
            shoe_base_result = fpid_result if fpid_shoe_signal >= deepfashion_shoe_signal else deepfashion_result

        if shoe_base_result:
            zappos_route = self._zappos_refinement_route(shoe_base_result, image_bytes)
            if zappos_route:
                return self._refine_shoe_prediction(image_bytes, shoe_base_result, zappos_route)

            result = dict(shoe_base_result)
            result["warnings"] = warnings
            result["classification_route"] = "shoe_fallback"
            return result

        deepfashion_apparel_like = deepfashion_category in APPAREL_CATEGORIES
        fpid_accessory_trustworthy = (
            fpid_category == "accessory"
            and fpid_subcategory
            and self._is_fpid_accessory_trustworthy(fpid_result, metrics)
        )
        strong_fpid_accessory_override = (
            fpid_accessory_trustworthy
            and fpid_confidence >= max(self.fpid_accessory_confidence_threshold, deepfashion_confidence + 0.20)
        )

        if strong_fpid_accessory_override and (
            not deepfashion_bottom_like
            or deepfashion_confidence < 0.50
        ):
            return self._build_override_result(
                fpid_result,
                subcategory=fpid_subcategory,
                confidence=fpid_confidence,
                route="fpid_primary_accessory_strong",
                warnings=warnings,
                base_result=deepfashion_result,
            )

        if fpid_accessory_trustworthy and (
            not deepfashion_apparel_like
            or (deepfashion_category in {"top", "outerwear"} and deepfashion_confidence < 0.72)
        ):
            return self._build_override_result(
                fpid_result,
                subcategory=fpid_subcategory,
                confidence=fpid_confidence,
                route="fpid_primary_accessory",
                warnings=warnings,
                base_result=deepfashion_result,
            )

        if deepfashion_bottom_like and deepfashion_subcategory:
            result = dict(deepfashion_result)
            result["warnings"] = warnings
            result["classification_route"] = (
                "deepfashion_primary"
                if deepfashion_confidence >= self.deepfashion_threshold
                else "deepfashion_primary_low_confidence"
            )
            result["support_model"] = fpid_result.get("model")
            result["support_subcategory"] = fpid_subcategory
            result["support_confidence"] = fpid_result.get("confidence")
            return result

        if deepfashion_subcategory and deepfashion_confidence >= self.deepfashion_threshold:
            result = dict(deepfashion_result)
            result["warnings"] = warnings
            result["classification_route"] = "deepfashion_primary"
            result["support_model"] = fpid_result.get("model")
            result["support_subcategory"] = fpid_subcategory
            result["support_confidence"] = fpid_result.get("confidence")
            return result

        if deepfashion_subcategory:
            result = dict(deepfashion_result)
            result["warnings"] = warnings
            result["classification_route"] = "deepfashion_primary_low_confidence"
            result["support_model"] = fpid_result.get("model")
            result["support_subcategory"] = fpid_subcategory
            result["support_confidence"] = fpid_result.get("confidence")
            return result

        if fpid_accessory_trustworthy:
            return self._build_override_result(
                fpid_result,
                subcategory=fpid_subcategory,
                confidence=fpid_confidence,
                route="fpid_primary_accessory",
                warnings=warnings,
                base_result=deepfashion_result,
            )

        return None

    def _build_override_result(self, source_result, subcategory, confidence, route, warnings, base_result=None):
        result = dict(source_result)
        result["subcategory"] = subcategory
        result["confidence"] = round(float(confidence), 4)
        existing_predictions = result.get("top_predictions", []) or []
        override_prediction = None
        for prediction in existing_predictions:
            if prediction.get("subcategory") == subcategory:
                override_prediction = dict(prediction)
                break

        candidate = SUBCATEGORY_LOOKUP.get(subcategory)
        if not override_prediction and candidate:
            override_prediction = {
                "subcategory": subcategory,
                "category": candidate["category"],
                "label": candidate["title"],
                "score": round(float(confidence), 4),
            }
        elif override_prediction:
            override_prediction["score"] = round(float(confidence), 4)

        result["top_predictions"] = [override_prediction] + [
            prediction
            for prediction in existing_predictions
            if prediction.get("subcategory") != subcategory
        ] if override_prediction else existing_predictions
        result["warnings"] = warnings
        result["classification_route"] = route
        if base_result:
            result["base_model"] = base_result.get("model")
            result["base_subcategory"] = base_result.get("subcategory")
            result["base_confidence"] = base_result.get("confidence")
        return result

    def _resolve_fpid_dress_override(self, image_bytes, deepfashion_result, fpid_result):
        fpid_subcategory = fpid_result.get("subcategory")
        fpid_confidence = float(fpid_result.get("confidence") or 0.0)
        deepfashion_subcategory = deepfashion_result.get("subcategory")
        deepfashion_candidate = SUBCATEGORY_LOOKUP.get(deepfashion_subcategory) if deepfashion_subcategory else None
        deepfashion_category = deepfashion_candidate.get("category") if deepfashion_candidate else None
        if deepfashion_category not in {"top", "bottom"} and deepfashion_subcategory not in {
            "skirt",
            "mini_skirt",
            "midi_skirt",
            "maxi_skirt",
        }:
            return None

        if fpid_subcategory == "dress" and fpid_confidence >= self.fpid_primary_confidence_threshold:
            return fpid_confidence

        dress_signal = self._extract_prediction_score(fpid_result, "dress")
        if dress_signal >= self.fpid_dress_hint_threshold:
            return dress_signal

        return None

    def _pick_best_shoe_base_result(self, deepfashion_result, fpid_result):
        deepfashion_score = self._shoe_signal_score(deepfashion_result)
        fpid_score = self._shoe_signal_score(fpid_result)

        if deepfashion_score <= 0.0 and fpid_score <= 0.0:
            return None
        return deepfashion_result if deepfashion_score >= fpid_score else fpid_result

    def _shoe_signal_score(self, classification):
        subcategory = classification.get("subcategory")
        if not subcategory:
            return 0.0

        candidate = SUBCATEGORY_LOOKUP.get(subcategory)
        confidence = float(classification.get("confidence") or 0.0)
        score = 0.0

        if subcategory in FPID_SHOE_HINT_SUBCATEGORIES:
            score += 1.0
        if candidate and candidate.get("category") == "shoes":
            score += 1.0

        score += confidence
        score += sum(
            float(prediction.get("score") or 0.0)
            for prediction in classification.get("top_predictions", [])[:3]
            if prediction.get("subcategory") in FPID_SHOE_HINT_SUBCATEGORIES
        )
        return score

    def _merge_warnings(self, *results):
        merged = []
        seen = set()
        for result in results:
            for warning in result.get("warnings", []):
                if warning not in seen:
                    seen.add(warning)
                    merged.append(warning)
        return merged

    def _log_model_predictions(
        self,
        original_filename,
        deepfashion_result,
        fpid_result,
        zappos_result,
        zero_shot_result,
        final_result,
    ):
        try:
            MODEL_LOGS_DIR.mkdir(parents=True, exist_ok=True)
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "filename": original_filename,
                "deepfashion": self._serialize_prediction_result(deepfashion_result),
                "fpid": self._serialize_prediction_result(fpid_result),
                "zappos": self._serialize_prediction_result(zappos_result),
                "zero_shot": self._serialize_prediction_result(zero_shot_result),
                "final": self._serialize_prediction_result(final_result),
            }
            with MODEL_PREDICTIONS_LOG_PATH.open("a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            return

    def _serialize_prediction_result(self, result):
        if not result:
            return None
        return {
            "subcategory": result.get("subcategory"),
            "confidence": result.get("confidence"),
            "model": result.get("model"),
            "source_dataset": result.get("source_dataset"),
            "classification_route": result.get("classification_route"),
            "base_model": result.get("base_model"),
            "base_subcategory": result.get("base_subcategory"),
            "top_predictions": result.get("top_predictions", []),
            "warnings": result.get("warnings", []),
        }

    def _extract_prediction_score(self, classification, subcategory):
        if classification.get("subcategory") == subcategory:
            return float(classification.get("confidence") or 0.0)

        for prediction in classification.get("top_predictions", []):
            if prediction.get("subcategory") == subcategory:
                return float(prediction.get("score") or 0.0)
        return 0.0

    def _zappos_refinement_route(self, classification, image_bytes):
        if not self.zappos_enabled:
            return None

        subcategory = classification.get("subcategory")
        if not subcategory:
            return None

        candidate = SUBCATEGORY_LOOKUP.get(subcategory)
        if subcategory in SHOE_SUBCATEGORIES or (candidate and candidate.get("category") == "shoes"):
            return "ensemble_to_zappos_shoes"
        if self._top_prediction_shoe_score(classification) >= self.zappos_top_shoe_score_threshold:
            return "ensemble_to_zappos_top3_shoes"
        if subcategory in ZAPPOS_SUSPECT_SUBCATEGORIES and self._looks_like_horizontal_shoe_object(image_bytes):
            return "ensemble_to_zappos_shape_fallback"
        return None

    def _top_prediction_shoe_score(self, classification):
        return sum(
            float(prediction.get("score") or 0.0)
            for prediction in classification.get("top_predictions", [])
            if prediction.get("subcategory") in SHOE_SUBCATEGORIES
        )

    def _get_object_metrics(self, image_bytes):
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            return None

        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGBA")
            image.thumbnail((320, 320))
            pixels = np.array(image)
        except Exception:
            return None

        alpha = pixels[:, :, 3]
        if alpha.min() < 250:
            mask = alpha > 24
        else:
            rgb = pixels[:, :, :3].astype(int)
            corners = np.concatenate(
                [
                    rgb[:8, :8].reshape(-1, 3),
                    rgb[:8, -8:].reshape(-1, 3),
                    rgb[-8:, :8].reshape(-1, 3),
                    rgb[-8:, -8:].reshape(-1, 3),
                ]
            )
            background = np.median(corners, axis=0)
            distance = np.linalg.norm(rgb - background, axis=2)
            mask = distance > 28

        ys, xs = np.where(mask)
        if len(xs) == 0 or len(ys) == 0:
            return None

        img_h, img_w = mask.shape
        x1, x2 = xs.min(), xs.max()
        y1, y2 = ys.min(), ys.max()
        box_w = x2 - x1 + 1
        box_h = y2 - y1 + 1
        row_counts = mask[y1 : y2 + 1, x1 : x2 + 1].sum(axis=1)
        max_row_width = int(row_counts.max()) if len(row_counts) else box_w

        return {
            "image_width": img_w,
            "image_height": img_h,
            "box_width": box_w,
            "box_height": box_h,
            "width_coverage": box_w / max(img_w, 1),
            "height_coverage": box_h / max(img_h, 1),
            "top_coverage": y1 / max(img_h, 1),
            "bottom_coverage": y2 / max(img_h, 1),
            "object_area": float(mask.mean()),
            "aspect_width": box_w / max(box_h, 1),
            "aspect_height": box_h / max(box_w, 1),
            "max_row_width_ratio": max_row_width / max(img_w, 1),
        }

    def _looks_like_horizontal_shoe_object(self, image_bytes):
        metrics = self._get_object_metrics(image_bytes)
        if not metrics:
            return False
        return self._looks_like_shoe_object_from_metrics(metrics)

    def _looks_like_shoe_object_from_metrics(self, metrics):
        if not metrics:
            return False
        return self._looks_like_horizontal_shoe_object_from_metrics(metrics) or self._looks_like_tall_shoe_object_from_metrics(
            metrics
        )

    def _looks_like_horizontal_shoe_object_from_metrics(self, metrics):
        return (
            metrics["aspect_width"] >= 1.15
            and 0.03 <= metrics["object_area"] <= 0.65
            and metrics["height_coverage"] <= 0.72
        )

    def _looks_like_tall_shoe_object_from_metrics(self, metrics):
        return (
            metrics["aspect_height"] >= 1.18
            and 0.03 <= metrics["object_area"] <= 0.58
            and metrics["width_coverage"] <= 0.52
            and metrics["height_coverage"] <= 0.88
        )

    def _looks_like_long_one_piece_garment(self, image_bytes):
        metrics = self._get_object_metrics(image_bytes)
        if not metrics:
            return False

        return (
            metrics["aspect_height"] >= 1.18
            and metrics["height_coverage"] >= 0.66
            and metrics["top_coverage"] <= 0.26
            and metrics["bottom_coverage"] >= 0.78
            and metrics["object_area"] >= 0.12
            and metrics["width_coverage"] >= 0.22
        )

    def _looks_like_large_apparel_object(self, metrics):
        if not metrics:
            return False
        return (
            metrics["height_coverage"] >= 0.52
            and metrics["object_area"] >= 0.10
            and metrics["aspect_height"] >= 0.95
        )

    def _is_fpid_accessory_trustworthy(self, fpid_result, metrics):
        subcategory = fpid_result.get("subcategory")
        if subcategory not in FPID_ACCESSORY_SUBCATEGORIES:
            return False
        if not metrics:
            return True

        confidence = float(fpid_result.get("confidence") or 0.0)
        if subcategory == "tie":
            return (
                confidence >= self.fpid_accessory_confidence_threshold
                and metrics["aspect_height"] >= 2.25
                and 0.02 <= metrics["object_area"] <= 0.24
                and metrics["max_row_width_ratio"] <= 0.42
            )
        if subcategory == "belt":
            return metrics["aspect_width"] >= 1.85 and metrics["height_coverage"] <= 0.48
        if subcategory in {"bracelet", "earrings", "jewelry", "necklace", "sunglasses", "watch"}:
            return confidence >= 0.55 and metrics["object_area"] <= 0.55 and metrics["height_coverage"] <= 0.88
        if subcategory in {"wallet", "socks"}:
            return confidence >= 0.52 and metrics["object_area"] <= 0.50 and metrics["height_coverage"] <= 0.82
        if subcategory in {"bag", "hat", "scarf"}:
            return confidence >= 0.58 and not (
                deepfashion_like := self._looks_like_large_apparel_object(metrics)
            ) or (confidence >= 0.82 and deepfashion_like)
        return True

    def _refine_shoe_prediction(self, image_bytes, base_result, route):
        zappos_result = self._shoe_classifier.predict(image_bytes)
        warnings = self._merge_warnings(base_result, zappos_result)

        if not zappos_result.get("subcategory"):
            fallback_result = dict(base_result)
            fallback_result["warnings"] = warnings
            fallback_result["classification_route"] = "zappos_unavailable"
            fallback_result["base_model"] = base_result.get("model")
            fallback_result["base_subcategory"] = base_result.get("subcategory")
            return fallback_result

        zappos_confidence = float(zappos_result.get("confidence") or 0.0)
        if route != "ensemble_to_zappos_shoes" and zappos_confidence < self.zappos_fallback_confidence_threshold:
            fallback_result = dict(base_result)
            fallback_result["warnings"] = warnings
            fallback_result["classification_route"] = f"{route}_kept_base"
            fallback_result["base_model"] = base_result.get("model")
            fallback_result["base_subcategory"] = base_result.get("subcategory")
            fallback_result["zappos_model"] = zappos_result.get("model")
            fallback_result["zappos_subcategory"] = zappos_result.get("subcategory")
            fallback_result["zappos_confidence"] = zappos_result.get("confidence")
            fallback_result["_zappos_result"] = zappos_result
            return fallback_result

        refined_result = dict(zappos_result)
        refined_result["warnings"] = warnings
        refined_result["classification_route"] = route
        refined_result["base_model"] = base_result.get("model")
        refined_result["base_subcategory"] = base_result.get("subcategory")
        refined_result["base_confidence"] = base_result.get("confidence")
        refined_result["_zappos_result"] = zappos_result
        return refined_result

    def _classify_image_zero_shot(self, image_bytes):
        try:
            from PIL import Image
            from transformers import pipeline
        except ImportError:
            return {
                "subcategory": None,
                "confidence": None,
                "top_predictions": [],
                "warnings": [
                    "Не удалось загрузить резервный zero-shot классификатор. Установите transformers и torch."
                ],
                "model": self.model_id,
            }

        try:
            if self._pipeline is None:
                self._pipeline = pipeline(
                    "zero-shot-image-classification",
                    model=self.model_id,
                    device=-1,
                )

            image = self._prepare_classifier_image(image_bytes, Image)
            predictions = self._pipeline(
                image,
                candidate_labels=[candidate["label"] for candidate in SUBCATEGORY_CANDIDATES],
            )
        except Exception:
            return {
                "subcategory": None,
                "confidence": None,
                "top_predictions": [],
                "warnings": [
                    "Резервный zero-shot классификатор недоступен. Выполнено только удаление фона и определение цветов."
                ],
                "model": self.model_id,
            }

        normalized_predictions = predictions if isinstance(predictions, list) else []
        top_predictions = []
        for entry in normalized_predictions[:5]:
            candidate = LABEL_LOOKUP.get(entry.get("label"))
            if not candidate:
                continue
            top_predictions.append(
                {
                    "subcategory": candidate["subcategory"],
                    "category": candidate["category"],
                    "label": candidate["title"],
                    "score": round(float(entry.get("score", 0.0)), 4),
                }
            )

        best_prediction = top_predictions[0] if top_predictions else None
        return {
            "subcategory": best_prediction["subcategory"] if best_prediction else None,
            "confidence": best_prediction["score"] if best_prediction else None,
            "top_predictions": top_predictions,
            "warnings": [],
            "model": self.model_id,
        }

    def _prepare_classifier_image(self, image_bytes, image_module):
        image = image_module.open(BytesIO(image_bytes)).convert("RGBA")
        background = image_module.new("RGBA", image.size, (255, 255, 255, 255))
        composited = image_module.alpha_composite(background, image).convert("RGB")
        return composited

    def _extract_palette_colors(self, image_bytes):
        try:
            import numpy as np
            from PIL import Image
        except ImportError as error:
            raise ApiError(
                "Не удалось определить цвета вещи. Установите зависимости Pillow и numpy.",
                500,
            ) from error

        image = Image.open(BytesIO(image_bytes)).convert("RGBA")
        image.thumbnail((240, 240))
        pixels = np.array(image)
        if pixels.size == 0:
            return []

        alpha_channel = pixels[:, :, 3]
        mask = alpha_channel > 12
        rgb_pixels = pixels[:, :, :3][mask] if mask.any() else pixels[:, :, :3].reshape(-1, 3)
        if len(rgb_pixels) == 0:
            return []

        if len(rgb_pixels) > 6000:
            step = max(len(rgb_pixels) // 6000, 1)
            rgb_pixels = rgb_pixels[::step]

        palette_names = list(COLOR_PALETTE.keys())
        palette_values = np.array(list(COLOR_PALETTE.values()))
        distances = ((rgb_pixels[:, None, :] - palette_values[None, :, :]) ** 2).sum(axis=2)
        nearest_indices = distances.argmin(axis=1)
        counts = np.bincount(nearest_indices, minlength=len(palette_names))
        total = counts.sum() or 1

        ranked_colors = [
            (palette_names[index], count / total)
            for index, count in enumerate(counts)
            if count > 0
        ]
        ranked_colors.sort(key=lambda item: item[1], reverse=True)

        if ranked_colors:
            dominant_color, dominant_share = ranked_colors[0]
            second_share = ranked_colors[1][1] if len(ranked_colors) > 1 else 0.0
            third_share = ranked_colors[2][1] if len(ranked_colors) > 2 else 0.0

            if dominant_share >= 0.48 or second_share < 0.18:
                return [dominant_color]
            if dominant_share + second_share >= 0.78 or third_share < 0.16:
                return [dominant_color, ranked_colors[1][0]]

        selected_colors = [color for color, share in ranked_colors if share >= 0.18][:3]
        if not selected_colors and ranked_colors:
            selected_colors = [ranked_colors[0][0]]
        return selected_colors

    def _build_attribute_suggestions(self, subcategory, colors):
        if not subcategory:
            return {
                "category": None,
                "subcategory": None,
                "title_suggestion": "Новая вещь",
                "styles": [],
                "season": "all-season",
                "formality": "casual",
                "fit": "balanced",
                "layer_level": None,
                "insulation_rating": 0.6,
                "waterproof": False,
                "windproof": False,
            }

        candidate = SUBCATEGORY_LOOKUP.get(subcategory)
        if not candidate:
            candidate = {
                "subcategory": subcategory,
                "category": "accessory",
                "title": subcategory.replace("_", " ").title(),
            }

        category = candidate["category"]
        suggestions = {
            "category": category,
            "subcategory": subcategory,
            "title_suggestion": candidate["title"],
            "styles": STYLE_SUGGESTIONS.get(subcategory) or STYLE_SUGGESTIONS.get(category) or ["casual"],
            "season": SEASON_SUGGESTIONS.get(subcategory, SEASON_SUGGESTIONS["default"]),
            "formality": FORMALITY_SUGGESTIONS.get(subcategory, FORMALITY_SUGGESTIONS["default"]),
            "fit": FIT_SUGGESTIONS.get(subcategory, FIT_SUGGESTIONS["default"]),
            "layer_level": LAYER_LEVEL_SUGGESTIONS.get(
                subcategory,
                LAYER_LEVEL_SUGGESTIONS.get(f"category_{category}"),
            ),
            "insulation_rating": INSULATION_SUGGESTIONS.get(subcategory, INSULATION_SUGGESTIONS["default"]),
            "waterproof": subcategory in WATERPROOF_SUBCATEGORIES,
            "windproof": subcategory in WINDPROOF_SUBCATEGORIES,
            "colors": colors,
        }
        return self._sanitize_attribute_suggestions(category, suggestions)

    def _sanitize_attribute_suggestions(self, category, suggestions):
        normalized_category = (category or "").strip().lower()
        if normalized_category not in FIT_SUPPORTED_CATEGORIES:
            suggestions["fit"] = None
        if normalized_category not in LAYER_LEVEL_SUPPORTED_CATEGORIES:
            suggestions["layer_level"] = None
        if normalized_category not in INSULATION_SUPPORTED_CATEGORIES:
            suggestions["insulation_rating"] = 0.0
        if normalized_category not in WATERPROOF_SUPPORTED_CATEGORIES:
            suggestions["waterproof"] = False
        if normalized_category not in WINDPROOF_SUPPORTED_CATEGORIES:
            suggestions["windproof"] = False
        return suggestions

    def _normalize_top_predictions(self, predictions):
        normalized_predictions = []
        for prediction in predictions or []:
            subcategory = prediction.get("subcategory")
            if not subcategory or subcategory not in SUBCATEGORY_LOOKUP:
                continue
            candidate = SUBCATEGORY_LOOKUP[subcategory]
            normalized_predictions.append(
                {
                    "subcategory": subcategory,
                    "category": candidate["category"],
                    "label": candidate["title"],
                    "score": prediction.get("score"),
                }
            )
        return normalized_predictions
