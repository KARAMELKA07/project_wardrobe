from collections import Counter
from itertools import combinations, product


FEATURE_WEIGHTS = {
    "color_harmony": 0.15,
    "style_match": 0.15,
    "event_match": 0.15,
    "season_match": 0.1,
    "temperature_match": 0.1,
    "weather_condition_match": 0.1,
    "layering_correctness": 0.08,
    "completeness": 0.06,
    "user_preference_match": 0.06,
    "constraints_match": 0.05,
}

ROLE_ORDER = {
    "top": 0,
    "bottom": 1,
    "shoes": 2,
    "outerwear": 3,
    "accessory": 4,
}

BRIGHT_COLORS = {"red", "yellow", "orange", "lime", "fuchsia", "pink"}
COLOR_ALIASES = {
    "black": "black",
    "white": "white",
    "off_white": "white",
    "gray": "gray",
    "grey": "gray",
    "charcoal": "gray",
    "graphite": "gray",
    "beige": "beige",
    "cream": "cream",
    "ivory": "cream",
    "sand": "beige",
    "nude": "beige",
    "taupe": "taupe",
    "brown": "brown",
    "camel": "camel",
    "tan": "camel",
    "chocolate": "brown",
    "mocha": "brown",
    "red": "red",
    "burgundy": "burgundy",
    "wine": "burgundy",
    "maroon": "burgundy",
    "orange": "orange",
    "coral": "coral",
    "peach": "coral",
    "terracotta": "terracotta",
    "yellow": "yellow",
    "mustard": "mustard",
    "green": "green",
    "olive": "olive",
    "khaki": "khaki",
    "mint": "mint",
    "emerald": "green",
    "forest": "green",
    "teal": "teal",
    "turquoise": "turquoise",
    "aqua": "turquoise",
    "blue": "blue",
    "sky": "blue",
    "sky_blue": "blue",
    "cobalt": "blue",
    "navy": "navy",
    "navy_blue": "navy",
    "denim": "denim",
    "indigo": "denim",
    "purple": "purple",
    "lilac": "purple",
    "lavender": "lavender",
    "violet": "purple",
    "plum": "purple",
    "pink": "pink",
    "blush": "pink",
    "rose": "pink",
    "fuchsia": "pink",
    "gold": "gold",
    "silver": "silver",
    "bronze": "bronze",
}
COLOR_FAMILY_MAP = {
    "black": "black",
    "white": "white",
    "gray": "gray",
    "beige": "beige",
    "cream": "beige",
    "taupe": "brown",
    "brown": "brown",
    "camel": "brown",
    "red": "red",
    "burgundy": "red",
    "orange": "orange",
    "coral": "orange",
    "terracotta": "orange",
    "yellow": "yellow",
    "mustard": "yellow",
    "green": "green",
    "olive": "green",
    "khaki": "green",
    "mint": "green",
    "teal": "teal",
    "turquoise": "teal",
    "blue": "blue",
    "navy": "blue",
    "denim": "blue",
    "purple": "purple",
    "lavender": "purple",
    "pink": "pink",
    "gold": "metallic",
    "silver": "metallic",
    "bronze": "metallic",
    "unknown": "unknown",
}
NEUTRAL_COLOR_TOKENS = {
    "black",
    "white",
    "gray",
    "navy",
    "beige",
    "brown",
    "cream",
    "taupe",
    "khaki",
    "denim",
}
METALLIC_COLOR_TOKENS = {"gold", "silver", "bronze"}
ANALOGOUS_FAMILY_PAIRS = {
    frozenset({"red", "orange"}),
    frozenset({"orange", "yellow"}),
    frozenset({"yellow", "green"}),
    frozenset({"green", "teal"}),
    frozenset({"teal", "blue"}),
    frozenset({"blue", "purple"}),
    frozenset({"purple", "pink"}),
    frozenset({"pink", "red"}),
}
COMPLEMENTARY_FAMILY_PAIRS = {
    frozenset({"blue", "orange"}),
    frozenset({"red", "green"}),
    frozenset({"yellow", "purple"}),
    frozenset({"teal", "orange"}),
}
ROLE_COLOR_WEIGHTS = {
    "outerwear": 3.1,
    "top": 3.0,
    "bottom": 2.6,
    "shoes": 1.2,
    "accessory": 0.8,
    "item": 2.0,
}
COLOR_SHARE_WEIGHTS = (0.7, 0.2, 0.1)
MAX_PRIMARY_POOL = 12
MAX_OUTERWEAR_POOL = 6
MAX_ACCESSORY_POOL = 3
EVENT_LABELS = {
    "office": "офис",
    "casual": "повседневный выход",
    "evening": "вечерний выход",
    "sport": "спорт",
    "party": "вечеринка",
    "travel": "поездка",
    "date": "свидание",
}
WINTER_SHOE_TYPES = {"winter_boots", "felt_boots", "warm_boots", "snow_boots"}
COLD_SHOE_TYPES = WINTER_SHOE_TYPES | {
    "demi_boots",
    "ankle_boots",
    "boots",
    "closed_shoes",
}
MID_SHOE_TYPES = {
    "demi_boots",
    "ankle_boots",
    "boots",
    "closed_shoes",
    "sneakers",
    "loafers",
    "pumps",
    "summer_sneakers",
}
HOT_SHOE_TYPES = {
    "sandals",
    "flip_flops",
    "slippers",
    "summer_sneakers",
    "espadrilles",
    "loafers",
    "sneakers",
}
OPEN_SHOE_TYPES = {"sandals", "flip_flops", "slippers", "espadrilles"}
RAIN_SAFE_SHOE_TYPES = COLD_SHOE_TYPES | {"sneakers", "summer_sneakers"}
SNOW_SAFE_SHOE_TYPES = WINTER_SHOE_TYPES | {"demi_boots", "ankle_boots", "boots"}
WARM_TOP_TYPES = {"sweater", "hoodie", "cardigan", "turtleneck", "sweatshirt"}
LIGHT_TOP_TYPES = {"t_shirt", "shirt", "blouse", "crop_top", "polo"}
WARM_BOTTOM_TYPES = {"jeans", "trousers", "joggers", "leggings", "culottes"}
LIGHT_BOTTOM_TYPES = {"shorts", "mini_skirt"}
HEAVY_OUTERWEAR_TYPES = {"coat", "parka", "down_jacket"}
LIGHT_OUTERWEAR_TYPES = {
    "jacket",
    "trench",
    "blazer",
    "leather_jacket",
    "windbreaker",
    "vest_outerwear",
}

EVENT_RULES = {
    "casual": {
        "styles": {"casual", "basic", "minimal", "street"},
        "formalities": {"casual", "smart"},
    },
    "office": {
        "styles": {"classic", "business", "minimal"},
        "formalities": {"smart", "formal"},
    },
    "evening": {
        "styles": {"evening", "classic", "fashion", "party"},
        "formalities": {"smart", "formal"},
    },
    "sport": {
        "styles": {"sport", "athleisure", "casual"},
        "formalities": {"casual"},
    },
    "party": {
        "styles": {"party", "fashion", "statement"},
        "formalities": {"smart", "formal"},
    },
    "travel": {
        "styles": {"casual", "sport", "street"},
        "formalities": {"casual", "smart"},
    },
    "date": {
        "styles": {"minimal", "classic", "romantic"},
        "formalities": {"smart", "formal"},
    },
}

STYLE_FAMILY_MAP = {
    "basic": "minimal",
    "minimal": "minimal",
    "classic": "classic",
    "business": "classic",
    "formal": "classic",
    "casual": "casual",
    "street": "casual",
    "sport": "sport",
    "athleisure": "sport",
    "romantic": "romantic",
    "evening": "evening",
    "party": "evening",
    "fashion": "fashion",
    "statement": "fashion",
}
STYLE_COMPATIBILITY_PAIRS = {
    frozenset({"minimal", "classic"}),
    frozenset({"minimal", "casual"}),
    frozenset({"classic", "romantic"}),
    frozenset({"classic", "fashion"}),
    frozenset({"casual", "sport"}),
    frozenset({"casual", "fashion"}),
    frozenset({"casual", "romantic"}),
    frozenset({"evening", "fashion"}),
    frozenset({"classic", "evening"}),
}
SUBCATEGORY_LAYER_LEVELS = {
    "t_shirt": "base",
    "shirt": "base",
    "blouse": "base",
    "crop_top": "base",
    "polo": "base",
    "longsleeve": "base",
    "tank_top": "base",
    "sweater": "mid",
    "hoodie": "mid",
    "cardigan": "mid",
    "turtleneck": "mid",
    "sweatshirt": "mid",
    "vest_top": "mid",
    "coat": "outer",
    "parka": "outer",
    "down_jacket": "outer",
    "jacket": "outer",
    "trench": "outer",
    "blazer": "outer",
    "leather_jacket": "outer",
    "windbreaker": "outer",
    "vest_outerwear": "outer",
}
WATERPROOF_OUTERWEAR_TYPES = {"trench", "parka", "down_jacket", "windbreaker", "jacket"}
WINDPROOF_OUTERWEAR_TYPES = {"coat", "parka", "down_jacket", "windbreaker", "leather_jacket"}
WATER_RESISTANT_MATERIALS = {"leather", "nylon", "polyester", "gabardine"}
TEXTURE_ALIAS_MAP = {
    "cotton": "soft_woven",
    "linen": "soft_woven",
    "silk": "fluid",
    "viscose": "fluid",
    "wool": "knit",
    "cashmere": "knit",
    "knit": "knit",
    "jersey": "knit",
    "denim": "structured",
    "leather": "structured",
    "suede": "structured",
    "tweed": "structured",
}
SUBCATEGORY_TEXTURE_MAP = {
    "jeans": "structured",
    "coat": "structured",
    "blazer": "structured",
    "leather_jacket": "structured",
    "trench": "structured",
    "sweater": "knit",
    "cardigan": "knit",
    "hoodie": "knit",
    "turtleneck": "knit",
    "shirt": "soft_woven",
    "blouse": "fluid",
    "dress_shirt": "soft_woven",
}
FITTED_SUBCATEGORIES = {
    "shirt",
    "blouse",
    "turtleneck",
    "blazer",
    "trousers",
    "pumps",
    "loafers",
    "closed_shoes",
}
RELAXED_SUBCATEGORIES = {
    "t_shirt",
    "sweater",
    "hoodie",
    "cardigan",
    "coat",
    "parka",
    "jacket",
    "jeans",
    "joggers",
    "sneakers",
}
EVENT_DISALLOWED_STYLES = {
    "office": {"sport"},
    "evening": {"sport"},
    "party": {"sport"},
}
EVENT_DISALLOWED_SUBCATEGORIES = {
    "office": {"flip_flops", "slippers", "felt_boots", "shorts", "hoodie"},
    "evening": {"flip_flops", "slippers", "felt_boots", "joggers", "hoodie"},
    "party": {"felt_boots", "snow_boots", "flip_flops"},
    "sport": {"blazer", "coat", "pumps", "loafers"},
}


