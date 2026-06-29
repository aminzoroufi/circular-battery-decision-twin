from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from config import INSPECTION_LOG_PATH, LATEST_DECISION_PATH, ensure_runtime_dirs


LOG_COLUMNS = [
    "timestamp",
    "battery_id",
    "image_id",
    "detected_shape",
    "detected_type",
    "decision_category",
    "confidence",
    "uncertainty",
    "soh",
    "temperature_c",
    "cycle_count",
    "internal_resistance_mohm",
    "voltage",
    "predicted_soh",
    "soh_model_used",
    "soh_confidence",
    "soh_error_estimate_percent",
    "risk_score",
    "risk_level",
    "policy_mode",
    "confidence_threshold",
    "reuse_soh_threshold",
    "conveyor_speed",
    "robot_mode",
    "ai_decision",
    "operator_decision",
    "final_decision",
    "target_bin",
    "manual_review_required",
    "reason",
    "original_image_filename",
    "received_image_filename",
    "received_image_path",
    "received_image_url",
    "features_json",
    "processing_time_ms",
]


def read_log() -> pd.DataFrame:
    if not INSPECTION_LOG_PATH.exists():
        return pd.DataFrame(columns=LOG_COLUMNS)
    try:
        return _normalize_log_columns(pd.read_csv(INSPECTION_LOG_PATH))
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=LOG_COLUMNS)


def _normalize_log_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in LOG_COLUMNS:
        if column not in df.columns:
            df[column] = None
    ordered_columns = LOG_COLUMNS + [column for column in df.columns if column not in LOG_COLUMNS]
    return df[ordered_columns]


def _write_log_atomic(df: pd.DataFrame) -> None:
    temp_path = INSPECTION_LOG_PATH.with_suffix(".csv.tmp")
    df.to_csv(temp_path, index=False)
    temp_path.replace(INSPECTION_LOG_PATH)


def append_inspection(record: dict) -> None:
    ensure_runtime_dirs()
    row = {column: record.get(column) for column in LOG_COLUMNS}
    existing = read_log()
    df = pd.concat([existing, pd.DataFrame([row], columns=LOG_COLUMNS)], ignore_index=True)
    _write_log_atomic(_normalize_log_columns(df))
    LATEST_DECISION_PATH.write_text(json.dumps(record, indent=2), encoding="utf-8")


def update_override(
    *,
    battery_id: str,
    operator_decision: str,
    override_reason: str,
    target_bin: str,
) -> dict:
    df = read_log()
    if df.empty or battery_id not in set(df["battery_id"].astype(str)):
        raise KeyError(f"No inspection record found for {battery_id}")

    for column in ["operator_decision", "decision_category", "final_decision", "target_bin", "reason"]:
        if column in df.columns:
            df[column] = df[column].astype("object")

    index = df.index[df["battery_id"].astype(str) == battery_id][-1]
    ai_decision = str(df.at[index, "ai_decision"])
    df.at[index, "operator_decision"] = operator_decision
    if "decision_category" in df.columns:
        df.at[index, "decision_category"] = operator_decision
    df.at[index, "final_decision"] = operator_decision
    df.at[index, "target_bin"] = target_bin
    df.at[index, "manual_review_required"] = operator_decision == "quarantine"
    df.at[index, "reason"] = f"Operator override: {override_reason}"
    _write_log_atomic(df)

    updated = df.loc[index].fillna("").to_dict()
    LATEST_DECISION_PATH.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    return {
        "battery_id": battery_id,
        "ai_decision": ai_decision,
        "operator_decision": operator_decision,
        "decision_category": operator_decision,
        "final_decision": operator_decision,
        "target_bin": target_bin,
        "override_saved": True,
    }


def read_latest() -> dict:
    if not Path(LATEST_DECISION_PATH).exists():
        return {}
    return json.loads(LATEST_DECISION_PATH.read_text(encoding="utf-8"))
