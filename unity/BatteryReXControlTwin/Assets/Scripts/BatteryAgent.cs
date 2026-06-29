using System;
using System.IO;
using UnityEngine;

public class BatteryAgent : MonoBehaviour
{
    public string batteryId;
    public string imagePath;
    public string batteryType;
    public string sourceType;
    public string sourceArea;
    public string previousApplication;
    public string currentState = "intake";
    public string finalDecision = "pending";
    public string targetBin = "none";
    public BatteryShape currentShape = BatteryShape.Unknown;
    public DecisionCategory decisionCategory = DecisionCategory.Quarantine;
    public string visualCategory = BatteryCategoryMapper.Unknown;
    public bool cameraClassificationComplete;
    public BatteryFloatingInfoPanel floatingInfoPanel;
    public BatteryInspectionResult latestResult;
    public string capturedImagePath;
    public bool IsSorted => currentState != null && currentState.StartsWith("sorted_", StringComparison.Ordinal);

    public void Configure(ManifestBattery manifestBattery)
    {
        batteryId = manifestBattery.battery_id;
        imagePath = string.Empty;
        currentShape = BatteryShape.Unknown;
        decisionCategory = DecisionCategory.Quarantine;
        batteryType = BatteryCategoryMapper.ShapeKey(currentShape);
        visualCategory = BatteryCategoryMapper.DecisionKey(decisionCategory);
        cameraClassificationComplete = false;
        sourceType = manifestBattery.source_type;
        sourceArea = manifestBattery.source_area;
        previousApplication = manifestBattery.previous_application;
        name = batteryId;
        EnsureSelectionCollider();
        ApplyVisualResult(BatteryShape.Unknown, DecisionCategory.Quarantine);
        GetOrCreateFloatingInfoPanel().ShowWaiting(this);
        Debug.Log("[BatteryAgent] Spawned " + batteryId + " as unknown/default shape.");
    }

    public void SetSelectedInspectionImage(string selectedImagePath)
    {
        imagePath = selectedImagePath;
        capturedImagePath = selectedImagePath;
        GetOrCreateFloatingInfoPanel().ShowCameraCapture(this, Path.GetFileName(selectedImagePath));
        BatterySelectionDetailPanel.RefreshIfSelected(this);
        Debug.Log("[BatteryAgent] " + batteryId + " selected AI image: " + imagePath);
    }

    public BatteryFloatingInfoPanel GetOrCreateFloatingInfoPanel()
    {
        if (floatingInfoPanel == null)
        {
            floatingInfoPanel = GetComponentInChildren<BatteryFloatingInfoPanel>();
        }

        if (floatingInfoPanel == null)
        {
            floatingInfoPanel = gameObject.AddComponent<BatteryFloatingInfoPanel>();
        }

        return floatingInfoPanel;
    }

    public string ResolveImagePath()
    {
        if (Path.IsPathRooted(imagePath))
        {
            return imagePath;
        }

        string fromAssets = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../", imagePath));
        if (File.Exists(fromAssets))
        {
            return fromAssets;
        }

        return Path.GetFullPath(Path.Combine(Application.streamingAssetsPath, imagePath));
    }

    public void ApplyInspectionResult(BatteryInspectionResult result)
    {
        latestResult = result;
        currentState = "decision_received";
        finalDecision = !string.IsNullOrEmpty(result.decision_category) ? result.decision_category : result.final_decision;
        targetBin = result.target_bin;
        BatterySelectionDetailPanel.RefreshIfSelected(this);
    }

    public void ApplyShapeClassification(BatteryShape shape)
    {
        currentState = "shape_classified";
        cameraClassificationComplete = true;
        currentShape = shape;
        batteryType = BatteryCategoryMapper.ShapeKey(shape);

        BatteryVisualController visual = GetComponent<BatteryVisualController>();
        if (visual == null)
        {
            visual = gameObject.AddComponent<BatteryVisualController>();
        }

        visual.ApplyShapeOnly(shape);
        BatterySelectionDetailPanel.RefreshIfSelected(this);
    }

    public void StoreLatestResult(BatteryInspectionResult result)
    {
        latestResult = result;
        BatterySelectionDetailPanel.RefreshIfSelected(this);
    }

    public void ApplyVisualCategory(string category)
    {
        ApplyVisualResult(BatteryCategoryMapper.NormalizeShape(category), DecisionCategory.Quarantine);
    }

    public void ApplyVisualResult(BatteryShape shape, DecisionCategory decision)
    {
        currentShape = shape;
        decisionCategory = decision;
        batteryType = BatteryCategoryMapper.ShapeKey(shape);
        visualCategory = BatteryCategoryMapper.DecisionKey(decision);
        BatteryVisualController visual = GetComponent<BatteryVisualController>();
        if (visual == null)
        {
            visual = gameObject.AddComponent<BatteryVisualController>();
        }

        visual.ApplyVisual(shape, decision);
        EnsureSelectionCollider();
        BatterySelectionDetailPanel.RefreshIfSelected(this);
    }

    void OnMouseDown()
    {
        BatterySelectionDetailPanel.ShowBattery(this);
    }

    void EnsureSelectionCollider()
    {
        BoxCollider collider = GetComponent<BoxCollider>();
        if (collider == null)
        {
            collider = gameObject.AddComponent<BoxCollider>();
        }

        collider.isTrigger = true;
        collider.center = new Vector3(0f, 0.24f, 0f);
        collider.size = new Vector3(1.15f, 0.70f, 0.85f);
    }

    public void SetHeldByRobot(bool held)
    {
        Rigidbody rigidbody = GetComponent<Rigidbody>();
        if (rigidbody != null)
        {
            rigidbody.isKinematic = held;
            rigidbody.useGravity = !held;
        }
    }
}

[Serializable]
public class ManifestBattery
{
    public string battery_id;
    public string image_path;
    public string source_type;
    public string source_area;
    public string previous_application;
    public string health_id;
}

[Serializable]
public class ManifestBatteryList
{
    public ManifestBattery[] batteries;
}
