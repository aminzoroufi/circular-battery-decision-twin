#if UNITY_EDITOR
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public static class BatteryReXSceneBuilder
{
    const string ScenePath = "Assets/Scenes/BatteryRecoveryMicroFactory.unity";
    const string KenneyFbxRoot = "Assets/ThirdParty/KenneyFactoryKit/Models/FBX format/";
    static readonly Color DarkPanel = new Color(0.07f, 0.08f, 0.09f, 0.88f);
    static readonly Color Panel = new Color(0.12f, 0.14f, 0.16f, 0.92f);
    static readonly Color Accent = new Color(0.05f, 0.55f, 0.85f, 1f);

    [InitializeOnLoadMethod]
    static void AutoRepairOpenDemoScene()
    {
        EditorApplication.delayCall += () =>
        {
            bool targetProject = Application.dataPath.Replace("\\", "/").EndsWith("/unity/BatteryReXControlTwin/Assets");
            if (!targetProject)
            {
                return;
            }

            Scene activeScene = SceneManager.GetActiveScene();
            bool isDemoScene = activeScene.path.EndsWith("BatteryRecoveryMicroFactory.unity");
            bool isTemporarySceneFromFailedRepair = string.IsNullOrEmpty(activeScene.path) && GameObject.Find("Battery Re-X Demo Root") != null;
            if (!isDemoScene && !isTemporarySceneFromFailedRepair)
            {
                return;
            }

            bool looksBroken = Camera.main == null || GameObject.Find("BatteryReXController") == null;
            bool needsDownloadedModelScene = false;
            bool needsMotionScene = GameObject.Find("ABB CRB 15000 GoFa Arm") == null ||
                GameObject.Find("Inspection Flash Light") == null ||
                GameObject.Find("Random Battery Image Provider") == null ||
                GameObject.Find("Industrial AI Camera") == null ||
                GameObject.Find("Thermal Camera Station") == null ||
                GameObject.Find("Impedance Sensor Station") == null ||
                GameObject.Find("Label - REUSE") == null;
            if (looksBroken || isTemporarySceneFromFailedRepair || needsDownloadedModelScene || needsMotionScene)
            {
                Debug.Log("Circular Battery Decision Twin scene needs the robot/camera/image-preview layout. Rebuilding generated demo scene.");
                BuildDemoScene(false);
            }
        };
    }

    [MenuItem("Battery Re-X/Rebuild Demo Scene")]
    public static void BuildDemoSceneFromMenu()
    {
        BuildDemoScene(true);
    }

    public static void BuildDemoSceneFromCommandLine()
    {
        BuildDemoScene(false);
    }

    static void BuildDemoScene(bool showDialog)
    {
        AssetDatabase.Refresh();
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        GameObject root = new GameObject("Battery Re-X Demo Root");

        Camera camera = CreateCamera();
        Light light = CreateLight();
        camera.transform.SetParent(root.transform);
        light.transform.SetParent(root.transform);

        CreateFactoryFloor(root.transform);

        Transform intakePoint = CreateMarker(root.transform, "IntakePoint", new Vector3(-7.7f, 0.22f, 0f));
        Transform inspectionPoint = CreateMarker(root.transform, "InspectionStationPoint", new Vector3(0f, 0.22f, 0f));
        Transform thermalPoint = CreateMarker(root.transform, "ThermalCameraPoint", new Vector3(1.7f, 0.22f, 0f));
        Transform electricalPoint = CreateMarker(root.transform, "ElectricalTestPoint", new Vector3(3.2f, 0.22f, 0f));
        Transform impedancePoint = CreateMarker(root.transform, "ImpedanceStationPoint", new Vector3(4.7f, 0.22f, 0f));
        Transform damageVisionPoint = CreateMarker(root.transform, "DamageVisionPoint", new Vector3(6.2f, 0.22f, 0f));
        Transform decisionPoint = CreateMarker(root.transform, "ReXDecisionGatePoint", new Vector3(7.45f, 0.22f, 0f));
        Transform reuseBin = CreateDecisionArea(root.transform, "REUSE", "reuse_bin", new Vector3(10.10f, 0.22f, 2.75f), BatteryCategoryMapper.DecisionColor(DecisionCategory.Reuse));
        Transform remanBin = CreateDecisionArea(root.transform, "REMANUFACTURE", "remanufacture_bin", new Vector3(11.75f, 0.22f, 0.92f), BatteryCategoryMapper.DecisionColor(DecisionCategory.Remanufacture));
        Transform recycleBin = CreateDecisionArea(root.transform, "RECYCLE", "recycle_bin", new Vector3(11.75f, 0.22f, -0.92f), BatteryCategoryMapper.DecisionColor(DecisionCategory.Recycle));
        Transform quarantineBin = CreateDecisionArea(root.transform, "QUARANTINE", "quarantine_bin", new Vector3(10.10f, 0.22f, -2.75f), BatteryCategoryMapper.DecisionColor(DecisionCategory.Quarantine));
        InspectionCameraController inspectionCamera = CreateInspectionCameraController(root.transform);
        CreateSensorStations(root.transform);
        ABBCRBArmController abbArm = CreateAbbCrbArm(root.transform);

        GameObject controller = new GameObject("BatteryReXController");
        controller.transform.SetParent(root.transform);
        BatterySpawner spawner = controller.AddComponent<BatterySpawner>();
        ConveyorController conveyor = controller.AddComponent<ConveyorController>();
        RobotSorter sorter = controller.AddComponent<RobotSorter>();
        BatteryInspectionClient client = controller.AddComponent<BatteryInspectionClient>();
        OperatorControlPanel controls = controller.AddComponent<OperatorControlPanel>();
        GameObject imageProviderGo = new GameObject("Random Battery Image Provider");
        imageProviderGo.transform.SetParent(root.transform);
        RandomBatteryImageProvider imageProvider = imageProviderGo.AddComponent<RandomBatteryImageProvider>();
        imageProvider.imageFolderRelativeToProject = "data/images";
        imageProvider.manifestFileName = "sample_manifest.json";

        GameObject canvas = CreateCanvas(root.transform);
        ProcessLoggerClient logger = CreateKpiPanel(canvas.transform);
        BuildControlPanel(canvas.transform, controls);
        CreateSelectedBatteryDetailPanel(canvas.transform);

        spawner.manifestFileName = "sample_manifest.json";
        spawner.intakePoint = intakePoint;
        spawner.conveyorController = conveyor;
        spawner.inspectionClient = client;
        spawner.spawnIntervalSeconds = 0.55f;
        spawner.releaseDelayAfterCameraSeconds = 0.35f;
        spawner.maxActiveBatteries = 4;

        conveyor.inspectionStation = inspectionPoint;
        conveyor.thermalCameraStation = thermalPoint;
        conveyor.electricalTestStation = electricalPoint;
        conveyor.impedanceStation = impedancePoint;
        conveyor.damageVisionStation = damageVisionPoint;
        conveyor.decisionStation = decisionPoint;
        conveyor.operatorControlPanel = controls;
        conveyor.slowSpeed = 0.75f;
        conveyor.normalSpeed = 1.35f;
        conveyor.fastSpeed = 2.25f;
        conveyor.inspectionDwellSeconds = 0.25f;
        conveyor.sensorDwellSeconds = 0.45f;

        sorter.reuseBin = reuseBin;
        sorter.remanufactureBin = remanBin;
        sorter.recycleBin = recycleBin;
        sorter.quarantineBin = quarantineBin;
        sorter.slotsPerRow = 3;
        sorter.slotRows = 2;
        sorter.slotSpacing = 0.45f;
        sorter.stackLayerHeight = 0.18f;
        sorter.armController = abbArm;

        client.backendBaseUrl = "http://127.0.0.1:8000";
        client.operatorControlPanel = controls;
        client.batteryInfoPanel = null;
        client.robotSorter = sorter;
        client.processLoggerClient = logger;
        client.inspectionCamera = inspectionCamera;
        client.imageProvider = imageProvider;

        controls.batterySpawner = spawner;
        controls.robotSorter = sorter;
        controls.inspectionClient = client;

        EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), ScenePath);
        AssetDatabase.Refresh();

        if (showDialog)
        {
            EditorUtility.DisplayDialog("Circular Battery Decision Twin", "Demo scene rebuilt. Start the FastAPI backend, then press Play and click Start Batch.", "OK");
        }
    }

    static Camera CreateCamera()
    {
        GameObject go = new GameObject("Main Camera");
        Camera camera = go.AddComponent<Camera>();
        go.tag = "MainCamera";
        camera.clearFlags = CameraClearFlags.Skybox;
        camera.fieldOfView = 50f;
        camera.transform.position = new Vector3(2.6f, 9.2f, -11.4f);
        camera.transform.rotation = Quaternion.Euler(57f, 0f, 0f);
        return camera;
    }

    static Light CreateLight()
    {
        GameObject go = new GameObject("Directional Light");
        Light light = go.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.1f;
        go.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        return light;
    }

    static void CreateFactoryFloor(Transform root)
    {
        CreateKenneyModel(root, "floor-large.fbx", "factory_floor_floor-large", new Vector3(2.0f, -0.04f, 0f), Quaternion.identity, new Vector3(10.5f, 1f, 5.2f), new Color(0.22f, 0.24f, 0.25f));
        CreatePrimitivePart(root, PrimitiveType.Cube, "continuous_main_conveyor_belt", new Vector3(0.05f, 0.135f, 0f), Quaternion.identity, new Vector3(16.3f, 0.055f, 1.05f), new Color(0.055f, 0.060f, 0.068f));
        CreatePrimitivePart(root, PrimitiveType.Cube, "continuous_main_conveyor_left_rail", new Vector3(0.05f, 0.225f, 0.62f), Quaternion.identity, new Vector3(16.4f, 0.10f, 0.10f), new Color(0.62f, 0.68f, 0.82f));
        CreatePrimitivePart(root, PrimitiveType.Cube, "continuous_main_conveyor_right_rail", new Vector3(0.05f, 0.225f, -0.62f), Quaternion.identity, new Vector3(16.4f, 0.10f, 0.10f), new Color(0.62f, 0.68f, 0.82f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_intake_rotated_90", new Vector3(-6.45f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.35f, 1f, 2.35f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_pre_camera_rotated_90", new Vector3(-4.05f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.35f, 1f, 2.35f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_camera_rotated_90", new Vector3(-1.65f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.35f, 1f, 2.35f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_sensor_a_rotated_90", new Vector3(0.75f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.35f, 1f, 2.35f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_sensor_b_rotated_90", new Vector3(3.15f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.35f, 1f, 2.35f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_sensor_c_rotated_90", new Vector3(5.55f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.35f, 1f, 2.35f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_rex_entry_rotated_90", new Vector3(7.65f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.35f, 1f, 1.75f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-stripe-sides-junction-t.fbx", "conveyor_rex_sort_junction", new Vector3(8.55f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.35f, 1f, 1.35f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_reuse_sort_lane", new Vector3(9.25f, 0.1f, 1.75f), Quaternion.identity, new Vector3(1.15f, 1f, 1.8f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_quarantine_sort_lane", new Vector3(9.25f, 0.1f, -1.75f), Quaternion.identity, new Vector3(1.15f, 1f, 1.8f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "conveyor-long-stripe-sides.fbx", "conveyor_reman_recycle_lane", new Vector3(10.75f, 0.1f, 0f), Quaternion.Euler(0f, 90f, 0f), new Vector3(1.15f, 1f, 1.75f), new Color(0.08f, 0.09f, 0.10f));
        CreateKenneyModel(root, "scanner-high.fbx", "inspection_camera_scanner-high", new Vector3(-0.1f, 0.1f, -0.95f), Quaternion.Euler(0f, 0f, 0f), new Vector3(1.15f, 1.15f, 1.15f), new Color(0.18f, 0.18f, 0.20f));
        CreateKenneyModel(root, "screen-panel-wide.fbx", "rex_decision_station_screen-panel-wide", new Vector3(7.45f, 0.1f, -1.25f), Quaternion.Euler(0f, -20f, 0f), new Vector3(1.2f, 1.2f, 1.2f), new Color(0.08f, 0.22f, 0.34f));
        CreateKenneyModel(root, "pipe-large-valve.fbx", "process_pipe_pipe-large-valve", new Vector3(4.4f, 0.1f, 1.55f), Quaternion.Euler(0f, 90f, 0f), new Vector3(0.8f, 0.8f, 0.8f), new Color(0.38f, 0.42f, 0.45f));
        CreateKenneyModel(root, "warning-traffic.fbx", "safety_marker_warning-traffic", new Vector3(-6.65f, 0.08f, -1.25f), Quaternion.identity, new Vector3(0.75f, 0.75f, 0.75f), new Color(0.9f, 0.6f, 0.12f));
        CreateKenneyModel(root, "button-floor-square.fbx", "operator_floor_button-floor-square", new Vector3(-7.75f, 0.08f, -1.25f), Quaternion.identity, new Vector3(0.9f, 0.9f, 0.9f), new Color(0.1f, 0.45f, 0.8f));
        CreateLabel(root, "Unknown intake", new Vector3(-7.65f, 0.35f, 0.78f), 0.040f, Color.white);
        CreateLabel(root, "AI camera", new Vector3(-0.65f, 0.35f, -1.55f), 0.040f, Color.white);
        CreateLabel(root, "Re-X gate", new Vector3(6.8f, 0.35f, -2.05f), 0.040f, Color.white);
    }

    static void CreateSensorStations(Transform root)
    {
        CreateKenneyModel(root, "scanner-low.fbx", "Thermal Camera Station", new Vector3(1.7f, 0.12f, -0.92f), Quaternion.identity, new Vector3(1.05f, 1.05f, 1.05f), new Color(0.16f, 0.18f, 0.20f));
        CreatePrimitivePart(root, PrimitiveType.Cube, "Thermal Camera Body", new Vector3(1.7f, 1.25f, -0.62f), Quaternion.Euler(18f, 0f, 0f), new Vector3(0.34f, 0.22f, 0.24f), new Color(0.12f, 0.05f, 0.04f));
        CreatePrimitivePart(root, PrimitiveType.Sphere, "Thermal Lens", new Vector3(1.7f, 1.12f, -0.43f), Quaternion.identity, new Vector3(0.16f, 0.16f, 0.16f), new Color(1.0f, 0.28f, 0.08f));
        CreateLabel(root, "Thermal camera", new Vector3(1.2f, 0.52f, -1.72f), 0.045f, new Color(1f, 0.55f, 0.32f));

        CreateKenneyModel(root, "machine-bed.fbx", "Electrical Capacity Test Station", new Vector3(3.2f, 0.10f, 1.0f), Quaternion.Euler(0f, 180f, 0f), new Vector3(0.9f, 0.9f, 0.9f), new Color(0.20f, 0.22f, 0.25f));
        CreatePrimitivePart(root, PrimitiveType.Cylinder, "Voltage Probe Positive", new Vector3(3.02f, 0.88f, 0.28f), Quaternion.Euler(0f, 0f, 0f), new Vector3(0.04f, 0.34f, 0.04f), new Color(0.95f, 0.72f, 0.18f));
        CreatePrimitivePart(root, PrimitiveType.Cylinder, "Voltage Probe Negative", new Vector3(3.38f, 0.88f, 0.28f), Quaternion.Euler(0f, 0f, 0f), new Vector3(0.04f, 0.34f, 0.04f), new Color(0.30f, 0.32f, 0.36f));
        CreateLabel(root, "Voltage / capacity", new Vector3(2.55f, 0.52f, 1.58f), 0.045f, new Color(0.9f, 0.82f, 0.42f));

        CreateKenneyModel(root, "machine-fortified.fbx", "Impedance Sensor Station", new Vector3(4.7f, 0.10f, -1.0f), Quaternion.identity, new Vector3(0.8f, 0.8f, 0.8f), new Color(0.18f, 0.21f, 0.25f));
        CreatePrimitivePart(root, PrimitiveType.Cube, "Impedance Contact Plate A", new Vector3(4.48f, 0.42f, -0.12f), Quaternion.identity, new Vector3(0.08f, 0.32f, 0.34f), new Color(0.46f, 0.62f, 0.78f));
        CreatePrimitivePart(root, PrimitiveType.Cube, "Impedance Contact Plate B", new Vector3(4.92f, 0.42f, -0.12f), Quaternion.identity, new Vector3(0.08f, 0.32f, 0.34f), new Color(0.46f, 0.62f, 0.78f));
        CreateLabel(root, "Impedance / IR", new Vector3(4.08f, 0.52f, -1.72f), 0.045f, new Color(0.68f, 0.86f, 1f));

        CreateKenneyModel(root, "scanner-high.fbx", "Damage Vision Station", new Vector3(6.2f, 0.12f, 0.96f), Quaternion.Euler(0f, 180f, 0f), new Vector3(0.95f, 0.95f, 0.95f), new Color(0.18f, 0.18f, 0.20f));
        CreatePrimitivePart(root, PrimitiveType.Cube, "Damage Vision Camera", new Vector3(6.2f, 1.18f, 0.58f), Quaternion.Euler(-18f, 0f, 0f), new Vector3(0.38f, 0.20f, 0.24f), new Color(0.09f, 0.10f, 0.12f));
        CreatePrimitivePart(root, PrimitiveType.Cube, "Damage Vision Light Bar", new Vector3(6.2f, 0.86f, 0.40f), Quaternion.identity, new Vector3(0.62f, 0.06f, 0.06f), new Color(0.70f, 0.95f, 1f));
        CreateLabel(root, "Damage vision", new Vector3(5.72f, 0.52f, 1.76f), 0.045f, new Color(0.75f, 0.95f, 1f));
    }

    static InspectionCameraController CreateInspectionCameraController(Transform root)
    {
        GameObject controller = new GameObject("Inspection Camera Controller");
        controller.transform.SetParent(root);
        InspectionCameraController cameraController = controller.AddComponent<InspectionCameraController>();

        CreatePrimitivePart(
            controller.transform,
            PrimitiveType.Cube,
            "Industrial AI Camera",
            new Vector3(0f, 1.35f, -0.78f),
            Quaternion.Euler(18f, 0f, 0f),
            new Vector3(0.42f, 0.24f, 0.28f),
            new Color(0.10f, 0.12f, 0.15f)
        );
        CreatePrimitivePart(
            controller.transform,
            PrimitiveType.Cylinder,
            "Industrial AI Camera Lens",
            new Vector3(0f, 1.20f, -0.58f),
            Quaternion.Euler(90f, 0f, 0f),
            new Vector3(0.12f, 0.08f, 0.12f),
            new Color(0.03f, 0.04f, 0.05f)
        );
        CreatePrimitivePart(
            controller.transform,
            PrimitiveType.Cube,
            "AI Camera Capture Ray",
            new Vector3(0f, 0.80f, -0.28f),
            Quaternion.Euler(30f, 0f, 0f),
            new Vector3(0.035f, 0.035f, 1.0f),
            new Color(0.20f, 0.70f, 1f, 0.72f)
        );

        GameObject lightGo = new GameObject("Inspection Flash Light");
        lightGo.transform.SetParent(controller.transform);
        lightGo.transform.position = new Vector3(0f, 1.45f, -0.72f);
        Light flashLight = lightGo.AddComponent<Light>();
        flashLight.type = LightType.Point;
        flashLight.range = 4.2f;
        flashLight.color = new Color(0.82f, 0.95f, 1f);
        flashLight.enabled = false;

        GameObject indicator = CreatePrimitivePart(
            controller.transform,
            PrimitiveType.Sphere,
            "Camera Flash Indicator",
            new Vector3(0f, 1.1f, -0.88f),
            Quaternion.identity,
            new Vector3(0.16f, 0.16f, 0.16f),
            new Color(0.12f, 0.20f, 0.24f)
        );

        cameraController.flashLight = flashLight;
        cameraController.flashIndicatorRenderer = indicator.GetComponent<Renderer>();
        CreateLabel(root, "AI Camera Station", new Vector3(-0.55f, 0.58f, -1.9f), 0.046f, new Color(0.82f, 0.94f, 1f));
        return cameraController;
    }

    static ABBCRBArmController CreateAbbCrbArm(Transform root)
    {
        GameObject armRoot = new GameObject("ABB CRB 15000 GoFa Arm");
        armRoot.transform.SetParent(root);

        Color abbWhite = new Color(0.82f, 0.84f, 0.92f);
        Color abbBlue = new Color(0.62f, 0.67f, 0.95f);
        Color jointColor = new Color(0.70f, 0.72f, 0.86f);

        GameObject baseJoint = CreatePrimitivePart(armRoot.transform, PrimitiveType.Cylinder, "ABB CRB Base Joint", new Vector3(8.45f, 0.18f, 0f), Quaternion.identity, new Vector3(0.55f, 0.18f, 0.55f), abbWhite);
        CreatePrimitivePart(armRoot.transform, PrimitiveType.Cylinder, "ABB CRB Pedestal", new Vector3(8.45f, 0.55f, 0f), Quaternion.identity, new Vector3(0.34f, 0.32f, 0.34f), abbBlue);
        GameObject shoulderJoint = CreatePrimitivePart(armRoot.transform, PrimitiveType.Sphere, "ABB CRB Shoulder Joint", new Vector3(8.45f, 0.98f, 0f), Quaternion.identity, new Vector3(0.34f, 0.34f, 0.34f), jointColor);
        GameObject upperArmLink = CreatePrimitivePart(armRoot.transform, PrimitiveType.Cube, "ABB CRB Upper Arm Link", new Vector3(7.95f, 1.15f, 0f), Quaternion.identity, new Vector3(0.16f, 0.8f, 0.16f), abbWhite);
        GameObject elbowJoint = CreatePrimitivePart(armRoot.transform, PrimitiveType.Sphere, "ABB CRB Elbow Joint", new Vector3(7.60f, 1.35f, 0f), Quaternion.identity, new Vector3(0.28f, 0.28f, 0.28f), jointColor);
        GameObject forearmLink = CreatePrimitivePart(armRoot.transform, PrimitiveType.Cube, "ABB CRB Forearm Link", new Vector3(7.25f, 1.2f, 0f), Quaternion.identity, new Vector3(0.14f, 0.7f, 0.14f), abbWhite);
        GameObject wristJoint = CreatePrimitivePart(armRoot.transform, PrimitiveType.Sphere, "ABB CRB Wrist Joint", new Vector3(6.95f, 1.05f, 0f), Quaternion.identity, new Vector3(0.22f, 0.22f, 0.22f), jointColor);
        GameObject flange = CreatePrimitivePart(armRoot.transform, PrimitiveType.Cylinder, "ABB CRB Tool Flange", new Vector3(6.85f, 1.05f, 0f), Quaternion.Euler(90f, 0f, 0f), new Vector3(0.14f, 0.08f, 0.14f), abbBlue);

        GameObject gripper = new GameObject("ABB CRB Gripper TCP");
        gripper.transform.SetParent(armRoot.transform);
        gripper.transform.position = new Vector3(7.35f, 0.95f, 0f);

        CreateLocalPrimitivePart(gripper.transform, PrimitiveType.Cube, "ABB CRB Gripper Palm", Vector3.zero, Quaternion.identity, new Vector3(0.34f, 0.10f, 0.22f), new Color(0.20f, 0.22f, 0.26f));
        GameObject leftFinger = CreateLocalPrimitivePart(gripper.transform, PrimitiveType.Cube, "ABB CRB Left Finger", new Vector3(-0.18f, -0.18f, 0f), Quaternion.identity, new Vector3(0.06f, 0.30f, 0.07f), new Color(0.12f, 0.13f, 0.15f));
        GameObject rightFinger = CreateLocalPrimitivePart(gripper.transform, PrimitiveType.Cube, "ABB CRB Right Finger", new Vector3(0.18f, -0.18f, 0f), Quaternion.identity, new Vector3(0.06f, 0.30f, 0.07f), new Color(0.12f, 0.13f, 0.15f));

        ABBCRBArmController arm = armRoot.AddComponent<ABBCRBArmController>();
        arm.baseJoint = baseJoint.transform;
        arm.shoulderJoint = shoulderJoint.transform;
        arm.elbowJoint = elbowJoint.transform;
        arm.wristJoint = wristJoint.transform;
        arm.upperArmLink = upperArmLink.transform;
        arm.forearmLink = forearmLink.transform;
        arm.toolFlange = flange.transform;
        arm.gripper = gripper.transform;
        arm.leftFinger = leftFinger.transform;
        arm.rightFinger = rightFinger.transform;
        arm.placementHeight = 0f;
        arm.liftHeight = 0.95f;

        CreateLabel(root, "ABB CRB 15000 GoFa-style arm", new Vector3(7.45f, 0.38f, 1.35f), 0.05f, Color.white);
        return arm;
    }

    static GameObject CreateCube(Transform parent, string name, Vector3 position, Vector3 scale, Color color)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.SetParent(parent);
        go.transform.position = position;
        go.transform.localScale = scale;
        Renderer renderer = go.GetComponent<Renderer>();
        renderer.sharedMaterial = CreateMaterial(color);
        return go;
    }

    static GameObject CreatePrimitivePart(Transform parent, PrimitiveType primitiveType, string name, Vector3 position, Quaternion rotation, Vector3 scale, Color color)
    {
        GameObject go = GameObject.CreatePrimitive(primitiveType);
        go.name = name;
        go.transform.SetParent(parent);
        go.transform.position = position;
        go.transform.rotation = rotation;
        go.transform.localScale = scale;
        Renderer renderer = go.GetComponent<Renderer>();
        renderer.sharedMaterial = CreateMaterial(color);
        return go;
    }

    static GameObject CreateLocalPrimitivePart(Transform parent, PrimitiveType primitiveType, string name, Vector3 localPosition, Quaternion localRotation, Vector3 localScale, Color color)
    {
        GameObject go = GameObject.CreatePrimitive(primitiveType);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPosition;
        go.transform.localRotation = localRotation;
        go.transform.localScale = localScale;
        Renderer renderer = go.GetComponent<Renderer>();
        renderer.sharedMaterial = CreateMaterial(color);
        return go;
    }

    static Transform CreateMarker(Transform parent, string name, Vector3 position)
    {
        GameObject marker = new GameObject(name);
        marker.transform.SetParent(parent);
        marker.transform.position = position;
        return marker.transform;
    }

    static Transform CreateDecisionArea(Transform parent, string label, string name, Vector3 position, Color color)
    {
        CreatePrimitivePart(parent, PrimitiveType.Cube, name + "_sorting_area", position + new Vector3(0f, -0.08f, 0f), Quaternion.identity, new Vector3(1.55f, 0.10f, 1.18f), new Color(0.24f, 0.25f, 0.28f));
        CreatePrimitivePart(parent, PrimitiveType.Cube, name + "_color_strip_front", position + new Vector3(0f, 0.02f, 0.64f), Quaternion.identity, new Vector3(1.50f, 0.08f, 0.08f), color);
        CreatePrimitivePart(parent, PrimitiveType.Cube, name + "_color_strip_back", position + new Vector3(0f, 0.02f, -0.64f), Quaternion.identity, new Vector3(1.50f, 0.06f, 0.06f), color * 0.75f);
        CreateKenneyModel(parent, "hopper-square.fbx", name + "_hopper-square", position + new Vector3(0f, -0.03f, 0f), Quaternion.identity, new Vector3(1.24f, 1.0f, 1.24f), new Color(0.40f, 0.42f, 0.46f));
        CreateLabel(parent, label, position + new Vector3(-0.72f, 0.52f, 0.82f), 0.044f, color);

        GameObject target = new GameObject(name);
        target.transform.SetParent(parent);
        target.transform.position = position;
        return target.transform;
    }

    static GameObject CreateKenneyModel(Transform parent, string modelName, string objectName, Vector3 position, Quaternion rotation, Vector3 scale, Color fallbackColor)
    {
        GameObject asset = LoadKenneyModel(modelName);
        GameObject go;
        if (asset != null)
        {
            go = (GameObject)PrefabUtility.InstantiatePrefab(asset);
            go.name = objectName;
        }
        else
        {
            go = CreateCube(parent, objectName + "_fallback_cube", position, scale, fallbackColor);
            return go;
        }

        go.transform.SetParent(parent);
        go.transform.position = position;
        go.transform.rotation = rotation;
        go.transform.localScale = scale;
        return go;
    }

    static GameObject LoadKenneyModel(string modelName)
    {
        return AssetDatabase.LoadAssetAtPath<GameObject>(KenneyFbxRoot + modelName);
    }

    static Material CreateMaterial(Color color)
    {
        Material material = new Material(Shader.Find("Standard"));
        material.color = color;
        return material;
    }

    static void CreateLabel(Transform parent, string text, Vector3 position, float size, Color color)
    {
        GameObject go = new GameObject("Label - " + text);
        go.transform.SetParent(parent);
        go.transform.position = position;
        go.transform.rotation = Quaternion.Euler(65f, 0f, 0f);
        TextMesh mesh = go.AddComponent<TextMesh>();
        mesh.text = text;
        mesh.fontSize = 48;
        mesh.characterSize = Mathf.Min(size, 0.040f);
        mesh.color = color;
        mesh.anchor = TextAnchor.MiddleLeft;
    }

    static GameObject CreateCanvas(Transform root)
    {
        GameObject canvasGo = new GameObject("Operator UI Canvas");
        canvasGo.transform.SetParent(root);
        Canvas canvas = canvasGo.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        CanvasScaler scaler = canvasGo.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        canvasGo.AddComponent<GraphicRaycaster>();

        if (Object.FindObjectOfType<EventSystem>() == null)
        {
            GameObject eventSystem = new GameObject("EventSystem");
            eventSystem.AddComponent<EventSystem>();
            eventSystem.AddComponent<StandaloneInputModule>();
        }

        return canvasGo;
    }

    static void BuildControlPanel(Transform canvas, OperatorControlPanel controls)
    {
        GameObject panel = CreatePanel(canvas, "Operator Control Panel", new Vector2(12f, -12f), new Vector2(355f, 720f), new Vector2(0f, 1f), new Vector2(0f, 1f));
        CreateText(panel.transform, "Circular Battery\nDecision Twin", new Vector2(20f, -28f), new Vector2(310f, 56f), 22, FontStyle.Bold, TextAnchor.MiddleLeft);

        controls.startBatchButton = CreateButton(panel.transform, "Start Batch", new Vector2(20f, -100f), new Vector2(150f, 42f), new Color(0.10f, 0.55f, 0.28f));
        controls.pauseButton = CreateButton(panel.transform, "Pause", new Vector2(185f, -100f), new Vector2(135f, 42f), new Color(0.44f, 0.45f, 0.46f));
        controls.resumeButton = CreateButton(panel.transform, "Resume Auto", new Vector2(20f, -152f), new Vector2(150f, 42f), Accent);
        controls.emergencyStopButton = CreateButton(panel.transform, "Emergency Stop", new Vector2(185f, -152f), new Vector2(135f, 42f), new Color(0.80f, 0.12f, 0.08f));
        controls.manualModeButton = CreateButton(panel.transform, "Manual Mode", new Vector2(20f, -204f), new Vector2(150f, 42f), new Color(0.33f, 0.28f, 0.70f));
        controls.approveManualSortButton = CreateButton(panel.transform, "Approve Sort", new Vector2(185f, -204f), new Vector2(135f, 42f), new Color(0.18f, 0.49f, 0.76f));

        CreateText(panel.transform, "Policy Mode", new Vector2(20f, -270f), new Vector2(150f, 26f), 16, FontStyle.Bold, TextAnchor.MiddleLeft);
        controls.policyDropdown = CreateDropdown(panel.transform, new Vector2(20f, -306f), new Vector2(300f, 38f), new[] { "balanced", "safety_first", "recovery_maximization" }, 0);

        CreateText(panel.transform, "Conveyor Speed", new Vector2(20f, -358f), new Vector2(150f, 26f), 16, FontStyle.Bold, TextAnchor.MiddleLeft);
        controls.conveyorSpeedDropdown = CreateDropdown(panel.transform, new Vector2(20f, -394f), new Vector2(300f, 38f), new[] { "slow", "normal", "fast" }, 1);

        CreateText(panel.transform, "Confidence Threshold", new Vector2(20f, -452f), new Vector2(220f, 26f), 16, FontStyle.Bold, TextAnchor.MiddleLeft);
        controls.confidenceThresholdLabel = CreateText(panel.transform, "0.65", new Vector2(260f, -452f), new Vector2(60f, 26f), 16, FontStyle.Normal, TextAnchor.MiddleRight);
        controls.confidenceThresholdSlider = CreateSlider(panel.transform, new Vector2(20f, -492f), new Vector2(300f, 28f), 0.1f, 0.95f, 0.65f);

        CreateText(panel.transform, "Reuse SOH Threshold", new Vector2(20f, -540f), new Vector2(220f, 26f), 16, FontStyle.Bold, TextAnchor.MiddleLeft);
        controls.reuseSohThresholdLabel = CreateText(panel.transform, "0.80", new Vector2(260f, -540f), new Vector2(60f, 26f), 16, FontStyle.Normal, TextAnchor.MiddleRight);
        controls.reuseSohThresholdSlider = CreateSlider(panel.transform, new Vector2(20f, -580f), new Vector2(300f, 28f), 0.45f, 0.95f, 0.80f);

        CreateText(panel.transform, "Manual Override", new Vector2(20f, -628f), new Vector2(220f, 26f), 16, FontStyle.Bold, TextAnchor.MiddleLeft);
        controls.overrideReuseButton = CreateButton(panel.transform, "Reuse", new Vector2(20f, -664f), new Vector2(70f, 34f), BatteryCategoryMapper.DecisionColor(DecisionCategory.Reuse));
        controls.overrideRemanufactureButton = CreateButton(panel.transform, "Reman", new Vector2(98f, -664f), new Vector2(74f, 34f), BatteryCategoryMapper.DecisionColor(DecisionCategory.Remanufacture));
        controls.overrideRecycleButton = CreateButton(panel.transform, "Recycle", new Vector2(180f, -664f), new Vector2(70f, 34f), BatteryCategoryMapper.DecisionColor(DecisionCategory.Recycle));
        controls.overrideQuarantineButton = CreateButton(panel.transform, "Quarantine", new Vector2(258f, -664f), new Vector2(78f, 34f), BatteryCategoryMapper.DecisionColor(DecisionCategory.Quarantine));
    }

    static BatteryInfoPanel CreateInfoPanel(Transform canvas)
    {
        GameObject panel = CreatePanel(canvas, "Battery Info Panel", new Vector2(-12f, -12f), new Vector2(500f, 1000f), new Vector2(1f, 1f), new Vector2(1f, 1f));
        BatteryInfoPanel info = panel.AddComponent<BatteryInfoPanel>();
        CreateText(panel.transform, "AI Inspection Panel", new Vector2(20f, -28f), new Vector2(260f, 32f), 22, FontStyle.Bold, TextAnchor.MiddleLeft);
        GameObject badge = CreatePanel(panel.transform, "Decision Badge", new Vector2(320f, -24f), new Vector2(150f, 36f), new Vector2(0f, 1f), new Vector2(0f, 1f));
        info.decisionBadgeImage = badge.GetComponent<Image>();
        info.decisionBadgeImage.color = new Color(0.34f, 0.36f, 0.40f);
        info.decisionBadgeText = CreateText(badge.transform, "PENDING", new Vector2(0f, 0f), new Vector2(150f, 36f), 16, FontStyle.Bold, TextAnchor.MiddleCenter);

        int y = -78;
        info.batteryIdText = AddInfoRow(panel.transform, "Battery ID", ref y);
        info.detectedTypeText = AddInfoRow(panel.transform, "Physical Shape", ref y);
        info.finalDecisionText = AddInfoRow(panel.transform, "Lifecycle Decision", ref y);
        info.confidenceText = AddInfoRow(panel.transform, "Confidence", ref y);
        info.uncertaintyText = AddInfoRow(panel.transform, "Uncertainty", ref y);
        info.sohText = AddInfoRow(panel.transform, "SOH", ref y);
        info.riskScoreText = AddInfoRow(panel.transform, "Risk Score", ref y);
        info.riskLevelText = AddInfoRow(panel.transform, "Risk Level", ref y);
        info.policyModeText = AddInfoRow(panel.transform, "Policy", ref y);
        info.statusText = AddInfoRow(panel.transform, "Pipeline", ref y);
        info.timestampText = AddInfoRow(panel.transform, "Timestamp", ref y);
        info.aiDecisionText = AddInfoRow(panel.transform, "Raw AI Route", ref y);
        info.sortCategoryText = AddInfoRow(panel.transform, "Sort Area", ref y);
        info.targetBinText = AddInfoRow(panel.transform, "Target Bin", ref y);

        CreateText(panel.transform, "Camera Feed / Latest Captured Image", new Vector2(20f, y - 8f), new Vector2(300f, 24f), 15, FontStyle.Bold, TextAnchor.MiddleLeft);
        info.sentImagePreview = CreateRawImage(panel.transform, "Sent Image Preview", new Vector2(20f, y - 42f), new Vector2(165f, 108f));
        CreateText(panel.transform, "Sent file", new Vector2(205f, y - 42f), new Vector2(90f, 22f), 13, FontStyle.Bold, TextAnchor.MiddleLeft);
        info.sentImagePathText = CreateText(panel.transform, "-", new Vector2(205f, y - 68f), new Vector2(260f, 42f), 13, FontStyle.Normal, TextAnchor.UpperLeft);
        CreateText(panel.transform, "Backend received", new Vector2(205f, y - 118f), new Vector2(150f, 22f), 13, FontStyle.Bold, TextAnchor.MiddleLeft);
        info.backendReceivedImageText = CreateText(panel.transform, "-", new Vector2(205f, y - 144f), new Vector2(260f, 48f), 13, FontStyle.Normal, TextAnchor.UpperLeft);
        y -= 194;

        CreateText(panel.transform, "Reasoning / Explanation", new Vector2(20f, y - 6f), new Vector2(220f, 24f), 15, FontStyle.Bold, TextAnchor.MiddleLeft);
        info.reasonText = CreateText(panel.transform, "Waiting for inspection.", new Vector2(20f, y - 76f), new Vector2(455f, 60f), 14, FontStyle.Normal, TextAnchor.UpperLeft);
        y -= 100;

        CreateText(panel.transform, "Data Used", new Vector2(20f, y - 6f), new Vector2(180f, 24f), 15, FontStyle.Bold, TextAnchor.MiddleLeft);
        info.featuresText = CreateText(panel.transform, "-", new Vector2(20f, y - 38f), new Vector2(455f, 108f), 13, FontStyle.Normal, TextAnchor.UpperLeft);
        y -= 150;

        info.metadataText = CreateText(panel.transform, "Estimated fields are labelled in the data section.", new Vector2(20f, y - 6f), new Vector2(455f, 40f), 12, FontStyle.Italic, TextAnchor.UpperLeft);
        return info;
    }

    static BatterySelectionDetailPanel CreateSelectedBatteryDetailPanel(Transform canvas)
    {
        GameObject panel = new GameObject("Selected Battery Detail Panel");
        panel.transform.SetParent(canvas, false);
        return panel.AddComponent<BatterySelectionDetailPanel>();
    }

    static ProcessLoggerClient CreateKpiPanel(Transform canvas)
    {
        GameObject panel = CreatePanel(canvas, "Live KPI Panel", new Vector2(385f, -12f), new Vector2(560f, 96f), new Vector2(0f, 1f), new Vector2(0f, 1f));
        ProcessLoggerClient logger = panel.AddComponent<ProcessLoggerClient>();
        CreateText(panel.transform, "Live KPIs", new Vector2(16f, -18f), new Vector2(110f, 26f), 18, FontStyle.Bold, TextAnchor.MiddleLeft);

        logger.inspectedCountText = AddKpi(panel.transform, "Inspected", new Vector2(16f, -62f));
        logger.reuseCountText = AddKpi(panel.transform, "Reuse", new Vector2(118f, -62f));
        logger.remanufactureCountText = AddKpi(panel.transform, "Reman", new Vector2(210f, -62f));
        logger.recycleCountText = AddKpi(panel.transform, "Recycle", new Vector2(302f, -62f));
        logger.quarantineCountText = AddKpi(panel.transform, "Quarantine", new Vector2(394f, -62f));
        logger.latestDecisionText = CreateText(panel.transform, "waiting", new Vector2(392f, -18f), new Vector2(140f, 26f), 15, FontStyle.Bold, TextAnchor.MiddleRight);
        return logger;
    }

    static Text AddInfoRow(Transform parent, string label, ref int y)
    {
        CreateText(parent, label, new Vector2(20f, y), new Vector2(160f, 22f), 14, FontStyle.Bold, TextAnchor.MiddleLeft);
        Text value = CreateText(parent, "-", new Vector2(190f, y), new Vector2(285f, 22f), 14, FontStyle.Normal, TextAnchor.MiddleRight);
        y -= 30;
        return value;
    }

    static Text AddKpi(Transform parent, string label, Vector2 position)
    {
        CreateText(parent, label, position + new Vector2(0f, 18f), new Vector2(86f, 18f), 12, FontStyle.Bold, TextAnchor.MiddleCenter);
        return CreateText(parent, "0", position, new Vector2(86f, 24f), 20, FontStyle.Bold, TextAnchor.MiddleCenter);
    }

    static GameObject CreatePanel(Transform parent, string name, Vector2 anchoredPosition, Vector2 size, Vector2 anchor, Vector2 pivot)
    {
        GameObject panel = new GameObject(name);
        panel.transform.SetParent(parent, false);
        Image image = panel.AddComponent<Image>();
        image.color = name.Contains("Control") ? DarkPanel : Panel;
        RectTransform rect = panel.GetComponent<RectTransform>();
        rect.anchorMin = anchor;
        rect.anchorMax = anchor;
        rect.pivot = pivot;
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = size;
        return panel;
    }

    static Text CreateText(Transform parent, string text, Vector2 anchoredPosition, Vector2 size, int fontSize, FontStyle style, TextAnchor alignment)
    {
        GameObject go = new GameObject("Text - " + text);
        go.transform.SetParent(parent, false);
        Text uiText = go.AddComponent<Text>();
        uiText.text = text;
        uiText.font = GetBuiltInUiFont();
        uiText.fontSize = fontSize;
        uiText.fontStyle = style;
        uiText.alignment = alignment;
        uiText.color = Color.white;
        uiText.horizontalOverflow = HorizontalWrapMode.Wrap;
        uiText.verticalOverflow = VerticalWrapMode.Overflow;
        RectTransform rect = go.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(0f, 1f);
        rect.pivot = new Vector2(0f, 1f);
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = size;
        return uiText;
    }

    static RawImage CreateRawImage(Transform parent, string name, Vector2 anchoredPosition, Vector2 size)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        RawImage image = go.AddComponent<RawImage>();
        image.color = new Color(0.18f, 0.20f, 0.23f, 1f);
        RectTransform rect = go.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(0f, 1f);
        rect.pivot = new Vector2(0f, 1f);
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = size;
        return image;
    }

    static Font GetBuiltInUiFont()
    {
        Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        if (font != null)
        {
            return font;
        }

        try
        {
            return Resources.GetBuiltinResource<Font>("Arial.ttf");
        }
        catch
        {
            return null;
        }
    }

    static Button CreateButton(Transform parent, string label, Vector2 anchoredPosition, Vector2 size, Color color)
    {
        GameObject go = DefaultControls.CreateButton(new DefaultControls.Resources());
        go.name = "Button - " + label;
        go.transform.SetParent(parent, false);
        RectTransform rect = go.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(0f, 1f);
        rect.pivot = new Vector2(0f, 1f);
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = size;
        Image image = go.GetComponent<Image>();
        image.color = color;
        Text text = go.GetComponentInChildren<Text>();
        text.text = label;
        text.fontSize = 14;
        text.color = Color.white;
        return go.GetComponent<Button>();
    }

    static Dropdown CreateDropdown(Transform parent, Vector2 anchoredPosition, Vector2 size, IEnumerable<string> options, int defaultIndex)
    {
        GameObject go = DefaultControls.CreateDropdown(new DefaultControls.Resources());
        go.name = "Dropdown";
        go.transform.SetParent(parent, false);
        RectTransform rect = go.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(0f, 1f);
        rect.pivot = new Vector2(0f, 1f);
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = size;
        Dropdown dropdown = go.GetComponent<Dropdown>();
        dropdown.options.Clear();
        foreach (string option in options)
        {
            dropdown.options.Add(new Dropdown.OptionData(option));
        }
        dropdown.value = defaultIndex;
        dropdown.RefreshShownValue();
        return dropdown;
    }

    static Slider CreateSlider(Transform parent, Vector2 anchoredPosition, Vector2 size, float min, float max, float value)
    {
        GameObject go = DefaultControls.CreateSlider(new DefaultControls.Resources());
        go.name = "Slider";
        go.transform.SetParent(parent, false);
        RectTransform rect = go.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(0f, 1f);
        rect.pivot = new Vector2(0f, 1f);
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = size;
        Slider slider = go.GetComponent<Slider>();
        slider.minValue = min;
        slider.maxValue = max;
        slider.value = value;
        return slider;
    }

    static void CreateSceneNotes(Transform root)
    {
        GameObject notes = new GameObject("How To Run");
        notes.transform.SetParent(root);
        TextMesh text = notes.AddComponent<TextMesh>();
        text.text = "Backend: http://127.0.0.1:8000\nFlow: image classify -> mock sensor line -> lifecycle sort\nPress Play > Start Batch";
        text.fontSize = 32;
        text.characterSize = 0.055f;
        text.color = Color.white;
        text.anchor = TextAnchor.MiddleLeft;
        notes.transform.position = new Vector3(-5.9f, 0.1f, -3.1f);
        notes.transform.rotation = Quaternion.Euler(65f, 0f, 0f);
    }

    static void CreateDownloadedModelSources(Transform root)
    {
        GameObject sources = new GameObject("Downloaded 3D Model Sources");
        sources.transform.SetParent(root);
        sources.transform.position = new Vector3(-6.25f, 0.1f, 3.15f);
        TextMesh text = sources.AddComponent<TextMesh>();
        text.text =
            "Kenney Factory Kit 3.0 CC0\n" +
            "floor-large.fbx\n" +
            "conveyor-long-stripe-sides.fbx\n" +
            "scanner-high.fbx\n" +
            "screen-panel-wide.fbx\n" +
            "scanner-low.fbx\n" +
            "machine-bed.fbx\n" +
            "machine-fortified.fbx\n" +
            "hopper-square.fbx\n" +
            "ABB CRB 15000 GoFa-style arm\n" +
            "Step 1: image/backend shape classification\n" +
            "Step 2: mock sensors generate lifecycle decision";
        text.fontSize = 32;
        text.characterSize = 0.045f;
        text.color = new Color(0.82f, 0.9f, 1f);
        text.anchor = TextAnchor.MiddleLeft;
        sources.transform.rotation = Quaternion.Euler(65f, 0f, 0f);
    }
}
#endif
