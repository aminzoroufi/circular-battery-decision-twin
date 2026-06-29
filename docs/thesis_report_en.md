# Circular Battery Decision Twin

## Abstract

I designed and implemented the Circular Battery Decision Twin as a local decision-support prototype for lithium-ion battery recovery, inspection, and circular manufacturing process control. The project addresses a practical problem that appears when electric vehicles, e-bike fleets, micro-mobility systems, solar storage units, and smart-building backup batteries reach end of first life: each battery must be routed safely and economically toward reuse, remanufacture, recycling, or quarantine. I built the system as a working prototype composed of a Unity-based process simulation, a FastAPI backend, a Streamlit analytics dashboard, local datasets, runtime logs, digital battery passports, and a rule-based decision engine.

The system is intentionally transparent. It separates what can be inferred from an image from what requires sensor or battery-management-system data. In the current prototype, the image is used to classify the visible physical battery type: cylindrical, pouch, prismatic, or unknown. Health and safety indicators such as state of health, temperature, internal resistance, cycle count, and damage risk are represented through mock or linked sample data because the prototype receives only an image as the physical input. I made this separation explicit in the system design so that the prototype remains technically honest and defensible while still demonstrating the full decision workflow expected in a real recovery facility.

The implemented twin demonstrates a two-stage industrial process. First, an unknown battery enters the conveyor and is imaged by a camera station. The backend classifies the battery shape and returns the classification to Unity, where the 3D object changes from an unknown shape into the detected shape without applying a lifecycle decision material. Second, the battery travels through downstream sensor stations representing thermal imaging, electrical/capacity testing, impedance testing, and damage-vision inspection. Because these signals are not available from the image alone, I generate mock sensor values for demonstration. The UI updates each reading sequentially, then the decision engine assigns the battery to a Re-X category and the robotic arm sorts it into the appropriate area.

The project contributes a coherent prototype architecture for battery circularity: an image classification pipeline, an explicit sensor-data abstraction, a local operational backend, a runtime dashboard, digital product passports, and a generated 3D micro-factory scene. The work is designed for explanation, extension, and examination rather than opaque automation.

## Acknowledgements

I acknowledge the public dataset providers and asset creators whose open resources made this prototype possible. I used RecyBat24 for lithium-ion battery imagery, the NASA Prognostics Center of Excellence battery aging data for health-record modelling, and Kenney Factory Kit assets for the industrial 3D environment. I also acknowledge the academic and industrial work on battery state-of-health estimation, circular economy, robotic sorting, digital twins, and safe lithium-ion battery handling that informed the design of this system.

## Table of Contents

1. Introduction
2. Problem Definition
3. Literature Review
4. System Requirements
5. System Architecture
6. Dataset Analysis
7. Methodology
8. Detailed File-by-File Repository Explanation
9. Computer Vision Pipeline
10. Machine Learning Components
11. Robotics and Navigation Components
12. Digital Twin Design
13. API and Backend Services
14. Experimental Setup
15. Evaluation and Results
16. Limitations
17. Future Work
18. Thesis Defense Questions and Answers
19. Conclusion
20. References

## Introduction

I developed this project to demonstrate how a digital twin can support battery recovery decisions in a future Dubai battery recycling and remanufacturing micro-factory. The system is not only a visual simulation. It connects a simulated conveyor, camera station, sensor stations, robotic sorter, backend classifier, decision engine, runtime logging layer, digital passport store, and analytics dashboard. This makes it an operational control twin rather than a static animation.

The motivation is the expected growth of lithium-ion battery waste streams. Batteries from electric mobility and stationary energy storage are valuable but hazardous. A healthy pack may be suitable for second-life reuse. A moderately degraded unit may be remanufactured or refurbished. A heavily degraded or damaged battery should be recycled or quarantined. The routing decision must consider safety, value recovery, traceability, and process throughput.

I designed the system around a central engineering principle: image data alone cannot determine the internal health of a battery. A visible image can identify battery format and sometimes visible damage, but it cannot reliably measure capacity, internal resistance, temperature history, cycle count, or electrochemical degradation. Therefore, I implemented a staged pipeline that separates visual classification from health-data acquisition.

### Possible Examiner Questions

**Question:** Why did I build a digital twin instead of a simple dashboard?

**Suggested answer:** I built a digital twin because the project is about operational decision-making inside a recovery process, not only data display. The Unity scene represents conveyor movement, camera inspection, sensor stages, robot sorting, and decision bins. This allows me to demonstrate how backend decisions change physical process behavior.

**Question:** Why is the separation between image classification and health estimation important?

**Suggested answer:** I separated them because image classification and battery health estimation are different measurement problems. A camera can identify visible geometry, but it cannot directly measure SOH, internal resistance, or cycle history. In a real system those values require BMS data, electrical testing, thermal sensors, or impedance measurement.

