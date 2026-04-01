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
