# Data

Runtime data used by the Circular Battery Decision Twin prototype.

## Images

`data/images/` contains a 90-image runtime subset from RecyBat24:

- 30 cylindrical images
- 30 pouch images
- 30 prismatic images

Source metadata and attribution are stored in `data/image_sources.csv`.

## Health Lookup

`data/nasa_health/battery_health_lookup.csv` is derived from the NASA PCoE Battery Data Set.

The decision workflow uses:

- SOH from measured capacity divided by rated capacity.
- Temperature and voltage from discharge-cycle measurements.
- Internal resistance from the nearest impedance-cycle `Re + Rct`.

## Raw Downloads

Large raw downloads are local rebuild artifacts and should not be committed to GitHub:

- RecyBat24 archive
- NASA PCoE Battery Data Set archive and extracted MAT files

Rebuild runtime data from the project root with:

```bash
python scripts/build_real_dataset.py
```
