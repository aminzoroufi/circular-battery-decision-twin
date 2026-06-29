using System.IO;
using UnityEngine;
using UnityEngine.UI;

public class BatteryFloatingInfoPanel : MonoBehaviour
{
    public Vector3 localOffset = new Vector3(0f, 1.05f, 0f);
    public float panelScale = 0.0042f;

    Canvas canvas;
    Image statusStrip;
    Text idText;
    Text statusText;
    Text shapeText;
    Text decisionText;
    Text confidenceText;
    Text sensorText;
    Text modelText;
    RawImage capturedImage;
    Text imageLabelText;

    void Awake()
    {
        BuildPanel();
    }

    void LateUpdate()
    {
        if (canvas == null)
        {
            return;
        }

        canvas.transform.localPosition = localOffset;
        Camera camera = Camera.main;
        if (camera != null)
        {
            canvas.transform.LookAt(
                canvas.transform.position + camera.transform.rotation * Vector3.forward,
                camera.transform.rotation * Vector3.up
            );
        }
    }

    public void ShowWaiting(BatteryAgent battery)
    {
        SetText(idText, ShortId(battery));
        SetText(statusText, "WAITING");
        SetText(shapeText, "Shape: unknown");
        SetText(decisionText, "Route: pending");
        SetText(confidenceText, "Vision: -");
        SetText(sensorText, "Sensors: waiting");
        SetText(modelText, "AI panel attached");
        SetImage(null);
        SetText(imageLabelText, "Camera image");
        SetStrip(new Color(0.36f, 0.38f, 0.42f));
    }

    public void ShowCameraCapture(BatteryAgent battery, string fileName)
    {
        SetText(idText, ShortId(battery));
        SetText(statusText, "CAMERA");
        SetText(shapeText, "Shape: analysing");
        SetText(decisionText, "Route: pending");
        SetText(confidenceText, "Image: " + SafeFile(fileName));
        SetText(sensorText, "Backend: sending");
        SetText(modelText, "Step 1 image classification");
        SetCapturedImage(battery);
        SetText(imageLabelText, SafeFile(fileName));
        SetStrip(new Color(0.10f, 0.50f, 0.85f));
    }

    public void ShowClassification(BatteryAgent battery, BatteryInspectionResult result, BatteryShape shape)
    {
        SetText(idText, ShortId(battery));
        SetText(statusText, "CLASSIFIED");
        SetText(shapeText, "Shape: " + BatteryCategoryMapper.ShapeLabel(shape));
        SetText(decisionText, "Route: waiting sensors");
        SetText(confidenceText, "Vision: " + Percent(result != null ? result.confidence : 0f));
        SetText(sensorText, "Sensors: queued");
        SetText(modelText, ModelLine(result));
        SetStrip(BatteryCategoryMapper.ShapeNeutralColor(shape));
    }

    public void ShowSensorStage(BatteryAgent battery, string stationName, BatteryInspectionResult result)
    {
        SetText(idText, ShortId(battery));
        SetText(statusText, stationName.ToUpperInvariant());
        SetText(shapeText, "Shape: " + BatteryCategoryMapper.ShapeLabel(battery.currentShape));
        SetText(decisionText, "Route: calculating");
        SetText(confidenceText, "Vision: " + Percent(result != null ? result.confidence : 0f));
        SetText(sensorText, SensorLine(result));
        SetText(modelText, "Sensor data -> SOH model");
        SetStrip(new Color(0.88f, 0.70f, 0.25f));
    }

    public void ShowDecision(BatteryAgent battery, BatteryInspectionResult result, DecisionCategory decision)
    {
        SetText(idText, ShortId(battery));
        SetText(statusText, "DECISION");
        SetText(shapeText, "Shape: " + BatteryCategoryMapper.ShapeLabel(battery.currentShape));
        SetText(decisionText, "Route: " + BatteryCategoryMapper.DecisionLabel(decision));
        SetText(confidenceText, "Risk: " + (result != null ? result.risk_score.ToString("0") : "-"));
        SetText(sensorText, SensorLine(result));
        SetText(modelText, ModelLine(result));
        SetStrip(BatteryCategoryMapper.DecisionColor(decision));
    }

