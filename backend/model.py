from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import joblib
import numpy as np
from PIL import Image, ImageStat

from cv_features import extract_features, open_rgb_image

CLASSES = ("cylindrical", "pouch", "prismatic")
MODEL_PATH = Path(__file__).resolve().parent / "trained_models" / "battery_type_classifier.joblib"
_MODEL_ARTIFACT: dict | None = None


def _open_image(image_path_or_bytes: str | Path | bytes | BinaryIO) -> Image.Image:
    return open_rgb_image(image_path_or_bytes)


def _load_model_artifact() -> dict | None:
    global _MODEL_ARTIFACT
    if _MODEL_ARTIFACT is not None:
        return _MODEL_ARTIFACT
    if not MODEL_PATH.exists():
        return None
    _MODEL_ARTIFACT = joblib.load(MODEL_PATH)
    return _MODEL_ARTIFACT


def _feature_classifier(image: Image.Image) -> tuple[str, float]:
    """Tiny deterministic fallback classifier for demos without a trained model."""
    width, height = image.size
    aspect = width / max(height, 1)
    mean_r, mean_g, mean_b = ImageStat.Stat(image).mean[:3]
    arr = np.asarray(image.resize((32, 32)), dtype=np.float32)
    contrast = float(arr.std())

    if aspect > 1.45:
        return "pouch", min(0.86, 0.62 + (aspect - 1.45) * 0.12)
    if aspect < 0.78:
        return "cylindrical", min(0.86, 0.62 + (0.78 - aspect) * 0.18)
    if mean_b > mean_r + 18:
        return "prismatic", 0.82
    if mean_g > mean_r + 12:
        return "pouch", 0.78
    if contrast > 55:
        return "cylindrical", 0.74
    return "unknown", 0.35


def classify_battery_image(
    image_path_or_bytes: str | Path | bytes | BinaryIO,
    filename: str | None = None,
) -> dict:
    """
    Classify a battery as cylindrical, pouch, prismatic, or unknown.

    Runtime prediction uses image pixels only. File and folder names are ignored
    because they can leak class labels in research datasets.
    """
    try:
        artifact = _load_model_artifact()
        if artifact is not None:
            feature_set = artifact.get("feature_set", "hybrid")
            estimator = artifact["estimator"]
            features = extract_features(image_path_or_bytes, feature_set).reshape(1, -1)
            predicted = str(estimator.predict(features)[0])

            confidence = 0.0
            probabilities = None
            if hasattr(estimator, "predict_proba"):
                probabilities = estimator.predict_proba(features)[0]
                confidence = float(np.max(probabilities))
            else:
                confidence = float(artifact.get("trust_percentage", 0.0)) / 100.0

            response = {
                "detected_type": predicted if predicted in CLASSES else "unknown",
                "confidence": round(max(0.0, min(1.0, confidence)), 3),
                "model_name": artifact.get("model_name", "trained_cv_model"),
                "model_trust_percentage": artifact.get("trust_percentage"),
                "classification_method": "trained_computer_vision",
            }
            if probabilities is not None:
                classes = [str(item) for item in artifact.get("classes", getattr(estimator, "classes_", []))]
                response["class_probabilities"] = {
                    label: round(float(prob), 3)
                    for label, prob in zip(classes, probabilities)
                }
            return response

        image = _open_image(image_path_or_bytes)
        detected_type, confidence = _feature_classifier(image)
        return {
            "detected_type": detected_type,
            "confidence": round(float(confidence), 3),
            "classification_method": "image_feature_fallback",
        }
    except Exception:
        return {"detected_type": "unknown", "confidence": 0.0, "classification_method": "failed"}
