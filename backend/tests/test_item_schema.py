import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas.item import validate_clothing_item_payload


class ClothingItemSchemaTests(unittest.TestCase):
    def test_accessory_metadata_is_sanitized(self):
        payload = {
            "title": "Leather belt",
            "category": "accessory",
            "subcategory": "belt",
            "colors": '["brown"]',
            "styles": '["classic"]',
            "season": "all-season",
            "formality": "smart",
            "fit": "fitted",
            "layer_level": "support",
            "insulation_rating": "1.4",
            "waterproof": "true",
            "windproof": "true",
        }

        cleaned = validate_clothing_item_payload(payload)

        self.assertIsNone(cleaned["fit"])
        self.assertIsNone(cleaned["layer_level"])
        self.assertEqual(cleaned["insulation_rating"], 0.0)
        self.assertFalse(cleaned["waterproof"])
        self.assertFalse(cleaned["windproof"])

    def test_shoes_keep_only_relevant_metadata(self):
        payload = {
            "title": "Rain boots",
            "category": "shoes",
            "subcategory": "boots",
            "colors": '["black"]',
            "styles": '["casual"]',
            "season": "autumn",
            "formality": "casual",
            "fit": "balanced",
            "layer_level": "outer",
            "insulation_rating": "1.5",
            "waterproof": "true",
            "windproof": "true",
        }

        cleaned = validate_clothing_item_payload(payload)

        self.assertIsNone(cleaned["fit"])
        self.assertIsNone(cleaned["layer_level"])
        self.assertEqual(cleaned["insulation_rating"], 1.5)
        self.assertTrue(cleaned["waterproof"])
        self.assertFalse(cleaned["windproof"])

    def test_bottom_does_not_keep_layer_level(self):
        payload = {
            "title": "Black jeans",
            "category": "bottom",
            "subcategory": "jeans",
            "colors": '["black"]',
            "styles": '["casual"]',
            "season": "all-season",
            "formality": "casual",
            "fit": "balanced",
            "layer_level": "base",
            "insulation_rating": "1.0",
            "waterproof": "true",
            "windproof": "true",
        }

        cleaned = validate_clothing_item_payload(payload)

        self.assertEqual(cleaned["fit"], "balanced")
        self.assertIsNone(cleaned["layer_level"])
        self.assertEqual(cleaned["insulation_rating"], 1.0)
        self.assertFalse(cleaned["waterproof"])
        self.assertFalse(cleaned["windproof"])


if __name__ == "__main__":
    unittest.main()
