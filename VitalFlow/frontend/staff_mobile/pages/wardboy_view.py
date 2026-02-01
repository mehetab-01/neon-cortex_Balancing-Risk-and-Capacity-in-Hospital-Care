"""
Ward Boy/Girl View - Staff Mobile App
Features:
- Patient transfer tickets
- Cleaning & food delivery checklist
- Mark tasks complete
- Equipment transport requests
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.staff_manager import staff_manager
from backend.ai_services.voice_alerts import voice_service
from backend.ai_services.emergency_alerts import emergency_service, announce_emergency
from shared.models import StaffStatus


def render_shift_status(staff):
    """Render shift status for ward staff."""
    if staff is None:
        st.warning("Staff data not available")
        return
    
    col1, col2, col3 = st.columns(3)
    
    hours_worked = staff_manager.get_hours_worked(staff.id)
    
    with col1:
        is_on_duty = str(staff.status) in ["Available", "Busy"]
        if is_on_duty:
            if st.button("🔴 End Shift", key="ward_punch_out"):
                staff_manager.punch_out(staff.id)
                st.rerun()
        else:
            if st.button("🟢 Start Shift", key="ward_punch_in"):
                staff_manager.punch_in(staff.id)
                st.rerun()
    
    with col2:
        st.metric("⏱️ Hours", f"{hours_worked:.1f}h")
    
    with col3:
        floor = staff.floor_assigned or "All"
        st.metric("🏥 Floor", floor)


def render_transfer_tickets():
    """Render patient transfer tickets."""
    st.markdown("### 🚶 Patient Transfer Tickets")
    
    # Generate transfer tickets from bed swaps and discharges
    # In production, these would come from a queue
    
    # Check for pending transfers in decision log
    pending_transfers = []
    
    for decision in hospital_state.decision_log[-20:]:
        action = decision.get("action", "")
        if "SWAP" in action.upper() or "TRANSFER" in action.upper():
            if "COMPLETED" not in action.upper():
                pending_transfers.append(decision)
    
    # Add sample transfers if none found
    if not pending_transfers:
        # Check for patients that might need transfer
        for patient in hospital_state.patients.values():
            if patient.bed_id:
                bed = hospital_state.beds.get(patient.bed_id)
                if bed:
                    # Example: patient status changed and needs bed change
                    if str(patient.status) == "Recovering" and str(bed.bed_type) == "ICU":
                        pending_transfers.append({
                            "action": "TRANSFER_REQUEST",
                            "reason": f"Move {patient.name} from ICU to General Ward (recovering)",
                            "details": {
                                "patient_id": patient.id,
                                "patient_name": patient.name,
                                "from_bed": bed.id,
                                "from_type": str(bed.bed_type),
                                "to_type": "General"
                            }
                        })
    
    if not pending_transfers:
        st.success("✅ No pending transfer tickets")
        return
    
    for idx, transfer in enumerate(pending_transfers[:5]):
        details = transfer.get("details", {})
        patient_name = details.get("patient_name", "Unknown Patient")
        from_bed = details.get("from_bed", "Unknown")
        to_type = details.get("to_type", "Unknown")
        
        st.markdown(f"""
        <div style="
            background: rgba(33, 150, 243, 0.1);
            border-left: 4px solid #2196f3;
            padding: 1rem;
            border-radius: 5px;
            margin: 0.5rem 0;
        ">
            <strong>🚶 Patient Transfer</strong><br>
            <strong>{patient_name}</strong><br>
            From: {from_bed} → To: {to_type}<br>
            <small>{transfer.get('reason', '')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🏃 Start Transfer", key=f"start_transfer_{idx}"):
                st.session_state[f"transfer_in_progress_{idx}"] = True
                st.info("Transfer in progress...")
        
        with col2:
            if st.session_state.get(f"transfer_in_progress_{idx}"):
                if st.button("✅ Complete", key=f"complete_transfer_{idx}"):
                    hospital_state.log_decision(
                        "TRANSFER_COMPLETED",
                        f"Patient transfer completed by ward staff",
                        {"original_transfer": transfer.get("action")}
                    )
                    st.success("Transfer completed!")
                    st.session_state[f"transfer_in_progress_{idx}"] = False
                    st.rerun()


def render_cleaning_checklist():
    """Render cleaning and sanitation checklist."""
    st.markdown("### 🧹 Cleaning Checklist")
    
    # Get beds that need cleaning (recently vacated)
    beds_to_clean = []
    
    for bed in hospital_state.beds.values():
        if not bed.is_occupied:
            # Check if recently sanitized
            if bed.last_sanitized:
                try:
                    if isinstance(bed.last_sanitized, str):
                        last_clean = datetime.fromisoformat(bed.last_sanitized)
                    else:
                        last_clean = bed.last_sanitized
                    
                    hours_since = (datetime.now() - last_clean).total_seconds() / 3600
                    if hours_since > 4:  # More than 4 hours
                        beds_to_clean.append((bed, hours_since))
                except:
                    beds_to_clean.append((bed, 24))  # Unknown time
            else:
                beds_to_clean.append((bed, 24))  # Never cleaned
    
    if not beds_to_clean:
        st.success("✅ All beds are clean")
    else:
        beds_to_clean.sort(key=lambda x: x[1], reverse=True)  # Most urgent first
        
        for bed, hours in beds_to_clean[:10]:
            urgency = "🔴" if hours > 8 else "🟡" if hours > 4 else "🟢"
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"{urgency} **{bed.id}** - {bed.ward}, Floor {bed.floor}")
            
            with col2:
                st.write(f"{hours:.1f}h ago")
            
            with col3:
                if st.button("✅ Clean", key=f"clean_{bed.id}"):
                    bed.last_sanitized = datetime.now()
                    hospital_state.save()
                    st.success(f"Bed {bed.id} marked as cleaned!")
                    st.rerun()