## Problem Definition

The core problem is to route used lithium-ion batteries into the most appropriate recovery pathway. I defined four output categories:

- **Reuse:** the battery is sufficiently healthy and low-risk for direct second-life application.
- **Remanufacture:** the battery has moderate health or requires repair, testing, or module-level reconfiguration.
- **Recycle:** the battery is too degraded for reuse or remanufacture but remains materially valuable.
- **Quarantine:** the battery is unsafe, uncertain, damaged, or requires manual review.

The decision is multi-factorial. It cannot be made from shape alone. A pouch battery may be excellent or dangerous; a cylindrical cell may be reusable or exhausted. Therefore, the problem requires both visible classification and health/risk information.

I decomposed the problem into the following sub-problems:

1. Capture or select a battery image.
2. Classify the battery format from image evidence.
3. Preserve traceability by storing the received image and metadata.
4. Acquire or simulate health and safety data.
5. Combine the readings into a risk score.
6. Apply policy thresholds to select a Re-X route.
7. Update the digital twin and UI in real time.
8. Sort the battery with a robot into the selected destination.
9. Log the decision and update the battery passport.

The current project assumes that only image input is physically available. For this reason, non-image health data is represented through linked sample data and mock sensor values. I implemented this assumption explicitly rather than hiding it inside the algorithm.

### Possible Examiner Questions

**Question:** What is the main technical problem solved by the project?

**Suggested answer:** The main technical problem is the integration of classification, sensor abstraction, decision logic, digital twin visualization, robotic sorting behavior, and traceability into one coherent recovery workflow.

**Question:** Can the project determine SOH from the image?

**Suggested answer:** No. I intentionally do not claim that. In the implemented workflow, the image identifies physical type. SOH is represented by mock or linked sensor data because true SOH requires electrical or BMS measurement.

## Literature Review

### Battery circular economy

Lithium-ion battery circularity depends on extending value before material recycling. Reuse and remanufacture can preserve embodied energy and economic value, while recycling recovers metals and reduces environmental risk. However, unsafe reuse can create fire and liability hazards. Therefore, recovery systems must combine state estimation, safety screening, and traceable routing.

### State of health and degradation

State of health is commonly defined as the ratio between current usable capacity and nominal or initial capacity:

```text
SOH = measured_capacity / rated_capacity
```

Capacity fade, internal resistance growth, thermal behavior, and cycle history are important indicators of degradation. NASA PCoE battery aging data is widely used in research because it includes charge, discharge, and impedance experiments. I used it as a sample health-data source because it provides realistic fields for demonstrating SOH and resistance-based decisions.

### Computer vision for battery sorting

Battery images can support format classification and visual damage inspection. RecyBat24 is suitable for this project because it is specifically focused on lithium-ion battery types used in recycling contexts: pouch, prismatic, and cylindrical. I used this dataset to avoid generic object datasets that do not represent battery recovery tasks.

### Digital twins

A digital twin is a dynamic digital representation of a physical process or asset. In this project, the twin mirrors process states: intake, camera classification, sensor inspection, Re-X decision, robotic sorting, and logging. The twin receives backend decisions and updates its physical simulation accordingly.

### Robotics in sorting

Industrial sorting systems often use conveyors, sensors, and robotic manipulators. In this prototype, I implemented a simplified ABB CRB-style arm using procedural Unity geometry. The purpose is not to solve industrial inverse kinematics, but to demonstrate pick-and-place behavior controlled by lifecycle decision outputs.

### Possible Examiner Questions

**Question:** Why did I use a rule-based decision engine instead of a black-box model?

**Suggested answer:** I used a rule-based engine because the prototype emphasizes explainability and safety. In battery recovery, an operator must understand why a battery was sent to reuse, remanufacture, recycle, or quarantine. A rule-based engine also works when labelled Re-X outcome data is unavailable.

**Question:** Why is RecyBat24 more suitable than a general image dataset?

**Suggested answer:** I selected RecyBat24 because it is directly about lithium-ion battery detection and classification for recycling. General datasets do not provide the specific pouch, prismatic, and cylindrical categories needed for this project.

## System Requirements

### Functional requirements

I defined the following functional requirements:

- The system shall accept a battery ID and image.
- The backend shall classify the visible battery type.
- The Unity twin shall update the battery shape after classification.
- The battery shall continue moving through sensor stations.
- The UI shall update the data readings stage by stage.
- The system shall generate mock health readings when real sensors are unavailable.
- The decision engine shall route the battery into reuse, remanufacture, recycle, or quarantine.
- The robot sorter shall place the battery into the corresponding area.
- The backend shall log inspections and maintain digital product passports.
- The dashboard shall display KPIs and runtime analytics.

