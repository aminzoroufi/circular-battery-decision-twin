using UnityEngine;
using UnityEngine.UI;

public class ProcessLoggerClient : MonoBehaviour
{
    public Text inspectedCountText;
    public Text reuseCountText;
    public Text remanufactureCountText;
    public Text recycleCountText;
    public Text quarantineCountText;
    public Text latestDecisionText;

    int inspectedCount;
    int reuseCount;
    int remanufactureCount;
    int recycleCount;
    int quarantineCount;

    public void SetLatestResult(BatteryInspectionResult result)
    {
        if (result == null)
        {
            return;
        }

        inspectedCount++;
        switch (result.final_decision)
        {
            case "reuse":
                reuseCount++;
                break;
            case "remanufacture":
                remanufactureCount++;
                break;
            case "recycle":
                recycleCount++;
                break;
            case "quarantine":
            case "manual_review":
                quarantineCount++;
                break;
        }

        Refresh(result.final_decision);
    }

    void Refresh(string latestDecision)
    {
        SetText(inspectedCountText, inspectedCount.ToString());
        SetText(reuseCountText, reuseCount.ToString());
        SetText(remanufactureCountText, remanufactureCount.ToString());
        SetText(recycleCountText, recycleCount.ToString());
        SetText(quarantineCountText, quarantineCount.ToString());
        SetText(latestDecisionText, latestDecision);
    }

    void SetText(Text text, string value)
    {
        if (text != null)
        {
            text.text = value;
        }
    }
}
