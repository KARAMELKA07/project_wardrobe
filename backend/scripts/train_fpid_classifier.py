from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_TORCH_HOME = BACKEND_ROOT / ".torch-cache"
os.environ.setdefault("TORCH_HOME", str(DEFAULT_TORCH_HOME))

sys.path.insert(0, str(BACKEND_ROOT))


ARTICLE_TYPE_TO_PROJECT = {
    "Backpacks": "bag",
    "Bags": "bag",
    "Belts": "belt",
    "Blazers": "blazer",
    "Booties": "boots",
    "Boxers": "underwear",
    "Bra": "underwear",
    "Bracelet": "bracelet",
    "Briefs": "underwear",
    "Camisoles": "top",
    "Capris": "trousers",
    "Caps": "hat",
    "Casual Shoes": "shoes",
    "Churidar": "trousers",
    "Clutches": "bag",
    "Dresses": "dress",
    "Duffel Bag": "bag",
    "Dupatta": "scarf",
    "Earrings": "earrings",
    "Flats": "shoes",
    "Flip Flops": "sandals",
    "Formal Shoes": "shoes",
    "Handbags": "bag",
    "Heels": "shoes",
    "Innerwear Vests": "underwear",
    "Jackets": "jacket",
    "Jeans": "jeans",
    "Jeggings": "leggings",
    "Jewellery Set": "jewelry",
    "Jumpsuit": "jumpsuit",
    "Kurtas": "kurta",
    "Kurtis": "kurta",
    "Laptop Bag": "bag",
    "Leggings": "leggings",
    "Lehenga Choli": "dress",
    "Messenger Bag": "bag",
    "Mobile Pouch": "bag",
    "Necklace and Chains": "necklace",
    "Night suits": "sleepwear",
    "Nightdress": "sleepwear",
    "Patiala": "trousers",
    "Pendant": "necklace",
    "Rain Jacket": "jacket",
    "Rompers": "jumpsuit",
    "Sandals": "sandals",
    "Sarees": "dress",
    "Scarves": "scarf",
    "Shirts": "shirt",
    "Shorts": "shorts",
    "Shrug": "cardigan",
    "Skirts": "skirt",
    "Socks": "socks",
    "Sports Sandals": "sandals",
    "Sports Shoes": "sneakers",
    "Stockings": "socks",
    "Sunglasses": "sunglasses",
    "Sweaters": "sweater",
    "Sweatshirts": "sweatshirt",
    "Ties": "tie",
    "Tops": "top",
    "Track Pants": "joggers",
    "Tracksuits": "tracksuit",
    "Travel Accessory": "accessory",
    "Trousers": "trousers",
    "Tshirts": "t_shirt",
    "Tunics": "tunic",
    "Waist Pouch": "bag",
    "Waistcoat": "vest",
    "Wallets": "wallet",
    "Watches": "watch",
}


@dataclass(frozen=True)
class FpidSample:
    image_path: Path
    label: str
    article_type: str
    base_colour: str
    season: str
    usage: str


class FpidClassificationDataset(Dataset):
    def __init__(self, samples: list[FpidSample], class_to_index: dict[str, int], transform):
        self.samples = samples
        self.class_to_index = class_to_index
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        image = Image.open(sample.image_path).convert("RGB")
        return self.transform(image), self.class_to_index[sample.label]


def resolve_dataset_dir(dataset_dir: str | Path) -> Path:
    path = Path(dataset_dir)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def read_fpid_samples(dataset_dir: Path) -> list[FpidSample]:
    csv_path = dataset_dir / "styles.csv"
    image_dir = dataset_dir / "images"
    if not csv_path.exists():
        raise FileNotFoundError(f"styles.csv not found: {csv_path}")
    if not image_dir.exists():
        raise FileNotFoundError(f"images directory not found: {image_dir}")

    samples: list[FpidSample] = []
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as file_handle:
        reader = csv.DictReader(file_handle)
        for row in reader:
            article_type = (row.get("articleType") or "").strip()
            item_id = (row.get("id") or "").strip()
            label = ARTICLE_TYPE_TO_PROJECT.get(article_type)
            if not item_id or not label:
                continue

            image_path = image_dir / f"{item_id}.jpg"
            if not image_path.exists():
                continue

            samples.append(
                FpidSample(
                    image_path=image_path,
                    label=label,
                    article_type=article_type,
                    base_colour=(row.get("baseColour") or "").strip(),
                    season=(row.get("season") or "").strip(),
                    usage=(row.get("usage") or "").strip(),
                )
            )
    return samples


def filter_classes(samples: list[FpidSample], min_samples_per_class: int, max_classes: int | None) -> list[FpidSample]:
    counts = Counter(sample.label for sample in samples)
    labels = [label for label, count in counts.most_common() if count >= min_samples_per_class]
    if max_classes:
        labels = labels[:max_classes]
    allowed = set(labels)
    return [sample for sample in samples if sample.label in allowed]


