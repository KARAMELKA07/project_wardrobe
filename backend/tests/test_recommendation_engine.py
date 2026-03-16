import unittest
from dataclasses import dataclass
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.recommendation_engine import RecommendationEngine


@dataclass
class DummyItem:
    id: int
    title: str
    category: str
    subcategory: str
    colors: list
    styles: list
    season: str
    formality: str
    material: str
    image_url: str = "/uploads/placeholders/top.svg"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "subcategory": self.subcategory,
            "colors": self.colors,
            "styles": self.styles,
            "season": self.season,
            "formality": self.formality,
            "material": self.material,
            "image_url": self.image_url,
        }


def build_item(item_id, title, category, subcategory, colors, styles, season, formality):
    return DummyItem(
        id=item_id,
        title=title,
        category=category,
        subcategory=subcategory,
        colors=colors,
        styles=styles,
        season=season,
        formality=formality,
        material="cotton",
        image_url=f"/uploads/placeholders/{category}.svg",
    )


class RecommendationEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RecommendationEngine()
        self.request_context = {
            "event_type": "casual",
            "preferred_colors": ["white", "black", "beige"],
            "preferred_style": "minimal",
            "temperature": 12,
            "weather_condition": "cloudy",
            "anchor_item_id": None,
            "constraints": [],
            "season": "spring",
            "city": "Moscow",
        }

    def make_candidate(self, *entries):
        return [{"role": role, "item": item} for role, item in entries]

    def get_color_score(self, candidate, preferred_colors=None):
        request_context = {
            **self.request_context,
            "preferred_colors": preferred_colors
            if preferred_colors is not None
            else self.request_context["preferred_colors"],
        }
        return self.engine.score_color_harmony(candidate, request_context)

    def test_generate_candidate_outfits_builds_base_and_outerwear_variants(self):
        items = [
            build_item(1, "White tee", "top", "t-shirt", ["white"], ["casual"], "summer", "casual"),
            build_item(2, "Beige shirt", "top", "shirt", ["beige"], ["minimal"], "spring", "smart"),
            build_item(3, "Black jeans", "bottom", "jeans", ["black"], ["casual"], "all-season", "casual"),
            build_item(4, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual"),
            build_item(5, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart"),
        ]

        candidates = self.engine.generate_candidate_outfits(items, self.request_context)

        self.assertEqual(len(candidates), 4)
        self.assertTrue(any(len(candidate) == 3 for candidate in candidates))
        self.assertTrue(any(len(candidate) == 4 for candidate in candidates))

    def test_generate_returns_empty_when_required_categories_missing(self):
        items = [
            build_item(1, "White tee", "top", "t-shirt", ["white"], ["casual"], "summer", "casual"),
            build_item(2, "Black jeans", "bottom", "jeans", ["black"], ["casual"], "all-season", "casual"),
        ]

        results = self.engine.generate(items, self.request_context)

        self.assertEqual(results, [])

    def test_generate_returns_only_top_five_ranked_outfits(self):
        items = [
            build_item(1, "White tee", "top", "t-shirt", ["white"], ["casual"], "summer", "casual"),
            build_item(2, "Black tee", "top", "t-shirt", ["black"], ["casual"], "summer", "casual"),
            build_item(3, "Beige shirt", "top", "shirt", ["beige"], ["minimal"], "spring", "smart"),
            build_item(4, "Black jeans", "bottom", "jeans", ["black"], ["casual"], "all-season", "casual"),
            build_item(5, "Beige trousers", "bottom", "trousers", ["beige"], ["minimal"], "spring", "smart"),
            build_item(6, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual"),
            build_item(7, "Black boots", "shoes", "boots", ["black"], ["classic"], "autumn", "smart"),
            build_item(8, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart"),
            build_item(9, "Black coat", "outerwear", "coat", ["black"], ["minimal"], "winter", "formal"),
        ]

        results = self.engine.generate(items, self.request_context, limit=5)

        self.assertEqual(len(results), 5)
        self.assertGreaterEqual(results[0]["score"], results[-1]["score"])
        self.assertTrue(all("items" in outfit for outfit in results))

    def test_evaluate_outfit_returns_feature_scores_and_explanation(self):
        candidate = [
            {"role": "top", "item": build_item(1, "White tee", "top", "t-shirt", ["white"], ["minimal"], "summer", "casual")},
            {"role": "bottom", "item": build_item(2, "Black jeans", "bottom", "jeans", ["black"], ["casual"], "all-season", "casual")},
            {"role": "shoes", "item": build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual")},
            {"role": "outerwear", "item": build_item(4, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart")},
        ]

        outfit = self.engine.evaluate_outfit(candidate, self.request_context, {})

        self.assertEqual(len(outfit["feature_scores"]), 10)
        self.assertIn("reasons", outfit)
        self.assertIn("explanation", outfit)
        self.assertGreaterEqual(outfit["score"], 0.0)
        self.assertLessEqual(outfit["score"], 1.0)

    def test_generate_candidate_outfits_excludes_loafers_in_snow(self):
        cold_request_context = {
            **self.request_context,
            "temperature": -12,
            "weather_condition": "snow",
            "season": "winter",
        }
        items = [
            build_item(1, "Warm sweater", "top", "sweater", ["gray"], ["casual"], "winter", "casual"),
            build_item(2, "Blue jeans", "bottom", "jeans", ["blue"], ["casual"], "winter", "casual"),
            build_item(3, "Beige loafers", "shoes", "loafers", ["beige"], ["classic"], "spring", "smart"),
            build_item(4, "Black winter boots", "shoes", "winter_boots", ["black"], ["casual"], "winter", "casual"),
            build_item(5, "Black coat", "outerwear", "coat", ["black"], ["classic"], "winter", "formal"),
        ]

        candidates = self.engine.generate_candidate_outfits(items, cold_request_context)

        self.assertTrue(candidates)
        for candidate in candidates:
            shoes = next(entry["item"] for entry in candidate if entry["role"] == "shoes")
            roles = {entry["role"] for entry in candidate}
            self.assertNotEqual(shoes.subcategory, "loafers")
            self.assertIn("outerwear", roles)

    def test_color_harmony_scores_all_neutral_outfit_high(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "White shirt", "top", "shirt", ["white"], ["minimal"], "spring", "smart")),
            ("bottom", build_item(2, "Black trousers", "bottom", "trousers", ["black"], ["minimal"], "spring", "smart")),
            ("shoes", build_item(3, "Beige loafers", "shoes", "loafers", ["beige"], ["classic"], "spring", "smart")),
            ("outerwear", build_item(4, "Gray blazer", "outerwear", "blazer", ["gray"], ["classic"], "spring", "smart")),
        )

        score = self.get_color_score(candidate, preferred_colors=["white", "black", "beige"])

        self.assertGreaterEqual(score, 0.84)

    def test_color_harmony_scores_neutral_base_with_one_accent_high(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Red knit", "top", "sweater", ["red"], ["minimal"], "autumn", "smart")),
            ("bottom", build_item(2, "Black trousers", "bottom", "trousers", ["black"], ["minimal"], "autumn", "smart")),
            ("shoes", build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["minimal"], "spring", "casual")),
            ("outerwear", build_item(4, "Beige coat", "outerwear", "coat", ["beige"], ["classic"], "autumn", "smart")),
        )

        score = self.get_color_score(candidate)

        self.assertGreaterEqual(score, 0.82)

    def test_color_harmony_scores_monochrome_blue_outfit_high(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Blue shirt", "top", "shirt", ["blue"], ["classic"], "spring", "smart")),
            ("bottom", build_item(2, "Navy trousers", "bottom", "trousers", ["navy"], ["classic"], "spring", "smart")),
            ("shoes", build_item(3, "Denim sneakers", "shoes", "sneakers", ["denim"], ["casual"], "spring", "casual")),
        )

        score = self.get_color_score(candidate, preferred_colors=["blue", "navy"])

        self.assertGreaterEqual(score, 0.83)

    def test_color_harmony_scores_analogous_palette_high(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Blue top", "top", "shirt", ["blue"], ["casual"], "spring", "casual")),
            ("bottom", build_item(2, "Teal skirt", "bottom", "skirt", ["teal"], ["casual"], "spring", "casual")),
            ("shoes", build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual")),
            ("accessory", build_item(4, "Green bag", "accessory", "bag", ["green"], ["casual"], "spring", "casual")),
        )

        score = self.get_color_score(candidate, preferred_colors=["blue", "teal"])

        self.assertGreaterEqual(score, 0.77)

    def test_color_harmony_scores_complementary_with_soft_accent_well(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Blue shirt", "top", "shirt", ["blue"], ["classic"], "spring", "smart")),
            ("bottom", build_item(2, "White trousers", "bottom", "trousers", ["white"], ["classic"], "spring", "smart")),
            ("shoes", build_item(3, "White sneakers", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual")),
            ("accessory", build_item(4, "Orange bag", "accessory", "bag", ["orange"], ["fashion"], "spring", "smart")),
        )

        score = self.get_color_score(candidate, preferred_colors=["blue", "orange"])

        self.assertGreaterEqual(score, 0.74)

    def test_color_harmony_penalizes_too_many_unrelated_bright_colors(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Red top", "top", "shirt", ["red"], ["fashion"], "spring", "smart")),
            ("bottom", build_item(2, "Green skirt", "bottom", "skirt", ["green"], ["fashion"], "spring", "smart")),
            ("shoes", build_item(3, "Yellow shoes", "shoes", "pumps", ["yellow"], ["fashion"], "spring", "smart")),
            ("outerwear", build_item(4, "Purple jacket", "outerwear", "jacket", ["purple"], ["fashion"], "spring", "smart")),
            ("accessory", build_item(5, "Teal bag", "accessory", "bag", ["teal"], ["fashion"], "spring", "smart")),
        )

        score = self.get_color_score(candidate, preferred_colors=[])

        self.assertLess(score, 0.55)

    def test_color_harmony_handles_neutral_shoes_and_metallic_accessory(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Cream knit", "top", "sweater", ["cream"], ["minimal"], "autumn", "smart")),
            ("bottom", build_item(2, "Taupe trousers", "bottom", "trousers", ["taupe"], ["minimal"], "autumn", "smart")),
            ("shoes", build_item(3, "Black boots", "shoes", "boots", ["black"], ["classic"], "autumn", "smart")),
            ("accessory", build_item(4, "Silver bag", "accessory", "bag", ["silver"], ["classic"], "autumn", "smart")),
        )

        score = self.get_color_score(candidate, preferred_colors=["cream", "taupe", "black"])

        self.assertGreaterEqual(score, 0.82)

    def test_preferred_colors_help_but_do_not_hide_bad_harmony(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Red top", "top", "shirt", ["red"], ["fashion"], "spring", "smart")),
            ("bottom", build_item(2, "Green skirt", "bottom", "skirt", ["green"], ["fashion"], "spring", "smart")),
            ("shoes", build_item(3, "Yellow shoes", "shoes", "pumps", ["yellow"], ["fashion"], "spring", "smart")),
            ("outerwear", build_item(4, "Purple jacket", "outerwear", "jacket", ["purple"], ["fashion"], "spring", "smart")),
        )

        base_score = self.get_color_score(candidate, preferred_colors=[])
        preferred_score = self.get_color_score(
            candidate,
            preferred_colors=["red", "green", "yellow", "purple"],
        )

        self.assertGreater(preferred_score, base_score)
        self.assertLess(preferred_score, 0.8)

    def test_color_harmony_handles_unknown_colors_without_crashing(self):
        candidate = self.make_candidate(
            ("top", build_item(1, "Mystic top", "top", "shirt", ["mystic haze"], ["casual"], "spring", "casual")),
            ("bottom", build_item(2, "Dusty bottom", "bottom", "trousers", ["dust storm"], ["casual"], "spring", "casual")),
            ("shoes", build_item(3, "White shoes", "shoes", "sneakers", ["white"], ["casual"], "spring", "casual")),
        )

        score = self.get_color_score(candidate, preferred_colors=["white"])

        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
