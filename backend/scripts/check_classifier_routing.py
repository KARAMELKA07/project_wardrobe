from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.fashion_image_service import FashionImageService


DEFAULT_SAMPLE_PATHS = [
    PROJECT_ROOT / "data" / "raw" / "fpid_full" / "fashion-dataset" / "images" / "15970.jpg",
    PROJECT_ROOT
    / "data"
    / "raw"
    / "zappos"
    / "ut-zap50k-images-square"
    / "Shoes"
    / "Sneakers and Athletic Shoes"
    / "adidas"
    / "115191.151.jpg",
]


def resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved.resolve()

    cwd_path = (Path.cwd() / resolved).resolve()
    if cwd_path.exists():
        return cwd_path
    return (PROJECT_ROOT / resolved).resolve()


def summarize_result(result: dict) -> dict:
    return {
        "subcategory": result.get("subcategory"),
        "confidence": result.get("confidence"),
        "model": result.get("model"),
        "source_dataset": result.get("source_dataset"),
        "classification_route": result.get("classification_route"),
        "base_model": result.get("base_model"),
        "base_subcategory": result.get("base_subcategory"),
        "base_confidence": result.get("base_confidence"),
        "top_predictions": (result.get("top_predictions") or [])[:5],
        "warnings": result.get("warnings") or [],
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Check FPID/Zappos classifier routing on local images.")
    parser.add_argument(
        "images",
        nargs="*",
        help="Image paths. If omitted, the script uses one FPID clothing sample and one Zappos shoe sample.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    image_paths = [resolve_path(path) for path in args.images] if args.images else DEFAULT_SAMPLE_PATHS
    service = FashionImageService()
    output = {}

    for image_path in image_paths:
        if not image_path.exists():
            output[str(image_path)] = {"error": "file_not_found"}
            continue
        result = service._classify_image(image_path.read_bytes())
        output[str(image_path)] = summarize_result(result)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
