# Battery Re-X Digital Twin Video Generation Prompt

## Master Prompt

Create a 60-90 second hyper-realistic cinematic industrial product demo video in 16:9, 4K if available.

The video presents a futuristic AI-powered Battery Re-X Digital Twin and Robotic Sorting System inside a clean smart factory. It should look like a premium commercial industrial technology showcase for investors, supervisors, factory clients, and thesis reviewers. The tone is serious, advanced, realistic, and sellable.

The factory is a clean automated battery sorting facility with reflective floors, industrial conveyors, high-resolution inspection cameras, thermal sensors, voltage and impedance testing stations, transparent safety barriers, digital dashboards, robotic arms, and believable holographic AR interfaces. No human worker physically touches the batteries or operates the production line. Remote supervision is shown only through AR/VR avatars or control-room digital twin dashboards.

Important technical rule:
The camera image is used only for physical battery type classification: cylindrical, pouch, prismatic, or unknown. Do not show SOH being predicted from the image alone. SOH must be predicted from downstream health data collected by sensor stations: cycle count, temperature, voltage, internal resistance, battery type, timestamp, and safety flags.

Core process:
An unknown battery enters on a conveyor. The conveyor stops under an AI camera station. A high-resolution industrial camera with LED ring captures the battery image and sends it to the AI vision backend. The AI classifies the visible battery shape only. Then the battery moves through thermal camera, voltage tester, impedance/internal resistance station, IR scanner, safety inspection camera, and digital passport scanner. A backend ML panel predicts SOH from sensor data using RandomForestRegressor. The Re-X decision engine applies lifecycle rules and safety overrides. A white collaborative robot arm similar to ABB GoFa / ABB CRB style, without brand logos, picks the battery and releases it into the correct color-coded bin.

Decision rules:
- SOH >= 80% -> Reuse
- 60-79% -> Remanufacture
- 30-59% -> Recycle
- SOH < 30% or unsafe readings -> Quarantine

Color code:
- Green = Reuse
- Orange/Yellow = Remanufacture
- Blue = Recycle
- Red = Quarantine
- Gray = Unknown / Manual Review

Readable UI data to show:
- Battery ID: BAT_001
- Detected Type: Cylindrical
- Vision Confidence: 92%
- Cycle Count: 430
- Temperature: 31.2 C
- Voltage: 3.72 V
- Internal Resistance: 0.052 ohm
- Predicted SOH: 94.49%
- Model Used: RandomForestRegressor
- Risk Level: Low
- Re-X Category: Reuse
- Target Bin: reuse_bin
- Digital Passport: Updated

The robot must align the gripper, close around the battery, lift it, move to the correct bin, release it clearly, open the gripper, let the battery settle naturally inside the bin, and return to home position. The next battery waits while the current battery is inspected or sorted. Batteries must not collide or overlap.

Camera style:
Cinematic wide shots, macro close-ups, battery POV, robot POV, top-down factory overview, slow dolly shots, smooth orbit around the robot arm, realistic motion blur, shallow depth of field, lens reflections, soft volumetric lighting, and crisp readable UI overlays.

Final text overlay:
"AI-Powered Robotic Battery Sorting"
"Digital Twin Controlled Circular Manufacturing"
"Computer Vision + SOH Prediction + Re-X Decision Support"
"Automated Reuse, Remanufacturing, Recycling & Quarantine Workflow"

## Negative Prompt

Do not make it cartoonish, low-poly, game-like, toy-like, messy, dirty, old, or unrealistic. Do not show human workers manually touching batteries. Do not show SOH coming from image alone. Do not skip camera inspection. Do not skip sensor stage. Do not skip backend ML prediction. Do not skip robot release into the bin. Do not let batteries collide on the conveyor. Do not show random robot arms that do not resemble a modern white collaborative robot. Do not show brand logos. Do not make UI unreadable or meaningless. Do not show impossible sci-fi machinery. Do not show the battery disappearing. Do not show the robot holding the battery forever. Do not use sparks, fire, smoke, or explosions unless explicitly showing a controlled quarantine warning.

## Shot-By-Shot Timeline

### Shot 1 | 0-7 s | Smart Factory Hero
Wide cinematic opening shot of a clean futuristic smart factory with automated battery conveyors, white collaborative robot arms, inspection cameras, sensor stations, transparent safety barriers, reflective floor, LED strips, digital dashboards, and floating industrial AR panels. Multiple batteries are queued on the conveyor, separated with realistic spacing.

On-screen text:
AI-Powered Battery Re-X Sorting

### Shot 2 | 7-13 s | Battery POV
Battery point-of-view shot moving along the conveyor toward the AI camera station. The camera rides low near an unknown battery. Sensors, conveyor rollers, robotic arms, safety gates, and holographic UI panels pass overhead. The factory feels real and physically grounded.

On-screen text:
Unknown Battery Intake

### Shot 3 | 13-20 s | Camera Inspection
The conveyor stops under a high-resolution industrial camera with LED ring light. Macro close-up of camera lens reflection on the battery surface. UI overlay appears: "Image Captured", "Sending to AI Backend", "Visual Classification Running". Show a small captured image thumbnail in the panel.

On-screen text:
Camera image used for physical type only

