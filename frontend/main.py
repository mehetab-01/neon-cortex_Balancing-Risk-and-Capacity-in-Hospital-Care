"""
VitalFlow AI - Main Application Entry Point
Handles navigation between Home (Auth) and Admin Dashboard
"""

import streamlit as st
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Page config
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

# Custom CSS - Ochre/Cream Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    :root {
        --ochre: #c4a35a;
        --ochre-dark: #a8893d;
        --ochre-light: #d4b86a;
        --cream: #faf8f5;
        --cream-dark: #f5f2eb;
        --brown: #5c4a32;
        --brown-light: #7a6548;
        --text-primary: #3d3425;
        --text-secondary: #6b5d4d;
        --text-muted: #9a8b78;
        --border-color: #e8e4dc;
        --success: #6b8e5e;
        --warning: #d4a357;
        --danger: #c45c4a;
    }
    
    * { font-family: 'DM Sans', sans-serif !important; }
    
    .stApp {
        background: linear-gradient(135deg, var(--cream) 0%, var(--cream-dark) 100%);
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

def show_home_page():
    """Display the home/auth page"""
    from home.app import main as home_main
    home_main()

def show_admin_dashboard():
    """Display the admin dashboard"""
    from admin_dashboard.app import main as admin_main
    admin_main()

def main():
    # Check authentication status
    if st.session_state.authenticated:
        # User is logged in, show appropriate dashboard
        if st.session_state.user_role == "admin":
            show_admin_dashboard()
        elif st.session_state.user_role == "doctor":
            st.info("🩺 Doctor Dashboard coming soon!")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user_email = None
                st.session_state.user_role = None
                st.rerun()
        else:
            st.info("👤 Staff Dashboard coming soon!")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user_email = None
                st.session_state.user_role = None
                st.rerun()
    else:
        # Not logged in, show home/auth page
        show_home_page()

if __name__ == "__main__":
    main()
