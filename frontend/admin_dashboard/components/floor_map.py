"""
VitalFlow AI - Floor Map Component
Visual grid-based floor layout showing beds and patient status
"""

import streamlit as st
from typing import Dict, List, Any
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from shared.constants import STATUS_COLORS, STATUS_EMOJI


def get_bed_color(patient: Dict = None) -> str:
    """Get the background color for a bed based on patient status"""
    if not patient:
        return "#2D2D2D"  # Empty bed - dark gray
    
    status = patient.get("status", "Stable")
    return STATUS_COLORS.get(status, "#2D2D2D")


def get_status_emoji(patient: Dict = None) -> str:
    """Get the emoji indicator for patient status"""
    if not patient:
        return "⬜"
    
    status = patient.get("status", "Stable")
    return STATUS_EMOJI.get(status, "⬜")


def render_bed_card(bed: Dict, patient: Dict = None):
    """Render a single bed card with patient info popover"""
    color = get_bed_color(patient)
    emoji = get_status_emoji(patient)
    
    if patient:
        # Occupied bed
        spo2 = patient.get("spo2", 0)
        hr = patient.get("heart_rate", 0)
        
        # SpO2 color coding
        if spo2 < 90:
            spo2_color = "#FF4B4B"
        elif spo2 < 95:
            spo2_color = "#FFA500"
        else:
            spo2_color = "#00CC66"
        
        with st.popover(f"{emoji} {bed['id']}", use_container_width=True):
            st.markdown(f"### 👤 {patient['name']}")
            st.markdown(f"**Age:** {patient['age']} | **ID:** {patient['id']}")
            st.markdown(f"**Diagnosis:** {patient['diagnosis']}")
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("SpO2", f"{spo2}%", delta=None)
                st.metric("Heart Rate", f"{hr} bpm", delta=None)
            with col2:
                st.metric("BP", patient.get('blood_pressure', 'N/A'))
                st.metric("Temp", f"{patient.get('temperature', 'N/A')}°C")
            
            st.divider()
            st.markdown(f"**Status:** {emoji} {patient['status']}")
            st.markdown(f"**Doctor:** {patient.get('assigned_doctor', 'Unassigned')}")
            
            if patient.get('notes'):
                st.info(f"📝 {patient['notes']}")
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                st.button("🔄 Transfer", key=f"transfer_{bed['id']}", use_container_width=True)
            with col2:
                st.button("📋 Details", key=f"details_{bed['id']}", use_container_width=True)
    else:
        # Empty bed
        with st.popover(f"⬜ {bed['id']}", use_container_width=True):
            st.markdown(f"### 🛏️ Bed {bed['id']}")
            st.markdown(f"**Room:** {bed['room_number']}")
            st.markdown(f"**Type:** {bed['bed_type']}")
            st.success("✅ Available")
            st.button("➕ Admit Patient", key=f"admit_{bed['id']}", use_container_width=True)


def render_bed_grid(beds: List[Dict], patients: List[Dict], cols_per_row: int = 5):
    """Render a grid of beds"""
    # Create patient lookup
    patient_lookup = {p['id']: p for p in patients}
    
    # Calculate rows needed
    total_beds = len(beds)
    rows = (total_beds + cols_per_row - 1) // cols_per_row
    
    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            bed_idx = row * cols_per_row + col_idx
            if bed_idx < total_beds:
                bed = beds[bed_idx]
                patient = patient_lookup.get(bed.get('patient_id')) if bed.get('patient_id') else None
                
                with cols[col_idx]:
                    render_bed_card(bed, patient)


