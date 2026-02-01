"""
Doctor View - Staff Mobile App
Features:
- Punch in/out
- View assigned patients
- Daily rounds schedule
- Approve/reject ICU transfers and bed swaps
- Submit daily medical report
- Patient recovery percentage
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.bed_manager import bed_manager
from backend.core_logic.staff_manager import staff_manager
from backend.core_logic.triage_engine import triage_engine
from backend.ai_services.emergency_alerts import emergency_service, EmergencyType, announce_emergency
from backend.ai_services.voice_alerts import voice_service
from shared.models import StaffStatus


def render_punch_section(staff):
    """Render punch in/out section."""
    if staff is None:
        st.warning("Staff data not available")
        return
    
    st.markdown("### ⏰ Shift Management")
    
    col1, col2 = st.columns(2)
    
    is_punched_in = staff.status in [StaffStatus.AVAILABLE, StaffStatus.BUSY, "Available", "Busy"]
    hours_worked = staff_manager.get_hours_worked(staff.id)
    fatigue_level = staff_manager.get_fatigue_level(staff.id)
    
    with col1:
        if not is_punched_in:
            if st.button("🟢 Punch In", key="punch_in", use_container_width=True):
                success = staff_manager.punch_in(staff.id)
                if success:
                    st.success("✅ Punched in successfully!")
                    st.rerun()
                else:
                    st.error("Failed to punch in")
        else:
            if st.button("🔴 Punch Out", key="punch_out", use_container_width=True):
                success = staff_manager.punch_out(staff.id)
                if success:
                    st.success("✅ Punched out successfully!")
                    st.rerun()
                else:
                    st.error("Failed to punch out")
    
    with col2:
        # Shift status
        status_colors = {
            "fresh": "🟢",
            "normal": "🟡",
            "tired": "🟠",
            "fatigued": "🔴"
        }
        color = status_colors.get(fatigue_level, "⚪")
        st.metric(f"{color} Fatigue Level", fatigue_level.upper())
    
    # Fatigue warning
    warning = staff_manager.get_fatigue_warning(staff.id)
    if warning:
        st.warning(warning)


def render_assigned_patients(staff):
    """Render list of assigned patients."""
    st.markdown("### 👥 My Patients")
    
    # Get patients assigned to this doctor
    assigned_patients = [
        p for p in hospital_state.patients.values()
        if p.assigned_doctor_id == staff.id
    ]
    
    if not assigned_patients:
        st.info("No patients currently assigned")
        return
    
    for patient in assigned_patients:
        status = str(patient.status)
        status_colors = {
            "Critical": "🔴",
            "Serious": "🟠",
            "Stable": "🟢",
            "Recovering": "🔵"
        }
        status_icon = status_colors.get(status, "⚪")
        
        priority = triage_engine.calculate_priority(patient)
        
        with st.expander(f"{status_icon} {patient.name} - {patient.diagnosis or 'No diagnosis'}", expanded=status == "Critical"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {patient.id}")
                st.write(f"**Age:** {patient.age} | **Gender:** {patient.gender}")
                st.write(f"**Bed:** {patient.bed_id or 'Not assigned'}")
                st.write(f"**Status:** {status}")
            
            with col2:
                st.metric("SpO2", f"{patient.spo2}%")
                st.metric("Heart Rate", f"{patient.heart_rate} bpm")
            
            # Calculate recovery percentage
            recovery_pct = calculate_recovery_percentage(patient)
            st.progress(recovery_pct / 100, text=f"Recovery: {recovery_pct}%")
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📝 Add Note", key=f"note_{patient.id}"):
                    st.session_state[f"adding_note_{patient.id}"] = True
            
            with col2:
                if status == "Critical" and patient.bed_id:
                    bed = hospital_state.beds.get(patient.bed_id)
                    if bed and str(bed.bed_type) != "ICU":
                        if st.button("🚨 Request ICU", key=f"icu_{patient.id}"):
                            st.info("ICU transfer request submitted")
            
            with col3:
                if status in ["Stable", "Recovering"]:
                    if st.button("✅ Ready to Discharge", key=f"discharge_{patient.id}"):
                        st.info("Discharge assessment initiated")
            
            # Note input
            if st.session_state.get(f"adding_note_{patient.id}"):
                note = st.text_area("Clinical Note", key=f"note_text_{patient.id}")
                if st.button("Save Note", key=f"save_note_{patient.id}"):
                    if note:
                        patient.notes.append(f"[{datetime.now().strftime('%d %b %H:%M')}] Dr. {staff.name}: {note}")
                        hospital_state.save()
                        st.success("Note saved")
                        st.session_state[f"adding_note_{patient.id}"] = False
                        st.rerun()


def calculate_recovery_percentage(patient) -> int:
    """Calculate patient recovery percentage based on vitals and status."""
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
    
    # SpO2 contribution (up to +15)
    if patient.spo2 >= 98:
        vital_bonus += 15
    elif patient.spo2 >= 95:
        vital_bonus += 10
    elif patient.spo2 >= 90:
        vital_bonus += 5
    
    # Heart rate contribution (up to +10)
    if 60 <= patient.heart_rate <= 100:
        vital_bonus += 10
    elif 55 <= patient.heart_rate <= 110:
        vital_bonus += 5
    
    return min(100, base + vital_bonus)


def render_rounds_schedule(staff):
    """Render daily rounds schedule."""
    st.markdown("### 📋 Daily Rounds")
    
    # Generate schedule based on assigned patients
    assigned_patients = [
        p for p in hospital_state.patients.values()
        if p.assigned_doctor_id == staff.id
    ]
    
    # Sort by priority
    assigned_patients.sort(key=lambda p: triage_engine.calculate_priority(p))
    
    if not assigned_patients:
        st.info("No rounds scheduled - no patients assigned")
        return
    
    st.markdown("**Today's Rounds Order** (by priority)")
    
    for idx, patient in enumerate(assigned_patients, 1):
        status = str(patient.status)
        priority = triage_engine.calculate_priority(patient)
        priority_label = triage_engine.get_priority_label(priority)
        
        completed = st.session_state.get(f"round_{patient.id}", False)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            status_emoji = "✅" if completed else f"#{idx}"
            st.write(f"{status_emoji} **{patient.name}** - {patient.bed_id or 'No bed'}")
        
        with col2:
            st.write(priority_label)
        
        with col3:
            if not completed:
                if st.button("Done", key=f"round_done_{patient.id}"):
                    st.session_state[f"round_{patient.id}"] = True
                    st.rerun()


def render_pending_approvals():
    """Render pending approvals section."""
    st.markdown("### ✅ Pending Approvals")
    
    # Get pending decisions that need doctor approval
    pending = [
        d for d in hospital_state.decision_log
        if "PENDING" in d.get("action", "").upper() or
           "SWAP" in d.get("action", "").upper() and
           "APPROVED" not in d.get("action", "").upper()
    ][-5:]  # Last 5
    
    if not pending:
        st.success("No pending approvals")
        return
    
    for idx, decision in enumerate(pending):
        action = decision.get("action", "Unknown")
        reason = decision.get("reason", "")
        timestamp = decision.get("timestamp", "")
        
        st.markdown(f"""
        <div style="
            background: rgba(255, 165, 0, 0.1);
            border-left: 3px solid #ffa500;
            padding: 1rem;
            border-radius: 5px;
            margin: 0.5rem 0;
        ">
            <strong>{action}</strong><br>
            <small>{reason}</small>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Approve", key=f"approve_dr_{idx}"):
                hospital_state.log_decision(
                    f"{action}_APPROVED",
                    f"Approved by doctor",
                    {"original_action": action}
                )
                st.success("Approved!")
                st.rerun()
        
        with col2:
            if st.button("❌ Reject", key=f"reject_dr_{idx}"):
                hospital_state.log_decision(
                    f"{action}_REJECTED",
                    f"Rejected by doctor",
                    {"original_action": action}
                )
                st.error("Rejected")
                st.rerun()


