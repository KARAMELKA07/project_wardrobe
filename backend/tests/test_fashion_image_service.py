import unittest
from io import BytesIO
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.fashion_image_service import FashionImageService


try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


class FakeClassifier:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def predict(self, image_bytes):
        self.calls += 1
        return dict(self.result)


@unittest.skipIf(Image is None, "Pillow не установлена")
class FashionImageServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = FashionImageService()

    def make_test_image(self):
        image = Image.new("RGBA", (120, 120), (255, 255, 255, 0))
        for x in range(0, 80):
            for y in range(0, 120):
                image.putpixel((x, y), (15, 15, 15, 255))

        for x in range(80, 120):
            for y in range(0, 120):
                image.putpixel((x, y), (244, 242, 235, 255))

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_extract_palette_colors_returns_ranked_basic_colors(self):
        colors = self.service._extract_palette_colors(self.make_test_image())

        self.assertTrue(colors)
        self.assertEqual(colors[0], "black")
        self.assertIn("white", colors)

    def test_build_attribute_suggestions_maps_subcategory_to_expected_fields(self):
        result = self.service._build_attribute_suggestions(
            "down_jacket",
            ["black"],
        )

        self.assertEqual(result["category"], "outerwear")
        self.assertEqual(result["subcategory"], "down_jacket")
        self.assertEqual(result["season"], "winter")
        self.assertTrue(result["waterproof"])
        self.assertTrue(result["windproof"])
        self.assertGreater(result["insulation_rating"], 2.0)

    def test_build_attribute_suggestions_for_unknown_subcategory_is_safe(self):
        result = self.service._build_attribute_suggestions(None, [])

        self.assertIsNone(result["category"])
        self.assertEqual(result["season"], "all-season")
        self.assertEqual(result["formality"], "casual")

    def test_fpid_shoe_prediction_is_refined_by_zappos(self):
        self.service._local_classifier = FakeClassifier(
            {
                "subcategory": "sneakers",
                "confidence": 0.91,
                "top_predictions": [{"subcategory": "sneakers", "score": 0.91}],
                "warnings": [],
                "model": "fpid-local:efficientnet_b0",
                "source_dataset": "Fashion Product Images",
            }
        )
        self.service._shoe_classifier = FakeClassifier(
            {
                "subcategory": "boots",
                "confidence": 0.82,
                "top_predictions": [{"subcategory": "boots", "score": 0.82}],
                "warnings": [],
                "model": "zappos-local:efficientnet_b0",
                "source_dataset": "Wardrobe manifest classifier (Zappos)",
            }
        )

        result = self.service._classify_image(b"image-bytes")

        self.assertEqual(result["subcategory"], "boots")
        self.assertEqual(result["model"], "zappos-local:efficientnet_b0")
        self.assertEqual(result["classification_route"], "fpid_to_zappos_shoes")
        self.assertEqual(result["base_model"], "fpid-local:efficientnet_b0")
        self.assertEqual(result["base_subcategory"], "sneakers")
        self.assertEqual(self.service._shoe_classifier.calls, 1)

    def test_fpid_non_shoe_prediction_does_not_call_zappos(self):
        self.service._local_classifier = FakeClassifier(
            {
                "subcategory": "t_shirt",
                "confidence": 0.93,
                "top_predictions": [{"subcategory": "t_shirt", "score": 0.93}],
                "warnings": [],
                "model": "fpid-local:efficientnet_b0",
                "source_dataset": "Fashion Product Images",
            }
        )
        self.service._shoe_classifier = FakeClassifier(
            {
                "subcategory": "boots",
                "confidence": 0.82,
                "top_predictions": [{"subcategory": "boots", "score": 0.82}],
                "warnings": [],
                "model": "zappos-local:efficientnet_b0",
                "source_dataset": "Wardrobe manifest classifier (Zappos)",
            }
        )

        result = self.service._classify_image(b"image-bytes")

        self.assertEqual(result["subcategory"], "t_shirt")
        self.assertEqual(result["model"], "fpid-local:efficientnet_b0")
        self.assertEqual(result["classification_route"], "fpid")
        self.assertEqual(self.service._shoe_classifier.calls, 0)

    def test_suspect_horizontal_accessory_prediction_can_fallback_to_zappos(self):
        self.service._local_classifier = FakeClassifier(
            {
                "subcategory": "necklace",
                "confidence": 0.94,
                "top_predictions": [{"subcategory": "necklace", "score": 0.94}],
                "warnings": [],
                "model": "fpid-local:efficientnet_b0",
                "source_dataset": "Fashion Product Images",
            }
        )
        self.service._shoe_classifier = FakeClassifier(
            {
                "subcategory": "pumps",
                "confidence": 0.88,
                "top_predictions": [{"subcategory": "pumps", "score": 0.88}],
                "warnings": [],
                "model": "zappos-local:efficientnet_b0",
                "source_dataset": "Wardrobe manifest classifier (Zappos)",
            }
        )
        self.service._looks_like_horizontal_shoe_object = lambda _image_bytes: True

        result = self.service._classify_image(b"image-bytes")

        self.assertEqual(result["subcategory"], "pumps")
        self.assertEqual(result["model"], "zappos-local:efficientnet_b0")
        self.assertEqual(result["classification_route"], "fpid_to_zappos_shape_fallback")
        self.assertEqual(result["base_subcategory"], "necklace")
        self.assertEqual(self.service._shoe_classifier.calls, 1)

    def test_suspect_non_horizontal_accessory_prediction_keeps_fpid(self):
        self.service._local_classifier = FakeClassifier(
            {
                "subcategory": "necklace",
                "confidence": 0.94,
                "top_predictions": [{"subcategory": "necklace", "score": 0.94}],
                "warnings": [],
                "model": "fpid-local:efficientnet_b0",
                "source_dataset": "Fashion Product Images",
            }
        )
        self.service._shoe_classifier = FakeClassifier(
            {
                "subcategory": "pumps",
                "confidence": 0.88,
                "top_predictions": [{"subcategory": "pumps", "score": 0.88}],
                "warnings": [],
                "model": "zappos-local:efficientnet_b0",
                "source_dataset": "Wardrobe manifest classifier (Zappos)",
            }
        )
        self.service._looks_like_horizontal_shoe_object = lambda _image_bytes: False

        result = self.service._classify_image(b"image-bytes")

        self.assertEqual(result["subcategory"], "necklace")
        self.assertEqual(result["classification_route"], "fpid")
        self.assertEqual(self.service._shoe_classifier.calls, 0)


if __name__ == "__main__":
    unittest.main()
