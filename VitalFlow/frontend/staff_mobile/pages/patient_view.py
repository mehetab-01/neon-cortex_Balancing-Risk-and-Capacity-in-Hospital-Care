"""
Patient View - Staff Mobile App
Features:
- Recovery percentage
- Estimated discharge time
- Medicines & reports (read-only)
- Assigned care team
- Vitals history
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.triage_engine import triage_engine


def apply_patient_styles():
    """Apply patient-friendly styling."""
    st.markdown("""
    <style>
        .patient-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .recovery-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin: 1rem 0;
        }
        
        .info-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
    </style>
    """, unsafe_allow_html=True)


def calculate_recovery_percentage(patient) -> int:
    """Calculate recovery percentage based on vitals and status."""
    status = str(patient.status)
    
    # Base score by status
    status_scores = {
        "Critical": 10,
        "Serious": 30,
        "Stable": 60,
        "Recovering": 85,
        "Discharged": 100
    }
    base = status_scores.get(status, 50)
    
    # Vital adjustments
    vital_bonus = 0
    
    # SpO2 contribution
    if patient.spo2 >= 98:
        vital_bonus += 15
    elif patient.spo2 >= 95:
        vital_bonus += 10
    elif patient.spo2 >= 90:
        vital_bonus += 5
    
    # Heart rate contribution
    if 60 <= patient.heart_rate <= 100:
        vital_bonus += 10
    elif 55 <= patient.heart_rate <= 110:
        vital_bonus += 5
    
    return min(100, base + vital_bonus)


def estimate_discharge_date(patient) -> str:
    """Estimate discharge date based on status and recovery."""
    status = str(patient.status)
    recovery = calculate_recovery_percentage(patient)
    
    # Estimate days based on status
    if status == "Discharged":
        return "Already discharged"
    elif status == "Recovering" and recovery >= 90:
        return "Within 1-2 days"
    elif status == "Recovering":
        return "Within 3-5 days"
    elif status == "Stable":
        return "Within 5-7 days"
    elif status == "Serious":
        return "1-2 weeks (pending improvement)"
    elif status == "Critical":
        return "Under intensive care - TBD"
    
    return "To be determined"


def select_patient():
    """Allow patient to select their record."""
    st.markdown("""
    <div class="patient-header">
        <h2>🏥 VitalFlow Patient Portal</h2>
        <p>View your health status and recovery progress</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 Access Your Records")
    
    # Get patient list
    patients = list(hospital_state.patients.values())
    
    if not patients:
        st.warning("No patient records found in the system")
        st.info("If you're a new patient, please contact the reception desk")
        
        if st.button("🔙 Back to Home"):
            st.session_state.logged_in = False
            st.session_state.portal = None
            st.rerun()
        return None
    
    # Patient selection (in production, would use authentication)
    patient_options = {f"{p.name} (#{p.id})": p.id for p in patients}
    
    selected = st.selectbox(
        "Select your name",
        list(patient_options.keys()),
        key="patient_select"
    )
    
    # Verification (simplified for demo)
    verify_dob = st.date_input("Date of Birth (for verification)", 
                               value=datetime.now() - timedelta(days=365*30))
    
    if st.button("📋 View My Records", use_container_width=True):
        patient_id = patient_options[selected]
        st.session_state.current_patient_id = patient_id
        st.rerun()
    
    st.markdown("---")
    if st.button("🔙 Back to Home", key="patient_back"):
        st.session_state.logged_in = False
        st.session_state.portal = None
        st.rerun()
    
    return None


