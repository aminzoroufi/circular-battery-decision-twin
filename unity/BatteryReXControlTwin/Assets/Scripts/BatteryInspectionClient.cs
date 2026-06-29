/*
Project: Circular Battery Decision Twin
Developer: Amin Zoroufi
Contact: aminn.zoroufi@gmail.com
*/

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class InspectionFeatures
{
    public float state_of_health;
    public float temperature_c;
    public int cycle_count;
    public float internal_resistance_mohm;
    public float voltage;
    public float confidence_threshold;
    public float reuse_soh_threshold;
    public float estimated_visual_damage_score;
    public bool simulated_visual_damage_score;
}

[Serializable]
public class BatteryInspectionResult
{
    public string battery_id;
    public string image_id;
    public string label;
    public string category;
    public string detected_shape;
    public string detected_type;
    public string decision_category;
    public float confidence;
    public float uncertainty;
    public float soh;
    public float predicted_soh;
    public float temperature_c;
    public int cycle_count;
    public float internal_resistance_mohm;
    public float resistance;
    public float voltage;
    public float risk_score;
    public string risk_level;
    public string policy_mode;
    public string ai_decision;
    public string final_decision;
    public string target_bin;
    public bool manual_review_required;
    public string reason;
    public float processing_time_ms;
    public string original_image_filename;
    public string received_image_filename;
    public string received_image_path;
    public string received_image_url;
    public string model_name;
    public string model_used;
    public string soh_model_used;
    public float soh_confidence;
    public float soh_error_estimate_percent;
    public float error_estimate_percent;
    public float model_trust_percentage;
    public string classification_method;
    public string timestamp;
    public InspectionFeatures features;
}

[Serializable]
public class OverrideRequest
{
    public string battery_id;
    public string operator_decision;
    public string override_reason;
    public string operator_id;
}

[Serializable]
public class OverrideResponse
{
    public string battery_id;
    public string ai_decision;
    public string operator_decision;
    public string final_decision;
    public string target_bin;
    public bool override_saved;
}

[Serializable]
public class SohPredictionRequest
{
    public string battery_id;
    public string battery_type;
    public int cycle_count;
    public float temperature;
    public float resistance;
    public float voltage;
}

public class BatteryInspectionClient : MonoBehaviour
{
    public string backendBaseUrl = "http://127.0.0.1:8000";
    public OperatorControlPanel operatorControlPanel;
    public BatteryInfoPanel batteryInfoPanel;
    public RobotSorter robotSorter;
    public ProcessLoggerClient processLoggerClient;
    public InspectionCameraController inspectionCamera;
    public RandomBatteryImageProvider imageProvider;

    public BatteryAgent ActiveBattery { get; private set; }
    public BatteryInspectionResult LastResult { get; private set; }

    string ClassifyUrl => backendBaseUrl.TrimEnd('/') + "/classify-battery";
    string InspectUrl => backendBaseUrl.TrimEnd('/') + "/inspect-battery";
    string PredictSohUrl => backendBaseUrl.TrimEnd('/') + "/predict-soh";
    string OverrideUrl => backendBaseUrl.TrimEnd('/') + "/override-decision";

    public void Inspect(BatteryAgent battery)
    {
        if (battery == null)
        {
            Debug.LogWarning("No battery selected for inspection.");
            return;
        }

        ActiveBattery = battery;
        StartCoroutine(SendInspectionRequest(battery));
    }

