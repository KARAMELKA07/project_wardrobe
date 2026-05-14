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


if __name__ == "__main__":
    unittest.main()
