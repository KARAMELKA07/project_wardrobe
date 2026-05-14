from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TORCH_HOME = PROJECT_ROOT / ".torch-cache"

os.environ.setdefault("TORCH_HOME", str(DEFAULT_TORCH_HOME))

import sys

sys.path.insert(0, str(PROJECT_ROOT))

from app.services.deepfashion_dataset import (
    build_class_names,
    build_class_to_index,
    load_supported_samples,
    resolve_dataset_dir,
    validate_dataset_dir,
)


class DeepFashionClassificationDataset(Dataset):
    def __init__(self, samples, class_to_index, transform):
        self.samples = samples
        self.class_to_index = class_to_index
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        image = Image.open(sample.image_path).convert("RGB")
        if sample.bbox:
            x1, y1, x2, y2 = sample.bbox
            image = image.crop((x1, y1, x2, y2))
        tensor = self.transform(image)
        label = self.class_to_index[sample.project_subcategory]
        return tensor, label


def create_model(architecture, num_classes):
    if architecture == "efficientnet_b0":
        model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
        return model

    if architecture == "resnet50":
        model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model

    raise ValueError(f"Unsupported architecture: {architecture}")


def run_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * labels.size(0)
        total_correct += (logits.argmax(dim=1) == labels).sum().item()
        total_samples += labels.size(0)

    return total_loss / max(total_samples, 1), total_correct / max(total_samples, 1)


def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)

            total_loss += loss.item() * labels.size(0)
            total_correct += (logits.argmax(dim=1) == labels).sum().item()
            total_samples += labels.size(0)

    return total_loss / max(total_samples, 1), total_correct / max(total_samples, 1)


def parse_args():
    parser = argparse.ArgumentParser(description="Train a DeepFashion-based clothing classifier for Project Wardrobe.")
    parser.add_argument(
        "--dataset-dir",
        default=str(PROJECT_ROOT / "Category and Attribute Prediction Benchmark"),
        help="Path to the DeepFashion Category and Attribute Prediction Benchmark directory.",
    )
    parser.add_argument("--architecture", default="efficientnet_b0", choices=["efficientnet_b0", "resnet50"])
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument(
        "--checkpoint-path",
        default=str(PROJECT_ROOT / "model_artifacts" / "deepfashion_classifier.pt"),
    )
    parser.add_argument(
        "--metadata-path",
        default=str(PROJECT_ROOT / "model_artifacts" / "deepfashion_classifier.metadata.json"),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    dataset_status = validate_dataset_dir(args.dataset_dir)
    if not dataset_status["has_images"]:
        raise SystemExit(
            "В датасете не найдены изображения. Скачайте и распакуйте 'Clothes Images' в папку Img/img или img."
        )

    dataset_dir = resolve_dataset_dir(args.dataset_dir)
    class_names = build_class_names()
    class_to_index = build_class_to_index()

    train_samples = load_supported_samples(dataset_dir, split="train")
    val_samples = load_supported_samples(dataset_dir, split="val")

    if not train_samples or not val_samples:
        raise SystemExit("Не удалось собрать обучающую и валидационную выборку из DeepFashion.")

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

    train_dataset = DeepFashionClassificationDataset(train_samples, class_to_index, train_transform)
    val_dataset = DeepFashionClassificationDataset(val_samples, class_to_index, eval_transform)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = create_model(args.architecture, len(class_names)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    best_accuracy = 0.0
    best_state = copy.deepcopy(model.state_dict())

    print(f"Dataset: {dataset_dir}")
    print(f"Train samples: {len(train_samples)}")
    print(f"Validation samples: {len(val_samples)}")
    print(f"Classes: {', '.join(class_names)}")
    print(f"Device: {device}")

    for epoch in range(1, args.epochs + 1):
        train_loss, train_accuracy = run_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_accuracy = evaluate(model, val_loader, criterion, device)
        print(
            f"Epoch {epoch}/{args.epochs} | "
            f"train_loss={train_loss:.4f} train_acc={train_accuracy:.4f} | "
            f"val_loss={val_loss:.4f} val_acc={val_accuracy:.4f}"
        )

        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            best_state = copy.deepcopy(model.state_dict())

    checkpoint_path = Path(args.checkpoint_path)
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
                "source_dataset": "DeepFashion Category and Attribute Prediction Benchmark",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Saved checkpoint: {checkpoint_path}")
    print(f"Saved metadata: {metadata_path}")
    print(f"Best validation accuracy: {best_accuracy:.4f}")


if __name__ == "__main__":
    main()
