using UnityEngine;

public class BatteryVisualController : MonoBehaviour
{
    public BatteryShape currentShape = BatteryShape.Unknown;
    public DecisionCategory currentDecision = DecisionCategory.Quarantine;
    public Transform visualRoot;
    public float surfaceOffset = 0.08f;

    public void ApplyShapeOnly(BatteryShape shape)
    {
        BuildVisual(shape, currentDecision, BatteryCategoryMapper.ShapeNeutralColor(shape));
    }

    public void ApplyVisual(BatteryShape shape, DecisionCategory decision)
    {
        BuildVisual(shape, decision, BatteryCategoryMapper.DecisionColor(decision));
    }

    void BuildVisual(BatteryShape shape, DecisionCategory decision, Color bodyColor)
    {
        currentShape = shape;
        currentDecision = decision;
        ClearVisual();
        visualRoot = new GameObject("Battery Visual - " + BatteryCategoryMapper.ShapeLabel(shape)).transform;
        visualRoot.SetParent(transform, false);
        visualRoot.localPosition = new Vector3(0f, surfaceOffset, 0f);
        visualRoot.localRotation = Quaternion.identity;

        switch (shape)
        {
            case BatteryShape.Cylindrical:
                AddCylindricalPack(bodyColor);
                break;
            case BatteryShape.Pouch:
                AddPouchCell(bodyColor);
                break;
            case BatteryShape.Prismatic:
                AddPrismaticModule(bodyColor);
                break;
            default:
                AddUnknownPack(bodyColor);
                break;
        }

        Debug.Log("[BatteryVisual] " + name + " shape=" + BatteryCategoryMapper.ShapeLabel(shape) + " decisionColor=" + BatteryCategoryMapper.DecisionLabel(decision));
    }

    public void ApplyCategory(string category)
    {
        ApplyVisual(BatteryCategoryMapper.NormalizeShape(category), DecisionCategory.Quarantine);
    }

    void ClearVisual()
    {
        if (visualRoot == null)
        {
            return;
        }

        if (Application.isPlaying)
        {
            Destroy(visualRoot.gameObject);
        }
        else
        {
            DestroyImmediate(visualRoot.gameObject);
        }

        visualRoot = null;
    }

    void AddUnknownPack(Color bodyColor)
    {
        AddPart(PrimitiveType.Cube, "Unknown Shrink Wrapped Body", Vector3.zero, Quaternion.identity, new Vector3(0.58f, 0.18f, 0.34f), bodyColor);
        AddPart(PrimitiveType.Cube, "Unknown Dark End Cap A", new Vector3(-0.32f, 0.01f, 0f), Quaternion.identity, new Vector3(0.035f, 0.20f, 0.36f), new Color(0.10f, 0.11f, 0.12f));
        AddPart(PrimitiveType.Cube, "Unknown Dark End Cap B", new Vector3(0.32f, 0.01f, 0f), Quaternion.identity, new Vector3(0.035f, 0.20f, 0.36f), new Color(0.10f, 0.11f, 0.12f));
        AddPart(PrimitiveType.Cube, "Unknown Warning Label", new Vector3(0f, 0.105f, -0.04f), Quaternion.identity, new Vector3(0.22f, 0.012f, 0.13f), new Color(0.96f, 0.74f, 0.18f));
        AddPart(PrimitiveType.Cylinder, "Unknown Top Button", new Vector3(0f, 0.15f, 0.09f), Quaternion.identity, new Vector3(0.055f, 0.025f, 0.055f), new Color(0.20f, 0.21f, 0.24f));
    }

    void AddCylindricalPack(Color bodyColor)
    {
        Color wrapperColor = Color.Lerp(bodyColor, new Color(0.10f, 0.30f, 0.62f), 0.45f);
        AddPart(PrimitiveType.Cylinder, "Single Cylindrical Cell Wrapper", Vector3.zero, Quaternion.Euler(0f, 0f, 90f), new Vector3(0.145f, 0.48f, 0.145f), wrapperColor);
        AddPart(PrimitiveType.Cylinder, "Positive Metal Cap", new Vector3(0.50f, 0f, 0f), Quaternion.Euler(0f, 0f, 90f), new Vector3(0.148f, 0.035f, 0.148f), new Color(0.86f, 0.88f, 0.90f));
        AddPart(PrimitiveType.Cylinder, "Negative Metal Cap", new Vector3(-0.50f, 0f, 0f), Quaternion.Euler(0f, 0f, 90f), new Vector3(0.148f, 0.035f, 0.148f), new Color(0.54f, 0.56f, 0.60f));
        AddPart(PrimitiveType.Cylinder, "Positive Button Terminal", new Vector3(0.55f, 0f, 0f), Quaternion.Euler(0f, 0f, 90f), new Vector3(0.070f, 0.020f, 0.070f), new Color(0.98f, 0.78f, 0.32f));
        AddPart(PrimitiveType.Cube, "Cylindrical Label Band", new Vector3(0.04f, 0.148f, 0f), Quaternion.identity, new Vector3(0.36f, 0.018f, 0.16f), new Color(0.94f, 0.94f, 0.88f));
        AddPart(PrimitiveType.Cube, "Cylindrical Polarity Stripe", new Vector3(0.28f, 0.153f, 0f), Quaternion.identity, new Vector3(0.075f, 0.020f, 0.17f), new Color(0.96f, 0.70f, 0.20f));
    }

