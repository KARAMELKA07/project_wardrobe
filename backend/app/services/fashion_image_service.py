from __future__ import annotations

import os
from io import BytesIO

from ..utils.errors import ApiError
from ..utils.storage import save_image_bytes
from .deepfashion_classifier import DeepFashionLocalClassifier, PROJECT_ROOT


SUBCATEGORY_CANDIDATES = [
    {"subcategory": "t_shirt", "category": "top", "label": "t-shirt", "title": "Футболка"},
    {"subcategory": "shirt", "category": "top", "label": "shirt", "title": "Рубашка"},
    {"subcategory": "blouse", "category": "top", "label": "blouse", "title": "Блузка"},
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

SUBCATEGORY_LOOKUP = {
    candidate["subcategory"]: candidate for candidate in SUBCATEGORY_CANDIDATES
}

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

SUBCATEGORY_LOOKUP.update(
    {
        candidate["subcategory"]: candidate
        for candidate in FPID_COMPAT_CANDIDATES
    }
)

LABEL_LOOKUP = {
    candidate["label"]: candidate
    for candidate in [*SUBCATEGORY_CANDIDATES, *FPID_COMPAT_CANDIDATES]
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
    "dress": ["classic", "casual"],
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

DEFAULT_ZAPPOS_CHECKPOINT_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "zappos_classifier.pt"
DEFAULT_ZAPPOS_METADATA_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "zappos_classifier.metadata.json"


class FashionImageService:
    def __init__(self):
        self.enabled = os.getenv("FASHION_AI_ENABLED", "true").lower() == "true"
        self.model_id = os.getenv(
            "FASHION_AI_MODEL_ID",
            "openai/clip-vit-base-patch32",
        )
        self.deepfashion_threshold = float(os.getenv("DEEPFASHION_CONFIDENCE_THRESHOLD", "0.55"))
        self.zappos_enabled = os.getenv("ZAPPOS_CLASSIFIER_ENABLED", "true").lower() == "true"
        self.zappos_top_shoe_score_threshold = float(os.getenv("ZAPPOS_TOP_SHOE_SCORE_THRESHOLD", "0.05"))
        self.zappos_fallback_confidence_threshold = float(os.getenv("ZAPPOS_FALLBACK_CONFIDENCE_THRESHOLD", "0.65"))
        self._pipeline = None
        self._local_classifier = DeepFashionLocalClassifier()
        self._shoe_classifier = DeepFashionLocalClassifier(
            checkpoint_path=os.getenv("ZAPPOS_CHECKPOINT_PATH", str(DEFAULT_ZAPPOS_CHECKPOINT_PATH)),
            metadata_path=os.getenv("ZAPPOS_METADATA_PATH", str(DEFAULT_ZAPPOS_METADATA_PATH)),
            model_slug="zappos-local",
            missing_model="zappos-local",
            default_source_dataset="Zappos",
        )

    def analyze_upload(self, file_storage):
        raw_image = self._read_file_storage(file_storage)
        processed_image = self._remove_background(raw_image)
        colors = self._extract_palette_colors(processed_image)
        classification = self._classify_image(processed_image)
        suggestions = self._build_attribute_suggestions(
            classification.get("subcategory"),
            colors,
        )

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
            "top_predictions": self._normalize_top_predictions(
                classification.get("top_predictions", [])
            ),
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
        except Exception as error:  # pragma: no cover - depends on runtime model
            raise ApiError(
                "Не удалось удалить фон с изображения. Проверьте, что модель rembg доступна.",
                500,
            ) from error

        if not result:
            raise ApiError("Сервис удаления фона вернул пустой результат.", 500)
        return result

    def _classify_image(self, image_bytes):
        if not self.enabled:
            return {
                "subcategory": None,
                "confidence": None,
                "top_predictions": [],
                "warnings": ["Автоматическое распознавание типа вещи отключено в настройках."],
                "model": None,
            }

        local_result = self._local_classifier.predict(image_bytes)
        local_confidence = float(local_result.get("confidence") or 0.0)
        local_model = local_result.get("model") or ""
        local_source = local_result.get("source_dataset") or ""
        is_fpid_model = local_model.startswith("fpid-local") or local_source == "Fashion Product Images"

        if is_fpid_model and local_result.get("subcategory"):
            zappos_route = self._zappos_refinement_route(local_result, image_bytes)
            if zappos_route:
                return self._refine_shoe_prediction(image_bytes, local_result, zappos_route)

            warnings = list(local_result.get("warnings", []))
            if local_confidence < self.deepfashion_threshold:
                warnings.append(
                    "Локальная FPID-модель дала результат с низкой уверенностью. Использован прогноз FPID без zero-shot fallback."
                )
            local_result["classification_route"] = "fpid"
            local_result["warnings"] = warnings
            return local_result

        if local_result.get("subcategory") and local_confidence >= self.deepfashion_threshold:
            local_result["classification_route"] = local_result.get("classification_route") or "local"
            return local_result

        zero_shot_result = self._classify_image_zero_shot(image_bytes)
        warnings = list(local_result.get("warnings", []))

        if local_result.get("subcategory") and not zero_shot_result.get("subcategory"):
            if local_confidence < self.deepfashion_threshold:
                warnings.append(
                    "Локальная DeepFashion-модель дала результат с пониженной уверенностью. Использован лучший доступный прогноз."
                )
            local_result["warnings"] = warnings
            return local_result

        if zero_shot_result.get("subcategory"):
            if local_result.get("subcategory") and local_confidence < self.deepfashion_threshold:
                warnings.append(
                    "Локальная DeepFashion-модель дала низкую уверенность. Выполнен резервный zero-shot анализ."
                )
            zero_shot_result["warnings"] = warnings + zero_shot_result.get("warnings", [])
            return zero_shot_result

        local_result["warnings"] = warnings + zero_shot_result.get("warnings", [])
        return local_result

    def _zappos_refinement_route(self, classification, image_bytes):
        if not self.zappos_enabled:
            return None
        subcategory = classification.get("subcategory")
        if not subcategory:
            return None
        candidate = SUBCATEGORY_LOOKUP.get(subcategory)
        if subcategory in SHOE_SUBCATEGORIES or (candidate and candidate.get("category") == "shoes"):
            return "fpid_to_zappos_shoes"
        if self._top_prediction_shoe_score(classification) >= self.zappos_top_shoe_score_threshold:
            return "fpid_to_zappos_top5_shoes"
        if subcategory in ZAPPOS_SUSPECT_SUBCATEGORIES and self._looks_like_horizontal_shoe_object(image_bytes):
            return "fpid_to_zappos_shape_fallback"
        return None

    def _top_prediction_shoe_score(self, classification):
        return sum(
            float(prediction.get("score") or 0.0)
            for prediction in classification.get("top_predictions", [])
            if prediction.get("subcategory") in SHOE_SUBCATEGORIES
        )

    def _looks_like_horizontal_shoe_object(self, image_bytes):
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            return False

        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGBA")
            image.thumbnail((256, 256))
            pixels = np.array(image)
        except Exception:
            return False

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
            return False

        width = xs.max() - xs.min() + 1
        height = ys.max() - ys.min() + 1
        object_area = float(mask.mean())
        aspect_ratio = width / max(height, 1)
        return aspect_ratio >= 1.15 and 0.03 <= object_area <= 0.65

    def _refine_shoe_prediction(self, image_bytes, base_result, route):
        zappos_result = self._shoe_classifier.predict(image_bytes)
        warnings = list(base_result.get("warnings", [])) + list(zappos_result.get("warnings", []))

        if not zappos_result.get("subcategory"):
            fallback_result = dict(base_result)
            fallback_result["warnings"] = warnings
            fallback_result["classification_route"] = "fpid_zappos_unavailable"
            fallback_result["base_model"] = base_result.get("model")
            fallback_result["base_subcategory"] = base_result.get("subcategory")
            return fallback_result

        zappos_confidence = float(zappos_result.get("confidence") or 0.0)
        if route != "fpid_to_zappos_shoes" and zappos_confidence < self.zappos_fallback_confidence_threshold:
            fallback_result = dict(base_result)
            fallback_result["warnings"] = warnings
            fallback_result["classification_route"] = f"{route}_kept_fpid"
            fallback_result["base_model"] = base_result.get("model")
            fallback_result["base_subcategory"] = base_result.get("subcategory")
            fallback_result["zappos_model"] = zappos_result.get("model")
            fallback_result["zappos_subcategory"] = zappos_result.get("subcategory")
            fallback_result["zappos_confidence"] = zappos_result.get("confidence")
            return fallback_result

        refined_result = dict(zappos_result)
        refined_result["warnings"] = warnings
        refined_result["classification_route"] = route
        refined_result["base_model"] = base_result.get("model")
        refined_result["base_subcategory"] = base_result.get("subcategory")
        refined_result["base_confidence"] = base_result.get("confidence")
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
                    "Не удалось загрузить резервный zero-shot классификатор. Установите transformers и torch.",
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
                    "Резервный zero-shot классификатор недоступен. Выполнено только удаление фона и определение цветов.",
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
        if mask.any():
            rgb_pixels = pixels[:, :, :3][mask]
        else:
            rgb_pixels = pixels[:, :, :3].reshape(-1, 3)

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
            "styles": STYLE_SUGGESTIONS.get(subcategory)
            or STYLE_SUGGESTIONS.get(category)
            or ["casual"],
            "season": SEASON_SUGGESTIONS.get(subcategory, SEASON_SUGGESTIONS["default"]),
            "formality": FORMALITY_SUGGESTIONS.get(subcategory, FORMALITY_SUGGESTIONS["default"]),
            "fit": FIT_SUGGESTIONS.get(subcategory, FIT_SUGGESTIONS["default"]),
            "layer_level": LAYER_LEVEL_SUGGESTIONS.get(
                subcategory,
                LAYER_LEVEL_SUGGESTIONS.get(f"category_{category}"),
            ),
            "insulation_rating": INSULATION_SUGGESTIONS.get(
                subcategory,
                INSULATION_SUGGESTIONS["default"],
            ),
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