    void BuildPanel()
    {
        if (canvas != null)
        {
            return;
        }

        GameObject canvasGo = new GameObject("Floating AI Inspection Panel");
        canvasGo.transform.SetParent(transform, false);
        canvasGo.transform.localPosition = localOffset;
        canvasGo.transform.localScale = Vector3.one * panelScale;

        canvas = canvasGo.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.WorldSpace;
        canvas.sortingOrder = 20;
        CanvasScaler scaler = canvasGo.AddComponent<CanvasScaler>();
        scaler.dynamicPixelsPerUnit = 18f;
        canvasGo.AddComponent<GraphicRaycaster>();

        RectTransform canvasRect = canvasGo.GetComponent<RectTransform>();
        canvasRect.sizeDelta = new Vector2(360f, 210f);

        GameObject panel = CreateRect(canvasGo.transform, "Panel", Vector2.zero, canvasRect.sizeDelta);
        Image background = panel.AddComponent<Image>();
        background.color = new Color(0.055f, 0.065f, 0.075f, 0.92f);

        GameObject strip = CreateRect(panel.transform, "Status Strip", new Vector2(0f, 0f), new Vector2(10f, 210f));
        RectTransform stripRect = strip.GetComponent<RectTransform>();
        stripRect.anchorMin = new Vector2(0f, 0.5f);
        stripRect.anchorMax = new Vector2(0f, 0.5f);
        stripRect.pivot = new Vector2(0f, 0.5f);
        stripRect.anchoredPosition = new Vector2(0f, 0f);
        statusStrip = strip.AddComponent<Image>();

        idText = CreateText(panel.transform, "ID", new Vector2(18f, -12f), new Vector2(190f, 22f), 15, FontStyle.Bold, TextAnchor.MiddleLeft);
        statusText = CreateText(panel.transform, "WAITING", new Vector2(250f, -12f), new Vector2(92f, 22f), 13, FontStyle.Bold, TextAnchor.MiddleRight);
        CreateImagePreview(panel.transform);
        shapeText = CreateText(panel.transform, "Shape: unknown", new Vector2(18f, -46f), new Vector2(205f, 22f), 13, FontStyle.Normal, TextAnchor.MiddleLeft);
        decisionText = CreateText(panel.transform, "Route: pending", new Vector2(18f, -72f), new Vector2(205f, 22f), 13, FontStyle.Bold, TextAnchor.MiddleLeft);
        confidenceText = CreateText(panel.transform, "Vision: -", new Vector2(18f, -98f), new Vector2(205f, 22f), 12, FontStyle.Normal, TextAnchor.MiddleLeft);
        sensorText = CreateText(panel.transform, "Sensors: waiting", new Vector2(18f, -124f), new Vector2(205f, 32f), 12, FontStyle.Normal, TextAnchor.UpperLeft);
        modelText = CreateText(panel.transform, "AI panel attached", new Vector2(18f, -168f), new Vector2(318f, 28f), 11, FontStyle.Italic, TextAnchor.UpperLeft);
        SetStrip(new Color(0.36f, 0.38f, 0.42f));
    }

    void CreateImagePreview(Transform parent)
    {
        GameObject frame = CreateRect(parent, "Camera Image Frame", new Vector2(238f, -46f), new Vector2(104f, 78f));
        RectTransform frameRect = frame.GetComponent<RectTransform>();
        frameRect.anchorMin = new Vector2(0f, 1f);
        frameRect.anchorMax = new Vector2(0f, 1f);
        frameRect.pivot = new Vector2(0f, 1f);
        Image frameImage = frame.AddComponent<Image>();
        frameImage.color = new Color(0.10f, 0.12f, 0.14f, 0.96f);

        GameObject preview = CreateRect(frame.transform, "Captured Battery Image", new Vector2(6f, -6f), new Vector2(92f, 54f));
        RectTransform previewRect = preview.GetComponent<RectTransform>();
        previewRect.anchorMin = new Vector2(0f, 1f);
        previewRect.anchorMax = new Vector2(0f, 1f);
        previewRect.pivot = new Vector2(0f, 1f);
        capturedImage = preview.AddComponent<RawImage>();
        capturedImage.color = new Color(0.18f, 0.20f, 0.23f, 1f);

        imageLabelText = CreateText(frame.transform, "Camera image", new Vector2(6f, -62f), new Vector2(92f, 14f), 9, FontStyle.Normal, TextAnchor.MiddleCenter);
    }