### Shot 4 | 20-27 s | AI Shape Classification
Animated scan lines and wireframe overlay map onto the battery. The AI identifies the battery as cylindrical, pouch, or prismatic. UI clearly states: "Image classification only: physical type detected". Example: "Detected Type: Cylindrical", "Vision Confidence: 92%". Do not show SOH here.

On-screen text:
Detected Type: Cylindrical

### Shot 5 | 27-38 s | Sensor Stage
The battery moves through thermal camera, voltage tester, impedance/internal resistance tester, IR scanner, safety inspection camera, and digital passport scanner. Each station updates a floating battery-specific AI panel. Show temperature, voltage, resistance, cycle count, timestamp, and safety flags appearing one by one.

On-screen text:
Health data collected from sensors

### Shot 6 | 38-47 s | Backend ML SOH Prediction
Show a backend ML holographic panel connected to the digital twin. UI displays:
"SOH Prediction Model"
"Input: cycle_count, temperature, voltage, resistance, battery_type"
"Model: RandomForestRegressor"
"Predicted SOH: 94.49%"
"Confidence: 98.1%"
"Safety Check: Passed"

On-screen text:
SOH predicted from sensor data, not image

### Shot 7 | 47-55 s | Re-X Decision Engine
Show a decision panel with lifecycle thresholds and safety override logic. A glowing green route path appears from the battery to the Reuse bin. UI says: "Recommended Route: Reuse", "Target Bin: reuse_bin", "Digital Battery Passport Updated".

On-screen text:
Re-X Decision: Reuse

### Shot 8 | 55-68 s | Robot Pick And Release
A white collaborative robot arm similar to ABB GoFa / ABB CRB style, without logos, aligns its gripper with the battery. Smooth realistic motion: gripper closes, lifts battery, moves to the glowing green Reuse bin, opens gripper, battery clearly releases and settles inside the bin, robot returns home. Conveyor stays stopped during robot handling.

On-screen text:
Robot Task Confirmed -> reuse_bin

### Shot 9 | 68-76 s | Unity-Style Digital Twin Dashboard
Cut to a digital twin monitoring dashboard showing a Unity-style 3D factory layout. Each battery has its own floating AI inspection panel with captured image thumbnail, detected type, sensor values, predicted SOH, Re-X category, target bin, and timestamp. Show live factory status, queue status, and robot cycle time.

On-screen text:
Digital Twin Synchronization Active

### Shot 10 | 76-84 s | AR/VR Remote Supervision
Remote supervisors appear as semi-transparent holographic avatars in a virtual control room. They monitor conveyor speed, robot pick timing, AI confidence threshold, sorting rules, manual override, safety status, and digital twin synchronization. No one physically touches batteries on the factory floor.

On-screen text:
Remote AR/VR Supervision

### Shot 11 | 84-90 s | Final Hero Shot
Final wide cinematic hero shot of the full automated line working smoothly. Multiple batteries are classified, health-scored, routed, and sorted into Reuse, Remanufacture, Recycle, and Quarantine bins. Holographic data panels float above the factory. The system looks scalable, reliable, and investor-ready.

Final overlay:
AI-Powered Robotic Battery Sorting
Digital Twin Controlled Circular Manufacturing
Computer Vision + SOH Prediction + Re-X Decision Support

## Voiceover Script

Battery lifecycle decisions require more than visual inspection.

In this Battery Re-X digital twin, each incoming battery is first identified by computer vision. The camera detects only the physical type: cylindrical, pouch, prismatic, or unknown.

Health prediction happens in the second stage. Sensor stations collect cycle count, temperature, voltage, and internal resistance.

The backend ML model predicts State of Health from these health parameters, not from the image.

The Re-X decision engine combines predicted SOH with safety rules to route each battery to reuse, remanufacturing, recycling, or quarantine.

The digital twin updates every battery record in real time, while a collaborative robot performs the final pick-and-place sorting task.

This creates an explainable, automated workflow for circular battery lifecycle decision support.

## Ultra-Short Prompt For Single-Prompt Video Tools

Create a 60-90 second hyper-realistic cinematic smart factory demo of an AI-powered Battery Re-X Digital Twin and robotic sorting line. Unknown batteries enter on conveyors. Camera station captures image and AI classifies only physical shape: cylindrical, pouch, prismatic, unknown. Then battery moves through thermal, voltage, impedance/resistance, IR, and safety sensor stations. Backend ML predicts SOH from cycle count, temperature, voltage, resistance, and battery type, not from image. UI shows RandomForestRegressor, predicted SOH 94.49%, confidence 98.1%, risk level low, Re-X decision reuse. Decision rules: SOH >=80 reuse, 60-79 remanufacture, 30-59 recycle, below 30 or unsafe quarantine. White ABB GoFa-style collaborative robot, no logo, picks battery and clearly releases it into the correct green Reuse bin. Clean futuristic factory, realistic conveyors, sensors, robot arms, glass barriers, LED lighting, holographic industrial UI, Unity-style digital twin dashboard, AR/VR remote supervision. No cartoon, no game look, no humans touching batteries, no SOH from image alone, no skipped sensor stage, no skipped robot release, no battery collisions.
