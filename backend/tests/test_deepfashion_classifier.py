import os
import tempfile
import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.deepfashion_classifier import DeepFashionLocalClassifier


class DeepFashionLocalClassifierTests(unittest.TestCase):
    def test_predict_returns_safe_warning_when_checkpoint_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_path = Path(temp_dir) / "missing.pt"
            metadata_path = Path(temp_dir) / "missing.json"
            original_checkpoint = os.environ.get("DEEPFASHION_CHECKPOINT_PATH")
            original_metadata = os.environ.get("DEEPFASHION_METADATA_PATH")

            os.environ["DEEPFASHION_CHECKPOINT_PATH"] = str(checkpoint_path)
            os.environ["DEEPFASHION_METADATA_PATH"] = str(metadata_path)

            try:
                classifier = DeepFashionLocalClassifier()
                result = classifier.predict(b"fake-image")
            finally:
                if original_checkpoint is None:
                    os.environ.pop("DEEPFASHION_CHECKPOINT_PATH", None)
                else:
                    os.environ["DEEPFASHION_CHECKPOINT_PATH"] = original_checkpoint

                if original_metadata is None:
                    os.environ.pop("DEEPFASHION_METADATA_PATH", None)
                else:
                    os.environ["DEEPFASHION_METADATA_PATH"] = original_metadata

            self.assertIsNone(result["subcategory"])
            self.assertTrue(result["warnings"])
            self.assertIn("DeepFashion", result["warnings"][0])


if __name__ == "__main__":
    unittest.main()