    public IEnumerator ClassifyBattery(BatteryAgent battery)
    {
        if (battery == null)
        {
            yield break;
        }

        ActiveBattery = battery;
        string selectedImagePath = imageProvider != null ? imageProvider.PickRandomImagePath() : string.Empty;
        if (!string.IsNullOrEmpty(selectedImagePath))
        {
            battery.SetSelectedInspectionImage(selectedImagePath);
        }

        string imagePath = battery.ResolveImagePath();
        if (!File.Exists(imagePath))
        {
            Debug.LogError("Battery image not found: " + imagePath);
            yield break;
        }

        Debug.Log("[InspectionClient] Step 1 camera classification for " + battery.batteryId + " using image " + imagePath);
        battery.GetOrCreateFloatingInfoPanel().ShowCameraCapture(battery, Path.GetFileName(imagePath));
        batteryInfoPanel?.ShowSentImage(imagePath, battery.batteryId);
        if (inspectionCamera != null)
        {
            yield return inspectionCamera.CaptureFlash(battery);
        }

        byte[] imageBytes = File.ReadAllBytes(imagePath);
        var form = new List<IMultipartFormSection>
        {
            new MultipartFormDataSection("battery_id", battery.batteryId),
            new MultipartFormFileSection("image", imageBytes, Path.GetFileName(imagePath), ContentTypeForPath(imagePath))
        };

        using (UnityWebRequest request = UnityWebRequest.Post(ClassifyUrl, form))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Classification request failed: " + request.error + " " + request.downloadHandler.text);
                yield break;
            }

