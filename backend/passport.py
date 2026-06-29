from __future__ import annotations

import json
from datetime import datetime, timezone

from config import PASSPORT_PATH, ensure_runtime_dirs


def _load_passports() -> dict:
    if not PASSPORT_PATH.exists():
        return {}
    return json.loads(PASSPORT_PATH.read_text(encoding="utf-8") or "{}")


def _save_passports(passports: dict) -> None:
    ensure_runtime_dirs()
    PASSPORT_PATH.write_text(json.dumps(passports, indent=2), encoding="utf-8")


def update_passport(record: dict, manifest_record: dict | None = None) -> dict:
    passports = _load_passports()
    manifest_record = manifest_record or {}
    battery_id = record["battery_id"]
    existing = passports.get(battery_id, {})
    history = existing.get("inspection_history", [])
    history.append(
        {
            "timestamp": record.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "policy_mode": record.get("policy_mode"),
            "detected_shape": record.get("detected_shape", record.get("detected_type")),
            "decision": record.get("decision_category", record.get("final_decision")),
        }
    )

    passport = {
        "battery_id": battery_id,
        "detected_shape": record.get("detected_shape", record.get("detected_type")),
        "detected_type": record.get("detected_type"),
        "decision_category": record.get("decision_category", record.get("final_decision")),
        "source_type": manifest_record.get("source_type", existing.get("source_type", "unknown")),
        "source_area": manifest_record.get("source_area", existing.get("source_area", "unknown")),
        "previous_application": manifest_record.get(
            "previous_application",
            existing.get("previous_application", "unknown"),
        ),
        "soh": record.get("soh"),
        "temperature_c": record.get("temperature_c"),
        "cycle_count": record.get("cycle_count"),
        "risk_score": record.get("risk_score"),
        "risk_level": record.get("risk_level"),
        "ai_decision": record.get("ai_decision"),
        "operator_decision": record.get("operator_decision"),
        "final_decision": record.get("final_decision"),
        "target_bin": record.get("target_bin"),
        "inspection_history": history,
    }
    passports[battery_id] = passport
    _save_passports(passports)
    return passport


def apply_override(battery_id: str, operator_decision: str, target_bin: str) -> dict:
    passports = _load_passports()
    if battery_id not in passports:
        raise KeyError(f"No passport found for {battery_id}")
    passport = passports[battery_id]
    passport["operator_decision"] = operator_decision
    passport["final_decision"] = operator_decision
    passport["target_bin"] = target_bin
    passport.setdefault("inspection_history", []).append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy_mode": "operator_override",
            "decision": operator_decision,
        }
    )
    passports[battery_id] = passport
    _save_passports(passports)
    return passport


def get_passport(battery_id: str) -> dict | None:
    return _load_passports().get(battery_id)


def all_passports() -> dict:
    return _load_passports()
