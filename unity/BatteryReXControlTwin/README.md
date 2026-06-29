# Unity Project

Open this folder in Unity 2021.3 LTS or newer.

## Scene Setup

The project includes an editor scene builder at `Assets/Editor/BatteryReXSceneBuilder.cs`.

The scene builder uses downloaded free FBX models from Kenney Factory Kit 3.0, stored in:

```text
Assets/ThirdParty/KenneyFactoryKit/Models/FBX format
```

The main model names used are `floor-large.fbx`, `conveyor-long-stripe-sides.fbx`, `scanner-high.fbx`, `screen-panel-wide.fbx`, and `hopper-square.fbx`. The ABB CRB-style arm and battery physical shapes are generated from Unity primitives so the gripper and battery body can animate/change at runtime.

If the scene opens empty or says `No cameras rendering`, run:

```text
Battery Re-X > Rebuild Demo Scene
```

Unity will generate the complete demo scene with:

- Main camera and lighting.
- Intake zone, conveyor, camera station, sensor-style decision station, ABB CRB-style arm, and four lifecycle decision areas.
- Operator control panel.
- Live KPI panel.
- Battery info panel.
- Wired runtime scripts for spawning, backend inspection, sorting, and override.

The default backend URL is `http://127.0.0.1:8000`.

## Demo Flow

1. Start the FastAPI backend.
2. Press Play in Unity.
3. Click Start Batch.
4. A battery spawns as the same default unknown shape.
5. The active battery moves to the inspection station and the conveyor stops.
6. `RandomBatteryImageProvider` selects a random image from `data/images`.
7. The Unity AI panel immediately displays that exact selected image.
8. Unity uploads the selected image and operator settings to `/inspect-battery`.
9. The backend returns `detected_shape`, `decision_category`, confidence, uncertainty, SOH, risk, reason, and route metadata.
10. Unity uses `detected_shape` only for the physical mesh: cylindrical, pouch, prismatic, or unknown.
11. Unity uses `decision_category` for material color and destination: reuse, remanufacture, recycle, or quarantine.
12. The ABB CRB-style gripper picks the battery and releases it into the matching lifecycle decision area.
13. After the arm returns home, the next battery cycle starts.

## Inspector Wiring

If you use `Battery Re-X > Rebuild Demo Scene`, these references are assigned automatically. For manual setup:

- `BatteryReXController`
  - `BatterySpawner`: assign `IntakePoint`, `ConveyorController`, and `BatteryInspectionClient`.
  - `ConveyorController`: assign `InspectionStationPoint` and `OperatorControlPanel`.
  - `BatteryInspectionClient`: assign `OperatorControlPanel`, `BatteryInfoPanel`, `RobotSorter`, `ProcessLoggerClient`, `InspectionCameraController`, and `RandomBatteryImageProvider`.
  - `RobotSorter`: assign `reuse_bin`, `remanufacture_bin`, `recycle_bin`, `quarantine_bin`, and `ABBCRBArmController`.
  - `OperatorControlPanel`: assign `BatterySpawner`, `RobotSorter`, `BatteryInspectionClient`, and the UI buttons/dropdowns/sliders.
- `Random Battery Image Provider`
  - `RandomBatteryImageProvider.imageFolderRelativeToProject`: `data/images`
  - `manifestFileName`: `sample_manifest.json`
- `Battery Info Panel`
  - `BatteryInfoPanel`: assign all text fields plus `Sent Image Preview`.
- `Inspection Camera Controller`
  - `InspectionCameraController`: assign `Inspection Flash Light` and `Camera Flash Indicator`.
- Spawned battery objects
  - Created automatically with `BatteryAgent` and `BatteryVisualController`.
