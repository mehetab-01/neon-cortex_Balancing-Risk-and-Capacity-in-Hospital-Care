"""
VitalFlow AI - Home & Authentication
"""

import streamlit as st
import sys
import os

# Add VitalFlow directory to path for imports
vitalflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, vitalflow_dir)

try:
    from config.google_auth import GoogleOAuthConfig, SimpleGoogleAuth
    GOOGLE_AUTH_AVAILABLE = True
except Exception as e:
    GOOGLE_AUTH_AVAILABLE = False
    print(f"Google Auth not available: {e}")

# Page config
st.set_page_config(
    page_title="VitalFlow AI",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    :root {
        --cream: #faf8f5;
        --cream-dark: #f0ebe3;
        --ochre: #c4a35a;
        --ochre-dark: #a68b4b;
        --brown: #5c4a32;
        --text-dark: #2d2a26;
        --text-muted: #6b6560;
        --border: #e0d8cc;
        --radius: 10px;
    }
    
    * { font-family: 'DM Sans', sans-serif; margin: 0; padding: 0; }
    html, body, [data-testid="stAppViewContainer"] { background: var(--cream) !important; }
    .stApp { background: var(--cream); }
    .main .block-container { padding: 0 !important; max-width: 100%; margin: 0 !important; }
    #MainMenu, footer, header { display: none !important; visibility: hidden !important; }
    [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
    .element-container { margin: 0 !important; padding: 0 !important; }
    
    /* Hide empty elements */
    .element-container:empty { display: none !important; }
    div[data-testid="stMarkdownContainer"]:empty { display: none !important; }
    div[data-testid="column"]:empty { display: none !important; }
    
    /* Remove all Streamlit padding */
    .stMarkdown { margin: 0 !important; padding: 0 !important; }
    section[data-testid="stVerticalBlock"] { gap: 0 !important; }
    div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; padding: 0 !important; }
    
    /* Hero Section */
    .hero {
        padding: 3rem 3rem 2rem;
        text-align: center;
        max-width: 850px;
        margin: 0 auto;
    }
    .hero h1 {
        font-size: 2.75rem;
        font-weight: 700;
        color: var(--text-dark);
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    .hero h1 span { color: var(--ochre); }
    .hero p {
        font-size: 1.05rem;
        color: var(--text-muted);
        line-height: 1.7;
        margin-bottom: 1.5rem;
    }
    
    /* Features Grid */
    .features {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.25rem;
        padding: 1.5rem 3rem 3rem;
        max-width: 1100px;
        margin: 0 auto;
    }
    .feature-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    .feature-icon {
        width: 44px;
        height: 44px;
        background: var(--cream-dark);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.75rem;
        font-size: 1.25rem;
    }
    .feature-card h3 {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 0.4rem;
    }
    .feature-card p {
        font-size: 0.8rem;
        color: var(--text-muted);
        line-height: 1.5;
    }
    
    /* User Type Tabs */
    .user-tabs {
        display: flex;
        background: var(--cream);
        border-radius: var(--radius);
        padding: 0.25rem;
        margin-bottom: 1rem;
    }
    
    /* Google Button */
    .google-btn {
        width: 100%;
        background: white;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 0.7rem;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-dark);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s;
    }
    .google-btn:hover { background: var(--cream); border-color: var(--ochre); }
    
    /* Divider */
    .divider { display: flex; align-items: center; gap: 0.75rem; margin: 0.75rem 0; }
    .divider-line { flex: 1; height: 1px; background: var(--border); }
    .divider-text { color: var(--text-muted); font-size: 0.75rem; }
    
    /* Form styling */
    .stTextInput > div > div > input {
        background: white !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.875rem !important;
        color: #2d2a26 !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #9a948c !important;
        opacity: 1 !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--ochre) !important;
        box-shadow: 0 0 0 2px rgba(196, 163, 90, 0.15) !important;
    }
    .stTextInput > label { 
        font-size: 0.85rem !important; 
        font-weight: 600 !important; 
        color: #2d2a26 !important; 
    }
    
    .stSelectbox > div > div { 
        background: white !important; 
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important; 
    }
    .stSelectbox label { 
        font-size: 0.85rem !important; 
        font-weight: 600 !important; 
        color: #2d2a26 !important; 
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background: white !important;
        color: #2d2a26 !important;
    }
    .stSelectbox [role="option"] {
        color: #2d2a26 !important;
    }
    
    .stButton > button {
        background: var(--ochre) !important;
        border: none !important;
        border-radius: var(--radius) !important;
        padding: 0.65rem 1.25rem !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        color: white !important;
    }
    .stButton > button:hover { background: var(--ochre-dark) !important; }
    .stButton > button[kind="secondary"] {
        background: white !important;
        border: 1px solid var(--border) !important;
        color: var(--text-dark) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--ochre) !important;
        color: var(--ochre) !important;
    }
    
    /* Login card */
    .login-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(92, 74, 50, 0.06);
    }
    
    @media (max-width: 900px) {
        .features { grid-template-columns: repeat(2, 1fr); }
        .hero h1 { font-size: 2rem; }
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# SESSION STATE
# ============================================
if 'show_login' not in st.session_state:
    st.session_state.show_login = False
if 'login_type' not in st.session_state:
    st.session_state.login_type = 'admin'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'google_auth' not in st.session_state and GOOGLE_AUTH_AVAILABLE:
    config = GoogleOAuthConfig()
    if config.is_configured:
        st.session_state.google_auth = SimpleGoogleAuth(config)
    else:
        st.session_state.google_auth = None


# ============================================
# MOCK USERS
# ============================================
MOCK_USERS = {
    'admin@vitalflow.ai': {'password': 'admin123', 'role': 'admin', 'name': 'Admin User'},
    'doctor@vitalflow.ai': {'password': 'doctor123', 'role': 'doctor', 'name': 'Dr. Smith'},
    'nurse@vitalflow.ai': {'password': 'nurse123', 'role': 'nurse', 'name': 'Nurse Johnson'},
}

def authenticate(email: str, password: str) -> dict:
    user = MOCK_USERS.get(email.lower())
    if user and user['password'] == password:
        return {'success': True, 'user': user}
    return {'success': False, 'error': 'Invalid credentials'}


# ============================================
# MAIN UI
# ============================================

if st.session_state.authenticated:
    # Logged in view
    st.markdown(f"""
    <div style="text-align: center; padding: 3rem 2rem;">
        <h1 style="color: #2d2a26; font-size: 1.75rem; margin-bottom: 0.5rem;">Welcome, {st.session_state.user_name}!</h1>
        <p style="color: #6b6560; margin-bottom: 1.5rem;">Logged in as <strong>{st.session_state.user_role.title()}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.info("✅ Run `streamlit run admin_dashboard/app.py` for dashboard")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.user_name = None
            st.session_state.show_login = False
            st.rerun()

else:
    # ===== TOP NAV BAR =====
    if st.session_state.show_login:
        nav1, nav2, nav3 = st.columns([0.8, 4, 0.1])
        with nav1:
            if st.button("← Back", key="nav_back", type="secondary"):
                st.session_state.show_login = False
                st.rerun()
        with nav2:
            st.markdown("<h2 style='color:#2d2a26; text-align:center; margin:0.5rem 0;'>VitalFlow <span style='color:#c4a35a;'>AI</span></h2>", unsafe_allow_html=True)
    else:
        nav1, nav2, nav3 = st.columns([4, 0.8, 0.9])
        with nav1:
            st.markdown("<h2 style='color:#2d2a26; margin:0.5rem 0 0 1rem;'>VitalFlow <span style='color:#c4a35a;'>AI</span></h2>", unsafe_allow_html=True)
        with nav2:
            if st.button("Sign In", key="nav_signin", type="secondary"):
                st.session_state.show_login = True
                st.rerun()
        with nav3:
            if st.button("Get Started", key="nav_signup"):
                st.session_state.show_login = True
                st.rerun()
    
    st.markdown("<hr style='margin:0.5rem 0; border:none; border-top:1px solid #e0d8cc;'>", unsafe_allow_html=True)
    
    if not st.session_state.show_login:
        # ===== HERO SECTION =====
        st.markdown("""
        <div class="hero">
            <h1>Intelligent Hospital <span>Command Center</span></h1>
            <p>
                VitalFlow AI transforms hospital operations with real-time bed management, 
                AI-powered patient prioritization, and seamless coordination across your healthcare network.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # ===== FEATURES =====
        st.markdown("""
        <div class="features">
            <div class="feature-card">
                <div class="feature-icon">🛏️</div>
                <h3>Bed Management</h3>
                <p>Real-time tracking of bed occupancy across departments.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <h3>AI Decisions</h3>
                <p>Smart patient prioritization powered by AI.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">👥</div>
                <h3>Staff Coordination</h3>
                <p>Optimize staff assignments automatically.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>Analytics</h3>
                <p>Insights for data-driven decisions.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # ===== LOGIN PAGE =====
        st.markdown("<h2 style='text-align:center; color:#2d2a26; margin: 1.5rem 0 1rem;'>Sign In to VitalFlow AI</h2>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.3, 1])
        
        with col2:
            st.markdown("<div class='login-card'>", unsafe_allow_html=True)
            
            # User type selection: Admin vs Staff
            st.markdown("<p style='font-weight:600; color:#2d2a26; margin: 0.75rem 0 0.5rem;'>I am a:</p>", unsafe_allow_html=True)
            t1, t2 = st.columns(2)
            with t1:
                if st.button("🔐 Admin", key="tab_admin", use_container_width=True, 
                            type="primary" if st.session_state.login_type == 'admin' else "secondary"):
                    st.session_state.login_type = 'admin'
                    st.rerun()
            with t2:
                if st.button("👤 Staff", key="tab_staff", use_container_width=True,
                            type="primary" if st.session_state.login_type == 'staff' else "secondary"):
                    st.session_state.login_type = 'staff'
                    st.rerun()
            
            st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
            
            # Google Auth - Check if configured
            if GOOGLE_AUTH_AVAILABLE and st.session_state.get('google_auth'):
                # Google Auth is configured and available
                if st.button("🔑 Continue with Google", key="google_auth_btn", use_container_width=True, type="secondary"):
                    auth = st.session_state.google_auth
                    auth_url = auth.get_auth_url()
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
                    st.info("Redirecting to Google...")
            else:
                # Mock Google button (not configured)
                st.markdown("""
                <button class="google-btn" onclick="alert('Google OAuth Setup Required:\\n\\n1. Go to console.cloud.google.com\\n2. Create OAuth credentials\\n3. Set Client ID and Secret in config/google_auth.py\\n\\nFor now, use email login below!')">
                    <svg width="18" height="18" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Continue with Google (Setup Required)
                </button>
                """, unsafe_allow_html=True)
            
            st.markdown('<div class="divider"><div class="divider-line"></div><span class="divider-text">or use email</span><div class="divider-line"></div></div>', unsafe_allow_html=True)
            
            # Staff role selection (only for staff)
            if st.session_state.login_type == 'staff':
                role = st.selectbox("Select Your Role", ["Doctor", "Nurse", "Ward Boy", "Ambulance Driver"])
            
            # Email & Password
            email = st.text_input("Email", placeholder="you@hospital.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            if st.button("Sign In", key="login_submit", use_container_width=True):
                if email and password:
                    result = authenticate(email, password)
                    if result['success']:
                        st.session_state.authenticated = True
                        st.session_state.user_role = result['user']['role']
                        st.session_state.user_name = result['user']['name']
                        st.session_state.show_login = False
                        st.rerun()
                    else:
                        st.error(result['error'])
                else:
                    st.warning("Please enter email and password")
            
            # Demo info
            if st.session_state.login_type == 'admin':
                st.markdown("<p style='text-align:center;color:#9a948c;font-size:0.75rem;margin-top:0.75rem;'>Demo: admin@vitalflow.ai / admin123</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='text-align:center;color:#9a948c;font-size:0.75rem;margin-top:0.75rem;'>Demo: doctor@vitalflow.ai / doctor123</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div style='text-align:center;padding:1.5rem;color:#9a948c;font-size:0.7rem;border-top:1px solid #e0d8cc;margin-top:2rem;'>© 2026 VitalFlow AI · Neon Cortex</div>", unsafe_allow_html=True)