def render_floor_summary(floor: Dict, patients: List[Dict]):
    """Render floor summary stats"""
    beds = floor.get('beds', [])
    floor_patients = [p for p in patients if any(b.get('patient_id') == p['id'] for b in beds)]
    
    occupied = sum(1 for b in beds if b.get('is_occupied'))
    total = len(beds)
    
    # Count by status
    status_counts = {
        "Critical": 0,
        "Serious": 0,
        "Stable": 0,
        "Recovering": 0
    }
    for p in floor_patients:
        status = p.get('status', 'Stable')
        if status in status_counts:
            status_counts[status] += 1
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Beds", total)
    with col2:
        st.metric("Occupied", occupied)
    with col3:
        st.metric("Available", total - occupied)
    with col4:
        st.markdown(f"🔴 **{status_counts['Critical']}** Critical")
    with col5:
        st.markdown(f"🟠 **{status_counts['Serious']}** Serious")
    with col6:
        st.markdown(f"🟢 **{status_counts['Stable'] + status_counts['Recovering']}** Stable/Recovering")


def render_floor_map(floors: List[Dict], patients: List[Dict], selected_floor: int = None):
    """
    Render the complete floor map with tabs for each floor
    """
    st.markdown("### 🏥 Hospital Floor Map")
    
    # Legend
    st.markdown("""
    **Legend:** 🔴 Critical | 🟠 Serious | 🟢 Stable | 🔵 Recovering | ⬜ Empty
    """)
    
    if selected_floor:
        # Show only selected floor
        floor = next((f for f in floors if f['floor_number'] == selected_floor), None)
        if floor:
            st.markdown(f"#### Floor {floor['floor_number']}: {floor['name']}")
            render_floor_summary(floor, patients)
            st.divider()
            render_bed_grid(floor['beds'], patients, cols_per_row=5)
    else:
        # Show all floors in tabs
        floor_tabs = st.tabs([f"Floor {f['floor_number']}: {f['name']}" for f in floors])
        
        for tab, floor in zip(floor_tabs, floors):
            with tab:
                render_floor_summary(floor, patients)
                st.divider()
                render_bed_grid(floor['beds'], patients, cols_per_row=5)


def render_compact_floor_view(floors: List[Dict], patients: List[Dict]):
    """
    Render a compact overview of all floors
    """
    st.markdown("### 🏥 Floor Overview")
    
    for floor in floors:
        beds = floor.get('beds', [])
        occupied = sum(1 for b in beds if b.get('is_occupied'))
        total = len(beds)
        pct = (occupied / total) * 100 if total > 0 else 0
        
        # Get critical count
        floor_patients = [p for p in patients if any(b.get('patient_id') == p['id'] for b in beds)]
        critical = sum(1 for p in floor_patients if p.get('status') == 'Critical')
        
        # Color based on capacity and critical patients
        if critical > 2 or pct > 90:
            bar_color = "🔴"
        elif critical > 0 or pct > 75:
            bar_color = "🟠"
        else:
            bar_color = "🟢"
        
        with st.expander(f"{bar_color} **Floor {floor['floor_number']}**: {floor['name']} ({occupied}/{total})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(pct / 100, text=f"{pct:.0f}% Occupied")
            with col2:
                if critical > 0:
                    st.error(f"🔴 {critical} Critical")
                else:
                    st.success("✅ No Critical")


def render_bed_matrix(beds: List[Dict], patients: List[Dict]):
    """
    Render a compact matrix view of beds using colored squares
    """
    patient_lookup = {p['id']: p for p in patients}
    
    # Build HTML for compact view
    html_rows = []
    
    for i, bed in enumerate(beds):
        patient = patient_lookup.get(bed.get('patient_id')) if bed.get('patient_id') else None
        color = get_bed_color(patient)
        emoji = get_status_emoji(patient)
        
        title = f"{bed['id']}"
        if patient:
            title += f" - {patient['name']} (SpO2: {patient['spo2']}%)"
        else:
            title += " - Empty"
        
        html_rows.append(
            f'<span title="{title}" style="display: inline-block; width: 40px; height: 40px; '
            f'background-color: {color}; margin: 2px; border-radius: 5px; '
            f'text-align: center; line-height: 40px; cursor: pointer; '
            f'font-size: 18px;">{emoji}</span>'
        )
        
        # Line break every 10 beds
        if (i + 1) % 10 == 0:
            html_rows.append('<br>')
    
    st.markdown(
        f'<div style="background: #1E1E1E; padding: 15px; border-radius: 10px;">{"".join(html_rows)}</div>',
        unsafe_allow_html=True
    )
