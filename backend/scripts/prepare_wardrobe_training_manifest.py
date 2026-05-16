from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ZAPPOS_ROOT = PROJECT_ROOT / "data" / "raw" / "zappos"
DEFAULT_IFASHION_ROOT = PROJECT_ROOT / "data" / "raw" / "ifashion" / "imat_fashion_comp-master"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "wardrobe_training"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

IFASHION_CATEGORY_TO_PROJECT = {
    "Athletic Pants": "joggers",
    "Athletic Sets": "tracksuit",
    "Athletic Shirts": "t_shirt",
    "Athletic Shorts": "shorts",
    "Baggy Jeans": "jeans",
    "Batwing Tops": "top",
    "Beach & Swim Wear": "swimwear",
    "Bikinis": "swimwear",
    "Binders": "underwear",
    "Blouses": "blouse",
    "Bodysuits": "bodysuit",
    "Boots": "boots",
    "Bra Straps": "underwear",
    "Bubble Coats": "coat",
    "Business Shoes": "shoes",
    "Capes & Capelets": "cape",
    "Capri Pants": "trousers",
    "Cardigans": "cardigan",
    "Cargo Pants": "trousers",
    "Cargo Shorts": "shorts",
    "Casual Dresses": "dress",
    "Casual Pants": "trousers",
    "Casual Shirts": "shirt",
    "Casual Shoes": "shoes",
    "Casual Shorts": "shorts",
    "Cleats": "sneakers",
    "Clubbing Dresses": "dress",
    "Cocktail Dresses": "dress",
    "Corsets": "corset",
    "Crop Tops": "top",
    "Dance Wear": "activewear",
    "Drawstring Pants": "trousers",
    "Dress Shirts": "shirt",
    "Dresses": "dress",
    "Fashion Sets": "set",
    "Flats": "flats",
    "Formal Dresses": "dress",
    "Halter Tops": "top",
    "Harem Pants": "trousers",
    "Heels": "pumps",
    "Hiking Boots": "boots",
    "Hoodies & Sweatshirts": "hoodie",
    "Hosiery, Stockings, Tights": "socks",
    "Jackets": "jacket",
    "Jeans": "jeans",
    "Jerseys": "t_shirt",
    "Jumpsuits Overalls & Rompers": "jumpsuit",
    "Kimonos": "kimono",
    "Leggings": "leggings",
    "Lingerie Sleepwear & Underwear": "underwear",
    "Loafers & Slip-on Shoes": "shoes",
    "Nightgowns": "sleepwear",
    "Padded Bras": "underwear",
    "Pajamas": "sleepwear",
    "Party Dresses": "dress",
    "Peacoats": "coat",
    "Pencil Skirts": "skirt",
    "Petticoats": "skirt",
    "Polos": "polo",
    "Prom Dresses": "dress",
    "Pullover Sweaters": "sweater",
    "Rain Boots": "boots",
    "Raincoats": "coat",
    "Robes": "robe",
    "Running Shoes": "sneakers",
    "Sandals": "sandals",
    "Sheer Tops": "top",
    "Shorts": "shorts",
    "Skinny Jeans": "jeans",
    "Skirts": "skirt",
    "Slippers": "slippers",
    "Sneakers": "sneakers",
    "Sports Bras": "underwear",
    "Stilettos": "pumps",
    "Suits & Blazers": "blazer",
    "Sweatpants": "joggers",
    "Swim Trunks": "swimwear",
    "Swimsuit Cover-ups": "swimwear",
    "Swimsuits": "swimwear",
    "T-Shirts": "t_shirt",
    "Tank Tops": "top",
    "Thermal Underwear": "underwear",
    "Thigh Highs": "socks",
    "Thongs": "underwear",
    "Three Piece Suits": "suit",
    "Trench Coats": "coat",
    "Trousers": "trousers",
    "Tube Tops": "top",
    "Tutus": "skirt",
    "Undershirts": "top",
    "Underwear": "underwear",
    "Vests": "vest",
    "Wedding Dresses": "dress",
    "Wedges & Platforms": "pumps",
    "Winter Boots": "boots",
    "Yoga Pants": "leggings",
}


@dataclass(frozen=True)
class ManifestRow:
    source: str
    split: str
    image_path: str
    label: str
    category: str
    source_id: str
    source_category: str
    source_subcategory: str


def resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved.resolve()


