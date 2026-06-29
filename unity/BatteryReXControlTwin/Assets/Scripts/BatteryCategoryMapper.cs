using System;
using UnityEngine;

public enum BatteryShape
{
    Unknown,
    Cylindrical,
    Pouch,
    Prismatic
}

public enum DecisionCategory
{
    Reuse,
    Remanufacture,
    Recycle,
    Quarantine
}

public static class BatteryCategoryMapper
{
    public const string Cylindrical = "cylindrical";
    public const string Pouch = "pouch";
    public const string Prismatic = "prismatic";
    public const string Unknown = "unknown";
    public const string Reuse = "reuse";
    public const string Remanufacture = "remanufacture";
    public const string Recycle = "recycle";
    public const string Quarantine = "quarantine";

    public static string Normalize(string label)
    {
        return ShapeKey(NormalizeShape(label));
    }

    public static BatteryShape NormalizeShape(string label)
    {
        string value = (label ?? string.Empty).Trim().ToLowerInvariant();
        value = value.Replace("-", "_").Replace(" ", "_");

        if (value.Contains("cyl") || value.Contains("round") || value.Contains("18650") || value.Contains("21700"))
        {
            return BatteryShape.Cylindrical;
        }

        if (value.Contains("pouch") || value.Contains("soft") || value.Contains("flat"))
        {
            return BatteryShape.Pouch;
        }

        if (value.Contains("prismatic") || value.Contains("prism") || value.Contains("block") || value.Contains("rectangular"))
        {
            return BatteryShape.Prismatic;
        }

        return BatteryShape.Unknown;
    }

    public static DecisionCategory NormalizeDecision(string label)
    {
        string value = (label ?? string.Empty).Trim().ToLowerInvariant();
        value = value.Replace("-", "_").Replace(" ", "_");

        if (value.Contains("reuse"))
        {
            return DecisionCategory.Reuse;
        }

        if (value.Contains("reman") || value.Contains("repair") || value.Contains("refurb"))
        {
            return DecisionCategory.Remanufacture;
        }

        if (value.Contains("recycle"))
        {
            return DecisionCategory.Recycle;
        }

        if (value.Contains("quarantine") || value.Contains("reject") || value.Contains("manual_review") || value.Contains("unknown"))
        {
            return DecisionCategory.Quarantine;
        }

        return DecisionCategory.Quarantine;
    }

    public static BatteryShape ResolveShape(BatteryInspectionResult result, float confidenceThreshold)
    {
        if (result == null)
        {
            return BatteryShape.Unknown;
        }

        BatteryShape shape = NormalizeShape(FirstNonEmpty(result.detected_shape, result.detected_type, result.label, result.category));
        if (shape == BatteryShape.Unknown)
        {
            return BatteryShape.Unknown;
        }

        if (result.confidence > 0f && result.confidence < confidenceThreshold)
        {
            return BatteryShape.Unknown;
        }

        return shape;
    }

    public static DecisionCategory ResolveDecision(BatteryInspectionResult result)
    {
        if (result == null)
        {
            return DecisionCategory.Quarantine;
        }

        return NormalizeDecision(FirstNonEmpty(result.decision_category, result.final_decision, result.ai_decision, result.target_bin));
    }

    public static Color ShapeNeutralColor(BatteryShape shape)
    {
        switch (shape)
        {
            case BatteryShape.Cylindrical:
                return new Color(0.74f, 0.78f, 0.82f);
            case BatteryShape.Pouch:
                return new Color(0.70f, 0.76f, 0.84f);
            case BatteryShape.Prismatic:
                return new Color(0.64f, 0.70f, 0.76f);
            default:
                return new Color(0.62f, 0.64f, 0.68f);
        }
    }

    public static Color DecisionColor(DecisionCategory decision)
    {
        switch (decision)
        {
            case DecisionCategory.Reuse:
                return new Color(0.13f, 0.62f, 0.32f);
            case DecisionCategory.Remanufacture:
                return new Color(0.16f, 0.42f, 0.86f);
            case DecisionCategory.Recycle:
                return new Color(0.92f, 0.62f, 0.16f);
            case DecisionCategory.Quarantine:
                return new Color(0.80f, 0.18f, 0.16f);
            default:
                return new Color(0.62f, 0.64f, 0.68f);
        }
    }

    public static string ShapeKey(BatteryShape shape)
    {
        switch (shape)
        {
            case BatteryShape.Cylindrical: return Cylindrical;
            case BatteryShape.Pouch: return Pouch;
            case BatteryShape.Prismatic: return Prismatic;
            default:
                return Unknown;
        }
    }

    public static string DecisionKey(DecisionCategory decision)
    {
        switch (decision)
        {
            case DecisionCategory.Reuse: return Reuse;
            case DecisionCategory.Remanufacture: return Remanufacture;
            case DecisionCategory.Recycle: return Recycle;
            case DecisionCategory.Quarantine: return Quarantine;
            default: return Quarantine;
        }
    }

    public static string ShapeLabel(BatteryShape shape)
    {
        switch (shape)
        {
            case BatteryShape.Cylindrical: return "CYLINDRICAL";
            case BatteryShape.Pouch: return "POUCH";
            case BatteryShape.Prismatic: return "PRISMATIC";
            default: return "UNKNOWN";
        }
    }

    public static string DecisionLabel(DecisionCategory decision)
    {
        switch (decision)
        {
            case DecisionCategory.Reuse: return "REUSE";
            case DecisionCategory.Remanufacture: return "REMANUFACTURE";
            case DecisionCategory.Recycle: return "RECYCLE";
            case DecisionCategory.Quarantine: return "QUARANTINE";
            default: return "QUARANTINE";
        }
    }

    public static string DecisionBinKey(DecisionCategory decision)
    {
        return DecisionKey(decision) + "_bin";
    }

    public static string LabelFor(string category)
    {
        return ShapeLabel(NormalizeShape(category));
    }

    public static Color ColorFor(string decisionOrShape)
    {
        return DecisionColor(NormalizeDecision(decisionOrShape));
    }

    public static string BinKeyFor(string decisionOrShape)
    {
        return DecisionBinKey(NormalizeDecision(decisionOrShape));
    }

    static string FirstNonEmpty(params string[] values)
    {
        foreach (string value in values)
        {
            if (!string.IsNullOrWhiteSpace(value))
            {
                return value;
            }
        }

        return string.Empty;
    }
}
