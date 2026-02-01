"""
Stats Panel Component
Real-time hospital statistics dashboard
"""
import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.bed_manager import bed_manager
from backend.core_logic.staff_manager import staff_manager


def render_stats_panel():
    """Render real-time hospital statistics."""
    st.markdown("## 📊 Hospital Statistics")
    
    # Get current stats
    stats = hospital_state.get_stats()
    occupancy = bed_manager.get_bed_occupancy()
    
    # Main metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "🛏️ Total Beds",
            stats.get('total_beds', 50),
            help="Total bed capacity"
        )
    
    with col2:
        available = stats.get('available_beds', 0)
        occupied = stats.get('occupied_beds', 0)
        st.metric(
            "🟢 Available",
            available,
            delta=f"{occupied} occupied",
            delta_color="inverse"
        )
    
    with col3:
        occupancy_rate = stats.get('occupancy_rate', 0)
        st.metric(
            "📊 Occupancy",
            f"{occupancy_rate:.1f}%",
            delta="Normal" if occupancy_rate < 80 else "High" if occupancy_rate < 95 else "Critical",
            delta_color="normal" if occupancy_rate < 80 else "off" if occupancy_rate < 95 else "inverse"
        )
    
    with col4:
        st.metric(
            "👥 Patients",
            stats.get('total_patients', 0)
        )
    
    with col5:
        st.metric(
            "👨‍⚕️ Staff",
            stats.get('total_staff', 0)
        )
    
    st.markdown("---")
    
    # Bed breakdown by type
    st.markdown("### 🛏️ Bed Availability by Type")
    
    bed_cols = st.columns(5)
    bed_types = ["ICU", "Emergency", "General", "Pediatric", "Maternity"]
    bed_icons = ["🏥", "🚨", "🏠", "👶", "🤰"]
    
    for idx, (col, bed_type, icon) in enumerate(zip(bed_cols, bed_types, bed_icons)):
        with col:
            bed_stats = occupancy.get(bed_type, {"total": 0, "occupied": 0, "available": 0})
            total = bed_stats['total']
            available = bed_stats['available']
            occupied = bed_stats['occupied']
            
            # Color based on availability
            if total > 0:
                pct_available = (available / total) * 100
                if pct_available > 50:
                    color = "🟢"
                elif pct_available > 20:
                    color = "🟡"
                else:
                    color = "🔴"
            else:
                color = "⚪"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 10px;">
                <div style="font-size: 2rem;">{icon}</div>
                <div style="font-weight: bold;">{bed_type}</div>
                <div style="font-size: 1.5rem; color: {'#4caf50' if pct_available > 50 else '#ff9800' if pct_available > 20 else '#f44336'};">
                    {available}/{total}
                </div>
                <div style="font-size: 0.8rem; color: #888;">Available</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Patient status breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏥 Patients by Status")
        
        patients_by_status = stats.get('patients_by_status', {})
        status_icons = {
            "Critical": "🔴",
            "Serious": "🟠",
            "Stable": "🟢",
            "Recovering": "🔵",
            "Discharged": "⚪"
        }
        
        for status, count in patients_by_status.items():
            icon = status_icons.get(status, "⚪")
            st.markdown(f"{icon} **{status}:** {count}")
    
    with col2:
        st.markdown("### 👥 Staff Status")
        
        # Count staff by status
        staff_counts = {"Available": 0, "Busy": 0, "On Break": 0, "Off Duty": 0}
        fatigued_count = 0
        
        for staff in hospital_state.staff.values():
            status = str(staff.status)
            if status in staff_counts:
                staff_counts[status] += 1
            if staff_manager.is_fatigued(staff.id):
                fatigued_count += 1
        
        st.markdown(f"🟢 **Available:** {staff_counts['Available']}")
        st.markdown(f"🟡 **Busy:** {staff_counts['Busy']}")
        st.markdown(f"☕ **On Break:** {staff_counts['On Break']}")
        st.markdown(f"🔴 **Off Duty:** {staff_counts['Off Duty']}")
        
        if fatigued_count > 0:
            st.warning(f"⚠️ **{fatigued_count} staff member(s) fatigued**")
    
    # Critical alerts summary
    st.markdown("---")
    st.markdown("### ⚠️ System Alerts")
    
    alerts = []
    
    # Check ICU availability
    icu_stats = occupancy.get("ICU", {"available": 0})
    if icu_stats['available'] == 0:
        alerts.append("🔴 **ICU FULL** - No ICU beds available")
    elif icu_stats['available'] <= 2:
        alerts.append(f"🟡 **ICU LOW** - Only {icu_stats['available']} ICU bed(s) available")
    
    # Check for critical patients without ICU bed
    for patient in hospital_state.patients.values():
        if str(patient.status) == "Critical":
            if patient.bed_id:
                bed = hospital_state.beds.get(patient.bed_id)
                if bed and str(bed.bed_type) != "ICU":
                    alerts.append(f"🔴 **{patient.name}** is Critical but not in ICU")
    
    # Check for fatigued staff with critical patients
    for staff in hospital_state.staff.values():
        if staff_manager.is_fatigued(staff.id) and staff.current_patient_ids:
            alerts.append(f"⚠️ **{staff.name}** is fatigued but has active patients")
    
    if alerts:
        for alert in alerts:
            st.markdown(alert)
    else:
        st.success("✅ All systems operating normally")


if __name__ == "__main__":
    render_stats_panel()
