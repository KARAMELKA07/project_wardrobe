from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import os
import random
import time
from collections import Counter
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

DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "processed" / "wardrobe_training" / "manifest.csv"
DEFAULT_METRICS_PATH = BACKEND_ROOT / "training_logs" / "wardrobe_training_metrics.jsonl"
DEFAULT_CHECKPOINT_PATH = BACKEND_ROOT / "model_artifacts" / "deepfashion_classifier.pt"
DEFAULT_METADATA_PATH = BACKEND_ROOT / "model_artifacts" / "deepfashion_classifier.metadata.json"


@dataclass(frozen=True)
class ManifestSample:
    image_path: Path
    label: str
    category: str
    source: str
    source_id: str
    split: str


class ManifestClassificationDataset(Dataset):
    def __init__(self, samples: list[ManifestSample], class_to_index: dict[str, int], transform):
        self.samples = samples
        self.class_to_index = class_to_index
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        image = Image.open(sample.image_path).convert("RGB")
        return self.transform(image), self.class_to_index[sample.label]


def resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved.resolve()


def read_manifest_samples(manifest_path: Path) -> list[ManifestSample]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    samples: list[ManifestSample] = []
    missing_images = 0
    with manifest_path.open("r", encoding="utf-8", errors="replace", newline="") as file_handle:
        reader = csv.DictReader(file_handle)
        for record in reader:
            image_path_value = (record.get("image_path") or "").strip()
            label = (record.get("label") or "").strip()
            split = (record.get("split") or "").strip()
            if not image_path_value or not label or split not in {"train", "val"}:
                continue

            image_path = Path(image_path_value)
            if not image_path.is_absolute():
                image_path = PROJECT_ROOT / image_path
            if not image_path.exists():
                missing_images += 1
                continue

            samples.append(
                ManifestSample(
                    image_path=image_path.resolve(),
                    label=label,
                    category=(record.get("category") or "").strip(),
                    source=(record.get("source") or "").strip(),
                    source_id=(record.get("source_id") or "").strip(),
                    split=split,
                )
            )

    if missing_images:
        print(f"[warn] skipped rows with missing image files: {missing_images}", flush=True)
    return samples


def filter_classes(
    samples: list[ManifestSample],
    min_samples_per_class: int,
    max_classes: int | None,
) -> list[ManifestSample]:
    counts = Counter(sample.label for sample in samples)
    labels = [label for label, count in counts.most_common() if count >= min_samples_per_class]
    if max_classes:
        labels = labels[:max_classes]
    allowed = set(labels)
    return [sample for sample in samples if sample.label in allowed]


def limit_split_samples(samples: list[ManifestSample], limit: int | None, seed: int) -> list[ManifestSample]:
    if not limit or len(samples) <= limit:
        return samples
    rng = random.Random(seed)
    limited = list(samples)
    rng.shuffle(limited)
    return limited[:limit]


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


