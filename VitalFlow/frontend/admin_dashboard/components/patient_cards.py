"""
Patient Cards Component
Display patient information with vitals and status
"""
import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.triage_engine import triage_engine
from shared.constants import STATUS_COLORS, PRIORITY_COLORS


def get_status_emoji(status: str) -> str:
    """Get emoji for patient status."""
    status_emojis = {
        "Critical": "🔴",
        "Serious": "🟠", 
        "Stable": "🟢",
        "Recovering": "🔵",
        "Discharged": "⚪"
    }
    return status_emojis.get(status, "⚪")


def get_vital_status(value, low_threshold, high_threshold, critical_low=None, critical_high=None):
    """Determine if vital is normal, warning, or critical."""
    if critical_low and value < critical_low:
        return "critical", "🔴"
    if critical_high and value > critical_high:
        return "critical", "🔴"
    if value < low_threshold or value > high_threshold:
        return "warning", "🟡"
    return "normal", "🟢"


def render_patient_card(patient):
    """Render a single patient card with detailed information."""
    status = str(patient.status)
    status_emoji = get_status_emoji(status)
    priority = triage_engine.calculate_priority(patient)
    priority_label = triage_engine.get_priority_label(priority)
    
    # Determine vital status indicators
    spo2_status, spo2_emoji = get_vital_status(patient.spo2, 90, 100, 85, None)
    hr_status, hr_emoji = get_vital_status(patient.heart_rate, 60, 100, 40, 150)
    
    # Get assigned staff
    doctor_name = "Not assigned"
    nurse_name = "Not assigned"
    
    if patient.assigned_doctor_id:
        doctor = hospital_state.staff.get(patient.assigned_doctor_id)
        if doctor:
            doctor_name = doctor.name
    
    if patient.assigned_nurse_id:
        nurse = hospital_state.staff.get(patient.assigned_nurse_id)
        if nurse:
            nurse_name = nurse.name
    
    # Render card
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        border-left: 4px solid {STATUS_COLORS.get(status, '#999')};
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.2rem; font-weight: bold;">{status_emoji} {patient.name}</span>
                <span style="margin-left: 1rem; color: #888;">#{patient.id}</span>
            </div>
            <div style="background: {PRIORITY_COLORS.get(priority, '#999')}; padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.8rem;">
                {priority_label}
            </div>
        </div>
        <div style="margin-top: 0.5rem; color: #aaa;">
            {patient.age} yrs | {patient.gender} | {patient.diagnosis or 'No diagnosis'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Vitals in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(f"{spo2_emoji} SpO2", f"{patient.spo2}%")
    
    with col2:
        st.metric(f"{hr_emoji} Heart Rate", f"{patient.heart_rate} bpm")
    
    with col3:
        st.metric("🌡️ Temp", f"{getattr(patient, 'temperature', 98.6)}°F")
    
    with col4:
        st.metric("💉 BP", getattr(patient, 'blood_pressure', '120/80'))
    
    # Additional info
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"🛏️ **Bed:** {patient.bed_id or 'Not assigned'}")
        st.write(f"👨‍⚕️ **Doctor:** {doctor_name}")
    
    with col2:
        st.write(f"👩‍⚕️ **Nurse:** {nurse_name}")
        if patient.admission_time:
            st.write(f"📅 **Admitted:** {patient.admission_time.strftime('%d %b, %H:%M') if hasattr(patient.admission_time, 'strftime') else patient.admission_time}")


def render_patient_cards():
    """Render all patient cards with filtering options."""
    st.markdown("## 👥 Patient Overview")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Critical", "Serious", "Stable", "Recovering"],
            key="patient_status_filter"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Priority", "Name", "Status", "SpO2"],
            key="patient_sort"
        )
    
    with col3:
        search = st.text_input("🔍 Search patient", key="patient_search")
    
    with col4:
        st.markdown("###")
        show_critical_only = st.checkbox("Show Critical Only", key="critical_only")
    
    # Get patients
    patients = list(hospital_state.patients.values())
    
    # Apply filters
    if status_filter != "All":
        patients = [p for p in patients if str(p.status) == status_filter]
    
    if show_critical_only:
        patients = [p for p in patients if str(p.status) == "Critical"]
    
    if search:
        patients = [p for p in patients if search.lower() in p.name.lower() or search in p.id]
    
    # Sort
    if sort_by == "Priority":
        patients.sort(key=lambda p: triage_engine.calculate_priority(p))
    elif sort_by == "Name":
        patients.sort(key=lambda p: p.name)
    elif sort_by == "Status":
        status_order = {"Critical": 0, "Serious": 1, "Stable": 2, "Recovering": 3, "Discharged": 4}
        patients.sort(key=lambda p: status_order.get(str(p.status), 5))
    elif sort_by == "SpO2":
        patients.sort(key=lambda p: p.spo2)
    
    # Display stats
    st.markdown(f"**Showing {len(patients)} patients**")
    
    # Render patient cards
    if not patients:
        st.info("No patients found matching the criteria")
    else:
        for patient in patients:
            with st.expander(f"{get_status_emoji(str(patient.status))} {patient.name} - {patient.diagnosis or 'No diagnosis'}", expanded=False):
                render_patient_card(patient)
                
                # Quick actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📝 Update Vitals", key=f"update_{patient.id}"):
                        st.session_state[f"editing_{patient.id}"] = True
                
                with col2:
                    if st.button("🔄 Request Transfer", key=f"transfer_{patient.id}"):
                        st.info(f"Transfer request initiated for {patient.name}")
                
                with col3:
                    if str(patient.status) == "Recovering":
                        if st.button("✅ Discharge", key=f"discharge_{patient.id}"):
                            st.success(f"Discharge process initiated for {patient.name}")


if __name__ == "__main__":
    render_patient_cards()
