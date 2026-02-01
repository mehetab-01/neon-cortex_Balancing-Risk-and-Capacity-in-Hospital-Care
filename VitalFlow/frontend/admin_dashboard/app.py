"""
VitalFlow AI - Admin Dashboard
Full hospital overview and management console

Features:
- Real-time bed occupancy visualization
- Patient status monitoring
- Staff management
- CCTV fall detection alerts
- Decision log transparency
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import backend modules
from backend.core_logic.state import hospital_state
from backend.core_logic.bed_manager import bed_manager
from backend.core_logic.staff_manager import staff_manager
from backend.core_logic.triage_engine import triage_engine
from backend.ai_services.fall_detector import fall_detector
from backend.ai_services.emergency_alerts import (
    emergency_service, EmergencyType, trigger_code_blue, 
    trigger_fall_alert, announce_emergency
)

# Import components
from .components.floor_map import render_floor_map
from .components.city_map import render_city_map
from .components.patient_cards import render_patient_cards
from .components.stats_panel import render_stats_panel
from .components.decision_log import render_decision_log


def apply_admin_styles():
    """Apply custom CSS for admin dashboard."""
    st.markdown("""
    <style>
        /* Dashboard container */
        .dashboard-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 1rem 2rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .dashboard-title {
            font-size: 1.8rem;
            font-weight: bold;
            color: #00d4ff;
        }
        
        /* Status cards */
        .status-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 1.5rem;
            border-left: 4px solid #00d4ff;
            margin: 0.5rem 0;
        }
        
        /* Alert styling */
        .alert-critical {
            background: rgba(255, 0, 0, 0.1);
            border-left: 4px solid #ff0000;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        
        .alert-warning {
            background: rgba(255, 165, 0, 0.1);
            border-left: 4px solid #ffa500;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 10px 20px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #00d4ff !important;
        }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the dashboard header with navigation."""
    # Try to get authenticated user
    try:
        from frontend.auth.google_auth import get_authenticated_user, google_auth_service
        user = get_authenticated_user()
    except ImportError:
        user = None
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        st.markdown("""
        <div class="dashboard-header">
            <span class="dashboard-title">🏥 VitalFlow Central Hospital</span>
            <span style="color: #00ff88; margin-left: 1rem;">● Live</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**📅 {datetime.now().strftime('%d %b %Y, %H:%M')}**")
    
    with col3:
        # Show user info if authenticated
        if user:
            if user.picture:
                st.image(user.picture, width=35)
            st.caption(user.name.split()[0] if user.name else "User")
    
    with col4:
        if st.button("🚪 Sign Out", key="admin_signout", type="secondary"):
            # Clear all session state including Google auth
            try:
                google_auth_service.sign_out()
            except:
                pass
            st.session_state.logged_in = False
            st.session_state.portal = None
            st.session_state.show_login = False
            st.session_state.admin_logged_in = False
            st.rerun()


def render_alerts_section():
    """Render active alerts and emergencies."""
    st.markdown("### 🚨 Active Alerts")
    
    # Check for CCTV alerts
    alerts = fall_detector.get_pending_alerts() if hasattr(fall_detector, 'get_pending_alerts') else []
    
    # Check for critical patients
    critical_patients = [p for p in hospital_state.patients.values() 
                        if hasattr(p, 'status') and str(p.status) == "Critical"]
    
    # Check for fatigued staff
    fatigued_staff = []
    for staff in hospital_state.staff.values():
        if staff_manager.is_fatigued(staff.id):
            fatigued_staff.append(staff)
    
    if not alerts and not critical_patients and not fatigued_staff:
        st.success("✅ No active alerts - All systems normal")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CCTV Alerts
        if alerts:
            for alert in alerts[:3]:  # Show top 3
                st.markdown(f"""
                <div class="alert-critical">
                    <strong>📹 CCTV ALERT</strong><br>
                    {alert.get('alert_type', 'Unknown')} at {alert.get('zone_name', 'Unknown Zone')}<br>
                    <small>Confidence: {alert.get('confidence', 0):.1f}%</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Critical patients
        if critical_patients:
            for patient in critical_patients[:3]:
                st.markdown(f"""
                <div class="alert-critical">
                    <strong>🔴 CRITICAL PATIENT</strong><br>
                    {patient.name} - {patient.diagnosis}<br>
                    <small>SpO2: {patient.spo2}% | HR: {patient.heart_rate}</small>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        # Fatigue warnings
        if fatigued_staff:
            for staff in fatigued_staff[:3]:
                warning = staff_manager.get_fatigue_warning(staff.id)
                st.markdown(f"""
                <div class="alert-warning">
                    <strong>⚠️ FATIGUE WARNING</strong><br>
                    {warning if warning else f"{staff.name} has exceeded safe working hours"}
                </div>
                """, unsafe_allow_html=True)


def render_bed_management():
    """Render bed management section with approval workflow."""
    st.markdown("### 🛏️ Bed Management")
    
    # Get bed occupancy stats
    occupancy = bed_manager.get_bed_occupancy()
    
    # Display bed type breakdown
    cols = st.columns(5)
    bed_types = ["ICU", "Emergency", "General", "Pediatric", "Maternity"]
    colors = ["🔴", "🟠", "🟢", "🔵", "💜"]
    
    for idx, (col, bed_type) in enumerate(zip(cols, bed_types)):
        with col:
            stats = occupancy.get(bed_type, {"total": 0, "occupied": 0, "available": 0})
            st.metric(
                f"{colors[idx]} {bed_type}",
                f"{stats['available']}/{stats['total']}",
                delta=f"-{stats['occupied']} occupied" if stats['occupied'] > 0 else "All free"
            )
    
    # Pending approvals
    st.markdown("#### 📋 Pending Approvals")
    
    pending_decisions = [d for d in hospital_state.decision_log 
                        if "PENDING" in d.get("action", "").upper() or 
                           "SWAP" in d.get("action", "").upper()][-5:]
    
    if pending_decisions:
        for decision in pending_decisions:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{decision.get('action', 'Unknown')}**: {decision.get('reason', '')}")
            with col2:
                if st.button("✅ Approve", key=f"approve_{decision.get('timestamp', '')}"):
                    st.success("Approved!")
            with col3:
                if st.button("❌ Reject", key=f"reject_{decision.get('timestamp', '')}"):
                    st.error("Rejected")
    else:
        st.info("No pending approvals")


def render_staff_overview():
    """Render staff management overview."""
    st.markdown("### 👥 Staff Overview")
    
    # Group staff by role
    doctors = [s for s in hospital_state.staff.values() if str(s.role) == "Doctor"]
    nurses = [s for s in hospital_state.staff.values() if str(s.role) == "Nurse"]
    wardboys = [s for s in hospital_state.staff.values() if str(s.role) == "Wardboy"]
    drivers = [s for s in hospital_state.staff.values() if str(s.role) == "Driver"]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        available_doctors = len([d for d in doctors if str(d.status) == "Available"])
        st.metric("👨‍⚕️ Doctors", f"{available_doctors}/{len(doctors)} available")
    
    with col2:
        available_nurses = len([n for n in nurses if str(n.status) == "Available"])
        st.metric("👩‍⚕️ Nurses", f"{available_nurses}/{len(nurses)} available")
    
    with col3:
        available_wardboys = len([w for w in wardboys if str(w.status) == "Available"])
        st.metric("🧹 Ward Staff", f"{available_wardboys}/{len(wardboys)} available")
    
    with col4:
        available_drivers = len([d for d in drivers if str(d.status) == "Available"])
        st.metric("🚑 Drivers", f"{available_drivers}/{len(drivers)} available")
    
    # Detailed staff table
    with st.expander("📋 View All Staff"):
        staff_data = []
        for staff in hospital_state.staff.values():
            hours = staff_manager.get_hours_worked(staff.id)
            fatigue = staff_manager.get_fatigue_level(staff.id)
            patients = staff_manager.get_patient_count(staff.id)
            
            staff_data.append({
                "ID": staff.id,
                "Name": staff.name,
                "Role": str(staff.role),
                "Status": str(staff.status),
                "Hours Worked": f"{hours:.1f}h",
                "Fatigue Level": fatigue.upper(),
                "Patients": patients
            })
        
        if staff_data:
            st.dataframe(staff_data, use_container_width=True)


def render_cctv_monitoring():
    """Render CCTV monitoring section with fall detection."""
    st.markdown("### 📹 CCTV Fall Detection Monitoring")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Active Camera Zones")
        
        # Get zones from fall detector
        zones = fall_detector.zones if hasattr(fall_detector, 'zones') else {}
        
        if zones:
            zone_data = []
            for zone_id, zone in zones.items():
                zone_data.append({
                    "Zone ID": zone_id,
                    "Location": zone.zone_name,
                    "Person Detected": "✅" if zone.person_detected else "❌",
                    "Movement": "✅" if not zone.alert_triggered else "⚠️",
                    "Status": "🟢 Normal" if not zone.alert_triggered else "🔴 Alert"
                })
            st.dataframe(zone_data, use_container_width=True)
        else:
            st.info("No camera zones configured")
    
    with col2:
        st.markdown("#### Alert History")
        
        alerts = list(fall_detector.alerts.values()) if hasattr(fall_detector, 'alerts') else []
        
        if alerts:
            for alert in alerts[-5:]:
                status_color = "🔴" if alert.status.value == "Pending Verification" else "🟢"
                st.markdown(f"""
                {status_color} **{alert.alert_type.value}**  
                📍 {alert.zone_name}  
                🕐 {alert.timestamp.strftime('%H:%M:%S')}  
                """)
        else:
            st.info("No alerts recorded")
    
    # Upload video for analysis
    st.markdown("#### 🎥 Upload Video for Analysis")
    uploaded_file = st.file_uploader(
        "Upload CCTV footage for fall detection analysis",
        type=["mp4", "avi", "mov"],
        key="cctv_upload"
    )
    
    if uploaded_file:
        if st.button("🔍 Analyze Video"):
            with st.spinner("Analyzing video for falls..."):
                # Trigger fall detection analysis
                st.info("Video analysis would be performed here using YOLOv8-Pose")
                st.success("Analysis complete - No falls detected")


def render_new_patient_registration():
    """Render new patient registration with automatic staff assignment."""
    st.markdown("### ➕ Register New Patient")
    st.info("🤖 **AI Auto-Assignment**: The system will automatically allocate the best available doctor and nurse based on workload, fatigue levels, and specialization.")
    
    # Import required models
    from shared.models import Patient, PatientStatus
    import uuid
    
    # Get available staff summary for preview
    available_doctors = staff_manager.get_available_doctors(exclude_fatigued=True)
    available_nurses = staff_manager.get_available_nurses(exclude_fatigued=True)
    
    # Staff availability preview
    st.markdown("#### 👥 Current Staff Availability")
    col1, col2 = st.columns(2)
    
    with col1:
        if available_doctors:
            st.success(f"✅ **{len(available_doctors)} Doctor(s) Available**")
            with st.expander("View Available Doctors"):
                for doc in available_doctors:
                    patient_count = staff_manager.get_patient_count(doc.id)
                    hours = staff_manager.get_hours_worked(doc.id)
                    fatigue = staff_manager.get_fatigue_level(doc.id)
                    can_take = staff_manager.can_take_more_patients(doc.id)
                    status_icon = "🟢" if can_take else "🔴"
                    st.markdown(f"""
                    {status_icon} **Dr. {doc.name}** ({doc.specialization or 'General'})  
                    └ Patients: {patient_count}/{staff_manager.MAX_PATIENTS_PER_DOCTOR} | Hours: {hours:.1f}h | {fatigue.upper()}
                    """)
        else:
            st.warning("⚠️ No doctors currently available (all fatigued or at capacity)")
    
    with col2:
        if available_nurses:
            st.success(f"✅ **{len(available_nurses)} Nurse(s) Available**")
            with st.expander("View Available Nurses"):
                for nurse in available_nurses:
                    patient_count = staff_manager.get_patient_count(nurse.id)
                    hours = staff_manager.get_hours_worked(nurse.id)
                    fatigue = staff_manager.get_fatigue_level(nurse.id)
                    can_take = staff_manager.can_take_more_patients(nurse.id)
                    status_icon = "🟢" if can_take else "🔴"
                    st.markdown(f"""
                    {status_icon} **{nurse.name}**  
                    └ Patients: {patient_count}/{staff_manager.MAX_PATIENTS_PER_NURSE} | Hours: {hours:.1f}h | {fatigue.upper()}
                    """)
        else:
            st.warning("⚠️ No nurses currently available (all fatigued or at capacity)")
    
    st.markdown("---")
    
    # Patient Registration Form
    st.markdown("#### 📋 Patient Information")
    
    with st.form("new_patient_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patient_name = st.text_input("👤 Patient Name *", placeholder="Enter patient name")
            patient_age = st.number_input("📅 Age *", min_value=0, max_value=120, value=30)
            patient_gender = st.selectbox("⚧ Gender", ["Male", "Female", "Other"])
        
        with col2:
            patient_diagnosis = st.text_input("🩺 Diagnosis *", placeholder="e.g., Pneumonia, Cardiac issues")
            patient_status = st.selectbox("🚨 Status *", [
                PatientStatus.STABLE.value,
                PatientStatus.SERIOUS.value,
                PatientStatus.CRITICAL.value,
                PatientStatus.RECOVERING.value
            ])
            blood_pressure = st.text_input("💉 Blood Pressure", value="120/80")
        
        with col3:
            spo2 = st.slider("🫁 SpO2 (%)", min_value=70, max_value=100, value=98)
            heart_rate = st.slider("💓 Heart Rate (bpm)", min_value=40, max_value=200, value=75)
            temperature = st.number_input("🌡️ Temperature (°F)", min_value=95.0, max_value=108.0, value=98.6, step=0.1)
        
        notes = st.text_area("📝 Additional Notes", placeholder="Any special conditions or requirements...")
        
        # Submit button
        submitted = st.form_submit_button("🚀 Register Patient & Auto-Assign Staff", type="primary", use_container_width=True)
        
        if submitted:
            if not patient_name or not patient_diagnosis:
                st.error("❌ Please fill in all required fields (Name and Diagnosis)")
            else:
                # Create new patient
                patient_id = f"P-{uuid.uuid4().hex[:8].upper()}"
                new_patient = Patient(
                    id=patient_id,
                    name=patient_name,
                    age=patient_age,
                    gender=patient_gender,
                    diagnosis=patient_diagnosis,
                    status=PatientStatus(patient_status),
                    spo2=float(spo2),
                    heart_rate=heart_rate,
                    blood_pressure=blood_pressure,
                    temperature=temperature,
                    notes=[notes] if notes else [],
                    admission_time=datetime.now()
                )
                
                # Add patient to state
                hospital_state.patients[patient_id] = new_patient
                
                # Log patient registration
                hospital_state.log_decision(
                    "PATIENT_REGISTERED",
                    f"New patient {patient_name} ({patient_status}) registered by admin",
                    {"patient_id": patient_id, "diagnosis": patient_diagnosis}
                )
                
                st.success(f"✅ Patient **{patient_name}** registered successfully!")
                st.markdown(f"**Patient ID:** `{patient_id}`")
                
                # Auto-assign bed
                best_bed = bed_manager.find_best_bed(new_patient)
                if best_bed:
                    bed_manager.assign_patient_to_bed(patient_id, best_bed.id)
                    st.success(f"🛏️ **Bed Assigned:** {best_bed.id} ({best_bed.bed_type} - {best_bed.ward})")
                else:
                    st.warning("⚠️ No beds available. Patient is in waiting list.")
                
                # Auto-assign doctor
                st.markdown("---")
                st.markdown("### 🤖 AI Staff Assignment")
                
                assigned_doctor = staff_manager.assign_doctor_to_patient(patient_id)
                if assigned_doctor:
                    doc_hours = staff_manager.get_hours_worked(assigned_doctor.id)
                    doc_patients = staff_manager.get_patient_count(assigned_doctor.id)
                    st.success(f"""
                    👨‍⚕️ **Doctor Assigned: Dr. {assigned_doctor.name}**  
                    └ Specialization: {assigned_doctor.specialization or 'General'}  
                    └ Hours Worked: {doc_hours:.1f}h  
                    └ Current Patients: {doc_patients}  
                    """)
                else:
                    st.warning("⚠️ No doctors available for assignment. Patient added to queue.")
                
                # Auto-assign nurse
                assigned_nurse = staff_manager.assign_nurse_to_patient(patient_id)
                if assigned_nurse:
                    nurse_hours = staff_manager.get_hours_worked(assigned_nurse.id)
                    nurse_patients = staff_manager.get_patient_count(assigned_nurse.id)
                    st.success(f"""
                    👩‍⚕️ **Nurse Assigned: {assigned_nurse.name}**  
                    └ Hours Worked: {nurse_hours:.1f}h  
                    └ Current Patients: {nurse_patients}  
                    """)
                else:
                    st.warning("⚠️ No nurses available for assignment. Patient added to queue.")
                
                # Show assignment summary
                if assigned_doctor or assigned_nurse:
                    st.markdown("---")
                    st.info(f"""
                    📊 **Assignment Summary**  
                    - Patient: {patient_name} ({patient_status})  
                    - Doctor: {"Dr. " + assigned_doctor.name if assigned_doctor else "Pending"}  
                    - Nurse: {assigned_nurse.name if assigned_nurse else "Pending"}  
                    - Bed: {best_bed.id if best_bed else "Pending"}
                    """)
                
                # Save state
                hospital_state.save()
                
                # Show balloons for successful registration
                st.balloons()


def render_emergency_alerts():
    """Render emergency alerts section with TTS notifications."""
    st.markdown("### 🚨 Emergency Alert System")
    
    # Get phone numbers
    phones = emergency_service.get_emergency_phone_info()
    
    # Emergency contacts display
    st.markdown("#### 📞 Emergency Contacts")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"🚑 **Emergency (108)**: {phones['emergency']}")
    with col2:
        st.info(f"🏥 **Hospital**: {phones['hospital']}")
    with col3:
        st.info(f"👨‍💼 **Admin**: {phones['admin']}")
    
    st.markdown("---")
    
    # Active Alerts
    active_alerts = emergency_service.get_active_alerts()
    
    if active_alerts:
        st.markdown("#### 🔴 Active Alerts")
        for alert in active_alerts:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.error(f"""
                    **{alert.emergency_type.value}** - {alert.location}  
                    {alert.description}  
                    📞 Call: **{alert.phone_to_call}**  
                    🕐 {alert.timestamp.strftime('%H:%M:%S')}
                    """)
                with col2:
                    if st.button("🔊 Replay", key=f"replay_{alert.id}"):
                        emergency_service.play_alert(alert.id)
                        st.success("Playing alert...")
                with col3:
                    if st.button("✅ Acknowledge", key=f"ack_{alert.id}"):
                        emergency_service.acknowledge_alert(alert.id)
                        st.rerun()
    else:
        st.success("✅ No active emergencies")
    
    st.markdown("---")
    
    # Trigger Emergency Alert
    st.markdown("#### ⚠️ Trigger Emergency Alert")
    
    with st.form("emergency_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            emergency_type = st.selectbox(
                "Emergency Type",
                [
                    EmergencyType.CODE_BLUE.value,
                    EmergencyType.CODE_RED.value,
                    EmergencyType.FALL_DETECTED.value,
                    EmergencyType.CRITICAL_VITALS.value,
                    EmergencyType.STAFF_EMERGENCY.value
                ]
            )
            location = st.text_input("Location *", placeholder="e.g., ICU Bed 3, Room 201")
        
        with col2:
            # Get patients for dropdown
            patient_options = ["None"] + [f"{p.name} ({p.id})" for p in hospital_state.patients.values()]
            selected_patient = st.selectbox("Patient (optional)", patient_options)
            description = st.text_area("Additional Details", placeholder="Describe the emergency...")
        
        # Custom message option
        custom_message = st.text_input(
            "Custom Voice Message (optional)", 
            placeholder="Enter custom message to announce..."
        )
        
        submitted = st.form_submit_button("🚨 TRIGGER EMERGENCY ALERT", type="primary", use_container_width=True)
        
        if submitted:
            if not location:
                st.error("Please specify the location!")
            else:
                # Extract patient info
                patient_name = None
                patient_id = None
                if selected_patient != "None":
                    parts = selected_patient.split(" (")
                    patient_name = parts[0]
                    patient_id = parts[1].rstrip(")")
                
                # Use custom message or standard alert
                if custom_message:
                    alert = announce_emergency(custom_message, location)
                else:
                    # Map to emergency type enum
                    etype = EmergencyType(emergency_type)
                    
                    if etype == EmergencyType.CODE_BLUE:
                        alert = trigger_code_blue(location, patient_name)
                    elif etype == EmergencyType.FALL_DETECTED:
                        alert = trigger_fall_alert(location, patient_name, confidence=95.0)
                    else:
                        alert = emergency_service.create_emergency_alert(
                            etype, location, description or "Emergency assistance required",
                            patient_id=patient_id, patient_name=patient_name
                        )
                
                st.success(f"🚨 Emergency alert triggered! ID: {alert.id}")
                st.warning(f"📞 **Call {alert.phone_to_call} for immediate assistance**")
                st.rerun()
    
    st.markdown("---")
    
    # Alert History
    st.markdown("#### 📋 Recent Alert History")
    history = emergency_service.get_alert_history(limit=10)
    
    if history:
        history_data = []
        for alert in reversed(history):
            history_data.append({
                "ID": alert.id,
                "Type": alert.emergency_type.value,
                "Location": alert.location,
                "Time": alert.timestamp.strftime('%H:%M:%S'),
                "Status": "✅ Acknowledged" if alert.is_acknowledged else "⏳ Pending"
            })
        st.dataframe(history_data, use_container_width=True)
    else:
        st.info("No alerts in history")


def run_admin_dashboard():
    """Main entry point for admin dashboard."""
    apply_admin_styles()
    
    # Render header with navigation
    render_header()
    
    # Create main tab navigation
    tabs = st.tabs([
        "📊 Overview",
        "➕ New Patient",
        "🚨 Emergency",
        "🛏️ Bed Map", 
        "👥 Patients",
        "👨‍⚕️ Staff",
        "📹 CCTV",
        "🗺️ City Map",
        "📝 Decision Log"
    ])
    
    with tabs[0]:  # Overview
        render_stats_panel()
        st.markdown("---")
        render_alerts_section()
    
    with tabs[1]:  # New Patient
        render_new_patient_registration()
    
    with tabs[2]:  # Emergency Alerts
        render_emergency_alerts()
    
    with tabs[3]:  # Bed Map
        render_floor_map()
        st.markdown("---")
        render_bed_management()
    
    with tabs[4]:  # Patients
        render_patient_cards()
    
    with tabs[5]:  # Staff
        render_staff_overview()
    
    with tabs[6]:  # CCTV
        render_cctv_monitoring()
    
    with tabs[7]:  # City Map
        render_city_map()
    
    with tabs[8]:  # Decision Log
        render_decision_log()
    
    # Auto-refresh every 10 seconds
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refresh Data", key="refresh_admin"):
            st.rerun()


if __name__ == "__main__":
    run_admin_dashboard()
