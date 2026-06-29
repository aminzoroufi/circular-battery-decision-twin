# 90-Second Demo Script

1. Show the Unity micro-factory with intake, conveyor, industrial camera station, ABB CRB-style arm, and four lifecycle areas: Reuse, Remanufacture, Recycle, Quarantine.
2. Click Start Batch.
3. A default unknown battery arrives at the inspection station and the conveyor stops.
4. Unity selects a random real test image, displays it in the AI panel, and sends that same image to FastAPI.
5. The backend returns physical shape, lifecycle decision, confidence, uncertainty, SOH, risk level, and route metadata.
6. Unity changes the same battery into the detected physical shape and colors it by lifecycle decision.
7. The ABB CRB-style gripper picks it and releases it into the matching lifecycle area.
8. Change policy from balanced to safety_first.
9. Inspect another battery and show stricter decision behavior.
10. Override one AI decision to quarantine and show the robot re-route the battery.
11. Open the Streamlit dashboard to show updated logs, KPIs, route distribution, and the battery passport.

Closing line: "The prototype demonstrates a practical decision-support workflow for circular battery recovery: Unity supervises the process, FastAPI returns explainable routing decisions, and every decision is logged for analytics and traceability."