def relative_project_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def map_zappos_label(category: str, subcategory: str) -> tuple[str, str]:
    source_category = category.strip()
    source_subcategory = subcategory.strip()
    normalized_category = normalize_text(source_category)
    normalized_subcategory = normalize_text(source_subcategory)

    if normalized_category == "boots":
        if normalized_subcategory == "ankle":
            return "shoes", "ankle_boots"
        return "shoes", "boots"

    if normalized_category == "sandals":
        return "shoes", "sandals"

    if normalized_category == "slippers":
        return "shoes", "slippers"

    if normalized_category == "shoes":
        if normalized_subcategory in {
            "sneakers_and_athletic_shoes",
            "athletic",
            "firstwalker",
            "prewalker",
            "crib_shoes",
        }:
            return "shoes", "sneakers"
        if normalized_subcategory in {"heels", "heel", "slipper_heels"}:
            return "shoes", "pumps"
        if normalized_subcategory in {"flats", "flat"}:
            return "shoes", "flats"
        if normalized_subcategory in {"loafers", "oxfords", "boat_shoes", "clogs_and_mules"}:
            return "shoes", "shoes"

    return "shoes", "shoes"


def build_image_index(image_root: Path) -> dict[str, Path]:
    image_by_stem: dict[str, Path] = {}
    for image_path in image_root.rglob("*"):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        image_by_stem.setdefault(image_path.stem, image_path)
    return image_by_stem


def find_zappos_image(cid: str, image_by_stem: dict[str, Path]) -> Path | None:
    normalized = cid.strip().replace("-", ".")
    return image_by_stem.get(normalized) or image_by_stem.get(cid.strip())


def split_rows(rows: list[ManifestRow], val_ratio: float, seed: int) -> list[ManifestRow]:
    rng = random.Random(seed)
    grouped: dict[str, list[ManifestRow]] = defaultdict(list)
    for row in rows:
        grouped[row.label].append(row)

    split_rows_result: list[ManifestRow] = []
    for label_rows in grouped.values():
        rng.shuffle(label_rows)
        val_count = max(1, int(len(label_rows) * val_ratio)) if len(label_rows) > 1 else 0
        for index, row in enumerate(label_rows):
            split = "val" if index < val_count else "train"
            split_rows_result.append(
                ManifestRow(
                    source=row.source,
                    split=split,
                    image_path=row.image_path,
                    label=row.label,
                    category=row.category,
                    source_id=row.source_id,
                    source_category=row.source_category,
                    source_subcategory=row.source_subcategory,
                )
            )

    rng.shuffle(split_rows_result)
    return split_rows_result


def cap_rows_per_label(rows: list[ManifestRow], max_samples_per_label: int | None, seed: int) -> list[ManifestRow]:
    if not max_samples_per_label:
        return rows

    rng = random.Random(seed)
    grouped: dict[str, list[ManifestRow]] = defaultdict(list)
    for row in rows:
        grouped[row.label].append(row)

    capped: list[ManifestRow] = []
    for label_rows in grouped.values():
        rng.shuffle(label_rows)
        capped.extend(label_rows[:max_samples_per_label])
    rng.shuffle(capped)
    return capped


def read_zappos_rows(zappos_root: Path, max_samples_per_label: int | None, seed: int) -> tuple[list[ManifestRow], dict]:
    data_root = zappos_root / "ut-zap50k-data"
    image_root = zappos_root / "ut-zap50k-images-square"
    metadata_path = data_root / "meta-data.csv"

    status = {
        "root": str(zappos_root),
        "metadata_path": str(metadata_path),
        "image_root": str(image_root),
        "available": metadata_path.exists() and image_root.exists(),
        "metadata_rows": 0,
        "images_indexed": 0,
        "matched_rows": 0,
        "missing_images": 0,
        "source_categories": {},
        "source_subcategories": {},
    }

    if not metadata_path.exists() or not image_root.exists():
        return [], status

    image_by_stem = build_image_index(image_root)
    status["images_indexed"] = len(image_by_stem)

    rows: list[ManifestRow] = []
    with metadata_path.open("r", encoding="utf-8", errors="replace", newline="") as file_handle:
        reader = csv.DictReader(file_handle)
        source_categories: Counter[str] = Counter()
        source_subcategories: Counter[str] = Counter()
        for record in reader:
            status["metadata_rows"] += 1
            cid = (record.get("CID") or "").strip()
            source_category = (record.get("Category") or "").strip()
            source_subcategory = (record.get("SubCategory") or "").strip()
            if not cid or not source_category:
                continue

            source_categories[source_category] += 1
            source_subcategories[source_subcategory] += 1

            image_path = find_zappos_image(cid, image_by_stem)
            if image_path is None:
                status["missing_images"] += 1
                continue

            category, label = map_zappos_label(source_category, source_subcategory)
            rows.append(
                ManifestRow(
                    source="zappos",
                    split="",
                    image_path=relative_project_path(image_path),
                    label=label,
                    category=category,
                    source_id=cid,
                    source_category=source_category,
                    source_subcategory=source_subcategory,
                )
            )

    rows = cap_rows_per_label(rows, max_samples_per_label, seed)
    status["matched_rows"] = len(rows)
    status["source_categories"] = dict(source_categories.most_common())
    status["source_subcategories"] = dict(source_subcategories.most_common())
    return rows, status


