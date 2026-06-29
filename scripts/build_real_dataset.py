from __future__ import annotations

import csv
import json
import re
import shutil
import sys
import tarfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, UnidentifiedImageError
from scipy.io import loadmat


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"
RAW_DIR = DATA_DIR / "raw"
NASA_RAW_DIR = RAW_DIR / "nasa"
WIKIMEDIA_RAW_DIR = RAW_DIR / "wikimedia"
HEALTH_CSV = DATA_DIR / "nasa_health" / "battery_health_lookup.csv"
MANIFEST_CSV = DATA_DIR / "manifest.csv"
IMAGE_SOURCES_CSV = DATA_DIR / "image_sources.csv"
UNITY_MANIFEST_JSON = PROJECT_ROOT / "unity" / "BatteryReXControlTwin" / "Assets" / "StreamingAssets" / "sample_manifest.json"

NASA_BATTERY_ZIP_URL = "https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip"
NASA_ZIP_PATH = NASA_RAW_DIR / "NASA_5_Battery_Data_Set.zip"
NASA_EXTRACT_DIR = NASA_RAW_DIR / "battery_dataset"

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "DubaiBatteryReXControlTwin/1.0 (local research prototype; Wikimedia Commons API)"
TARGET_IMAGES_PER_CLASS = 30
MAX_COMMONS_RESULTS_PER_QUERY = 35
RECYBAT24_URL = "https://zenodo.org/records/15226091/files/recybat24.tar.gz?download=1"
RECYBAT24_README_URL = "https://zenodo.org/records/15226091/files/README.md?download=1"
RECYBAT24_ARCHIVE = RAW_DIR / "recybat24" / "recybat24.tar.gz"
RECYBAT24_README = RAW_DIR / "recybat24" / "README.md"

COMMONS_QUERIES = {
    "cylindrical": [
        "18650 lithium ion battery",
        "21700 lithium ion battery cell",
        "cylindrical lithium ion cell",
        "lithium ion cylindrical battery",
    ],
    "pouch": [
        "lithium polymer battery pouch",
        "pouch cell lithium ion battery",
        "mobile phone lithium ion battery",
        "lipo battery pack",
    ],
    "prismatic": [
        "prismatic lithium ion battery",
        "LiFePO4 prismatic cell",
        "EV battery module prismatic",
        "lithium ion prismatic cell",
    ],
}

SOURCE_TYPES = [
    "e-bike fleet",
    "EV service center",
    "solar storage",
    "smart building backup",
    "micro-mobility operator",
]
SOURCE_AREAS = [
    "Business Bay",
    "Dubai Marina",
    "Jebel Ali",
    "Al Quoz",
    "Dubai Silicon Oasis",
    "Downtown Dubai",
    "Deira",
]
PREVIOUS_APPLICATIONS = [
    "delivery mobility",
    "EV service module",
    "residential solar storage",
    "UPS backup module",
    "shared scooter pack",
    "commercial energy storage",
]


def request_json(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            wait_seconds = 8 * (attempt + 1)
            print(f"Wikimedia rate limited this request; waiting {wait_seconds}s before retrying...")
            time.sleep(wait_seconds)
    raise RuntimeError("Unreachable Wikimedia request retry state")


def clean_filename(value: str) -> str:
    value = value.replace("File:", "")
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value[:90].strip("_")


def commons_info_from_page(title: str, info: dict) -> dict | None:
    mime = info.get("mime", "")
    if not mime.startswith("image/") or mime in {"image/svg+xml", "image/gif"}:
        return None
    metadata = info.get("extmetadata", {})
    return {
        "title": title,
        "download_url": info.get("thumburl") or info.get("url"),
        "source_url": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'), safe=':/_')}",
        "license": metadata.get("LicenseShortName", {}).get("value", ""),
        "usage_terms": metadata.get("UsageTerms", {}).get("value", ""),
        "artist": re.sub("<[^<]+?>", "", metadata.get("Artist", {}).get("value", "")).strip(),
        "credit": re.sub("<[^<]+?>", "", metadata.get("Credit", {}).get("value", "")).strip(),
        "object_name": metadata.get("ObjectName", {}).get("value", title),
        "mime": mime,
    }


def commons_search(query: str) -> list[dict]:
    payload = request_json(
        COMMONS_API,
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": 6,
            "gsrsearch": query,
            "gsrlimit": MAX_COMMONS_RESULTS_PER_QUERY,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime",
            "iiurlwidth": 1200,
        },
    )
    pages = payload.get("query", {}).get("pages", {})
    infos = []
    for page in pages.values():
        title = page.get("title", "")
        if not title.startswith("File:"):
            continue
        imageinfo = (page.get("imageinfo") or [None])[0]
        if not imageinfo:
            continue
        info = commons_info_from_page(title, imageinfo)
        if info:
            infos.append(info)
    return infos


