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

# ============================================
# MOCK USERS
# ============================================
MOCK_USERS = {
    # Admin users
    'admin@vitalflow.ai': {'password': 'admin123', 'role': 'admin', 'name': 'Admin User'},
    # Staff users - different roles
    'doctor@vitalflow.ai': {'password': 'doctor123', 'role': 'doctor', 'name': 'Dr. Smith', 'staff_id': 'D001'},
    'nurse@vitalflow.ai': {'password': 'nurse123', 'role': 'nurse', 'name': 'Nurse Johnson', 'staff_id': 'N001'},
    'wardboy@vitalflow.ai': {'password': 'wardboy123', 'role': 'wardboy', 'name': 'Ward Boy Kumar', 'staff_id': 'W001'},
    'driver@vitalflow.ai': {'password': 'driver123', 'role': 'driver', 'name': 'Driver Sharma', 'staff_id': 'DR001'},
}

# Role mapping for staff selection
STAFF_ROLES = ['Doctor', 'Nurse', 'Ward Boy', 'Ambulance Driver']
ROLE_MAPPING = {
    'Doctor': 'doctor',
    'Nurse': 'nurse',
    'Ward Boy': 'wardboy',
    'Ambulance Driver': 'driver'
}


def authenticate(email: str, password: str, selected_role: str = None) -> dict:
    """Authenticate user with email/password or create staff session"""
    user = MOCK_USERS.get(email.lower())
    if user and user['password'] == password:
        return {'success': True, 'user': user}

    # For staff login with role selection, create a demo session
    if selected_role and email and password:
        role_key = ROLE_MAPPING.get(selected_role, 'staff')
        return {
            'success': True,
            'user': {
                'role': role_key,
                'name': f'Demo {selected_role}',
                'staff_id': f'{role_key[:1].upper()}001'
            }
        }

    return {'success': False, 'error': 'Invalid credentials'}


def authenticate_google_user(user_info: dict, login_type: str) -> dict:
    """Authenticate user from Google OAuth response"""
    email = user_info.get('email', '')
    name = user_info.get('name', email.split('@')[0])

    # Check if email exists in mock users
    if email.lower() in MOCK_USERS:
        user = MOCK_USERS[email.lower()]
        return {'success': True, 'user': user}

    # For new Google users, assign role based on login_type selection
    if login_type == 'admin':
        role = 'admin'
    else:
        role = 'doctor'  # Default staff role

    return {
        'success': True,
        'user': {
            'role': role,
            'name': name,
            'email': email,
            'staff_id': f'{role[0].upper()}001'
        }
    }


def _handle_oauth_callback():
    """Handle Google OAuth callback"""
    # Check for authorization code in URL
    query_params = st.query_params

    if 'code' in query_params:
        code = query_params.get('code')

        if GOOGLE_AUTH_AVAILABLE and st.session_state.get('google_auth'):
            auth = st.session_state.google_auth

            # Exchange code for tokens
            tokens = auth.exchange_code(code)

            if tokens and 'access_token' in tokens:
                # Get user info
                user_info = auth.get_user_info(tokens['access_token'])

                if user_info:
                    # Authenticate the Google user
                    login_type = st.session_state.get('login_type', 'admin')
                    result = authenticate_google_user(user_info, login_type)

                    if result['success']:
                        st.session_state.authenticated = True
                        st.session_state.user_role = result['user']['role']
                        st.session_state.user_name = result['user']['name']
                        if 'staff_id' in result['user']:
                            st.session_state.staff_id = result['user']['staff_id']
                        st.session_state.show_login = False

                        # Clear the URL params
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error("Google authentication failed")
                else:
                    st.error("Could not get user info from Google")
            else:
                st.error("Could not exchange authorization code")

        # Clear the code from URL to prevent reuse
        st.query_params.clear()


def _init_session_state():
    """Initialize session state variables"""
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
    if 'staff_id' not in st.session_state:
        st.session_state.staff_id = None
    if 'google_auth' not in st.session_state and GOOGLE_AUTH_AVAILABLE:
        try:
            config = GoogleOAuthConfig()
            if config.is_configured:
                st.session_state.google_auth = SimpleGoogleAuth(config)
            else:
                st.session_state.google_auth = None
        except:
            st.session_state.google_auth = None