def render_food_delivery():
    """Render food delivery checklist."""
    st.markdown("### 🍽️ Food Delivery Schedule")
    
    current_hour = datetime.now().hour
    
    # Determine current meal
    if 6 <= current_hour < 10:
        meal = "Breakfast"
        emoji = "🍳"
    elif 12 <= current_hour < 15:
        meal = "Lunch"
        emoji = "🍛"
    elif 17 <= current_hour < 20:
        meal = "Dinner"
        emoji = "🍽️"
    else:
        meal = "Snacks/Other"
        emoji = "🍎"
    
    st.markdown(f"**Current Meal: {emoji} {meal}**")
    
    # List patients for food delivery
    patients = list(hospital_state.patients.values())
    
    if not patients:
        st.info("No patients for food delivery")
        return
    
    st.markdown("**Patient Meal Status:**")
    
    for patient in patients:
        if str(patient.status) == "Discharged":
            continue
        
        meal_key = f"meal_{patient.id}_{meal}"
        delivered = st.session_state.get(meal_key, False)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            diet_type = "Normal"  # Would come from patient record
            st.write(f"**{patient.name}** - {patient.bed_id or 'No bed'}")
            st.write(f"Diet: {diet_type}")
        
        with col2:
            status_emoji = "✅" if delivered else "⏳"
            st.write(f"{status_emoji} {meal}")
        
        with col3:
            if not delivered:
                if st.button("Deliver", key=meal_key):
                    st.session_state[meal_key] = True
                    hospital_state.log_decision(
                        "MEAL_DELIVERED",
                        f"{meal} delivered to {patient.name}",
                        {"patient_id": patient.id, "meal": meal}
                    )
                    st.rerun()


