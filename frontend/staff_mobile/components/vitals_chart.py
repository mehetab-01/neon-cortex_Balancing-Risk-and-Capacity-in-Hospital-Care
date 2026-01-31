"""
VitalFlow AI - Vitals Chart Component
Displays patient vitals in a mobile-friendly chart
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import random


def render_vitals_chart(vitals_history: List[Dict], chart_type: str = "both"):
    """
    Render a mobile-optimized vitals chart
    
    Args:
        vitals_history: List of vitals readings with timestamp, spo2, heart_rate
        chart_type: "spo2", "heart_rate", or "both"
    """
    if not vitals_history:
        st.warning("No vitals data available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(vitals_history)
    
    # Chart styling
    st.markdown("""
    <style>
        .vitals-chart-container {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 15px;
            padding: 15px;
            margin: 10px 0;
        }
        .chart-title {
            color: #fff;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .vital-value {
            font-size: 32px;
            font-weight: bold;
            text-align: center;
        }
        .vital-label {
            font-size: 12px;
            color: #888;
            text-align: center;
        }
        .spo2-value { color: #00D4FF; }
        .hr-value { color: #FF6B6B; }
    </style>
    """, unsafe_allow_html=True)
    
    if chart_type in ["spo2", "both"]:
        st.markdown("#### 🫁 SpO2 (Blood Oxygen)")
        
        # Current value display
        current_spo2 = vitals_history[-1]["spo2"] if vitals_history else 0
        spo2_color = "#00C851" if current_spo2 >= 95 else "#FFA500" if current_spo2 >= 90 else "#FF4444"
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.line_chart(df.set_index("timestamp")["spo2"], use_container_width=True)
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 36px; font-weight: bold; color: {spo2_color};">{current_spo2}%</div>
                <div style="font-size: 12px; color: #888;">Current</div>
            </div>
            """, unsafe_allow_html=True)
    
    if chart_type in ["heart_rate", "both"]:
        st.markdown("#### ❤️ Heart Rate")
        
        # Current value display
        current_hr = vitals_history[-1]["heart_rate"] if vitals_history else 0
        hr_color = "#00C851" if 60 <= current_hr <= 100 else "#FFA500" if 50 <= current_hr <= 110 else "#FF4444"
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.line_chart(df.set_index("timestamp")["heart_rate"], use_container_width=True)
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 36px; font-weight: bold; color: {hr_color};">{current_hr}</div>
                <div style="font-size: 12px; color: #888;">BPM</div>
            </div>
            """, unsafe_allow_html=True)


def render_mini_vitals(spo2: float, heart_rate: int, compact: bool = True):
    """
    Render compact vitals display for cards
    
    Args:
        spo2: Blood oxygen level
        heart_rate: Heart rate in BPM
        compact: If True, show in single row
    """
    spo2_color = "#00C851" if spo2 >= 95 else "#FFA500" if spo2 >= 90 else "#FF4444"
    hr_color = "#00C851" if 60 <= heart_rate <= 100 else "#FFA500" if 50 <= heart_rate <= 110 else "#FF4444"
    
    if compact:
        st.markdown(f"""
        <div style="display: flex; justify-content: space-around; padding: 10px; background: #1a1a2e; border-radius: 10px;">
            <div style="text-align: center;">
                <span style="font-size: 20px; color: {spo2_color}; font-weight: bold;">🫁 {spo2}%</span>
                <div style="font-size: 10px; color: #888;">SpO2</div>
            </div>
            <div style="text-align: center;">
                <span style="font-size: 20px; color: {hr_color}; font-weight: bold;">❤️ {heart_rate}</span>
                <div style="font-size: 10px; color: #888;">BPM</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🫁 SpO2", f"{spo2}%")
        with col2:
            st.metric("❤️ Heart Rate", f"{heart_rate} BPM")


def generate_demo_vitals_history(minutes: int = 30) -> List[Dict]:
    """Generate demo vitals history for testing"""
    history = []
    base_spo2 = random.uniform(92, 98)
    base_hr = random.randint(70, 90)
    
    for i in range(minutes):
        timestamp = (datetime.now() - timedelta(minutes=(minutes - i))).strftime("%H:%M")
        history.append({
            "timestamp": timestamp,
            "spo2": round(base_spo2 + random.uniform(-3, 3), 1),
            "heart_rate": base_hr + random.randint(-10, 10)
        })
    
    return history