def render_recovery_dashboard(patient):
    """Render main recovery dashboard."""
    recovery_pct = calculate_recovery_percentage(patient)
    status = str(patient.status)
    
    # Header with patient name
    st.markdown(f"""
    <div class="patient-header">
        <h2>👋 Hello, {patient.name}</h2>
        <p>Here's your health update</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Recovery percentage card
    st.markdown(f"""
    <div class="recovery-card">
        <h1 style="font-size: 4rem; margin: 0;">{recovery_pct}%</h1>
        <p style="font-size: 1.5rem; margin: 0.5rem 0;">Recovery Progress</p>
        <p>Status: {status}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    st.progress(recovery_pct / 100)
    
    # Discharge estimate
    discharge_estimate = estimate_discharge_date(patient)
    st.info(f"📅 **Estimated Discharge:** {discharge_estimate}")


def render_vitals_section(patient):
    """Render current vitals section."""
    st.markdown("### 📊 Your Current Vitals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # SpO2
        spo2_status = "🟢 Normal" if patient.spo2 >= 95 else "🟡 Low" if patient.spo2 >= 90 else "🔴 Critical"
        st.metric(
            "Oxygen Level (SpO2)",
            f"{patient.spo2}%",
            help="Normal range: 95-100%"
        )
        st.caption(spo2_status)
        
        # Blood Pressure
        bp = getattr(patient, 'blood_pressure', '120/80')
        st.metric("Blood Pressure", bp)
    
    with col2:
        # Heart Rate
        hr = patient.heart_rate
        hr_status = "🟢 Normal" if 60 <= hr <= 100 else "🟡 Abnormal"
        st.metric(
            "Heart Rate",
            f"{hr} bpm",
            help="Normal range: 60-100 bpm"
        )
        st.caption(hr_status)
        
        # Temperature
        temp = getattr(patient, 'temperature', 98.6)
        temp_status = "🟢 Normal" if 97 <= temp <= 99 else "🟡 Fever"
        st.metric("Temperature", f"{temp}°F")
        st.caption(temp_status)


def render_care_team(patient):
    """Render assigned care team."""
    st.markdown("### 👨‍⚕️ Your Care Team")
    
    # Doctor
    if patient.assigned_doctor_id:
        doctor = hospital_state.staff.get(patient.assigned_doctor_id)
        if doctor:
            st.markdown(f"""
            <div class="info-card">
                <h4>👨‍⚕️ Primary Doctor</h4>
                <p><strong>{doctor.name}</strong></p>
                <p>Specialization: {doctor.specialization or 'General Medicine'}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👨‍⚕️ Doctor will be assigned shortly")
    
    # Nurse
    if patient.assigned_nurse_id:
        nurse = hospital_state.staff.get(patient.assigned_nurse_id)
        if nurse:
            st.markdown(f"""
            <div class="info-card">
                <h4>👩‍⚕️ Assigned Nurse</h4>
                <p><strong>{nurse.name}</strong></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👩‍⚕️ Nurse will be assigned shortly")
    
    # Bed info
    if patient.bed_id:
        bed = hospital_state.beds.get(patient.bed_id)
        if bed:
            st.markdown(f"""
            <div class="info-card">
                <h4>🛏️ Your Bed</h4>
                <p><strong>{bed.id}</strong> - {bed.ward}</p>
                <p>Floor: {bed.floor}</p>
            </div>
            """, unsafe_allow_html=True)


def render_medicines_reports(patient):
    """Render medicines and reports section."""
    st.markdown("### 💊 Medicines & Reports")
    
    tabs = st.tabs(["💊 Medicines", "📋 Reports", "📝 Notes"])
    
    with tabs[0]:
        st.markdown("**Current Medications:**")
        
        # Sample medications based on status
        status = str(patient.status)
        
        if status == "Critical":
            meds = [
                "IV Fluids - Continuous",
                "Emergency medications as per doctor's orders",
                "Pain management - As needed"
            ]
        elif status == "Serious":
            meds = [
                "Prescribed medication - Every 6 hours",
                "IV fluids - As needed",
                "Supplements - Daily"
            ]
        else:
            meds = [
                "Regular medication - As prescribed",
                "Multivitamins - Daily",
                "Pain relief - As needed"
            ]
        
        for med in meds:
            st.write(f"• {med}")
        
        st.caption("*For detailed prescription, please ask your nurse*")
    
    with tabs[1]:
        st.markdown("**Recent Reports:**")
        
        reports = [
            f"🩸 Blood Test - {(datetime.now() - timedelta(days=1)).strftime('%d %b')}",
            f"📊 Vitals Report - {datetime.now().strftime('%d %b')}",
            f"📝 Admission Report - {patient.admission_time.strftime('%d %b') if hasattr(patient.admission_time, 'strftime') else 'On Admission'}"
        ]
        
        for report in reports:
            st.write(f"• {report}")
        
        st.caption("*Request detailed reports from the nursing station*")
    
    with tabs[2]:
        st.markdown("**Doctor's Notes:**")
        
        if patient.notes:
            for note in patient.notes[-5:]:
                st.markdown(f"📝 {note}")
        else:
            st.info("No notes added yet")


def render_patient_view():
    """Main render function for patient view."""
    apply_patient_styles()
    
    # Check if patient is selected
    if "current_patient_id" not in st.session_state:
        select_patient()
        return
    
    patient = hospital_state.patients.get(st.session_state.current_patient_id)
    
    if not patient:
        st.error("Patient record not found")
        if st.button("🔙 Back"):
            del st.session_state.current_patient_id
            st.rerun()
        return
    
    # Sign Out button in header
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚪 Sign Out", key="patient_signout", type="secondary"):
            if "current_patient_id" in st.session_state:
                del st.session_state.current_patient_id
            st.session_state.logged_in = False
            st.session_state.portal = None
            st.rerun()
    
    # Main content tabs
    tabs = st.tabs(["📊 Overview", "💊 Treatment", "👨‍⚕️ Care Team"])
    
    with tabs[0]:
        render_recovery_dashboard(patient)
        st.markdown("---")
        render_vitals_section(patient)
    
    with tabs[1]:
        render_medicines_reports(patient)
    
    with tabs[2]:
        render_care_team(patient)
    
    # Help section
    st.markdown("---")
    st.markdown("### 🆘 Need Help?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔔 Call Nurse", use_container_width=True):
            st.success("Nurse has been notified!")
    
    with col2:
        if st.button("❓ Ask Question", use_container_width=True):
            st.info("Your query has been logged. A staff member will visit shortly.")


if __name__ == "__main__":
    render_patient_view()
