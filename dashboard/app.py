"""Project: Circular Battery Decision Twin
Developer: Amin Zoroufi
Contact: YOUR_EMAIL
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = PROJECT_ROOT / "outputs" / "inspection_log.csv"
PASSPORT_PATH = PROJECT_ROOT / "outputs" / "battery_passports.json"
LATEST_DECISION_PATH = PROJECT_ROOT / "outputs" / "latest_decision.json"


st.set_page_config(page_title="Circular Battery Decision Twin", layout="wide")


@st.cache_data(ttl=3)
def load_log() -> pd.DataFrame:
    if not LOG_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(LOG_PATH)
    if df.empty or "battery_id" not in df.columns:
        return pd.DataFrame()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


@st.cache_data(ttl=3)
def load_passports() -> dict:
    if not PASSPORT_PATH.exists():
        return {}
    return json.loads(PASSPORT_PATH.read_text(encoding="utf-8") or "{}")


@st.cache_data(ttl=3)
def load_latest_decision() -> dict:
    if not LATEST_DECISION_PATH.exists():
        return {}
    return json.loads(LATEST_DECISION_PATH.read_text(encoding="utf-8") or "{}")


def count_decision(df: pd.DataFrame, decision: str) -> int:
    if df.empty or "final_decision" not in df.columns:
        return 0
    return int((df["final_decision"] == decision).sum())


def metric_row(df: pd.DataFrame) -> None:
    total = len(df)
    manual_review = int(df.get("manual_review_required", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()) if total else 0
    overrides = int(df.get("operator_decision", pd.Series(dtype=str)).notna().sum()) if total else 0
    avg_soh = float(df["soh"].mean()) if total and "soh" in df else 0
    avg_risk = float(df["risk_score"].mean()) if total and "risk_score" in df else 0
    avg_time = float(df["processing_time_ms"].mean()) if total and "processing_time_ms" in df else 0

    cols = st.columns(9)
    cols[0].metric("Inspected", total)
    cols[1].metric("Reuse", count_decision(df, "reuse"))
    cols[2].metric("Remanufacture", count_decision(df, "remanufacture"))
    cols[3].metric("Recycle", count_decision(df, "recycle"))
    cols[4].metric("Quarantine", count_decision(df, "quarantine"))
    cols[5].metric("Manual Review", manual_review)
    cols[6].metric("Avg SOH", f"{avg_soh:.2f}")
    cols[7].metric("Avg Risk", f"{avg_risk:.1f}")
    cols[8].metric("Avg ms", f"{avg_time:.1f}")
    st.caption(f"Operator overrides: {overrides}")


def empty_state() -> None:
    st.info("No inspections yet. Start the FastAPI backend, run an inspection from Unity or curl, then refresh this dashboard.")


def decision_color(decision: str | None) -> str:
    palette = {
        "reuse": "#219e55",
        "remanufacture": "#2b6fe3",
        "recycle": "#e99b28",
        "quarantine": "#cc2e2a",
        "manual_review": "#cc2e2a",
    }
    return palette.get(str(decision or "").lower(), "#7a7f89")


def latest_inspection_panel(latest: dict) -> None:
    st.subheader("AI Inspection Panel")
    if not latest:
        st.info("Waiting for the first inspection.")
        return

    decision = latest.get("decision_category") or latest.get("final_decision") or "unknown"
    shape = latest.get("detected_shape") or latest.get("detected_type") or "unknown"
    color = decision_color(decision)
    st.markdown(
        f"""
        <div style="border-left: 8px solid {color}; padding: 0.75rem 1rem; background: #1118270d; border-radius: 8px;">
          <div style="font-size: 0.85rem; color: #6b7280;">Lifecycle decision</div>
          <div style="font-size: 1.8rem; font-weight: 700; color: {color}; text-transform: uppercase;">{decision}</div>
          <div style="color: #374151;">Detected physical shape: <b>{shape}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    image_path = latest.get("received_image_path")
    cols = st.columns([1.1, 1.4, 1.5])
    if image_path:
        resolved_image_path = PROJECT_ROOT / image_path
        if resolved_image_path.exists():
            cols[0].image(str(resolved_image_path), caption=latest.get("received_image_filename", "latest captured image"))
        else:
            cols[0].warning(f"Image file missing: {image_path}")
    else:
        cols[0].info("No captured image path yet.")

    cols[1].metric("Confidence", f"{float(latest.get('confidence') or 0):.2f}")
    cols[1].metric("Uncertainty", f"{float(latest.get('uncertainty') or 0):.2f}")
    cols[1].metric("Risk score", str(latest.get("risk_score", "-")))
    cols[1].caption(f"Status: latest inspection at {latest.get('timestamp', '-')}")

    features = latest.get("features") or {}
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except json.JSONDecodeError:
            features = {}
    cols[2].write("Reasoning / Explanation")
    cols[2].write(latest.get("reason", "No explanation provided."))
    cols[2].write("Data used")
    cols[2].json(features or {
        "state_of_health": latest.get("soh"),
        "cycle_count": latest.get("cycle_count"),
        "temperature_c": latest.get("temperature_c"),
        "risk_level": latest.get("risk_level"),
    })


