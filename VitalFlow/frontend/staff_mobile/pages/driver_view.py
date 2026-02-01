"""
Ambulance Driver View - Staff Mobile App
Features:
- Emergency trip start button
- Live ETA display
- Bed confirmation status
- Hospital diversion notice if ICU full
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.bed_manager import bed_manager
from backend.core_logic.ambulance_manager import ambulance_manager
from backend.core_logic.staff_manager import staff_manager
from backend.ai_services.voice_alerts import voice_service
from backend.ai_services.emergency_alerts import emergency_service, announce_emergency


def render_driver_status(staff):
    """Render driver status section."""
    if staff is None:
        st.warning("Staff data not available")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        is_on_duty = str(staff.status) in ["Available", "Busy"]
        status_emoji = "🟢" if is_on_duty else "🔴"
        st.metric(f"{status_emoji} Status", str(staff.status))
    
    with col2:
        hours_worked = staff_manager.get_hours_worked(staff.id)
        st.metric("⏱️ Hours", f"{hours_worked:.1f}h")
    
    with col3:
        if st.button("📞 Contact Dispatch"):
            st.info("Calling dispatch center...")


def render_current_trip():
    """Render current active trip if any."""
    st.markdown("### 🚑 Current Trip")
    
    # Check for active ambulance
    active_trip = st.session_state.get("active_trip", None)
    
    if not active_trip:
        st.info("No active trip")
        
        # Start new trip button
        if st.button("🚨 START EMERGENCY TRIP", key="start_trip", use_container_width=True):
            st.session_state.show_trip_form = True
        
        if st.session_state.get("show_trip_form"):
            render_trip_form()
        return
    
    # Display active trip info
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ff4444 0%, #ff6b6b 100%);
        border-radius: 15px;
        padding: 1.5rem;
        color: white;
        text-align: center;
    ">
        <h2>🚨 EMERGENCY IN PROGRESS</h2>
        <h3>{active_trip.get('patient_name', 'Unknown Patient')}</h3>
        <p>Condition: {active_trip.get('condition', 'Unknown')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ETA and navigation
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        eta = active_trip.get("eta_minutes", 10)
        # Simulate ETA countdown
        if "trip_start_time" in st.session_state:
            elapsed = (datetime.now() - st.session_state.trip_start_time).total_seconds() / 60
            remaining = max(0, eta - elapsed)
            st.metric("⏱️ ETA", f"{remaining:.0f} min")
        else:
            st.metric("⏱️ ETA", f"{eta} min")
    
    with col2:
        distance = active_trip.get("distance", 5.2)
        st.metric("📍 Distance", f"{distance} km")
    
    # Bed confirmation status
    st.markdown("---")
    st.markdown("### 🛏️ Bed Status")
    
    bed_status = active_trip.get("bed_status", "Pending")
    
    if bed_status == "Confirmed":
        st.success(f"✅ **Bed Confirmed:** {active_trip.get('reserved_bed', 'ICU-01')}")
        st.info(f"👨‍⚕️ Doctor on standby: {active_trip.get('doctor', 'Dr. Available')}")
    elif bed_status == "Pending":
        st.warning("⏳ Bed allocation in progress...")
        
        # Check ICU availability
        occupancy = bed_manager.get_bed_occupancy()
        icu_available = occupancy.get("ICU", {}).get("available", 0)
        
        if icu_available == 0:
            st.error("⚠️ ICU FULL - Tetris swap in progress")
    else:
        st.error("❌ No bed available - May need diversion")
    
    # Hospital diversion notice
    if active_trip.get("diverted"):
        st.markdown("---")
        st.error(f"""
        ### 🔄 DIVERTED
        Redirecting to: **{active_trip.get('diversion_hospital', 'City General')}**  
        Reason: {active_trip.get('diversion_reason', 'ICU Full')}
        """)
    
    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📍 Update Location", key="update_location"):
            # Simulate location update
            st.success("Location updated to dispatch")
    
    with col2:
        if st.button("🏥 Arrived at Hospital", key="arrived"):
            hospital_state.log_decision(
                "AMBULANCE_ARRIVED",
                f"Ambulance arrived with patient {active_trip.get('patient_name', 'Unknown')}",
                {"trip_id": active_trip.get('trip_id', 'unknown')}
            )
            st.session_state.active_trip = None
            st.success("Trip completed! Patient handed over.")
            st.rerun()


def render_trip_form():
    """Render form to start a new emergency trip."""
    st.markdown("### 📝 New Emergency Call")
    
    with st.form("trip_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_name = st.text_input("Patient Name", value="Emergency Patient")
            patient_age = st.number_input("Age", value=45, min_value=0, max_value=120)
        
        with col2:
            condition = st.selectbox(
                "Condition",
                ["Cardiac Emergency", "Trauma", "Respiratory Distress", 
                 "Stroke", "Accident", "Unknown Critical"]
            )
            severity = st.selectbox("Severity", ["Critical", "Serious", "Stable"])
        
        pickup_location = st.text_input("Pickup Location", value="123 Main Street")
        
        col1, col2 = st.columns(2)
        
        with col1:
            eta = st.number_input("Estimated ETA (minutes)", value=15, min_value=1, max_value=60)
        
        with col2:
            contact = st.text_input("Contact Number", value="+91 98765 43210")
        
        submitted = st.form_submit_button("🚨 START TRIP", use_container_width=True)
        
        if submitted:
            # Check bed availability
            occupancy = bed_manager.get_bed_occupancy()
            icu_available = occupancy.get("ICU", {}).get("available", 0)
            
            bed_status = "Confirmed" if icu_available > 0 else "Pending"
            
            # Create trip record
            trip = {
                "patient_name": patient_name,
                "patient_age": patient_age,
                "condition": condition,
                "severity": severity,
                "pickup_location": pickup_location,
                "eta_minutes": eta,
                "contact": contact,
                "distance": round(random.uniform(3, 15), 1),
                "bed_status": bed_status,
                "reserved_bed": "ICU-01" if bed_status == "Confirmed" else None,
                "doctor": "Dr. On Call",
                "diverted": False,
                "start_time": datetime.now().isoformat()
            }
            
            # Register with ambulance manager
            try:
                ambulance_manager.register_ambulance(
                    f"AMB-{random.randint(100, 999)}",
                    {"name": patient_name, "age": patient_age, "condition": condition},
                    eta
                )
            except Exception as e:
                pass  # Continue even if manager fails
            
            st.session_state.active_trip = trip
            st.session_state.trip_start_time = datetime.now()
            st.session_state.show_trip_form = False
            
            hospital_state.log_decision(
                "AMBULANCE_DISPATCHED",
                f"Ambulance dispatched for {patient_name} - {condition}",
                {"eta": eta, "severity": severity}
            )
            
            st.success("Trip started!")
            st.rerun()


def render_trip_history():
    """Render past trip history."""
    st.markdown("### 📋 Trip History")
    
    # Get from decision log
    trips = [
        d for d in hospital_state.decision_log
        if "AMBULANCE" in d.get("action", "").upper()
    ][-10:]
    
    if not trips:
        st.info("No recent trips")
        return
    
    for trip in reversed(trips):
        action = trip.get("action", "")
        reason = trip.get("reason", "")
        timestamp = trip.get("timestamp", "")
        
        icon = "🚑" if "DISPATCH" in action.upper() else "🏥"
        
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            padding: 0.5rem;
            border-radius: 5px;
            margin: 0.3rem 0;
        ">
            {icon} <strong>{action}</strong><br>
            <small>{reason}</small><br>
            <small style="color: #888;">{timestamp}</small>
        </div>
        """, unsafe_allow_html=True)


