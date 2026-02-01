"""
VitalFlow AI - Main Landing Portal
Hospital Command Center - Entry Point

Run with: streamlit run frontend/main.py
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="VitalFlow AI - Hospital Command Center",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the landing page
def apply_landing_styles():
    """Apply custom CSS for landing page styling."""
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        }
        
        /* Logo container */
        .logo-container {
            text-align: center;
            padding: 2rem 0;
        }
        
        .hospital-logo {
            font-size: 5rem;
            margin-bottom: 1rem;
        }
        
        .hospital-name {
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .hospital-tagline {
            font-size: 1.2rem;
            color: #a0a0a0;
            margin-bottom: 2rem;
        }
        
        /* Button styling */
        .stButton > button {
            width: 100%;
            padding: 1.5rem 2rem;
            font-size: 1.2rem;
            border-radius: 15px;
            border: 2px solid transparent;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transition: all 0.3s ease;
            margin: 0.5rem 0;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        /* Card styling for login options */
        .login-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 2rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin: 1rem 0;
        }
        
        /* Icon styling */
        .role-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: #666;
            padding: 2rem 0;
            font-size: 0.9rem;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Status indicators */
        .status-online {
            color: #00ff88;
            font-weight: bold;
        }
        
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin: 2rem 0;
            padding: 1rem;
            background: rgba(0, 212, 255, 0.1);
            border-radius: 10px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #a0a0a0;
        }
    </style>
    """, unsafe_allow_html=True)


def render_logo_section():
    """Render the hospital logo and branding."""
    st.markdown("""
    <div class="logo-container">
        <div class="hospital-logo">🏥</div>
        <div class="hospital-name">VitalFlow AI</div>
        <div class="hospital-tagline">Balancing Risk and Capacity in Hospital Care</div>
        <div class="status-online">● System Online</div>
    </div>
    """, unsafe_allow_html=True)


def render_stats_preview():
    """Render quick stats preview on landing page."""
    try:
        from backend.core_logic.state import hospital_state
        stats = hospital_state.get_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🛏️ Beds Available", 
                     f"{stats.get('available_beds', 0)}/{stats.get('total_beds', 50)}")
        
        with col2:
            st.metric("👥 Patients", 
                     stats.get('total_patients', 0))
        
        with col3:
            st.metric("👨‍⚕️ Staff On Duty", 
                     stats.get('total_staff', 0))
        
        with col4:
            occupancy = stats.get('occupancy_rate', 0)
            st.metric("📊 Occupancy", f"{occupancy:.1f}%")
                     
    except Exception as e:
        # Show default stats if backend not initialized
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🛏️ Beds Available", "35/50")
        with col2:
            st.metric("👥 Patients", "15")
        with col3:
            st.metric("👨‍⚕️ Staff On Duty", "45")
        with col4:
            st.metric("📊 Occupancy", "30%")


def render_login_options():
    """Render the three login options."""
    st.markdown("### 🔐 Select Access Portal")
    
    # Import Google Auth
    try:
        from frontend.auth.google_auth import (
            google_auth_service, 
            render_google_login_option,
            render_demo_login,
            is_authenticated,
            get_authenticated_user
        )
        google_auth_available = True
    except ImportError:
        google_auth_available = False
    
    # Check for Google OAuth callback
    if google_auth_available:
        user = google_auth_service.handle_callback()
        if user:
            st.session_state.logged_in = True
            st.success(f"✅ Welcome, {user.name}!")
            st.rerun()
    
    # Show authenticated user if exists
    if google_auth_available and is_authenticated():
        user = get_authenticated_user()
        if user:
            st.markdown("---")
            col1, col2 = st.columns([1, 4])
            with col1:
                if user.picture:
                    st.image(user.picture, width=50)
                else:
                    st.markdown("### 👤")
            with col2:
                st.markdown(f"**Welcome back, {user.name}!**")
                st.caption(user.email)
            st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="login-card">
            <div style="text-align: center;">
                <div class="role-icon">👨‍💼</div>
                <h3>Admin Portal</h3>
                <p style="color: #a0a0a0;">Full hospital overview, bed management, staff coordination, CCTV monitoring</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔑 Admin Login", key="admin_login", use_container_width=True):
            st.session_state.portal = "admin"
            st.session_state.logged_in = True
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="login-card">
            <div style="text-align: center;">
                <div class="role-icon">👨‍⚕️</div>
                <h3>Staff Portal</h3>
                <p style="color: #a0a0a0;">Doctor, Nurse, Ward Boy, and Ambulance Driver interfaces</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔑 Staff Login", key="staff_login", use_container_width=True):
            st.session_state.portal = "staff"
            st.session_state.logged_in = True
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="login-card">
            <div style="text-align: center;">
                <div class="role-icon">🤒</div>
                <h3>Patient Portal</h3>
                <p style="color: #a0a0a0;">View recovery status, medicines, reports, and discharge info</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔑 Patient Login", key="patient_login", use_container_width=True):
            st.session_state.portal = "patient"
            st.session_state.logged_in = True
            st.rerun()
    
    # Google Sign-In Option
    if google_auth_available:
        st.markdown("---")
        st.markdown("##### 🔐 Single Sign-On")
        
        if google_auth_service.is_configured:
            google_auth_service.render_sign_in_button("Sign in with Google")
        else:
            render_demo_login()


def render_landing_page():
    """Render the main landing page."""
    apply_landing_styles()
    
    # Logo and branding
    render_logo_section()
    
    st.markdown("---")
    
    # Quick stats preview
    render_stats_preview()
    
    st.markdown("---")
    
    # Get Started button
    if not st.session_state.get("show_login", False):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Get Started", key="get_started", use_container_width=True):
                st.session_state.show_login = True
                st.rerun()
    else:
        # Login options
        render_login_options()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>🏥 VitalFlow AI - Hospital Command Center</p>
        <p>Powered by Agentic AI • Computer Vision • Real-time Monitoring</p>
        <p style="font-size: 0.8rem; margin-top: 1rem;">
            ⚠️ Safety-Critical System • Human-in-the-Loop Approvals Required
        </p>
    </div>
    """, unsafe_allow_html=True)


def route_to_portal():
    """Route to the appropriate portal based on login selection."""
    portal = st.session_state.get("portal", None)
    
    if portal == "admin":
        # Import and run admin dashboard
        from frontend.admin_dashboard.app import run_admin_dashboard
        run_admin_dashboard()
        
    elif portal == "staff":
        # Import and run staff mobile app
        from frontend.staff_mobile.app import run_staff_app
        run_staff_app()
        
    elif portal == "patient":
        # Import and run patient view
        from frontend.staff_mobile.pages.patient_view import render_patient_view
        render_patient_view()
    else:
        render_landing_page()


def main():
    """Main entry point for VitalFlow frontend."""
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "portal" not in st.session_state:
        st.session_state.portal = None
    if "show_login" not in st.session_state:
        st.session_state.show_login = False
    
    # Route based on login state
    if st.session_state.logged_in and st.session_state.portal:
        route_to_portal()
    else:
        render_landing_page()


if __name__ == "__main__":
    main()
