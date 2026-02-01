"""
Nurse View - Staff Mobile App
Features:
- Task list (medicine preparation from medicine_ai)
- Receive voice alerts
- Mark tasks complete
- Emergency trolley checklist
- Patient vitals monitoring
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.staff_manager import staff_manager
from backend.core_logic.triage_engine import triage_engine
from backend.ai_services.medicine_ai import medicine_ai
from backend.ai_services.voice_alerts import voice_service
from backend.ai_services.emergency_alerts import emergency_service, EmergencyType, announce_emergency
from shared.models import StaffStatus


def render_shift_status(staff):
    """Render current shift status."""
    if staff is None:
        st.warning("Staff data not available")
        return
    
    col1, col2, col3 = st.columns(3)
    
    hours_worked = staff_manager.get_hours_worked(staff.id)
    fatigue_level = staff_manager.get_fatigue_level(staff.id)
    patient_count = staff_manager.get_patient_count(staff.id)
    
    with col1:
        is_on_duty = str(staff.status) in ["Available", "Busy"]
        if is_on_duty:
            if st.button("🔴 End Shift", key="nurse_punch_out"):
                staff_manager.punch_out(staff.id)
                st.rerun()
        else:
            if st.button("🟢 Start Shift", key="nurse_punch_in"):
                staff_manager.punch_in(staff.id)
                st.rerun()
    
    with col2:
        fatigue_colors = {"fresh": "🟢", "normal": "🟡", "tired": "🟠", "fatigued": "🔴"}
        st.metric(f"{fatigue_colors.get(fatigue_level, '⚪')} Hours", f"{hours_worked:.1f}h")
    
    with col3:
        st.metric("👥 Patients", patient_count)
    
    # Fatigue warning
    warning = staff_manager.get_fatigue_warning(staff.id)
    if warning:
        st.warning(warning)


def render_task_list(staff):
    """Render medicine preparation and task list."""
    st.markdown("### 📋 Task List")
    
    # Get assigned patients
    assigned_patients = [
        p for p in hospital_state.patients.values()
        if p.assigned_nurse_id == staff.id
    ]
    
    if not assigned_patients:
        st.info("No patients currently assigned")
        return
    
    # Generate tasks for each patient
    for patient in assigned_patients:
        status = str(patient.status)
        status_emoji = {"Critical": "🔴", "Serious": "🟠", "Stable": "🟢", "Recovering": "🔵"}.get(status, "⚪")
        
        with st.expander(f"{status_emoji} {patient.name} - Tasks", expanded=status in ["Critical", "Serious"]):
            # Get AI-generated preparation checklist
            try:
                checklist = medicine_ai.get_preparation_checklist(patient)
            except Exception as e:
                checklist = get_fallback_checklist(patient)
            
            # Medications
            st.markdown("**💊 Medications:**")
            medications = checklist.get("medications", [])
            for idx, med in enumerate(medications):
                if isinstance(med, dict):
                    med_name = med.get("name", "Unknown")
                    dosage = med.get("dosage", "")
                    timing = med.get("timing", "")
                else:
                    med_name = str(med)
                    dosage = ""
                    timing = ""
                
                task_key = f"med_{patient.id}_{idx}"
                completed = st.session_state.get(task_key, False)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    checkbox = st.checkbox(
                        f"{med_name} {dosage} - {timing}",
                        value=completed,
                        key=task_key
                    )
                with col2:
                    if checkbox and not completed:
                        st.session_state[task_key] = True
                        hospital_state.log_decision(
                            "MEDICINE_GIVEN",
                            f"Medicine {med_name} given to {patient.name}",
                            {"nurse_id": staff.id, "patient_id": patient.id}
                        )
            
            # Equipment
            st.markdown("**🔧 Equipment:**")
            equipment = checklist.get("equipment", [])
            for idx, equip in enumerate(equipment):
                equip_name = equip if isinstance(equip, str) else str(equip)
                task_key = f"equip_{patient.id}_{idx}"
                st.checkbox(equip_name, key=task_key)
            
            # Vitals check
            st.markdown("**📊 Vital Signs (Every 2 hours):**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("SpO2", f"{patient.spo2}%")
                st.metric("BP", getattr(patient, 'blood_pressure', '120/80'))
            
            with col2:
                st.metric("HR", f"{patient.heart_rate} bpm")
                st.metric("Temp", f"{getattr(patient, 'temperature', 98.6)}°F")
            
            # Quick actions
            if st.button(f"📊 Record Vitals", key=f"vitals_{patient.id}"):
                st.session_state[f"recording_vitals_{patient.id}"] = True
            
            if st.session_state.get(f"recording_vitals_{patient.id}"):
                with st.form(f"vitals_form_{patient.id}"):
                    new_spo2 = st.number_input("SpO2", value=float(patient.spo2), min_value=50.0, max_value=100.0)
                    new_hr = st.number_input("Heart Rate", value=int(patient.heart_rate), min_value=30, max_value=200)
                    new_bp = st.text_input("Blood Pressure", value=getattr(patient, 'blood_pressure', '120/80'))
                    new_temp = st.number_input("Temperature", value=getattr(patient, 'temperature', 98.6), min_value=90.0, max_value=110.0)
                    
                    if st.form_submit_button("Save Vitals"):
                        triage_engine.update_patient_vitals(patient.id, {
                            "spo2": new_spo2,
                            "heart_rate": new_hr,
                            "blood_pressure": new_bp,
                            "temperature": new_temp
                        })
                        st.success("Vitals updated!")
                        st.session_state[f"recording_vitals_{patient.id}"] = False
                        st.rerun()


def get_fallback_checklist(patient) -> dict:
    """Fallback checklist when AI is unavailable."""
    status = str(patient.status)
    
    if status == "Critical":
        return {
            "medications": [
                {"name": "Emergency medication", "dosage": "As prescribed", "timing": "STAT"},
                {"name": "IV fluids", "dosage": "500ml", "timing": "Continuous"}
            ],
            "equipment": ["Cardiac monitor", "Oxygen mask", "Crash cart nearby", "IV line check"],
            "urgency": "CRITICAL"
        }
    elif status == "Serious":
        return {
            "medications": [
                {"name": "Prescribed medication", "dosage": "As per chart", "timing": "Every 6h"}
            ],
            "equipment": ["Vitals monitor", "Oxygen if needed"],
            "urgency": "HIGH"
        }
    else:
        return {
            "medications": [
                {"name": "Regular medication", "dosage": "As prescribed", "timing": "Scheduled"}
            ],
            "equipment": ["Standard vitals check"],
            "urgency": "ROUTINE"
        }


def render_voice_alerts(staff):
    """Render voice alerts section."""
    st.markdown("### 🔊 Voice Alerts")
    
    # Recent alerts (would come from voice_service in production)
    recent_alerts = st.session_state.get("voice_alerts", [])
    
    if not recent_alerts:
        st.success("✅ No pending voice alerts")
    else:
        for alert in recent_alerts:
            st.warning(f"🔊 {alert}")
    
    # Test voice alert
    st.markdown("**Test Voice Alert:**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔔 Code Blue Alert", key="test_code_blue"):
            try:
                voice_service.generate_alert("code_blue", patient_name="Test Patient", location="ICU-01")
                st.info("🔊 Code Blue alert generated")
            except:
                st.info("🔊 Voice alert would be played here")
    
    with col2:
        if st.button("💊 Medicine Reminder", key="test_med"):
            st.info("🔊 Medicine reminder would be played")


def render_emergency_trolley():
    """Render emergency trolley checklist."""
    st.markdown("### 🚨 Emergency Trolley Checklist")
    
    checklist_items = [
        ("Defibrillator", "Check charge and pads"),
        ("Oxygen supply", "Check tank level"),
        ("Ambu bag", "Inspect for damage"),
        ("Laryngoscope", "Check light"),
        ("IV supplies", "Stock check"),
        ("Emergency medications", "Check expiry dates"),
        ("Gloves (all sizes)", "Stock check"),
        ("Syringes", "Various sizes available"),
        ("Suction equipment", "Functional test"),
        ("ECG leads", "Complete set")
    ]
    
    all_checked = True
    
    for item, description in checklist_items:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            checked = st.checkbox(f"**{item}** - {description}", key=f"trolley_{item}")
            if not checked:
                all_checked = False
    
    st.markdown("---")
    
    if all_checked:
        st.success("✅ Emergency trolley fully checked")
        if st.button("📝 Submit Checklist", key="submit_trolley"):
            hospital_state.log_decision(
                "EMERGENCY_TROLLEY_CHECKED",
                f"Emergency trolley verified",
                {"timestamp": datetime.now().isoformat()}
            )
            st.success("Checklist submitted!")
    else:
        st.warning("⚠️ Complete all items before submitting")


def render_elevenlabs_alerts(staff):
    """Render ElevenLabs voice alerts section for nurses."""
    st.markdown("### 🔊 Voice Alerts (ElevenLabs)")
    
    phones = emergency_service.get_emergency_phone_info()
    st.info(f"📞 Emergency: **{phones['emergency']}** | Hospital: **{phones['hospital']}**")
    
    st.markdown("#### 🎤 Quick Voice Announcements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 Code Blue", key="nurse_code_blue", use_container_width=True):
            alert = emergency_service.code_blue_alert(
                location=f"Nurse {staff.name if staff else ''} Station",
                patient_name="Emergency Patient"
            )
            st.success(f"🔊 Code Blue! Call {alert.phone_to_call}")
        
        if st.button("👨‍⚕️ Call Doctor", key="nurse_call_doctor", use_container_width=True):
            message = f"Doctor please respond to Nurse {staff.name if staff else ''} station immediately"
            audio = voice_service.text_to_speech(message, f"call_doctor_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Doctor called!")
    
    with col2:
        if st.button("🛏️ Bed Assistance", key="nurse_bed_assist", use_container_width=True):
            message = "Ward staff assistance required for patient transfer"
            audio = voice_service.text_to_speech(message, f"bed_assist_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Assistance requested!")
        
        if st.button("💊 Medicine Ready", key="nurse_med_ready", use_container_width=True):
            message = f"Medication prepared and ready for administration by Nurse {staff.name if staff else 'on duty'}"
            audio = voice_service.text_to_speech(message, f"med_ready_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Medicine notification sent!")
    
    st.markdown("---")
    st.markdown("#### 📝 Custom Announcement")
    
    custom_msg = st.text_input("Enter message", key="nurse_custom_msg", placeholder="Type your announcement...")
    
    if st.button("🔊 Announce", key="nurse_announce", use_container_width=True):
        if custom_msg:
            audio = voice_service.text_to_speech(custom_msg, f"custom_nurse_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Announcement played!")
        else:
            st.warning("Please enter a message")


def render_nurse_view(staff):
    """Main render function for nurse view."""
    render_shift_status(staff)
    
    st.markdown("---")
    
    # Tabs for different sections
    tabs = st.tabs(["📋 Tasks", "🔊 Voice Alerts", "🎤 ElevenLabs", "🚨 Emergency"])
    
    with tabs[0]:
        render_task_list(staff)
    
    with tabs[1]:
        render_voice_alerts(staff)
    
    with tabs[2]:
        render_elevenlabs_alerts(staff)
    
    with tabs[3]:
        render_emergency_trolley()
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh", key="refresh_nurse"):
        st.rerun()


if __name__ == "__main__":
    render_nurse_view(None)