def render_hospital_status():
    """Render current hospital bed status for driver awareness."""
    st.markdown("### 🏥 Hospital Capacity")
    
    occupancy = bed_manager.get_bed_occupancy()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        icu = occupancy.get("ICU", {})
        icu_available = icu.get("available", 0)
        icu_total = icu.get("total", 10)
        color = "🟢" if icu_available > 2 else "🟡" if icu_available > 0 else "🔴"
        st.metric(f"{color} ICU", f"{icu_available}/{icu_total}")
    
    with col2:
        er = occupancy.get("Emergency", {})
        er_available = er.get("available", 0)
        er_total = er.get("total", 10)
        color = "🟢" if er_available > 2 else "🟡" if er_available > 0 else "🔴"
        st.metric(f"{color} ER", f"{er_available}/{er_total}")
    
    with col3:
        gen = occupancy.get("General", {})
        gen_available = gen.get("available", 0)
        gen_total = gen.get("total", 20)
        color = "🟢" if gen_available > 5 else "🟡" if gen_available > 0 else "🔴"
        st.metric(f"{color} General", f"{gen_available}/{gen_total}")
    
    # Diversion alert
    icu = occupancy.get("ICU", {})
    if icu.get("available", 0) == 0:
        st.error("⚠️ **ICU FULL** - New critical patients may be diverted")


