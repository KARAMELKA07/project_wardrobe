import json

from ..utils.errors import ApiError


ALLOWED_CATEGORIES = {"top", "bottom", "shoes", "outerwear", "accessory"}


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


def validate_clothing_item_payload(payload):
    title = (payload.get("title") or "").strip()
    category = (payload.get("category") or "").strip().lower()
    subcategory = (payload.get("subcategory") or "").strip() or None
    season = (payload.get("season") or "all-season").strip().lower()
    formality = (payload.get("formality") or "casual").strip().lower()
    material = (payload.get("material") or "").strip() or None
    image_url = (payload.get("image_url") or "").strip() or None

    if not title:
        raise ApiError("Название вещи обязательно.", 400)
    if category not in ALLOWED_CATEGORIES:
        raise ApiError(
            "Категория должна быть одной из: top, bottom, shoes, outerwear, accessory.",
            400,
        )

    return {
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "colors": parse_list_field(payload.get("colors")),
        "styles": parse_list_field(payload.get("styles")),
        "season": season or "all-season",
        "formality": formality or "casual",
        "material": material,
        "image_url": image_url,
    }
