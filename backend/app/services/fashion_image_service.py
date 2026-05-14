from __future__ import annotations

import os
from io import BytesIO

from ..utils.errors import ApiError
from ..utils.storage import save_image_bytes
from .deepfashion_classifier import DeepFashionLocalClassifier


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
LABEL_LOOKUP = {
    candidate["label"]: candidate for candidate in SUBCATEGORY_CANDIDATES
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
    "bottom": ["casual"],
    "shoes": ["casual"],
    "outerwear": ["classic"],
    "accessory": ["minimal"],
    "hoodie": ["sport", "casual"],
    "sweatshirt": ["sport", "casual"],
    "sneakers": ["casual", "sport"],
    "summer_sneakers": ["casual", "sport"],
    "blazer": ["classic", "business"],
    "trench": ["classic", "minimal"],
    "coat": ["classic", "minimal"],
    "jewelry": ["evening", "classic"],
    "bag": ["minimal", "classic"],
    "backpack": ["casual", "travel"],
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
    "bag": "smart",
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

LAYER_LEVEL_SUGGESTIONS = {
    "default": None,
    "category_top": "base",
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
    "scarf": "support",
    "hat": "support",
    "cap": "support",
    "gloves": "support",
    "belt": "support",
    "jewelry": "support",
}

INSULATION_SUGGESTIONS = {
    "default": 0.6,
    "crop_top": 0.2,
    "shorts": 0.3,
    "sandals": 0.2,
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


class FashionImageService:
    def __init__(self):
        self.enabled = os.getenv("FASHION_AI_ENABLED", "true").lower() == "true"
        self.model_id = os.getenv(
            "FASHION_AI_MODEL_ID",
            "openai/clip-vit-base-patch32",
        )
        self.deepfashion_threshold = float(os.getenv("DEEPFASHION_CONFIDENCE_THRESHOLD", "0.55"))
        self._pipeline = None
        self._local_classifier = DeepFashionLocalClassifier()

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
        if local_result.get("subcategory") and local_confidence >= self.deepfashion_threshold:
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

        selected_colors = [color for color, share in ranked_colors if share >= 0.12][:3]
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

        candidate = SUBCATEGORY_LOOKUP[subcategory]
        category = candidate["category"]

        return {
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