    void AddPouchCell(Color bodyColor)
    {
        Color foil = Color.Lerp(new Color(0.78f, 0.82f, 0.86f), bodyColor, 0.35f);
        AddPart(PrimitiveType.Cube, "Pouch Foil Envelope", Vector3.zero, Quaternion.identity, new Vector3(0.86f, 0.045f, 0.50f), foil);
        AddPart(PrimitiveType.Cube, "Pouch Soft Swollen Center", new Vector3(0f, 0.045f, -0.01f), Quaternion.identity, new Vector3(0.68f, 0.045f, 0.34f), Color.Lerp(foil, Color.white, 0.14f));
        AddPart(PrimitiveType.Cube, "Pouch Left Heat Seal", new Vector3(-0.45f, 0.062f, 0f), Quaternion.identity, new Vector3(0.035f, 0.020f, 0.52f), new Color(0.64f, 0.69f, 0.76f));
        AddPart(PrimitiveType.Cube, "Pouch Right Heat Seal", new Vector3(0.45f, 0.062f, 0f), Quaternion.identity, new Vector3(0.035f, 0.020f, 0.52f), new Color(0.64f, 0.69f, 0.76f));
        AddPart(PrimitiveType.Cube, "Pouch Top Heat Seal", new Vector3(0f, 0.066f, 0.265f), Quaternion.identity, new Vector3(0.84f, 0.020f, 0.035f), new Color(0.88f, 0.92f, 0.96f));
        AddPart(PrimitiveType.Cube, "Pouch Positive Foil Tab", new Vector3(-0.18f, 0.085f, 0.38f), Quaternion.identity, new Vector3(0.16f, 0.018f, 0.16f), new Color(0.96f, 0.73f, 0.28f));
        AddPart(PrimitiveType.Cube, "Pouch Negative Foil Tab", new Vector3(0.18f, 0.085f, 0.38f), Quaternion.identity, new Vector3(0.16f, 0.018f, 0.16f), new Color(0.50f, 0.54f, 0.58f));
        AddPart(PrimitiveType.Cube, "Pouch Printed Label", new Vector3(0.16f, 0.091f, -0.08f), Quaternion.identity, new Vector3(0.25f, 0.012f, 0.14f), new Color(0.10f, 0.12f, 0.15f));
    }

    void AddPrismaticModule(Color bodyColor)
    {
        Color caseColor = Color.Lerp(bodyColor, new Color(0.50f, 0.56f, 0.62f), 0.45f);
        AddPart(PrimitiveType.Cube, "Prismatic Rigid Can", Vector3.zero, Quaternion.identity, new Vector3(0.52f, 0.40f, 0.34f), caseColor);
        AddPart(PrimitiveType.Cube, "Prismatic Top Cover Plate", new Vector3(0f, 0.225f, 0f), Quaternion.identity, new Vector3(0.56f, 0.045f, 0.38f), Color.Lerp(caseColor, Color.white, 0.13f));
        AddPart(PrimitiveType.Cube, "Prismatic Bottom Foot", new Vector3(0f, -0.225f, 0f), Quaternion.identity, new Vector3(0.56f, 0.045f, 0.38f), new Color(0.22f, 0.24f, 0.27f));
        AddPart(PrimitiveType.Cube, "Prismatic Front Data Plate", new Vector3(0f, 0.02f, -0.183f), Quaternion.identity, new Vector3(0.34f, 0.20f, 0.014f), new Color(0.88f, 0.90f, 0.84f));
        AddPart(PrimitiveType.Cube, "Prismatic Vertical Rib A", new Vector3(-0.23f, 0.02f, -0.188f), Quaternion.identity, new Vector3(0.030f, 0.30f, 0.018f), new Color(0.30f, 0.33f, 0.37f));
        AddPart(PrimitiveType.Cube, "Prismatic Vertical Rib B", new Vector3(0.23f, 0.02f, -0.188f), Quaternion.identity, new Vector3(0.030f, 0.30f, 0.018f), new Color(0.30f, 0.33f, 0.37f));
        AddPart(PrimitiveType.Cylinder, "Prismatic Positive Bolt Terminal", new Vector3(-0.15f, 0.285f, 0.08f), Quaternion.identity, new Vector3(0.060f, 0.050f, 0.060f), new Color(0.96f, 0.73f, 0.24f));
        AddPart(PrimitiveType.Cylinder, "Prismatic Negative Bolt Terminal", new Vector3(0.15f, 0.285f, 0.08f), Quaternion.identity, new Vector3(0.060f, 0.050f, 0.060f), new Color(0.44f, 0.47f, 0.52f));
        AddPart(PrimitiveType.Cube, "Prismatic Warning Stripe", new Vector3(0f, 0.15f, -0.198f), Quaternion.identity, new Vector3(0.24f, 0.045f, 0.014f), new Color(0.94f, 0.66f, 0.18f));
    }

    GameObject AddPart(PrimitiveType primitiveType, string partName, Vector3 localPosition, Quaternion localRotation, Vector3 localScale, Color color)
    {
        GameObject part = GameObject.CreatePrimitive(primitiveType);
        part.name = partName;
        part.transform.SetParent(visualRoot, false);
        part.transform.localPosition = localPosition;
        part.transform.localRotation = localRotation;
        part.transform.localScale = localScale;

        Renderer renderer = part.GetComponent<Renderer>();
        if (renderer != null)
        {
            Material material = new Material(Shader.Find("Standard"));
            material.color = color;
            renderer.sharedMaterial = material;
        }

        Collider collider = part.GetComponent<Collider>();
        if (collider != null)
        {
            collider.isTrigger = true;
        }

        return part;
    }
}