def split_samples(samples: list[FpidSample], val_ratio: float, seed: int) -> tuple[list[FpidSample], list[FpidSample]]:
    rng = random.Random(seed)
    grouped: dict[str, list[FpidSample]] = defaultdict(list)
    for sample in samples:
        grouped[sample.label].append(sample)

    train: list[FpidSample] = []
    val: list[FpidSample] = []
    for label_samples in grouped.values():
        rng.shuffle(label_samples)
        val_count = max(1, int(len(label_samples) * val_ratio))
        val.extend(label_samples[:val_count])
        train.extend(label_samples[val_count:])

    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def create_model(architecture: str, num_classes: int, freeze_backbone: bool, pretrained: bool):
    if architecture == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        if freeze_backbone:
            for parameter in model.features.parameters():
                parameter.requires_grad = False
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
        return model

    if architecture == "resnet50":
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        model = models.resnet50(weights=weights)
        if freeze_backbone:
            for name, parameter in model.named_parameters():
                if not name.startswith("fc."):
                    parameter.requires_grad = False
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model

    raise ValueError(f"Unsupported architecture: {architecture}")


def format_duration(seconds: float) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        return "unknown"
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def run_train_epoch(model, loader, criterion, optimizer, device, epoch: int, epochs: int, log_every: int):
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    started_at = time.time()
    total_batches = len(loader)

    for batch_index, (images, labels) in enumerate(loader, start=1):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        batch_size = labels.size(0)
        total_loss += loss.item() * batch_size
        total_correct += (logits.argmax(dim=1) == labels).sum().item()
        total_samples += batch_size

        if batch_index == 1 or batch_index % log_every == 0 or batch_index == total_batches:
            elapsed = time.time() - started_at
            progress = batch_index / max(total_batches, 1)
            eta = elapsed * (1 - progress) / max(progress, 1e-9)
            accuracy = total_correct / max(total_samples, 1)
            print(
                f"[train] epoch {epoch}/{epochs} batch {batch_index}/{total_batches} "
                f"loss={total_loss / max(total_samples, 1):.4f} "
                f"acc={accuracy:.4f} eta={format_duration(eta)}",
                flush=True,
            )

    return total_loss / max(total_samples, 1), total_correct / max(total_samples, 1)


def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    total_batches = len(loader)
    started_at = time.time()

    with torch.no_grad():
        for batch_index, (images, labels) in enumerate(loader, start=1):
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)

            batch_size = labels.size(0)
            total_loss += loss.item() * batch_size
            total_correct += (logits.argmax(dim=1) == labels).sum().item()
            total_samples += batch_size

            if batch_index == 1 or batch_index == total_batches:
                elapsed = time.time() - started_at
                progress = batch_index / max(total_batches, 1)
                eta = elapsed * (1 - progress) / max(progress, 1e-9)
                print(f"[val] batch {batch_index}/{total_batches} eta={format_duration(eta)}", flush=True)

    return total_loss / max(total_samples, 1), total_correct / max(total_samples, 1)