### Non-functional requirements

- **Explainability:** The route must have a textual reason and visible risk indicators.
- **Traceability:** Uploaded images, logs, and passports must be preserved.
- **Extensibility:** Real sensors, trained CV models, ROS 2, or databases should be addable later.
- **Local reproducibility:** The prototype must run locally through Python services and Unity.
- **Safety-first operation:** Low confidence, high risk, and emergency stop states must prevent unsafe sorting.

### Possible Examiner Questions

**Question:** What was the most important non-functional requirement?

**Suggested answer:** Explainability was the most important because battery routing has safety and economic consequences. I wanted every decision to include a reason, a risk score, and visible UI feedback.

## System Architecture

The architecture has six major layers:

1. **Unity control twin:** camera station, conveyors, mock sensor stations, robot, bins, and operator UI.
2. **FastAPI backend:** image classification, inspection APIs, health lookup, decision logic, logs, and passports.
3. **Data layer:** RecyBat24 images, NASA-derived health lookup, manifest, raw archives, output logs.
4. **Decision engine:** risk scoring and Re-X route selection.
5. **Streamlit dashboard:** KPI monitoring, inspection logs, passports, and grant-impact simulation.
6. **Documentation and build scripts:** dataset preparation, real data source notes, architecture notes, and pilot roadmap.

The current flow is:

```text
Unknown battery enters conveyor
    -> camera captures/selects image
    -> FastAPI /classify-battery returns shape
    -> Unity changes neutral 3D shape
    -> thermal/electrical/impedance/damage stations generate mock readings
    -> decision logic assigns Re-X route
    -> material changes to Re-X decision color
    -> robot sorts into destination
    -> logs/passports/dashboard update
```

I chose this architecture because it separates concerns. Unity handles spatial process behavior. FastAPI handles backend logic and traceability. Streamlit handles analytics. CSV and JSON files keep the prototype simple and inspectable.

Alternative approaches considered:

- **Single monolithic Unity-only implementation:** rejected because backend services and dashboards would be harder to test and replace.
- **Database-first cloud architecture:** rejected for the prototype because local CSV/JSON files are easier to inspect and demonstrate.
- **End-to-end neural network decision model:** rejected because labelled Re-X decision data was unavailable and explainability was more important.

### Possible Examiner Questions

**Question:** Why did I choose FastAPI?

**Suggested answer:** I chose FastAPI because it provides a lightweight, typed, local HTTP service that Unity can call through multipart form requests. It is easy to extend with additional endpoints for future sensor data.

## Dataset Analysis

### RecyBat24 image dataset

**Exact name:** RecyBat24: an Image Dataset for LIB Recycling.

**Source and provider:** The dataset is published on Zenodo by Acaro Chacon, Lo Scudo, Cappuccino, and Dodaro. The public Zenodo record describes it as a dataset for classification and detection of lithium-ion battery types: pouch, prismatic, and cylindrical.

**Why I selected it:** I selected RecyBat24 because it matches the exact visual classification problem in this project. It provides lithium-ion battery images in categories relevant to battery recycling. I rejected generic object datasets because they do not represent the physical forms and recycling context of lithium-ion batteries.

**Licensing:** The project metadata records the image subset under CC-BY-4.0. I preserved attribution metadata in `data/image_sources.csv`.

**Structure in this repository:**

```text
data/images/cylindrical/ 30 images
data/images/pouch/       30 images
data/images/prismatic/   30 images
```

The active subset contains 90 images in total. File names include the local subset prefix, the detected class, an index, and the original RecyBat24 filename. Example:

```text
recybat24_pouch_030_38_4_F_2_po.jpg
```

From this name I can safely infer that the source is RecyBat24 and the type is pouch. I cannot infer SOH, SOC, cycle count, temperature, or internal resistance.

**Preprocessing:** The build script extracts image files from the RecyBat24 archive, filters images by class suffix and folder logic, copies a selected subset into class-specific directories, and writes source metadata. The prototype does not perform heavy augmentation because the implemented classifier is deterministic and lightweight rather than a trained deep model.

**Train/validation/test split:** I did not perform a formal train/validation/test split for a deep model in the current version. Instead, I used the dataset as a runtime classification and demonstration subset. If I train a YOLO, ResNet, MobileNet, or RT-DETR model later, I would use a stratified split such as 70/15/15 or 80/10/10 while ensuring that near-duplicate images do not leak across splits.

**Limitations and biases:** The subset contains only three battery form factors. It may not represent damaged packs, mixed waste scenes, occlusions, labels, lighting variation, or industrial conveyor backgrounds. The current subset is small, so it is suitable for prototype demonstration but not for production deployment.