def download_and_validate_image(url: str, output_path: Path) -> bool:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            output_path.write_bytes(response.read())
        with Image.open(output_path) as image:
            image.verify()
        with Image.open(output_path) as image:
            rgb = image.convert("RGB")
            rgb.thumbnail((1200, 1200))
            rgb.save(output_path.with_suffix(".jpg"), quality=88, optimize=True)
        if output_path.suffix.lower() != ".jpg":
            output_path.unlink(missing_ok=True)
        return True
    except (OSError, UnidentifiedImageError, urllib.error.URLError):
        output_path.unlink(missing_ok=True)
        output_path.with_suffix(".jpg").unlink(missing_ok=True)
        return False


def rebuild_real_images() -> list[dict]:
    for label in COMMONS_QUERIES:
        target_dir = IMAGE_DIR / label
        target_dir.mkdir(parents=True, exist_ok=True)
        for file_path in target_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()

    WIKIMEDIA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    seen_titles: set[str] = set()

    for label, queries in COMMONS_QUERIES.items():
        class_count = 0
        for query in queries:
            if class_count >= TARGET_IMAGES_PER_CLASS:
                break
            for info in commons_search(query):
                if class_count >= TARGET_IMAGES_PER_CLASS:
                    break
                title = info["title"]
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                if not info.get("download_url"):
                    continue

                class_count += 1
                filename = f"real_{label}_{class_count:03d}_{clean_filename(title)}.jpg"
                output_path = IMAGE_DIR / label / filename
                temp_path = output_path.with_suffix(".download")
                if not download_and_validate_image(info["download_url"], temp_path):
                    class_count -= 1
                    continue

                final_path = temp_path.with_suffix(".jpg")
                if final_path != output_path:
                    final_path.replace(output_path)

                record = {
                    "detected_type": label,
                    "local_path": str(output_path.relative_to(PROJECT_ROOT)),
                    **info,
                }
                records.append(record)
                time.sleep(0.15)

        if class_count < 12:
            print(f"WARNING: only downloaded {class_count} images for {label}", file=sys.stderr)

    IMAGE_SOURCES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with IMAGE_SOURCES_CSV.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "detected_type",
                "local_path",
                "title",
                "source_url",
                "download_url",
                "license",
                "usage_terms",
                "artist",
                "credit",
                "object_name",
                "mime",
            ],
        )
        writer.writeheader()
        writer.writerows(records)
    return records


def download_recybat24() -> None:
    RECYBAT24_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    if not RECYBAT24_ARCHIVE.exists() or RECYBAT24_ARCHIVE.stat().st_size < 200_000_000:
        print(f"Downloading RecyBat24 image dataset from {RECYBAT24_URL}")
        request = urllib.request.Request(RECYBAT24_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=180) as response, RECYBAT24_ARCHIVE.open("wb") as output:
            shutil.copyfileobj(response, output)
    if not RECYBAT24_README.exists():
        request = urllib.request.Request(RECYBAT24_README_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=45) as response:
            RECYBAT24_README.write_bytes(response.read())


def label_from_recybat24_name(name: str) -> str | None:
    stem = Path(name).stem.lower()
    if stem.endswith("_cyl"):
        return "cylindrical"
    if stem.endswith("_po"):
        return "pouch"
    if stem.endswith("_pri"):
        return "prismatic"
    return None


