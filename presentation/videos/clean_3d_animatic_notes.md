# Clean 3D Battery Re-X Animatic Notes

Generated MP4: `Battery_ReX_Clean_3D_Process_Animatic.mp4`
Duration: approximately 52 seconds
Resolution: 1280x720
Frame rate: 20 fps

## Design Direction

- Cleaner and tidier than the first storyboard.
- Uses one isometric 3D factory line instead of many dense panels.
- Shows one highlighted battery at a time.
- Uses one main UI card per stage for readability.
- Keeps the project logic technically correct.

## Technical Rules Preserved

- Image data is used only for physical shape classification.
- SOH prediction uses health parameters: cycle count, temperature, voltage, resistance and battery type.
- The model shown is RandomForestRegressor.
- The decision thresholds are reuse >=80, remanufacture 60-79, recycle 30-59 and quarantine below 30 or unsafe.

## Shot List

1. Clean 3D Process Overview (00-07s): A tidy isometric view introduces the full Battery Re-X digital twin pipeline.
2. Camera Shape Detection (07-14s): The camera captures an image and classifies only the visible battery shape.
3. Health Sensor Data (14-22s): The battery moves through sensor stations that provide the data needed for SOH prediction.
4. ML SOH Prediction (22-30s): The backend model predicts State of Health from health parameters, not from the image.
5. Re-X Decision (30-37s): SOH thresholds and safety rules determine reuse, remanufacture, recycle or quarantine.
6. Robot Sorting (37-46s): The robot picks the battery and releases it into the correct colored bin.
7. Final Digital Twin View (46-52s): The clean 3D overview ends with the live battery record and synchronized decision result.