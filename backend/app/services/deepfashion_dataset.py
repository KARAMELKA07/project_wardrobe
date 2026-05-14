from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEEPFASHION_TO_PROJECT = {
    "Anorak": "jacket",
    "Blazer": "blazer",
    "Blouse": "blouse",
    "Bomber": "jacket",
    "Button-Down": "shirt",
    "Cardigan": "cardigan",
    "Flannel": "shirt",
    "Halter": "blouse",
    "Henley": "longsleeve",
    "Hoodie": "hoodie",
    "Jacket": "jacket",
    "Jersey": "t_shirt",
    "Parka": "parka",
    "Peacoat": "coat",
    "Poncho": "coat",
    "Sweater": "sweater",
    "Tank": "crop_top",
    "Tee": "t_shirt",
    "Top": "blouse",
    "Turtleneck": "turtleneck",
    "Capris": "trousers",
    "Chinos": "chinos",
    "Culottes": "culottes",
    "Cutoffs": "shorts",
    "Gauchos": "culottes",
    "Jeans": "jeans",
    "Jeggings": "leggings",
    "Jodhpurs": "trousers",
    "Joggers": "joggers",
    "Leggings": "leggings",
    "Sarong": "skirt",
    "Shorts": "shorts",
    "Skirt": "skirt",
    "Sweatpants": "joggers",
    "Sweatshorts": "shorts",
    "Trunks": "shorts",
}

SUPPORTED_PROJECT_LABELS = sorted(set(DEEPFASHION_TO_PROJECT.values()))

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_DIR = PROJECT_ROOT / "backend" / "Category and Attribute Prediction Benchmark"


@dataclass
class DeepFashionSample:
    image_path: Path
    relative_image_path: str
    split: str
    category_name: str
    project_subcategory: str
    bbox: tuple[int, int, int, int] | None


def resolve_dataset_dir(dataset_dir: str | Path | None = None) -> Path:
    if dataset_dir:
        resolved = Path(dataset_dir)
        if not resolved.is_absolute():
            resolved = PROJECT_ROOT / resolved
        return resolved.resolve()
    return DEFAULT_DATASET_DIR


def validate_dataset_dir(dataset_dir: str | Path | None = None) -> dict:
    dataset_path = resolve_dataset_dir(dataset_dir)
    image_root = find_image_root(dataset_path)

    return {
        "dataset_dir": str(dataset_path),
        "exists": dataset_path.exists(),
        "has_annotations": (dataset_path / "Anno_coarse").exists() and (dataset_path / "Eval").exists(),
        "image_root": str(image_root) if image_root else None,
        "has_images": image_root is not None,
    }


def find_image_root(dataset_dir: str | Path | None = None) -> Path | None:
    dataset_path = resolve_dataset_dir(dataset_dir)
    candidates = [
        dataset_path / "Img" / "img" / "img",
        dataset_path / "img" / "img",
        dataset_path / "img",
        dataset_path / "Img" / "img",
        dataset_path / "Img",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_class_names() -> list[str]:
    return list(SUPPORTED_PROJECT_LABELS)


def build_class_to_index() -> dict[str, int]:
    return {label: index for index, label in enumerate(build_class_names())}


def load_supported_samples(dataset_dir: str | Path | None = None, split: str | None = None) -> list[DeepFashionSample]:
    dataset_path = resolve_dataset_dir(dataset_dir)
    image_root = find_image_root(dataset_path)
    if image_root is None:
        raise FileNotFoundError(
            "Не найдена папка с изображениями DeepFashion. Ожидается Img/img или img внутри датасета."
        )

    category_names = _load_category_names(dataset_path / "Anno_coarse" / "list_category_cloth.txt")
    categories_by_image = _load_category_labels(
        dataset_path / "Anno_coarse" / "list_category_img.txt",
        category_names,
    )
    partitions = _load_eval_partitions(dataset_path / "Eval" / "list_eval_partition.txt")
    bboxes = _load_bboxes(dataset_path / "Anno_coarse" / "list_bbox.txt")

    samples: list[DeepFashionSample] = []
    for relative_path, category_name in categories_by_image.items():
        if category_name not in DEEPFASHION_TO_PROJECT:
            continue
        sample_split = partitions.get(relative_path)
        if split and sample_split != split:
            continue

        image_path = resolve_image_path(image_root, relative_path)
        if image_path is None:
            continue

        samples.append(
            DeepFashionSample(
                image_path=image_path,
                relative_image_path=relative_path,
                split=sample_split or "train",
                category_name=category_name,
                project_subcategory=DEEPFASHION_TO_PROJECT[category_name],
                bbox=bboxes.get(relative_path),
            )
        )

    return samples


def resolve_image_path(image_root: Path, relative_path: str) -> Path | None:
    trimmed = relative_path[4:] if relative_path.startswith("img/") else relative_path
    candidates = [
        image_root / relative_path,
        image_root / trimmed,
        image_root.parent / relative_path,
        image_root.parent / trimmed,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def dump_dataset_summary(dataset_dir: str | Path | None = None) -> dict:
    dataset_path = resolve_dataset_dir(dataset_dir)
    summary = validate_dataset_dir(dataset_path)
    if not summary["has_images"]:
        return summary

    counts: dict[str, dict[str, int]] = {}
    for split_name in ("train", "val", "test"):
        split_counts: dict[str, int] = {}
        for sample in load_supported_samples(dataset_path, split=split_name):
            split_counts[sample.project_subcategory] = split_counts.get(sample.project_subcategory, 0) + 1
        counts[split_name] = split_counts

    summary["splits"] = counts
    summary["class_names"] = build_class_names()
    return summary


def save_dataset_summary(destination: str | Path, dataset_dir: str | Path | None = None):
    destination_path = Path(destination)
    destination_path.write_text(
        json.dumps(dump_dataset_summary(dataset_dir), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _iter_table_rows(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file_handle:
        next(file_handle, None)
        next(file_handle, None)
        for line in file_handle:
            stripped = line.strip()
            if not stripped:
                continue
            yield stripped.split()


def _load_category_names(file_path: Path) -> dict[int, str]:
    category_names: dict[int, str] = {}
    for index, row in enumerate(_iter_table_rows(file_path), start=1):
        category_names[index] = row[0]
    return category_names


def _load_category_labels(file_path: Path, category_names: dict[int, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in _iter_table_rows(file_path):
        relative_path = row[0]
        category_id = int(row[1])
        result[relative_path] = category_names[category_id]
    return result


def _load_eval_partitions(file_path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in _iter_table_rows(file_path):
        result[row[0]] = row[1]
    return result


def _load_bboxes(file_path: Path) -> dict[str, tuple[int, int, int, int]]:
    result: dict[str, tuple[int, int, int, int]] = {}
    for row in _iter_table_rows(file_path):
        result[row[0]] = tuple(int(value) for value in row[1:5])
    return result
