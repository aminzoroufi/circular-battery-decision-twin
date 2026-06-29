# Circular Battery Decision Twin

Local research prototype for exploring circular battery recovery decisions with a Unity process simulation, FastAPI backend, Streamlit dashboard, and battery passport logs.

The current version focuses on the core workflow: an incoming battery is inspected, assigned a visible form factor, matched with health data, routed to a lifecycle pathway, and logged for later review. It is designed as a portfolio and research prototype, not as a certified industrial control system.

## What It Does

The project models a small battery recovery line where used lithium-ion batteries can be routed to:

- reuse
- remanufacture
- recycle
- quarantine

Unity provides the operator-facing process simulation. The Python backend handles image classification, health lookup or SOH prediction, risk scoring, lifecycle routing, and runtime logging. The Streamlit dashboard reads the generated logs and passports so the decision flow can be reviewed after each inspection.

## Why It Was Built

Used batteries from EVs, e-bikes, micromobility, solar storage, and building backup systems need safe and traceable routing at end of first life. A practical recovery workflow needs more than a visual label: it needs a clear distinction between form-factor recognition, health assessment, safety rules, operator override, and traceability.

This prototype was built to demonstrate that workflow end to end in a local environment.

## Main Features

- Unity scene for a simulated battery intake, conveyor, inspection stations, robot sorting, and lifecycle areas.
- FastAPI backend with endpoints for image classification, full inspection, SOH prediction, decision override, logs, and battery passports.
- Battery image classification for cylindrical, pouch, and prismatic form factors using a trained lightweight computer-vision model with a deterministic fallback.
- NASA-derived SOH lookup and an ML-based SOH prediction path for sensor-style inputs.
- Explainable decision logic for reuse, remanufacture, recycle, quarantine, manual review, and emergency stop states.
- Operator controls for policy mode, confidence threshold, reuse SOH threshold, conveyor speed, robot mode, pause, emergency stop, and override.
- Runtime CSV/JSON outputs for inspection history, latest decision, and digital battery passports.
- Streamlit dashboard for KPIs, decision distribution, process performance, passport review, and simple impact estimation.
- Presentation material and demo media for explaining the prototype.

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

## Project Structure

```text
dubai-battery-rex-control-twin/
├── backend/                     # FastAPI service, decision logic, CV/SOH models
├── dashboard/                   # Streamlit analytics dashboard
├── data/                        # Runtime image subset, manifest, NASA-derived health table
├── docs/                        # Architecture, model notes, demo scripts, roadmap
├── outputs/                     # Runtime logs, latest decision, passports, model reports
├── presentation/                # Slide deck, figures, video notes, generated demo media
├── scripts/                     # Dataset rebuild and model training scripts
├── unity/BatteryReXControlTwin/ # Unity project
├── README.md
└── .gitignore
```

## How It Works

```text
Unity process simulation
  -> sends battery_id, image, and operator settings
FastAPI backend
  -> classifies visible battery type
  -> looks up or predicts health information
  -> scores risk and selects a lifecycle route
Unity runtime
  -> updates the battery shape, UI, robot action, and destination area
Runtime logger
  -> writes inspection_log.csv, latest_decision.json, and battery_passports.json
Streamlit dashboard
  -> displays KPIs, charts, latest inspection, and passports
```

The image classifier is used for visible form factor only. Health and routing are handled separately through SOH records, sensor-style inputs, thresholds, risk scoring, and safety rules.

## Setup

Create separate virtual environments for the backend and dashboard, or use one shared environment from the project root if you prefer.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Check that the service is running:

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
3. If the scene opens empty or looks outdated, stop Play mode and run `Battery Re-X > Rebuild Demo Scene`.
4. Keep the backend URL set to `http://127.0.0.1:8000`.
5. Press Play and click `Start Batch`.

## Demo Workflow

