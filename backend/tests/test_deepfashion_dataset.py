import tempfile
import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.deepfashion_dataset import (
    load_supported_samples,
    validate_dataset_dir,
)


class DeepFashionDatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dataset_dir = Path(self.temp_dir.name)
        (self.dataset_dir / "Anno_coarse").mkdir(parents=True, exist_ok=True)
        (self.dataset_dir / "Eval").mkdir(parents=True, exist_ok=True)
        (self.dataset_dir / "img" / "sample_item").mkdir(parents=True, exist_ok=True)

        (self.dataset_dir / "img" / "sample_item" / "img_0001.jpg").write_bytes(b"test")
        (self.dataset_dir / "img" / "sample_item" / "img_0002.jpg").write_bytes(b"test")

        (self.dataset_dir / "Anno_coarse" / "list_category_cloth.txt").write_text(
            "\n".join(
                [
                    "2",
                    "category_name  category_type",
                    "Button-Down    1",
                    "Dress          3",
                ]
            ),
            encoding="utf-8",
        )
        (self.dataset_dir / "Anno_coarse" / "list_category_img.txt").write_text(
            "\n".join(
                [
                    "2",
                    "image_name  category_label",
                    "img/sample_item/img_0001.jpg 1",
                    "img/sample_item/img_0002.jpg 2",
                ]
            ),
            encoding="utf-8",
        )
        (self.dataset_dir / "Anno_coarse" / "list_bbox.txt").write_text(
            "\n".join(
                [
                    "2",
                    "image_name x_1 y_1 x_2 y_2",
                    "img/sample_item/img_0001.jpg 0 0 20 30",
                    "img/sample_item/img_0002.jpg 0 0 20 30",
                ]
            ),
            encoding="utf-8",
        )
        (self.dataset_dir / "Eval" / "list_eval_partition.txt").write_text(
            "\n".join(
                [
                    "2",
                    "image_name evaluation_status",
                    "img/sample_item/img_0001.jpg train",
                    "img/sample_item/img_0002.jpg val",
                ]
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_dataset_dir_reports_image_root(self):
        status = validate_dataset_dir(self.dataset_dir)

        self.assertTrue(status["exists"])
        self.assertTrue(status["has_annotations"])
        self.assertTrue(status["has_images"])
        self.assertIn("img", status["image_root"])

    def test_load_supported_samples_filters_unsupported_classes(self):
        samples = load_supported_samples(self.dataset_dir)

        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].project_subcategory, "shirt")
        self.assertEqual(samples[0].split, "train")
        self.assertEqual(samples[0].bbox, (0, 0, 20, 30))


if __name__ == "__main__":
    unittest.main()
