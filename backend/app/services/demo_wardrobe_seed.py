from ..extensions import db
from ..models import ClothingItem, UserPreferences


PEXELS_PHOTO_IDS = {
    "white_tshirt": "18186106",
    "black_tshirt": "8486692",
    "beige_tshirt": "6786618",
    "blue_shirt": "19189134",
    "white_polo": "8730572",
    "green_shirt": "8727445",
    "white_blouse": "8058727",
    "pink_blouse": "20107165",
    "brown_sweater": "11505332",
    "gray_sweater": "3754685",
    "blue_hoodie": "19602188",
    "beige_turtleneck": "8062965",
    "black_turtleneck": "6580564",
    "beige_cardigan": "8797760",
    "black_jeans": "2448535",
    "blue_jeans": "1082529",
    "beige_trousers": "11927534",
    "black_midi_skirt": "7391123",
    "white_shorts": "8746743",
    "gray_joggers": "10378467",
    "black_leggings": "4534648",
    "beige_skirt": "6445991",
    "black_skirt_alt": "18490258",
    "white_sneakers": "4252969",
    "black_boots": "2929281",
    "beige_loafers": "27141835",
    "winter_boots": "6608415",
    "brown_boots": "9929610",
    "white_sandals": "26954370",
    "black_flip_flops": "14934603",
    "black_pumps": "8134242",
    "black_ankle_boots": "27204301",
    "black_heeled_sandals": "7383130",
    "black_coat": "18794485",
    "beige_jacket": "14694444",
    "gray_blazer": "7653837",
    "beige_trench": "21838449",
    "windbreaker": "6778713",
    "puffer_jacket": "19426409",
    "black_blazer": "12809816",
    "olive_jacket": "13260209",
    "leather_jacket": "4750189",
    "black_bag": "6167276",
    "beige_scarf": "8121914",
    "brown_belt": "20777832",
    "white_cap": "13359665",
    "silver_jewelry": "23859401",
    "brown_backpack": "11578809",
    "beige_gloves": "9413652",
    "gold_jewelry": "8626814",
}
FIT_BY_SUBCATEGORY = {
    "t_shirt": "balanced",
    "shirt": "fitted",
    "blouse": "fitted",
    "polo": "balanced",
    "longsleeve": "balanced",
    "sweater": "loose",
    "hoodie": "oversized",
    "cardigan": "loose",
    "turtleneck": "fitted",
    "sweatshirt": "loose",
    "vest": "balanced",
    "crop_top": "fitted",
    "jeans": "balanced",
    "trousers": "fitted",
    "chinos": "balanced",
    "joggers": "loose",
    "leggings": "fitted",
    "culottes": "loose",
    "skirt": "balanced",
    "mini_skirt": "fitted",
    "midi_skirt": "balanced",
    "maxi_skirt": "loose",
    "shorts": "balanced",
    "winter_boots": "balanced",
    "felt_boots": "balanced",
    "warm_boots": "balanced",
    "demi_boots": "balanced",
    "ankle_boots": "fitted",
    "boots": "balanced",
    "closed_shoes": "fitted",
    "pumps": "fitted",
    "loafers": "fitted",
    "sneakers": "balanced",
    "summer_sneakers": "balanced",
    "sandals": "fitted",
    "espadrilles": "balanced",
    "flip_flops": "loose",
    "coat": "balanced",
    "jacket": "balanced",
    "parka": "oversized",
    "down_jacket": "oversized",
    "trench": "balanced",
    "blazer": "fitted",
    "leather_jacket": "balanced",
    "windbreaker": "loose",
    "vest_outerwear": "balanced",
    "bag": "balanced",
    "backpack": "balanced",
    "scarf": "loose",
    "hat": "balanced",
    "cap": "balanced",
    "gloves": "fitted",
    "belt": "fitted",
    "jewelry": "fitted",
}
LAYER_BY_SUBCATEGORY = {
    "t_shirt": "base",
    "shirt": "base",
    "blouse": "base",
    "polo": "base",
    "longsleeve": "base",
    "crop_top": "base",
    "turtleneck": "base",
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
INSULATION_BY_SUBCATEGORY = {
    "t_shirt": 0.6,
    "shirt": 0.8,
    "blouse": 0.7,
    "polo": 0.7,
    "longsleeve": 1.0,
    "crop_top": 0.3,
    "sweater": 1.8,
    "hoodie": 1.7,
    "cardigan": 1.4,
    "turtleneck": 1.5,
    "sweatshirt": 1.5,
    "vest": 1.1,
    "jeans": 1.4,
    "trousers": 1.2,
    "chinos": 1.1,
    "joggers": 1.4,
    "leggings": 1.0,
    "culottes": 0.9,
    "skirt": 0.8,
    "mini_skirt": 0.5,
    "midi_skirt": 0.8,
    "maxi_skirt": 0.9,
    "shorts": 0.3,
    "winter_boots": 2.0,
    "felt_boots": 2.2,
    "warm_boots": 1.9,
    "demi_boots": 1.5,
    "ankle_boots": 1.4,
    "boots": 1.3,
    "closed_shoes": 1.0,
    "pumps": 0.8,
    "loafers": 0.8,
    "sneakers": 0.9,
    "summer_sneakers": 0.6,
    "sandals": 0.2,
    "espadrilles": 0.3,
    "flip_flops": 0.1,
    "coat": 2.4,
    "jacket": 1.7,
    "parka": 2.6,
    "down_jacket": 2.8,
    "trench": 1.5,
    "blazer": 1.2,
    "leather_jacket": 1.6,
    "windbreaker": 1.2,
    "vest_outerwear": 1.2,
    "scarf": 0.5,
    "hat": 0.4,
    "gloves": 0.4,
}
WATERPROOF_SUBCATEGORIES = {"trench", "parka", "down_jacket", "windbreaker", "jacket"}
WINDPROOF_SUBCATEGORIES = {"coat", "parka", "down_jacket", "windbreaker", "leather_jacket"}
WATER_RESISTANT_MATERIALS = {"leather", "nylon", "polyester", "rubber"}


def build_demo_preferences():
    return {
        "preferred_styles": ["minimal", "classic", "casual", "business"],
        "preferred_colors": ["white", "black", "beige", "gray", "cream", "navy", "olive"],
        "constraints": [],
        "disliked_items": [],
    }


def build_demo_wardrobe_items():
    return [
        _item("Белая футболка", "top", "t_shirt", ["white"], ["basic", "minimal"], "all-season", "casual", "cotton", "white_tshirt"),
        _item("Черная футболка", "top", "t_shirt", ["black"], ["casual", "basic"], "all-season", "casual", "cotton", "black_tshirt"),
        _item("Бежевая футболка", "top", "t_shirt", ["beige"], ["minimal", "basic"], "all-season", "casual", "cotton", "beige_tshirt"),
        _item("Голубая рубашка", "top", "shirt", ["blue"], ["classic", "business"], "spring", "smart", "cotton", "blue_shirt"),
        _item("Белое поло", "top", "polo", ["white"], ["classic", "casual"], "all-season", "smart", "cotton", "white_polo"),
        _item("Зеленая рубашка", "top", "shirt", ["green"], ["casual", "minimal"], "spring", "casual", "cotton", "green_shirt"),
        _item("Белая блузка", "top", "blouse", ["white"], ["romantic", "evening"], "summer", "smart", "viscose", "white_blouse"),
        _item("Розовая блузка", "top", "blouse", ["pink"], ["romantic", "fashion"], "summer", "smart", "viscose", "pink_blouse"),
        _item("Коричневый свитер", "top", "sweater", ["brown"], ["minimal", "casual"], "autumn", "smart", "knit", "brown_sweater"),
        _item("Серый свитер", "top", "sweater", ["gray"], ["minimal", "classic"], "winter", "smart", "knit", "gray_sweater"),
        _item("Синее худи", "top", "hoodie", ["blue"], ["street", "sport"], "autumn", "casual", "cotton", "blue_hoodie"),
        _item("Бежевый гольф", "top", "turtleneck", ["beige"], ["minimal", "classic"], "autumn", "smart", "knit", "beige_turtleneck"),
        _item("Черная водолазка", "top", "turtleneck", ["black"], ["minimal", "classic"], "autumn", "smart", "knit", "black_turtleneck"),
        _item("Бежевый кардиган", "top", "cardigan", ["beige"], ["classic", "minimal"], "autumn", "casual", "knit", "beige_cardigan"),

        _item("Черные джинсы", "bottom", "jeans", ["black"], ["street", "casual"], "all-season", "casual", "denim", "black_jeans"),
        _item("Синие джинсы", "bottom", "jeans", ["blue"], ["basic", "casual"], "all-season", "casual", "denim", "blue_jeans"),
        _item("Бежевые брюки", "bottom", "trousers", ["beige"], ["minimal", "classic"], "spring", "smart", "cotton", "beige_trousers"),
        _item("Черная юбка-миди", "bottom", "midi_skirt", ["black"], ["classic", "fashion"], "autumn", "smart", "cotton", "black_midi_skirt"),
        _item("Белые шорты", "bottom", "shorts", ["white"], ["minimal", "casual"], "summer", "casual", "viscose", "white_shorts"),
        _item("Серые джоггеры", "bottom", "joggers", ["gray"], ["sport", "street"], "all-season", "casual", "cotton", "gray_joggers"),
        _item("Черные леггинсы", "bottom", "leggings", ["black"], ["sport", "minimal"], "all-season", "casual", "jersey", "black_leggings"),
        _item("Бежевая юбка-миди", "bottom", "midi_skirt", ["beige"], ["romantic", "minimal"], "summer", "smart", "linen", "beige_skirt"),
        _item("Черная юбка-карандаш", "bottom", "skirt", ["black"], ["classic", "evening"], "all-season", "formal", "cotton", "black_skirt_alt"),

        _item("Белые кроссовки", "shoes", "sneakers", ["white"], ["casual", "sport"], "spring", "casual", "textile", "white_sneakers"),
        _item("Черные ботинки", "shoes", "boots", ["black"], ["classic", "casual"], "autumn", "smart", "leather", "black_boots"),
        _item("Бежевые лоферы", "shoes", "loafers", ["beige"], ["classic", "minimal"], "spring", "smart", "leather", "beige_loafers"),
        _item("Черные зимние сапоги", "shoes", "winter_boots", ["black"], ["casual"], "winter", "casual", "leather", "winter_boots"),
        _item("Коричневые демисезонные ботинки", "shoes", "demi_boots", ["brown"], ["classic", "casual"], "autumn", "smart", "leather", "brown_boots"),
        _item("Белые босоножки", "shoes", "sandals", ["white"], ["minimal", "romantic"], "summer", "smart", "leather", "white_sandals"),
        _item("Черные шлепки", "shoes", "flip_flops", ["black"], ["casual", "minimal"], "summer", "casual", "rubber", "black_flip_flops"),
        _item("Черные лодочки", "shoes", "pumps", ["black"], ["classic", "evening"], "all-season", "formal", "leather", "black_pumps"),
        _item("Черные ботильоны", "shoes", "ankle_boots", ["black"], ["classic", "evening"], "autumn", "smart", "leather", "black_ankle_boots"),
        _item("Черные босоножки на каблуке", "shoes", "sandals", ["black"], ["evening", "fashion"], "summer", "formal", "leather", "black_heeled_sandals"),

        _item("Черное пальто", "outerwear", "coat", ["black"], ["classic", "minimal"], "autumn", "formal", "wool", "black_coat"),
        _item("Бежевая куртка", "outerwear", "jacket", ["beige"], ["casual", "minimal"], "autumn", "casual", "cotton", "beige_jacket"),
        _item("Серый пиджак", "outerwear", "blazer", ["gray"], ["business", "classic"], "all-season", "smart", "wool", "gray_blazer"),
        _item("Светлый тренч", "outerwear", "trench", ["beige"], ["classic", "minimal"], "spring", "smart", "cotton", "beige_trench"),
        _item("Темная ветровка", "outerwear", "windbreaker", ["gray"], ["sport", "casual"], "autumn", "casual", "nylon", "windbreaker"),
        _item("Черный пуховик", "outerwear", "down_jacket", ["black"], ["casual"], "winter", "casual", "nylon", "puffer_jacket"),
        _item("Черный жакет", "outerwear", "blazer", ["black"], ["business", "classic"], "all-season", "formal", "wool", "black_blazer"),
        _item("Оливковая куртка", "outerwear", "jacket", ["olive"], ["casual", "street"], "autumn", "casual", "cotton", "olive_jacket"),
        _item("Черная кожаная куртка", "outerwear", "leather_jacket", ["black"], ["street", "evening"], "autumn", "smart", "leather", "leather_jacket"),

        _item("Черная сумка", "accessory", "bag", ["black"], ["minimal", "classic"], "all-season", "smart", "leather", "black_bag"),
        _item("Бежевый шарф", "accessory", "scarf", ["beige"], ["classic", "minimal"], "autumn", "casual", "cotton", "beige_scarf"),
        _item("Коричневый ремень", "accessory", "belt", ["brown"], ["classic", "business"], "all-season", "smart", "leather", "brown_belt"),
        _item("Белая кепка", "accessory", "cap", ["white"], ["sport", "casual"], "summer", "casual", "cotton", "white_cap"),
        _item("Серебристое украшение", "accessory", "jewelry", ["silver"], ["evening", "minimal"], "all-season", "formal", "metal", "silver_jewelry"),
        _item("Коричневый рюкзак", "accessory", "backpack", ["brown"], ["casual", "travel"], "all-season", "casual", "leather", "brown_backpack"),
        _item("Бежевые перчатки", "accessory", "gloves", ["beige"], ["classic", "minimal"], "winter", "casual", "knit", "beige_gloves"),
        _item("Золотое украшение", "accessory", "jewelry", ["gold"], ["evening", "classic"], "all-season", "formal", "metal", "gold_jewelry"),
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


def _item(title, category, subcategory, colors, styles, season, formality, material, image_key):
    return {
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "colors": colors,
        "styles": styles,
        "season": season,
        "formality": formality,
        "fit": FIT_BY_SUBCATEGORY.get(subcategory, "balanced"),
        "layer_level": LAYER_BY_SUBCATEGORY.get(subcategory),
        "insulation_rating": INSULATION_BY_SUBCATEGORY.get(subcategory, 0.6),
        "waterproof": subcategory in WATERPROOF_SUBCATEGORIES or material in WATER_RESISTANT_MATERIALS,
        "windproof": subcategory in WINDPROOF_SUBCATEGORIES,
        "material": material,
        "image_url": _pexels_image(image_key),
    }


def _pexels_image(image_key):
    photo_id = PEXELS_PHOTO_IDS[image_key]
    return f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=1200"
