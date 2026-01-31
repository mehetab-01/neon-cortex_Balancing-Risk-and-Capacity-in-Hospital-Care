"""
VitalFlow AI - Patient Cards Component
Individual patient status cards with vitals and actions
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from shared.constants import STATUS_COLORS, STATUS_EMOJI


def get_vital_status(vital_type: str, value: float) -> tuple:
    """
    Get status color and icon for a vital sign
    Returns: (color, icon, status_text)
    """
    if vital_type == "spo2":
        if value < 90:
            return "#FF4B4B", "🔴", "Critical"
        elif value < 95:
            return "#FFA500", "🟠", "Low"
        else:
            return "#00CC66", "🟢", "Normal"
    
    elif vital_type == "heart_rate":
        if value < 50 or value > 120:
            return "#FF4B4B", "🔴", "Critical"
        elif value < 60 or value > 100:
            return "#FFA500", "🟠", "Abnormal"
        else:
            return "#00CC66", "🟢", "Normal"
    
    elif vital_type == "temperature":
        if value < 35 or value > 39:
            return "#FF4B4B", "🔴", "Critical"
        elif value < 36 or value > 38:
            return "#FFA500", "🟠", "Abnormal"
        else:
            return "#00CC66", "🟢", "Normal"
    
    return "#888888", "⚪", "Unknown"


def render_patient_card(patient: Dict, expanded: bool = False):
    """
    Render a single patient card with status and vitals
    """
    status = patient.get("status", "Stable")
    color = STATUS_COLORS.get(status, "#888888")
    emoji = STATUS_EMOJI.get(status, "⚪")
    
    # Calculate time since admission
    admitted_at = patient.get("admitted_at")
    if admitted_at:
        if isinstance(admitted_at, str):
            admitted_dt = datetime.fromisoformat(admitted_at.replace('Z', '+00:00'))
        else:
            admitted_dt = admitted_at
        time_diff = datetime.now() - admitted_dt.replace(tzinfo=None)
        hours = int(time_diff.total_seconds() // 3600)
        if hours < 24:
            time_str = f"{hours}h ago"
        else:
            days = hours // 24
            time_str = f"{days}d ago"
    else:
        time_str = "N/A"
    
    # Card container with colored border
    with st.container():
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%);
                border-left: 4px solid {color};
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: white;">{emoji} {patient['name']}</h4>
                        <p style="margin: 5px 0; color: #888;">
                            ID: {patient['id']} | Age: {patient['age']} | Bed: {patient.get('bed_id', 'N/A')}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="
                            background: {color}; 
                            color: white; 
                            padding: 5px 10px; 
                            border-radius: 15px;
                            font-size: 12px;
                            font-weight: bold;
                        ">{status}</span>
                        <p style="margin: 5px 0; color: #888; font-size: 12px;">Admitted {time_str}</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if expanded:
            # Vitals section
            col1, col2, col3, col4 = st.columns(4)
            
            spo2_color, spo2_icon, spo2_status = get_vital_status("spo2", patient.get("spo2", 0))
            hr_color, hr_icon, hr_status = get_vital_status("heart_rate", patient.get("heart_rate", 0))
            temp_color, temp_icon, temp_status = get_vital_status("temperature", patient.get("temperature", 0))
            
            with col1:
                st.markdown(f"**{spo2_icon} SpO2**")
                st.markdown(f"<h3 style='color: {spo2_color}; margin: 0;'>{patient.get('spo2', 'N/A')}%</h3>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**{hr_icon} Heart Rate**")
                st.markdown(f"<h3 style='color: {hr_color}; margin: 0;'>{patient.get('heart_rate', 'N/A')} bpm</h3>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"**💉 Blood Pressure**")
                st.markdown(f"<h3 style='margin: 0;'>{patient.get('blood_pressure', 'N/A')}</h3>", unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"**{temp_icon} Temperature**")
                st.markdown(f"<h3 style='color: {temp_color}; margin: 0;'>{patient.get('temperature', 'N/A')}°C</h3>", unsafe_allow_html=True)
            
            st.markdown(f"**📋 Diagnosis:** {patient.get('diagnosis', 'N/A')}")
            st.markdown(f"**👨‍⚕️ Doctor:** {patient.get('assigned_doctor', 'Unassigned')}")
            
            if patient.get('notes'):
                st.info(f"📝 Notes: {patient['notes']}")


def render_patient_list(patients: List[Dict], filter_status: Optional[str] = None, 
                        sort_by: str = "status", limit: int = None):
    """
    Render a list of patient cards with filtering and sorting
    """
    # Filter
    filtered = patients
    if filter_status:
        filtered = [p for p in patients if p.get('status') == filter_status]
    
    # Sort
    status_priority = {"Critical": 0, "Serious": 1, "Stable": 2, "Recovering": 3}
    
    if sort_by == "status":
        filtered.sort(key=lambda x: status_priority.get(x.get('status', 'Stable'), 99))
    elif sort_by == "spo2":
        filtered.sort(key=lambda x: x.get('spo2', 100))
    elif sort_by == "name":
        filtered.sort(key=lambda x: x.get('name', ''))
    elif sort_by == "admitted":
        filtered.sort(key=lambda x: x.get('admitted_at', ''), reverse=True)
    
    # Limit
    if limit:
        filtered = filtered[:limit]
    
    # Render
    if not filtered:
        st.info("No patients matching the criteria")
        return
    
    for patient in filtered:
        with st.expander(f"{STATUS_EMOJI.get(patient.get('status', 'Stable'), '⚪')} {patient['name']} - {patient.get('bed_id', 'N/A')}", expanded=False):
            render_patient_card(patient, expanded=True)


def render_critical_patients_panel(patients: List[Dict]):
    """
    Render a panel showing only critical patients
    """
    critical = [p for p in patients if p.get('status') == 'Critical']
    
    st.markdown("### 🚨 Critical Patients")
    
    if not critical:
        st.success("✅ No critical patients at this time")
        return
    
    st.error(f"⚠️ {len(critical)} patients require immediate attention")
    
    for patient in critical:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**🔴 {patient['name']}** ({patient['id']})")
            st.markdown(f"Bed: {patient.get('bed_id', 'N/A')} | {patient['diagnosis']}")
        
        with col2:
            spo2 = patient.get('spo2', 0)
            spo2_color = "#FF4B4B" if spo2 < 90 else "#FFA500"
            st.markdown(f"<span style='color: {spo2_color}; font-size: 24px; font-weight: bold;'>SpO2: {spo2}%</span>", unsafe_allow_html=True)
        
        with col3:
            hr = patient.get('heart_rate', 0)
            hr_color = "#FF4B4B" if hr > 120 or hr < 50 else "#FFA500"
            st.markdown(f"<span style='color: {hr_color}; font-size: 24px; font-weight: bold;'>HR: {hr}</span>", unsafe_allow_html=True)
        
        st.divider()


def render_patient_table(patients: List[Dict]):
    """
    Render patients in a table format
    """
    import pandas as pd
    
    if not patients:
        st.info("No patients to display")
        return
    
    # Prepare data
    data = []
    for p in patients:
        data.append({
            "Status": f"{STATUS_EMOJI.get(p.get('status', 'Stable'), '⚪')} {p.get('status', 'N/A')}",
            "ID": p['id'],
            "Name": p['name'],
            "Age": p['age'],
            "Bed": p.get('bed_id', 'N/A'),
            "Diagnosis": p['diagnosis'][:30] + "..." if len(p.get('diagnosis', '')) > 30 else p.get('diagnosis', 'N/A'),
            "SpO2": f"{p.get('spo2', 'N/A')}%",
            "HR": f"{p.get('heart_rate', 'N/A')} bpm",
            "Doctor": p.get('assigned_doctor', 'Unassigned'),
        })
    
    df = pd.DataFrame(data)
    
    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "ID": st.column_config.TextColumn("ID", width="small"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "SpO2": st.column_config.TextColumn("SpO2", width="small"),
            "HR": st.column_config.TextColumn("HR", width="small"),
        }
    )


def render_patient_search(patients: List[Dict]) -> List[Dict]:
    """
    Render search and filter controls, return filtered patients
    """
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search = st.text_input("🔍 Search patient", placeholder="Name, ID, or diagnosis...")
    
    with col2:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Critical", "Serious", "Stable", "Recovering"]
        )
    
    with col3:
        sort_option = st.selectbox(
            "Sort by",
            ["Priority (Status)", "SpO2 (Low first)", "Name", "Recently Admitted"]
        )
    
    # Apply filters
    filtered = patients
    
    if search:
        search_lower = search.lower()
        filtered = [
            p for p in filtered
            if search_lower in p.get('name', '').lower()
            or search_lower in p.get('id', '').lower()
            or search_lower in p.get('diagnosis', '').lower()
        ]
    
    if status_filter != "All":
        filtered = [p for p in filtered if p.get('status') == status_filter]
    
    # Apply sorting
    status_priority = {"Critical": 0, "Serious": 1, "Stable": 2, "Recovering": 3}
    
    if sort_option == "Priority (Status)":
        filtered.sort(key=lambda x: status_priority.get(x.get('status', 'Stable'), 99))
    elif sort_option == "SpO2 (Low first)":
        filtered.sort(key=lambda x: x.get('spo2', 100))
    elif sort_option == "Name":
        filtered.sort(key=lambda x: x.get('name', ''))
    elif sort_option == "Recently Admitted":
        filtered.sort(key=lambda x: x.get('admitted_at', ''), reverse=True)
    
    return filtered
