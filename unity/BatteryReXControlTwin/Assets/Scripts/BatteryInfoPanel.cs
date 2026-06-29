using System.IO;
using UnityEngine;
using UnityEngine.UI;

public class BatteryInfoPanel : MonoBehaviour
{
    public Text batteryIdText;
    public Text detectedTypeText;
    public Text confidenceText;
    public Text sohText;
    public Text riskScoreText;
    public Text riskLevelText;
    public Text policyModeText;
    public Text aiDecisionText;
    public Text finalDecisionText;
    public Text sortCategoryText;
    public Text uncertaintyText;
    public Text featuresText;
    public Text timestampText;
    public Text statusText;
    public Text metadataText;
    public Image decisionBadgeImage;
    public Text decisionBadgeText;
    public Text reasonText;
    public Text targetBinText;
    public RawImage sentImagePreview;
    public Text sentImagePathText;
    public Text backendReceivedImageText;

    public void Show(BatteryInspectionResult result)
    {
        if (result == null)
        {
            return;
        }

        SetText(batteryIdText, result.battery_id);
        SetText(detectedTypeText, !string.IsNullOrEmpty(result.detected_shape) ? result.detected_shape : result.detected_type);
        SetText(confidenceText, result.confidence.ToString("0.00"));
        SetText(uncertaintyText, result.uncertainty.ToString("0.00"));
        SetText(sohText, result.predicted_soh > 0f ? result.predicted_soh.ToString("0.0") + "%" : result.soh.ToString("0.00"));
        SetText(riskScoreText, result.risk_score.ToString("0"));
        SetText(riskLevelText, result.risk_level);
        SetText(policyModeText, result.policy_mode);
        SetText(aiDecisionText, result.ai_decision);
        SetText(finalDecisionText, !string.IsNullOrEmpty(result.decision_category) ? result.decision_category : result.final_decision);
        SetText(reasonText, result.reason);
        SetText(targetBinText, result.target_bin);
        SetText(timestampText, result.timestamp);
        SetText(featuresText, BuildFeaturesText(result));
        SetText(metadataText, BuildModelMetadata(result) + "\nSOH is predicted by the backend ML model from sensor inputs, not from the battery image.");
        string receivedImage = string.IsNullOrEmpty(result.received_image_filename)
            ? "-"
            : result.received_image_filename + "\n" + result.received_image_path;
        SetText(backendReceivedImageText, receivedImage);
    }

    public void ShowSortCategory(string category)
    {
        SetText(sortCategoryText, BatteryCategoryMapper.DecisionLabel(BatteryCategoryMapper.NormalizeDecision(category)));
    }

    public void ShowClassificationResult(BatteryInspectionResult result, BatteryShape shape)
    {
        if (result == null)
        {
            return;
        }

        SetText(batteryIdText, result.battery_id);
        SetText(detectedTypeText, BatteryCategoryMapper.ShapeLabel(shape));
        SetText(confidenceText, result.confidence.ToString("0.00"));
        SetText(uncertaintyText, result.uncertainty.ToString("0.00"));
        SetText(finalDecisionText, "WAITING FOR SENSOR DATA");
        SetText(sortCategoryText, "PENDING");
        SetText(aiDecisionText, "classification only");
        SetText(statusText, "Step 1 complete - shape updated, battery moving to sensor line");
        SetText(reasonText, "Image/backend classification identifies the visible battery type. Health data is not available from the image.");
        SetText(targetBinText, "-");
        SetText(timestampText, result.timestamp);
        SetText(featuresText, "Image classification: " + BatteryCategoryMapper.ShapeLabel(shape) + "\nHealth readings: waiting for mock sensor stations");
        SetText(metadataText, BuildModelMetadata(result) + "\nImage gives shape only. Sensor readings below are mock values for this prototype.");
        string receivedImage = string.IsNullOrEmpty(result.received_image_filename)
            ? "-"
            : result.received_image_filename + "\n" + result.received_image_path;
        SetText(backendReceivedImageText, receivedImage);

        if (decisionBadgeImage != null)
        {
            decisionBadgeImage.color = BatteryCategoryMapper.ShapeNeutralColor(shape);
        }
        SetText(decisionBadgeText, "CLASSIFIED");
    }

    public void ShowSensorStage(string stationName, BatteryInspectionResult result, string detail)
    {
        SetText(statusText, stationName + " - reading updated");
        SetText(reasonText, detail);
        if (result != null)
        {
            SetText(sohText, result.predicted_soh > 0f ? result.predicted_soh.ToString("0.0") + "%" : result.soh > 0f ? (result.soh * 100f).ToString("0.0") + "%" : "-");
            SetText(riskScoreText, result.risk_score > 0f ? result.risk_score.ToString("0") : "-");
            SetText(riskLevelText, string.IsNullOrEmpty(result.risk_level) ? "-" : result.risk_level);
            SetText(featuresText, BuildFeaturesText(result));
        }
        SetText(metadataText, BuildModelMetadata(result) + "\nUnity generates mock sensor readings; backend ML predicts SOH and Re-X route.");
    }