def parse_args():
    parser = argparse.ArgumentParser(description="Train a Fashion Product Images classifier for Project Wardrobe.")
    parser.add_argument("--dataset-dir", default=str(PROJECT_ROOT / "data" / "raw" / "fpid_small"))
    parser.add_argument("--architecture", default="efficientnet_b0", choices=["efficientnet_b0", "resnet50"])
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-samples-per-class", type=int, default=30)
    parser.add_argument("--max-classes", type=int, default=40)
    parser.add_argument("--freeze-backbone", action="store_true")
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--log-every", type=int, default=25)
    parser.add_argument(
        "--checkpoint-path",
        default=str(BACKEND_ROOT / "model_artifacts" / "deepfashion_classifier.pt"),
    )
    parser.add_argument(
        "--metadata-path",
        default=str(BACKEND_ROOT / "model_artifacts" / "deepfashion_classifier.metadata.json"),
    )
    parser.add_argument(
        "--metrics-path",
        default=str(BACKEND_ROOT / "training_logs" / "fpid_training_metrics.jsonl"),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    dataset_dir = resolve_dataset_dir(args.dataset_dir)

    print("[stage] reading Fashion Product Images metadata", flush=True)
    samples = read_fpid_samples(dataset_dir)
    if not samples:
        raise SystemExit(f"No supported samples found in {dataset_dir}")

    original_count = len(samples)
    samples = filter_classes(samples, args.min_samples_per_class, args.max_classes)
    if len(set(sample.label for sample in samples)) < 2:
        raise SystemExit("Not enough classes after filtering. Lower --min-samples-per-class or check the dataset.")

    train_samples, val_samples = split_samples(samples, args.val_ratio, args.seed)
    class_names = sorted(set(sample.label for sample in samples))
    class_to_index = {label: index for index, label in enumerate(class_names)}
    metrics_path = Path(args.metrics_path)
    if not metrics_path.is_absolute():
        metrics_path = PROJECT_ROOT / metrics_path
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    print("[stage] dataset summary", flush=True)
    print(f"Dataset: {dataset_dir}")
    print(f"Supported samples before filtering: {original_count}")
    print(f"Samples after filtering: {len(samples)}")
    print(f"Train samples: {len(train_samples)}")
    print(f"Validation samples: {len(val_samples)}")
    print(f"Classes ({len(class_names)}): {', '.join(class_names)}")
    print("Top class counts:")
    for label, count in Counter(sample.label for sample in samples).most_common(20):
        print(f"  {label}: {count}")
    print(f"Metrics log: {metrics_path}")

    metrics_path.write_text(
        json.dumps(
            {
                "event": "start",
                "dataset_dir": str(dataset_dir),
                "architecture": args.architecture,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "min_samples_per_class": args.min_samples_per_class,
                "max_classes": args.max_classes,
                "train_samples": len(train_samples),
                "val_samples": len(val_samples),
                "class_names": class_names,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    train_transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    eval_transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    train_loader = DataLoader(
        FpidClassificationDataset(train_samples, class_to_index, train_transform),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
    )
    val_loader = DataLoader(
        FpidClassificationDataset(val_samples, class_to_index, eval_transform),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("[stage] building model", flush=True)
    print(f"Architecture: {args.architecture}")
    print(f"Pretrained backbone: {not args.no_pretrained}")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA is not available. Training will run on CPU.")

    model = create_model(args.architecture, len(class_names), args.freeze_backbone, not args.no_pretrained).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.learning_rate)

    best_accuracy = 0.0
    best_state = copy.deepcopy(model.state_dict())
    history = []
    training_started_at = time.time()

    print("[stage] training", flush=True)
    for epoch in range(1, args.epochs + 1):
        epoch_started_at = time.time()
        train_loss, train_accuracy = run_train_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
            epoch,
            args.epochs,
            args.log_every,
        )
        val_loss, val_accuracy = evaluate(model, val_loader, criterion, device)
        epoch_seconds = time.time() - epoch_started_at
        print(
            f"[epoch] {epoch}/{args.epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_accuracy:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_accuracy:.4f} "
            f"duration={format_duration(epoch_seconds)}",
            flush=True,
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": round(train_loss, 6),
                "train_accuracy": round(train_accuracy, 6),
                "val_loss": round(val_loss, 6),
                "val_accuracy": round(val_accuracy, 6),
                "seconds": round(epoch_seconds, 2),
            }
        )
        with metrics_path.open("a", encoding="utf-8") as metrics_file:
            metrics_file.write(
                json.dumps(
                    {
                        "event": "epoch",
                        "epoch": epoch,
                        "epochs": args.epochs,
                        "train_loss": round(train_loss, 6),
                        "train_accuracy": round(train_accuracy, 6),
                        "val_loss": round(val_loss, 6),
                        "val_accuracy": round(val_accuracy, 6),
                        "seconds": round(epoch_seconds, 2),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            best_state = copy.deepcopy(model.state_dict())
            print(f"[checkpoint] new best val_acc={best_accuracy:.4f}", flush=True)

    checkpoint_path = Path(args.checkpoint_path)
    if not checkpoint_path.is_absolute():
        checkpoint_path = PROJECT_ROOT / checkpoint_path
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": best_state,
            "class_names": class_names,
            "architecture": args.architecture,
            "best_val_accuracy": best_accuracy,
        },
        checkpoint_path,
    )

    metadata_path = Path(args.metadata_path)
    if not metadata_path.is_absolute():
        metadata_path = PROJECT_ROOT / metadata_path
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "architecture": args.architecture,
                "class_names": class_names,
                "best_val_accuracy": round(best_accuracy, 4),
                "dataset_dir": str(dataset_dir),
                "train_samples": len(train_samples),
                "val_samples": len(val_samples),
                "source_dataset": "Fashion Product Images",
                "pretrained_backbone": not args.no_pretrained,
                "history": history,
                "training_seconds": round(time.time() - training_started_at, 2),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("[stage] done", flush=True)
    print(f"Saved checkpoint: {checkpoint_path}")
    print(f"Saved metadata: {metadata_path}")
    print(f"Saved metrics log: {metrics_path}")
    print(f"Best validation accuracy: {best_accuracy:.4f}")


if __name__ == "__main__":
    main()
