from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from config import HEALTH_LOOKUP_PATH, MANIFEST_PATH


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def get_manifest_record(battery_id: str) -> dict:
    manifest = _read_csv(MANIFEST_PATH)
    if manifest.empty or "battery_id" not in manifest.columns:
        return {}
    match = manifest[manifest["battery_id"] == battery_id]
    if match.empty:
        return {}
    return match.iloc[0].fillna("").to_dict()


def _stable_index(value: str, length: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % max(length, 1)


def get_health_record(battery_id: str, health_id: str | None = None) -> dict:
    lookup = _read_csv(HEALTH_LOOKUP_PATH)
    if lookup.empty:
        return {
            "health_id": health_id or "fallback",
            "cycle_count": 650,
            "rated_capacity_ah": 3.0,
            "measured_capacity_ah": 2.25,
            "voltage": 3.7,
            "temperature_c": 34.0,
            "internal_resistance_mohm": 90.0,
            "soh": 0.75,
        }

    if health_id and "health_id" in lookup.columns:
        match = lookup[lookup["health_id"] == health_id]
        if not match.empty:
            row = match.iloc[0].to_dict()
        else:
            row = lookup.iloc[_stable_index(battery_id, len(lookup))].to_dict()
    else:
        row = lookup.iloc[_stable_index(battery_id, len(lookup))].to_dict()

    rated = float(row.get("rated_capacity_ah", 1.0) or 1.0)
    measured = float(row.get("measured_capacity_ah", 0.0) or 0.0)
    row["soh"] = round(measured / rated, 3) if rated else 0.0
    return row