def render_equipment_transport():
    """Render equipment transport requests."""
    st.markdown("### 🔧 Equipment Transport")
    
    # Sample equipment requests
    equipment_requests = [
        {"item": "Wheelchair", "from": "Storage", "to": "Room 205", "urgent": False},
        {"item": "Oxygen Cylinder", "from": "Supply", "to": "ICU-03", "urgent": True},
        {"item": "IV Stand", "from": "ER", "to": "General Ward", "urgent": False},
    ]
    
    # Filter to show only incomplete
    pending_equipment = [
        r for r in equipment_requests
        if not st.session_state.get(f"equip_done_{r['item']}_{r['to']}", False)
    ]
    
    if not pending_equipment:
        st.success("✅ No pending equipment transport")
        return
    
    for req in pending_equipment:
        urgency = "🔴 URGENT" if req["urgent"] else "🟢"
        
        st.markdown(f"""
        <div style="
            background: rgba(255, 152, 0, 0.1);
            border-left: 4px solid {'#f44336' if req['urgent'] else '#4caf50'};
            padding: 1rem;
            border-radius: 5px;
            margin: 0.5rem 0;
        ">
            <strong>{urgency} {req['item']}</strong><br>
            {req['from']} → {req['to']}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"✅ Delivered", key=f"equip_btn_{req['item']}_{req['to']}"):
            st.session_state[f"equip_done_{req['item']}_{req['to']}"] = True
            st.success("Equipment delivered!")
            st.rerun()


def render_voice_alerts_ward(staff):
    """Render ElevenLabs voice alerts for ward staff."""
    st.markdown("### 🔊 Voice Alerts (ElevenLabs)")
    
    phones = emergency_service.get_emergency_phone_info()
    st.info(f"📞 Emergency: **{phones['emergency']}** | Hospital: **{phones['hospital']}**")
    
    st.markdown("#### 🎤 Quick Announcements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 Emergency Help", key="ward_emergency", use_container_width=True):
            alert = announce_emergency(
                f"Ward staff emergency at Floor {staff.floor_assigned if staff and staff.floor_assigned else 'unknown'}",
                location=f"Ward Station"
            )
            st.success(f"🔊 Emergency! Call {alert.phone_to_call}")
        
        if st.button("🛏️ Transfer Ready", key="ward_transfer_ready", use_container_width=True):
            message = "Patient transfer ready. Ward staff standing by for movement."
            audio = voice_service.text_to_speech(message, f"transfer_ready_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Transfer notification sent!")
    
    with col2:
        if st.button("🧹 Cleaning Complete", key="ward_clean_done", use_container_width=True):
            message = "Room cleaning completed. Bed is sanitized and ready for new patient."
            audio = voice_service.text_to_speech(message, f"clean_done_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Cleaning notification sent!")
        
        if st.button("👨‍⚕️ Call Nurse", key="ward_call_nurse", use_container_width=True):
            message = "Nurse assistance required at ward station"
            audio = voice_service.text_to_speech(message, f"call_nurse_ward_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Nurse called!")
    
    st.markdown("---")
    st.markdown("#### 📝 Custom Announcement")
    
    custom_msg = st.text_input("Enter message", key="ward_custom_msg", placeholder="Type your announcement...")
    
    if st.button("🔊 Announce", key="ward_announce", use_container_width=True):
        if custom_msg:
            audio = voice_service.text_to_speech(custom_msg, f"custom_ward_{datetime.now().strftime('%H%M%S')}")
            if audio:
                voice_service.play_audio(audio)
            st.success("🔊 Announcement played!")
        else:
            st.warning("Please enter a message")


def render_wardboy_view(staff):
    """Main render function for ward boy/girl view."""
    render_shift_status(staff)
    
    st.markdown("---")
    
    # Tabs for different sections
    tabs = st.tabs(["🚶 Transfers", "🧹 Cleaning", "🍽️ Food", "🔧 Equipment", "🔊 Alerts"])
    
    with tabs[0]:
        render_transfer_tickets()
    
    with tabs[1]:
        render_cleaning_checklist()
    
    with tabs[2]:
        render_food_delivery()
    
    with tabs[3]:
        render_equipment_transport()
    
    with tabs[4]:
        render_voice_alerts_ward(staff)
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh", key="refresh_ward"):
        st.rerun()


if __name__ == "__main__":
    render_wardboy_view(None)
