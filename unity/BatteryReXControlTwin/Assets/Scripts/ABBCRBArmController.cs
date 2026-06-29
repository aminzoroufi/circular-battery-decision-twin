using System.Collections;
using UnityEngine;

public class ABBCRBArmController : MonoBehaviour
{
    public Transform baseJoint;
    public Transform shoulderJoint;
    public Transform elbowJoint;
    public Transform wristJoint;
    public Transform upperArmLink;
    public Transform forearmLink;
    public Transform toolFlange;
    public Transform gripper;
    public Transform leftFinger;
    public Transform rightFinger;

    public float moveSpeed = 2.4f;
    public float placementHeight = 0.0f;
    public float liftHeight = 0.95f;
    public float elbowLift = 0.45f;
    public float linkThickness = 0.16f;

    Vector3 homeToolPosition;
    bool homeCaptured;

    void Start()
    {
        CaptureHome();
        SetGripperClosed(false);
        if (gripper != null)
        {
            UpdateArmGeometry(gripper.position);
        }
    }

    public IEnumerator PickAndPlace(BatteryAgent battery, Transform destination)
    {
        if (battery == null || destination == null || gripper == null)
        {
            yield break;
        }

        CaptureHome();
        battery.currentState = "robot_approaching";
        Vector3 pickup = battery.transform.position;
        Vector3 pickupAbove = pickup + Vector3.up * liftHeight;
        Vector3 drop = destination.position + Vector3.up * placementHeight;
        Vector3 dropAbove = drop + Vector3.up * liftHeight;

        Debug.Log("[ABBCRBArm] Moving to pick " + battery.batteryId);
        SetGripperClosed(false);
        yield return MoveToolTo(pickupAbove);
        yield return MoveToolTo(pickup + Vector3.up * 0.18f);

        battery.currentState = "robot_gripped";
        SetGripperClosed(true);
        battery.SetHeldByRobot(true);
        battery.transform.SetParent(gripper, true);
        battery.transform.position = gripper.position + Vector3.down * 0.22f;
        yield return new WaitForSeconds(0.12f);

        battery.currentState = "robot_carrying";
        Debug.Log("[ABBCRBArm] Carrying " + battery.batteryId + " to " + destination.name);
        yield return MoveToolTo(pickupAbove);
        yield return MoveToolTo(dropAbove);
        yield return MoveToolTo(drop);

        battery.transform.SetParent(null, true);
        battery.transform.position = drop;
        battery.SetHeldByRobot(false);
        battery.currentState = "sorted_" + battery.targetBin;
        SetGripperClosed(false);
        Debug.Log("[ABBCRBArm] Released " + battery.batteryId + " at " + destination.name);
        yield return new WaitForSeconds(0.12f);

        yield return MoveToolTo(homeToolPosition);
        Debug.Log("[ABBCRBArm] Returned home.");
    }

    IEnumerator MoveToolTo(Vector3 target)
    {
        while (Vector3.Distance(gripper.position, target) > 0.025f)
        {
            gripper.position = Vector3.MoveTowards(gripper.position, target, moveSpeed * Time.deltaTime);
            UpdateArmGeometry(gripper.position);
            yield return null;
        }

        gripper.position = target;
        UpdateArmGeometry(target);
    }

    void CaptureHome()
    {
        if (!homeCaptured && gripper != null)
        {
            homeToolPosition = gripper.position;
            homeCaptured = true;
        }
    }

    void UpdateArmGeometry(Vector3 toolPosition)
    {
        if (baseJoint != null)
        {
            Vector3 planarTarget = new Vector3(toolPosition.x, baseJoint.position.y, toolPosition.z);
            Vector3 direction = planarTarget - baseJoint.position;
            if (direction.sqrMagnitude > 0.001f)
            {
                baseJoint.rotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
            }
        }

        if (shoulderJoint == null)
        {
            return;
        }

        Vector3 shoulderPosition = shoulderJoint.position;
        Vector3 wristPosition = toolPosition + Vector3.up * 0.08f;
        Vector3 elbowPosition = Vector3.Lerp(shoulderPosition, wristPosition, 0.55f) + Vector3.up * elbowLift;

        if (elbowJoint != null)
        {
            elbowJoint.position = elbowPosition;
        }

        if (wristJoint != null)
        {
            wristJoint.position = wristPosition;
        }

        PlaceLinkBetween(upperArmLink, shoulderPosition, elbowPosition);
        PlaceLinkBetween(forearmLink, elbowPosition, wristPosition);

        if (toolFlange != null)
        {
            toolFlange.position = toolPosition + Vector3.up * 0.06f;
            toolFlange.rotation = Quaternion.LookRotation(Vector3.forward, Vector3.up);
        }
    }

    void PlaceLinkBetween(Transform link, Vector3 start, Vector3 end)
    {
        if (link == null)
        {
            return;
        }

        Vector3 direction = end - start;
        float length = direction.magnitude;
        if (length <= 0.001f)
        {
            return;
        }

        link.position = start + direction * 0.5f;
        link.rotation = Quaternion.FromToRotation(Vector3.up, direction.normalized);
        link.localScale = new Vector3(linkThickness, length * 0.5f, linkThickness);
    }

    void SetGripperClosed(bool closed)
    {
        float offset = closed ? 0.055f : 0.18f;
        if (leftFinger != null)
        {
            leftFinger.localPosition = new Vector3(-offset, -0.18f, 0f);
        }

        if (rightFinger != null)
        {
            rightFinger.localPosition = new Vector3(offset, -0.18f, 0f);
        }
    }
}