### NASA PCoE battery aging data

**Exact name:** NASA PCoE Battery Data Set / Li-ion Battery Aging Datasets.

**Source and provider:** NASA Ames Prognostics Center of Excellence collected lithium-ion battery aging data on a custom battery prognostics testbed. The data includes charge, discharge, and electrochemical impedance spectroscopy under different operating conditions.

**Why I selected it:** I selected NASA PCoE data because it is a widely recognized public battery aging dataset and includes the kinds of signals needed to justify Re-X routing: capacity, temperature, voltage, cycle count, and impedance-derived resistance.

**Structure in this repository:**

```text
data/raw/nasa/NASA_5_Battery_Data_Set.zip
data/nasa_health/battery_health_lookup.csv
```

The processed CSV contains:

- `health_id`
- `battery_source_id`
- `cycle_count`
- `rated_capacity_ah`
- `measured_capacity_ah`
- `voltage`
- `temperature_c`
- `internal_resistance_mohm`
- `soh`
- source path and URL fields

**SOH calculation:** I calculate SOH as:

```text
soh = measured_capacity_ah / rated_capacity_ah
```

**Use in the project:** Earlier backend inspection calls can map a demo `battery_id` to a `health_id` through `manifest.csv`, then retrieve corresponding health fields. In the most recent two-step Unity flow, the image classification stage remains separate and downstream sensor readings are mock values because the live input is image-only.

**Limitations:** NASA data comes from controlled laboratory cells and may not fully represent field-returned batteries from Dubai mobility, solar, or smart-building sources. It also does not correspond physically to the RecyBat24 images. I therefore treat it as sample health data, not ground truth for the photographed batteries.

### Manifest dataset

`data/manifest.csv` and Unity `sample_manifest.json` define a synthetic operational manifest. I use it to assign IDs, source areas, previous applications, image references, and health IDs. This is necessary because a digital twin requires traceable assets moving through the process. In a real deployment, this manifest would be replaced or enriched by QR codes, serial numbers, battery passports, BMS exports, and enterprise asset records.

### Kenney Factory Kit

**Exact name:** Kenney Factory Kit 3.0.

**Source and provider:** Kenney.nl.

**License:** Creative Commons CC0 according to the provider page and local license file.

**Use in the project:** I used these 3D assets to construct the factory floor, conveyors, scanners, screens, industrial props, and bin areas. I chose this kit because it is lightweight, modular, consistent in visual style, and legally suitable for prototyping.

### Possible Examiner Questions

**Question:** Why did I not use NASA data as direct ground truth for the images?

**Suggested answer:** The NASA records and RecyBat24 images come from different sources. I used NASA data as representative health data, but I do not claim that a NASA health row describes the actual photographed battery. This distinction protects the scientific validity of the prototype.

**Question:** Why did I not train a deep model on RecyBat24?

**Suggested answer:** The current project focuses on system integration and explainable process control. I implemented a lightweight classifier and left trained CV models as a future extension because production-level training would require a larger labelled dataset, formal splits, evaluation metrics, and validation against real conveyor images.

## Methodology

I followed a modular engineering methodology:

1. Define the Re-X decision categories and operational workflow.
2. Select suitable public datasets and assets.
3. Implement a backend service for classification, health lookup, decision logic, logging, and passports.
4. Build a Unity digital twin representing the factory process.
5. Implement staged camera and sensor behavior.
6. Implement dashboard analytics.
7. Verify compile-time correctness and runtime data flow.
8. Document assumptions, limitations, and future improvements.

The decision method combines deterministic classification and rule-based risk scoring. The theoretical basis is multi-criteria decision-making: each risk factor contributes to a combined score, and the score is interpreted under a chosen operating policy.

The risk scoring factors include:

- low classifier confidence
- low SOH
- high temperature
- high cycle count
- high internal resistance
- unknown type
- policy mode
- visual/electrical damage score in mock mode

I chose additive scoring because it is transparent and easy to defend. A weighted machine-learning classifier could be used later, but only after sufficient labelled decision outcomes are collected.

## Detailed File-by-File Repository Explanation

This section documents the repository from top to bottom. Generated files are documented as generated artifacts rather than hand-authored design units. This includes `.venv`, `__pycache__`, Unity `Library`, Unity `Temp`, runtime `outputs/uploaded_images`, and `.meta` files. They are important for execution but are not the primary authored logic.

### Root folder

#### `README.md`

This is the main project overview. It explains the purpose, architecture, setup steps, data notes, real versus simulated components, demo workflow, and pilot relevance. I use it as the entry point for supervisors or reviewers.

#### `.gitignore`

This file defines which generated or environment-specific files should be excluded from version control. It exists to prevent cache files, virtual environments, and build artifacts from polluting the source repository.

