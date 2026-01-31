"""
VitalFlow AI - Driver View
Mobile interface for ambulance drivers with trip management,
status updates, and hospital confirmation
"""
import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Mobile styling - UI STYLE ONLY
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {max-width: 480px; margin: 0 auto; background: #F4F7FA;}
    
    /* Driver header - UI STYLE ONLY */
    .driver-header {
        background: #2F80ED;
        color: white;
        padding: 24px 20px;
        border-radius: 16px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(47, 128, 237, 0.15);
    }
    
    /* Status card - UI STYLE ONLY */
    .status-card {
        background: #E9EEF3;
        border-radius: 16px;
        padding: 35px 25px;
        margin: 24px 0;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .status-idle {
        border: 2px solid #CBD5E1;
    }
    
    .status-enroute {
        border: 2px solid #2F80ED;
        animation: pulse-border-blue 2s infinite;
    }
    
    .status-loaded {
        border: 2px solid #F2994A;
    }
    
    .status-arriving {
        border: 2px solid #27AE60;
        animation: pulse-border-green 1.5s infinite;
    }
    
    @keyframes pulse-border-blue {
        0%, 100% { box-shadow: 0 0 0 0 rgba(47, 128, 237, 0.3), 0 2px 8px rgba(0, 0, 0, 0.08); }
        50% { box-shadow: 0 0 0 8px rgba(47, 128, 237, 0), 0 2px 8px rgba(0, 0, 0, 0.08); }
    }
    
    @keyframes pulse-border-green {
        0%, 100% { box-shadow: 0 0 0 0 rgba(39, 174, 96, 0.3), 0 2px 8px rgba(0, 0, 0, 0.08); }
        50% { box-shadow: 0 0 0 8px rgba(39, 174, 96, 0), 0 2px 8px rgba(0, 0, 0, 0.08); }
    }
    
    /* Emergency button - UI STYLE ONLY */
    .emergency-btn button {
        background: #EB5757 !important;
        color: white !important;
        height: 90px !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(235, 87, 87, 0.25) !important;
        border: none !important;
    }
    
    .emergency-btn button:hover {
        background: #D64545 !important;
    }
    
    /* Info row - UI STYLE ONLY */
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 14px 18px;
        background: #E9EEF3;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #CBD5E1;
    }
    
    /* Hospital confirmed - UI STYLE ONLY */
    .hospital-confirmed {
        background: rgba(39, 174, 96, 0.1);
        border: 1px solid rgba(39, 174, 96, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    }
    
    /* ETA display - UI STYLE ONLY */
    .eta-display {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 14px;
        padding: 28px;
        margin: 20px 0;
        text-align: center;
    }
    
    .eta-value {
        font-size: 48px;
        font-weight: 800;
        color: #2F80ED;
    }
    
    /* Next state button - UI STYLE ONLY */
    .next-state-btn button {
        background: #2F80ED !important;
        color: white !important;
        height: 70px !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(47, 128, 237, 0.2) !important;
        border: none !important;
    }
    
    .next-state-btn button:hover {
        background: #2563EB !important;
    }
    
    /* End trip button - UI STYLE ONLY */
    .end-trip-btn button {
        background: #27AE60 !important;
        color: white !important;
        height: 70px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(39, 174, 96, 0.2) !important;
        border: none !important;
    }
    
    .end-trip-btn button:hover {
        background: #219653 !important;
    }
    
    /* Section headers - UI STYLE ONLY */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 24px 0 16px 0;
    }
    
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #1F2937;
    }
    
    /* Trip detail card - UI STYLE ONLY */
    .trip-detail {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    }
    
    .detail-label {
        font-size: 11px;
        color: #2F80ED;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    
    .detail-value {
        font-size: 15px;
        color: #1F2937;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Trip state configuration - UI STYLE ONLY
TRIP_STATES = {
    "IDLE": {
        "icon": "🅿️",
        "label": "Ready",
        "color": "#4B5563",
        "description": "Waiting for dispatch",
        "class": "status-idle"
    },
    "EN_ROUTE": {
        "icon": "🚑",
        "label": "En Route to Patient",
        "color": "#2F80ED",
        "description": "Heading to pickup location",
        "class": "status-enroute"
    },
    "PATIENT_LOADED": {
        "icon": "👤",
        "label": "Patient Loaded",
        "color": "#F2994A",
        "description": "Transporting to hospital",
        "class": "status-loaded"
    },
    "ARRIVING": {
        "icon": "🏥",
        "label": "Arriving at Hospital",
        "color": "#27AE60",
        "description": "Almost there",
        "class": "status-arriving"
    },
    "COMPLETED": {
        "icon": "✅",
        "label": "Trip Completed",
        "color": "#2F80ED",
        "description": "Patient delivered",
        "class": "status-idle"
    }
}


def init_driver_state():
    """Initialize driver-specific session state"""
    if 'trip_state' not in st.session_state:
        st.session_state.trip_state = "IDLE"
    if 'current_trip' not in st.session_state:
        st.session_state.current_trip = None
    if 'trips_completed' not in st.session_state:
        st.session_state.trips_completed = 0


def generate_mock_trip():
    """Generate a mock trip"""
    locations = [
        "MG Road Junction, Near Metro Station",
        "Railway Station - Platform 2 Exit",
        "Airport Terminal 2 - Arrival Gate",
        "Central Mall Parking Area",
        "Industrial Area Gate 5",
        "Highway KM 45 - Accident Site"
    ]
    
    hospitals = [
        {"name": "City General Hospital", "bed": "ICU-04"},
        {"name": "Apollo Hospital", "bed": "Emergency-2"},
        {"name": "Fortis Healthcare", "bed": "ICU-07"},
        {"name": "Max Hospital", "bed": "Trauma-1"}
    ]
    
    import random
    location = random.choice(locations)
    hospital = random.choice(hospitals)
    
    return {
        "id": f"AMB{random.randint(1000, 9999)}",
        "patient_name": random.choice(["Raj Kumar", "Amit Patel", "Sunita Devi", "Vikram Singh"]),
        "pickup_location": location,
        "destination_hospital": hospital["name"],
        "confirmed_bed": hospital["bed"],
        "eta_minutes": random.randint(10, 30),
        "started_at": datetime.now(),
        "patient_condition": random.choice(["Cardiac Emergency", "Accident Trauma", "Respiratory Distress", "Stroke"])
    }


def render_header():
    """Render driver dashboard header"""
    trips_today = st.session_state.trips_completed
    
    st.markdown(f"""
    <div class="driver-header">
        <div style="font-size: 13px; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase;">🚑 Ambulance Driver</div>
        <div style="font-size: 28px; font-weight: 800; margin: 12px 0; letter-spacing: -0.5px;">
            {st.session_state.staff_name}
        </div>
        <div style="font-size: 12px; opacity: 0.85;">ID: {st.session_state.staff_id} • {trips_today} trips today</div>
    </div>
    """, unsafe_allow_html=True)


def render_status_card():
    """Render current trip status card"""
    state = st.session_state.trip_state
    config = TRIP_STATES[state]
    
    # Display status with enhanced styling - UI STYLE ONLY
    st.markdown(f"""
    <div class="status-card {config['class']}">
        <div style="font-size: 56px; margin-bottom: 12px;">{config['icon']}</div>
        <div style="font-size: 22px; font-weight: 800; color: #1F2937; margin-bottom: 6px;">{config['label']}</div>
        <div style="font-size: 13px; color: {config['color']};">{config['description']}</div>
    </div>
    """, unsafe_allow_html=True)


def render_trip_details():
    """Render current trip details"""
    if not st.session_state.current_trip:
        return
    
    trip = st.session_state.current_trip
    
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">📋</span>
        <span class="section-title">Trip Details</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Patient info with styled card
    st.markdown(f"""
    <div class="trip-detail">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="detail-label">Patient</div>
                <div class="detail-value">👤 {trip['patient_name']}</div>
            </div>
            <div style="
                background: rgba(235, 87, 87, 0.15);
                color: #EB5757;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            ">🚨 {trip['patient_condition']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Pickup location
    st.markdown(f"""
    <div class="trip-detail">
        <div class="detail-label">📍 Pickup Location</div>
        <div class="detail-value">{trip['pickup_location']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Destination
    st.markdown(f"""
    <div class="trip-detail">
        <div class="detail-label">🏥 Destination Hospital</div>
        <div class="detail-value">{trip['destination_hospital']}</div>
    </div>
    """, unsafe_allow_html=True)


def render_hospital_confirmation():
    """Render hospital bed confirmation"""
    if not st.session_state.current_trip:
        return
    
    trip = st.session_state.current_trip
    
    st.markdown(f"""
    <div class="hospital-confirmed">
        <div style="font-size: 32px; margin-bottom: 10px;">✅</div>
        <div style="color: #27AE60; font-size: 16px; font-weight: 700;">BED CONFIRMED</div>
        <div style="color: #1F2937; font-size: 14px; margin-top: 6px;">{trip['destination_hospital']}</div>
        <div style="
            display: inline-block;
            margin-top: 12px;
            padding: 8px 20px;
            background: rgba(39, 174, 96, 0.15);
            border-radius: 25px;
            color: #27AE60;
            font-weight: 600;
            font-size: 14px;
        ">🛏️ {trip['confirmed_bed']} Ready</div>
        <div style="color: #4B5563; font-size: 11px; margin-top: 10px;">Hospital staff notified</div>
    </div>
    """, unsafe_allow_html=True)


def render_eta_display():
    """Render ETA display"""
    if not st.session_state.current_trip:
        return
    
    if st.session_state.trip_state in ["IDLE", "COMPLETED"]:
        return
    
    trip = st.session_state.current_trip
    
    # Calculate remaining ETA based on state
    base_eta = trip['eta_minutes']
    if st.session_state.trip_state == "PATIENT_LOADED":
        eta = max(5, base_eta - 10)
    elif st.session_state.trip_state == "ARRIVING":
        eta = 2
    else:
        eta = base_eta
    
    st.markdown(f"""
    <div class="eta-display">
        <div style="color: #4B5563; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Estimated Arrival</div>
        <div class="eta-value">{eta}</div>
        <div style="color: #2F80ED; font-size: 14px; font-weight: 500;">minutes</div>
    </div>
    """, unsafe_allow_html=True)


def render_idle_view():
    """Render view when driver is idle"""
    render_status_card()
    
    st.markdown("---")
    
    # Start Emergency Trip button
    st.markdown('<div class="emergency-btn">', unsafe_allow_html=True)
    if st.button("🚨 START EMERGENCY TRIP", key="start_trip", use_container_width=True):
        # Generate trip and log to backend
        trip = generate_mock_trip()
        st.session_state.current_trip = trip
        st.session_state.trip_state = "EN_ROUTE"
        
        # Log to backend
        from services.api_service import api_service
        api_service.start_trip(
            st.session_state.staff_id,
            trip['pickup_location'],
            trip['patient_name']
        )
        
        st.success("🚑 Emergency trip started!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats card - UI STYLE ONLY
    st.markdown(f"""
    <div style="
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 24px;
        margin-top: 20px;
        text-align: center;
    ">
        <div style="color: #4B5563; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Today's Completed Trips</div>
        <div style="
            font-size: 48px;
            font-weight: 800;
            color: #27AE60;
            margin: 8px 0;
        ">{st.session_state.trips_completed}</div>
        <div style="color: #2F80ED; font-size: 13px;">Keep up the great work! 💪</div>
    </div>
    """, unsafe_allow_html=True)


def render_active_trip_view():
    """Render view when trip is active"""
    render_status_card()
    render_hospital_confirmation()
    render_eta_display()
    render_trip_details()
    
    st.markdown("---")
    
    # State transition buttons
    state = st.session_state.trip_state
    state_order = ["IDLE", "EN_ROUTE", "PATIENT_LOADED", "ARRIVING", "COMPLETED"]
    current_idx = state_order.index(state)
    
    if state == "EN_ROUTE":
        st.markdown('<div class="next-state-btn">', unsafe_allow_html=True)
        if st.button("👤 PATIENT LOADED", key="load_patient", use_container_width=True):
            st.session_state.trip_state = "PATIENT_LOADED"
            
            # Log to backend
            from services.api_service import api_service
            api_service.update_trip_state(
                st.session_state.current_trip['id'],
                st.session_state.staff_id,
                "PATIENT_LOADED"
            )
            
            st.success("Patient loaded! Heading to hospital...")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif state == "PATIENT_LOADED":
        st.markdown('<div class="next-state-btn">', unsafe_allow_html=True)
        if st.button("🏥 ARRIVING AT HOSPITAL", key="arriving", use_container_width=True):
            st.session_state.trip_state = "ARRIVING"
            
            # Log to backend
            from services.api_service import api_service
            api_service.update_trip_state(
                st.session_state.current_trip['id'],
                st.session_state.staff_id,
                "ARRIVING"
            )
            
            st.success("Almost there! Hospital notified...")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif state == "ARRIVING":
        st.markdown('<div class="end-trip-btn">', unsafe_allow_html=True)
        if st.button("✅ COMPLETE TRIP", key="complete_trip", use_container_width=True):
            st.session_state.trip_state = "COMPLETED"
            st.session_state.trips_completed += 1
            
            # Log to backend
            from services.api_service import api_service
            api_service.end_trip(
                st.session_state.current_trip['id'],
                st.session_state.staff_id
            )
            
            st.success("🎉 Trip completed successfully!")
            st.balloons()
            
            # Reset after delay
            st.session_state.trip_state = "IDLE"
            st.session_state.current_trip = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Cancel trip option
    st.markdown("---")
    if st.button("❌ Cancel Trip", key="cancel_trip", use_container_width=True):
        st.session_state.trip_state = "IDLE"
        st.session_state.current_trip = None
        st.warning("Trip cancelled")
        st.rerun()


def render_quick_actions():
    """Render quick action buttons"""
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size: 22px;">⚡</span>
        <span class="section-title">Quick Actions</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📞 Call Hospital", key="call_hospital", use_container_width=True):
            st.info("📞 Connecting to hospital...")
    
    with col2:
        if st.button("🆘 Emergency SOS", key="sos", use_container_width=True):
            st.error("🆘 SOS sent to dispatch!")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("🗺️ Navigation", key="nav", use_container_width=True):
            st.info("🗺️ Opening navigation...")
    
    with col4:
        if st.button("📊 Trip History", key="history", use_container_width=True):
            st.info(f"Total trips today: {st.session_state.trips_completed}")


def render_driver_view():
    """Main render function for driver view"""
    init_driver_state()
    
    render_header()
    
    # Show appropriate view based on state
    if st.session_state.trip_state == "IDLE":
        render_idle_view()
    else:
        render_active_trip_view()
    
    st.markdown("---")
    render_quick_actions()
    
    # Footer - UI STYLE ONLY
    st.markdown("""
    <div style="
        text-align: center;
        padding: 40px 0 20px 0;
        margin-top: 30px;
        border-top: 1px solid #CBD5E1;
    ">
        <p style="color: #4B5563; font-size: 11px; margin: 0;">
            VitalFlow AI • Driver Interface
        </p>
        <p style="color: #4B5563; font-size: 10px; margin: 6px 0 0 0;">
            🔄 Last sync: Just now
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    # For standalone testing
    st.set_page_config(page_title="Driver View", page_icon="🚑", layout="centered")
    st.session_state.staff_id = "DR001"
    st.session_state.staff_name = "Driver Demo"
    render_driver_view()
