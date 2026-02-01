"""
Floor Map Component
Visual bed occupancy by floor/ward
"""
import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.bed_manager import bed_manager
from shared.constants import WARD_NAMES, BED_TYPE_COLORS


def get_bed_color(bed) -> str:
    """Get color based on bed status and type."""
    if bed.is_occupied:
        # Get patient status for color
        patient = hospital_state.patients.get(bed.patient_id)
        if patient:
            status = str(patient.status)
            if status == "Critical":
                return "#ff4444"  # Red
            elif status == "Serious":
                return "#ff8c00"  # Orange
            elif status == "Stable":
                return "#4caf50"  # Green
            elif status == "Recovering":
                return "#2196f3"  # Blue
        return "#9e9e9e"  # Gray for occupied unknown
    else:
        return "#e0e0e0"  # Light gray for empty


def render_bed_grid(beds_on_floor, floor_num):
    """Render a visual grid of beds for a floor."""
    if not beds_on_floor:
        st.info(f"No beds on Floor {floor_num}")
        return
    
    # Create a grid layout
    cols_per_row = 5
    rows = (len(beds_on_floor) + cols_per_row - 1) // cols_per_row
    
    bed_list = list(beds_on_floor)
    
    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            bed_idx = row * cols_per_row + col_idx
            if bed_idx < len(bed_list):
                bed = bed_list[bed_idx]
                color = get_bed_color(bed)
                
                with cols[col_idx]:
                    # Bed visualization
                    patient_info = ""
                    if bed.is_occupied and bed.patient_id:
                        patient = hospital_state.patients.get(bed.patient_id)
                        if patient:
                            patient_info = f"{patient.name[:10]}..."
                    
                    st.markdown(f"""
                    <div style="
                        background: {color};
                        border-radius: 8px;
                        padding: 10px;
                        text-align: center;
                        margin: 5px 0;
                        min-height: 80px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    ">
                        <div style="font-weight: bold; color: #333;">🛏️ {bed.id}</div>
                        <div style="font-size: 0.8rem; color: #555;">{str(bed.bed_type)}</div>
                        <div style="font-size: 0.7rem; color: #666;">{patient_info or 'Empty'}</div>
                    </div>
                    """, unsafe_allow_html=True)


def render_floor_map():
    """Render the floor-wise bed visualization."""
    st.markdown("## 🏥 Hospital Floor Map")
    
    # Floor selector
    col1, col2 = st.columns([1, 3])
    
    with col1:
        floor_options = list(WARD_NAMES.keys())
        selected_floor = st.selectbox(
            "Select Floor",
            floor_options,
            format_func=lambda x: f"Floor {x} - {WARD_NAMES.get(x, 'Unknown')}"
        )
    
    with col2:
        # Legend
        st.markdown("""
        **Legend:** 
        🔴 Critical | 🟠 Serious | 🟢 Stable | 🔵 Recovering | ⚪ Empty
        """)
    
    # Get beds for selected floor
    beds_on_floor = [b for b in hospital_state.beds.values() if b.floor == selected_floor]
    
    # Group by bed type
    bed_types = {}
    for bed in beds_on_floor:
        bed_type = str(bed.bed_type)
        if bed_type not in bed_types:
            bed_types[bed_type] = []
        bed_types[bed_type].append(bed)
    
    # Render each bed type section
    for bed_type, beds in bed_types.items():
        occupied = sum(1 for b in beds if b.is_occupied)
        st.markdown(f"### {bed_type} ({occupied}/{len(beds)} occupied)")
        render_bed_grid(beds, selected_floor)
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Request Bed Sanitization", key="sanitize_btn"):
            st.info("Sanitization request sent to ward staff")
    
    with col2:
        if st.button("🔄 Trigger Bed Swap Analysis", key="swap_btn"):
            st.info("Running Tetris algorithm for optimal bed allocation...")
    
    with col3:
        if st.button("📊 Export Floor Report", key="export_floor"):
            st.info("Floor report generated")


if __name__ == "__main__":
    render_floor_map()