class RecommendationEngine:
    def __init__(self, weights=None):
        self.weights = {**FEATURE_WEIGHTS, **(weights or {})}

    def generate(self, clothing_items, request_context, user_preferences=None, limit=5):
        candidates = self.generate_candidate_outfits(clothing_items, request_context)
        ranked_outfits = [
            self.evaluate_outfit(candidate, request_context, user_preferences or {})
            for candidate in candidates
        ]
        ranked_outfits.sort(key=lambda outfit: outfit["score"], reverse=True)

        top_outfits = ranked_outfits[:limit]
        for index, outfit in enumerate(top_outfits, start=1):
            event_type = request_context.get("event_type", "casual")
            outfit["name"] = self.build_outfit_name(event_type, index)

        return top_outfits

    def build_outfit_name(self, event_type, index):
        event_label = EVENT_LABELS.get(self._normalize_token(event_type), "базовый")
        return f"Образ: {event_label} #{index}"

    def generate_candidate_outfits(self, clothing_items, request_context):
        categorized_items = self._categorize_items(clothing_items)
        anchor_item = self._find_anchor_item(
            clothing_items,
            request_context.get("anchor_item_id"),
        )
        if request_context.get("anchor_item_id") and anchor_item is None:
            return []

        tops = self._build_pool(categorized_items["top"], anchor_item, "top")
        bottoms = self._build_pool(categorized_items["bottom"], anchor_item, "bottom")
        shoes = self._build_pool(categorized_items["shoes"], anchor_item, "shoes")
        outerwear = self._build_pool(
            categorized_items["outerwear"],
            anchor_item,
            "outerwear",
            allow_empty=True,
        )
        accessories = self._build_pool(
            categorized_items["accessory"],
            anchor_item,
            "accessory",
            allow_empty=True,
        )

        if not tops or not bottoms or not shoes:
            return []

        constraints = self._normalize_tokens(request_context.get("constraints"))
        candidates = []
        if anchor_item and anchor_item.category == "accessory":
            accessory_pool = [anchor_item]
        else:
            accessory_pool = [item for item in accessories[:MAX_ACCESSORY_POOL] if item is not None]
            accessory_pool = [None] + accessory_pool if accessory_pool else [None]

        for top_item, bottom_item, shoes_item in product(
            tops[:MAX_PRIMARY_POOL],
            bottoms[:MAX_PRIMARY_POOL],
            shoes[:MAX_PRIMARY_POOL],
        ):
            base_candidate = [
                self._make_candidate_entry("top", top_item),
                self._make_candidate_entry("bottom", bottom_item),
                self._make_candidate_entry("shoes", shoes_item),
            ]
            for accessory_item in accessory_pool:
                candidate_with_accessory = list(base_candidate)
                if accessory_item is not None:
                    candidate_with_accessory.append(
                        self._make_candidate_entry("accessory", accessory_item)
                    )

                if (
                    (not anchor_item or anchor_item.category != "outerwear")
                    and self._is_valid_candidate(
                    candidate_with_accessory,
                    constraints,
                    request_context,
                    )
                ):
                    candidates.append(candidate_with_accessory)

                for outerwear_item in outerwear[:MAX_OUTERWEAR_POOL]:
                    if outerwear_item is None:
                        continue
                    layered_candidate = list(candidate_with_accessory) + [
                        self._make_candidate_entry("outerwear", outerwear_item)
                    ]
                    if self._is_valid_candidate(
                        layered_candidate,
                        constraints,
                        request_context,
                    ):
                        candidates.append(layered_candidate)

        return self._deduplicate_candidates(candidates)

    def evaluate_outfit(self, candidate, request_context, user_preferences=None):
        color_detail = self._evaluate_color_harmony(candidate, request_context)
        contextual_weights = self._get_contextual_weights(request_context)
        feature_scores = self.get_feature_scores(
            candidate,
            request_context,
            user_preferences or {},
            color_detail=color_detail,
        )
        total_score = self.calculate_total_score(feature_scores, contextual_weights)
        reasons, explanation = self.build_outfit_explanation(
            feature_scores,
            request_context,
            feature_details={"color_harmony": color_detail},
        )

        items = [
            self._serialize_candidate_item(entry)
            for entry in sorted(candidate, key=lambda entry: ROLE_ORDER[entry["role"]])
        ]

        return {
            "name": "",
            "event_type": request_context.get("event_type"),
            "weather_context": {
                "temperature": request_context.get("temperature"),
                "weather_condition": request_context.get("weather_condition"),
                "season": request_context.get("season"),
                "city": request_context.get("city"),
            },
            "items": items,
            "score": total_score,
            "total_score": total_score,
            "feature_scores": feature_scores,
            "scores_by_feature": feature_scores,
            "applied_weights": contextual_weights,
            "reasons": reasons,
            "explanation": explanation,
        }

    def get_feature_scores(
        self,
        candidate,
        request_context,
        user_preferences=None,
        color_detail=None,
    ):
        items = [entry["item"] for entry in candidate]
        user_preferences = user_preferences or {}
        color_detail = color_detail or self._evaluate_color_harmony(
            candidate,
            request_context,
        )

        return {
            "color_harmony": color_detail["score"],
            "style_match": self.score_style_match(items, request_context),
            "event_match": self.score_event_match(items, request_context),
            "season_match": self.score_season_match(items, request_context),
            "temperature_match": self.score_temperature_match(candidate, request_context),
            "weather_condition_match": self.score_weather_condition_match(
                candidate,
                request_context,
            ),
            "completeness": self.score_completeness(candidate, request_context),
            "layering_correctness": self.score_layering_correctness(
                candidate,
                request_context,
            ),
            "user_preference_match": self.score_user_preference_match(
                candidate,
                request_context,
                user_preferences,
            ),
            "constraints_match": self.score_constraints_match(
                candidate,
                request_context,
                user_preferences,
            ),
        }

    def calculate_total_score(self, feature_scores, weights=None):
        active_weights = weights or self.weights
        total_score = 0.0
        for feature_name, weight in active_weights.items():
            total_score += feature_scores.get(feature_name, 0.0) * weight
        return round(min(max(total_score, 0.0), 1.0), 4)

    def build_outfit_explanation(
        self,
        feature_scores,
        request_context,
        feature_details=None,
    ):
        feature_details = feature_details or {}
        color_detail = feature_details.get("color_harmony") or {}
        event_label = EVENT_LABELS.get(
            self._normalize_token(request_context.get("event_type")),
            "выбранного события",
        )
        reason_templates = {
            "color_harmony": (
                color_detail.get(
                    "reason",
                    "Цвета вещей хорошо сочетаются между собой",
                ),
                color_detail.get(
                    "fragment",
                    "цвета выглядят согласованно",
                ),
            ),
            "style_match": (
                "Стили вещей хорошо сочетаются",
                "стили вещей не конфликтуют",
            ),
            "event_match": (
                f"Образ подходит для события: {event_label}",
                "образ подходит под выбранное событие",
            ),
            "season_match": (
                "Вещи согласованы по сезону",
                "вещи подходят по сезону",
            ),
            "temperature_match": (
                "Образ соответствует заданной температуре",
                "комплект подходит под температуру",
            ),
            "weather_condition_match": (
                "Образ соответствует погодным условиям",
                "погода учтена при подборе",
            ),
            "completeness": (
                "Собран полный комплект одежды",
                "комплект выглядит полным",
            ),
            "layering_correctness": (
                "Слои подобраны логично и без конфликтов",
                "слои собраны корректно",
            ),
            "user_preference_match": (
                "Учтены предпочтения пользователя",
                "предпочтения пользователя были учтены",
            ),
            "constraints_match": (
                "Соблюдены заданные ограничения",
                "заданные ограничения соблюдены",
            ),
        }

        sorted_features = sorted(
            feature_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        best_features = [item for item in sorted_features if item[1] >= 0.75][:4]
        if not best_features:
            best_features = sorted_features[:2]

        reasons = [reason_templates[name][0] for name, _score in best_features]
        fragments = [reason_templates[name][1] for name, _score in best_features[:3]]

        if not fragments:
            explanation = "Образ собран без явных конфликтов и подходит для базового использования."
        elif len(fragments) == 1:
            explanation = f"Образ получил высокий балл, потому что {fragments[0]}."
        else:
            explanation = (
                "Образ получил высокий балл, потому что "
                f"{', '.join(fragments[:-1])} и {fragments[-1]}."
            )

        return reasons, explanation

    def score_color_harmony(self, outfit, request_context):
        return self._evaluate_color_harmony(outfit, request_context)["score"]

    def score_style_match(self, items, request_context):
        style_profiles = [
            self._get_item_style_families(item)
            for item in items
            if self._get_item_style_families(item)
        ]
        if not style_profiles:
            return 0.65

        style_counter = Counter(
            style_family
            for style_profile in style_profiles
            for style_family in style_profile
        )
        dominant_ratio = style_counter.most_common(1)[0][1] / len(style_profiles)

        pair_scores = [
            self._score_style_profile_pair(left_profile, right_profile)
            for left_profile, right_profile in combinations(style_profiles, 2)
        ]
        pairwise_score = sum(pair_scores) / len(pair_scores) if pair_scores else 0.9

        preferred_style = self._normalize_token(request_context.get("preferred_style"))
        preferred_family = STYLE_FAMILY_MAP.get(preferred_style, preferred_style)
        preferred_bonus = 0.75
        if preferred_family:
            preferred_bonus = sum(
                1.0 if preferred_family in style_profile else 0.5
                for style_profile in style_profiles
            ) / len(style_profiles)

        return round(
            min(
                1.0,
                (dominant_ratio * 0.45)
                + (pairwise_score * 0.35)
                + (preferred_bonus * 0.2),
            ),
            4,
        )

    def score_event_match(self, items, request_context):
        event_type = self._normalize_token(request_context.get("event_type")) or "casual"
        event_rule = EVENT_RULES.get(event_type, EVENT_RULES["casual"])
        if any(not self._item_matches_event_hard_rule(item, event_type) for item in items):
            return 0.0

        item_scores = [
            self._score_item_event_fit(item, event_type, event_rule)
            for item in items
        ]
        return round(sum(item_scores) / len(item_scores), 4)

    def score_season_match(self, items, request_context):
        target_season = self._normalize_token(request_context.get("season"))
        if not target_season:
            target_season = self._infer_season_from_temperature(
                request_context.get("temperature")
            )

        item_seasons = [
            self._normalize_token(item.season)
            for item in items
            if self._normalize_token(item.season)
        ]
        if not item_seasons:
            return 0.7

        target_score = 0.78
        if target_season:
            target_matches = [
                self._score_item_season_fit(item_season, target_season)
                for item_season in item_seasons
            ]
            target_score = sum(target_matches) / len(target_matches)

        filtered_seasons = [
            item_season for item_season in item_seasons if item_season != "all_season"
        ]
        internal_consistency = 1.0
        if filtered_seasons:
            internal_consistency = (
                Counter(filtered_seasons).most_common(1)[0][1] / len(filtered_seasons)
            )

        insulation_score = self._score_insulation_balance(items, request_context)
        return round(
            (target_score * 0.4)
            + (internal_consistency * 0.2)
            + (insulation_score * 0.4),
            4,
        )

    def score_temperature_match(self, candidate, request_context):
        temperature = request_context.get("temperature")
        if temperature is None:
            return 0.7

        items = [entry["item"] for entry in candidate]
        shoes = self._get_item_by_category(candidate, "shoes")
        outerwear_score = self._score_outerwear_fit(
            candidate,
            temperature,
            request_context.get("weather_condition"),
        )
        warmth_score = self._score_insulation_balance(items, request_context)
        shoes_score = self._score_shoe_temperature_fit(shoes, temperature)
        layer_score = self._score_layer_coverage(candidate, request_context)

        return round(
            (warmth_score * 0.45)
            + (shoes_score * 0.25)
            + (layer_score * 0.2)
            + (outerwear_score * 0.1),
            4,
        )

    def score_weather_condition_match(self, candidate, request_context):
        weather_condition = self._normalize_token(request_context.get("weather_condition"))
        if not weather_condition:
            return 0.7

        normalized_weather = {"clear": "sunny"}.get(weather_condition, weather_condition)
        temperature = request_context.get("temperature")
        shoes = self._get_item_by_category(candidate, "shoes")
        bottom = self._get_item_by_category(candidate, "bottom")
        protection_score = self._score_weather_protection(
            candidate,
            normalized_weather,
            temperature,
        )

        shoes_score = self._score_shoe_weather_fit(
            shoes,
            normalized_weather,
            temperature,
        )
        outerwear_score = self._score_outerwear_fit(
            candidate,
            temperature,
            normalized_weather,
        )
        bottom_score = self._score_bottom_weather_fit(
            bottom,
            normalized_weather,
            temperature,
        )

        if normalized_weather == "snow" and shoes_score < 0.45:
            return 0.0

        return round(
            (protection_score * 0.35)
            + (shoes_score * 0.3)
            + (outerwear_score * 0.2)
            + (bottom_score * 0.15),
            4,
        )

    def score_completeness(self, candidate, request_context=None):
        roles = {entry["role"] for entry in candidate}
        required_roles = {"top", "bottom", "shoes"}
        matched_roles = len(roles & required_roles)
        base_score = matched_roles / len(required_roles)
        request_context = request_context or {}
        needs_outerwear = self._requires_outerwear(request_context)
        outerwear_score = 1.0 if not needs_outerwear else 1.0 if "outerwear" in roles else 0.2
        event_type = self._normalize_token(request_context.get("event_type"))
        accessory_bonus = 0.85
        if event_type in {"office", "evening", "party", "date"}:
            accessory_bonus = 1.0 if "accessory" in roles else 0.55
        return round(
            min(1.0, (base_score * 0.75) + (outerwear_score * 0.15) + (accessory_bonus * 0.1)),
            4,
        )

    def score_layering_correctness(self, candidate, request_context):
        role_counts = Counter(entry["role"] for entry in candidate)
        if any(count > 1 for count in role_counts.values()):
            return 0.3

        roles = set(role_counts)
        if not {"top", "bottom", "shoes"}.issubset(roles):
            return 0.35

        has_outerwear = "outerwear" in roles
        temperature = request_context.get("temperature")
        weather_condition = self._normalize_token(request_context.get("weather_condition"))

        if has_outerwear and "top" not in roles:
            return 0.3
        if self._requires_outerwear(request_context) and not has_outerwear:
            return 0.2
        if temperature is not None and temperature >= 24 and has_outerwear:
            outerwear = self._get_item_by_category(candidate, "outerwear")
            if self._normalize_token(outerwear.subcategory) in HEAVY_OUTERWEAR_TYPES:
                return 0.35
            return 0.7
        if weather_condition in {"rain", "snow", "wind"} and not has_outerwear:
            return 0.35

        layer_score = self._score_layer_coverage(candidate, request_context)
        texture_score = self._score_texture_contrast(candidate)
        silhouette_score = self._score_silhouette_balance(candidate)
        return round(
            (layer_score * 0.55)
            + (texture_score * 0.2)
            + (silhouette_score * 0.25),
            4,
        )

    def score_user_preference_match(self, candidate, request_context, user_preferences):
        items = [entry["item"] for entry in candidate]
        preferred_colors = {
            self._normalize_color(color)
            for color in self._split_color_values(user_preferences.get("preferred_colors"))
        }
        preferred_colors |= {
            self._normalize_color(color)
            for color in self._split_color_values(request_context.get("preferred_colors"))
        }
        preferred_colors.discard(None)

        preferred_styles = {
            STYLE_FAMILY_MAP.get(style, style)
            for style in self._normalize_tokens(user_preferences.get("preferred_styles"))
        }
        request_style = self._normalize_token(request_context.get("preferred_style"))
        if request_style:
            preferred_styles.add(STYLE_FAMILY_MAP.get(request_style, request_style))

        colors_score = 0.75
        if preferred_colors:
            color_hits = 0
            for item in items:
                item_colors = set(self._extract_item_colors(item))
                item_families = {
                    self._get_color_family(color_token) for color_token in item_colors
                }
                if item_colors & preferred_colors:
                    color_hits += 1
                elif any(
                    self._get_color_family(color_token) in item_families
                    for color_token in preferred_colors
                ):
                    color_hits += 0.75
            colors_score = color_hits / len(items)

        styles_score = 0.75
        if preferred_styles:
            style_hits = 0
            for item in items:
                item_styles = self._get_item_style_families(item)
                if item_styles & preferred_styles:
                    style_hits += 1
            styles_score = style_hits / len(items)

        constraint_alignment = 1.0
        request_constraints = self._normalize_tokens(request_context.get("constraints"))
        if request_constraints:
            constraint_alignment = (
                1.0
                if not self._violates_hard_constraints(candidate, request_constraints)
                else 0.3
            )

        return round(
            (colors_score * 0.45)
            + (styles_score * 0.35)
            + (constraint_alignment * 0.2),
            4,
        )

    def score_constraints_match(self, candidate, request_context, user_preferences):
        constraints = self._normalize_tokens(request_context.get("constraints"))
        constraints += self._normalize_tokens(user_preferences.get("constraints"))
        disliked_items = self._normalize_tokens(user_preferences.get("disliked_items"))

        total_checks = len(constraints) + len(disliked_items)
        if total_checks == 0:
            return 1.0

        violations = 0
        for constraint in constraints:
            if self._candidate_violates_constraint(candidate, constraint):
                violations += 1

        for disliked_item in disliked_items:
            if self._candidate_has_attribute(candidate, disliked_item):
                violations += 1

        return round(max(0.0, 1 - (violations / total_checks)), 4)

    def _categorize_items(self, clothing_items):
        categorized = {
            "top": [],
            "bottom": [],
            "shoes": [],
            "outerwear": [],
            "accessory": [],
        }
        for item in clothing_items:
            if item.category in categorized:
                categorized[item.category].append(item)
        return categorized

    def _build_pool(self, items, anchor_item, category, allow_empty=False):
        if anchor_item and anchor_item.category == category:
            return [anchor_item]
        if allow_empty:
            return items or [None]
        return items

    def _find_anchor_item(self, clothing_items, anchor_item_id):
        if not anchor_item_id:
            return None
        return next((item for item in clothing_items if item.id == anchor_item_id), None)

    def _make_candidate_entry(self, role, item):
        return {"role": role, "item": item}

    def _is_valid_candidate(self, candidate, constraints, request_context):
        item_ids = [entry["item"].id for entry in candidate if entry.get("item")]
        if len(item_ids) != len(set(item_ids)):
            return False

        roles = {entry["role"] for entry in candidate}
        if not {"top", "bottom", "shoes"}.issubset(roles):
            return False

        if self._violates_hard_constraints(candidate, constraints):
            return False
        if any(
            not self._item_matches_event_hard_rule(entry["item"], self._normalize_token(request_context.get("event_type")) or "casual")
            for entry in candidate
        ):
            return False

        shoes = self._get_item_by_category(candidate, "shoes")
        bottom = self._get_item_by_category(candidate, "bottom")
        temperature = request_context.get("temperature")
        weather_condition = request_context.get("weather_condition")

        if self._score_shoe_temperature_fit(shoes, temperature) < 0.45:
            return False
        if self._score_shoe_weather_fit(shoes, weather_condition, temperature) < 0.45:
            return False
        if self._score_bottom_weather_fit(bottom, weather_condition, temperature) < 0.35:
            return False
        if self._requires_outerwear(request_context) and "outerwear" not in roles:
            return False

        return True

    def _deduplicate_candidates(self, candidates):
        unique_candidates = []
        seen = set()
        for candidate in candidates:
            key = tuple(
                sorted((entry["role"], entry["item"].id) for entry in candidate)
            )
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)
        return unique_candidates

    def _serialize_candidate_item(self, entry):
        item = entry["item"]
        payload = item.to_dict()
        payload["role"] = entry["role"]
        payload["clothing_item_id"] = item.id
        return payload

    def _normalize_tokens(self, values):
        if not values:
            return []
        normalized = []
        for value in values:
            token = self._normalize_token(value)
            if token:
                normalized.append(token)
        return normalized

    def _normalize_token(self, value):
        if value is None:
            return None
        token = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        return token or None

    def _normalize_color(self, value):
        token = self._normalize_token(value)
        if not token:
            return None

        if token in COLOR_ALIASES:
            return COLOR_ALIASES[token]

        parts = [part for part in token.split("_") if part]
        for size in range(min(3, len(parts)), 0, -1):
            for start in range(0, len(parts) - size + 1):
                candidate = "_".join(parts[start : start + size])
                if candidate in COLOR_ALIASES:
                    return COLOR_ALIASES[candidate]

        for part in parts:
            if part in COLOR_ALIASES:
                return COLOR_ALIASES[part]

        return "unknown"

    def _get_color_family(self, color_token):
        normalized_color = self._normalize_color(color_token)
        if not normalized_color:
            return "unknown"
        return COLOR_FAMILY_MAP.get(normalized_color, "unknown")

    def _is_neutral_color(self, color_token):
        normalized_color = self._normalize_color(color_token)
        return normalized_color in NEUTRAL_COLOR_TOKENS

    def _is_metallic_color(self, color_token):
        normalized_color = self._normalize_color(color_token)
        return normalized_color in METALLIC_COLOR_TOKENS

    def _coerce_outfit_entries(self, outfit):
        entries = []
        for entry in outfit or []:
            if isinstance(entry, dict) and "item" in entry:
                item = entry.get("item")
                role = self._normalize_token(entry.get("role"))
            else:
                item = entry
                role = None

            if item is None:
                continue

            entries.append(
                {
                    "role": role or self._normalize_token(getattr(item, "category", None)) or "item",
                    "item": item,
                }
            )

        return entries

    def _normalize_weights(self, weights):
        total_weight = sum(max(weight, 0.0) for weight in weights.values()) or 1.0
        return {
            feature_name: round(max(weight, 0.0) / total_weight, 4)
            for feature_name, weight in weights.items()
        }

    def _get_contextual_weights(self, request_context):
        weights = dict(self.weights)
        temperature = request_context.get("temperature")
        weather_condition = self._normalize_token(request_context.get("weather_condition"))
        event_type = self._normalize_token(request_context.get("event_type"))

        if weather_condition in {"snow", "rain", "wind"} or (
            temperature is not None and temperature <= 5
        ):
            weights["weather_condition_match"] += 0.05
            weights["temperature_match"] += 0.04
            weights["season_match"] += 0.03
            weights["layering_correctness"] += 0.03
            weights["color_harmony"] -= 0.05
            weights["style_match"] -= 0.03
            weights["user_preference_match"] -= 0.04
            weights["completeness"] -= 0.03

        if event_type in {"office", "evening", "party", "date"}:
            weights["event_match"] += 0.03
            weights["style_match"] += 0.02
            weights["color_harmony"] += 0.01
            weights["user_preference_match"] -= 0.03
            weights["constraints_match"] -= 0.03

        return self._normalize_weights(weights)

    def _get_item_style_families(self, item):
        style_families = {
            STYLE_FAMILY_MAP.get(style_token, style_token)
            for style_token in self._normalize_tokens(item.styles or [])
        }
        style_families.discard(None)

        if style_families:
            return style_families

        formality = self._normalize_token(item.formality)
        subcategory = self._normalize_token(item.subcategory)
        if formality in {"formal", "smart"} or subcategory in {"blazer", "loafers", "pumps"}:
            return {"classic"}
        if subcategory in {"hoodie", "joggers", "sneakers", "summer_sneakers"}:
            return {"casual"}
        return {"casual"}

    def _score_style_profile_pair(self, left_profile, right_profile):
        if left_profile & right_profile:
            return 1.0
        if any(
            frozenset({left_family, right_family}) in STYLE_COMPATIBILITY_PAIRS
            for left_family in left_profile
            for right_family in right_profile
        ):
            return 0.8
        return 0.45

    def _item_matches_event_hard_rule(self, item, event_type):
        disallowed_styles = EVENT_DISALLOWED_STYLES.get(event_type, set())
        if self._get_item_style_families(item) & disallowed_styles:
            return False

        subcategory = self._normalize_token(item.subcategory)
        if subcategory in EVENT_DISALLOWED_SUBCATEGORIES.get(event_type, set()):
            return False

        return True

    def _score_shoe_event_fit(self, item, event_type):
        subcategory = self._normalize_token(item.subcategory)
        if event_type == "office":
            if subcategory in {"loafers", "pumps", "closed_shoes", "boots", "ankle_boots"}:
                return 1.0
            if subcategory in {"sneakers", "summer_sneakers"}:
                return 0.7
            return 0.25

        if event_type in {"evening", "party", "date"}:
            if subcategory in {"pumps", "heels", "loafers", "closed_shoes", "boots", "ankle_boots"}:
                return 1.0
            if subcategory in {"sneakers", "summer_sneakers"}:
                return 0.65
            return 0.2

        if event_type == "sport":
            if subcategory in {"sneakers", "summer_sneakers"}:
                return 1.0
            if subcategory in {"boots", "ankle_boots"}:
                return 0.45
            return 0.2

        return 0.9 if subcategory not in {"pumps", "heels"} else 0.75

    def _score_item_event_fit(self, item, event_type, event_rule):
        allowed_styles = {
            STYLE_FAMILY_MAP.get(style_token, style_token)
            for style_token in event_rule["styles"]
        }
        style_families = self._get_item_style_families(item)
        if style_families & allowed_styles:
            style_score = 1.0
        elif any(
            frozenset({style_family, allowed_style}) in STYLE_COMPATIBILITY_PAIRS
            for style_family in style_families
            for allowed_style in allowed_styles
        ):
            style_score = 0.7
        else:
            style_score = 0.25

        formality = self._normalize_token(item.formality)
        if formality in event_rule["formalities"]:
            formality_score = 1.0
        elif formality == "smart" and "formal" in event_rule["formalities"]:
            formality_score = 0.8
        elif formality == "casual" and "smart" in event_rule["formalities"]:
            formality_score = 0.55
        else:
            formality_score = 0.25

        shoe_score = 1.0
        if self._normalize_token(item.category) == "shoes":
            shoe_score = self._score_shoe_event_fit(item, event_type)

        return round(
            (style_score * 0.45) + (formality_score * 0.35) + (shoe_score * 0.2),
            4,
        )

    def _score_item_season_fit(self, item_season, target_season):
        normalized_item_season = self._normalize_token(item_season)
        if normalized_item_season in {None, "all_season"}:
            return 0.9
        if normalized_item_season == target_season:
            return 1.0

        adjacent_seasons = {
            frozenset({"winter", "autumn"}),
            frozenset({"autumn", "spring"}),
            frozenset({"spring", "summer"}),
        }
        if frozenset({normalized_item_season, target_season}) in adjacent_seasons:
            return 0.72
        return 0.35

    def _estimate_required_insulation(self, request_context):
        temperature = request_context.get("temperature")
        target_season = self._normalize_token(request_context.get("season"))

        if temperature is not None:
            if temperature <= -15:
                return 10.2
            if temperature <= -5:
                return 8.8
            if temperature <= 5:
                return 7.1
            if temperature <= 15:
                return 5.8
            if temperature <= 24:
                return 4.3
            return 3.0

        return {
            "winter": 8.5,
            "autumn": 6.3,
            "spring": 5.7,
            "summer": 3.2,
        }.get(target_season, 5.2)

    def _score_insulation_balance(self, items, request_context):
        provided_insulation = sum(self._estimate_item_warmth(item) for item in items)
        required_insulation = self._estimate_required_insulation(request_context)
        if required_insulation <= 0:
            return 0.8

        if provided_insulation <= required_insulation:
            return round(min(provided_insulation / required_insulation, 1.0), 4)

        excess_ratio = (provided_insulation - required_insulation) / required_insulation
        return round(max(0.3, 1.0 - (excess_ratio * 0.35)), 4)

    def _infer_layer_level(self, item):
        explicit_layer_level = self._normalize_token(getattr(item, "layer_level", None))
        if explicit_layer_level in {"base", "mid", "outer", "support"}:
            return explicit_layer_level

        category = self._normalize_token(item.category)
        subcategory = self._normalize_token(item.subcategory)
        if category == "outerwear":
            return "outer"
        if subcategory in SUBCATEGORY_LAYER_LEVELS:
            return SUBCATEGORY_LAYER_LEVELS[subcategory]
        if category == "top":
            return "base"
        return None

    def _get_required_layers(self, request_context):
        temperature = request_context.get("temperature")
        weather_condition = self._normalize_token(request_context.get("weather_condition"))

        if weather_condition == "snow" or (temperature is not None and temperature <= 0):
            return {"base", "mid", "outer"}
        if weather_condition in {"rain", "wind"} or (temperature is not None and temperature <= 12):
            return {"base", "outer"}
        return {"base"}

    def _score_layer_coverage(self, candidate, request_context):
        layer_levels = {
            self._infer_layer_level(entry["item"])
            for entry in candidate
            if self._infer_layer_level(entry["item"])
        }
        required_layers = self._get_required_layers(request_context)
        coverage_score = len(layer_levels & required_layers) / len(required_layers)

        temperature = request_context.get("temperature")
        if temperature is not None and temperature >= 24 and "outer" in layer_levels:
            outerwear = self._get_item_by_category(candidate, "outerwear")
            if outerwear and self._normalize_token(outerwear.subcategory) in HEAVY_OUTERWEAR_TYPES:
                coverage_score *= 0.45

        return round(min(max(coverage_score, 0.0), 1.0), 4)

    def _get_texture_key(self, item):
        material = self._normalize_token(getattr(item, "material", None))
        subcategory = self._normalize_token(item.subcategory)
        if material in TEXTURE_ALIAS_MAP:
            return TEXTURE_ALIAS_MAP[material]
        if subcategory in SUBCATEGORY_TEXTURE_MAP:
            return SUBCATEGORY_TEXTURE_MAP[subcategory]
        category = self._normalize_token(item.category)
        return {
            "outerwear": "structured",
            "shoes": "structured",
            "accessory": "structured",
            "top": "soft_woven",
            "bottom": "structured",
        }.get(category, "soft_woven")

    def _score_texture_contrast(self, candidate):
        items = [
            entry["item"]
            for entry in candidate
            if entry["role"] in {"top", "bottom", "outerwear", "accessory"}
        ]
        if len(items) < 2:
            return 0.7

        unique_textures = {self._get_texture_key(item) for item in items}
        unique_count = len(unique_textures)
        if unique_count == 1:
            return 0.45
        if unique_count == 2:
            return 0.72
        return min(1.0, 0.82 + ((unique_count - 3) * 0.06))

    def _infer_fit_profile(self, item):
        explicit_fit = self._normalize_token(getattr(item, "fit", None))
        explicit_fit_map = {
            "fitted": "fitted",
            "balanced": "balanced",
            "loose": "loose",
            "oversized": "loose",
        }
        if explicit_fit in explicit_fit_map:
            return explicit_fit_map[explicit_fit]

        subcategory = self._normalize_token(item.subcategory)
        if subcategory in FITTED_SUBCATEGORIES:
            return "fitted"
        if subcategory in RELAXED_SUBCATEGORIES:
            return "loose"

        style_families = self._get_item_style_families(item)
        if "classic" in style_families or "romantic" in style_families:
            return "fitted"
        if "sport" in style_families or "casual" in style_families:
            return "loose"
        return "balanced"

    def _score_silhouette_balance(self, candidate):
        fit_profiles = [
            self._infer_fit_profile(entry["item"])
            for entry in candidate
            if entry["role"] in {"top", "bottom", "outerwear"}
        ]
        if not fit_profiles:
            return 0.7

        loose_count = sum(1 for fit_profile in fit_profiles if fit_profile == "loose")
        fitted_count = sum(1 for fit_profile in fit_profiles if fit_profile == "fitted")
        if loose_count == 0 and fitted_count == 0:
            return 0.7

        return round(
            1.0 - abs(loose_count - fitted_count) / (loose_count + fitted_count),
            4,
        )

    def _score_weather_protection(self, candidate, weather_condition, temperature):
        if weather_condition == "sunny":
            outerwear = self._get_item_by_category(candidate, "outerwear")
            if (
                outerwear
                and temperature is not None
                and temperature >= 24
                and self._normalize_token(outerwear.subcategory) in HEAVY_OUTERWEAR_TYPES
            ):
                return 0.4
            return 0.9

        if weather_condition == "cloudy":
            return 0.88 if not self._requires_outerwear({"temperature": temperature, "weather_condition": weather_condition}) else 0.78

        outerwear = self._get_item_by_category(candidate, "outerwear")
        if outerwear is None:
            return 0.15 if weather_condition in {"rain", "snow"} else 0.45

        outerwear_subcategory = self._normalize_token(outerwear.subcategory)
        outerwear_material = self._normalize_token(outerwear.material)
        explicit_waterproof = bool(getattr(outerwear, "waterproof", False))
        explicit_windproof = bool(getattr(outerwear, "windproof", False))

        if weather_condition == "rain":
            if (
                explicit_waterproof
                or explicit_windproof
                or outerwear_subcategory in WATERPROOF_OUTERWEAR_TYPES
                or outerwear_material in WATER_RESISTANT_MATERIALS
            ):
                return 1.0
            if outerwear_subcategory in WINDPROOF_OUTERWEAR_TYPES:
                return 0.75
            return 0.65

        if weather_condition == "snow":
            if (
                explicit_windproof
                or explicit_waterproof
                or outerwear_subcategory in HEAVY_OUTERWEAR_TYPES | WINDPROOF_OUTERWEAR_TYPES
            ):
                return 1.0
            return 0.55

        if weather_condition == "wind":
            if explicit_windproof or outerwear_subcategory in WINDPROOF_OUTERWEAR_TYPES:
                return 1.0
            if explicit_waterproof or outerwear_subcategory in WATERPROOF_OUTERWEAR_TYPES:
                return 0.82
            return 0.7

        return 0.8

    def _split_color_values(self, colors):
        if not colors:
            return []
        if isinstance(colors, str):
            raw_values = colors
            for separator in ["/", ";", "|"]:
                raw_values = raw_values.replace(separator, ",")
            return [value.strip() for value in raw_values.split(",") if value.strip()]
        return list(colors)

    def _extract_item_colors(self, item):
        colors = []
        for value in self._split_color_values(getattr(item, "colors", None)):
            normalized_color = self._normalize_color(value)
            if normalized_color and normalized_color not in colors:
                colors.append(normalized_color)
        return colors[:3]

    def _get_color_share_weights(self, color_count):
        if color_count <= 1:
            return (1.0,)
        if color_count == 2:
            return (0.78, 0.22)
        return COLOR_SHARE_WEIGHTS[:color_count]

    # Approximate palette proportions by garment role so top/bottom dominate,
    # while shoes and accessories stay softer accents.
    def _build_outfit_color_profile(self, outfit):
        entries = self._coerce_outfit_entries(outfit)
        family_weights = Counter()
        active_family_weights = Counter()
        token_weights = Counter()
        role_profiles = {}
        total_weight = 0.0
        known_weight = 0.0
        neutral_weight = 0.0
        metallic_weight = 0.0
        unknown_weight = 0.0

        for entry in entries:
            item = entry["item"]
            role = entry["role"]
            role_weight = ROLE_COLOR_WEIGHTS.get(role, ROLE_COLOR_WEIGHTS["item"])
            colors = self._extract_item_colors(item)
            role_family_weights = Counter()
            role_known_weight = 0.0
            role_neutral_weight = 0.0
            role_metallic_weight = 0.0
            role_active_families = set()
            role_families = set()

            if not colors:
                soft_unknown_weight = role_weight * 0.45
                total_weight += soft_unknown_weight
                unknown_weight += soft_unknown_weight
                role_profiles[role] = {
                    "role": role,
                    "tokens": [],
                    "families": set(),
                    "active_families": set(),
                    "family_weights": role_family_weights,
                    "known_weight": 0.0,
                    "neutral_share": 0.0,
                    "metallic_share": 0.0,
                }
                continue

            for color_token, share_weight in zip(
                colors,
                self._get_color_share_weights(len(colors)),
            ):
                color_weight = role_weight * share_weight
                family = self._get_color_family(color_token)

                total_weight += color_weight
                token_weights[color_token] += color_weight
                family_weights[family] += color_weight
                role_family_weights[family] += color_weight
                role_families.add(family)

                if family == "unknown":
                    unknown_weight += color_weight
                    continue

                known_weight += color_weight
                role_known_weight += color_weight

                if self._is_neutral_color(color_token):
                    neutral_weight += color_weight
                    role_neutral_weight += color_weight
                elif self._is_metallic_color(color_token):
                    metallic_weight += color_weight
                    role_metallic_weight += color_weight
                else:
                    active_family_weights[family] += color_weight
                    role_active_families.add(family)

            role_profiles[role] = {
                "role": role,
                "tokens": colors,
                "families": role_families,
                "active_families": role_active_families,
                "family_weights": role_family_weights,
                "known_weight": role_known_weight,
                "neutral_share": (
                    role_neutral_weight / role_known_weight if role_known_weight else 0.0
                ),
                "metallic_share": (
                    role_metallic_weight / role_known_weight if role_known_weight else 0.0
                ),
            }

        active_total = sum(active_family_weights.values())
        dominant_active_family = None
        dominant_active_share = 0.0
        if active_family_weights:
            dominant_active_family, dominant_active_weight = active_family_weights.most_common(1)[0]
            dominant_active_share = (
                dominant_active_weight / active_total if active_total else 0.0
            )

        return {
            "total_weight": total_weight,
            "known_weight": known_weight,
            "known_ratio": (known_weight / total_weight) if total_weight else 0.0,
            "neutral_weight": neutral_weight,
            "metallic_weight": metallic_weight,
            "unknown_weight": unknown_weight,
            "unknown_share": (unknown_weight / total_weight) if total_weight else 0.0,
            "neutral_share": (
                (neutral_weight + metallic_weight) / known_weight if known_weight else 0.0
            ),
            "family_weights": family_weights,
            "active_family_weights": active_family_weights,
            "token_weights": token_weights,
            "role_profiles": role_profiles,
            "dominant_family": dominant_active_family,
            "dominant_active_share": dominant_active_share,
        }

    def _score_neutral_base_scheme(self, profile):
        if profile["known_weight"] <= 0:
            return 0.62

        active_family_count = len(profile["active_family_weights"])
        neutral_share = profile["neutral_share"]

        if active_family_count == 0:
            return 0.92
        if neutral_share >= 0.55 and active_family_count == 1:
            return 0.97
        if neutral_share >= 0.45 and active_family_count <= 2:
            return 0.88
        if neutral_share >= 0.35 and active_family_count <= 3:
            return 0.76
        if neutral_share <= 0.15 and active_family_count >= 4:
            return 0.25
        if neutral_share <= 0.2 and active_family_count >= 3:
            return 0.55
        return 0.62

    def _score_monochrome_scheme(self, profile):
        active_family_weights = profile["active_family_weights"]
        if not active_family_weights:
            return 0.82

        active_family_count = len(active_family_weights)
        dominant_share = profile["dominant_active_share"]

        if active_family_count == 1:
            score = 0.96
        elif active_family_count == 2 and dominant_share >= 0.78:
            score = 0.88
        elif active_family_count <= 3 and dominant_share >= 0.7:
            score = 0.76
        else:
            score = 0.34

        if score >= 0.76 and profile["neutral_share"] >= 0.25:
            score += 0.04

        return round(min(score, 1.0), 4)

    def _score_analogous_scheme(self, profile):
        families = list(profile["active_family_weights"].keys())
        if len(families) < 2:
            return 0.35
        if len(families) > 3:
            return 0.22

        analogous_links = sum(
            1
            for left_family, right_family in combinations(families, 2)
            if frozenset({left_family, right_family}) in ANALOGOUS_FAMILY_PAIRS
        )

        if len(families) == 2:
            score = 0.9 if analogous_links == 1 else 0.32
        else:
            score = 0.88 if analogous_links >= 2 else 0.48 if analogous_links == 1 else 0.24

        if analogous_links and profile["dominant_active_share"] >= 0.5:
            score += 0.04

        return round(min(score, 1.0), 4)

    def _score_complementary_scheme(self, profile):
        active_family_weights = profile["active_family_weights"]
        active_total = sum(active_family_weights.values())
        if active_total <= 0:
            return 0.25

        best_score = 0.22
        for left_family, right_family in combinations(active_family_weights.keys(), 2):
            if frozenset({left_family, right_family}) not in COMPLEMENTARY_FAMILY_PAIRS:
                continue

            pair_weight = active_family_weights[left_family] + active_family_weights[right_family]
            dominant_share = max(
                active_family_weights[left_family],
                active_family_weights[right_family],
            ) / pair_weight
            accent_share = min(
                active_family_weights[left_family],
                active_family_weights[right_family],
            ) / pair_weight
            extra_share = max(0.0, active_total - pair_weight) / active_total

            if dominant_share >= 0.65 and accent_share <= 0.35:
                score = 0.9
            elif dominant_share >= 0.58 and accent_share <= 0.42:
                score = 0.78
            else:
                score = 0.58

            score -= extra_share * 0.45
            best_score = max(best_score, score)

        return round(min(max(best_score, 0.0), 1.0), 4)

    def _score_color_complexity(self, profile):
        active_family_weights = profile["active_family_weights"]
        active_total = sum(active_family_weights.values())
        if active_total <= 0:
            return 0.95

        active_family_count = len(active_family_weights)
        if active_family_count == 1:
            score = 0.95
        elif active_family_count == 2:
            score = 0.88
        elif active_family_count == 3:
            score = 0.78
        elif active_family_count == 4:
            score = 0.45
        else:
            score = 0.22

        coverage_top_three = (
            sum(weight for _family, weight in active_family_weights.most_common(3))
            / active_total
        )
        if active_family_count <= 3 and coverage_top_three >= 0.9:
            score += 0.04
        elif active_family_count >= 4 and coverage_top_three < 0.78:
            score -= 0.08

        if profile["unknown_share"] > 0.35:
            score -= 0.05

        return round(min(max(score, 0.0), 1.0), 4)

    def _score_color_accent_balance(self, profile):
        known_weight = profile["known_weight"]
        if known_weight <= 0:
            return 0.62

        family_shares = sorted(
            (
                weight / known_weight
                for family, weight in profile["family_weights"].items()
                if family != "unknown"
            ),
            reverse=True,
        )
        if profile["neutral_share"] >= 0.65:
            return 0.9

        significant_share_count = len([share for share in family_shares if share >= 0.12])
        if significant_share_count <= 1:
            return 0.88
        if significant_share_count == 2:
            dominant_share, secondary_share = family_shares[:2]
            imbalance = (
                (abs(dominant_share - 0.7) / 0.7)
                + (abs(secondary_share - 0.3) / 0.3)
            ) / 2
            return round(max(0.0, 1.0 - imbalance), 4)
        if significant_share_count == 3:
            dominant_share, secondary_share, accent_share = family_shares[:3]
            imbalance = (
                (abs(dominant_share - 0.5) / 0.5)
                + (abs(secondary_share - 0.3) / 0.3)
                + (abs(accent_share - 0.2) / 0.2)
            ) / 3
            return round(max(0.0, 1.0 - imbalance), 4)

        while len(family_shares) < 3:
            family_shares.append(0.0)

        dominant_share, secondary_share, accent_share = family_shares[:3]
        imbalance = (
            (abs(dominant_share - 0.6) / 0.6)
            + (abs(secondary_share - 0.3) / 0.3)
            + (abs(accent_share - 0.1) / 0.1)
        ) / 3

        if len([share for share in family_shares[:4] if share >= 0.08]) >= 4:
            imbalance += 0.18

        return round(max(0.0, 1.0 - imbalance), 4)

    def _score_preferred_colors_fit(self, profile, request_context):
        preferred_colors = []
        for value in self._split_color_values(request_context.get("preferred_colors")):
            normalized_color = self._normalize_color(value)
            if normalized_color and normalized_color != "unknown" and normalized_color not in preferred_colors:
                preferred_colors.append(normalized_color)

        if not preferred_colors:
            return 0.7

        matched_weight = 0.0
        for preferred_color in preferred_colors:
            family = self._get_color_family(preferred_color)
            if profile["token_weights"].get(preferred_color):
                matched_weight += 1.0
            elif family != "unknown" and profile["family_weights"].get(family):
                matched_weight += 0.82

        coverage = matched_weight / len(preferred_colors)
        score = 0.45 + (coverage * 0.45)
        return round(min(score, 0.92), 4)

    def _family_supported_outside_role(self, profile, role, family):
        supported_weight = 0.0
        for other_role, role_profile in profile["role_profiles"].items():
            if other_role == role:
                continue
            supported_weight += role_profile["family_weights"].get(family, 0.0)
        return supported_weight >= 0.25

    def _score_multicolor_support(self, profile):
        multicolor_profiles = [
            role_profile
            for role_profile in profile["role_profiles"].values()
            if len(role_profile["tokens"]) >= 2
        ]
        if not multicolor_profiles:
            return 0.7

        scores = []
        for role_profile in multicolor_profiles:
            known_families = [
                family
                for family in role_profile["families"]
                if family != "unknown"
            ]
            if not known_families:
                scores.append(0.62)
                continue

            support_hits = sum(
                1
                for family in known_families
                if self._family_supported_outside_role(
                    profile,
                    role_profile["role"],
                    family,
                )
            )
            if support_hits >= 2:
                scores.append(0.92)
            elif support_hits == 1:
                scores.append(0.82)
            else:
                scores.append(0.62)

        return round(sum(scores) / len(scores), 4)

    def _score_shoes_color_fit(self, profile):
        shoes_profile = profile["role_profiles"].get("shoes")
        if not shoes_profile:
            return 0.8
        if shoes_profile["known_weight"] <= 0:
            return 0.78
        if shoes_profile["neutral_share"] >= 0.5 or shoes_profile["metallic_share"] >= 0.5:
            return 0.94

        shoes_families = {
            family for family in shoes_profile["active_families"] if family != "unknown"
        }
        if not shoes_families:
            return 0.82

        repeated_family = any(
            self._family_supported_outside_role(profile, "shoes", family)
            for family in shoes_families
        )
        introduces_new_family = any(
            not self._family_supported_outside_role(profile, "shoes", family)
            for family in shoes_families
        )

        if repeated_family:
            return 0.9
        if profile["neutral_share"] >= 0.45 and len(profile["active_family_weights"]) <= 2:
            return 0.82
        if introduces_new_family and len(profile["active_family_weights"]) >= 4:
            return 0.3
        if introduces_new_family and len(profile["active_family_weights"]) >= 3:
            return 0.48
        return 0.72

    def _score_accessory_color_fit(self, profile):
        accessory_profile = profile["role_profiles"].get("accessory")
        if not accessory_profile:
            return 0.85
        if accessory_profile["known_weight"] <= 0:
            return 0.82
        if accessory_profile["metallic_share"] >= 0.5:
            return 0.96
        if accessory_profile["neutral_share"] >= 0.5:
            return 0.92

        accessory_families = {
            family
            for family in accessory_profile["active_families"]
            if family != "unknown"
        }
        if not accessory_families:
            return 0.86

        repeated_family = any(
            self._family_supported_outside_role(profile, "accessory", family)
            for family in accessory_families
        )
        introduces_new_family = any(
            not self._family_supported_outside_role(profile, "accessory", family)
            for family in accessory_families
        )

        if repeated_family:
            return 0.91
        if profile["neutral_share"] >= 0.45 and len(profile["active_family_weights"]) <= 2:
            return 0.88
        if introduces_new_family and len(profile["active_family_weights"]) >= 4:
            return 0.45
        return 0.75

    def _select_best_color_scheme(self, profile):
        if profile["known_weight"] <= 0:
            return {
                "name": "soft_unknown",
                "score": 0.62,
                "reason": "Цветовая палитра определена частично, но явных конфликтов нет",
                "fragment": "цветовая палитра выглядит достаточно спокойной",
            }

        if not profile["active_family_weights"]:
            score = self._score_neutral_base_scheme(profile)
            return {
                "name": "all_neutral",
                "score": score,
                "reason": "В образе использована спокойная нейтральная палитра",
                "fragment": "палитра построена на нейтральных базовых цветах",
            }

        candidates = [
            {
                "name": "neutral_accent",
                "score": self._score_neutral_base_scheme(profile),
                "reason": "В образе использована нейтральная база и один акцентный цвет",
                "fragment": "нейтральная база поддерживает один акцентный цвет",
            },
            {
                "name": "monochrome",
                "score": self._score_monochrome_scheme(profile),
                "reason": "Цвета собраны по монохромной схеме",
                "fragment": "палитра собрана по монохромной схеме",
            },
            {
                "name": "analogous",
                "score": self._score_analogous_scheme(profile),
                "reason": "Цвета находятся в соседних сегментах цветового круга",
                "fragment": "цвета находятся в соседних сегментах цветового круга",
            },
            {
                "name": "complementary",
                "score": self._score_complementary_scheme(profile),
                "reason": "Контрастный цвет использован как аккуратный акцент",
                "fragment": "контрастный цвет работает как аккуратный акцент",
            },
        ]

        return max(candidates, key=lambda candidate: candidate["score"])

    def _evaluate_color_harmony(self, outfit, request_context):
        profile = self._build_outfit_color_profile(outfit)
        if profile["total_weight"] <= 0:
            return {
                "score": 0.6,
                "reason": "Цветовая палитра определена частично, но явных конфликтов нет",
                "fragment": "цветовая палитра выглядит достаточно спокойной",
                "scheme": "soft_unknown",
                "subscores": {},
            }

        base_palette_score = self._score_neutral_base_scheme(profile)
        scheme = self._select_best_color_scheme(profile)
        complexity_score = self._score_color_complexity(profile)
        accent_balance_score = self._score_color_accent_balance(profile)
        preferred_colors_score = self._score_preferred_colors_fit(
            profile,
            request_context,
        )
        multicolor_support_score = self._score_multicolor_support(profile)
        base_palette_score = min(
            1.0,
            (base_palette_score * 0.82) + (multicolor_support_score * 0.18),
        )
        shoes_score = self._score_shoes_color_fit(profile)
        accessory_score = self._score_accessory_color_fit(profile)
        shoes_accessories_score = round((shoes_score + accessory_score) / 2, 4)

        total_score = (
            (base_palette_score * 0.25)
            + (scheme["score"] * 0.25)
            + (complexity_score * 0.15)
            + (accent_balance_score * 0.15)
            + (preferred_colors_score * 0.1)
            + (shoes_accessories_score * 0.10)
        )

        if profile["known_ratio"] < 0.35:
            total_score = (total_score * 0.5) + 0.62 * 0.5

        reason = scheme["reason"]
        fragment = scheme["fragment"]
        if shoes_accessories_score >= 0.93 and scheme["score"] < 0.9:
            accessory_profile = profile["role_profiles"].get("accessory")
            if accessory_profile and accessory_profile["metallic_share"] >= 0.5:
                reason = "Аксессуар не конфликтует с основными цветами"
                fragment = "аксессуар не конфликтует с основной палитрой"
            else:
                reason = "Обувь поддерживает палитру образа"
                fragment = "обувь поддерживает общую палитру"

        if profile["known_ratio"] < 0.35 and scheme["score"] < 0.75:
            reason = "Цветовая палитра определена частично, но явных конфликтов нет"
            fragment = "цветовая палитра выглядит достаточно спокойной"

        return {
            "score": round(min(max(total_score, 0.0), 1.0), 4),
            "reason": reason,
            "fragment": fragment,
            "scheme": scheme["name"],
            "subscores": {
                "base_palette_score": round(base_palette_score, 4),
                "scheme_score": round(scheme["score"], 4),
                "color_complexity_score": round(complexity_score, 4),
                "accent_balance_score": round(accent_balance_score, 4),
                "preferred_colors_score": round(preferred_colors_score, 4),
                "shoes_accessories_score": round(shoes_accessories_score, 4),
            },
        }

    def _infer_season_from_temperature(self, temperature):
        if temperature is None:
            return None
        if temperature <= 2:
            return "winter"
        if temperature <= 15:
            return "spring"
        return "summer"

    def _estimate_item_warmth(self, item):
        explicit_insulation = getattr(item, "insulation_rating", None)
        if explicit_insulation is not None:
            try:
                explicit_insulation = float(explicit_insulation)
            except (TypeError, ValueError):
                explicit_insulation = None

        base_warmth = {
            "top": 1.2,
            "bottom": 1.3,
            "shoes": 0.8,
            "outerwear": 2.8,
            "accessory": 0.3,
        }.get(item.category, 0.5)

        if explicit_insulation is not None:
            return max(0.1, explicit_insulation)

        item_subcategory = self._normalize_token(item.subcategory)
        item_season = self._normalize_token(item.season)
        if item_season == "winter":
            base_warmth += 1.0
        elif item_season == "autumn":
            base_warmth += 0.5
        elif item_season == "summer":
            base_warmth -= 0.4

        if item.category == "top":
            if item_subcategory in WARM_TOP_TYPES:
                base_warmth += 0.9
            elif item_subcategory in LIGHT_TOP_TYPES:
                base_warmth -= 0.3
        elif item.category == "bottom":
            if item_subcategory in WARM_BOTTOM_TYPES:
                base_warmth += 0.35
            elif item_subcategory in LIGHT_BOTTOM_TYPES:
                base_warmth -= 0.75
        elif item.category == "shoes":
            if item_subcategory in WINTER_SHOE_TYPES:
                base_warmth += 1.2
            elif item_subcategory in {"demi_boots", "ankle_boots", "boots", "closed_shoes"}:
                base_warmth += 0.7
            elif item_subcategory in OPEN_SHOE_TYPES:
                base_warmth -= 0.5
        elif item.category == "outerwear":
            if item_subcategory in HEAVY_OUTERWEAR_TYPES:
                base_warmth += 1.4
            elif item_subcategory in LIGHT_OUTERWEAR_TYPES:
                base_warmth += 0.7

        return max(0.2, base_warmth)

    def _get_item_by_category(self, candidate, category):
        return next((entry["item"] for entry in candidate if entry["item"].category == category), None)

    def _requires_outerwear(self, request_context):
        temperature = request_context.get("temperature")
        weather_condition = self._normalize_token(request_context.get("weather_condition"))

        if weather_condition in {"snow", "rain"}:
            return True
        if temperature is not None and temperature <= 10:
            return True
        if weather_condition == "wind" and (temperature is None or temperature <= 18):
            return True
        return False

    def _score_outerwear_fit(self, candidate, temperature, weather_condition):
        has_outerwear = any(entry["role"] == "outerwear" for entry in candidate)
        outerwear = self._get_item_by_category(candidate, "outerwear")
        normalized_weather = self._normalize_token(weather_condition)
        requires_outerwear = self._requires_outerwear(
            {
                "temperature": temperature,
                "weather_condition": normalized_weather,
            }
        )

        if requires_outerwear:
            if not has_outerwear or outerwear is None:
                return 0.0

            subcategory = self._normalize_token(outerwear.subcategory)
            if normalized_weather == "snow" or (temperature is not None and temperature <= 0):
                return 1.0 if subcategory in HEAVY_OUTERWEAR_TYPES else 0.7
            return 1.0 if subcategory in HEAVY_OUTERWEAR_TYPES | LIGHT_OUTERWEAR_TYPES else 0.75

        if not has_outerwear or outerwear is None:
            return 1.0

        subcategory = self._normalize_token(outerwear.subcategory)
        if temperature is not None and temperature >= 24 and subcategory in HEAVY_OUTERWEAR_TYPES:
            return 0.25
        if temperature is not None and temperature >= 20 and subcategory in LIGHT_OUTERWEAR_TYPES:
            return 0.7
        return 0.85

    def _score_shoe_temperature_fit(self, shoes, temperature):
        if shoes is None or temperature is None:
            return 0.7

        subcategory = self._normalize_token(shoes.subcategory)
        season = self._normalize_token(shoes.season)

        if temperature <= -5:
            if subcategory in WINTER_SHOE_TYPES:
                return 1.0
            if subcategory in {"demi_boots", "ankle_boots", "boots"} or season == "winter":
                return 0.65
            return 0.05

        if temperature <= 10:
            if subcategory in {"demi_boots", "ankle_boots", "boots", "closed_shoes", "sneakers"}:
                return 1.0
            if subcategory in WINTER_SHOE_TYPES or subcategory in {"loafers", "pumps"}:
                return 0.6
            return 0.15

        if temperature <= 20:
            if subcategory in MID_SHOE_TYPES | {"sandals", "espadrilles"}:
                return 1.0
            return 0.3

        if subcategory in HOT_SHOE_TYPES:
            return 1.0
        if subcategory in {"pumps", "closed_shoes"}:
            return 0.55
        return 0.15

    def _score_shoe_weather_fit(self, shoes, weather_condition, temperature):
        if shoes is None:
            return 0.4 if weather_condition in {"snow", "rain"} else 0.7

        normalized_weather = {"clear": "sunny"}.get(
            self._normalize_token(weather_condition),
            self._normalize_token(weather_condition),
        )
        if not normalized_weather:
            return 0.7

        subcategory = self._normalize_token(shoes.subcategory)

        if normalized_weather == "snow":
            if subcategory in WINTER_SHOE_TYPES:
                return 1.0
            if subcategory in SNOW_SAFE_SHOE_TYPES and (temperature is None or temperature <= 2):
                return 0.75
            return 0.0

        if normalized_weather == "rain":
            if subcategory in RAIN_SAFE_SHOE_TYPES:
                return 1.0
            if subcategory in {"loafers", "pumps"}:
                return 0.35
            return 0.1

        if normalized_weather == "wind":
            return 0.45 if subcategory in OPEN_SHOE_TYPES else 0.9

        if normalized_weather == "cloudy":
            if subcategory in OPEN_SHOE_TYPES and temperature is not None and temperature < 15:
                return 0.45
            return 0.9

        if normalized_weather == "sunny":
            if temperature is not None and temperature >= 22:
                if subcategory in HOT_SHOE_TYPES:
                    return 1.0
                if subcategory in {"sneakers", "loafers"}:
                    return 0.75
                return 0.4
            return 0.9 if subcategory not in WINTER_SHOE_TYPES else 0.5

        return 0.75

    def _score_bottom_weather_fit(self, bottom, weather_condition, temperature):
        if bottom is None:
            return 0.7

        subcategory = self._normalize_token(bottom.subcategory)
        normalized_weather = self._normalize_token(weather_condition)

        if temperature is not None and temperature <= 0 and subcategory in {"shorts", "mini_skirt"}:
            return 0.0
        if temperature is not None and temperature <= 10 and subcategory == "shorts":
            return 0.15
        if normalized_weather in {"snow", "rain"} and subcategory in {"shorts", "mini_skirt"}:
            return 0.25
        if temperature is not None and temperature >= 24 and subcategory in {"jeans", "joggers", "leggings"}:
            return 0.65

        return 1.0

    def _violates_hard_constraints(self, candidate, constraints):
        for constraint in constraints:
            if self._candidate_violates_constraint(candidate, constraint):
                return True
        return False

    def _candidate_violates_constraint(self, candidate, constraint):
        normalized_constraint = self._normalize_token(constraint)
        if not normalized_constraint:
            return False

        for entry in candidate:
            item = entry["item"]
            category = self._normalize_token(item.category)
            subcategory = self._normalize_token(item.subcategory)
            colors = set(self._normalize_tokens(item.colors or []))
            attributes = {
                category,
                subcategory,
                self._normalize_token(item.material),
                self._normalize_token(item.formality),
                self._normalize_token(getattr(item, "fit", None)),
                self._normalize_token(getattr(item, "layer_level", None)),
                "waterproof" if getattr(item, "waterproof", False) else None,
                "windproof" if getattr(item, "windproof", False) else None,
                *colors,
                *self._normalize_tokens(item.styles or []),
            }
            attributes.discard(None)

            if normalized_constraint in {"no_heels", "avoid_heels"}:
                if category == "shoes" and subcategory in {"heels", "high_heels", "pumps"}:
                    return True
            elif normalized_constraint in {"no_skirts", "avoid_skirts"}:
                if category == "bottom" and subcategory == "skirt":
                    return True
            elif normalized_constraint == "no_bright_colors":
                if colors & BRIGHT_COLORS:
                    return True
            elif normalized_constraint == "no_outerwear":
                if category == "outerwear":
                    return True
            elif normalized_constraint.startswith("no_"):
                if normalized_constraint[3:] in attributes:
                    return True
            elif normalized_constraint.startswith("avoid_"):
                if normalized_constraint[6:] in attributes:
                    return True
            elif normalized_constraint in attributes:
                return True

        return False

    def _candidate_has_attribute(self, candidate, attribute):
        normalized_attribute = self._normalize_token(attribute)
        for entry in candidate:
            item = entry["item"]
            tokens = {
                self._normalize_token(item.category),
                self._normalize_token(item.subcategory),
                self._normalize_token(item.material),
                self._normalize_token(item.formality),
                self._normalize_token(getattr(item, "fit", None)),
                self._normalize_token(getattr(item, "layer_level", None)),
                "waterproof" if getattr(item, "waterproof", False) else None,
                "windproof" if getattr(item, "windproof", False) else None,
                *self._normalize_tokens(item.colors or []),
                *self._normalize_tokens(item.styles or []),
            }
            tokens.discard(None)
            if normalized_attribute in tokens:
                return True
        return False