def render_voice_alerts_driver(staff):
    """Render ElevenLabs voice alerts for ambulance drivers."""
    st.markdown("### 🔊 Voice Alerts (ElevenLabs)")
    
    phones = emergency_service.get_emergency_phone_info()
    st.info(f"📞 Emergency: **{phones['emergency']}** | Hospital: **{phones['hospital']}**")
    
    st.markdown("#### 🎤 Quick Announcements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 Emergency Inbound", key="driver_emergency", use_container_width=True):
            message = "Attention Emergency Department! Ambulance inbound with critical patient. Prepare trauma team immediately."
            audio = voice_service.text_to_speech(message, f"emergency_inbound_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 ER notified!")
        
        if st.button("🛏️ Request Bed", key="driver_request_bed", use_container_width=True):
            message = "Ambulance requesting bed confirmation for incoming patient. Please confirm ICU or Emergency bed availability."
            audio = voice_service.text_to_speech(message, f"request_bed_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Bed request sent!")
    
    with col2:
        if st.button("✅ Patient Delivered", key="driver_delivered", use_container_width=True):
            message = "Ambulance has arrived. Patient successfully delivered to Emergency Department."
            audio = voice_service.text_to_speech(message, f"patient_delivered_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Arrival announced!")
        
        if st.button("📞 Contact Dispatch", key="driver_dispatch", use_container_width=True):
            message = f"Driver requesting dispatch contact. Please respond on radio or call {phones['hospital']}"
            audio = voice_service.text_to_speech(message, f"dispatch_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Dispatch contacted!")
    
    st.markdown("---")
    st.markdown("#### 📝 Custom Announcement")
    
    custom_msg = st.text_input("Enter message", key="driver_custom_msg", placeholder="Type your announcement...")
    
    if st.button("🔊 Announce", key="driver_announce", use_container_width=True):
        if custom_msg:
            audio = voice_service.text_to_speech(custom_msg, f"custom_driver_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Announcement played!")
        else:
            st.warning("Please enter a message")


def render_driver_view(staff):
    """Main render function for ambulance driver view."""
    render_driver_status(staff)
    
    st.markdown("---")
    
    # Tabs for different sections
    tabs = st.tabs(["🚑 Current Trip", "📋 History", "🏥 Hospital Status", "🔊 Alerts"])
    
    with tabs[0]:
        render_current_trip()
    
    with tabs[1]:
        render_trip_history()
    
    with tabs[2]:
        render_hospital_status()
    
    with tabs[3]:
        render_voice_alerts_driver(staff)
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh", key="refresh_driver"):
        st.rerun()


if __name__ == "__main__":
    render_driver_view(None)
