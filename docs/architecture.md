# Architecture

```text
Unity process simulation
  - operator start/pause/e-stop
  - policy and threshold controls
  - battery/conveyor/robot simulation
  - manual override UI
        |
        | multipart/form-data: battery_id + image + settings
        v
FastAPI Backend
  - image classifier
  - manifest lookup
  - NASA-style SOH lookup
  - risk scoring
  - Re-X decision engine
        |
        | JSON decision
        v
Unity runtime
  - updates battery info panel
  - animates sorting to returned target_bin
  - updates local KPIs

Backend Runtime Logger
  - outputs/inspection_log.csv
  - outputs/latest_decision.json
  - outputs/battery_passports.json
        |
        v
Streamlit Dashboard
  - KPIs
  - decision/risk/type charts
  - process performance
  - passport viewer
  - grant impact simulator
```

## Prototype Behavior

Unity does more than render a static model. It mirrors the state of a simulated battery recovery process, sends live inspection requests to the backend, allows the operator to adjust policies, changes robot behavior based on returned decisions, and logs process state for analytics and future optimization.

## Extension Points

- Replace the lightweight classifier with a trained YOLO/ResNet model.
- Swap CSV/JSON logging for PostgreSQL or a time-series database.
- Add ROS 2 commands in `RobotSorter` after a lab robot is available.
- Add OPC UA or PLC integration at the conveyor control boundary.
- Add thermal image and voltage sensor channels to `/inspect-battery`.