            LastResult = JsonUtility.FromJson<BatteryInspectionResult>(request.downloadHandler.text);
        }

        NormalizeClassificationResult(LastResult);
        float confidenceThreshold = operatorControlPanel != null ? operatorControlPanel.ConfidenceThreshold : 0.65f;
        BatteryShape detectedShape = BatteryCategoryMapper.ResolveShape(LastResult, confidenceThreshold);
        if (LastResult.confidence > 0f && LastResult.confidence < confidenceThreshold)
        {
            detectedShape = BatteryShape.Unknown;
            LastResult.manual_review_required = true;
        }

        battery.ApplyShapeClassification(detectedShape);
        battery.StoreLatestResult(LastResult);
        battery.GetOrCreateFloatingInfoPanel().ShowClassification(battery, LastResult, detectedShape);
        batteryInfoPanel?.ShowClassificationResult(LastResult, detectedShape);
        Debug.Log("[InspectionClient] Step 1 complete for " + battery.batteryId + ": shape=" + BatteryCategoryMapper.ShapeLabel(detectedShape));
    }

    public void ApplyMockSensorStage(BatteryAgent battery, string stationKey)
    {
        BatteryInspectionResult result = EnsureMockResult(battery);
        InspectionFeatures features = result.features;

        switch (stationKey)
        {
            case "thermal":
                features.temperature_c = UnityEngine.Random.Range(27.0f, 58.0f);
                result.temperature_c = features.temperature_c;
                battery.GetOrCreateFloatingInfoPanel().ShowSensorStage(battery, "thermal", result);
                batteryInfoPanel?.ShowSensorStage(
                    "Thermal camera",
                    result,
                    "Mock thermal camera reading: " + features.temperature_c.ToString("0.0") + " C"
                );
                break;
            case "electrical":
                features.voltage = UnityEngine.Random.Range(3.05f, 4.18f);
                result.voltage = features.voltage;
                battery.GetOrCreateFloatingInfoPanel().ShowSensorStage(battery, "electrical", result);
                batteryInfoPanel?.ShowSensorStage(
                    "Voltage / capacity tester",
                    result,
                    "Mock electrical reading: voltage " + features.voltage.ToString("0.00") + " V"
                );
                break;
            case "impedance":
                features.internal_resistance_mohm = UnityEngine.Random.Range(45.0f, 190.0f);
                result.internal_resistance_mohm = features.internal_resistance_mohm;
                result.resistance = features.internal_resistance_mohm / 1000f;
                result.cycle_count = UnityEngine.Random.Range(20, 1250);
                features.cycle_count = result.cycle_count;
                battery.GetOrCreateFloatingInfoPanel().ShowSensorStage(battery, "impedance", result);
                batteryInfoPanel?.ShowSensorStage(
                    "Impedance station",
                    result,
                    "Mock impedance reading: " + features.internal_resistance_mohm.ToString("0.0") + " mOhm, cycles " + features.cycle_count
                );
                break;
            case "vision_damage":
                features.estimated_visual_damage_score = UnityEngine.Random.Range(0.02f, 0.72f);
                battery.GetOrCreateFloatingInfoPanel().ShowSensorStage(battery, "damage", result);
                batteryInfoPanel?.ShowSensorStage(
                    "Damage vision camera",
                    result,
                    "Mock visual damage score: " + features.estimated_visual_damage_score.ToString("0.00")
                );
                break;
            default:
                battery.GetOrCreateFloatingInfoPanel().ShowSensorStage(battery, "sensor", result);
                batteryInfoPanel?.ShowSensorStage("Sensor line", result, "Mock sensor scan in progress.");
                break;
        }

        LastResult = result;
        battery.StoreLatestResult(result);
    }

    public BatteryInspectionResult FinalizeMockDecision(BatteryAgent battery)
    {
        BatteryInspectionResult result = EnsureMockResult(battery);
        InspectionFeatures features = result.features;

        EnsureMockHealthInputs(result);
        features.state_of_health = EstimateFallbackSoh(features);
        result.soh = features.state_of_health;
        result.predicted_soh = result.soh * 100f;

        int riskScore = CalculateMockRisk(result);
        DecisionCategory decision = DecideMockRoute(result, riskScore);
        result.risk_score = riskScore;
        result.risk_level = RiskLevelFromScore(riskScore);
        result.policy_mode = operatorControlPanel != null ? operatorControlPanel.PolicyMode : "balanced";
        result.ai_decision = BatteryCategoryMapper.DecisionKey(decision);
        result.decision_category = result.ai_decision;
        result.final_decision = result.ai_decision;
        result.target_bin = BatteryCategoryMapper.DecisionBinKey(decision);
        result.reason = "Local fallback route generated from mock health sensor inputs because the ML API was unavailable.";
        result.timestamp = DateTime.UtcNow.ToString("o");
        result.features = features;

        ApplyFinalResult(battery, result, decision);
        return result;
    }

    public IEnumerator FinalizeMlDecision(BatteryAgent battery, Action<BatteryInspectionResult> onComplete)
    {
        BatteryInspectionResult result = EnsureMockResult(battery);
        EnsureMockHealthInputs(result);
        result.reason = "Sending cycle count, temperature, resistance, voltage, and battery type to the SOH ML model.";
        battery.GetOrCreateFloatingInfoPanel().ShowSensorStage(battery, "soh ml", result);
        batteryInfoPanel?.ShowSensorStage("SOH ML prediction", result, "Sending mock sensor data to backend SOH predictor.");

        var payload = new SohPredictionRequest
        {
            battery_id = battery.batteryId,
            battery_type = BatteryCategoryMapper.ShapeKey(battery.currentShape),
            cycle_count = result.features.cycle_count,
            temperature = result.features.temperature_c,
            resistance = result.features.internal_resistance_mohm / 1000f,
            voltage = result.features.voltage
        };

        string json = JsonUtility.ToJson(payload);
        BatteryInspectionResult response = null;
        using (UnityWebRequest request = new UnityWebRequest(PredictSohUrl, "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("SOH prediction request failed: " + request.error + " " + request.downloadHandler.text);
                BatteryInspectionResult fallback = FinalizeMockDecision(battery);
                onComplete?.Invoke(fallback);
                yield break;
            }

            response = JsonUtility.FromJson<BatteryInspectionResult>(request.downloadHandler.text);
        }

        MergeSohResponse(result, response);
        DecisionCategory decision = BatteryCategoryMapper.ResolveDecision(result);
        ApplyFinalResult(battery, result, decision);
        onComplete?.Invoke(result);
    }

    IEnumerator SendInspectionRequest(BatteryAgent battery)
    {
        string selectedImagePath = imageProvider != null ? imageProvider.PickRandomImagePath() : string.Empty;
        if (!string.IsNullOrEmpty(selectedImagePath))
        {
            battery.SetSelectedInspectionImage(selectedImagePath);
        }

        string imagePath = battery.ResolveImagePath();
        if (!File.Exists(imagePath))
        {
            Debug.LogError("Battery image not found: " + imagePath);
            yield break;
        }

        Debug.Log("[InspectionClient] Camera capture for " + battery.batteryId + " using image " + imagePath);
        battery.GetOrCreateFloatingInfoPanel().ShowCameraCapture(battery, Path.GetFileName(imagePath));
        batteryInfoPanel?.ShowSentImage(imagePath, battery.batteryId);
        if (inspectionCamera != null)
        {
            yield return inspectionCamera.CaptureFlash(battery);
        }

        byte[] imageBytes = File.ReadAllBytes(imagePath);
        string policyMode = operatorControlPanel != null ? operatorControlPanel.PolicyMode : "balanced";
        string conveyorSpeed = operatorControlPanel != null ? operatorControlPanel.ConveyorSpeed : "normal";
        string robotMode = operatorControlPanel != null ? operatorControlPanel.RobotMode : "auto";
        float confidenceThreshold = operatorControlPanel != null ? operatorControlPanel.ConfidenceThreshold : 0.65f;
        float reuseSohThreshold = operatorControlPanel != null ? operatorControlPanel.ReuseSohThreshold : 0.80f;

        var form = new List<IMultipartFormSection>
        {
            new MultipartFormDataSection("battery_id", battery.batteryId),
            new MultipartFormFileSection("image", imageBytes, Path.GetFileName(imagePath), ContentTypeForPath(imagePath)),
            new MultipartFormDataSection("policy_mode", policyMode),
            new MultipartFormDataSection("confidence_threshold", confidenceThreshold.ToString("0.00")),
            new MultipartFormDataSection("reuse_soh_threshold", reuseSohThreshold.ToString("0.00")),
            new MultipartFormDataSection("conveyor_speed", conveyorSpeed),
            new MultipartFormDataSection("robot_mode", robotMode)
        };

        using (UnityWebRequest request = UnityWebRequest.Post(InspectUrl, form))
        {
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Inspection request failed: " + request.error + " " + request.downloadHandler.text);
                yield break;
            }

            LastResult = JsonUtility.FromJson<BatteryInspectionResult>(request.downloadHandler.text);
        }

        NormalizeFlexibleResult(LastResult);
        BatteryShape detectedShape = BatteryCategoryMapper.ResolveShape(LastResult, confidenceThreshold);
        DecisionCategory decisionCategory = BatteryCategoryMapper.ResolveDecision(LastResult);
        if (LastResult.confidence > 0f && LastResult.confidence < confidenceThreshold)
        {
            decisionCategory = DecisionCategory.Quarantine;
            LastResult.manual_review_required = true;
        }

        string sortBinKey = BatteryCategoryMapper.DecisionBinKey(decisionCategory);
        Debug.Log(
            "[InspectionClient] AI result for " + battery.batteryId +
            ": shape=" + BatteryCategoryMapper.ShapeLabel(detectedShape) +
            " decision=" + BatteryCategoryMapper.DecisionLabel(decisionCategory) +
            " confidence=" + LastResult.confidence.ToString("0.00") +
            " sortBin=" + sortBinKey
        );

        battery.ApplyInspectionResult(LastResult);
        battery.ApplyVisualResult(detectedShape, decisionCategory);
        battery.StoreLatestResult(LastResult);
        battery.GetOrCreateFloatingInfoPanel().ShowDecision(battery, LastResult, decisionCategory);
        batteryInfoPanel?.Show(LastResult);
        batteryInfoPanel?.ShowDecisionResult(detectedShape, decisionCategory, LastResult);
        processLoggerClient?.SetLatestResult(LastResult);

        if (robotSorter != null)
        {
            robotSorter.SortBattery(battery, sortBinKey, decisionCategory == DecisionCategory.Quarantine, robotMode);
        }
    }

    void EnsureMockHealthInputs(BatteryInspectionResult result)
    {
        if (result == null)
        {
            return;
        }

        if (result.features == null)
        {
            result.features = new InspectionFeatures();
        }

        InspectionFeatures features = result.features;
        if (features.temperature_c <= 0f)
        {
            features.temperature_c = UnityEngine.Random.Range(27.0f, 58.0f);
        }
        if (features.internal_resistance_mohm <= 0f)
        {
            features.internal_resistance_mohm = UnityEngine.Random.Range(45.0f, 190.0f);
        }
        if (features.cycle_count <= 0)
        {
            features.cycle_count = UnityEngine.Random.Range(20, 1250);
        }
        if (features.voltage <= 0f)
        {
            features.voltage = UnityEngine.Random.Range(3.05f, 4.18f);
        }

        result.temperature_c = features.temperature_c;
        result.internal_resistance_mohm = features.internal_resistance_mohm;
        result.resistance = features.internal_resistance_mohm / 1000f;
        result.cycle_count = features.cycle_count;
        result.voltage = features.voltage;
        result.features = features;
    }

    float EstimateFallbackSoh(InspectionFeatures features)
    {
        float cycleLoss = Mathf.Clamp01(features.cycle_count / 1600f) * 0.34f;
        float resistanceLoss = Mathf.Clamp01((features.internal_resistance_mohm - 55f) / 170f) * 0.22f;
        float voltagePenalty = features.voltage < 3.25f ? 0.12f : features.voltage < 3.45f ? 0.06f : 0f;
        float temperaturePenalty = features.temperature_c > 50f ? 0.12f : features.temperature_c > 42f ? 0.06f : 0f;
        return Mathf.Clamp(1.0f - cycleLoss - resistanceLoss - voltagePenalty - temperaturePenalty, 0.20f, 0.99f);
    }

    void MergeSohResponse(BatteryInspectionResult result, BatteryInspectionResult response)
    {
        if (result == null || response == null)
        {
            return;
        }

        result.predicted_soh = response.predicted_soh > 0f ? response.predicted_soh : response.soh * 100f;
        result.soh = response.soh > 0f ? response.soh : result.predicted_soh / 100f;
        result.decision_category = response.decision_category;
        result.ai_decision = response.ai_decision;
        result.final_decision = response.final_decision;
        result.target_bin = response.target_bin;
        result.risk_score = response.risk_score;
        result.risk_level = response.risk_level;
        result.manual_review_required = response.manual_review_required;
        result.reason = response.reason;
        result.policy_mode = "ml_soh_thresholds";
        result.timestamp = string.IsNullOrEmpty(response.timestamp) ? DateTime.UtcNow.ToString("o") : response.timestamp;
        result.soh_model_used = !string.IsNullOrEmpty(response.model_used) ? response.model_used : response.model_name;
        result.soh_confidence = response.confidence;
        result.soh_error_estimate_percent = response.error_estimate_percent;
        result.error_estimate_percent = response.error_estimate_percent;
        if (!string.IsNullOrEmpty(result.soh_model_used))
        {
            result.model_used = result.soh_model_used;
        }

        if (result.features == null)
        {
            result.features = new InspectionFeatures();
        }

        result.features.state_of_health = result.soh;
        result.features.temperature_c = result.temperature_c;
        result.features.cycle_count = result.cycle_count;
        result.features.internal_resistance_mohm = result.internal_resistance_mohm;
        result.features.voltage = result.voltage;
    }

    void ApplyFinalResult(BatteryAgent battery, BatteryInspectionResult result, DecisionCategory decision)
    {
        if (battery == null || result == null)
        {
            return;
        }

        battery.ApplyInspectionResult(result);
        battery.ApplyVisualResult(battery.currentShape, decision);
        battery.GetOrCreateFloatingInfoPanel().ShowDecision(battery, result, decision);
        batteryInfoPanel?.Show(result);
        batteryInfoPanel?.ShowDecisionResult(battery.currentShape, decision, result);
        processLoggerClient?.SetLatestResult(result);
        LastResult = result;
        battery.StoreLatestResult(result);
    }

    BatteryInspectionResult EnsureMockResult(BatteryAgent battery)
    {
        if (LastResult == null || battery == null || LastResult.battery_id != battery.batteryId)
        {
            LastResult = new BatteryInspectionResult();
        }

        LastResult.battery_id = battery != null ? battery.batteryId : LastResult.battery_id;
        LastResult.detected_shape = battery != null ? BatteryCategoryMapper.ShapeKey(battery.currentShape) : LastResult.detected_shape;
        LastResult.detected_type = LastResult.detected_shape;
        LastResult.policy_mode = operatorControlPanel != null ? operatorControlPanel.PolicyMode : "balanced";
        LastResult.ai_decision = string.IsNullOrEmpty(LastResult.ai_decision) ? "pending" : LastResult.ai_decision;
        LastResult.final_decision = string.IsNullOrEmpty(LastResult.final_decision) ? "pending" : LastResult.final_decision;
        LastResult.decision_category = string.IsNullOrEmpty(LastResult.decision_category) ? "pending" : LastResult.decision_category;
        LastResult.target_bin = string.IsNullOrEmpty(LastResult.target_bin) ? "none" : LastResult.target_bin;
        LastResult.reason = string.IsNullOrEmpty(LastResult.reason) ? "Waiting for downstream mock sensor readings." : LastResult.reason;
        LastResult.timestamp = DateTime.UtcNow.ToString("o");

        if (LastResult.features == null)
        {
            LastResult.features = new InspectionFeatures();
        }

        LastResult.features.confidence_threshold = operatorControlPanel != null ? operatorControlPanel.ConfidenceThreshold : 0.65f;
        LastResult.features.reuse_soh_threshold = operatorControlPanel != null ? operatorControlPanel.ReuseSohThreshold : 0.80f;
        LastResult.features.simulated_visual_damage_score = true;
        return LastResult;
    }

    int CalculateMockRisk(BatteryInspectionResult result)
    {
        InspectionFeatures features = result.features;
        int risk = 0;
        float confidenceThreshold = operatorControlPanel != null ? operatorControlPanel.ConfidenceThreshold : 0.65f;

        if (result.confidence > 0f && result.confidence < confidenceThreshold) risk += 30;
        if (features.state_of_health < 0.50f) risk += 35;
        else if (features.state_of_health < 0.65f) risk += 20;
        if (features.temperature_c > 50f) risk += 40;
        else if (features.temperature_c >= 40f) risk += 20;
        if (features.cycle_count > 900) risk += 20;
        else if (features.cycle_count >= 600) risk += 10;
        if (features.internal_resistance_mohm > 150f) risk += 20;
        if (features.estimated_visual_damage_score > 0.55f) risk += 25;
        else if (features.estimated_visual_damage_score > 0.30f) risk += 10;
        if (result.detected_shape == BatteryCategoryMapper.Unknown) risk += 30;

        string policyMode = operatorControlPanel != null ? operatorControlPanel.PolicyMode : "balanced";
        if (policyMode == "safety_first") risk += 10;
        else if (policyMode == "recovery_maximization") risk = Mathf.Max(0, risk - 10);
        return Mathf.Clamp(risk, 0, 100);
    }

    DecisionCategory DecideMockRoute(BatteryInspectionResult result, int riskScore)
    {
        InspectionFeatures features = result.features;
        float reuseThreshold = operatorControlPanel != null ? operatorControlPanel.ReuseSohThreshold : 0.80f;
        string policyMode = operatorControlPanel != null ? operatorControlPanel.PolicyMode : "balanced";

        if (riskScore > 80) return DecisionCategory.Quarantine;
        if (policyMode == "safety_first" && riskScore > 60) return DecisionCategory.Quarantine;
        if (features.state_of_health >= reuseThreshold && riskScore <= 30) return DecisionCategory.Reuse;
        if (features.state_of_health >= 0.60f && riskScore <= 60) return DecisionCategory.Remanufacture;
        if (policyMode == "recovery_maximization" && features.state_of_health >= 0.55f && riskScore <= 70) return DecisionCategory.Remanufacture;
        if (features.state_of_health < 0.60f) return DecisionCategory.Recycle;
        return DecisionCategory.Quarantine;
    }

    string RiskLevelFromScore(int riskScore)
    {
        if (riskScore <= 30) return "low";
        if (riskScore <= 60) return "medium";
        if (riskScore <= 80) return "high";
        return "critical";
    }

    void NormalizeFlexibleResult(BatteryInspectionResult result)
    {
        if (result == null)
        {
            return;
        }

        if (string.IsNullOrEmpty(result.detected_shape))
        {
            result.detected_shape = !string.IsNullOrEmpty(result.detected_type)
                ? result.detected_type
                : !string.IsNullOrEmpty(result.category)
                    ? result.category
                    : result.label;
        }

        if (string.IsNullOrEmpty(result.detected_type))
        {
            result.detected_type = result.detected_shape;
        }

        if (string.IsNullOrEmpty(result.decision_category))
        {
            result.decision_category = !string.IsNullOrEmpty(result.final_decision) ? result.final_decision : result.ai_decision;
        }
        result.decision_category = BatteryCategoryMapper.DecisionKey(BatteryCategoryMapper.NormalizeDecision(result.decision_category));
        result.detected_shape = BatteryCategoryMapper.ShapeKey(BatteryCategoryMapper.NormalizeShape(result.detected_shape));

        if (string.IsNullOrEmpty(result.final_decision))
        {
            result.final_decision = result.decision_category;
        }

        if (result.uncertainty <= 0f && result.confidence > 0f)
        {
            result.uncertainty = Mathf.Clamp01(1f - result.confidence);
        }
    }

    void NormalizeClassificationResult(BatteryInspectionResult result)
    {
        if (result == null)
        {
            return;
        }

        if (string.IsNullOrEmpty(result.detected_shape))
        {
            result.detected_shape = !string.IsNullOrEmpty(result.detected_type)
                ? result.detected_type
                : !string.IsNullOrEmpty(result.category)
                    ? result.category
                    : result.label;
        }

        result.detected_shape = BatteryCategoryMapper.ShapeKey(BatteryCategoryMapper.NormalizeShape(result.detected_shape));
        result.detected_type = result.detected_shape;
        result.ai_decision = "classification only";
        result.decision_category = "pending";
        result.final_decision = "pending";
        result.target_bin = "none";
        result.manual_review_required = false;
        result.policy_mode = operatorControlPanel != null ? operatorControlPanel.PolicyMode : "balanced";
        result.reason = "Image classification identifies shape only. Lifecycle routing waits for sensor data.";

        if (string.IsNullOrEmpty(result.timestamp))
        {
            result.timestamp = DateTime.UtcNow.ToString("o");
        }

        if (result.uncertainty <= 0f && result.confidence > 0f)
        {
            result.uncertainty = Mathf.Clamp01(1f - result.confidence);
        }
    }

    string ContentTypeForPath(string imagePath)
    {
        string extension = Path.GetExtension(imagePath).ToLowerInvariant();
        if (extension == ".jpg" || extension == ".jpeg") return "image/jpeg";
        if (extension == ".webp") return "image/webp";
        return "image/png";
    }

    public void SubmitOverride(string operatorDecision, string reason = "Manual operator override", string operatorId = "operator_01")
    {
        if (ActiveBattery == null)
        {
            Debug.LogWarning("No active battery to override.");
            return;
        }

        StartCoroutine(SendOverrideRequest(ActiveBattery, operatorDecision, reason, operatorId));
    }

    IEnumerator SendOverrideRequest(BatteryAgent battery, string operatorDecision, string reason, string operatorId)
    {
        var payload = new OverrideRequest
        {
            battery_id = battery.batteryId,
            operator_decision = operatorDecision,
            override_reason = reason,
            operator_id = operatorId
        };
        string json = JsonUtility.ToJson(payload);

        OverrideResponse response;
        using (UnityWebRequest request = new UnityWebRequest(OverrideUrl, "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError("Override request failed: " + request.error + " " + request.downloadHandler.text);
                yield break;
            }

            response = JsonUtility.FromJson<OverrideResponse>(request.downloadHandler.text);
        }

        battery.finalDecision = response.final_decision;
        battery.targetBin = response.target_bin;

        if (LastResult != null)
        {
            LastResult.final_decision = response.final_decision;
            LastResult.target_bin = response.target_bin;
            LastResult.reason = "Operator override saved: " + reason;
            batteryInfoPanel?.Show(LastResult);
            battery.StoreLatestResult(LastResult);
        }

        DecisionCategory overrideDecision = BatteryCategoryMapper.NormalizeDecision(response.final_decision);
        battery.ApplyVisualResult(battery.currentShape, overrideDecision);
        battery.GetOrCreateFloatingInfoPanel().ShowDecision(battery, LastResult, overrideDecision);
        string targetBin = BatteryCategoryMapper.DecisionBinKey(overrideDecision);
        robotSorter?.SortBattery(battery, targetBin, overrideDecision == DecisionCategory.Quarantine, "auto");
    }
}
