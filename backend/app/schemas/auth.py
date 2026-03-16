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
