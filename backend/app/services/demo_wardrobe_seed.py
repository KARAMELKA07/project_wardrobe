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
        "preferred_styles": ["minimal", "classic", "casual", "business"],
        "preferred_colors": ["white", "black", "beige", "gray", "cream", "navy", "olive"],
        "constraints": [],
        "disliked_items": [],
    }


def build_demo_wardrobe_items():
    return [
        _item("Белая футболка", "top", "t_shirt", ["white"], ["casual", "basic"], "summer", "casual", "cotton"),
        _item("Черная футболка", "top", "t_shirt", ["black"], ["casual", "basic"], "summer", "casual", "cotton"),
        _item("Бежевая футболка", "top", "t_shirt", ["beige"], ["minimal", "basic"], "summer", "casual", "cotton"),
        _item("Голубая рубашка", "top", "shirt", ["blue"], ["classic", "business"], "spring", "smart", "cotton"),
        _item("Белая рубашка", "top", "shirt", ["white"], ["classic", "business"], "all-season", "smart", "cotton"),
        _item("Бежевая рубашка", "top", "shirt", ["beige"], ["minimal", "classic"], "spring", "smart", "linen"),
        _item("Розовая блузка", "top", "blouse", ["pink"], ["romantic", "classic"], "summer", "smart", "viscose"),
        _item("Серый лонгслив", "top", "longsleeve", ["gray"], ["casual", "minimal"], "autumn", "casual", "cotton"),
        _item("Кремовая водолазка", "top", "turtleneck", ["cream"], ["minimal", "classic"], "winter", "smart", "knit"),
        _item("Оливковое худи", "top", "hoodie", ["olive"], ["casual", "street"], "autumn", "casual", "cotton"),
        _item("Темно-синий свитер", "top", "sweater", ["navy"], ["classic", "minimal"], "winter", "smart", "wool"),
        _item("Молочный кардиган", "top", "cardigan", ["cream"], ["romantic", "minimal"], "autumn", "smart", "knit"),
        _item("Бордовое поло", "top", "polo", ["burgundy"], ["casual", "smart"], "summer", "smart", "cotton"),
        _item("Графитовый свитшот", "top", "sweatshirt", ["gray"], ["sport", "street"], "autumn", "casual", "cotton"),

        _item("Черные джинсы", "bottom", "jeans", ["black"], ["casual", "street"], "all-season", "casual", "denim"),
        _item("Синие джинсы", "bottom", "jeans", ["blue"], ["casual", "basic"], "all-season", "casual", "denim"),
        _item("Бежевые брюки", "bottom", "trousers", ["beige"], ["minimal", "business"], "spring", "smart", "cotton"),
        _item("Серые брюки", "bottom", "trousers", ["gray"], ["classic", "business"], "autumn", "smart", "wool"),
        _item("Белые льняные брюки", "bottom", "trousers", ["white"], ["minimal", "classic"], "summer", "smart", "linen"),
        _item("Оливковые чиносы", "bottom", "chinos", ["olive"], ["casual", "smart"], "spring", "casual", "cotton"),
        _item("Черная юбка-миди", "bottom", "midi_skirt", ["black"], ["classic", "minimal"], "all-season", "smart", "viscose"),
        _item("Бежевая юбка-миди", "bottom", "midi_skirt", ["beige"], ["romantic", "classic"], "spring", "smart", "cotton"),
        _item("Джинсовая юбка", "bottom", "skirt", ["blue"], ["casual", "street"], "summer", "casual", "denim"),
        _item("Черные джоггеры", "bottom", "joggers", ["black"], ["sport", "casual"], "autumn", "casual", "cotton"),
        _item("Серые леггинсы", "bottom", "leggings", ["gray"], ["sport", "minimal"], "all-season", "casual", "jersey"),
        _item("Белые шорты", "bottom", "shorts", ["white"], ["casual", "minimal"], "summer", "casual", "linen"),

        _item("Белые кроссовки", "shoes", "sneakers", ["white"], ["casual", "sport"], "spring", "casual", "leather"),
        _item("Черные ботинки", "shoes", "boots", ["black"], ["classic", "casual"], "autumn", "smart", "leather"),
        _item("Бежевые лоферы", "shoes", "loafers", ["beige"], ["classic", "minimal"], "spring", "smart", "leather"),
        _item("Черные зимние сапоги", "shoes", "winter_boots", ["black"], ["classic"], "winter", "casual", "leather"),
        _item("Коричневые демисезонные ботинки", "shoes", "demi_boots", ["brown"], ["casual", "classic"], "autumn", "casual", "leather"),
        _item("Серые ботильоны", "shoes", "ankle_boots", ["gray"], ["classic", "smart"], "autumn", "smart", "leather"),
        _item("Черные закрытые туфли", "shoes", "closed_shoes", ["black"], ["business", "classic"], "spring", "smart", "leather"),
        _item("Бежевые туфли", "shoes", "pumps", ["beige"], ["classic", "romantic"], "summer", "formal", "leather"),
        _item("Серебристые летние кроссовки", "shoes", "summer_sneakers", ["silver"], ["sport", "casual"], "summer", "casual", "textile"),
        _item("Белые босоножки", "shoes", "sandals", ["white"], ["romantic", "minimal"], "summer", "smart", "leather"),
        _item("Черные шлепки", "shoes", "flip_flops", ["black"], ["casual", "minimal"], "summer", "casual", "rubber"),
        _item("Голубые эспадрильи", "shoes", "espadrilles", ["blue"], ["casual", "romantic"], "summer", "casual", "canvas"),

        _item("Черное пальто", "outerwear", "coat", ["black"], ["classic", "minimal"], "winter", "formal", "wool"),
        _item("Бежевая куртка", "outerwear", "jacket", ["beige"], ["casual", "minimal"], "autumn", "casual", "cotton"),
        _item("Серый пиджак", "outerwear", "blazer", ["gray"], ["business", "classic"], "spring", "smart", "wool"),
        _item("Светлый тренч", "outerwear", "trench", ["cream"], ["classic", "minimal"], "spring", "smart", "cotton"),
        _item("Оливковая парка", "outerwear", "parka", ["olive"], ["casual", "street"], "winter", "casual", "nylon"),
        _item("Молочная ветровка", "outerwear", "windbreaker", ["cream"], ["sport", "casual"], "summer", "casual", "nylon"),
        _item("Темно-синий пуховик", "outerwear", "down_jacket", ["navy"], ["casual"], "winter", "casual", "nylon"),

        _item("Черная сумка", "accessory", "bag", ["black"], ["minimal", "classic"], "all-season", "smart", "leather"),
        _item("Светлый шарф", "accessory", "scarf", ["cream"], ["classic", "minimal"], "winter", "casual", "cotton"),
        _item("Коричневый ремень", "accessory", "belt", ["brown"], ["classic", "business"], "all-season", "smart", "leather"),
        _item("Белая кепка", "accessory", "cap", ["white"], ["sport", "casual"], "summer", "casual", "cotton"),
        _item("Серебристое украшение", "accessory", "jewelry", ["silver"], ["evening", "minimal"], "all-season", "formal", "metal"),
    ]


def get_demo_wardrobe_item_count():
    return len(build_demo_wardrobe_items())


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