def render_daily_report_form(staff):
    """Render daily medical report submission form."""
    st.markdown("### 📝 Submit Daily Report")
    
    with st.form("daily_report_form"):
        st.markdown("**End of Shift Summary**")
        
        patients_seen = st.number_input("Patients Seen Today", min_value=0, max_value=50, value=5)
        
        critical_events = st.text_area(
            "Critical Events",
            placeholder="Document any critical events or emergencies..."
        )
        
        handover_notes = st.text_area(
            "Handover Notes",
            placeholder="Notes for the next shift..."
        )
        
        concerns = st.text_area(
            "Concerns/Issues",
            placeholder="Any concerns about patients or resources..."
        )
        
        submitted = st.form_submit_button("📤 Submit Report", use_container_width=True)
        
        if submitted:
            hospital_state.log_decision(
                "DAILY_REPORT_SUBMITTED",
                f"Dr. {staff.name} submitted daily report",
                {
                    "doctor_id": staff.id,
                    "patients_seen": patients_seen,
                    "has_critical_events": len(critical_events) > 0,
                    "has_concerns": len(concerns) > 0
                }
            )
            st.success("✅ Daily report submitted successfully!")


def render_voice_alerts_section(staff):
    """Render voice alerts section with ElevenLabs TTS."""
    st.markdown("### 🔊 Voice Alerts (ElevenLabs)")
    
    # Emergency phone info
    phones = emergency_service.get_emergency_phone_info()
    st.info(f"📞 Emergency: **{phones['emergency']}** | Hospital: **{phones['hospital']}**")
    
    st.markdown("#### 🎤 Quick Voice Announcements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 Code Blue Alert", key="dr_code_blue", use_container_width=True):
            alert = emergency_service.code_blue_alert(
                location=f"Doctor {staff.name if staff else 'Station'}",
                patient_name="Emergency Patient"
            )
            st.success(f"🔊 Code Blue announced! Call {alert.phone_to_call}")
        
        if st.button("📢 Call Nurse", key="dr_call_nurse", use_container_width=True):
            message = f"Nurse assistance required at Doctor {staff.name if staff else ''} station immediately"
            audio = voice_service.text_to_speech(message, f"call_nurse_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Nurse call announced!")
    
    with col2:
        if st.button("⚠️ Critical Patient Alert", key="dr_critical", use_container_width=True):
            message = f"Attention! Critical patient requires immediate attention from Dr. {staff.name if staff else 'on duty'}"
            audio = voice_service.text_to_speech(message, f"critical_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Critical alert announced!")
        
        if st.button("🏥 Page Admin", key="dr_page_admin", use_container_width=True):
            message = f"Admin team please contact Doctor {staff.name if staff else 'on duty'} immediately"
            audio = voice_service.text_to_speech(message, f"page_admin_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Admin paged!")
    
    st.markdown("---")
    st.markdown("#### 📝 Custom Announcement")
    
    custom_message = st.text_input("Enter custom message", key="dr_custom_msg", placeholder="Type your announcement...")
    
    if st.button("🔊 Announce", key="dr_announce_custom", use_container_width=True):
        if custom_message:
            audio = voice_service.text_to_speech(custom_message, f"custom_dr_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Announcement played!")
        else:
            st.warning("Please enter a message")


def render_doctor_view(staff):
    """Main render function for doctor view."""
    # Tabs for different sections
    tabs = st.tabs(["🏥 My Patients", "📋 Rounds", "✅ Approvals", "🔊 Alerts", "📝 Report"])
    
    with tabs[0]:
        render_punch_section(staff)
        st.markdown("---")
        render_assigned_patients(staff)
    
    with tabs[1]:
        render_rounds_schedule(staff)
    
    with tabs[2]:
        render_pending_approvals()
    
    with tabs[3]:
        render_voice_alerts_section(staff)
    
    with tabs[4]:
        render_daily_report_form(staff)
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh", key="refresh_doctor"):
        st.rerun()


if __name__ == "__main__":
    # For testing
    render_doctor_view(None)
