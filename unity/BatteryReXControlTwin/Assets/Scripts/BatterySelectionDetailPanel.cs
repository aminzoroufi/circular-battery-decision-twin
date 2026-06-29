using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class BatterySelectionDetailPanel : MonoBehaviour
{
    static BatterySelectionDetailPanel instance;

    public Vector2 openSize = new Vector2(470f, 690f);
    public Vector2 closedSize = new Vector2(58f, 58f);
    public float animationSeconds = 0.22f;

    RectTransform panelRect;
    CanvasGroup panelGroup;
    Image statusStrip;
    RawImage imagePreview;
    Text titleText;
    Text statusText;
    Text idText;
    Text shapeText;
    Text decisionText;
    Text confidenceText;
    Text sohText;
    Text temperatureText;
    Text voltageText;
    Text resistanceText;
    Text riskText;
    Text routeText;
    Text modelText;
    Text reasonText;
    Text fileText;
    Button toggleButton;

    BatteryAgent selectedBattery;
    Coroutine animationRoutine;
    bool isOpen = true;

    void Awake()
    {
        instance = this;
        BuildPanel();
        SetOpen(false, true);
    }

    public static void ShowBattery(BatteryAgent battery)
    {
        EnsureInstance();
        instance.selectedBattery = battery;
        instance.Refresh();
        instance.SetOpen(true, false);
    }

    public static void RefreshIfSelected(BatteryAgent battery)
    {
        if (instance == null || battery == null || instance.selectedBattery != battery)
        {
            return;
        }

        instance.Refresh();
    }

    static void EnsureInstance()
    {
        if (instance != null)
        {
            return;
        }

        Canvas canvas = null;
        Canvas[] canvases = Object.FindObjectsOfType<Canvas>();
        foreach (Canvas candidate in canvases)
        {
            if (candidate != null && candidate.renderMode == RenderMode.ScreenSpaceOverlay)
            {
                canvas = candidate;
                break;
            }
        }

        if (canvas == null)
        {
            GameObject canvasGo = new GameObject("Runtime UI Canvas");
            canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            CanvasScaler scaler = canvasGo.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            canvasGo.AddComponent<GraphicRaycaster>();
        }

        if (Object.FindObjectOfType<EventSystem>() == null)
        {
            GameObject eventSystem = new GameObject("EventSystem");
            eventSystem.AddComponent<EventSystem>();
            eventSystem.AddComponent<StandaloneInputModule>();
        }

        GameObject panelGo = new GameObject("Selected Battery Detail Panel");
        panelGo.transform.SetParent(canvas.transform, false);
        instance = panelGo.AddComponent<BatterySelectionDetailPanel>();
    }

    public void Toggle()
    {
        SetOpen(!isOpen, false);
    }

    void SetOpen(bool open, bool instant)
    {
        isOpen = open;
        if (animationRoutine != null)
        {
            StopCoroutine(animationRoutine);
        }

        if (instant)
        {
            ApplyAnimationState(open ? 1f : 0f);
            return;
        }

        animationRoutine = StartCoroutine(AnimateOpen(open));
    }

    IEnumerator AnimateOpen(bool open)
    {
        float start = panelRect.sizeDelta.x <= closedSize.x + 1f ? 0f : 1f;
        float end = open ? 1f : 0f;
        float elapsed = 0f;

        while (elapsed < animationSeconds)
        {
            elapsed += Time.unscaledDeltaTime;
            float t = Mathf.Clamp01(elapsed / animationSeconds);
            t = t * t * (3f - 2f * t);
            ApplyAnimationState(Mathf.Lerp(start, end, t));
            yield return null;
        }

        ApplyAnimationState(end);
        animationRoutine = null;
    }

    void ApplyAnimationState(float t)
    {
        if (panelRect == null || panelGroup == null)
        {
            return;
        }

        panelRect.sizeDelta = Vector2.Lerp(closedSize, openSize, t);
        panelGroup.alpha = 1f;
        panelGroup.interactable = true;
        panelGroup.blocksRaycasts = true;

        if (toggleButton != null)
        {
            Text label = toggleButton.GetComponentInChildren<Text>();
            if (label != null)
            {
                label.text = t > 0.5f ? "X" : "i";
            }
        }
    }

    void Refresh()
    {
        if (selectedBattery == null)
        {
            SetEmpty();
            return;
        }

        BatteryInspectionResult result = selectedBattery.latestResult;
        DecisionCategory decision = selectedBattery.decisionCategory;
        SetText(titleText, "Selected Battery");
        SetText(statusText, selectedBattery.currentState);
        SetText(idText, selectedBattery.batteryId);
        SetText(shapeText, BatteryCategoryMapper.ShapeLabel(selectedBattery.currentShape));
        SetText(decisionText, BatteryCategoryMapper.DecisionLabel(decision));
        SetText(confidenceText, result != null && result.confidence > 0f ? (result.confidence * 100f).ToString("0.0") + "%" : "-");
        SetText(sohText, result != null && result.predicted_soh > 0f ? result.predicted_soh.ToString("0.0") + "%" : result != null && result.soh > 0f ? (result.soh * 100f).ToString("0.0") + "%" : "-");
        SetText(temperatureText, result != null && result.temperature_c > 0f ? result.temperature_c.ToString("0.0") + " C" : "-");
        SetText(voltageText, result != null && result.voltage > 0f ? result.voltage.ToString("0.00") + " V" : "-");
        SetText(resistanceText, result != null && result.internal_resistance_mohm > 0f ? result.internal_resistance_mohm.ToString("0.0") + " mOhm" : "-");
        SetText(riskText, result != null && result.risk_score > 0f ? result.risk_score.ToString("0") + " / " + result.risk_level : "-");
        SetText(routeText, result != null ? result.target_bin : selectedBattery.targetBin);
        SetText(modelText, ModelLine(result));
        SetText(reasonText, result != null && !string.IsNullOrEmpty(result.reason) ? result.reason : "Waiting for inspection data from this battery.");
        SetText(fileText, string.IsNullOrEmpty(selectedBattery.capturedImagePath) ? "-" : Path.GetFileName(selectedBattery.capturedImagePath));
        SetImage(selectedBattery);

        if (statusStrip != null)
        {
            statusStrip.color = BatteryCategoryMapper.DecisionColor(decision);
        }
    }

    void SetEmpty()
    {
        SetText(titleText, "Selected Battery");
        SetText(statusText, "No selection");
        SetText(idText, "-");
        SetText(shapeText, "-");
        SetText(decisionText, "-");
        SetText(confidenceText, "-");
        SetText(sohText, "-");
        SetText(temperatureText, "-");
        SetText(voltageText, "-");
        SetText(resistanceText, "-");
        SetText(riskText, "-");
        SetText(routeText, "-");
        SetText(modelText, "-");
        SetText(reasonText, "Tap a battery in the scene to inspect its AI result.");
        SetText(fileText, "-");
        if (imagePreview != null)
        {
            imagePreview.texture = null;
            imagePreview.color = new Color(0.16f, 0.18f, 0.21f, 1f);
        }
    }

    void BuildPanel()
    {
        if (panelRect != null)
        {
            return;
        }

        panelRect = gameObject.GetComponent<RectTransform>();
        if (panelRect == null)
        {
            panelRect = gameObject.AddComponent<RectTransform>();
        }

        panelRect.anchorMin = new Vector2(1f, 1f);
        panelRect.anchorMax = new Vector2(1f, 1f);
        panelRect.pivot = new Vector2(1f, 1f);
        panelRect.anchoredPosition = new Vector2(-14f, -118f);
        panelRect.sizeDelta = openSize;

        Image background = gameObject.AddComponent<Image>();
        background.color = new Color(0.055f, 0.065f, 0.075f, 0.94f);
        gameObject.AddComponent<RectMask2D>();
        panelGroup = gameObject.AddComponent<CanvasGroup>();

        GameObject strip = CreateRect(transform, "Status Strip", new Vector2(0f, 0f), new Vector2(10f, openSize.y));
        RectTransform stripRect = strip.GetComponent<RectTransform>();
        stripRect.anchorMin = new Vector2(0f, 0f);
        stripRect.anchorMax = new Vector2(0f, 1f);
        stripRect.pivot = new Vector2(0f, 0.5f);
        stripRect.anchoredPosition = Vector2.zero;
        stripRect.sizeDelta = new Vector2(10f, 0f);
        statusStrip = strip.AddComponent<Image>();
        statusStrip.color = new Color(0.36f, 0.38f, 0.42f);

        toggleButton = CreateButton(transform, "X", new Vector2(-12f, -12f), new Vector2(38f, 34f));
        toggleButton.onClick.AddListener(Toggle);

        titleText = CreateText(transform, "Selected Battery", new Vector2(22f, -18f), new Vector2(260f, 28f), 22, FontStyle.Bold, TextAnchor.MiddleLeft);
        statusText = CreateText(transform, "No selection", new Vector2(265f, -20f), new Vector2(140f, 24f), 14, FontStyle.Bold, TextAnchor.MiddleRight);

        imagePreview = CreateRawImage(transform, "Selected Battery Image", new Vector2(22f, -62f), new Vector2(190f, 124f));
        CreateText(transform, "Camera image", new Vector2(22f, -194f), new Vector2(120f, 20f), 13, FontStyle.Bold, TextAnchor.MiddleLeft);
        fileText = CreateText(transform, "-", new Vector2(122f, -194f), new Vector2(290f, 20f), 12, FontStyle.Normal, TextAnchor.MiddleRight);

        int y = -232;
        idText = AddRow("Battery ID", ref y);
        shapeText = AddRow("Physical shape", ref y);
        decisionText = AddRow("Re-X decision", ref y);
        confidenceText = AddRow("Vision trust", ref y);
        sohText = AddRow("SOH", ref y);
        temperatureText = AddRow("Temperature", ref y);
        voltageText = AddRow("Voltage", ref y);
        resistanceText = AddRow("Resistance", ref y);
        riskText = AddRow("Risk", ref y);
        routeText = AddRow("Target bin", ref y);
        modelText = AddRow("Model", ref y);

        CreateText(transform, "Reasoning", new Vector2(22f, y - 10f), new Vector2(130f, 22f), 14, FontStyle.Bold, TextAnchor.MiddleLeft);
        reasonText = CreateText(transform, "Tap a battery in the scene to inspect its AI result.", new Vector2(22f, y - 40f), new Vector2(405f, 90f), 13, FontStyle.Normal, TextAnchor.UpperLeft);
    }

    Text AddRow(string label, ref int y)
    {
        CreateText(transform, label, new Vector2(22f, y), new Vector2(145f, 22f), 13, FontStyle.Bold, TextAnchor.MiddleLeft);
        Text value = CreateText(transform, "-", new Vector2(172f, y), new Vector2(255f, 22f), 13, FontStyle.Normal, TextAnchor.MiddleRight);
        y -= 32;
        return value;
    }

    GameObject CreateRect(Transform parent, string name, Vector2 anchoredPosition, Vector2 size)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        RectTransform rect = go.AddComponent<RectTransform>();
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(0f, 1f);
        rect.pivot = new Vector2(0f, 1f);
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = size;
        return go;
    }

    Text CreateText(Transform parent, string text, Vector2 anchoredPosition, Vector2 size, int fontSize, FontStyle style, TextAnchor alignment)
    {
        GameObject go = CreateRect(parent, "Text - " + text, anchoredPosition, size);
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

    Button CreateButton(Transform parent, string label, Vector2 anchoredPosition, Vector2 size)
    {
        GameObject go = CreateRect(parent, "Button - Toggle Selected Battery Panel", anchoredPosition, size);
        RectTransform rect = go.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(1f, 1f);
        rect.anchorMax = new Vector2(1f, 1f);
        rect.pivot = new Vector2(1f, 1f);
        Image image = go.AddComponent<Image>();
        image.color = new Color(0.14f, 0.16f, 0.18f, 1f);
        Button button = go.AddComponent<Button>();
        CreateText(go.transform, label, new Vector2(0f, 0f), size, 18, FontStyle.Bold, TextAnchor.MiddleCenter);
        return button;
    }

    RawImage CreateRawImage(Transform parent, string name, Vector2 anchoredPosition, Vector2 size)
    {
        GameObject go = CreateRect(parent, name, anchoredPosition, size);
        RawImage rawImage = go.AddComponent<RawImage>();
        rawImage.color = new Color(0.16f, 0.18f, 0.21f, 1f);
        return rawImage;
    }

    void SetImage(BatteryAgent battery)
    {
        if (imagePreview == null)
        {
            return;
        }

        string path = battery != null ? battery.ResolveImagePath() : string.Empty;
        if (string.IsNullOrEmpty(path) || !File.Exists(path))
        {
            imagePreview.texture = null;
            imagePreview.color = new Color(0.16f, 0.18f, 0.21f, 1f);
            return;
        }

        byte[] data = File.ReadAllBytes(path);
        Texture2D texture = new Texture2D(2, 2);
        if (texture.LoadImage(data))
        {
            imagePreview.texture = texture;
            imagePreview.color = Color.white;
        }
    }

    string ModelLine(BatteryInspectionResult result)
    {
        if (result != null && !string.IsNullOrEmpty(result.soh_model_used))
        {
            string sohTrust = result.soh_confidence > 0f
                ? (result.soh_confidence * 100f).ToString("0.0") + "%"
                : "-";
            return result.soh_model_used + " SOH (" + sohTrust + ")";
        }

        if (result == null || string.IsNullOrEmpty(result.model_name))
        {
            return "waiting";
        }

        string trust = result.model_trust_percentage > 0f
            ? result.model_trust_percentage.ToString("0.0") + "%"
            : "-";
        return result.model_name + " (" + trust + ")";
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

    void SetText(Text text, string value)
    {
        if (text != null)
        {
            text.text = string.IsNullOrEmpty(value) ? "-" : value;
        }
    }
}
