"""Project: Circular Battery Decision Twin
Developer: Amin Zoroufi
Contact: aminn.zoroufi@gmail.com
"""

from __future__ import annotations

import shutil
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import DECISION_TO_BIN, PROJECT_ROOT, SERVICE_NAME, UPLOAD_DIR, VALID_DECISIONS, ensure_runtime_dirs
from decision_engine import make_decision
from health_lookup import get_health_record, get_manifest_record
from logger import append_inspection, read_latest, read_log, update_override
from ml.soh_model import load_model_artifact, model_exists, predict_soh_and_decision
from model import classify_battery_image
from passport import all_passports, apply_override, get_passport, update_passport


ensure_runtime_dirs()
app = FastAPI(title=SERVICE_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploaded-images", StaticFiles(directory=str(UPLOAD_DIR)), name="uploaded-images")


class OverrideRequest(BaseModel):
    battery_id: str
    operator_decision: str = Field(pattern="^(reuse|remanufacture|recycle|quarantine)$")
    override_reason: str
    operator_id: str = "operator_01"


class SohPredictionRequest(BaseModel):
    battery_id: str
    battery_type: str
    cycle_count: int
    temperature: float
    resistance: float | None = None
    voltage: float
    internal_resistance_mohm: float | None = None


@app.on_event("startup")
def startup() -> None:
    ensure_runtime_dirs()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/soh-model-metrics")
def soh_model_metrics() -> dict:
    if not model_exists():
        raise HTTPException(status_code=503, detail="SOH model is not trained. Run scripts/train_soh_models.py.")
    artifact = load_model_artifact()
    return {
        "model_used": artifact["model_name"],
        "metrics": artifact["metrics"],
        "all_model_metrics": artifact.get("all_model_metrics", {}),
        "dataset": artifact.get("dataset", {}),
        "feature_columns": artifact.get("feature_columns", []),
    }


@app.post("/predict-soh")
def predict_soh(request: SohPredictionRequest) -> dict:
    started = time.perf_counter()
    ensure_runtime_dirs()
    if not model_exists():
        raise HTTPException(status_code=503, detail="SOH model is not trained. Run scripts/train_soh_models.py.")

    payload = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    response = predict_soh_and_decision(payload)
    response["processing_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
    response["timestamp"] = datetime.now(timezone.utc).isoformat()

    features = {
        "cycle_count": response.get("cycle_count"),
        "temperature_c": response.get("temperature_c"),
        "internal_resistance_mohm": response.get("internal_resistance_mohm"),
        "voltage": response.get("voltage"),
        "battery_type": response.get("battery_type"),
        "predicted_soh": response.get("predicted_soh"),
        "state_of_health": response.get("soh"),
        "model_used": response.get("model_used"),
        "error_estimate_percent": response.get("error_estimate_percent"),
        "safety_flags": response.get("safety_flags", []),
    }
    record = {
        "timestamp": response["timestamp"],
        "battery_id": response["battery_id"],
        "image_id": None,
        "detected_shape": response["battery_type"],
        "detected_type": response["battery_type"],
        "decision_category": response["rex_category"],
        "confidence": response["confidence"],
        "uncertainty": round(max(0.0, min(1.0, 1.0 - float(response["confidence"]))), 3),
        "soh": response["soh"],
        "predicted_soh": response["predicted_soh"],
        "temperature_c": response["temperature_c"],
        "cycle_count": response["cycle_count"],
        "internal_resistance_mohm": response["internal_resistance_mohm"],
        "voltage": response["voltage"],
        "risk_score": response["risk_score"],
        "risk_level": response["risk_level"],
        "policy_mode": "ml_soh_thresholds",
        "confidence_threshold": None,
        "reuse_soh_threshold": 0.80,
        "conveyor_speed": None,
        "robot_mode": None,
        "ai_decision": response["ai_decision"],
        "operator_decision": None,
        "final_decision": response["final_decision"],
        "target_bin": response["target_bin"],
        "manual_review_required": response["manual_review_required"],
        "reason": response["reason"],
        "features": features,
        "features_json": json.dumps(features),
        "processing_time_ms": response["processing_time_ms"],
        "soh_model_used": response["model_used"],
        "soh_confidence": response["confidence"],
        "soh_error_estimate_percent": response["error_estimate_percent"],
    }
    append_inspection(record)
    response["features"] = features
    return response


@app.post("/classify-battery")
async def classify_battery(
    battery_id: str = Form(...),
    image: UploadFile = File(...),
) -> dict:
    started = time.perf_counter()
    ensure_runtime_dirs()

    safe_name = Path(image.filename or "uploaded_battery.jpg").name
    upload_token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    upload_filename = f"{battery_id}_{upload_token}_{safe_name}"
    upload_path = UPLOAD_DIR / upload_filename
    with upload_path.open("wb") as output:
        shutil.copyfileobj(image.file, output)

    model_result = classify_battery_image(upload_path, filename=safe_name)
    confidence = float(model_result["confidence"])
    detected_shape = model_result["detected_type"]
    processing_time_ms = round((time.perf_counter() - started) * 1000, 2)

    return {
        "battery_id": battery_id,
        "image_id": upload_filename,
        "detected_shape": detected_shape,
        "detected_type": detected_shape,
        "confidence": confidence,
        "uncertainty": round(max(0.0, min(1.0, 1.0 - confidence)), 3),
        "model_name": model_result.get("model_name"),
        "model_trust_percentage": model_result.get("model_trust_percentage"),
        "classification_method": model_result.get("classification_method"),
        "class_probabilities": model_result.get("class_probabilities"),
        "processing_time_ms": processing_time_ms,
        "original_image_filename": safe_name,
        "received_image_filename": upload_filename,
        "received_image_path": str(upload_path.relative_to(PROJECT_ROOT)),
        "received_image_url": "/uploaded-images/" + quote(upload_filename),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/inspect-battery")
async def inspect_battery(
    battery_id: str = Form(...),
    image: UploadFile = File(...),
    policy_mode: str = Form("balanced"),
    confidence_threshold: float = Form(0.65),
    reuse_soh_threshold: float = Form(0.8),
    conveyor_speed: str = Form("normal"),
    robot_mode: str = Form("auto"),
    operator_note: str | None = Form(None),
) -> dict:
    started = time.perf_counter()
    ensure_runtime_dirs()

    if policy_mode not in {"balanced", "safety_first", "recovery_maximization"}:
        raise HTTPException(status_code=422, detail="Invalid policy_mode")
    if conveyor_speed not in {"slow", "normal", "fast"}:
        raise HTTPException(status_code=422, detail="Invalid conveyor_speed")
    if robot_mode not in {"auto", "manual", "paused", "emergency_stop"}:
        raise HTTPException(status_code=422, detail="Invalid robot_mode")

    safe_name = Path(image.filename or "uploaded_battery.jpg").name
    upload_token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    upload_filename = f"{battery_id}_{upload_token}_{safe_name}"
    upload_path = UPLOAD_DIR / upload_filename
    with upload_path.open("wb") as output:
        shutil.copyfileobj(image.file, output)
    received_image_path = str(upload_path.relative_to(PROJECT_ROOT))
    received_image_url = "/uploaded-images/" + quote(upload_filename)

    manifest_record = get_manifest_record(battery_id)
    health_record = get_health_record(battery_id, manifest_record.get("health_id"))
    model_result = classify_battery_image(upload_path, filename=safe_name)
    decision = make_decision(
        detected_type=model_result["detected_type"],
        confidence=float(model_result["confidence"]),
        soh=float(health_record["soh"]),
        temperature_c=float(health_record["temperature_c"]),
        cycle_count=int(health_record["cycle_count"]),
        internal_resistance_mohm=float(health_record["internal_resistance_mohm"]),
        policy_mode=policy_mode,
        confidence_threshold=confidence_threshold,
        reuse_soh_threshold=reuse_soh_threshold,
        robot_mode=robot_mode,
    )

    processing_time_ms = round((time.perf_counter() - started) * 1000, 2)
    detected_shape = model_result["detected_type"]
    decision_category = normalize_decision_category(decision["final_decision"])
    confidence = float(model_result["confidence"])
    uncertainty = round(max(0.0, min(1.0, 1.0 - confidence)), 3)
    features = {
        "state_of_health": float(health_record["soh"]),
        "temperature_c": float(health_record["temperature_c"]),
        "cycle_count": int(health_record["cycle_count"]),
        "internal_resistance_mohm": float(health_record["internal_resistance_mohm"]),
        "classification_method": model_result.get("classification_method"),
        "classification_model": model_result.get("model_name"),
        "model_trust_percentage": model_result.get("model_trust_percentage"),
        "confidence_threshold": float(confidence_threshold),
        "reuse_soh_threshold": float(reuse_soh_threshold),
        "estimated_visual_damage_score": round(float(decision["risk_score"]) / 100.0, 3),
        "simulated_visual_damage_score": True,
    }
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "battery_id": battery_id,
        "image_id": upload_filename,
        "detected_shape": detected_shape,
        "detected_type": model_result["detected_type"],
        "decision_category": decision_category,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "soh": float(health_record["soh"]),
        "temperature_c": float(health_record["temperature_c"]),
        "cycle_count": int(health_record["cycle_count"]),
        "internal_resistance_mohm": float(health_record["internal_resistance_mohm"]),
        "policy_mode": policy_mode,
        "confidence_threshold": confidence_threshold,
        "reuse_soh_threshold": reuse_soh_threshold,
        "conveyor_speed": conveyor_speed,
        "robot_mode": robot_mode,
        "operator_decision": None,
        "processing_time_ms": processing_time_ms,
        "operator_note": operator_note,
        "original_image_filename": safe_name,
        "received_image_filename": upload_filename,
        "received_image_path": received_image_path,
        "received_image_url": received_image_url,
        "features": features,
        "features_json": json.dumps(features),
        **decision,
    }
    append_inspection(record)
    update_passport(record, manifest_record)

    return {
        "battery_id": record["battery_id"],
        "image_id": record["image_id"],
        "detected_shape": record["detected_shape"],
        "detected_type": record["detected_type"],
        "decision_category": record["decision_category"],
        "confidence": record["confidence"],
        "uncertainty": record["uncertainty"],
        "soh": record["soh"],
        "temperature_c": record["temperature_c"],
        "cycle_count": record["cycle_count"],
        "model_name": model_result.get("model_name"),
        "model_trust_percentage": model_result.get("model_trust_percentage"),
        "classification_method": model_result.get("classification_method"),
        "class_probabilities": model_result.get("class_probabilities"),
        "risk_score": record["risk_score"],
        "risk_level": record["risk_level"],
        "policy_mode": record["policy_mode"],
        "ai_decision": record["ai_decision"],
        "final_decision": record["final_decision"],
        "target_bin": record["target_bin"],
        "manual_review_required": record["manual_review_required"],
        "reason": record["reason"],
        "processing_time_ms": record["processing_time_ms"],
        "original_image_filename": record["original_image_filename"],
        "received_image_filename": record["received_image_filename"],
        "received_image_path": record["received_image_path"],
        "received_image_url": record["received_image_url"],
        "features": record["features"],
        "timestamp": record["timestamp"],
    }


@app.post("/override-decision")
def override_decision(request: OverrideRequest) -> dict:
    if request.operator_decision not in VALID_DECISIONS:
        raise HTTPException(status_code=422, detail="Invalid operator_decision")
    target_bin = DECISION_TO_BIN[request.operator_decision]
    try:
        response = update_override(
            battery_id=request.battery_id,
            operator_decision=request.operator_decision,
            override_reason=request.override_reason,
            target_bin=target_bin,
        )
        apply_override(request.battery_id, request.operator_decision, target_bin)
        return response
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/inspection-log")
def inspection_log() -> list[dict]:
    df = read_log()
    if df.empty:
        return []
    return df.where(pd.notnull(df), None).to_dict(orient="records")


@app.get("/latest-decision")
def latest_decision() -> dict:
    return read_latest()


@app.get("/latest-received-image")
def latest_received_image() -> dict:
    latest = read_latest()
    if not latest:
        return {}
    return {
        "battery_id": latest.get("battery_id"),
        "original_image_filename": latest.get("original_image_filename"),
        "received_image_filename": latest.get("received_image_filename"),
        "received_image_path": latest.get("received_image_path"),
        "received_image_url": latest.get("received_image_url"),
        "detected_shape": latest.get("detected_shape", latest.get("detected_type")),
        "decision_category": latest.get("decision_category", latest.get("final_decision")),
        "confidence": latest.get("confidence"),
        "uncertainty": latest.get("uncertainty"),
        "timestamp": latest.get("timestamp"),
    }


def normalize_decision_category(value: str | None) -> str:
    normalized = (value or "quarantine").lower().strip()
    if normalized == "manual_review":
        return "quarantine"
    if normalized in {"reuse", "remanufacture", "recycle", "quarantine"}:
        return normalized
    return "quarantine"


@app.get("/battery-passport/{battery_id}")
def battery_passport(battery_id: str) -> dict:
    passport = get_passport(battery_id)
    if not passport:
        raise HTTPException(status_code=404, detail="Battery passport not found")
    return passport


@app.get("/battery-passports")
def battery_passports() -> dict:
    return all_passports()