#### `.DS_Store`

This is a macOS Finder metadata file. It has no project logic and should normally be ignored.

#### `.venv/`

This local Python virtual environment contains installed packages and command-line entry points such as `uvicorn`, `fastapi`, and `streamlit`. It is an execution environment, not authored source code. It allows reproducible local service execution without installing packages globally.

### Backend folder

#### `backend/README.md`

This file explains how to run the FastAPI backend and describes its role in classification, health lookup, risk scoring, logging, and passport updates.

#### `backend/requirements.txt`

This file declares backend dependencies. The backend uses FastAPI for HTTP services, Uvicorn for ASGI serving, pandas for CSV processing, Pillow and NumPy for image features, and supporting libraries for multipart file handling.

#### `backend/config.py`

This file centralizes paths and constants. It defines the project root, data directories, output directories, image upload directory, decision names, and decision-to-bin mapping. It solves the problem of hard-coded paths being repeated across modules. I chose this approach because configuration should be shared and explicit.

#### `backend/model.py`

This module implements the lightweight image classifier. It first checks path or filename labels for known classes. If path inference is unavailable, it opens the image and uses deterministic image features: aspect ratio, RGB channel means, and contrast. This is not a production deep-learning model. It is a transparent fallback classifier for demonstration.

Inputs:

- image path, bytes, or file-like object
- optional filename

Outputs:

- `detected_type`
- `confidence`

Limitations:

- It cannot identify subtle damage.
- It can be fooled by unusual crops or backgrounds.
- It relies partly on class labels embedded in paths when using the prepared dataset.

Future improvement:

- Replace with trained YOLO, RT-DETR, ResNet, EfficientNet, or MobileNet pipeline.

#### `backend/health_lookup.py`

This module loads `manifest.csv` and `battery_health_lookup.csv`. It maps a `battery_id` to a `health_id`, then retrieves the corresponding health record. If no match exists, it uses a stable hash of the battery ID to choose a deterministic fallback row. I chose deterministic fallback instead of pure randomness because repeated tests should be reproducible.

#### `backend/decision_engine.py`

This module implements the risk scoring and Re-X route selection. It converts multiple health and safety factors into a `risk_score`, maps that score to `risk_level`, and selects `reuse`, `remanufacture`, `recycle`, `quarantine`, `manual_review`, or `paused`.

The rule logic is intentionally auditable. For example, high SOH and low risk produce reuse, moderate SOH and acceptable risk produce remanufacture, low SOH produces recycling, and critical risk produces quarantine.

#### `backend/logger.py`

This module writes runtime inspection records to `outputs/inspection_log.csv` and `outputs/latest_decision.json`. It also supports manual override updates. It solves the traceability problem: every decision must be inspectable after the event.

#### `backend/passport.py`

This module creates and updates digital battery passport records in `outputs/battery_passports.json`. A passport stores identity, source metadata, latest inspection result, decision, target bin, and history. I implemented this because circular battery systems require persistent traceability.

#### `backend/main.py`

This is the FastAPI application. It defines:

- `/health`
- `/classify-battery`
- `/inspect-battery`
- `/override-decision`
- `/inspection-log`
- `/latest-decision`
- `/latest-received-image`
- `/battery-passport/{battery_id}`
- `/battery-passports`

The `/classify-battery` endpoint supports the two-step image-first workflow. The `/inspect-battery` endpoint preserves the earlier complete backend decision workflow. I retained both because they serve different experimental modes.

#### `backend/__pycache__/`

This folder contains compiled Python bytecode. It is generated automatically and has no design responsibility.

### Dashboard folder

#### `dashboard/README.md`

This file explains how the Streamlit dashboard reads logs and passports.

#### `dashboard/requirements.txt`

This declares dashboard dependencies such as Streamlit, pandas, and Plotly.

#### `dashboard/app.py`

This is the analytics dashboard. It reads `inspection_log.csv` and `battery_passports.json`, displays KPIs, charts decision distributions, shows process performance, exposes passport records, and provides a grant impact simulator. It solves the problem of communicating prototype outputs to non-technical reviewers.

#### `dashboard/__pycache__/`

Generated Python bytecode.

### Data folder

#### `data/README.md`

This explains the image dataset, health lookup, raw downloads, and rebuild command.

#### `data/image_sources.csv`

This records image source metadata for the RecyBat24 subset: detected class, local path, original title, source URL, download URL, license, usage terms, authors, citation, object name, and MIME type.

#### `data/manifest.csv`

This maps each demo battery ID to an image, source type, source area, previous application, health ID, image source URL, image license, and health source. It makes the demo process traceable.

#### `data/images/`

This folder contains the active image subset:

