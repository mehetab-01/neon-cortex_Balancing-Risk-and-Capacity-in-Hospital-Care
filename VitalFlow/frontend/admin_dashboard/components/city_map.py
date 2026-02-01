"""
City Map Component
Hospital network and ambulance tracking visualization
"""
import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.ambulance_manager import ambulance_manager


def render_city_map():
    """Render city-level hospital and ambulance map."""
    st.markdown("## 🗺️ City Hospital Network")
    
    # Hospital info
    st.markdown("""
    ### 🏥 VitalFlow General Hospital
    **Location:** Mumbai, Maharashtra  
    **Coordinates:** 19.0760° N, 72.8777° E  
    **Capacity:** 50 beds across 5 floors
    """)
    
    # Get current ambulance status
    active_ambulances = ambulance_manager.active_ambulances if hasattr(ambulance_manager, 'active_ambulances') else {}
    
    st.markdown("---")
    st.markdown("### 🚑 Active Ambulances")
    
    if active_ambulances:
        for amb_id, tracking in active_ambulances.items():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                patient_name = tracking.patient_info.get('name', 'Unknown') if tracking.patient_info else 'No patient'
                st.markdown(f"**🚑 {amb_id}**")
                st.write(f"Patient: {patient_name}")
            
            with col2:
                st.metric("ETA", f"{tracking.eta_minutes} min")
            
            with col3:
                st.write(f"📍 Status: {tracking.status.value}")
            
            with col4:
                st.write(f"🏥 {tracking.preclearance_status.value}")
    else:
        st.info("No ambulances currently en route")
    
    # Map visualization placeholder
    st.markdown("---")
    st.markdown("### 🗺️ Live Map View")
    
    # Create a simple map using coordinates
    try:
        import pandas as pd
        
        # Hospital location
        map_data = pd.DataFrame({
            'lat': [19.0760],
            'lon': [72.8777],
            'name': ['VitalFlow Hospital']
        })
        
        # Add ambulance locations
        for amb_id, tracking in active_ambulances.items():
            if tracking.gps_lat and tracking.gps_lng:
                new_row = pd.DataFrame({
                    'lat': [tracking.gps_lat],
                    'lon': [tracking.gps_lng],
                    'name': [amb_id]
                })
                map_data = pd.concat([map_data, new_row], ignore_index=True)
        
        st.map(map_data, latitude='lat', longitude='lon', zoom=12)
        
    except Exception as e:
        st.warning(f"Map visualization requires additional setup: {e}")
        st.markdown("""
        **Hospital Location:** 🏥 VitalFlow General (19.0760, 72.8777)
        
        *Map visualization would show:*
        - Hospital location
        - Active ambulance positions
        - Estimated routes and ETAs
        - Nearby hospitals for diversion
        """)
    
    # Nearby hospitals for diversion
    st.markdown("---")
    st.markdown("### 🏥 Nearby Hospitals (for Diversion)")
    
    nearby_hospitals = [
        {"name": "City General Hospital", "distance": "2.5 km", "icu_available": 3},
        {"name": "Metro Healthcare", "distance": "4.2 km", "icu_available": 1},
        {"name": "Sunrise Medical Center", "distance": "5.8 km", "icu_available": 5},
        {"name": "Central Hospital", "distance": "7.1 km", "icu_available": 2},
    ]
    
    for hospital in nearby_hospitals:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"🏥 {hospital['name']}")
        with col2:
            st.write(f"📍 {hospital['distance']}")
        with col3:
            color = "🟢" if hospital['icu_available'] > 2 else "🟡" if hospital['icu_available'] > 0 else "🔴"
            st.write(f"{color} {hospital['icu_available']} ICU")


if __name__ == "__main__":
    render_city_map()
