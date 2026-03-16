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


if __name__ == "__main__":
    unittest.main()