def _apply_css():
    """Apply custom CSS styles"""
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

        .element-container:empty { display: none !important; }
        div[data-testid="stMarkdownContainer"]:empty { display: none !important; }
        div[data-testid="column"]:empty { display: none !important; }

        .stMarkdown { margin: 0 !important; padding: 0 !important; }
        section[data-testid="stVerticalBlock"] { gap: 0 !important; }
        div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; padding: 0 !important; }

        .hero { padding: 3rem 3rem 2rem; text-align: center; max-width: 850px; margin: 0 auto; }
        .hero h1 { font-size: 2.75rem; font-weight: 700; color: var(--text-dark); margin-bottom: 1rem; line-height: 1.2; }
        .hero h1 span { color: var(--ochre); }
        .hero p { font-size: 1.05rem; color: var(--text-muted); line-height: 1.7; margin-bottom: 1.5rem; }

        .features { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem; padding: 1.5rem 3rem 3rem; max-width: 1100px; margin: 0 auto; }
        .feature-card { background: white; border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; text-align: center; }
        .feature-icon { width: 44px; height: 44px; background: var(--cream-dark); border-radius: 10px; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.75rem; font-size: 1.25rem; }
        .feature-card h3 { font-size: 0.9rem; font-weight: 600; color: var(--text-dark); margin-bottom: 0.4rem; }
        .feature-card p { font-size: 0.8rem; color: var(--text-muted); line-height: 1.5; }

        .google-btn { width: 100%; background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 0.7rem; font-size: 0.875rem; font-weight: 500; color: var(--text-dark); cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-bottom: 0.75rem; transition: all 0.2s; }
        .google-btn:hover { background: var(--cream); border-color: var(--ochre); }

        .divider { display: flex; align-items: center; gap: 0.75rem; margin: 0.75rem 0; }
        .divider-line { flex: 1; height: 1px; background: var(--border); }
        .divider-text { color: var(--text-muted); font-size: 0.75rem; }

        .stTextInput > div > div > input { background: white !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; padding: 0.7rem 1rem !important; font-size: 0.875rem !important; color: #2d2a26 !important; }
        .stTextInput > div > div > input:focus { border-color: var(--ochre) !important; box-shadow: 0 0 0 2px rgba(196, 163, 90, 0.15) !important; }
        .stTextInput > label { font-size: 0.85rem !important; font-weight: 600 !important; color: #2d2a26 !important; }

        .stSelectbox > div > div { background: white !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
        .stSelectbox label { font-size: 0.85rem !important; font-weight: 600 !important; color: #2d2a26 !important; }

        .stButton > button { background: var(--ochre) !important; border: none !important; border-radius: var(--radius) !important; padding: 0.65rem 1.25rem !important; font-weight: 600 !important; font-size: 0.875rem !important; color: white !important; }
        .stButton > button:hover { background: var(--ochre-dark) !important; }
        .stButton > button[kind="secondary"] { background: white !important; border: 1px solid var(--border) !important; color: var(--text-dark) !important; }
        .stButton > button[kind="secondary"]:hover { border-color: var(--ochre) !important; color: var(--ochre) !important; }

        .login-card { background: white; border: 1px solid var(--border); border-radius: 14px; padding: 1.5rem; box-shadow: 0 2px 12px rgba(92, 74, 50, 0.06); }

        @media (max-width: 900px) { .features { grid-template-columns: repeat(2, 1fr); } .hero h1 { font-size: 2rem; } }
    </style>
    """, unsafe_allow_html=True)


def _render_navbar():
    """Render the navigation bar"""
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


def _render_hero():
    """Render hero section"""
    st.markdown("""
    <div class="hero">
        <h1>Intelligent Hospital <span>Command Center</span></h1>
        <p>VitalFlow AI transforms hospital operations with real-time bed management,
        AI-powered patient prioritization, and seamless coordination across your healthcare network.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="features">
        <div class="feature-card"><div class="feature-icon">🛏️</div><h3>Bed Management</h3><p>Real-time tracking of bed occupancy across departments.</p></div>
        <div class="feature-card"><div class="feature-icon">🤖</div><h3>AI Decisions</h3><p>Smart patient prioritization powered by AI.</p></div>
        <div class="feature-card"><div class="feature-icon">👥</div><h3>Staff Coordination</h3><p>Optimize staff assignments automatically.</p></div>
        <div class="feature-card"><div class="feature-icon">📊</div><h3>Analytics</h3><p>Insights for data-driven decisions.</p></div>
    </div>
    """, unsafe_allow_html=True)


def _render_login():
    """Render login form"""
    st.markdown("<h2 style='text-align:center; color:#2d2a26; margin: 1.5rem 0 1rem;'>Sign In to VitalFlow AI</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.3, 1])

    with col2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        # User type selection
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

        # Google Auth button
        google_configured = GOOGLE_AUTH_AVAILABLE and st.session_state.get('google_auth')

        if google_configured:
            if st.button("🔑 Continue with Google", key="google_auth_btn", use_container_width=True, type="secondary"):
                auth = st.session_state.google_auth
                auth_url = auth.get_auth_url(state=st.session_state.login_type)
                st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
                st.info("Redirecting to Google...")
        else:
            # Show setup instructions
            with st.expander("🔑 Sign in with Google (Setup Required)"):
                st.markdown("""
                **To enable Google Sign-In:**

                1. Go to [Google Cloud Console](https://console.cloud.google.com)
                2. Create OAuth 2.0 credentials
                3. Add your Client ID and Secret to `.env` file:

                ```
                GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
                GOOGLE_CLIENT_SECRET=your-secret
                ```

                4. Restart the application
                """)

        st.markdown('<div class="divider"><div class="divider-line"></div><span class="divider-text">or use email</span><div class="divider-line"></div></div>', unsafe_allow_html=True)

        # Staff role selection
        role = None
        if st.session_state.login_type == 'staff':
            role = st.selectbox("Select Your Role", ["Doctor", "Nurse", "Ward Boy", "Ambulance Driver"])

        # Email & Password
        email = st.text_input("Email", placeholder="you@hospital.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")

        if st.button("Sign In", key="login_submit", use_container_width=True):
            if email and password:
                selected_role = role if st.session_state.login_type == 'staff' else None
                result = authenticate(email, password, selected_role)
                if result['success']:
                    st.session_state.authenticated = True
                    st.session_state.user_role = result['user']['role']
                    st.session_state.user_name = result['user']['name']
                    if 'staff_id' in result['user']:
                        st.session_state.staff_id = result['user']['staff_id']
                    st.session_state.show_login = False
                    st.rerun()
                else:
                    st.error(result['error'])
            else:
                st.warning("Please enter email and password")

        # Demo credentials hint
        if st.session_state.login_type == 'admin':
            st.markdown("<p style='text-align:center;color:#9a948c;font-size:0.75rem;margin-top:0.75rem;'>Demo: admin@vitalflow.ai / admin123</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align:center;color:#9a948c;font-size:0.75rem;margin-top:0.75rem;'>Demo: doctor@vitalflow.ai / doctor123</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main function for the home/auth page"""
    _init_session_state()
    _apply_css()

    # Handle OAuth callback (for standalone mode)
    _handle_oauth_callback()

    # If authenticated, main.py will handle routing - don't show anything here
    if st.session_state.authenticated:
        # This shouldn't normally be reached when run from main.py
        # But if running standalone, show a redirect message
        st.markdown(f"""
        <div style="text-align: center; padding: 3rem 2rem;">
            <h1 style="color: #2d2a26; font-size: 1.75rem; margin-bottom: 0.5rem;">Welcome, {st.session_state.user_name}!</h1>
            <p style="color: #6b6560; margin-bottom: 1.5rem;">Redirecting to dashboard...</p>
        </div>
        """, unsafe_allow_html=True)
        return  # Let main.py handle the routing

    # Not logged in - show home page or login
    _render_navbar()

    if not st.session_state.show_login:
        _render_hero()
    else:
        _render_login()

    # Footer
    st.markdown("<div style='text-align:center;padding:1.5rem;color:#9a948c;font-size:0.7rem;border-top:1px solid #e0d8cc;margin-top:2rem;'>© 2026 VitalFlow AI · Neon Cortex</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        st.set_page_config(
            page_title="VitalFlow AI",
            page_icon="⚕️",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
    except st.errors.StreamlitAPIException:
        pass
    main()
