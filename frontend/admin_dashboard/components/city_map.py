"""
VitalFlow AI - City Map Component
Multi-hospital network view using Folium maps
"""

import streamlit as st
from typing import Dict, List, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from shared.constants import MAP_CENTER, MAP_ZOOM


def get_hospital_color(hospital: Dict) -> str:
    """
    Get marker color based on hospital capacity
    Red if ICU < 10%, Yellow if < 25%, Green otherwise
    """
    icu_pct = hospital.get('icu_percentage', 50)
    occupancy = hospital.get('occupancy_rate', 50)
    
    if icu_pct < 10 or occupancy > 90:
        return 'red'
    elif icu_pct < 25 or occupancy > 80:
        return 'orange'
    else:
        return 'green'


def get_hospital_icon(hospital: Dict) -> str:
    """Get icon based on hospital status"""
    color = get_hospital_color(hospital)
    if color == 'red':
        return '🔴'
    elif color == 'orange':
        return '🟠'
    return '🟢'


def render_city_map_folium(hospitals: List[Dict]):
    """
    Render city map using streamlit-folium
    """
    try:
        import folium
        from streamlit_folium import st_folium
        
        # Create map centered on Mumbai
        m = folium.Map(
            location=MAP_CENTER,
            zoom_start=MAP_ZOOM,
            tiles='CartoDB dark_matter'  # Dark theme map
        )
        
        # Add hospital markers
        for hospital in hospitals:
            color = get_hospital_color(hospital)
            
            # Create popup content
            popup_html = f"""
            <div style="width: 250px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{hospital['name']}</h4>
                <p style="margin: 5px 0; color: #666;"><b>Address:</b> {hospital.get('address', 'N/A')}</p>
                <hr style="margin: 10px 0;">
                <table style="width: 100%;">
                    <tr>
                        <td><b>Total Beds:</b></td>
                        <td>{hospital['total_beds']}</td>
                    </tr>
                    <tr>
                        <td><b>Available:</b></td>
                        <td style="color: {'green' if hospital['available_beds'] > 10 else 'red'};">
                            {hospital['available_beds']}
                        </td>
                    </tr>
                    <tr>
                        <td><b>ICU Available:</b></td>
                        <td style="color: {'green' if hospital['icu_available'] > 2 else 'red'};">
                            {hospital['icu_available']}/{hospital['icu_total']}
                        </td>
                    </tr>
                    <tr>
                        <td><b>Occupancy:</b></td>
                        <td>{hospital['occupancy_rate']}%</td>
                    </tr>
                </table>
                <div style="margin-top: 10px; padding: 5px; background: {'#ffebee' if color == 'red' else '#fff3e0' if color == 'orange' else '#e8f5e9'}; border-radius: 5px; text-align: center;">
                    <b style="color: {color};">
                        {'⚠️ CRITICAL CAPACITY' if color == 'red' else '⚡ HIGH LOAD' if color == 'orange' else '✅ NORMAL'}
                    </b>
                </div>
            </div>
            """
            
            # Add marker
            folium.Marker(
                location=[hospital['lat'], hospital['lon']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{hospital['name']} - ICU: {hospital['icu_available']} available",
                icon=folium.Icon(
                    color=color,
                    icon='plus-sign' if color == 'red' else 'info-sign',
                    prefix='glyphicon'
                )
            ).add_to(m)
            
            # Add circle to show capacity visually
            folium.Circle(
                location=[hospital['lat'], hospital['lon']],
                radius=300,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.3,
            ).add_to(m)
        
        # Display map
        st_folium(m, width=None, height=500, use_container_width=True)
        
    except ImportError:
        st.warning("📦 Folium not installed. Using alternative view.")
        render_city_map_alternative(hospitals)


def render_city_map_pydeck(hospitals: List[Dict]):
    """
    Alternative map rendering using PyDeck (built into Streamlit)
    """
    import pandas as pd
    
    # Prepare data
    data = []
    for h in hospitals:
        color = get_hospital_color(h)
        if color == 'red':
            rgb = [255, 75, 75, 200]
        elif color == 'orange':
            rgb = [255, 165, 0, 200]
        else:
            rgb = [0, 204, 102, 200]
        
        data.append({
            'name': h['name'],
            'lat': h['lat'],
            'lon': h['lon'],
            'icu_available': h['icu_available'],
            'available_beds': h['available_beds'],
            'occupancy': h['occupancy_rate'],
            'color': rgb,
            'size': 1000,
        })
    
    df = pd.DataFrame(data)
    
    st.pydeck_chart(
        {
            "initialViewState": {
                "latitude": MAP_CENTER[0],
                "longitude": MAP_CENTER[1],
                "zoom": 11,
                "pitch": 45,
            },
            "layers": [
                {
                    "type": "ScatterplotLayer",
                    "data": df.to_dict('records'),
                    "getPosition": ["lon", "lat"],
                    "getColor": "color",
                    "getRadius": "size",
                    "pickable": True,
                },
                {
                    "type": "TextLayer",
                    "data": df.to_dict('records'),
                    "getPosition": ["lon", "lat"],
                    "getText": "name",
                    "getSize": 14,
                    "getColor": [255, 255, 255],
                    "getAngle": 0,
                    "getTextAnchor": "'middle'",
                    "getAlignmentBaseline": "'bottom'",
                }
            ],
            "mapStyle": "mapbox://styles/mapbox/dark-v10",
        },
        use_container_width=True,
        height=500
    )


def render_city_map_alternative(hospitals: List[Dict]):
    """
    Fallback view when map libraries aren't available
    """
    st.markdown("### 🗺️ Hospital Network Status")
    
    # Summary stats
    total_beds = sum(h['total_beds'] for h in hospitals)
    total_available = sum(h['available_beds'] for h in hospitals)
    total_icu = sum(h['icu_total'] for h in hospitals)
    total_icu_available = sum(h['icu_available'] for h in hospitals)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Network Hospitals", len(hospitals))
    with col2:
        st.metric("Total Beds", total_beds, f"{total_available} available")
    with col3:
        st.metric("Total ICU", total_icu, f"{total_icu_available} available")
    with col4:
        avg_occupancy = sum(h['occupancy_rate'] for h in hospitals) / len(hospitals) if hospitals else 0
        st.metric("Avg Occupancy", f"{avg_occupancy:.1f}%")
    
    st.divider()
    
    # Hospital cards
    for hospital in hospitals:
        icon = get_hospital_icon(hospital)
        color = get_hospital_color(hospital)
        
        border_color = "#FF4B4B" if color == 'red' else "#FFA500" if color == 'orange' else "#00CC66"
        
        st.markdown(
            f"""
            <div style="
                background: #1E1E1E;
                border-left: 4px solid {border_color};
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h4 style="margin: 0; color: white;">{icon} {hospital['name']}</h4>
                        <p style="margin: 5px 0; color: #888;">📍 {hospital.get('address', 'N/A')}</p>
                    </div>
                    <div style="text-align: right;">
                        <span style="
                            background: {border_color}20;
                            color: {border_color};
                            padding: 5px 10px;
                            border-radius: 15px;
                            font-size: 12px;
                        ">
                            {hospital['occupancy_rate']}% Occupied
                        </span>
                    </div>
                </div>
                <div style="display: flex; gap: 20px; margin-top: 15px;">
                    <div>
                        <span style="color: #888;">Total Beds:</span>
                        <span style="color: white; font-weight: bold;"> {hospital['total_beds']}</span>
                    </div>
                    <div>
                        <span style="color: #888;">Available:</span>
                        <span style="color: #00CC66; font-weight: bold;"> {hospital['available_beds']}</span>
                    </div>
                    <div>
                        <span style="color: #888;">ICU:</span>
                        <span style="color: {'#FF4B4B' if hospital['icu_available'] < 2 else '#00CC66'}; font-weight: bold;">
                            {hospital['icu_available']}/{hospital['icu_total']}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_city_map(hospitals: List[Dict], use_folium: bool = True):
    """
    Main entry point for city map rendering
    """
    st.markdown("### 🗺️ Hospital Network Map")
    
    # Legend
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**Legend:**")
    with col2:
        st.markdown("🟢 Normal (<80% capacity)")
    with col3:
        st.markdown("🟠 High Load (>80%)")
    with col4:
        st.markdown("🔴 Critical (>90% or ICU <10%)")
    
    st.divider()
    
    # Try folium first, fallback to pydeck, then alternative
    if use_folium:
        try:
            render_city_map_folium(hospitals)
        except Exception as e:
            st.warning(f"Folium map failed: {e}")
            try:
                render_city_map_pydeck(hospitals)
            except:
                render_city_map_alternative(hospitals)
    else:
        try:
            render_city_map_pydeck(hospitals)
        except:
            render_city_map_alternative(hospitals)


def render_hospital_comparison(hospitals: List[Dict]):
    """
    Render a comparison table of all hospitals
    """
    import pandas as pd
    
    st.markdown("### 📊 Hospital Comparison")
    
    data = []
    for h in hospitals:
        status = "🔴 Critical" if get_hospital_color(h) == 'red' else "🟠 High" if get_hospital_color(h) == 'orange' else "🟢 Normal"
        data.append({
            "Hospital": h['name'],
            "Status": status,
            "Total Beds": h['total_beds'],
            "Available": h['available_beds'],
            "ICU Total": h['icu_total'],
            "ICU Free": h['icu_available'],
            "Occupancy": f"{h['occupancy_rate']}%",
        })
    
    df = pd.DataFrame(data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def render_transfer_panel(hospitals: List[Dict], current_hospital_id: str = None):
    """
    Render panel for transferring patients between hospitals
    """
    st.markdown("### 🔄 Inter-Hospital Transfer")
    
    # Filter out current hospital
    available_hospitals = [h for h in hospitals if h['id'] != current_hospital_id and h['available_beds'] > 0]
    
    if not available_hospitals:
        st.warning("No hospitals with available beds for transfer")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox(
            "Transfer Patient",
            ["Select patient..."],  # Would be populated with actual patients
            key="transfer_patient"
        )
    
    with col2:
        hospital_options = [f"{h['name']} ({h['available_beds']} beds, {h['icu_available']} ICU)" for h in available_hospitals]
        st.selectbox(
            "Destination Hospital",
            hospital_options,
            key="transfer_destination"
        )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox("Transfer Type", ["Ambulance", "Critical Care Unit", "Regular Transport"])
    with col2:
        st.selectbox("Priority", ["Emergency", "Urgent", "Standard"])
    with col3:
        st.button("🚑 Initiate Transfer", type="primary", use_container_width=True)
