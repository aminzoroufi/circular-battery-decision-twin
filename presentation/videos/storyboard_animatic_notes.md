# Battery Re-X Storyboard Animatic Notes

Generated MP4: `Battery_ReX_Digital_Twin_Storyboard_Animatic.mp4`
Duration: approximately 75 seconds
Resolution: 1280x720
Frame rate: 20 fps

## Technical Accuracy

- The camera image is shown only as the source for physical battery type classification.
- SOH prediction is shown as a second-stage backend ML task using cycle count, temperature, voltage, internal resistance and battery type.
- The displayed SOH example is 94.49 percent and the selected model is RandomForestRegressor.
- Re-X decision thresholds are: >=80 reuse, 60-79 remanufacture, 30-59 recycle, below 30 or unsafe quarantine.
- Unity sensor readings are represented as mock values because the available image dataset does not contain health measurements.

## Shot List

1. Smart Factory Hero (00-06s): Opening view of the Battery Re-X digital twin: conveyors, inspection stations, robot sorting and live dashboards.
2. Unknown Battery Intake (06-12s): The next battery waits until the current image classification and backend response are complete.
3. Camera Image Capture (12-19s): The camera captures an image and sends it to the AI backend for physical shape classification only.
4. Computer Vision Shape Detection (19-26s): The model detects cylindrical, pouch, prismatic or unknown. Battery health is not inferred from the image.
5. Sensor Health Data Collection (26-34s): Thermal, voltage, internal resistance, safety and cycle-count data update one by one for the battery.
6. ML-Based SOH Prediction (34-41s): The backend predicts State of Health from sensor parameters using the selected RandomForestRegressor model.
7. Re-X Decision Engine (41-48s): Lifecycle rules and safety overrides assign the final Re-X category and target bin.
8. Robot Pick And Release (48-57s): The collaborative robot grips, lifts and releases the battery into the correct colored bin.
9. Unity-Style Digital Twin Dashboard (57-63s): Each battery has its own inspection record with captured image, sensor data, SOH and Re-X decision.
10. AR/VR Remote Supervision (63-69s): Remote supervisors monitor speed, safety, AI thresholds and sorting outcomes through a virtual control room.
11. Final Circular Workflow (69-75s): The full automated line supports reuse, remanufacturing, recycling and quarantine decision support.

## Suggested Voiceover

Battery lifecycle decisions require more than visual inspection. In this Battery Re-X digital twin, each incoming battery is first identified by computer vision. The camera detects only the physical type: cylindrical, pouch, prismatic, or unknown. Health prediction happens in the second stage, where sensor stations collect cycle count, temperature, voltage and internal resistance. The backend ML model predicts State of Health from these health parameters, not from the image. The Re-X decision engine combines predicted SOH with safety rules to route each battery to reuse, remanufacturing, recycling or quarantine. The digital twin updates every battery record in real time, while a collaborative robot performs the final pick-and-place sorting task.