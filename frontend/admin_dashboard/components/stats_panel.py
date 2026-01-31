"""
VitalFlow AI - Stats Panel Component
Real-time statistics display with metrics and progress bars
"""

import streamlit as st
from typing import Dict, Any


def render_stats_panel(stats: Dict[str, Any]):
    """
    Render the main statistics panel with metrics and progress bars
    """
    st.markdown("### 📊 Hospital Statistics")
    
    # Row 1: Main Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🛏️ Total Beds",
            value=stats["total_beds"],
            delta=None
        )
    
    with col2:
        st.metric(
            label="👥 Occupied",
            value=stats["occupied_beds"],
            delta=f"+{stats.get('admissions_last_hour', 0)} this hour",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="✅ Available",
            value=stats["available_beds"],
            delta=f"-{stats.get('discharges_last_hour', 0)} discharged",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            label="👨‍⚕️ Staff On-Duty",
            value=f"{stats['staff_on_duty']}/{stats['total_staff']}",
            delta=None
        )
    
    st.divider()
    
    # Row 2: Capacity Bars
    st.markdown("#### Bed Capacity by Type")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        icu_occupied = stats["icu_total"] - stats["icu_available"]
        icu_pct = (icu_occupied / stats["icu_total"]) * 100 if stats["icu_total"] > 0 else 0
        st.markdown(f"**🚨 ICU Beds**")
        st.progress(icu_pct / 100, text=f"{icu_occupied}/{stats['icu_total']} occupied ({icu_pct:.0f}%)")
        if icu_pct > 85:
            st.warning(f"⚠️ Only {stats['icu_available']} ICU beds available!")
    
    with col2:
        er_occupied = stats["emergency_total"] - stats["emergency_available"]
        er_pct = (er_occupied / stats["emergency_total"]) * 100 if stats["emergency_total"] > 0 else 0
        st.markdown(f"**🏥 Emergency Beds**")
        st.progress(er_pct / 100, text=f"{er_occupied}/{stats['emergency_total']} occupied ({er_pct:.0f}%)")
        if er_pct > 85:
            st.warning(f"⚠️ Only {stats['emergency_available']} ER beds available!")
    
    with col3:
        gen_occupied = stats["general_total"] - stats["general_available"]
        gen_pct = (gen_occupied / stats["general_total"]) * 100 if stats["general_total"] > 0 else 0
        st.markdown(f"**🛌 General Wards**")
        st.progress(gen_pct / 100, text=f"{gen_occupied}/{stats['general_total']} occupied ({gen_pct:.0f}%)")
    
    st.divider()
    
    # Row 3: Patient Status Overview
    st.markdown("#### Patient Status Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #FF4B4B 0%, #FF6B6B 100%); 
                        padding: 20px; border-radius: 10px; text-align: center;">
                <h2 style="color: white; margin: 0;">{stats['critical_patients']}</h2>
                <p style="color: white; margin: 0;">🔴 Critical</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #FFA500 0%, #FFB84D 100%); 
                        padding: 20px; border-radius: 10px; text-align: center;">
                <h2 style="color: white; margin: 0;">{stats['serious_patients']}</h2>
                <p style="color: white; margin: 0;">🟠 Serious</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #00CC66 0%, #00E676 100%); 
                        padding: 20px; border-radius: 10px; text-align: center;">
                <h2 style="color: white; margin: 0;">{stats['stable_patients']}</h2>
                <p style="color: white; margin: 0;">🟢 Stable</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #4DA6FF 0%, #64B5F6 100%); 
                        padding: 20px; border-radius: 10px; text-align: center;">
                <h2 style="color: white; margin: 0;">{stats['recovering_patients']}</h2>
                <p style="color: white; margin: 0;">🔵 Recovering</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_mini_stats(stats: Dict[str, Any]):
    """
    Render a compact stats view for sidebar
    """
    st.markdown("### Quick Stats")
    
    # Occupancy gauge
    total_pct = (stats["occupied_beds"] / stats["total_beds"]) * 100 if stats["total_beds"] > 0 else 0
    
    # Color based on capacity
    if total_pct > 90:
        color = "#FF4B4B"
        status = "CRITICAL"
    elif total_pct > 75:
        color = "#FFA500"
        status = "HIGH"
    else:
        color = "#00CC66"
        status = "NORMAL"
    
    st.markdown(
        f"""
        <div style="background: #1E1E1E; padding: 15px; border-radius: 10px; 
                    border-left: 4px solid {color};">
            <p style="margin: 0; color: #888;">Overall Capacity</p>
            <h2 style="margin: 5px 0; color: {color};">{total_pct:.1f}%</h2>
            <p style="margin: 0; color: {color}; font-weight: bold;">{status}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick metrics
    metrics = [
        ("🔴 Critical", stats["critical_patients"], "#FF4B4B"),
        ("🚨 ICU Free", stats["icu_available"], "#FF6B6B" if stats["icu_available"] < 3 else "#00CC66"),
        ("🏥 ER Free", stats["emergency_available"], "#FFA500" if stats["emergency_available"] < 3 else "#00CC66"),
        ("👨‍⚕️ Staff", f"{stats['staff_on_duty']}/{stats['total_staff']}", "#4DA6FF"),
    ]
    
    for label, value, color in metrics:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; 
                        padding: 8px 0; border-bottom: 1px solid #333;">
                <span>{label}</span>
                <span style="color: {color}; font-weight: bold;">{value}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_alerts_summary(stats: Dict[str, Any]):
    """
    Render critical alerts summary
    """
    alerts = []
    
    if stats["critical_patients"] > 5:
        alerts.append(("🚨", f"High number of critical patients: {stats['critical_patients']}", "error"))
    
    if stats["icu_available"] < 2:
        alerts.append(("⚠️", f"ICU capacity critical: Only {stats['icu_available']} beds available", "error"))
    
    if stats["emergency_available"] < 3:
        alerts.append(("⚠️", f"Emergency capacity low: {stats['emergency_available']} beds available", "warning"))
    
    icu_pct = ((stats["icu_total"] - stats["icu_available"]) / stats["icu_total"]) * 100 if stats["icu_total"] > 0 else 0
    if icu_pct > 90:
        alerts.append(("🔴", f"ICU at {icu_pct:.0f}% capacity - consider patient transfers", "error"))
    
    if alerts:
        st.markdown("### 🚨 Active Alerts")
        for icon, message, alert_type in alerts:
            if alert_type == "error":
                st.error(f"{icon} {message}")
            else:
                st.warning(f"{icon} {message}")
    else:
        st.success("✅ All systems operating normally")
