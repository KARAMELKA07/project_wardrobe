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

    return {
        "name": name,
        "event_type": event_type,
        "weather_context": weather_context,
        "score": score,
        "explanation": explanation,
        "items": cleaned_items,
    }


def validate_feedback_payload(payload):
    reaction = (payload.get("reaction") or "").strip().lower()
    if reaction not in {"like", "dislike", "save"}:
        raise ApiError("Поле reaction должно быть одним из: like, dislike, save.", 400)
    return {"reaction": reaction}