st.title("Circular Battery Decision Twin")
st.caption("Prototype dashboard for battery recovery decisions, overrides, and digital product passports.")

auto_refresh = st.sidebar.toggle("Auto-refresh", value=True)
refresh_seconds = st.sidebar.slider("Refresh seconds", 2, 15, 5)
if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

df = load_log()
passports = load_passports()
latest_decision = load_latest_decision()

tabs = st.tabs(["Overview", "Decision Distribution", "Process Performance", "Passport Viewer", "Grant Impact Simulator"])

with tabs[0]:
    st.subheader("Overview")
    if df.empty:
        empty_state()
    else:
        metric_row(df)
        latest_inspection_panel(latest_decision)
        st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Decision Distribution")
    if df.empty:
        empty_state()
    else:
        left, right = st.columns(2)
        decision_counts = df["final_decision"].fillna("unknown").value_counts().reset_index()
        decision_counts.columns = ["final_decision", "count"]
        left.plotly_chart(px.pie(decision_counts, names="final_decision", values="count", hole=0.35), use_container_width=True)
        left.plotly_chart(px.bar(decision_counts, x="final_decision", y="count"), use_container_width=True)

        risk_counts = df["risk_level"].fillna("unknown").value_counts().reset_index()
        risk_counts.columns = ["risk_level", "count"]
        type_counts = df["detected_type"].fillna("unknown").value_counts().reset_index()
        type_counts.columns = ["detected_type", "count"]
        right.plotly_chart(px.bar(risk_counts, x="risk_level", y="count", color="risk_level"), use_container_width=True)
        right.plotly_chart(px.bar(type_counts, x="detected_type", y="count", color="detected_type"), use_container_width=True)

with tabs[2]:
    st.subheader("Process Performance")
    if df.empty:
        empty_state()
    else:
        ordered = df.sort_values("timestamp")
        if "processing_time_ms" in ordered:
            st.plotly_chart(px.line(ordered, x="timestamp", y="processing_time_ms", markers=True), use_container_width=True)

        col_a, col_b, col_c = st.columns(3)
        if "timestamp" in ordered and ordered["timestamp"].notna().sum() > 1:
            elapsed_hours = max((ordered["timestamp"].max() - ordered["timestamp"].min()).total_seconds() / 3600, 1 / 60)
            throughput = len(ordered) / elapsed_hours
        else:
            throughput = len(ordered)
        col_a.metric("Throughput estimate", f"{throughput:.1f} batteries/hour")

        policy_counts = ordered.groupby(["policy_mode", "final_decision"]).size().reset_index(name="count")
        st.plotly_chart(px.bar(policy_counts, x="policy_mode", y="count", color="final_decision", barmode="group"), use_container_width=True)

        override_df = ordered[ordered["operator_decision"].notna()]
        col_b.metric("Override count", len(override_df))
        col_c.metric("Latest decision", str(ordered.iloc[-1].get("final_decision", "unknown")))

with tabs[3]:
    st.subheader("Passport Viewer")
    if not passports:
        st.info("No passports generated yet.")
    else:
        selected = st.selectbox("Battery ID", sorted(passports.keys()))
        st.json(passports[selected])

with tabs[4]:
    st.subheader("Grant Impact Simulator")
    st.caption("Prototype estimates based on observed route ratios. Replace assumptions with partner pilot data before investment decisions.")
    annual_volume = st.number_input("Annual battery volume", min_value=0, value=25000, step=1000)
    reuse_value = st.number_input("Estimated reuse value per battery (AED)", min_value=0.0, value=180.0, step=10.0)
    recycling_value = st.number_input("Estimated recycling value per battery (AED)", min_value=0.0, value=45.0, step=5.0)
    quarantine_cost = st.number_input("Estimated quarantine handling cost per case (AED)", min_value=0.0, value=35.0, step=5.0)

    if df.empty:
        ratios = {"reuse": 0.30, "remanufacture": 0.35, "recycle": 0.25, "quarantine": 0.10}
    else:
        counts = df["final_decision"].value_counts(normalize=True).to_dict()
        ratios = {key: float(counts.get(key, 0)) for key in ["reuse", "remanufacture", "recycle", "quarantine"]}

    reuse_count = int(annual_volume * ratios["reuse"])
    reman_count = int(annual_volume * ratios["remanufacture"])
    recycle_count = int(annual_volume * ratios["recycle"])
    quarantine_count = int(annual_volume * ratios["quarantine"])
    recovered_value = reuse_count * reuse_value + reman_count * reuse_value * 0.65 + recycle_count * recycling_value - quarantine_count * quarantine_cost

    cols = st.columns(5)
    cols[0].metric("Reusable", reuse_count)
    cols[1].metric("Remanufacturable", reman_count)
    cols[2].metric("Recycled", recycle_count)
    cols[3].metric("Quarantine", quarantine_count)
    cols[4].metric("Estimated value recovered", f"AED {recovered_value:,.0f}")
