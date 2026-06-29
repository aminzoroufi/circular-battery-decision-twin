# Real Data Sources

This prototype now uses real public source data instead of generated placeholder battery images or hand-made SOH rows.

## Battery Images

Primary source:

- Dataset: RecyBat24: an Image Dataset for LIB Recycling
- Source: https://zenodo.org/records/15226091
- DOI: 10.5281/zenodo.15226091
- License: Creative Commons Attribution 4.0 International
- Classes used: Cylindrical, Pouch, Prismatic
- Runtime subset: 90 real images, 30 per class

Local files:

- `data/images/cylindrical/`
- `data/images/pouch/`
- `data/images/prismatic/`
- `data/image_sources.csv`

The full downloaded archive is stored under `data/raw/recybat24/`.

## Battery Health / SOH Data

Primary source:

- Dataset: NASA PCoE Battery Data Set
- Source: https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip
- NASA repository page: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
- NASA Open Data page: https://data.nasa.gov/dataset/li-ion-battery-aging-datasets

Extracted fields:

- `health_id`
- `battery_source_id`
- `cycle_count`
- `rated_capacity_ah`
- `measured_capacity_ah`
- `voltage`
- `temperature_c`
- `internal_resistance_mohm`
- `soh`
- `source_file`
- `source_url`

SOH is calculated from real NASA discharge-cycle capacity:

```text
soh = measured_capacity_ah / rated_capacity_ah
```

Internal resistance is derived from the nearest NASA impedance cycle using:

```text
internal_resistance_mohm = (Re + Rct) * 1000
```

Local file:

- `data/nasa_health/battery_health_lookup.csv`

## Rebuild Command

```bash
python scripts/build_real_dataset.py
```

The script rebuilds:

- `data/images/`
- `data/image_sources.csv`
- `data/nasa_health/battery_health_lookup.csv`
- `data/manifest.csv`
- `unity/BatteryReXControlTwin/Assets/StreamingAssets/sample_manifest.json`