def append_metric(metrics_path: Path, payload: dict) -> None:
    with metrics_path.open("a", encoding="utf-8") as metrics_file:
        metrics_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


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
    parser = argparse.ArgumentParser(description="Train Project Wardrobe classifier from a prepared manifest.")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--architecture", default="efficientnet_b0", choices=["efficientnet_b0", "resnet50"])
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-samples-per-class", type=int, default=30)
    parser.add_argument("--max-classes", type=int, default=None)
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--max-val-samples", type=int, default=None)
    parser.add_argument("--freeze-backbone", action="store_true")
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--log-every", type=int, default=25)
    parser.add_argument("--checkpoint-path", default=str(DEFAULT_CHECKPOINT_PATH))
    parser.add_argument("--metadata-path", default=str(DEFAULT_METADATA_PATH))
    parser.add_argument("--metrics-path", default=str(DEFAULT_METRICS_PATH))
    return parser.parse_args()


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    random.seed(args.seed)

    manifest_path = resolve_path(args.manifest_path)
    metrics_path = resolve_path(args.metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    print("[stage] reading manifest", flush=True)
    samples = read_manifest_samples(manifest_path)
    if not samples:
        raise SystemExit(f"No supported samples found in manifest: {manifest_path}")

    original_count = len(samples)
    samples = filter_classes(samples, args.min_samples_per_class, args.max_classes)
    if len(set(sample.label for sample in samples)) < 2:
        raise SystemExit("Not enough classes after filtering. Lower --min-samples-per-class or check the manifest.")

    train_samples = [sample for sample in samples if sample.split == "train"]
    val_samples = [sample for sample in samples if sample.split == "val"]
    train_samples = limit_split_samples(train_samples, args.max_train_samples, args.seed)
    val_samples = limit_split_samples(val_samples, args.max_val_samples, args.seed)
    if not train_samples or not val_samples:
        raise SystemExit("Manifest must contain both train and val samples after filtering.")

    class_names = sorted(set(sample.label for sample in samples))
    class_to_index = {label: index for index, label in enumerate(class_names)}
    source_counts = Counter(sample.source for sample in samples)
    label_counts = Counter(sample.label for sample in samples)

    print("[stage] dataset summary", flush=True)
    print(f"Manifest: {manifest_path}")
    print(f"Supported samples before filtering: {original_count}")
    print(f"Samples after filtering: {len(samples)}")
    print(f"Train samples: {len(train_samples)}")
    print(f"Validation samples: {len(val_samples)}")
    print(f"Classes ({len(class_names)}): {', '.join(class_names)}")
    print(f"Sources: {dict(source_counts)}")
    print(f"Metrics log: {metrics_path}")
    print("Top class counts:")
    for label, count in label_counts.most_common(20):
        print(f"  {label}: {count}")

    metrics_path.write_text(
        json.dumps(
            {
                "event": "start",
                "manifest_path": str(manifest_path),
                "architecture": args.architecture,
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "min_samples_per_class": args.min_samples_per_class,
                "max_classes": args.max_classes,
                "train_samples": len(train_samples),
                "val_samples": len(val_samples),
                "class_names": class_names,
                "source_counts": dict(source_counts),
                "label_counts": dict(label_counts.most_common()),
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
        ManifestClassificationDataset(train_samples, class_to_index, train_transform),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
    )
    val_loader = DataLoader(
        ManifestClassificationDataset(val_samples, class_to_index, eval_transform),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("[stage] building model", flush=True)
    print(f"Architecture: {args.architecture}")
    print(f"Pretrained backbone: {not args.no_pretrained}")
    print(f"Freeze backbone: {args.freeze_backbone}")
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
        is_best = val_accuracy > best_accuracy
        if is_best:
            best_accuracy = val_accuracy
            best_state = copy.deepcopy(model.state_dict())

        epoch_metrics = {
            "event": "epoch",
            "epoch": epoch,
            "epochs": args.epochs,
            "train_loss": round(train_loss, 6),
            "train_accuracy": round(train_accuracy, 6),
            "val_loss": round(val_loss, 6),
            "val_accuracy": round(val_accuracy, 6),
            "best_val_accuracy": round(best_accuracy, 6),
            "is_best": is_best,
            "seconds": round(epoch_seconds, 2),
        }
        history.append(epoch_metrics)
        append_metric(metrics_path, epoch_metrics)

        print(
            f"[epoch] {epoch}/{args.epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_accuracy:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_accuracy:.4f} "
            f"best_val_acc={best_accuracy:.4f} "
            f"duration={format_duration(epoch_seconds)}",
            flush=True,
        )
        if is_best:
            print(f"[checkpoint] new best val_acc={best_accuracy:.4f}", flush=True)

    checkpoint_path = resolve_path(args.checkpoint_path)
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

    metadata_path = resolve_path(args.metadata_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "architecture": args.architecture,
                "class_names": class_names,
                "best_val_accuracy": round(best_accuracy, 4),
                "manifest_path": str(manifest_path),
                "train_samples": len(train_samples),
                "val_samples": len(val_samples),
                "source_dataset": "Wardrobe manifest classifier (Zappos, iFashion-ready)",
                "source_counts": dict(source_counts),
                "label_counts": dict(label_counts.most_common()),
                "pretrained_backbone": not args.no_pretrained,
                "freeze_backbone": args.freeze_backbone,
                "history": history,
                "training_seconds": round(time.time() - training_started_at, 2),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    append_metric(
        metrics_path,
        {
            "event": "complete",
            "best_val_accuracy": round(best_accuracy, 6),
            "checkpoint_path": str(checkpoint_path),
            "metadata_path": str(metadata_path),
            "metrics_path": str(metrics_path),
            "seconds": round(time.time() - training_started_at, 2),
        },
    )

    print("[stage] done", flush=True)
    print(f"Saved checkpoint: {checkpoint_path}")
    print(f"Saved metadata: {metadata_path}")
    print(f"Saved metrics log: {metrics_path}")
    print(f"Best validation accuracy: {best_accuracy:.4f}")


if __name__ == "__main__":
    main()
