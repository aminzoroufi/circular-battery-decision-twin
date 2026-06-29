from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

try:
    from config import PROJECT_ROOT
except ModuleNotFoundError:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]


MODEL_PATH = PROJECT_ROOT / "backend" / "trained_models" / "soh_predictor.joblib"
VALID_BATTERY_TYPES = {"cylindrical", "pouch", "prismatic"}
DECISION_TO_BIN = {
    "reuse": "reuse_bin",
    "remanufacture": "remanufacture_bin",
    "recycle": "recycle_bin",
    "quarantine": "quarantine_bin",
}


@dataclass(frozen=True)
class BatteryHealthInput:
    battery_id: str
    battery_type: str
    cycle_count: int
    temperature: float
    resistance: float
    voltage: float


def model_exists() -> bool:
    return MODEL_PATH.exists()


def load_model_artifact(path: Path = MODEL_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"SOH model artifact not found at {path}. Run scripts/train_soh_models.py first."
        )
    artifact = joblib.load(path)
    required = {"model", "model_name", "feature_columns", "metrics"}
    missing = required.difference(artifact)
    if missing:
        raise ValueError(f"SOH model artifact is missing keys: {sorted(missing)}")
    return artifact


def normalize_battery_type(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"cyl", "cylinder", "cylindrical_cell"}:
        return "cylindrical"
    if normalized in {"po", "pouch_cell"}:
        return "pouch"
    if normalized in {"pri", "prism", "prismatic_cell"}:
        return "prismatic"
    return normalized or "unknown"


def validate_health_input(payload: dict[str, Any]) -> tuple[BatteryHealthInput | None, list[str]]:
    flags: list[str] = []
    battery_id = str(payload.get("battery_id") or "").strip() or "BAT_UNKNOWN"
    battery_type = normalize_battery_type(payload.get("battery_type") or payload.get("detected_shape"))

    if battery_type not in VALID_BATTERY_TYPES:
        flags.append("unknown_battery_type")

    cycle_count = _coerce_int(payload.get("cycle_count"))
    temperature = _coerce_float(payload.get("temperature", payload.get("temperature_c")))
    voltage = _coerce_float(payload.get("voltage"))
    resistance = _coerce_float(payload.get("resistance"))
    if resistance is None:
        resistance_mohm = _coerce_float(payload.get("internal_resistance_mohm"))
        if resistance_mohm is not None:
            resistance = resistance_mohm / 1000.0

    if cycle_count is None:
        flags.append("missing_cycle_count")
    if temperature is None:
        flags.append("missing_temperature")
    if resistance is None:
        flags.append("missing_resistance")
    if voltage is None:
        flags.append("missing_voltage")

    if flags:
        return None, flags

    assert cycle_count is not None
    assert temperature is not None
    assert resistance is not None
    assert voltage is not None

    if cycle_count < 0 or cycle_count > 5000:
        flags.append("abnormal_cycle_count")
    if temperature < -20.0 or temperature > 90.0:
        flags.append("abnormal_temperature")
    if resistance <= 0.0 or resistance > 1.0:
        flags.append("abnormal_resistance")
    if voltage < 1.5 or voltage > 5.0:
        flags.append("abnormal_voltage")

    health_input = BatteryHealthInput(
        battery_id=battery_id,
        battery_type=battery_type,
        cycle_count=int(cycle_count),
        temperature=float(temperature),
        resistance=float(resistance),
        voltage=float(voltage),
    )
    return health_input, flags