def load_ifashion_category_maps(label_map_path: Path) -> tuple[dict[str, str], dict[str, str], Counter[str], list[str]]:
    label_id_to_name: dict[str, str] = {}
    label_id_to_project: dict[str, str] = {}
    task_counts: Counter[str] = Counter()
    category_labels: list[str] = []

    if not label_map_path.exists():
        return label_id_to_name, label_id_to_project, task_counts, category_labels

    with label_map_path.open("r", encoding="utf-8", errors="replace", newline="") as file_handle:
        reader = csv.DictReader(file_handle)
        for record in reader:
            label_id = (record.get("labelId") or "").strip()
            task_name = (record.get("taskName") or "").strip()
            label_name = (record.get("labelName") or "").strip()
            if task_name:
                task_counts[task_name] += 1
            if task_name != "category" or not label_id or not label_name:
                continue
            category_labels.append(label_name)
            label_id_to_name[label_id] = label_name
            project_label = IFASHION_CATEGORY_TO_PROJECT.get(label_name)
            if project_label:
                label_id_to_project[label_id] = project_label

    return label_id_to_name, label_id_to_project, task_counts, category_labels


def find_ifashion_image_dirs(ifashion_root: Path) -> list[Path]:
    candidate_dirs = [
        ifashion_root / "images",
        ifashion_root / "train",
        ifashion_root / "val",
        ifashion_root / "train_images",
        ifashion_root / "val_images",
    ]
    return [path for path in candidate_dirs if path.exists()]


def build_ifashion_image_index(image_dirs: list[Path]) -> dict[str, Path]:
    image_by_key: dict[str, Path] = {}
    for image_dir in image_dirs:
        for image_path in image_dir.rglob("*"):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            image_by_key.setdefault(image_path.stem.lower(), image_path)
            image_by_key.setdefault(image_path.name.lower(), image_path)
    return image_by_key


def find_ifashion_image(image_record: dict, image_by_key: dict[str, Path]) -> Path | None:
    image_id = str(image_record.get("image_id") or "").strip()
    url = str(image_record.get("url") or "").strip()
    candidates = []
    if image_id:
        candidates.append(image_id.lower())
    if url:
        parsed_name = Path(urlparse(url).path).name
        if parsed_name:
            candidates.append(parsed_name.lower())
            candidates.append(Path(parsed_name).stem.lower())

    for candidate in candidates:
        image_path = image_by_key.get(candidate)
        if image_path:
            return image_path
    return None


def read_ifashion_split(
    split_path: Path,
    split: str,
    image_by_key: dict[str, Path],
    label_id_to_name: dict[str, str],
    label_id_to_project: dict[str, str],
) -> tuple[list[ManifestRow], dict]:
    status = {
        "path": str(split_path),
        "available": split_path.exists(),
        "images_in_json": 0,
        "annotations_in_json": 0,
        "matched_rows": 0,
        "missing_images": 0,
        "unsupported_annotations": 0,
    }
    if not split_path.exists():
        return [], status

    payload = json.loads(split_path.read_text(encoding="utf-8"))
    images = payload.get("images") or []
    annotations = payload.get("annotations") or []
    status["images_in_json"] = len(images)
    status["annotations_in_json"] = len(annotations)

    image_by_id = {str(image.get("image_id")): image for image in images if image.get("image_id") is not None}
    rows: list[ManifestRow] = []
    for annotation in annotations:
        image_id = str(annotation.get("image_id") or "").strip()
        label_ids = annotation.get("label_id") or []
        if not isinstance(label_ids, list):
            label_ids = [label_ids]

        matched_label_id = next((str(label_id) for label_id in label_ids if str(label_id) in label_id_to_project), None)
        if not matched_label_id:
            status["unsupported_annotations"] += 1
            continue

        image_record = image_by_id.get(image_id)
        if not image_record:
            status["missing_images"] += 1
            continue

        image_path = find_ifashion_image(image_record, image_by_key)
        if image_path is None:
            status["missing_images"] += 1
            continue

        label = label_id_to_project[matched_label_id]
        source_category = label_id_to_name.get(matched_label_id, label)
        rows.append(
            ManifestRow(
                source="ifashion",
                split=split,
                image_path=relative_project_path(image_path),
                label=label,
                category=label,
                source_id=image_id,
                source_category=source_category,
                source_subcategory=source_category,
            )
        )

    status["matched_rows"] = len(rows)
    return rows, status