    public void ShowDecisionResult(BatteryShape shape, DecisionCategory decision, BatteryInspectionResult result)
    {
        SetText(detectedTypeText, BatteryCategoryMapper.ShapeLabel(shape));
        SetText(sortCategoryText, BatteryCategoryMapper.DecisionLabel(decision));
        SetText(finalDecisionText, BatteryCategoryMapper.DecisionLabel(decision));
        SetText(statusText, "AI decision received - robot sorting to " + BatteryCategoryMapper.DecisionLabel(decision));

        if (decisionBadgeImage != null)
        {
            decisionBadgeImage.color = BatteryCategoryMapper.DecisionColor(decision);
        }

        SetText(decisionBadgeText, BatteryCategoryMapper.DecisionLabel(decision));
        if (result != null && string.IsNullOrEmpty(result.reason))
        {
            SetText(reasonText, "Decision generated from estimated health, risk score, and classifier confidence.");
        }
    }

    public void ShowSentImage(string imagePath, string batteryId = null)
    {
        if (!string.IsNullOrEmpty(batteryId))
        {
            SetText(batteryIdText, batteryId);
        }

        SetText(sentImagePathText, Path.GetFileName(imagePath));
        SetText(detectedTypeText, "waiting");
        SetText(confidenceText, "-");
        SetText(uncertaintyText, "-");
        SetText(sohText, "-");
        SetText(riskScoreText, "-");
        SetText(riskLevelText, "-");
        SetText(policyModeText, "-");
        SetText(finalDecisionText, "PENDING");
        SetText(aiDecisionText, "classification pending");
        SetText(sortCategoryText, "PENDING");
        SetText(targetBinText, "-");
        SetText(timestampText, "-");
        SetText(backendReceivedImageText, "waiting for backend");
        SetText(statusText, "Camera captured image - sending to backend classifier");
        SetText(reasonText, "Step 1 uses the image to identify battery shape only.");
        SetText(featuresText, "Waiting for image classification");
        SetText(metadataText, "Health, temperature, cycles, and resistance will be mock sensor data in step 2.");
        SetText(decisionBadgeText, "PENDING");
        if (decisionBadgeImage != null)
        {
            decisionBadgeImage.color = new Color(0.34f, 0.36f, 0.40f);
        }

        if (sentImagePreview == null || !File.Exists(imagePath))
        {
            return;
        }

        byte[] data = File.ReadAllBytes(imagePath);
        Texture2D texture = new Texture2D(2, 2);
        if (texture.LoadImage(data))
        {
            sentImagePreview.texture = texture;
        }
    }

    string BuildFeaturesText(BatteryInspectionResult result)
    {
        if (result == null)
        {
            return "-";
        }

        InspectionFeatures features = result.features;
        if (features == null)
        {
            return
                "Predicted SOH: " + (result.predicted_soh > 0f ? result.predicted_soh.ToString("0.0") + "%" : result.soh > 0f ? (result.soh * 100f).ToString("0.0") + "%" : "-") + "\n" +
                "Cycle count: " + result.cycle_count + "\n" +
                "Temperature: " + (result.temperature_c > 0f ? result.temperature_c.ToString("0.0") + " C" : "-") + "\n" +
                "Voltage: " + (result.voltage > 0f ? result.voltage.ToString("0.00") + " V" : "-") + "\n" +
                "Internal resistance: " + (result.internal_resistance_mohm > 0f ? result.internal_resistance_mohm.ToString("0.0") + " mOhm" : "-") + "\n" +
                "Risk score: " + (result.risk_score > 0f ? result.risk_score.ToString("0") : "-");
        }

        return
            "Predicted SOH: " + (result.predicted_soh > 0f ? result.predicted_soh.ToString("0.0") + "%" : features.state_of_health > 0f ? (features.state_of_health * 100f).ToString("0.0") + "%" : "-") + "\n" +
            "Cycle count: " + features.cycle_count + "\n" +
            "Temperature: " + (features.temperature_c > 0f ? features.temperature_c.ToString("0.0") + " C" : "-") + "\n" +
            "Voltage: " + (features.voltage > 0f ? features.voltage.ToString("0.00") + " V" : "-") + "\n" +
            "Internal resistance: " + (features.internal_resistance_mohm > 0f ? features.internal_resistance_mohm.ToString("0.0") + " mOhm" : "-") + "\n" +
            "Mock visual/electrical risk score: " + features.estimated_visual_damage_score.ToString("0.00") +
            (features.simulated_visual_damage_score ? " (estimated)" : "");
    }

    string BuildModelMetadata(BatteryInspectionResult result)
    {
        if (result != null && !string.IsNullOrEmpty(result.soh_model_used))
        {
            string sohTrust = result.soh_confidence > 0f
                ? (result.soh_confidence * 100f).ToString("0.00") + "% estimated trust"
                : "confidence unavailable";
            string error = result.soh_error_estimate_percent > 0f
                ? ", error +/- " + result.soh_error_estimate_percent.ToString("0.00") + " SOH points"
                : "";
            return "SOH model: " + result.soh_model_used + " (" + sohTrust + error + ")";
        }

        if (result == null || string.IsNullOrEmpty(result.model_name))
        {
            return "Computer vision model: image-feature fallback";
        }

        string trust = result.model_trust_percentage > 0f
            ? result.model_trust_percentage.ToString("0.00") + "% validation trust"
            : "validation trust unavailable";
        return "Computer vision model: " + result.model_name + " (" + trust + ")";
    }

    void SetText(Text text, string value)
    {
        if (text != null)
        {
            text.text = value;
        }
    }
}
