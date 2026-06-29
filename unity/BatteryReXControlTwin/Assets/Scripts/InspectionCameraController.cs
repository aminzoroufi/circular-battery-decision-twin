using System.Collections;
using UnityEngine;

public class InspectionCameraController : MonoBehaviour
{
    public Light flashLight;
    public Renderer flashIndicatorRenderer;
    public float preCaptureWaitSeconds = 0.45f;
    public float flashSeconds = 0.22f;
    public float postCaptureWaitSeconds = 0.25f;
    public float flashIntensity = 7f;

    Color idleColor = new Color(0.12f, 0.20f, 0.24f);
    Color flashColor = new Color(0.85f, 0.95f, 1f);

    void Awake()
    {
        SetFlash(false);
    }

    public IEnumerator CaptureFlash(BatteryAgent battery)
    {
        if (battery != null)
        {
            battery.currentState = "waiting_under_camera";
        }

        yield return new WaitForSeconds(preCaptureWaitSeconds);
        SetFlash(true);
        yield return new WaitForSeconds(flashSeconds);
        SetFlash(false);
        yield return new WaitForSeconds(postCaptureWaitSeconds);

        if (battery != null)
        {
            battery.currentState = "image_sent_to_backend";
        }
    }

    void SetFlash(bool active)
    {
        if (flashLight != null)
        {
            flashLight.enabled = active;
            flashLight.intensity = active ? flashIntensity : 0f;
        }

        if (flashIndicatorRenderer != null)
        {
            flashIndicatorRenderer.sharedMaterial.color = active ? flashColor : idleColor;
        }
    }
}
