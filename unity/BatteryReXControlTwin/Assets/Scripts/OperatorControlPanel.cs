using UnityEngine;
using UnityEngine.UI;

public class OperatorControlPanel : MonoBehaviour
{
    public BatterySpawner batterySpawner;
    public RobotSorter robotSorter;
    public BatteryInspectionClient inspectionClient;

    public Button startBatchButton;
    public Button pauseButton;
    public Button resumeButton;
    public Button emergencyStopButton;
    public Button manualModeButton;
    public Button approveManualSortButton;
    public Button overrideReuseButton;
    public Button overrideRemanufactureButton;
    public Button overrideRecycleButton;
    public Button overrideQuarantineButton;

    public Dropdown policyDropdown;
    public Dropdown conveyorSpeedDropdown;
    public Slider confidenceThresholdSlider;
    public Slider reuseSohThresholdSlider;
    public Text confidenceThresholdLabel;
    public Text reuseSohThresholdLabel;

    [SerializeField] string policyMode = "balanced";
    [SerializeField] string conveyorSpeed = "normal";
    [SerializeField] string robotMode = "auto";
    [SerializeField] float confidenceThreshold = 0.65f;
    [SerializeField] float reuseSohThreshold = 0.80f;

    public string PolicyMode => policyMode;
    public string ConveyorSpeed => conveyorSpeed;
    public string RobotMode => robotMode;
    public float ConfidenceThreshold => confidenceThreshold;
    public float ReuseSohThreshold => reuseSohThreshold;

    void Start()
    {
        BindUiEvents();
        ApplyUiValues();
    }

    void Update()
    {
        if (confidenceThresholdSlider != null)
        {
            confidenceThreshold = confidenceThresholdSlider.value;
        }

        if (reuseSohThresholdSlider != null)
        {
            reuseSohThreshold = reuseSohThresholdSlider.value;
        }

        if (confidenceThresholdLabel != null)
        {
            confidenceThresholdLabel.text = confidenceThreshold.ToString("0.00");
        }

        if (reuseSohThresholdLabel != null)
        {
            reuseSohThresholdLabel.text = reuseSohThreshold.ToString("0.00");
        }
    }

    public void StartBatch()
    {
        robotMode = "auto";
        batterySpawner?.StartBatch();
    }

    public void Pause()
    {
        robotMode = "paused";
    }

    public void ResumeAuto()
    {
        robotMode = "auto";
    }

    public void EmergencyStop()
    {
        robotMode = "emergency_stop";
        batterySpawner?.StopBatch();
    }

    public void SetManualMode()
    {
        robotMode = "manual";
    }

    public void ApproveManualSort()
    {
        robotSorter?.ApproveNextManualSort();
    }

    public void OnPolicyDropdownChanged(int index)
    {
        string[] values = { "balanced", "safety_first", "recovery_maximization" };
        policyMode = values[Mathf.Clamp(index, 0, values.Length - 1)];
    }

    public void OnConveyorDropdownChanged(int index)
    {
        string[] values = { "slow", "normal", "fast" };
        conveyorSpeed = values[Mathf.Clamp(index, 0, values.Length - 1)];
    }

    public void OverrideReuse()
    {
        inspectionClient?.SubmitOverride("reuse", "Operator approved reuse route.");
    }

    public void OverrideRemanufacture()
    {
        inspectionClient?.SubmitOverride("remanufacture", "Operator selected remanufacturing route.");
    }

    public void OverrideRecycle()
    {
        inspectionClient?.SubmitOverride("recycle", "Operator selected recycling route.");
    }

    public void OverrideQuarantine()
    {
        inspectionClient?.SubmitOverride("quarantine", "Operator requested quarantine/manual review.");
    }

    void ApplyUiValues()
    {
        if (policyDropdown != null)
        {
            policyDropdown.ClearOptions();
            policyDropdown.AddOptions(new System.Collections.Generic.List<string>
            {
                "balanced",
                "safety_first",
                "recovery_maximization"
            });
            policyDropdown.value = policyMode == "safety_first" ? 1 : policyMode == "recovery_maximization" ? 2 : 0;
        }

        if (conveyorSpeedDropdown != null)
        {
            conveyorSpeedDropdown.ClearOptions();
            conveyorSpeedDropdown.AddOptions(new System.Collections.Generic.List<string>
            {
                "slow",
                "normal",
                "fast"
            });
            conveyorSpeedDropdown.value = conveyorSpeed == "slow" ? 0 : conveyorSpeed == "fast" ? 2 : 1;
        }

        if (confidenceThresholdSlider != null)
        {
            confidenceThresholdSlider.minValue = 0.1f;
            confidenceThresholdSlider.maxValue = 0.95f;
            confidenceThresholdSlider.value = confidenceThreshold;
        }

        if (reuseSohThresholdSlider != null)
        {
            reuseSohThresholdSlider.minValue = 0.45f;
            reuseSohThresholdSlider.maxValue = 0.95f;
            reuseSohThresholdSlider.value = reuseSohThreshold;
        }

        ApplyButtonColor(overrideReuseButton, BatteryCategoryMapper.DecisionColor(DecisionCategory.Reuse));
        ApplyButtonColor(overrideRemanufactureButton, BatteryCategoryMapper.DecisionColor(DecisionCategory.Remanufacture));
        ApplyButtonColor(overrideRecycleButton, BatteryCategoryMapper.DecisionColor(DecisionCategory.Recycle));
        ApplyButtonColor(overrideQuarantineButton, BatteryCategoryMapper.DecisionColor(DecisionCategory.Quarantine));
    }

    void BindUiEvents()
    {
        if (startBatchButton != null) startBatchButton.onClick.AddListener(StartBatch);
        if (pauseButton != null) pauseButton.onClick.AddListener(Pause);
        if (resumeButton != null) resumeButton.onClick.AddListener(ResumeAuto);
        if (emergencyStopButton != null) emergencyStopButton.onClick.AddListener(EmergencyStop);
        if (manualModeButton != null) manualModeButton.onClick.AddListener(SetManualMode);
        if (approveManualSortButton != null) approveManualSortButton.onClick.AddListener(ApproveManualSort);
        if (overrideReuseButton != null) overrideReuseButton.onClick.AddListener(OverrideReuse);
        if (overrideRemanufactureButton != null) overrideRemanufactureButton.onClick.AddListener(OverrideRemanufacture);
        if (overrideRecycleButton != null) overrideRecycleButton.onClick.AddListener(OverrideRecycle);
        if (overrideQuarantineButton != null) overrideQuarantineButton.onClick.AddListener(OverrideQuarantine);
        if (policyDropdown != null) policyDropdown.onValueChanged.AddListener(OnPolicyDropdownChanged);
        if (conveyorSpeedDropdown != null) conveyorSpeedDropdown.onValueChanged.AddListener(OnConveyorDropdownChanged);
    }

    void ApplyButtonColor(Button button, Color color)
    {
        if (button != null && button.image != null)
        {
            button.image.color = color;
        }
    }
}
