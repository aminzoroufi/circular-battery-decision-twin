using System.Collections;
using System.Collections.Generic;
using System;
using UnityEngine;

public class RobotSorter : MonoBehaviour
{
    public Transform reuseBin;
    public Transform remanufactureBin;
    public Transform recycleBin;
    public Transform quarantineBin;
    public ABBCRBArmController armController;
    public float sortingSpeed = 1.8f;
    public int slotsPerRow = 3;
    public int slotRows = 2;
    public float slotSpacing = 0.42f;
    public float stackLayerHeight = 0.18f;
    public event Action<BatteryAgent> SortCompleted;

    readonly Queue<SortTask> manualQueue = new Queue<SortTask>();
    readonly HashSet<BatteryAgent> activeSorts = new HashSet<BatteryAgent>();
    readonly Dictionary<Transform, int> binSlotCounts = new Dictionary<Transform, int>();

    public void SortBattery(BatteryAgent battery, string targetBin, bool manualReviewRequired, string robotMode)
    {
        if (battery == null)
        {
            return;
        }

        if (robotMode == "manual")
        {
            manualQueue.Enqueue(new SortTask(battery, targetBin, manualReviewRequired));
            battery.currentState = "waiting_for_operator_approval";
            Debug.Log("[RobotSorter] Manual mode queued " + battery.batteryId + " for " + targetBin);
            return;
        }

        if (robotMode == "paused" || robotMode == "emergency_stop" || targetBin == "none")
        {
            battery.currentState = "sorting_paused";
            Debug.Log("[RobotSorter] Sorting paused for " + battery.batteryId + " mode=" + robotMode + " target=" + targetBin);
            return;
        }

        Debug.Log("[RobotSorter] Sorting " + battery.batteryId + " to " + targetBin);
        StartCoroutine(PerformSort(battery, targetBin, manualReviewRequired));
    }

    public void ApproveNextManualSort()
    {
        if (manualQueue.Count == 0)
        {
            return;
        }

        SortTask task = manualQueue.Dequeue();
        StartCoroutine(PerformSort(task.battery, task.targetBin, task.manualReviewRequired));
    }

    IEnumerator PerformSort(BatteryAgent battery, string targetBin, bool manualReviewRequired)
    {
        if (activeSorts.Contains(battery))
        {
            yield break;
        }

        Transform bin = ResolveBin(targetBin, manualReviewRequired);
        if (bin == null)
        {
            Debug.LogWarning("No destination configured for target bin: " + targetBin);
            yield break;
        }
        Transform destination = ReservePlacementSlot(bin, targetBin);

        activeSorts.Add(battery);
        battery.targetBin = targetBin;
        battery.currentState = "robot_sorting";
        if (armController != null)
        {
            yield return armController.PickAndPlace(battery, destination);
        }
        else
        {
            yield return MoveBatteryToBin(battery, destination);
        }

        activeSorts.Remove(battery);
        Debug.Log("[RobotSorter] Sort complete for " + battery.batteryId + " -> " + targetBin);
        SortCompleted?.Invoke(battery);
    }

    IEnumerator MoveBatteryToBin(BatteryAgent battery, Transform destination)
    {
        Vector3 dropPosition = destination.position;
        while (Vector3.Distance(battery.transform.position, dropPosition) > 0.05f)
        {
            battery.transform.position = Vector3.MoveTowards(
                battery.transform.position,
                dropPosition,
                sortingSpeed * Time.deltaTime
            );
            yield return null;
        }

        battery.currentState = "sorted_" + battery.targetBin;
    }

    Transform ResolveBin(string targetBin, bool manualReviewRequired)
    {
        if (manualReviewRequired)
        {
            return quarantineBin;
        }

        switch (targetBin)
        {
            case "reuse_bin": return reuseBin;
            case "remanufacture_bin": return remanufactureBin;
            case "recycle_bin": return recycleBin;
            case "quarantine_bin": return quarantineBin;
            default:
                DecisionCategory decision = BatteryCategoryMapper.NormalizeDecision(targetBin);
                switch (decision)
                {
                    case DecisionCategory.Reuse: return reuseBin;
                    case DecisionCategory.Remanufacture: return remanufactureBin;
                    case DecisionCategory.Recycle: return recycleBin;
                    default: return quarantineBin;
                }
        }
    }

    Transform ReservePlacementSlot(Transform bin, string targetBin)
    {
        int count = binSlotCounts.ContainsKey(bin) ? binSlotCounts[bin] : 0;
        binSlotCounts[bin] = count + 1;

        int columns = Mathf.Max(1, slotsPerRow);
        int rows = Mathf.Max(1, slotRows);
        int layerSize = columns * rows;
        int layer = count / layerSize;
        int layerIndex = count % layerSize;
        int column = layerIndex % columns;
        int row = layerIndex / columns;

        float xOffset = (column - (columns - 1) * 0.5f) * slotSpacing;
        float zOffset = (row - (rows - 1) * 0.5f) * slotSpacing;
        Vector3 slotPosition = bin.position + new Vector3(xOffset, layer * stackLayerHeight, zOffset);

        GameObject slot = new GameObject("Slot - " + targetBin + " - " + count);
        slot.transform.SetParent(bin, true);
        slot.transform.position = slotPosition;
        Debug.Log("[RobotSorter] Reserved " + slot.name + " at " + slotPosition);
        return slot.transform;
    }

    struct SortTask
    {
        public BatteryAgent battery;
        public string targetBin;
        public bool manualReviewRequired;

        public SortTask(BatteryAgent battery, string targetBin, bool manualReviewRequired)
        {
            this.battery = battery;
            this.targetBin = targetBin;
            this.manualReviewRequired = manualReviewRequired;
        }
    }
}
