"""
VitalFlow AI - Main Application Entry Point
Handles navigation between Home (Auth), Admin Dashboard, and Staff Mobile

Navigation Flow:
    Homepage -> Login -> Admin Dashboard (for admin role)
                      -> Staff Mobile (for doctor/nurse/wardboy/driver roles)
"""

import streamlit as st
import sys
import os

# Add paths for imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'frontend'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    pass

# Staff roles that should be routed to staff_mobile
STAFF_ROLES = ['doctor', 'nurse', 'wardboy', 'driver']

# Role name mapping for display
ROLE_DISPLAY_NAMES = {
    'doctor': 'Doctor',
    'nurse': 'Nurse',
    'wardboy': 'Ward Boy',
    'driver': 'Driver'
}

# Page config - set once at the start
st.set_page_config(
    page_title="VitalFlow AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "staff_id" not in st.session_state:
    st.session_state.staff_id = None
if "selected_role" not in st.session_state:
    st.session_state.selected_role = None
if "login_type" not in st.session_state:
    st.session_state.login_type = 'admin'


def handle_oauth_callback():
    """Handle Google OAuth callback at the main app level"""
    query_params = st.query_params

    if 'code' in query_params and not st.session_state.authenticated:
        code = query_params.get('code')
        state = query_params.get('state', 'admin')  # state contains login_type

        try:
            from config.google_auth import GoogleOAuthConfig, SimpleGoogleAuth

            config = GoogleOAuthConfig()
            if config.is_configured:
                auth = SimpleGoogleAuth(config)

                # Exchange code for tokens
                tokens = auth.exchange_code(code)

                if tokens and 'access_token' in tokens:
                    # Get user info
                    user_info = auth.get_user_info(tokens['access_token'])

                    if user_info:
                        email = user_info.get('email', '')
                        name = user_info.get('name', email.split('@')[0])

                        # Determine role based on login type (from state parameter)
                        if state == 'staff':
                            role = 'doctor'  # Default staff role
                        else:
                            role = 'admin'

                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.user_role = role
                        st.session_state.user_name = name
                        st.session_state.user_email = email
                        st.session_state.staff_id = f"{role[0].upper()}001"

                        # Clear URL params and rerun
                        st.query_params.clear()
                        st.rerun()

        except Exception as e:
            st.error(f"OAuth error: {e}")

        # Clear params even on error
        st.query_params.clear()


def show_home_page():
    """Display the home/auth page"""
    from frontend.home.app import main as home_main
    home_main()


def show_admin_dashboard():
    """Display the admin dashboard"""
    # Add logout button in sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Logout", key="admin_logout", use_container_width=True):
            logout()

    # Load and execute admin dashboard
    admin_path = os.path.join(BASE_DIR, 'frontend', 'admin_dashboard', 'app.py')

    with open(admin_path, 'r', encoding='utf-8') as f:
        code = f.read()

    # Skip the __main__ block only (be careful not to break function definitions)
    code = code.replace('if __name__ == "__main__":', 'if False:  # Disabled by main.py')

    exec(compile(code, admin_path, 'exec'), globals())


def show_staff_mobile():
    """Display the staff mobile interface"""
    role = st.session_state.user_role

    if role in ROLE_DISPLAY_NAMES:
        st.session_state.selected_role = ROLE_DISPLAY_NAMES[role]

    if not st.session_state.staff_id:
        st.session_state.staff_id = f"{role[0].upper()}001"

    st.session_state.staff_name = st.session_state.user_name

    from frontend.staff_mobile.app import main as staff_main
    staff_main()


def logout():
    """Clear session state and logout user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def main():
    """Main application router"""
    # Handle OAuth callback first
    handle_oauth_callback()

    # Route based on authentication status
    if st.session_state.authenticated:
        user_role = st.session_state.user_role

        if user_role == "admin":
            show_admin_dashboard()
        elif user_role in STAFF_ROLES:
            show_staff_mobile()
        else:
            st.error(f"Unknown role: {user_role}")
            if st.button("Logout"):
                logout()
    else:
        show_home_page()


if __name__ == "__main__":
    main()
