from ..extensions import db
from ..models import ClothingItem, UserPreferences


PLACEHOLDER_IMAGE_URLS = {
    "top": "/uploads/placeholders/top.svg",
    "bottom": "/uploads/placeholders/bottom.svg",
    "shoes": "/uploads/placeholders/shoes.svg",
    "outerwear": "/uploads/placeholders/outerwear.svg",
    "accessory": "/uploads/placeholders/accessory.svg",
}


def build_demo_preferences():
    return {
        "preferred_styles": ["minimal", "classic", "casual"],
        "preferred_colors": ["white", "black", "beige", "gray"],
        "constraints": [],
        "disliked_items": [],
    }


def build_demo_wardrobe_items():
    return [
        _item("Белая футболка", "top", "t-shirt", ["white"], ["casual", "minimal"], "summer", "casual", "cotton"),
        _item("Черная футболка", "top", "t-shirt", ["black"], ["casual", "basic"], "summer", "casual", "cotton"),
        _item("Бежевая рубашка", "top", "shirt", ["beige"], ["minimal", "classic"], "spring", "smart", "linen"),
        _item("Голубая рубашка", "top", "shirt", ["blue"], ["classic", "business"], "spring", "smart", "cotton"),
        _item("Серый лонгслив", "top", "longsleeve", ["gray"], ["casual", "minimal"], "autumn", "casual", "cotton"),
        _item("Черные джинсы", "bottom", "jeans", ["black"], ["casual", "street"], "all-season", "casual", "denim"),
        _item("Синие джинсы", "bottom", "jeans", ["blue"], ["casual", "basic"], "all-season", "casual", "denim"),
        _item("Бежевые брюки", "bottom", "trousers", ["beige"], ["minimal", "business"], "spring", "smart", "cotton"),
        _item("Черная юбка", "bottom", "skirt", ["black"], ["classic", "minimal"], "all-season", "smart", "viscose"),
        _item("Белые кеды", "shoes", "sneakers", ["white"], ["casual", "sport"], "spring", "casual", "leather"),
        _item("Черные ботинки", "shoes", "boots", ["black"], ["classic", "casual"], "autumn", "smart", "leather"),
        _item("Бежевые лоферы", "shoes", "loafers", ["beige"], ["classic", "minimal"], "spring", "smart", "leather"),
        _item("Черное пальто", "outerwear", "coat", ["black"], ["classic", "minimal"], "winter", "formal", "wool"),
        _item("Бежевая куртка", "outerwear", "jacket", ["beige"], ["casual", "minimal"], "autumn", "casual", "cotton"),
        _item("Серый пиджак", "outerwear", "blazer", ["gray"], ["business", "classic"], "spring", "smart", "wool"),
        _item("Черная сумка", "accessory", "bag", ["black"], ["minimal", "classic"], "all-season", "smart", "leather"),
        _item("Светлый шарф", "accessory", "scarf", ["beige", "white"], ["classic", "minimal"], "winter", "casual", "cotton"),
    ]


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


def _item(title, category, subcategory, colors, styles, season, formality, material):
    return {
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "colors": colors,
        "styles": styles,
        "season": season,
        "formality": formality,
        "material": material,
        "image_url": PLACEHOLDER_IMAGE_URLS[category],
    }
