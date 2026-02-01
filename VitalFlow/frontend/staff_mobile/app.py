"""
VitalFlow AI - Staff Mobile App
Role-based mobile interface for hospital staff

Roles:
- Doctor
- Nurse
- Ward Boy / Girl
- Ambulance Driver
- Medical Staff
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core_logic.state import hospital_state
from backend.core_logic.staff_manager import staff_manager
from shared.models import StaffRole


def apply_mobile_styles():
    """Apply mobile-friendly CSS styling."""
    st.markdown("""
    <style>
        /* Mobile-friendly styling */
        .mobile-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .role-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: bold;
            margin: 0.5rem;
        }
        
        .task-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #00d4ff;
        }
        
        .action-button {
            width: 100%;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        
        .status-online { background: #00ff88; }
        .status-busy { background: #ffa500; }
        .status-offline { background: #ff4444; }
    </style>
    """, unsafe_allow_html=True)


def render_role_selector():
    """Render role selection screen."""
    st.markdown("""
    <div class="mobile-header">
        <h2>🏥 VitalFlow Staff Portal</h2>
        <p>Select your role to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Role selection grid
    col1, col2 = st.columns(2)
    
    roles = [
        ("👨‍⚕️", "Doctor", "Manage patients, rounds, approvals"),
        ("👩‍⚕️", "Nurse", "Tasks, medicine prep, vitals"),
        ("🧹", "Ward Boy/Girl", "Transfers, cleaning, logistics"),
        ("🚑", "Ambulance Driver", "Emergency transport"),
        ("⚕️", "Medical Staff", "General medical support")
    ]
    
    for idx, (icon, role, desc) in enumerate(roles):
        col = col1 if idx % 2 == 0 else col2
        with col:
            st.markdown(f"""
            <div style="
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                padding: 1.5rem;
                text-align: center;
                margin: 0.5rem 0;
                border: 1px solid rgba(255,255,255,0.1);
            ">
                <div style="font-size: 3rem;">{icon}</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">{role}</div>
                <div style="font-size: 0.8rem; color: #888;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Login as {role}", key=f"role_{role}", use_container_width=True):
                st.session_state.staff_role = role
                st.session_state.staff_logged_in = True
                st.rerun()
    
    # Sign Out button
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Back to Home", key="staff_back"):
            st.session_state.logged_in = False
            st.session_state.portal = None
            st.rerun()
    with col2:
        if st.button("🚪 Sign Out", key="staff_role_signout", type="secondary"):
            # Clear Google auth if available
            try:
                from frontend.auth.google_auth import google_auth_service
                google_auth_service.sign_out()
            except:
                pass
            st.session_state.logged_in = False
            st.session_state.portal = None
            st.session_state.staff_logged_in = False
            st.session_state.staff_role = None
            st.rerun()


def render_staff_header(role: str, staff_info: dict = None):
    """Render header for staff view."""
    # Try to get authenticated user
    try:
        from frontend.auth.google_auth import get_authenticated_user, google_auth_service
        google_user = get_authenticated_user()
    except ImportError:
        google_user = None
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        role_icons = {
            "Doctor": "👨‍⚕️",
            "Nurse": "👩‍⚕️",
            "Ward Boy/Girl": "🧹",
            "Ambulance Driver": "🚑",
            "Medical Staff": "⚕️"
        }
        icon = role_icons.get(role, "👤")
        # Show Google user name if available
        if google_user:
            st.markdown(f"### {icon} {role} Dashboard")
            st.caption(f"👤 {google_user.name}")
        else:
            st.markdown(f"### {icon} {role} Dashboard")
    
    with col2:
        if staff_info:
            hours = staff_info.get('hours_worked', 0)
            st.metric("Hours", f"{hours:.1f}h")
    
    with col3:
        if st.button("🔄 Change Role", key="change_role"):
            st.session_state.staff_role = None
            st.session_state.staff_logged_in = False
            st.session_state.current_staff_id = None
            st.rerun()
    
    with col4:
        if st.button("🚪 Sign Out", key="staff_signout", type="secondary"):
            st.session_state.staff_role = None
            st.session_state.staff_logged_in = False
            st.session_state.current_staff_id = None
            st.session_state.logged_in = False
            st.session_state.portal = None
            st.rerun()


def select_staff_member(role: str):
    """Let user select their staff identity."""
    st.markdown("### 👤 Select Your Profile")
    
    # Get staff of this role
    role_map = {
        "Doctor": "Doctor",
        "Nurse": "Nurse",
        "Ward Boy/Girl": "Wardboy",
        "Ambulance Driver": "Driver",
        "Medical Staff": "Nurse"  # Map to nurse for now
    }
    
    target_role = role_map.get(role, "Doctor")
    matching_staff = [s for s in hospital_state.staff.values() 
                     if str(s.role) == target_role]
    
    if not matching_staff:
        st.warning(f"No {role} staff found in system. Using demo mode.")
        return None
    
    # Create selection
    staff_options = {f"{s.name} ({s.id})": s.id for s in matching_staff}
    
    selected = st.selectbox(
        "Who are you?",
        list(staff_options.keys()),
        key="staff_select"
    )
    
    if selected:
        staff_id = staff_options[selected]
        st.session_state.current_staff_id = staff_id
        return hospital_state.staff.get(staff_id)
    
    return None


def route_to_role_view(role: str):
    """Route to the appropriate role-specific view."""
    apply_mobile_styles()
    
    # Get or select staff member
    if "current_staff_id" not in st.session_state or st.session_state.current_staff_id is None:
        staff = select_staff_member(role)
        if not staff:
            return
        if st.button("✅ Continue", key="continue_staff"):
            st.rerun()
        return
    
    staff = hospital_state.staff.get(st.session_state.current_staff_id)
    
    # Handle case where staff not found
    if staff is None:
        st.error("Staff member not found. Please select again.")
        if st.button("🔄 Select Staff", key="reselect_staff"):
            st.session_state.current_staff_id = None
            st.rerun()
        return
    
    # Get staff info
    staff_info = {
        "name": staff.name,
        "hours_worked": staff_manager.get_hours_worked(staff.id),
        "fatigue_level": staff_manager.get_fatigue_level(staff.id)
    }
    
    render_staff_header(role, staff_info)
    st.markdown("---")
    
    # Route to role-specific view
    if role == "Doctor":
        from .pages.doctor_view import render_doctor_view
        render_doctor_view(staff)
    
    elif role == "Nurse":
        from .pages.nurse_view import render_nurse_view
        render_nurse_view(staff)
    
    elif role == "Ward Boy/Girl":
        from .pages.wardboy_view import render_wardboy_view
        render_wardboy_view(staff)
    
    elif role == "Ambulance Driver":
        from .pages.driver_view import render_driver_view
        render_driver_view(staff)
    
    elif role == "Medical Staff":
        # Medical Staff view - combined functionality
        render_medical_staff_view(staff)
    
    else:
        st.info(f"View for {role} is under development")


def render_medical_staff_view(staff):
    """Render view for general medical staff."""
    st.markdown("### 🩺 Medical Staff Dashboard")
    
    # Shift status
    col1, col2 = st.columns(2)
    with col1:
        hours = staff_manager.get_hours_worked(staff.id)
        st.metric("⏱️ Hours Worked", f"{hours:.1f}h")
    with col2:
        fatigue = staff_manager.get_fatigue_level(staff.id)
        fatigue_icons = {"fresh": "🟢", "normal": "🟡", "tired": "🟠", "fatigued": "🔴"}
        st.metric(f"{fatigue_icons.get(fatigue, '⚪')} Fatigue", fatigue.upper())
    
    # Quick actions
    st.markdown("### 🎯 Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 View Tasks", use_container_width=True):
            st.info("Tasks feature coming soon")
    with col2:
        if st.button("🏥 Hospital Status", use_container_width=True):
            stats = hospital_state.get_stats()
            st.json(stats)
    
    # Current patients in hospital
    st.markdown("### 👥 Hospital Overview")
    patients = list(hospital_state.patients.values())
    st.write(f"Total Patients: **{len(patients)}**")
    
    # Show patient summary by status
    status_counts = {}
    for p in patients:
        status = str(p.status)
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        st.write(f"- {status}: {count}")


def run_staff_app():
    """Main entry point for staff mobile app."""
    apply_mobile_styles()
    
    # Initialize session state
    if "staff_logged_in" not in st.session_state:
        st.session_state.staff_logged_in = False
    if "staff_role" not in st.session_state:
        st.session_state.staff_role = None
    
    # Route based on state
    if st.session_state.staff_logged_in and st.session_state.staff_role:
        route_to_role_view(st.session_state.staff_role)
    else:
        render_role_selector()


if __name__ == "__main__":
    run_staff_app()
