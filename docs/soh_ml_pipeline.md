# ML-Based SOH Prediction and Re-X Decision Stage

## Purpose

This module implements the second stage of the Battery Re-X digital twin pipeline. The camera stage classifies the physical battery shape as cylindrical, pouch, or prismatic. The SOH stage does not use the image to estimate health. Instead, it receives health-related measurements from the simulated sensor line:

- cycle count
- temperature in Celsius
- internal resistance in ohms or milliohms
- voltage in volts
- battery type from the vision stage

The backend predicts State of Health (SOH) as a percentage and converts the result into the final Re-X route.

## Dataset Selection

I evaluated public lithium-ion aging datasets suitable for SOH regression:

- NASA PCoE Li-ion Battery Aging Dataset: selected for this implementation because it is already downloaded in the project, contains charge/discharge/impedance measurements, and includes discharge capacity needed to compute SOH directly.
- CALCE Battery Data: highly relevant because it includes multiple chemistries and form factors, including cylindrical, pouch, and prismatic cells. It is identified as the best future extension for type-specific calibration.
- Oxford Battery Degradation Dataset 1: useful long-term degradation data for Kokam pouch cells, but it is a larger MATLAB dataset and was not needed for the first integrated backend stage.

The current implementation trains from `data/nasa_health/battery_health_lookup.csv`, which is generated from the local NASA raw `.mat` files. The selected NASA subset contains 636 clean discharge rows from B0005, B0006, B0007, and B0018.

## SOH Target

SOH is calculated from measured capacity:

```text
SOH (%) = measured_capacity_ah / rated_capacity_ah * 100
```

The saved training target is `soh_percent`. Unity receives the result as both:

- `predicted_soh`: percentage, for example `78.4`
- `soh`: fraction, for example `0.784`, for compatibility with older Unity UI code

## Features

The model input columns are:

- `cycle_count`
- `temperature_c`
- `internal_resistance_mohm`
- `voltage`
- `battery_type`

NASA rows are cylindrical cells. The API accepts pouch and prismatic values because Unity can classify those shapes, but the current trained model does not yet contain real pouch/prismatic aging calibration. Future work should add CALCE and Oxford rows to improve type-specific predictions.

## Models Trained

The training script is `scripts/train_soh_models.py`. It compares:

- Linear Regression baseline
- Random Forest Regressor
- Gradient Boosting Regressor
- Support Vector Regression
- MLP Regressor
- XGBoost if installed
- LightGBM if installed

The script saves the best model to `backend/trained_models/soh_predictor.joblib` and writes the comparison report to `outputs/model_evaluation/soh_model_comparison.json`.

Current selected model:

```text
RandomForestRegressor
MAE: 0.5348 SOH percentage points
RMSE: 0.7761 SOH percentage points
R2: 0.9946
MAPE: 0.6617%
```

## Decision Rules

The backend first validates the input. Missing values, unknown battery types, physically abnormal values, very high temperature, very high resistance, or abnormal voltage route directly to quarantine.

If the input is valid, Re-X routing uses predicted SOH:

- SOH >= 80%: reuse
- 60% <= SOH < 80%: remanufacture
- 30% <= SOH < 60%: recycle
- SOH < 30%: quarantine

Safety overrides:

- temperature >= 60 C: quarantine
- internal resistance >= 0.18 ohm: quarantine
- voltage < 2.5 V or voltage > 4.3 V: quarantine

## Backend API

Endpoint:

```text
POST /predict-soh
```

Example request:

```json
{
  "battery_id": "BAT_001",
  "battery_type": "cylindrical",
  "cycle_count": 430,
  "temperature": 31.2,
  "resistance": 0.052,
  "voltage": 3.72
}
```

Example response:

```json
{
  "battery_id": "BAT_001",
  "battery_type": "cylindrical",
  "cycle_count": 430,
  "temperature": 31.2,
  "resistance": 0.052,
  "voltage": 3.72,
  "predicted_soh": 94.49,
  "rex_category": "reuse",
  "model_used": "RandomForestRegressor"
}
```

Full responses also include risk score, risk level, target bin, confidence, estimated prediction error, and safety flags.

## Unity Integration

Unity now follows this sequence:

1. Battery stops at the camera station.
2. The image classifier detects physical shape only.
3. The battery moves through sensor stations.
4. Unity generates mock sensor values because real hardware sensors are not connected in this prototype.
5. Unity sends cycle count, temperature, resistance, voltage, and classified shape to `/predict-soh`.
6. The backend returns predicted SOH and Re-X category.
7. Unity updates the floating battery panel, selected-battery panel, and robot sorter.

This keeps the scientific boundary clear: image data is used for type classification; health data is used for SOH prediction.