1. Start the FastAPI backend.
2. Start the Streamlit dashboard.
3. Open the Unity scene and press Play.
4. Click `Start Batch`.
5. A default unknown battery moves to the inspection station.
6. Unity selects a real test image from `data/images` and sends it to the backend.
7. The backend returns the detected form factor, confidence, SOH, risk, decision route, target bin, and explanation.
8. Unity updates the battery shape and routes it through the robot sorting sequence.
9. The backend writes the inspection log, latest decision, and battery passport.
10. The dashboard updates the KPIs, charts, latest inspection panel, and passport viewer.

## Data

The active runtime image subset contains 90 public battery images from RecyBat24:

- 30 cylindrical images
- 30 pouch images
- 30 prismatic images

The SOH lookup table is derived from the NASA PCoE Battery Data Set. Source details, licenses, extracted fields, and rebuild commands are documented in `docs/real_data_sources.md`.

Large raw downloads under `data/raw/` should be treated as local rebuild artifacts and are ignored for GitHub hygiene.

## Model Notes

The current battery type classifier is a lightweight computer-vision model trained on the local 90-image subset. It is suitable for demonstrating the workflow, but the reported validation score should not be interpreted as production accuracy.

The SOH model is trained from NASA-derived rows. The current health data is strongest for cylindrical-cell style ageing records; pouch and prismatic health calibration should be expanded with additional datasets before claiming type-specific battery health performance.

## Demo Material

The repository includes supporting presentation material:

- `presentation/Battery_ReX_Digital_Twin_Thesis_Presentation.pptx`
- `presentation/figures/`
- `presentation/videos/`
- `docs/demo_script.md`

Need confirmation: add a public demo video link here if one is available.

## Configuration

No environment variables are required for the local demo.

Default local service URLs:

- Backend: `http://127.0.0.1:8000`
- Dashboard: Streamlit local URL shown in the terminal

Important runtime paths:

- `outputs/inspection_log.csv`
- `outputs/latest_decision.json`
- `outputs/battery_passports.json`
- `outputs/uploaded_images/`

## Tests

No dedicated automated test suite is included yet.

Useful validation checks:

```bash
python -m compileall backend dashboard scripts
curl http://127.0.0.1:8000/health
```

Need confirmation: add formal API, dashboard, and Unity play-mode tests if this project will be maintained beyond the prototype stage.

## Known Limitations

- This is a local research prototype, not a production deployment.
- The Unity conveyor, robot, and inspection stations are simulated.
- The physical robot, PLC/OPC UA layer, thermal camera, voltage tester, and impedance hardware are not connected.
- Some Unity sensor values are mock readings used to demonstrate the staged workflow.
- The image dataset subset is small and should be expanded for stronger validation.
- The current runtime storage uses CSV and JSON files rather than a database.
- Authentication, access control, and operator audit trails are not included yet.
- The Unity project folder name and several class names still use the earlier internal project name to avoid breaking serialized Unity references.

## Future Improvements

- Add a larger battery image dataset with varied lighting, angles, backgrounds, and damage states.
- Extend SOH training with CALCE, Oxford, or partner battery ageing data.
- Add physical sensor inputs for thermal, voltage, capacity, and impedance measurements.
- Replace file-based logs with PostgreSQL or another database.
- Add ROS 2, OPC UA, or PLC integration for a lab-scale pilot.
- Add user authentication and operator-level audit trails.
- Add AR/VR operator views after the core decision workflow is validated.
- Add automated backend tests, dashboard smoke tests, and Unity play-mode tests.

## Author

Author: Amin Zoroufi  
Role: Developer  
Location: Dubai, UAE  
Email: YOUR_EMAIL  
LinkedIn: YOUR_LINKEDIN  
GitHub: YOUR_GITHUB  
Portfolio: YOUR_PORTFOLIO

## License

Need confirmation: choose a project license before publishing on GitHub.

Third-party assets and datasets keep their own licenses. See:

- `docs/real_data_sources.md`
- `docs/unity_3d_models.md`
