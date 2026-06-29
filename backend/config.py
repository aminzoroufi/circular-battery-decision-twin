from pathlib import Path


SERVICE_NAME = "Circular Battery Decision Twin Backend"

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
IMAGE_DIR = DATA_DIR / "images"
HEALTH_LOOKUP_PATH = DATA_DIR / "nasa_health" / "battery_health_lookup.csv"
MANIFEST_PATH = DATA_DIR / "manifest.csv"
INSPECTION_LOG_PATH = OUTPUTS_DIR / "inspection_log.csv"
PASSPORT_PATH = OUTPUTS_DIR / "battery_passports.json"
LATEST_DECISION_PATH = OUTPUTS_DIR / "latest_decision.json"
UPLOAD_DIR = OUTPUTS_DIR / "uploaded_images"

VALID_DECISIONS = {"reuse", "remanufacture", "recycle", "quarantine"}
DECISION_TO_BIN = {
    "reuse": "reuse_bin",
    "remanufacture": "remanufacture_bin",
    "recycle": "recycle_bin",
    "quarantine": "quarantine_bin",
    "manual_review": "quarantine_bin",
    "paused": "none",
}


def ensure_runtime_dirs() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