def read_ifashion_rows(ifashion_root: Path) -> tuple[list[ManifestRow], dict]:
    label_map_path = ifashion_root / "iMat_fashion_2018_label_map_228.csv"
    train_json = ifashion_root / "train.json"
    val_json = ifashion_root / "val.json"
    label_id_to_name, label_id_to_project, task_counts, category_labels = load_ifashion_category_maps(label_map_path)
    image_dirs = find_ifashion_image_dirs(ifashion_root)
    image_by_key = build_ifashion_image_index(image_dirs)
    train_rows, train_status = read_ifashion_split(
        train_json,
        "train",
        image_by_key,
        label_id_to_name,
        label_id_to_project,
    )
    val_rows, val_status = read_ifashion_split(
        val_json,
        "val",
        image_by_key,
        label_id_to_name,
        label_id_to_project,
    )

    rows = train_rows + val_rows
    status = {
        "root": str(ifashion_root),
        "label_map_path": str(label_map_path),
        "label_map_available": label_map_path.exists(),
        "train_json_available": train_json.exists(),
        "val_json_available": val_json.exists(),
        "image_dirs_found": [str(path) for path in image_dirs],
        "images_indexed": len(image_by_key),
        "ready_for_training": train_json.exists() and val_json.exists() and bool(image_dirs),
        "matched_rows": len(rows),
        "train": train_status,
        "val": val_status,
        "task_counts": dict(task_counts.most_common()),
        "category_label_count": len(category_labels),
        "mapped_category_label_count": len(set(label_id_to_project.values())),
        "note": (
            "iFashion is merged only when train.json, val.json, and downloaded image files are present."
        ),
    }
    return rows, status


def write_manifest(rows: list[ManifestRow], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "split",
        "image_path",
        "label",
        "category",
        "source_id",
        "source_category",
        "source_subcategory",
    ]
    with manifest_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_summary(summary: dict, summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare Project Wardrobe image-classifier training manifest.")
    parser.add_argument("--zappos-root", default=str(DEFAULT_ZAPPOS_ROOT))
    parser.add_argument("--ifashion-root", default=str(DEFAULT_IFASHION_ROOT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--max-samples-per-label",
        type=int,
        default=None,
        help="Optional cap for smoke-test manifests.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.val_ratio <= 0 or args.val_ratio >= 0.5:
        raise SystemExit("--val-ratio must be greater than 0 and lower than 0.5")

    zappos_root = resolve_path(args.zappos_root)
    ifashion_root = resolve_path(args.ifashion_root)
    output_dir = resolve_path(args.output_dir)
    manifest_path = output_dir / "manifest.csv"
    summary_path = output_dir / "summary.json"

    print("[stage] inspecting Zappos", flush=True)
    zappos_rows, zappos_status = read_zappos_rows(
        zappos_root=zappos_root,
        max_samples_per_label=args.max_samples_per_label,
        seed=args.seed,
    )
    if not zappos_rows:
        raise SystemExit(f"No usable Zappos rows found in {zappos_root}")
    zappos_rows = split_rows(zappos_rows, args.val_ratio, args.seed)

    print("[stage] inspecting iFashion", flush=True)
    ifashion_rows, ifashion_status = read_ifashion_rows(ifashion_root)

    rows = zappos_rows + ifashion_rows
    random.Random(args.seed).shuffle(rows)

    label_counts = Counter(row.label for row in rows)
    split_counts = Counter(row.split for row in rows)
    label_split_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"train": 0, "val": 0})
    for row in rows:
        label_split_counts[row.label][row.split] += 1

    summary = {
        "manifest_path": str(manifest_path),
        "total_rows": len(rows),
        "label_counts": dict(label_counts.most_common()),
        "split_counts": dict(split_counts.most_common()),
        "label_split_counts": dict(sorted(label_split_counts.items())),
        "zappos": zappos_status,
        "ifashion": ifashion_status,
        "settings": {
            "val_ratio": args.val_ratio,
            "seed": args.seed,
            "max_samples_per_label": args.max_samples_per_label,
        },
    }

    print("[stage] writing outputs", flush=True)
    write_manifest(rows, manifest_path)
    write_summary(summary, summary_path)

    print("[stage] done", flush=True)
    print(f"Manifest: {manifest_path}")
    print(f"Summary: {summary_path}")
    print(f"Rows: {len(rows)}")
    print(f"Train: {split_counts.get('train', 0)}")
    print(f"Validation: {split_counts.get('val', 0)}")
    print("Labels:")
    for label, count in label_counts.most_common():
        split_info = label_split_counts[label]
        print(f"  {label}: {count} (train={split_info['train']}, val={split_info['val']})")
    if not ifashion_status["ready_for_training"]:
        print(
            "iFashion is not merged yet: train.json, val.json, and downloaded images are missing.",
            flush=True,
        )
    elif not ifashion_rows:
        print(
            "iFashion files are present, but no supported local image rows were matched.",
            flush=True,
        )
    else:
        print(f"iFashion rows merged: {len(ifashion_rows)}", flush=True)


if __name__ == "__main__":
    main()
