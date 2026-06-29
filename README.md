# Circular Battery Decision Twin

Completed local research prototype for circular battery recovery decision support, built with Unity, FastAPI, Streamlit, computer vision, SOH prediction, and digital battery passport logging.

The project demonstrates a full end-to-end workflow for inspecting used lithium-ion batteries, classifying their visible form factor, evaluating health and risk signals, selecting a recovery route, simulating robotic sorting, and recording the decision trail for review.

## Project Overview

Circular Battery Decision Twin models a small battery recovery line for second-life and end-of-life battery handling. The system connects three layers:

- Unity process simulation for intake, inspection, operator control, and robot sorting.
- FastAPI backend for classification, health/risk evaluation, lifecycle routing, overrides, and passport records.
- Streamlit dashboard for inspection KPIs, route distribution, process performance, latest decisions, and battery passports.

The recovery routes implemented in the project are:

- reuse
- remanufacture
- recycle
- quarantine

## Problem

Used lithium-ion batteries from EVs, e-bikes, micromobility, solar storage, and backup systems cannot be routed safely from visual inspection alone. A recovery workflow needs to separate visible form-factor recognition from health assessment, risk scoring, operator review, and traceability.

This repository implements that workflow as a working local prototype.

## Implemented Capabilities

- Unity scene with battery intake, conveyor movement, inspection stations, lifecycle decision areas, and robotic sorting.
- FastAPI backend with inspection, image classification, SOH prediction, decision override, log, and passport endpoints.
- Battery image classification for cylindrical, pouch, and prismatic form factors.
- Trained lightweight computer-vision model with deterministic fallback behavior.
- NASA-derived SOH lookup table and ML-based SOH prediction path for sensor-style inputs.
- Explainable routing logic for reuse, remanufacture, recycle, quarantine, manual review, and emergency stop states.
- Operator controls for policy mode, confidence threshold, reuse SOH threshold, conveyor speed, robot mode, pause, emergency stop, and override.
- Runtime generation of inspection history, latest decision records, and digital battery passports.
- Streamlit dashboard for operational review and decision analytics.
- Presentation deck, demo figures, video assets, and supporting technical documentation.

## Architecture

```text
Unity process simulation
  -> battery_id, image, and operator settings
FastAPI backend
  -> form-factor classification
  -> health lookup / SOH prediction
  -> risk scoring and lifecycle routing
Unity runtime
  -> battery visual update, UI update, robot sorting action
Runtime logger
  -> inspection log, latest decision, digital battery passports
Streamlit dashboard
  -> KPIs, charts, latest inspection view, passport viewer
```

The image model is used for visible battery type only. Health and route selection are handled separately through SOH records, sensor-style values, thresholds, and safety rules.

## Tech Stack

- Unity 2021.3 LTS or newer
- C# Unity scripts
- Python 3.10+
- FastAPI
- Streamlit
- pandas
- scikit-learn
- scikit-image
- Pillow
- Plotly
- joblib

## Repository Structure

```text
dubai-battery-rex-control-twin/
├── backend/                     # FastAPI backend, CV/SOH models, decision logic
├── dashboard/                   # Streamlit dashboard
├── data/                        # Runtime image subset, manifest, NASA-derived SOH table
├── docs/                        # Architecture, model notes, demo scripts, technical reports
├── outputs/                     # Model evaluation reports; runtime outputs are gitignored
├── presentation/                # Slide deck, figures, video assets, presenter notes
├── scripts/                     # Dataset rebuild and model training scripts
├── unity/BatteryReXControlTwin/ # Unity project
├── README.md
└── .gitignore
```

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

### Dashboard

Open a second terminal:

```bash
cd dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Unity

1. Open `unity/BatteryReXControlTwin` in Unity 2021.3 LTS or newer.
2. Open `Assets/Scenes/BatteryRecoveryMicroFactory.unity`.
3. If the scene needs to be regenerated, stop Play mode and run `Battery Re-X > Rebuild Demo Scene`.
4. Keep the backend URL set to `http://127.0.0.1:8000`.
5. Press Play and click `Start Batch`.

## Demo Workflow

1. Start the FastAPI backend.
2. Start the Streamlit dashboard.
3. Open the Unity scene and press Play.
4. Click `Start Batch`.
5. A battery enters the simulated recovery line and moves to the inspection station.
6. Unity selects a runtime battery image from `data/images` and sends it to the backend.
7. The backend returns form factor, confidence, SOH/risk values, route decision, target bin, and explanation.
8. Unity updates the battery visual state and runs the robot sorting sequence.
9. The backend writes the inspection record, latest decision, and battery passport.
10. The dashboard displays updated KPIs, charts, latest inspection details, and passport records.

## Data and Models

The runtime image subset contains 90 public battery images from RecyBat24:

- 30 cylindrical images
- 30 pouch images
- 30 prismatic images

The SOH lookup table is derived from the NASA PCoE Battery Data Set. Source details, licensing notes, extracted fields, and rebuild commands are documented in `docs/real_data_sources.md`.

The trained form-factor classifier uses HOG/image features and a lightweight scikit-learn model. The SOH prediction path uses NASA-derived ageing data and sensor-style inputs such as cycle count, temperature, voltage, and internal resistance.

## Validation

Useful local checks:

```bash
python -m compileall backend dashboard scripts
curl http://127.0.0.1:8000/health
```

The Unity scene can be validated by starting the backend, pressing Play, running `Start Batch`, and checking that inspection records appear in the Streamlit dashboard.

## Engineering Scope

This repository is a completed local research prototype. The conveyor, robot, inspection stations, and some sensor values are simulated so the full decision workflow can be demonstrated without physical hardware. Industrial deployment would require hardware integration, certified safety controls, production data infrastructure, and real-world validation.

## Author

- Author: Amin Zoroufi
- Role: AI Researcher / XR Developer
- Location: Dubai, UAE
- Email: [aminn.zoroufi@gmail.com](mailto:aminn.zoroufi@gmail.com)
- LinkedIn: [linkedin.com/in/amin-zoroufi](https://www.linkedin.com/in/amin-zoroufi/)
- GitHub: [github.com/aminzoroufi](https://github.com/aminzoroufi)
- Portfolio: [aminzoroufi.github.io](https://aminzoroufi.github.io/)

## License

No open-source license is provided in this repository. Contact the author for reuse or collaboration permissions.

Third-party assets and datasets keep their own licenses. See:

- `docs/real_data_sources.md`
- `docs/unity_3d_models.md`