def predict_soh_and_decision(payload: dict[str, Any], artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    health_input, validation_flags = validate_health_input(payload)
    if health_input is None:
        return _quarantine_response(payload, validation_flags, predicted_soh=None)

    safety_flags = validation_flags + safety_flags_for(health_input)
    predicted_soh: float | None = None
    confidence = 0.0
    error_estimate = None
    model_name = "unavailable"

    if not validation_flags:
        artifact = artifact or load_model_artifact()
        row = pd.DataFrame(
            [
                {
                    "cycle_count": health_input.cycle_count,
                    "temperature_c": health_input.temperature,
                    "internal_resistance_mohm": health_input.resistance * 1000.0,
                    "voltage": health_input.voltage,
                    "battery_type": health_input.battery_type,
                }
            ]
        )
        raw_prediction = float(np.ravel(artifact["model"].predict(row))[0])
        predicted_soh = round(float(np.clip(raw_prediction, 0.0, 110.0)), 2)
        model_name = str(artifact.get("model_name", "trained_soh_model"))
        error_estimate = round(float(artifact.get("residual_std", 0.0)), 2)
        confidence = round(max(0.0, min(1.0, 1.0 - (error_estimate / 40.0))), 3)

    rex_category = decide_rex(predicted_soh, safety_flags)
    risk_score = risk_score_for(predicted_soh, health_input, safety_flags)
    response = {
        "battery_id": health_input.battery_id,
        "battery_type": health_input.battery_type,
        "cycle_count": health_input.cycle_count,
        "temperature": round(health_input.temperature, 3),
        "temperature_c": round(health_input.temperature, 3),
        "resistance": round(health_input.resistance, 6),
        "internal_resistance_mohm": round(health_input.resistance * 1000.0, 3),
        "voltage": round(health_input.voltage, 3),
        "predicted_soh": predicted_soh,
        "soh": round(predicted_soh / 100.0, 4) if predicted_soh is not None else 0.0,
        "confidence": confidence,
        "error_estimate_percent": error_estimate,
        "model_used": model_name,
        "model_name": model_name,
        "rex_category": rex_category,
        "decision_category": rex_category,
        "ai_decision": rex_category,
        "final_decision": rex_category,
        "target_bin": DECISION_TO_BIN[rex_category],
        "risk_score": risk_score,
        "risk_level": risk_level_from_score(risk_score),
        "manual_review_required": rex_category == "quarantine",
        "safety_flags": safety_flags,
        "reason": reason_for(predicted_soh, rex_category, safety_flags),
    }
    return response


def safety_flags_for(value: BatteryHealthInput) -> list[str]:
    flags: list[str] = []
    if value.temperature >= 60.0:
        flags.append("high_temperature")
    if value.resistance >= 0.18:
        flags.append("high_internal_resistance")
    if value.voltage < 2.5 or value.voltage > 4.3:
        flags.append("abnormal_voltage")
    return flags


def decide_rex(predicted_soh: float | None, flags: list[str]) -> str:
    if flags or predicted_soh is None:
        return "quarantine"
    if predicted_soh >= 80.0:
        return "reuse"
    if predicted_soh >= 60.0:
        return "remanufacture"
    if predicted_soh >= 30.0:
        return "recycle"
    return "quarantine"


def risk_score_for(predicted_soh: float | None, value: BatteryHealthInput, flags: list[str]) -> int:
    if predicted_soh is None:
        return 100
    risk = max(0.0, 100.0 - predicted_soh)
    if value.temperature >= 45.0:
        risk += 15.0
    if value.temperature >= 60.0:
        risk += 35.0
    if value.resistance >= 0.12:
        risk += 10.0
    if value.resistance >= 0.18:
        risk += 30.0
    if value.voltage < 3.0 or value.voltage > 4.2:
        risk += 10.0
    if flags:
        risk += 25.0
    return int(max(0, min(100, round(risk))))


def risk_level_from_score(risk_score: int) -> str:
    if risk_score <= 30:
        return "low"
    if risk_score <= 60:
        return "medium"
    if risk_score <= 80:
        return "high"
    return "critical"


def reason_for(predicted_soh: float | None, decision: str, flags: list[str]) -> str:
    if flags:
        return "Safety validation routed this battery to quarantine: " + ", ".join(flags) + "."
    if predicted_soh is None:
        return "SOH could not be predicted because required health data was missing or invalid."
    if decision == "reuse":
        return "Predicted SOH is at least 80%, so the battery is suitable for reuse."
    if decision == "remanufacture":
        return "Predicted SOH is between 60% and 80%, so remanufacturing is recommended."
    if decision == "recycle":
        return "Predicted SOH is between 30% and 60%, so material recycling is recommended."
    return "Predicted SOH is below 30%, so quarantine and manual safety review are required."


def _quarantine_response(payload: dict[str, Any], flags: list[str], predicted_soh: float | None) -> dict[str, Any]:
    battery_type = normalize_battery_type(payload.get("battery_type") or payload.get("detected_shape"))
    battery_id = str(payload.get("battery_id") or "").strip() or "BAT_UNKNOWN"
    return {
        "battery_id": battery_id,
        "battery_type": battery_type,
        "cycle_count": payload.get("cycle_count"),
        "temperature": payload.get("temperature", payload.get("temperature_c")),
        "temperature_c": payload.get("temperature", payload.get("temperature_c")),
        "resistance": payload.get("resistance"),
        "internal_resistance_mohm": payload.get("internal_resistance_mohm"),
        "voltage": payload.get("voltage"),
        "predicted_soh": predicted_soh,
        "soh": 0.0,
        "confidence": 0.0,
        "error_estimate_percent": None,
        "model_used": "validation",
        "model_name": "validation",
        "rex_category": "quarantine",
        "decision_category": "quarantine",
        "ai_decision": "quarantine",
        "final_decision": "quarantine",
        "target_bin": DECISION_TO_BIN["quarantine"],
        "risk_score": 100,
        "risk_level": "critical",
        "manual_review_required": True,
        "safety_flags": flags,
        "reason": reason_for(predicted_soh, "quarantine", flags),
    }


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return number


def _coerce_int(value: Any) -> int | None:
    number = _coerce_float(value)
    if number is None:
        return None
    return int(round(number))
