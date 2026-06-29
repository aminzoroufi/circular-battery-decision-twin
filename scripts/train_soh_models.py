from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVR


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HEALTH_CSV = PROJECT_ROOT / "data" / "nasa_health" / "battery_health_lookup.csv"
MODEL_DIR = PROJECT_ROOT / "backend" / "trained_models"
MODEL_PATH = MODEL_DIR / "soh_predictor.joblib"
EVAL_DIR = PROJECT_ROOT / "outputs" / "model_evaluation"
EVAL_PATH = EVAL_DIR / "soh_model_comparison.json"
FEATURE_COLUMNS = [
    "cycle_count",
    "temperature_c",
    "internal_resistance_mohm",
    "voltage",
    "battery_type",
]
NUMERIC_FEATURES = ["cycle_count", "temperature_c", "internal_resistance_mohm", "voltage"]
CATEGORICAL_FEATURES = ["battery_type"]


def load_training_frame() -> pd.DataFrame:
    if not HEALTH_CSV.exists():
        raise FileNotFoundError(
            f"NASA-derived health table not found: {HEALTH_CSV}. "
            "Run scripts/build_real_dataset.py to download and extract the NASA battery data first."
        )

    df = pd.read_csv(HEALTH_CSV)
    required = {
        "cycle_count",
        "rated_capacity_ah",
        "measured_capacity_ah",
        "voltage",
        "temperature_c",
        "internal_resistance_mohm",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Health table is missing required columns: {sorted(missing)}")

    df = df.copy()
    df["battery_type"] = "cylindrical"
    df["soh_percent"] = (df["measured_capacity_ah"] / df["rated_capacity_ah"]) * 100.0
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=FEATURE_COLUMNS + ["soh_percent"])
    df = df[
        (df["cycle_count"] >= 0)
        & (df["temperature_c"].between(-20, 90))
        & (df["internal_resistance_mohm"].between(1, 1000))
        & (df["voltage"].between(1.5, 5.0))
        & (df["soh_percent"].between(0, 120))
    ]
    if len(df) < 50:
        raise ValueError(f"Not enough clean SOH rows for training: {len(df)}")
    return df


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", NUMERIC_FEATURES),
            ("battery_type", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )


def make_scaled_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("battery_type", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )


def candidate_models() -> dict[str, Pipeline]:
    models: dict[str, Pipeline] = {
        "LinearRegression": Pipeline(
            [
                ("preprocess", make_preprocessor()),
                ("model", LinearRegression()),
            ]
        ),
        "RandomForestRegressor": Pipeline(
            [
                ("preprocess", make_preprocessor()),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=400,
                        min_samples_leaf=2,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "GradientBoostingRegressor": Pipeline(
            [
                ("preprocess", make_preprocessor()),
                (
                    "model",
                    GradientBoostingRegressor(
                        n_estimators=350,
                        learning_rate=0.035,
                        max_depth=3,
                        random_state=42,
                    ),
                ),
            ]
        ),
        "SupportVectorRegression": Pipeline(
            [
                ("preprocess", make_scaled_preprocessor()),
                ("model", SVR(C=80.0, epsilon=0.8, gamma="scale")),
            ]
        ),
        "MLPRegressor": Pipeline(
            [
                ("preprocess", make_scaled_preprocessor()),
                (
                    "model",
                    MLPRegressor(
                        hidden_layer_sizes=(64, 32),
                        activation="relu",
                        alpha=0.0005,
                        learning_rate_init=0.003,
                        max_iter=1500,
                        random_state=42,
                        early_stopping=True,
                    ),
                ),
            ]
        ),
    }

    try:
        from xgboost import XGBRegressor

        models["XGBRegressor"] = Pipeline(
            [
                ("preprocess", make_preprocessor()),
                (
                    "model",
                    XGBRegressor(
                        n_estimators=450,
                        max_depth=3,
                        learning_rate=0.035,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        objective="reg:squarederror",
                        random_state=42,
                    ),
                ),
            ]
        )
    except Exception:
        pass

    try:
        from lightgbm import LGBMRegressor

        models["LGBMRegressor"] = Pipeline(
            [
                ("preprocess", make_preprocessor()),
                (
                    "model",
                    LGBMRegressor(
                        n_estimators=450,
                        learning_rate=0.035,
                        num_leaves=24,
                        random_state=42,
                    ),
                ),
            ]
        )
    except Exception:
        pass

    return models


def evaluate_model(name: str, model: Pipeline, x_train: pd.DataFrame, x_test: pd.DataFrame, y_train: pd.Series, y_test: pd.Series) -> dict[str, Any]:
    model.fit(x_train, y_train)
    predictions = np.asarray(model.predict(x_test), dtype=float)
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    mae = float(mean_absolute_error(y_test, predictions))
    mape = float(np.mean(np.abs((y_test.to_numpy() - predictions) / np.maximum(np.abs(y_test.to_numpy()), 1e-6))) * 100.0)
    r2 = float(r2_score(y_test, predictions))
    residual_std = float(np.std(y_test.to_numpy() - predictions))
    return {
        "name": name,
        "model": model,
        "metrics": {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "mape": round(mape, 4),
            "residual_std": round(residual_std, 4),
        },
    }


def main() -> None:
    df = load_training_frame()
    x = df[FEATURE_COLUMNS]
    y = df["soh_percent"]
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        shuffle=True,
    )

    results = []
    for name, model in candidate_models().items():
        print(f"Training {name}...")
        results.append(evaluate_model(name, model, x_train, x_test, y_train, y_test))

    results.sort(key=lambda item: (item["metrics"]["rmse"], item["metrics"]["mae"]))
    best = results[0]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": best["model"],
        "model_name": best["name"],
        "feature_columns": FEATURE_COLUMNS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target": "soh_percent",
        "metrics": best["metrics"],
        "all_model_metrics": {item["name"]: item["metrics"] for item in results},
        "residual_std": best["metrics"]["residual_std"],
        "dataset": {
            "selected_dataset": "NASA PCoE Li-ion Battery Aging Dataset",
            "local_table": str(HEALTH_CSV.relative_to(PROJECT_ROOT)),
            "source_url": "https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip",
            "rows_total": int(len(df)),
            "rows_train": int(len(x_train)),
            "rows_test": int(len(x_test)),
            "battery_sources": sorted(df["battery_source_id"].astype(str).unique().tolist())
            if "battery_source_id" in df.columns
            else [],
            "battery_type_note": "NASA rows are cylindrical cells; pouch and prismatic API inputs are accepted but require future aging data for type-specific calibration.",
        },
    }
    joblib.dump(artifact, MODEL_PATH)

    report = {
        "best_model": best["name"],
        "best_metrics": best["metrics"],
        "models": artifact["all_model_metrics"],
        "feature_columns": FEATURE_COLUMNS,
        "dataset": artifact["dataset"],
    }
    EVAL_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved SOH model: {MODEL_PATH}")
    print(f"Saved comparison report: {EVAL_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SOH training failed: {exc}", file=sys.stderr)
        raise
