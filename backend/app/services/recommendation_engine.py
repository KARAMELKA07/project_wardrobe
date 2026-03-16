from collections import Counter
from itertools import product


FEATURE_WEIGHTS = {
    "color_harmony": 0.14,
    "style_match": 0.13,
    "event_match": 0.13,
    "season_match": 0.1,
    "temperature_match": 0.1,
    "weather_condition_match": 0.1,
    "completeness": 0.1,
    "layering_correctness": 0.08,
    "user_preference_match": 0.07,
    "constraints_match": 0.05,
}

ROLE_ORDER = {
    "top": 0,
    "bottom": 1,
    "shoes": 2,
    "outerwear": 3,
    "accessory": 4,
}

NEUTRAL_COLORS = {"black", "white", "gray", "grey", "beige", "brown", "navy"}
WARM_COLORS = {"red", "orange", "yellow", "burgundy", "camel"}
COOL_COLORS = {"blue", "green", "teal", "purple", "mint"}
BRIGHT_COLORS = {"red", "yellow", "orange", "lime", "fuchsia", "pink"}
EVENT_LABELS = {
    "office": "офис",
    "casual": "повседневный выход",
    "evening": "вечерний выход",
    "sport": "спорт",
    "party": "вечеринка",
    "travel": "поездка",
    "date": "свидание",
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

        if not tops or not bottoms or not shoes:
            return []

        accessory_anchor = (
            anchor_item if anchor_item and anchor_item.category == "accessory" else None
        )
        constraints = self._normalize_tokens(request_context.get("constraints"))
        candidates = []

        for top_item, bottom_item, shoes_item in product(tops[:20], bottoms[:20], shoes[:20]):
            base_candidate = [
                self._make_candidate_entry("top", top_item),
                self._make_candidate_entry("bottom", bottom_item),
                self._make_candidate_entry("shoes", shoes_item),
            ]
            if accessory_anchor:
                base_candidate.append(
                    self._make_candidate_entry("accessory", accessory_anchor)
                )

            if (
                not anchor_item or anchor_item.category != "outerwear"
            ) and self._is_valid_candidate(base_candidate, constraints):
                candidates.append(base_candidate)

            for outerwear_item in outerwear[:20]:
                if outerwear_item is None:
                    continue
                layered_candidate = list(base_candidate) + [
                    self._make_candidate_entry("outerwear", outerwear_item)
                ]
                if self._is_valid_candidate(layered_candidate, constraints):
                    candidates.append(layered_candidate)

        return self._deduplicate_candidates(candidates)

    def evaluate_outfit(self, candidate, request_context, user_preferences=None):
        feature_scores = self.get_feature_scores(
            candidate,
            request_context,
            user_preferences or {},
        )
        total_score = self.calculate_total_score(feature_scores)
        reasons, explanation = self.build_outfit_explanation(
            feature_scores,
            request_context,
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
            "reasons": reasons,
            "explanation": explanation,
        }

    def get_feature_scores(self, candidate, request_context, user_preferences=None):
        items = [entry["item"] for entry in candidate]
        user_preferences = user_preferences or {}

        return {
            "color_harmony": self.score_color_harmony(items, request_context),
            "style_match": self.score_style_match(items, request_context),
            "event_match": self.score_event_match(items, request_context),
            "season_match": self.score_season_match(items, request_context),
            "temperature_match": self.score_temperature_match(candidate, request_context),
            "weather_condition_match": self.score_weather_condition_match(
                candidate,
                request_context,
            ),
            "completeness": self.score_completeness(candidate),
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

    def calculate_total_score(self, feature_scores):
        total_score = 0.0
        for feature_name, weight in self.weights.items():
            total_score += feature_scores.get(feature_name, 0.0) * weight
        return round(min(max(total_score, 0.0), 1.0), 4)

    def build_outfit_explanation(self, feature_scores, request_context):
        event_label = EVENT_LABELS.get(
            self._normalize_token(request_context.get("event_type")),
            "выбранного события",
        )
        reason_templates = {
            "color_harmony": (
                "Цвета вещей хорошо сочетаются между собой",
                "цвета выглядят согласованно",
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

    def score_color_harmony(self, items, request_context):
        colors = [
            self._normalize_color(color)
            for item in items
            for color in (item.colors or [])
        ]
        colors = [color for color in colors if color]
        if not colors:
            return 0.6

        unique_colors = list(dict.fromkeys(colors))
        pair_scores = []
        for index, left_color in enumerate(unique_colors):
            for right_color in unique_colors[index + 1 :]:
                pair_scores.append(self._score_color_pair(left_color, right_color))

        base_score = sum(pair_scores) / len(pair_scores) if pair_scores else 0.85
        preferred_colors = set(
            self._normalize_tokens(request_context.get("preferred_colors"))
        )
        preferred_match = 0.7
        if preferred_colors:
            matched_colors = sum(1 for color in unique_colors if color in preferred_colors)
            preferred_match = matched_colors / len(unique_colors)

        has_neutral = any(color in NEUTRAL_COLORS for color in unique_colors)
        neutral_bonus = 1.0 if has_neutral else 0.65
        return round(
            min(
                1.0,
                (base_score * 0.55) + (preferred_match * 0.25) + (neutral_bonus * 0.2),
            ),
            4,
        )

    def score_style_match(self, items, request_context):
        item_styles = []
        for item in items:
            normalized_styles = self._normalize_tokens(item.styles or [])
            if normalized_styles:
                item_styles.append(set(normalized_styles))

        if not item_styles:
            return 0.6

        style_counter = Counter(style for styles in item_styles for style in styles)
        dominant_ratio = style_counter.most_common(1)[0][1] / len(items)
        preferred_style = self._normalize_token(request_context.get("preferred_style"))
        preferred_bonus = 0.7
        if preferred_style:
            preferred_bonus = (
                sum(1 for styles in item_styles if preferred_style in styles)
                / len(item_styles)
            )

        return round(min(1.0, (dominant_ratio * 0.7) + (preferred_bonus * 0.3)), 4)

    def score_event_match(self, items, request_context):
        event_type = self._normalize_token(request_context.get("event_type")) or "casual"
        event_rule = EVENT_RULES.get(event_type, EVENT_RULES["casual"])

        style_scores = []
        formality_scores = []
        for item in items:
            styles = set(self._normalize_tokens(item.styles or []))
            style_scores.append(1.0 if styles & event_rule["styles"] else 0.55)

            item_formality = self._normalize_token(item.formality)
            if item_formality in event_rule["formalities"]:
                formality_scores.append(1.0)
            elif item_formality == "casual" and "smart" in event_rule["formalities"]:
                formality_scores.append(0.7)
            else:
                formality_scores.append(0.45)

        total = (sum(style_scores) + sum(formality_scores)) / (2 * len(items))
        return round(total, 4)

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

        if target_season:
            target_matches = [
                1.0 if season in {target_season, "all_season"} else 0.4
                for season in item_seasons
            ]
            target_score = sum(target_matches) / len(target_matches)
        else:
            target_score = 0.75

        filtered_seasons = [season for season in item_seasons if season != "all_season"]
        if filtered_seasons:
            internal_consistency = (
                Counter(filtered_seasons).most_common(1)[0][1] / len(filtered_seasons)
            )
        else:
            internal_consistency = 1.0

        return round((target_score * 0.65) + (internal_consistency * 0.35), 4)

    def score_temperature_match(self, candidate, request_context):
        temperature = request_context.get("temperature")
        if temperature is None:
            return 0.7

        items = [entry["item"] for entry in candidate]
        warmth_level = sum(self._estimate_item_warmth(item) for item in items)
        has_outerwear = any(entry["role"] == "outerwear" for entry in candidate)

        if temperature <= 0:
            ideal_warmth = 8.5
            if not has_outerwear:
                warmth_level -= 1.2
        elif temperature <= 10:
            ideal_warmth = 6.2
            if not has_outerwear:
                warmth_level -= 0.7
        elif temperature <= 20:
            ideal_warmth = 4.5
        else:
            ideal_warmth = 3.0
            if has_outerwear:
                warmth_level += 1.0

        distance = abs(warmth_level - ideal_warmth)
        return round(max(0.0, 1 - (distance / 6.5)), 4)

    def score_weather_condition_match(self, candidate, request_context):
        weather_condition = self._normalize_token(request_context.get("weather_condition"))
        if not weather_condition:
            return 0.7

        normalized_weather = {"clear": "sunny"}.get(weather_condition, weather_condition)
        items = [entry["item"] for entry in candidate]
        has_outerwear = any(entry["role"] == "outerwear" for entry in candidate)
        shoes = next((item for item in items if item.category == "shoes"), None)
        open_shoes = False
        if shoes and shoes.subcategory:
            normalized_subcategory = self._normalize_token(shoes.subcategory)
            open_shoes = normalized_subcategory in {
                "sandals",
                "flip_flops",
                "slippers",
            }

        if normalized_weather == "sunny":
            return 0.65 if has_outerwear else 0.95
        if normalized_weather == "cloudy":
            return 0.9
        if normalized_weather == "rain":
            if has_outerwear and not open_shoes:
                return 1.0
            if has_outerwear or not open_shoes:
                return 0.7
            return 0.35
        if normalized_weather == "snow":
            return 1.0 if has_outerwear and not open_shoes else 0.35
        if normalized_weather == "wind":
            return 0.95 if has_outerwear else 0.65

        return 0.75

    def score_completeness(self, candidate):
        roles = {entry["role"] for entry in candidate}
        required_roles = {"top", "bottom", "shoes"}
        matched_roles = len(roles & required_roles)
        return round(matched_roles / len(required_roles), 4)

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
        if temperature is not None and temperature >= 24 and has_outerwear:
            return 0.7
        if weather_condition in {"rain", "snow", "wind"} and not has_outerwear:
            return 0.7

        return 1.0

    def score_user_preference_match(self, candidate, request_context, user_preferences):
        items = [entry["item"] for entry in candidate]
        preferred_colors = set(
            self._normalize_tokens(user_preferences.get("preferred_colors"))
        )
        preferred_colors |= set(
            self._normalize_tokens(request_context.get("preferred_colors"))
        )

        preferred_styles = set(
            self._normalize_tokens(user_preferences.get("preferred_styles"))
        )
        request_style = self._normalize_token(request_context.get("preferred_style"))
        if request_style:
            preferred_styles.add(request_style)

        colors_score = 0.75
        if preferred_colors:
            color_hits = 0
            for item in items:
                item_colors = set(self._normalize_tokens(item.colors or []))
                if item_colors & preferred_colors:
                    color_hits += 1
            colors_score = color_hits / len(items)

        styles_score = 0.75
        if preferred_styles:
            style_hits = 0
            for item in items:
                item_styles = set(self._normalize_tokens(item.styles or []))
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
            (colors_score * 0.4) + (styles_score * 0.4) + (constraint_alignment * 0.2),
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

    def _is_valid_candidate(self, candidate, constraints):
        item_ids = [entry["item"].id for entry in candidate if entry.get("item")]
        if len(item_ids) != len(set(item_ids)):
            return False

        roles = {entry["role"] for entry in candidate}
        if not {"top", "bottom", "shoes"}.issubset(roles):
            return False

        if self._violates_hard_constraints(candidate, constraints):
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
        return self._normalize_token(value)

    def _score_color_pair(self, left_color, right_color):
        if left_color == right_color:
            return 0.95
        if left_color in NEUTRAL_COLORS or right_color in NEUTRAL_COLORS:
            return 0.9
        if (
            left_color in WARM_COLORS and right_color in WARM_COLORS
        ) or (
            left_color in COOL_COLORS and right_color in COOL_COLORS
        ):
            return 0.8
        return 0.6

    def _infer_season_from_temperature(self, temperature):
        if temperature is None:
            return None
        if temperature <= 5:
            return "winter"
        if temperature <= 17:
            return "spring"
        return "summer"

    def _estimate_item_warmth(self, item):
        base_warmth = {
            "top": 1.2,
            "bottom": 1.3,
            "shoes": 0.8,
            "outerwear": 2.8,
            "accessory": 0.3,
        }.get(item.category, 0.5)

        item_season = self._normalize_token(item.season)
        if item_season == "winter":
            base_warmth += 1.0
        elif item_season == "autumn":
            base_warmth += 0.5
        elif item_season == "summer":
            base_warmth -= 0.4

        material = self._normalize_token(item.material)
        if material in {"wool", "cashmere", "fleece", "denim"}:
            base_warmth += 0.4

        return max(0.2, base_warmth)

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
                *colors,
                *self._normalize_tokens(item.styles or []),
            }

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
                *self._normalize_tokens(item.colors or []),
                *self._normalize_tokens(item.styles or []),
            }
            if normalized_attribute in tokens:
                return True
        return False