def rebuild_recybat24_images() -> list[dict]:
    download_recybat24()
    for label in COMMONS_QUERIES:
        target_dir = IMAGE_DIR / label
        target_dir.mkdir(parents=True, exist_ok=True)
        for file_path in target_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()

    selected: dict[str, list[tarfile.TarInfo]] = {label: [] for label in COMMONS_QUERIES}
    with tarfile.open(RECYBAT24_ARCHIVE, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            label = label_from_recybat24_name(member.name)
            if not label:
                continue
            if len(selected[label]) < TARGET_IMAGES_PER_CLASS:
                selected[label].append(member)
            if all(len(items) >= TARGET_IMAGES_PER_CLASS for items in selected.values()):
                break

        records = []
        for label, members in selected.items():
            for index, member in enumerate(members, start=1):
                source_name = Path(member.name).name
                output_path = IMAGE_DIR / label / f"recybat24_{label}_{index:03d}_{source_name}"
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                output_path.write_bytes(extracted.read())
                records.append(
                    {
                        "detected_type": label,
                        "local_path": str(output_path.relative_to(PROJECT_ROOT)),
                        "title": source_name,
                        "source_url": "https://zenodo.org/records/15226091",
                        "download_url": RECYBAT24_URL,
                        "license": "CC-BY-4.0",
                        "usage_terms": "Creative Commons Attribution 4.0 International",
                        "artist": "Acaro Chacon, Ximena Carolina; Lo Scudo, Fabrizio; Cappuccino, Gregorio; Dodaro, Carmine",
                        "credit": "RecyBat24: an Image Dataset for LIB Recycling, Zenodo, DOI 10.5281/zenodo.15226091",
                        "object_name": source_name,
                        "mime": "image/jpeg",
                    }
                )

    missing = {label: TARGET_IMAGES_PER_CLASS - len(items) for label, items in selected.items() if len(items) < TARGET_IMAGES_PER_CLASS}
    if missing:
        raise RuntimeError(f"RecyBat24 did not provide enough images for: {missing}")

    IMAGE_SOURCES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with IMAGE_SOURCES_CSV.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "detected_type",
                "local_path",
                "title",
                "source_url",
                "download_url",
                "license",
                "usage_terms",
                "artist",
                "credit",
                "object_name",
                "mime",
            ],
        )
        writer.writeheader()
        writer.writerows(records)
    return records


