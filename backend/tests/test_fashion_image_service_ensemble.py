import unittest

from app.services.fashion_image_service import FashionImageService


LARGE_VERTICAL_APPAREL = {
    "aspect_height": 1.8,
    "aspect_width": 0.55,
    "height_coverage": 0.88,
    "width_coverage": 0.48,
    "top_coverage": 0.06,
    "bottom_coverage": 0.93,
    "object_area": 0.23,
    "max_row_width_ratio": 0.52,
}

NARROW_TIE_OBJECT = {
    "aspect_height": 3.2,
    "aspect_width": 0.31,
    "height_coverage": 0.82,
    "width_coverage": 0.18,
    "top_coverage": 0.08,
    "bottom_coverage": 0.90,
    "object_area": 0.09,
    "max_row_width_ratio": 0.21,
}

HORIZONTAL_SHOE_OBJECT = {
    "aspect_height": 0.42,
    "aspect_width": 2.4,
    "height_coverage": 0.38,
    "width_coverage": 0.78,
    "top_coverage": 0.31,
    "bottom_coverage": 0.69,
    "object_area": 0.18,
    "max_row_width_ratio": 0.72,
}


def prediction(subcategory, confidence, top_predictions=None, model="test-model"):
    return {
        "subcategory": subcategory,
        "confidence": confidence,
        "top_predictions": top_predictions or [],
        "warnings": [],
        "model": model,
    }


class StubClassifier:
    def __init__(self, result):
        self.result = result

    def predict(self, _image_bytes):
        return self.result


class FashionImageServiceEnsembleTest(unittest.TestCase):
    def make_service(self, metrics):
        service = object.__new__(FashionImageService)
        service.deepfashion_threshold = 0.55
        service.deepfashion_early_priority_threshold = 0.30
        service.deepfashion_apparel_fallback_threshold = 0.18
        service.fpid_primary_confidence_threshold = 0.58
        service.fpid_accessory_confidence_threshold = 0.76
        service.fpid_dress_hint_threshold = 0.18
        service.fpid_dress_shape_threshold = 0.08
        service.zappos_enabled = False
        service.zappos_top_shoe_score_threshold = 0.05
        service.zappos_fallback_confidence_threshold = 0.62
        service._get_object_metrics = lambda _image_bytes: metrics
        return service

    def test_deepfashion_trousers_beats_untrusted_fpid_tie(self):
        service = self.make_service(LARGE_VERTICAL_APPAREL)
        result = service._classify_with_ensemble(
            b"image",
            prediction("trousers", 0.45, model="deepfashion-local"),
            prediction("tie", 0.79, model="fpid-local"),
        )

        self.assertEqual(result["subcategory"], "trousers")
        self.assertEqual(result["classification_route"], "deepfashion_priority_over_untrusted_fpid_accessory")

    def test_dress_shape_and_fpid_hint_beats_deepfashion_skirt(self):
        service = self.make_service(LARGE_VERTICAL_APPAREL)
        result = service._classify_with_ensemble(
            b"image",
            prediction("skirt", 0.98, model="deepfashion-local"),
            prediction(
                "top",
                0.41,
                top_predictions=[
                    {"subcategory": "top", "score": 0.41},
                    {"subcategory": "dress", "score": 0.12},
                ],
                model="fpid-local",
            ),
        )

        self.assertEqual(result["subcategory"], "dress")
        self.assertEqual(result["classification_route"], "fpid_dress_or_shape")

    def test_real_tie_is_still_allowed_when_shape_matches(self):
        service = self.make_service(NARROW_TIE_OBJECT)
        result = service._classify_with_ensemble(
            b"image",
            prediction(None, None, model="deepfashion-local"),
            prediction("tie", 0.86, model="fpid-local"),
        )

        self.assertEqual(result["subcategory"], "tie")
        self.assertEqual(result["classification_route"], "fpid_accessory")

    def test_zappos_refines_shoe_prediction(self):
        service = self.make_service(HORIZONTAL_SHOE_OBJECT)
        service.zappos_enabled = True
        service._shoe_classifier = StubClassifier(prediction("pumps", 0.72, model="zappos-local"))

        result = service._classify_with_ensemble(
            b"image",
            prediction(None, None, model="deepfashion-local"),
            prediction("sandals", 0.68, model="fpid-local"),
        )

        self.assertEqual(result["subcategory"], "pumps")
        self.assertEqual(result["classification_route"], "ensemble_to_zappos_shoes")
        self.assertEqual(result["base_subcategory"], "sandals")


if __name__ == "__main__":
    unittest.main()
