"""
Vitals Display Component
Displays patient vital signs with visual indicators
Supports real-time updates and threshold alerts
"""
import streamlit as st
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class VitalThresholds:
    """Normal ranges for vital signs."""
    # Heart Rate (BPM)
    heart_rate_low: int = 60
    heart_rate_high: int = 100
    heart_rate_critical_low: int = 40
    heart_rate_critical_high: int = 120
    
    # Blood Pressure Systolic (mmHg)
    bp_systolic_low: int = 90
    bp_systolic_high: int = 140
    bp_systolic_critical_low: int = 70
    bp_systolic_critical_high: int = 180
    
    # Blood Pressure Diastolic (mmHg)
    bp_diastolic_low: int = 60
    bp_diastolic_high: int = 90
    bp_diastolic_critical_low: int = 50
    bp_diastolic_critical_high: int = 110
    
    # Oxygen Saturation (%)
    spo2_low: int = 95
    spo2_critical_low: int = 90
    
    # Temperature (°C)
    temp_low: float = 36.0
    temp_high: float = 37.5
    temp_critical_low: float = 35.0
    temp_critical_high: float = 39.0
    
    # Respiratory Rate (breaths/min)
    resp_rate_low: int = 12
    resp_rate_high: int = 20
    resp_rate_critical_low: int = 8
    resp_rate_critical_high: int = 30


# Default thresholds
DEFAULT_THRESHOLDS = VitalThresholds()


def get_vital_status(value: float, low: float, high: float, 
                     critical_low: float, critical_high: float) -> Tuple[str, str]:
    """
    Determine vital sign status and color.
    
    Returns:
        Tuple of (status, color)
    """
    if value <= critical_low or value >= critical_high:
        return "Critical", "#dc2626"  # Red
    elif value < low or value > high:
        return "Warning", "#f59e0b"  # Amber
    else:
        return "Normal", "#22c55e"  # Green


def render_vital_gauge(
    label: str,
    value: float,
    unit: str,
    low: float,
    high: float,
    critical_low: float,
    critical_high: float,
    icon: str = "📊",
    show_history: bool = False,
    history: Optional[List[float]] = None
):
    """
    Render a vital sign gauge with status indicator.
    
    Args:
        label: Vital sign name
        value: Current value
        unit: Unit of measurement
        low: Normal low threshold
        high: Normal high threshold
        critical_low: Critical low threshold
        critical_high: Critical high threshold
        icon: Icon to display
        show_history: Whether to show mini sparkline
        history: Historical values for sparkline
    """
    status, color = get_vital_status(value, low, high, critical_low, critical_high)
    
    # Calculate percentage for visual bar (between critical low and high)
    range_span = critical_high - critical_low
    percentage = ((value - critical_low) / range_span) * 100
    percentage = max(0, min(100, percentage))
    
    # Render the gauge
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            border: 1px solid {color}40;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #94a3b8; font-size: 0.85rem;">{icon} {label}</span>
                <span style="
                    background: {color}20;
                    color: {color};
                    padding: 2px 8px;
                    border-radius: 8px;
                    font-size: 0.7rem;
                    font-weight: bold;
                ">{status}</span>
            </div>
            <div style="display: flex; align-items: baseline; gap: 4px;">
                <span style="color: white; font-size: 1.8rem; font-weight: bold;">{value:.1f}</span>
                <span style="color: #64748b; font-size: 0.9rem;">{unit}</span>
            </div>
            <div style="
                background: #334155;
                border-radius: 4px;
                height: 4px;
                margin-top: 8px;
                overflow: hidden;
            ">
                <div style="
                    background: {color};
                    width: {percentage}%;
                    height: 100%;
                    border-radius: 4px;
                "></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px;">
                <span style="color: #64748b; font-size: 0.7rem;">{critical_low}</span>
                <span style="color: #64748b; font-size: 0.7rem;">Normal: {low}-{high}</span>
                <span style="color: #64748b; font-size: 0.7rem;">{critical_high}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_vitals_dashboard(
    vitals: Dict,
    patient_name: Optional[str] = None,
    last_updated: Optional[datetime] = None,
    thresholds: VitalThresholds = DEFAULT_THRESHOLDS,
    compact: bool = False
):
    """
    Render a complete vitals dashboard.
    
    Args:
        vitals: Dictionary with vital sign values
        patient_name: Patient name to display
        last_updated: When vitals were last updated
        thresholds: Threshold configuration
        compact: Whether to use compact layout
    """
    # Header
    if patient_name:
        st.markdown(f"### 👤 {patient_name}")
    
    if last_updated:
        time_str = last_updated.strftime("%I:%M %p")
        st.caption(f"🕐 Last updated: {time_str}")
    
    # Check for critical vitals
    has_critical = False
    critical_vitals = []
    
    # Heart Rate
    hr = vitals.get("heart_rate", vitals.get("hr", 75))
    if hr <= thresholds.heart_rate_critical_low or hr >= thresholds.heart_rate_critical_high:
        has_critical = True
        critical_vitals.append(f"Heart Rate: {hr} BPM")
    
    # SpO2
    spo2 = vitals.get("spo2", vitals.get("oxygen", 98))
    if spo2 <= thresholds.spo2_critical_low:
        has_critical = True
        critical_vitals.append(f"SpO2: {spo2}%")
    
    # Show critical alert
    if has_critical:
        st.error(f"🚨 **CRITICAL VITALS DETECTED!** {', '.join(critical_vitals)}")
    
    # Render vitals in grid
    if compact:
        cols = st.columns(3)
    else:
        cols = st.columns(2)
    
    col_idx = 0
    
    # Heart Rate
    with cols[col_idx % len(cols)]:
        render_vital_gauge(
            label="Heart Rate",
            value=hr,
            unit="BPM",
            low=thresholds.heart_rate_low,
            high=thresholds.heart_rate_high,
            critical_low=thresholds.heart_rate_critical_low,
            critical_high=thresholds.heart_rate_critical_high,
            icon="❤️"
        )
    col_idx += 1
    
    # Blood Pressure
    bp_sys = vitals.get("bp_systolic", vitals.get("bp", {}).get("systolic", 120))
    bp_dia = vitals.get("bp_diastolic", vitals.get("bp", {}).get("diastolic", 80))
    
    with cols[col_idx % len(cols)]:
        # Custom BP display
        bp_status, bp_color = get_vital_status(
            bp_sys, 
            thresholds.bp_systolic_low, 
            thresholds.bp_systolic_high,
            thresholds.bp_systolic_critical_low,
            thresholds.bp_systolic_critical_high
        )
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border-radius: 12px;
                padding: 16px;
                margin: 8px 0;
                border: 1px solid {bp_color}40;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 0.85rem;">🩺 Blood Pressure</span>
                    <span style="
                        background: {bp_color}20;
                        color: {bp_color};
                        padding: 2px 8px;
                        border-radius: 8px;
                        font-size: 0.7rem;
                        font-weight: bold;
                    ">{bp_status}</span>
                </div>
                <div style="display: flex; align-items: baseline; gap: 4px;">
                    <span style="color: white; font-size: 1.8rem; font-weight: bold;">{bp_sys}/{bp_dia}</span>
                    <span style="color: #64748b; font-size: 0.9rem;">mmHg</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    col_idx += 1
    
    # SpO2
    with cols[col_idx % len(cols)]:
        render_vital_gauge(
            label="Oxygen Saturation",
            value=spo2,
            unit="%",
            low=thresholds.spo2_low,
            high=100,
            critical_low=thresholds.spo2_critical_low,
            critical_high=100,
            icon="🫁"
        )
    col_idx += 1
    
    # Temperature
    temp = vitals.get("temperature", vitals.get("temp", 36.8))
    with cols[col_idx % len(cols)]:
        render_vital_gauge(
            label="Temperature",
            value=temp,
            unit="°C",
            low=thresholds.temp_low,
            high=thresholds.temp_high,
            critical_low=thresholds.temp_critical_low,
            critical_high=thresholds.temp_critical_high,
            icon="🌡️"
        )
    col_idx += 1
    
    # Respiratory Rate
    resp = vitals.get("respiratory_rate", vitals.get("resp", 16))
    with cols[col_idx % len(cols)]:
        render_vital_gauge(
            label="Respiratory Rate",
            value=resp,
            unit="breaths/min",
            low=thresholds.resp_rate_low,
            high=thresholds.resp_rate_high,
            critical_low=thresholds.resp_rate_critical_low,
            critical_high=thresholds.resp_rate_critical_high,
            icon="🌬️"
        )


