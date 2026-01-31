"""
VitalFlow AI - Staff Mobile Interface
Main Application Entry Point

This is the main Streamlit app for the mobile staff interface.
Run with: streamlit run app.py
"""
import streamlit as st
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="VitalFlow Staff",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# UI STYLE ONLY - VitalFlow Professional Healthcare Theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* UI STYLE ONLY - Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* UI STYLE ONLY - Mobile container with healthcare background */
    .stApp {
        max-width: 480px;
        margin: 0 auto;
        background: #F4F7FA !important;
        min-height: 100vh;
    }
    
    [data-testid="stAppViewContainer"] {
        background: #F4F7FA !important;
    }
    
    .main .block-container {
        background: #F4F7FA !important;
        padding: 1rem 1rem 3rem 1rem !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* UI STYLE ONLY - Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #E9EEF3;
    }
    ::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #2F80ED;
    }
    
    /* UI STYLE ONLY - Unified touch-friendly buttons */
    .stButton > button {
        width: 100%;
        height: 72px;
        font-size: 16px;
        font-weight: 600;
        margin: 6px 0;
        border-radius: 12px;
        border: 1px solid #CBD5E1 !important;
        background: #E9EEF3 !important;
        color: #1F2937 !important;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
        letter-spacing: 0.2px;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(47, 128, 237, 0.2);
        border-color: #2F80ED !important;
        background: #FFFFFF !important;
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* UI STYLE ONLY - Primary button style */
    .stButton > button[kind="primary"] {
        background: #2F80ED !important;
        border-color: #2F80ED !important;
        color: white !important;
    }
    
    /* UI STYLE ONLY - UNIFIED Role selector buttons - ALL same color #2F80ED */
    div[data-testid="stVerticalBlock"] > div:nth-child(4) .stButton > button,
    div[data-testid="stVerticalBlock"] > div:nth-child(5) .stButton > button,
    div[data-testid="stVerticalBlock"] > div:nth-child(6) .stButton > button,
    div[data-testid="stVerticalBlock"] > div:nth-child(7) .stButton > button {
        background: #2F80ED !important;
        border-color: #2F80ED !important;
        color: white !important;
    }
    
    div[data-testid="stVerticalBlock"] > div:nth-child(4) .stButton > button:hover,
    div[data-testid="stVerticalBlock"] > div:nth-child(5) .stButton > button:hover,
    div[data-testid="stVerticalBlock"] > div:nth-child(6) .stButton > button:hover,
    div[data-testid="stVerticalBlock"] > div:nth-child(7) .stButton > button:hover {
        background: #1a6fd4 !important;
        box-shadow: 0 6px 16px rgba(47, 128, 237, 0.35);
    }
    
    /* UI STYLE ONLY - Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 26px;
        font-weight: 700;
        color: #2F80ED !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 12px;
        font-weight: 500;
        color: #4B5563 !important;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    
    [data-testid="stMetricDelta"] {
        color: #27AE60 !important;
    }
    
    /* UI STYLE ONLY - Card styling */
    .stAlert {
        border-radius: 10px;
        border: 1px solid #CBD5E1;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }
    
    /* UI STYLE ONLY - Success alert */
    .stAlert[data-baseweb="notification"] {
        background: #E9EEF3;
        border-left: 3px solid #27AE60;
    }
    
    /* UI STYLE ONLY - Info alert */
    div[data-baseweb="notification"][kind="info"] {
        background: #E9EEF3;
        border-left: 3px solid #2F80ED;
    }
    
    /* UI STYLE ONLY - Warning alert */
    div[data-baseweb="notification"][kind="warning"] {
        background: #E9EEF3;
        border-left: 3px solid #F2994A;
    }
    
    /* UI STYLE ONLY - Error alert */
    div[data-baseweb="notification"][kind="negative"] {
        background: #E9EEF3;
        border-left: 3px solid #EB5757;
    }
    
    /* UI STYLE ONLY - Checkbox styling */
    .stCheckbox {
        padding: 10px 14px;
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        margin: 4px 0;
        transition: all 0.2s ease;
    }
    
    .stCheckbox:hover {
        background: #FFFFFF;
        border-color: #2F80ED;
    }
    
    .stCheckbox label {
        color: #1F2937 !important;
    }
    
    /* UI STYLE ONLY - Expander styling */
    .streamlit-expanderHeader {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        font-weight: 500;
        color: #1F2937;
    }
    
    .streamlit-expanderHeader:hover {
        background: #FFFFFF;
        border-color: #2F80ED;
    }
    
    /* UI STYLE ONLY - Progress bar */
    .stProgress > div > div {
        background: #2F80ED;
        border-radius: 6px;
    }
    
    .stProgress {
        background: #CBD5E1;
        border-radius: 6px;
    }
    
    /* UI STYLE ONLY - Divider */
    hr {
        border: none;
        height: 1px;
        background: #CBD5E1;
        margin: 20px 0;
    }
    
    /* Column containers */
    [data-testid="column"] {
        padding: 4px;
    }
    
    /* UI STYLE ONLY - Caption text */
    .stCaption {
        color: #4B5563 !important;
        font-size: 12px;
    }
    
    /* UI STYLE ONLY - Markdown headings */
    h1 {
        color: #1F2937 !important;
        font-weight: 700 !important;
        font-size: 24px !important;
    }
    
    h2 {
        color: #1F2937 !important;
        font-weight: 600 !important;
        font-size: 20px !important;
    }
    
    h3 {
        color: #1F2937 !important;
        font-weight: 600 !important;
        font-size: 17px !important;
        margin-top: 16px !important;
        margin-bottom: 10px !important;
    }
    
    h4 {
        color: #4B5563 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    /* UI STYLE ONLY - Paragraph text */
    p, span, div {
        color: #1F2937;
    }
    
    /* UI STYLE ONLY - Strong text */
    strong {
        color: #1F2937;
        font-weight: 600;
    }
    
    /* UI STYLE ONLY - Link styling */
    a {
        color: #2F80ED !important;
    }
    
    a:hover {
        color: #1a6fd4 !important;
    }
    
    /* UI STYLE ONLY - Back button styling */
    div[data-testid="stVerticalBlock"] > div:first-child .stButton > button {
        height: 42px;
        font-size: 14px;
        background: #E9EEF3 !important;
        border: 1px solid #CBD5E1 !important;
        color: #4B5563 !important;
    }
    
    div[data-testid="stVerticalBlock"] > div:first-child .stButton > button:hover {
        background: #FFFFFF !important;
        border-color: #2F80ED !important;
        color: #2F80ED !important;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .stAlert {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* UI STYLE ONLY - Card styling */
    .glass-card {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }
    
    /* UI STYLE ONLY - Select box styling */
    .stSelectbox [data-baseweb="select"] {
        background: #E9EEF3;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
    }
    
    .stTextInput input {
        background: #E9EEF3 !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #1F2937 !important;
    }
    
    .stTextInput input:focus {
        border-color: #2F80ED !important;
        box-shadow: 0 0 0 2px rgba(47, 128, 237, 0.15) !important;
    }
    
    /* UI STYLE ONLY - Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: #E9EEF3;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #4B5563;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: #2F80ED !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'selected_role' not in st.session_state:
        st.session_state.selected_role = None
    if 'staff_id' not in st.session_state:
        st.session_state.staff_id = None
    if 'staff_name' not in st.session_state:
        st.session_state.staff_name = None
    if 'is_on_duty' not in st.session_state:
        st.session_state.is_on_duty = False
    if 'shift_start' not in st.session_state:
        st.session_state.shift_start = None


def render_header():
    """Render app header - UI STYLE ONLY"""
    st.markdown("""
    <div style="
        text-align: center;
        padding: 28px 20px 22px 20px;
        background: #E9EEF3;
        border-bottom: 1px solid #CBD5E1;
        margin: -16px -16px 24px -16px;
    ">
        <div style="
            width: 56px;
            height: 56px;
            background: #2F80ED;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 12px auto;
            font-size: 28px;
            box-shadow: 0 4px 12px rgba(47, 128, 237, 0.25);
        ">🏥</div>
        <h1 style="
            font-size: 22px;
            font-weight: 700;
            color: #1F2937;
            margin: 0 0 4px 0;
            letter-spacing: -0.3px;
        ">VitalFlow AI</h1>
        <p style="
            font-size: 12px;
            color: #4B5563;
            margin: 0;
            font-weight: 500;
            letter-spacing: 0.3px;
        ">Staff Mobile Interface</p>
    </div>
    """, unsafe_allow_html=True)


def render_role_selector():
    """Render the role selection screen"""
    render_header()
    
    # UI STYLE ONLY - Role selector intro
    st.markdown("""
    <div style="text-align: center; margin: 8px 0 20px 0;">
        <p style="
            font-size: 15px;
            color: #1F2937;
            font-weight: 600;
            margin: 0;
        ">Select Your Role</p>
        <p style="
            font-size: 13px;
            color: #4B5563;
            margin: 6px 0 0 0;
        ">Access your personalized dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Role buttons with icons
    roles = [
        {"name": "Doctor", "icon": "👨‍⚕️", "id": "D001", "class": "doctor"},
        {"name": "Nurse", "icon": "👩‍⚕️", "id": "N001", "class": "nurse"},
        {"name": "Ward Boy", "icon": "🧑‍🔧", "id": "W001", "class": "wardboy"},
        {"name": "Driver", "icon": "🚑", "id": "DR001", "class": "driver"},
    ]
    
    for role in roles:
        if st.button(
            f'{role["icon"]}  {role["name"]}',
            key=f'role_{role["name"].lower().replace(" ", "_")}',
            use_container_width=True
        ):
            st.session_state.selected_role = role["name"]
            st.session_state.staff_id = role["id"]
            st.session_state.staff_name = f"Demo {role['name']}"
            st.rerun()
    
    # UI STYLE ONLY - Footer info
    st.markdown("""
    <div style="
        text-align: center;
        margin-top: 32px;
        padding: 16px;
        border-top: 1px solid #CBD5E1;
    ">
        <p style="
            font-size: 12px;
            color: #4B5563;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        ">🔒 Secure Healthcare Platform</p>
        <p style="
            font-size: 11px;
            color: #6B7280;
            margin: 6px 0 0 0;
        ">v2.0 • Powered by VitalFlow AI</p>
    </div>
    """, unsafe_allow_html=True)


def render_back_button():
    """Render back to role selection button"""
    if st.button("← Back to Role Selection", key="back_btn"):
        st.session_state.selected_role = None
        st.session_state.staff_id = None
        st.session_state.is_on_duty = False
        st.rerun()


def main():
    """Main application entry point"""
    init_session_state()
    
    # Route based on selected role
    if st.session_state.selected_role is None:
        render_role_selector()
    else:
        # Import and render the appropriate view
        role = st.session_state.selected_role
        
        if role == "Doctor":
            from pages.doctor_view import render_doctor_view
            render_back_button()
            render_doctor_view()
            
        elif role == "Nurse":
            from pages.nurse_view import render_nurse_view
            render_back_button()
            render_nurse_view()
            
        elif role == "Ward Boy":
            from pages.wardboy_view import render_wardboy_view
            render_back_button()
            render_wardboy_view()
            
        elif role == "Driver":
            from pages.driver_view import render_driver_view
            render_back_button()
            render_driver_view()


if __name__ == "__main__":
    main()