- `cylindrical/`: 30 cylindrical battery images.
- `pouch/`: 30 pouch battery images.
- `prismatic/`: 30 prismatic battery images.

Each image is a runtime classification sample.

#### `data/nasa_health/battery_health_lookup.csv`

This processed CSV provides NASA-derived health records. It is used for sample SOH and resistance modelling in backend inspection mode.

#### `data/raw/`

This contains raw source archives:

- `raw/nasa/NASA_5_Battery_Data_Set.zip`
- `raw/recybat24/recybat24.tar.gz`
- `raw/recybat24/classifications.zip`
- `raw/recybat24/README.md`
- `raw/wikimedia/` reserved for earlier or alternative image acquisition.

Raw archives are preserved for reproducibility.

### Scripts folder

#### `scripts/build_real_dataset.py`

This script downloads or extracts real datasets, processes images, writes `image_sources.csv`, builds the NASA health lookup, creates `manifest.csv`, and prepares the Unity `sample_manifest.json`. It is the dataset reproducibility script.

Major responsibilities:

- Download RecyBat24 archive.
- Extract and select class-specific images.
- Process NASA `.mat` files.
- Calculate SOH.
- Write manifest and metadata.

Alternative approaches such as manual copying were rejected because they are not reproducible.

#### `scripts/__pycache__/`

Generated Python bytecode.

### Docs folder

#### `docs/architecture.md`

Explains the system architecture and control twin behavior.

#### `docs/demo_script.md`

Provides a short demo script for presenting the system.

#### `docs/grant_concept_note.md`

Frames the project for funding or pilot-program discussion.

#### `docs/pilot_roadmap.md`

Defines future pilot stages from prototype to real deployment.

#### `docs/real_data_sources.md`

Documents RecyBat24, NASA PCoE, Kenney assets, licenses, and rebuild instructions.

#### `docs/unity_3d_models.md`

Documents 3D model sources and Unity asset usage.

#### `docs/thesis_report_en.md`

This English thesis-style technical report.

#### `docs/thesis_report_fa.md`

The Persian version of this thesis-style technical report.

### Outputs folder

#### `outputs/inspection_log.csv`

Runtime inspection log. It records timestamps, battery IDs, image IDs, detected shapes, decisions, confidence, SOH, temperature, cycle count, risk score, target bin, reasons, image paths, feature JSON, and processing time.

#### `outputs/latest_decision.json`

Latest decision snapshot used by dashboards and demos.

#### `outputs/battery_passports.json`

Digital passport store. It contains per-battery identity, latest state, decision, source metadata, and history.

#### `outputs/uploaded_images/`

Runtime uploaded image archive. It contains images received by the backend during inspection/classification. These are generated evidence files for traceability.

### Unity project folder

#### `unity/BatteryReXControlTwin/README.md`

Unity-specific setup and project notes.

#### `Assets/Editor/BatteryReXSceneBuilder.cs`

This editor script procedurally constructs the demo scene. It creates the floor, conveyors, camera station, sensor stations, decision areas, ABB-style robot arm, UI canvas, KPI panel, control panel, labels, markers, and component wiring. I used procedural scene generation to keep the scene reproducible.

#### `Assets/Scenes/BatteryRecoveryMicroFactory.unity`

The generated Unity scene file. It contains the visual micro-factory and all object references after scene construction.

#### `Assets/Scripts/ABBCRBArmController.cs`

Controls the procedural ABB CRB-style arm. It moves the gripper above the battery, picks it, carries it to a destination slot, releases it, and returns home. It approximates robotic pick-and-place without full inverse kinematics.

#### `Assets/Scripts/BatteryAgent.cs`

Represents a battery instance in Unity. It stores battery ID, image path, source metadata, current state, final decision, target bin, current shape, and visual category. It applies classification and decision results to the visual controller.

#### `Assets/Scripts/BatteryCategoryMapper.cs`

Provides shared mappings between strings, enums, labels, colors, and bin names. It prevents inconsistent category naming across scripts.

#### `Assets/Scripts/BatteryInfoPanel.cs`

Controls the right-side UI panel. It shows image preview, shape classification, confidence, mock sensor readings, SOH, risk, decision, reason, target bin, and backend image metadata. It updates step by step during the new two-stage workflow.

#### `Assets/Scripts/BatteryInspectionClient.cs`

Handles HTTP communication with the backend. It sends the image to `/classify-battery`, parses classification results, generates mock sensor values, calculates mock Re-X decisions, and supports the older full inspection and override workflow.

#### `Assets/Scripts/BatterySpawner.cs`

Loads the Unity sample manifest and spawns unknown batteries at the intake point. It waits for a battery to be sorted before spawning the next one.

#### `Assets/Scripts/BatteryVisualController.cs`

