from __future__ import annotations


def risk_level_from_score(risk_score: int) -> str:
    if risk_score <= 30:
        return "low"
    if risk_score <= 60:
        return "medium"
    if risk_score <= 80:
        return "high"
    return "critical"


def make_decision(
    *,
    detected_type: str,
    confidence: float,
    soh: float,
    temperature_c: float,
    cycle_count: int,
    internal_resistance_mohm: float,
    policy_mode: str,
    confidence_threshold: float,
    reuse_soh_threshold: float,
    robot_mode: str,
) -> dict:
    risk_score = 0

    if confidence < confidence_threshold:
        risk_score += 30
    if soh < 0.5:
        risk_score += 35
    elif 0.5 <= soh < 0.65:
        risk_score += 20
    if temperature_c > 50:
        risk_score += 40
    elif 40 <= temperature_c <= 50:
        risk_score += 20
    if cycle_count > 900:
        risk_score += 20
    elif 600 <= cycle_count <= 900:
        risk_score += 10
    if internal_resistance_mohm > 150:
        risk_score += 20
    if detected_type == "unknown":
        risk_score += 30

    if policy_mode == "safety_first":
        risk_score += 10
    elif policy_mode == "recovery_maximization":
        risk_score = max(0, risk_score - 10)

    risk_score = min(100, int(risk_score))
    risk_level = risk_level_from_score(risk_score)
    manual_review_required = False

    if robot_mode == "emergency_stop":
        ai_decision = "paused"
        target_bin = "none"
        reason = "Emergency stop active."
    elif confidence < confidence_threshold:
        ai_decision = "manual_review"
        target_bin = "quarantine_bin"
        manual_review_required = True
        reason = "Classifier confidence is below the operator threshold."
    elif risk_level == "critical":
        ai_decision = "quarantine"
        target_bin = "quarantine_bin"
        reason = "Critical risk score requires quarantine and manual review."
    elif policy_mode == "safety_first" and risk_score > 60:
        ai_decision = "quarantine"
        target_bin = "quarantine_bin"
        reason = "Safety-first policy quarantines high-risk batteries."
    elif soh >= reuse_soh_threshold and risk_score <= 30:
        ai_decision = "reuse"
        target_bin = "reuse_bin"
        reason = "High SOH and low risk meet the reuse policy threshold."
    elif soh >= 0.60 and risk_score <= 60:
        ai_decision = "remanufacture"
        target_bin = "remanufacture_bin"
        reason = "Moderate SOH with acceptable risk supports remanufacturing."
    elif policy_mode == "recovery_maximization" and soh >= 0.55 and risk_score <= 70:
        ai_decision = "remanufacture"
        target_bin = "remanufacture_bin"
        reason = "Recovery maximization keeps this battery in a remanufacturing path."
    elif soh < 0.60:
        ai_decision = "recycle"
        target_bin = "recycle_bin"
        reason = "Low SOH routes the battery to recycling."
    else:
        ai_decision = "quarantine"
        target_bin = "quarantine_bin"
        reason = "Borderline battery state requires manual review."

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "ai_decision": ai_decision,
        "final_decision": ai_decision,
        "target_bin": target_bin,
        "manual_review_required": manual_review_required,
        "reason": reason,
    }
