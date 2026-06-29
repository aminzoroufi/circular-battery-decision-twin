using System.Collections;
using UnityEngine;

public class ConveyorController : MonoBehaviour
{
    public Transform inspectionStation;
    public Transform thermalCameraStation;
    public Transform electricalTestStation;
    public Transform impedanceStation;
    public Transform damageVisionStation;
    public Transform decisionStation;
    public OperatorControlPanel operatorControlPanel;
    public float slowSpeed = 0.75f;
    public float normalSpeed = 1.35f;
    public float fastSpeed = 2.25f;
    public float arrivalDistance = 0.05f;
    public float inspectionDwellSeconds = 0.25f;
    public float sensorDwellSeconds = 0.45f;

    public void QueueBattery(BatteryAgent battery, BatteryInspectionClient client)
    {
        StartCoroutine(MoveThroughProcess(battery, client));
    }

    IEnumerator MoveThroughProcess(BatteryAgent battery, BatteryInspectionClient client)
    {
        if (inspectionStation == null || battery == null)
        {
            yield break;
        }

        battery.currentState = "on_conveyor";
        Debug.Log("[Conveyor] Moving " + battery.batteryId + " to camera station.");
        yield return MoveBatteryToStation(battery, inspectionStation, "classification_camera");
        Debug.Log("[Conveyor] " + battery.batteryId + " stopped under camera.");
        yield return new WaitForSeconds(inspectionDwellSeconds);
        if (client != null)
        {
            yield return client.ClassifyBattery(battery);
        }

        yield return VisitSensorStation(battery, client, thermalCameraStation, "thermal", "thermal_camera_station");
        yield return VisitSensorStation(battery, client, electricalTestStation, "electrical", "electrical_test_station");
        yield return VisitSensorStation(battery, client, impedanceStation, "impedance", "impedance_station");
        yield return VisitSensorStation(battery, client, damageVisionStation, "vision_damage", "damage_vision_station");

        if (decisionStation != null)
        {
            yield return MoveBatteryToStation(battery, decisionStation, "rex_decision_gate");
        }

        BatteryInspectionResult result = null;
        if (client != null)
        {
            yield return client.FinalizeMlDecision(battery, completedResult => result = completedResult);
        }
        string robotMode = operatorControlPanel != null ? operatorControlPanel.RobotMode : "auto";
        if (client != null && client.robotSorter != null && result != null)
        {
            client.robotSorter.SortBattery(battery, result.target_bin, result.manual_review_required, robotMode);
        }
    }

    IEnumerator VisitSensorStation(BatteryAgent battery, BatteryInspectionClient client, Transform station, string stationKey, string state)
    {
        if (station == null || battery == null)
        {
            yield break;
        }

        yield return MoveBatteryToStation(battery, station, state);
        yield return new WaitForSeconds(sensorDwellSeconds);
        client?.ApplyMockSensorStage(battery, stationKey);
        yield return new WaitForSeconds(sensorDwellSeconds);
    }

    IEnumerator MoveBatteryToStation(BatteryAgent battery, Transform station, string state)
    {
        if (battery == null || station == null)
        {
            yield break;
        }

        battery.currentState = state;
        while (Vector3.Distance(battery.transform.position, station.position) > arrivalDistance)
        {
            string robotMode = operatorControlPanel != null ? operatorControlPanel.RobotMode : "auto";
            if (robotMode == "paused" || robotMode == "emergency_stop")
            {
                yield return null;
                continue;
            }

            battery.transform.position = Vector3.MoveTowards(
                battery.transform.position,
                station.position,
                SpeedForMode() * Time.deltaTime
            );
            yield return null;
        }

        battery.transform.position = station.position;
    }

    float SpeedForMode()
    {
        string speed = operatorControlPanel != null ? operatorControlPanel.ConveyorSpeed : "normal";
        if (speed == "slow") return slowSpeed;
        if (speed == "fast") return fastSpeed;
        return normalSpeed;
    }
}