def render_vitals_mini(vitals: Dict):
    """
    Render a compact vitals summary (for list views).
    """
    hr = vitals.get("heart_rate", vitals.get("hr", 75))
    spo2 = vitals.get("spo2", vitals.get("oxygen", 98))
    bp_sys = vitals.get("bp_systolic", vitals.get("bp", {}).get("systolic", 120))
    bp_dia = vitals.get("bp_diastolic", vitals.get("bp", {}).get("diastolic", 80))
    
    # Get status colors
    _, hr_color = get_vital_status(hr, 60, 100, 40, 120)
    _, spo2_color = get_vital_status(spo2, 95, 100, 90, 100)
    _, bp_color = get_vital_status(bp_sys, 90, 140, 70, 180)
    
    st.markdown(f"""
        <div style="display: flex; gap: 16px; flex-wrap: wrap;">
            <span style="color: {hr_color};">❤️ {hr} BPM</span>
            <span style="color: {spo2_color};">🫁 {spo2}%</span>
            <span style="color: {bp_color};">🩺 {bp_sys}/{bp_dia}</span>
        </div>
    """, unsafe_allow_html=True)


# Demo usage
if __name__ == "__main__":
    st.set_page_config(page_title="Vitals Display Demo", layout="wide")
    st.title("Vitals Display Component Demo")
    
    # Sample vitals
    sample_vitals = {
        "heart_rate": 78,
        "spo2": 97,
        "bp_systolic": 125,
        "bp_diastolic": 82,
        "temperature": 37.1,
        "respiratory_rate": 18
    }
    
    render_vitals_dashboard(
        vitals=sample_vitals,
        patient_name="Ramesh Kumar",
        last_updated=datetime.now()
    )
    
    st.markdown("---")
    st.subheader("Critical Vitals Example")
    
    critical_vitals = {
        "heart_rate": 135,
        "spo2": 88,
        "bp_systolic": 185,
        "bp_diastolic": 110,
        "temperature": 39.5,
        "respiratory_rate": 28
    }
    
    render_vitals_dashboard(
        vitals=critical_vitals,
        patient_name="Critical Patient",
        last_updated=datetime.now()
    )