def download_nasa_zip() -> None:
    NASA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    if NASA_ZIP_PATH.exists() and NASA_ZIP_PATH.stat().st_size > 100_000_000:
        return
    print(f"Downloading NASA battery dataset from {NASA_BATTERY_ZIP_URL}")
    request = urllib.request.Request(NASA_BATTERY_ZIP_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, NASA_ZIP_PATH.open("wb") as output:
        shutil.copyfileobj(response, output)


def extract_nasa_zip() -> None:
    NASA_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(NASA_ZIP_PATH) as archive:
        archive.extractall(NASA_EXTRACT_DIR)
    for nested_zip in sorted(NASA_EXTRACT_DIR.rglob("*.zip")):
        nested_dir = nested_zip.with_suffix("")
        if nested_dir.exists() and any(nested_dir.rglob("*.mat")):
            continue
        nested_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(nested_zip) as archive:
            archive.extractall(nested_dir)


def scalar(value) -> float | None:
    try:
        arr = np.asarray(value).squeeze()
        if arr.size == 0:
            return None
        return float(arr.flat[0])
    except Exception:
        return None


def flatten_cycle_data(data) -> dict:
    if hasattr(data, "_fieldnames"):
        return {field: np.asarray(getattr(data, field)).squeeze() for field in data._fieldnames}
    fields = getattr(data, "dtype", None).names or []
    return {field: np.asarray(data[field]).squeeze() for field in fields}


def extract_battery_rows(mat_path: Path) -> list[dict]:
    mat = loadmat(mat_path, squeeze_me=True, struct_as_record=False)
    battery_key = next((key for key in mat.keys() if key.startswith("B")), None)
    if not battery_key:
        return []
    cycles = np.atleast_1d(getattr(mat[battery_key], "cycle", []))
    rows = []
    discharge_count = 0
    rated_capacity = None
    impedance_by_cycle_index: list[tuple[int, float]] = []

    for cycle_index, cycle in enumerate(cycles):
        if getattr(cycle, "type", "") != "impedance":
            continue
        data = flatten_cycle_data(cycle.data)
        re_value = scalar(data.get("Re"))
        rct_value = scalar(data.get("Rct"))
        if re_value is not None and rct_value is not None:
            impedance_by_cycle_index.append((cycle_index, (re_value + rct_value) * 1000))

    for cycle_index, cycle in enumerate(cycles):
        if getattr(cycle, "type", "") != "discharge":
            continue
        data = flatten_cycle_data(cycle.data)
        capacity = scalar(data.get("Capacity"))
        if capacity is None or capacity <= 0:
            continue
        if rated_capacity is None:
            rated_capacity = capacity
        discharge_count += 1
        temp = scalar(np.nanmean(np.asarray(data.get("Temperature_measured", [np.nan]), dtype=float)))
        voltage = scalar(np.nanmean(np.asarray(data.get("Voltage_measured", [np.nan]), dtype=float)))
        resistance = None
        if impedance_by_cycle_index:
            _, resistance = min(impedance_by_cycle_index, key=lambda item: abs(item[0] - cycle_index))

        rows.append(
            {
                "health_id": f"{battery_key}-D{discharge_count:03d}",
                "battery_source_id": battery_key,
                "cycle_count": discharge_count,
                "rated_capacity_ah": round(float(rated_capacity), 5),
                "measured_capacity_ah": round(float(capacity), 5),
                "voltage": round(float(voltage), 5) if voltage is not None and not np.isnan(voltage) else "",
                "temperature_c": round(float(temp), 5) if temp is not None and not np.isnan(temp) else "",
                "internal_resistance_mohm": round(float(resistance), 5) if resistance else "",
                "soh": round(float(capacity) / float(rated_capacity), 5),
                "source_file": str(mat_path.relative_to(PROJECT_ROOT)),
                "source_url": NASA_BATTERY_ZIP_URL,
            }
        )
    return rows


def rebuild_nasa_health_lookup() -> list[dict]:
    download_nasa_zip()
    extract_nasa_zip()
    mat_files = sorted(NASA_EXTRACT_DIR.rglob("B*.mat"))
    selected_files = [path for path in mat_files if path.stem in {"B0005", "B0006", "B0007", "B0018"}]
    if not selected_files:
        selected_files = mat_files[:8]

    rows: list[dict] = []
    for mat_file in selected_files:
        rows.extend(extract_battery_rows(mat_file))

    if not rows:
        raise RuntimeError("NASA battery MAT files were found, but no discharge capacity rows could be extracted.")

    HEALTH_CSV.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(HEALTH_CSV, index=False)
    return rows


def rebuild_manifest(image_records: list[dict], health_rows: list[dict]) -> list[dict]:
    if not image_records:
        raise RuntimeError("No real image records were downloaded.")
    if not health_rows:
        raise RuntimeError("No real NASA health rows were extracted.")

    manifest = []
    health_rows_sorted = sorted(health_rows, key=lambda row: (row["battery_source_id"], row["cycle_count"]))
    for index, record in enumerate(image_records, start=1):
        if len(image_records) == 1:
            health_index = 0
        else:
            health_index = round((index - 1) * (len(health_rows_sorted) - 1) / (len(image_records) - 1))
        health = health_rows_sorted[health_index]
        manifest.append(
            {
                "battery_id": f"DXB-REAL-BAT-{index:03d}",
                "image_path": record["local_path"],
                "source_type": SOURCE_TYPES[(index - 1) % len(SOURCE_TYPES)],
                "source_area": SOURCE_AREAS[(index - 1) % len(SOURCE_AREAS)],
                "previous_application": PREVIOUS_APPLICATIONS[(index - 1) % len(PREVIOUS_APPLICATIONS)],
                "health_id": health["health_id"],
                "image_source_url": record["source_url"],
                "image_license": record["license"],
                "health_source": "NASA PCoE Battery Data Set",
            }
        )

    pd.DataFrame(manifest).to_csv(MANIFEST_CSV, index=False)
    UNITY_MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    UNITY_MANIFEST_JSON.write_text(json.dumps({"batteries": manifest}, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    image_records = rebuild_recybat24_images()
    health_rows = rebuild_nasa_health_lookup()
    manifest = rebuild_manifest(image_records, health_rows)
    print(f"Sampled real RecyBat24 battery images: {len(image_records)}")
    print(f"Extracted NASA health rows: {len(health_rows)}")
    print(f"Built manifest rows: {len(manifest)}")
    print(f"Image sources: {IMAGE_SOURCES_CSV}")
    print(f"Health lookup: {HEALTH_CSV}")
    print(f"Unity manifest: {UNITY_MANIFEST_JSON}")


if __name__ == "__main__":
    main()