    GameObject CreateRect(Transform parent, string name, Vector2 anchoredPosition, Vector2 size)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        RectTransform rect = go.AddComponent<RectTransform>();
        rect.anchorMin = new Vector2(0.5f, 0.5f);
        rect.anchorMax = new Vector2(0.5f, 0.5f);
        rect.pivot = new Vector2(0.5f, 0.5f);
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = size;
        return go;
    }

    Text CreateText(Transform parent, string text, Vector2 anchoredPosition, Vector2 size, int fontSize, FontStyle style, TextAnchor alignment)
    {
        GameObject go = CreateRect(parent, "Text - " + text, anchoredPosition, size);
        RectTransform rect = go.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(0f, 1f);
        rect.pivot = new Vector2(0f, 1f);
        Text uiText = go.AddComponent<Text>();
        uiText.text = text;
        uiText.font = GetBuiltInUiFont();
        uiText.fontSize = fontSize;
        uiText.fontStyle = style;
        uiText.alignment = alignment;
        uiText.color = Color.white;
        uiText.horizontalOverflow = HorizontalWrapMode.Wrap;
        uiText.verticalOverflow = VerticalWrapMode.Truncate;
        return uiText;
    }

    Font GetBuiltInUiFont()
    {
        Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        if (font != null)
        {
            return font;
        }

        return Resources.GetBuiltinResource<Font>("Arial.ttf");
    }

    string ShortId(BatteryAgent battery)
    {
        if (battery == null || string.IsNullOrEmpty(battery.batteryId))
        {
            return "BATTERY";
        }

        string id = battery.batteryId;
        return id.Length > 18 ? id.Substring(id.Length - 18) : id;
    }

    string SafeFile(string fileName)
    {
        if (string.IsNullOrEmpty(fileName))
        {
            return "-";
        }

        return Path.GetFileName(fileName);
    }

    string Percent(float confidence)
    {
        return confidence > 0f ? (confidence * 100f).ToString("0") + "%" : "-";
    }

    string SensorLine(BatteryInspectionResult result)
    {
        if (result == null)
        {
            return "Sensors: waiting";
        }

        string soh = result.predicted_soh > 0f ? result.predicted_soh.ToString("0") + "%" : result.soh > 0f ? (result.soh * 100f).ToString("0") + "%" : "-";
        string temp = result.temperature_c > 0f ? result.temperature_c.ToString("0") + " C" : "-";
        string voltage = result.voltage > 0f ? result.voltage.ToString("0.00") + " V" : "-";
        string resistance = result.internal_resistance_mohm > 0f ? result.internal_resistance_mohm.ToString("0") + " mOhm" : "-";
        return "SOH " + soh + " | " + temp + "\n" + voltage + " | " + resistance;
    }

    string ModelLine(BatteryInspectionResult result)
    {
        if (result != null && !string.IsNullOrEmpty(result.soh_model_used))
        {
            string trust = result.soh_confidence > 0f ? (result.soh_confidence * 100f).ToString("0") + "%" : "-";
            return "SOH: " + result.soh_model_used + " | trust " + trust;
        }

        if (result == null || string.IsNullOrEmpty(result.model_name))
        {
            return "CV model: image features";
        }

        return result.model_name + " | trust " + result.model_trust_percentage.ToString("0.0") + "%";
    }

    void SetCapturedImage(BatteryAgent battery)
    {
        if (battery == null)
        {
            SetImage(null);
            return;
        }

        string path = battery.ResolveImagePath();
        if (!File.Exists(path))
        {
            SetImage(null);
            return;
        }

        byte[] data = File.ReadAllBytes(path);
        Texture2D texture = new Texture2D(2, 2);
        if (texture.LoadImage(data))
        {
            SetImage(texture);
        }
    }

    void SetImage(Texture texture)
    {
        if (capturedImage != null)
        {
            capturedImage.texture = texture;
            capturedImage.color = texture == null
                ? new Color(0.18f, 0.20f, 0.23f, 1f)
                : Color.white;
        }
    }

    void SetStrip(Color color)
    {
        if (statusStrip != null)
        {
            statusStrip.color = color;
        }
    }

    void SetText(Text text, string value)
    {
        if (text != null)
        {
            text.text = value;
        }
    }
}