Builds procedural 3D geometry for unknown, cylindrical, pouch, and prismatic batteries. It supports neutral shape-only rendering and final decision-color rendering.

#### `Assets/Scripts/ConveyorController.cs`

Moves batteries through the staged process: camera station, thermal station, electrical station, impedance station, damage-vision station, decision gate, and robot sorting.

#### `Assets/Scripts/InspectionCameraController.cs`

Controls the camera flash and capture indication at the first station.

#### `Assets/Scripts/OperatorControlPanel.cs`

Handles start, pause, resume, emergency stop, manual mode, manual sort approval, policy dropdown, conveyor speed, confidence threshold, reuse SOH threshold, and manual overrides.

#### `Assets/Scripts/ProcessLoggerClient.cs`

Maintains live KPI counts inside Unity: inspected, reuse, remanufacture, recycle, quarantine, and latest decision.

#### `Assets/Scripts/RandomBatteryImageProvider.cs`

Loads available images from `data/images` or the Unity manifest and selects a random image for each inspection.

#### `Assets/Scripts/RobotSorter.cs`

Receives a final target bin and sorts the battery using the robotic arm or fallback movement. It reserves placement slots in each bin.

#### `Assets/StreamingAssets/sample_manifest.json`

Unity-readable manifest used at runtime by the spawner.

#### `Assets/ThirdParty/KenneyFactoryKit/`

Contains the Kenney Factory Kit assets, previews, license, and imported FBX models. `Models/FBX format` contains 287 files including FBX models and Unity metadata. `Previews` contains 286 preview images and metadata. These are third-party assets used to construct the industrial environment.

#### `.meta` files

Unity `.meta` files store asset GUIDs and import settings. They are necessary for Unity project consistency but do not contain authored application logic.

#### `Packages/manifest.json`

Defines Unity package dependencies such as TextMeshPro, Timeline, UI, and navigation-related packages.

#### `Packages/packages-lock.json`

Locks Unity package versions for reproducibility.

#### `ProjectSettings/`

Contains Unity project settings: audio, physics, graphics, quality, tags, input, time, package manager settings, and project version. These files define the execution environment of the Unity project.

#### `Library/`, `Temp/`, `Logs/`, `UserSettings/`

Unity-generated local project folders. They contain caches, imported packages, editor state, logs, temporary files, and local user settings. I treat them as generated execution artifacts rather than source design modules.

## Computer Vision Pipeline

The implemented CV pipeline is intentionally simple and transparent:

1. Unity selects an image.
2. The image is sent to the backend.
3. The backend attempts class inference from path or filename.
4. If class inference fails, it computes aspect ratio, mean RGB values, and contrast.
5. It returns a class and confidence.

Theory:

- Pouch cells are often flatter and wider.
- Cylindrical cells often have elongated round profiles.
- Prismatic cells often appear as rectangular block-like units.
- Image statistics can provide weak heuristics when no trained model is present.

This is not a substitute for production vision. It is a prototype classifier designed for clear behavior and local execution.

## Machine Learning Components

The current project does not train a deep learning model. I treat the classifier as a deterministic CV heuristic and the decision engine as a rule-based model. This is a valid engineering choice for an early-stage operational twin because:

- labelled Re-X outcome data is unavailable;
- safety decisions require explainability;
- the project focuses on integration of a complete process;
- a future trained model can be inserted behind the same API.

Competing models considered:

- **YOLO/RT-DETR:** strong for detection, but requires annotation and training.
- **ResNet/EfficientNet/MobileNet:** strong for image classification, but requires formal training and validation.
- **SVM or random forest on image features:** simpler than deep learning but less robust for real images.
- **End-to-end decision model:** rejected because the decision requires non-image sensor data.

## Robotics and Navigation Components

The robotic component demonstrates pick-and-place sorting. I implemented a procedural arm rather than importing a full robot model because the purpose is to show process response to decisions. The arm has base, shoulder, elbow, wrist, flange, gripper, and fingers. It moves through approach, pick, lift, carry, drop, release, and return-home states.

The conveyor is waypoint-based. I chose waypoint movement because it is deterministic, easy to inspect, and sufficient for a single-battery demonstration. Full physics-based conveyor belts or ROS 2 control would be more realistic but unnecessary for this prototype.

## Digital Twin Design

The digital twin represents process state, not merely geometry. It includes:

- physical layout,
- animated movement,
- camera station,
- sensor stations,
- decision gate,
- robot sorting,
- operator controls,
- runtime UI,
- logs and passports.

The twin supports supervisory explanation. A reviewer can see what data is known at each stage and when the decision becomes available.

## API and Backend Services

The backend exposes endpoints for health checking, image classification, full inspection, overrides, logs, latest result, and passports. Inputs are multipart form data or JSON. Outputs are structured JSON. I chose HTTP because Unity can call it easily and because it matches real industrial integration patterns where machines and services communicate over network APIs.

