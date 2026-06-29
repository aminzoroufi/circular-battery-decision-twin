from __future__ import annotations

import json
import copy
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
DATASET_DIR = PROJECT_ROOT / "data" / "images"
MODEL_DIR = PROJECT_ROOT / "backend" / "trained_models"
REPORT_DIR = PROJECT_ROOT / "outputs" / "model_evaluation"

sys.path.insert(0, str(BACKEND_DIR))

from cv_features import extract_features  # noqa: E402


CLASSES = ("cylindrical", "pouch", "prismatic")
RANDOM_STATE = 42


@dataclass(frozen=True)
class ModelSpec:
    name: str
    feature_set: str
    estimator: Pipeline
    rationale: str


def collect_dataset() -> tuple[list[Path], np.ndarray]:
    image_paths: list[Path] = []
    labels: list[str] = []
    for label in CLASSES:
        class_dir = DATASET_DIR / label
        if not class_dir.exists():
            raise FileNotFoundError(f"Missing class directory: {class_dir}")
        for path in sorted(class_dir.glob("*")):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                image_paths.append(path)
                labels.append(label)

    if not image_paths:
        raise RuntimeError(f"No images found under {DATASET_DIR}")
    return image_paths, np.asarray(labels)


def build_feature_matrix(image_paths: list[Path], feature_set: str) -> np.ndarray:
    return np.vstack([extract_features(path, feature_set) for path in image_paths])


def model_specs() -> list[ModelSpec]:
    return [
        ModelSpec(
            name="logistic_regression_color_shape",
            feature_set="color_shape",
            estimator=Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)),
                ]
            ),
            rationale="Fast interpretable baseline using color histograms, aspect ratio, and edge density.",
        ),
        ModelSpec(
            name="random_forest_color_shape",
            feature_set="color_shape",
            estimator=Pipeline(
                [
                    (
                        "classifier",
                        RandomForestClassifier(
                            n_estimators=300,
                            max_depth=None,
                            min_samples_leaf=2,
                            class_weight="balanced",
                            random_state=RANDOM_STATE,
                        ),
                    )
                ]
            ),
            rationale="Non-linear baseline for handcrafted color and shape features.",
        ),
        ModelSpec(
            name="linear_svm_hog",
            feature_set="hog",
            estimator=Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("classifier", SVC(kernel="linear", C=1.0, probability=True, class_weight="balanced", random_state=RANDOM_STATE)),
                ]
            ),
            rationale="Shape-focused classifier using HOG gradients and a linear support vector machine.",
        ),
        ModelSpec(
            name="rbf_svm_hybrid",
            feature_set="hybrid",
            estimator=Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("classifier", SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, class_weight="balanced", random_state=RANDOM_STATE)),
                ]
            ),
            rationale="Selected candidate for non-linear boundaries using both HOG and color/shape features.",
        ),
    ]


def evaluate_model(spec: ModelSpec, image_paths: list[Path], labels: np.ndarray) -> tuple[dict, Pipeline]:
    features = build_feature_matrix(image_paths, spec.feature_set)
    train_x, test_x, train_y, test_y = train_test_split(
        features,
        labels,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=labels,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_accuracy = cross_val_score(spec.estimator, features, labels, cv=cv, scoring="accuracy")
    cv_f1 = cross_val_score(spec.estimator, features, labels, cv=cv, scoring="f1_macro")

    estimator = copy.deepcopy(spec.estimator)
    estimator.fit(train_x, train_y)
    predictions = estimator.predict(test_x)
    test_accuracy = accuracy_score(test_y, predictions)
    test_f1 = f1_score(test_y, predictions, average="macro")

    report = {
        "name": spec.name,
        "feature_set": spec.feature_set,
        "rationale": spec.rationale,
        "cv_accuracy_mean": round(float(cv_accuracy.mean()), 4),
        "cv_accuracy_std": round(float(cv_accuracy.std()), 4),
        "cv_macro_f1_mean": round(float(cv_f1.mean()), 4),
        "cv_macro_f1_std": round(float(cv_f1.std()), 4),
        "holdout_accuracy": round(float(test_accuracy), 4),
        "holdout_macro_f1": round(float(test_f1), 4),
        "confusion_matrix": confusion_matrix(test_y, predictions, labels=list(CLASSES)).tolist(),
        "classification_report": classification_report(test_y, predictions, labels=list(CLASSES), output_dict=True, zero_division=0),
    }

    final_estimator = copy.deepcopy(spec.estimator)
    final_estimator.fit(features, labels)
    return report, final_estimator


def select_best(results: list[dict]) -> dict:
    return max(
        results,
        key=lambda item: (
            item["cv_accuracy_mean"],
            item["cv_macro_f1_mean"],
            item["holdout_accuracy"],
            item["holdout_macro_f1"],
        ),
    )


def main() -> None:
    image_paths, labels = collect_dataset()
    class_counts = {label: int((labels == label).sum()) for label in CLASSES}
    specs = model_specs()
    results = []
    final_estimators: dict[str, Pipeline] = {}

    for spec in specs:
        print(f"Training/evaluating {spec.name} ({spec.feature_set})")
        result, final_estimator = evaluate_model(spec, image_paths, labels)
        results.append(result)
        final_estimators[spec.name] = final_estimator

    best = select_best(results)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model_name": best["name"],
        "feature_set": best["feature_set"],
        "classes": list(CLASSES),
        "estimator": final_estimators[best["name"]],
        "trust_percentage": round(best["cv_accuracy_mean"] * 100.0, 2),
        "metrics": best,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    model_path = MODEL_DIR / "battery_type_classifier.joblib"
    joblib.dump(artifact, model_path)

    summary = {
        "generated_at": artifact["trained_at"],
        "dataset": {
            "path": str(DATASET_DIR.relative_to(PROJECT_ROOT)),
            "total_images": len(image_paths),
            "classes": list(CLASSES),
            "class_counts": class_counts,
            "label_source": "folder names are used only as ground-truth labels during evaluation; runtime prediction uses image pixels only.",
        },
        "selected_model": {
            "name": best["name"],
            "feature_set": best["feature_set"],
            "trust_percentage": artifact["trust_percentage"],
            "selection_rule": "highest mean 5-fold cross-validation accuracy, then macro F1 and holdout metrics as tie-breakers",
            "why_selected": best["rationale"],
            "model_path": str(model_path.relative_to(PROJECT_ROOT)),
        },
        "results": sorted(results, key=lambda item: item["cv_accuracy_mean"], reverse=True),
    }

    report_path = REPORT_DIR / "battery_type_model_comparison.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\nSelected model:", summary["selected_model"]["name"])
    print("Trust percentage:", f"{summary['selected_model']['trust_percentage']:.2f}%")
    print("Model saved to:", model_path)
    print("Report saved to:", report_path)


if __name__ == "__main__":
    main()
