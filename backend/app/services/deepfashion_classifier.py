from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CHECKPOINT_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "deepfashion_classifier.pt"
DEFAULT_METADATA_PATH = PROJECT_ROOT / "backend" / "model_artifacts" / "deepfashion_classifier.metadata.json"


def _resolve_runtime_path(path_value, default_path):
    raw_path = Path(path_value or default_path)
    if not raw_path.is_absolute():
        raw_path = PROJECT_ROOT / raw_path
    return raw_path.resolve()


class DeepFashionLocalClassifier:
    def __init__(self):
        self.enabled = os.getenv("FASHION_AI_ENABLED", "true").lower() == "true"
        self.checkpoint_path = _resolve_runtime_path(
            os.getenv("DEEPFASHION_CHECKPOINT_PATH"),
            DEFAULT_CHECKPOINT_PATH,
        )
        self.metadata_path = _resolve_runtime_path(
            os.getenv("DEEPFASHION_METADATA_PATH"),
            DEFAULT_METADATA_PATH,
        )
        self._loaded = False
        self._model = None
        self._class_names: list[str] = []
        self._architecture = "efficientnet_b0"
        self._preprocess = None

    def predict(self, image_bytes):
        if not self.enabled:
            return self._empty_result("Локальная DeepFashion-модель отключена в настройках.", model=None)

        if not self.checkpoint_path.exists():
            return self._empty_result(
                "Локальная DeepFashion-модель не найдена. Пока используется резервный классификатор.",
                model="deepfashion-local",
            )

        try:
            self._ensure_loaded()
        except Exception:
            return self._empty_result(
                "Не удалось загрузить локальную DeepFashion-модель. Пока используется резервный классификатор.",
                model="deepfashion-local",
            )

        try:
            import torch
            from PIL import Image
        except ImportError:
            return self._empty_result(
                "Для локальной DeepFashion-модели не хватает зависимостей torch, torchvision или Pillow.",
                model="deepfashion-local",
            )

        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            tensor = self._preprocess(image).unsqueeze(0)
            with torch.no_grad():
                logits = self._model(tensor)
                probabilities = torch.softmax(logits, dim=1)[0]
        except Exception:
            return self._empty_result(
                "Локальная DeepFashion-модель не смогла обработать изображение. Используется резервный классификатор.",
                model="deepfashion-local",
            )

        sorted_indices = torch.argsort(probabilities, descending=True).tolist()
        top_predictions = []
        for index in sorted_indices[:5]:
            if index >= len(self._class_names):
                continue
            top_predictions.append(
                {
                    "subcategory": self._class_names[index],
                    "score": round(float(probabilities[index].item()), 4),
                }
            )

        best_prediction = top_predictions[0] if top_predictions else None
        return {
            "subcategory": best_prediction["subcategory"] if best_prediction else None,
            "confidence": best_prediction["score"] if best_prediction else None,
            "top_predictions": top_predictions,
            "warnings": [],
            "model": f"deepfashion-local:{self._architecture}",
        }

    def _ensure_loaded(self):
        if self._loaded:
            return

        try:
            import torch
            from torchvision import models, transforms
        except ImportError as error:
            raise RuntimeError("Missing deepfashion classifier dependencies") from error

        metadata = self._load_metadata()
        checkpoint_payload = torch.load(self.checkpoint_path, map_location="cpu")

        if isinstance(checkpoint_payload, dict) and "state_dict" in checkpoint_payload:
            state_dict = checkpoint_payload["state_dict"]
            class_names = checkpoint_payload.get("class_names") or metadata.get("class_names")
            architecture = checkpoint_payload.get("architecture") or metadata.get("architecture") or "efficientnet_b0"
        else:
            state_dict = checkpoint_payload
            class_names = metadata.get("class_names")
            architecture = metadata.get("architecture") or "efficientnet_b0"

        if not class_names:
            raise RuntimeError("DeepFashion classifier metadata is missing class_names")

        self._class_names = list(class_names)
        self._architecture = architecture
        self._model = self._build_model(models, architecture, len(self._class_names))
        self._model.load_state_dict(state_dict)
        self._model.eval()
        self._preprocess = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )
        self._loaded = True

    def _load_metadata(self):
        if not self.metadata_path.exists():
            return {}
        with self.metadata_path.open("r", encoding="utf-8") as metadata_file:
            return json.load(metadata_file)

    def _build_model(self, models, architecture, num_classes):
        import torch

        if architecture == "efficientnet_b0":
            model = models.efficientnet_b0(weights=None)
            in_features = model.classifier[1].in_features
            model.classifier[1] = torch.nn.Linear(in_features, num_classes)
            return model

        if architecture == "resnet50":
            model = models.resnet50(weights=None)
            in_features = model.fc.in_features
            model.fc = torch.nn.Linear(in_features, num_classes)
            return model

        raise RuntimeError(f"Unsupported DeepFashion architecture: {architecture}")

    def _empty_result(self, warning_message, model):
        return {
            "subcategory": None,
            "confidence": None,
            "top_predictions": [],
            "warnings": [warning_message],
            "model": model,
        }