## Experimental Setup

To run the system:

1. Start the backend with Uvicorn.
2. Start the Streamlit dashboard.
3. Open the Unity project.
4. Rebuild the scene if needed.
5. Press Play.
6. Click Start Batch.

Verification performed:

- Python backend compile check passed.
- Unity runtime scripts compiled against local Unity assemblies.
- Unity editor scene-builder compiled against local Unity editor assemblies.
- Unity batchmode scene rebuild was blocked when the project was already open in another Unity instance.

## Evaluation and Results

The prototype successfully demonstrates:

- image-only shape classification;
- neutral shape transformation before decision coloring;
- staged mock sensor updates;
- Re-X decision routing;
- robotic sorting;
- runtime logging;
- digital passport updating;
- dashboard visualization.

Because the classifier is heuristic and the health readings are mock values in the two-step Unity process, the evaluation is functional rather than statistical. A future trained model would require classification accuracy, precision, recall, F1-score, confusion matrix, and robustness testing under varied lighting and backgrounds.

## Limitations

- The system cannot infer SOH from an image.
- Mock sensor data is not a substitute for real BMS/electrical/thermal/impedance measurements.
- The classifier is lightweight and not production-grade.
- NASA health data does not correspond physically to RecyBat24 images.
- The robotic arm is a simplified simulation.
- The dashboard uses local files rather than a database.
- The prototype does not implement industrial safety certification, PLC integration, ROS 2, OPC UA, or real hardware control.

## Future Work

I would extend the project through:

- trained object detection and classification;
- visual damage detection;
- real thermal camera input;
- voltage and capacity testing integration;
- impedance measurement integration;
- QR/serial battery passport scanning;
- PostgreSQL or time-series database storage;
- ROS 2 robot integration;
- OPC UA/PLC conveyor control;
- cloud deployment;
- formal model evaluation;
- field pilot with Dubai battery sources.

## Thesis Defense Questions and Answers

**Question:** What is the central contribution of this work?

**Answer:** My central contribution is an integrated operational prototype that connects image classification, staged sensor abstraction, rule-based Re-X decisions, a Unity digital twin, robotic sorting, traceability logs, passports, and dashboard analytics.

**Question:** Why do I use mock sensor data?

**Answer:** I use mock sensor data because the current physical input is only an image. Health data cannot be derived reliably from the image alone. The mock stations show where real sensors would be placed in a physical deployment.

**Question:** Why are there both `/classify-battery` and `/inspect-battery` endpoints?

**Answer:** I retained both because they support different workflows. `/classify-battery` supports the two-step camera-first process. `/inspect-battery` preserves a complete backend decision mode that uses linked health records.

**Question:** What would make this production-ready?

**Answer:** Production readiness would require real sensors, validated CV models, calibrated thresholds, safety certification, hardware integration, database storage, cybersecurity controls, operator training, and field validation.

**Question:** Why did I choose Unity?

**Answer:** I chose Unity because it allows interactive 3D process simulation, UI controls, camera/sensor visualization, and animated robot behavior in one environment.

**Question:** What is the mathematical basis of SOH?

**Answer:** I use SOH as the ratio of measured capacity to rated or initial capacity. This is a standard interpretation for capacity-based battery health.

**Question:** Why did I not use a neural network for Re-X routing?

**Answer:** I did not have labelled examples mapping real measured batteries to verified Re-X outcomes. A rule-based engine is more explainable and appropriate for a prototype.

## Conclusion

I designed and implemented the Circular Battery Decision Twin as a local prototype for safe, explainable, and traceable battery recovery process control. The system demonstrates the correct engineering distinction between image-based classification and sensor-based health assessment. It integrates a backend, datasets, decision logic, Unity simulation, robotic sorting, runtime logging, passports, and dashboard analytics. The result is a technical foundation for future research, pilot testing, and industrial extension.

## References

1. Acaro Chacon, X. C., Lo Scudo, F., Cappuccino, G., and Dodaro, C. RecyBat24: an Image Dataset for LIB Recycling. Zenodo. https://zenodo.org/records/15226091
2. NASA Open Data Portal. Li-ion Battery Aging Datasets. NASA Ames Prognostics Center of Excellence. https://data.nasa.gov/dataset/li-ion-battery-aging-datasets
3. NASA Prognostics Center of Excellence Data Set Repository. https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
4. Kenney. Factory Kit. https://kenney.nl/assets/factory-kit
5. FastAPI documentation. https://fastapi.tiangolo.com/
6. Streamlit documentation. https://docs.streamlit.io/
7. Unity documentation. https://docs.unity3d.com/
