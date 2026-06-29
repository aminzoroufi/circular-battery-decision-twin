using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

public class BatterySpawner : MonoBehaviour
{
    public string manifestFileName = "sample_manifest.json";
    public Transform intakePoint;
    public ConveyorController conveyorController;
    public BatteryInspectionClient inspectionClient;
    public float spawnIntervalSeconds = 0.55f;
    public float releaseDelayAfterCameraSeconds = 0.35f;
    public int maxActiveBatteries = 4;

    ManifestBatteryList manifest;
    int nextIndex;
    Coroutine batchRoutine;
    readonly List<BatteryAgent> activeBatteries = new List<BatteryAgent>();
    BatteryAgent lastReleasedBattery;

    void Awake()
    {
        LoadManifest();
    }

    public void StartBatch()
    {
        if (batchRoutine == null)
        {
            batchRoutine = StartCoroutine(SpawnBatch());
        }
    }

    public void StopBatch()
    {
        if (batchRoutine != null)
        {
            StopCoroutine(batchRoutine);
            batchRoutine = null;
        }
    }

    IEnumerator SpawnBatch()
    {
        while (manifest != null && manifest.batteries != null && manifest.batteries.Length > 0)
        {
            CleanupActiveBatteries();
            if (activeBatteries.Count < maxActiveBatteries && CanReleaseNextBattery())
            {
                BatteryAgent battery = SpawnNextBattery();
                if (battery != null)
                {
                    activeBatteries.Add(battery);
                    lastReleasedBattery = battery;
                    Debug.Log("[BatterySpawner] Pipeline release for " + battery.batteryId + " active=" + activeBatteries.Count);
                    conveyorController?.QueueBattery(battery, inspectionClient);
                    if (releaseDelayAfterCameraSeconds > 0f)
                    {
                        yield return new WaitForSeconds(releaseDelayAfterCameraSeconds);
                    }
                }
            }

            yield return new WaitForSeconds(spawnIntervalSeconds);
        }
    }

    bool CanReleaseNextBattery()
    {
        if (lastReleasedBattery == null || lastReleasedBattery.IsSorted)
        {
            return true;
        }

        return lastReleasedBattery.cameraClassificationComplete &&
            lastReleasedBattery.currentState != "classification_camera";
    }

    BatteryAgent SpawnNextBattery()
    {
        ManifestBattery item = manifest.batteries[nextIndex % manifest.batteries.Length];
        nextIndex++;

        GameObject instance = new GameObject("Unknown Battery");
        instance.transform.position = intakePoint != null ? intakePoint.position : transform.position;

        BatteryAgent agent = instance.AddComponent<BatteryAgent>();
        instance.AddComponent<BatteryVisualController>();
        agent.Configure(item);
        return agent;
    }

    void CleanupActiveBatteries()
    {
        for (int i = activeBatteries.Count - 1; i >= 0; i--)
        {
            BatteryAgent battery = activeBatteries[i];
            if (battery == null || battery.IsSorted)
            {
                activeBatteries.RemoveAt(i);
            }
        }
    }

    void LoadManifest()
    {
        string path = Path.Combine(Application.streamingAssetsPath, manifestFileName);
        if (!File.Exists(path))
        {
            Debug.LogError("Manifest not found: " + path);
            return;
        }

        manifest = JsonUtility.FromJson<ManifestBatteryList>(File.ReadAllText(path));
    }
}
