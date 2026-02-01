"""
VitalFlow - Google Authentication Service
Handles Google OAuth sign-in for the frontend
Supports both local development and Streamlit Cloud deployment
"""
import streamlit as st
import sys
import os
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import secrets

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env file first
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


def get_secret(key: str, default: str = None) -> Optional[str]:
    """
    Get secret from environment or Streamlit secrets.
    Priority: Environment Variables > Streamlit Secrets > Default
    """
    # Check environment variables first
    value = os.getenv(key)
    if value:
        return value
    
    # Check Streamlit secrets (for Streamlit Cloud deployment)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    
    return default


@dataclass
class UserInfo:
    """Authenticated user information."""
    email: str
    name: str
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    locale: Optional[str] = None
    verified_email: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "locale": self.locale,
            "verified_email": self.verified_email
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserInfo':
        return cls(
            email=data.get("email", ""),
            name=data.get("name", ""),
            picture=data.get("picture"),
            given_name=data.get("given_name"),
            family_name=data.get("family_name"),
            locale=data.get("locale"),
            verified_email=data.get("verified_email", True)
        )


class GoogleAuthService:
    """
    Google Authentication Service for Streamlit.
    Supports both streamlit-google-auth package and manual OAuth flow.
    Works with local development (.env) and Streamlit Cloud (secrets.toml).
    """
    
    # OAuth URLs
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    def __init__(self):
        # Get credentials from environment or Streamlit secrets
        self.client_id = get_secret(
            "GOOGLE_CLIENT_ID", 
            "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
        )
        self.client_secret = get_secret(
            "GOOGLE_CLIENT_SECRET", 
            "YOUR_GOOGLE_CLIENT_SECRET"
        )
        
        # For deployment, redirect URI should be the deployed app URL
        # Auto-detect if running on Streamlit Cloud
        self.redirect_uri = self._get_redirect_uri()
        
        self.scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ]
        
        # Generate a session-specific state for CSRF protection
        if "oauth_state" not in st.session_state:
            st.session_state.oauth_state = secrets.token_urlsafe(32)
    
    def _get_redirect_uri(self) -> str:
        """
        Get the appropriate redirect URI based on environment.
        Supports local development and various deployment platforms.
        """
        # First check for explicitly configured redirect URI
        configured_uri = get_secret("GOOGLE_REDIRECT_URI")
        if configured_uri:
            return configured_uri
        
        # Auto-detect Streamlit Cloud
        try:
            # Check for Streamlit Cloud environment
            if os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("STREAMLIT_SERVER_HEADLESS"):
                # Try to get from query params or headers
                pass
        except:
            pass
        
        # Default to localhost for development
        return "http://localhost:8502/"
    
    @property
    def is_configured(self) -> bool:
        """Check if OAuth credentials are configured."""
        return (
            self.client_id != "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com" and
            self.client_secret != "YOUR_GOOGLE_CLIENT_SECRET" and
            "YOUR_" not in self.client_id and
            self.client_id is not None and
            self.client_secret is not None
        )
    
    def get_auth_url(self, state: str = None) -> str:
        """Generate Google OAuth authorization URL."""
        import urllib.parse
        
        # Use session-specific state for CSRF protection
        if state is None:
            state = st.session_state.get("oauth_state", "vitalflow_auth")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "state": state,
            "prompt": "select_account"
        }
        
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access tokens."""
        try:
            import requests
            
            response = requests.post(self.TOKEN_URL, data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Token exchange error: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[UserInfo]:
        """Get user information from Google."""
        try:
            import requests
            
            response = requests.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return UserInfo(
                    email=data.get("email", ""),
                    name=data.get("name", ""),
                    picture=data.get("picture"),
                    given_name=data.get("given_name"),
                    family_name=data.get("family_name"),
                    locale=data.get("locale"),
                    verified_email=data.get("verified_email", True)
                )
            return None
            
        except Exception as e:
            print(f"User info error: {e}")
            return None
    
    def handle_callback(self) -> Optional[UserInfo]:
        """Handle OAuth callback from Google."""
        # Check for authorization code in query params
        query_params = st.query_params
        
        code = query_params.get("code")
        state = query_params.get("state")
        
        # Validate state for CSRF protection
        expected_state = st.session_state.get("oauth_state", "vitalflow_auth")
        
        if code and (state == expected_state or state == "vitalflow_auth"):
            # Clear the URL params
            st.query_params.clear()
            
            # Exchange code for tokens
            tokens = self.exchange_code_for_tokens(code)
            
            if tokens and "access_token" in tokens:
                # Get user info
                user_info = self.get_user_info(tokens["access_token"])
                
                if user_info:
                    # Store in session
                    st.session_state.google_user = user_info.to_dict()
                    st.session_state.google_token = tokens["access_token"]
                    st.session_state.google_authenticated = True
                    st.session_state.auth_time = datetime.now().isoformat()
                    
                    # Store refresh token if available
                    if "refresh_token" in tokens:
                        st.session_state.google_refresh_token = tokens["refresh_token"]
                    
                    return user_info
        
        return None
    
    def get_current_user(self) -> Optional[UserInfo]:
        """Get the currently authenticated user."""
        if st.session_state.get("google_authenticated") and st.session_state.get("google_user"):
            return UserInfo.from_dict(st.session_state.google_user)
        return None
    
    def sign_out(self):
        """Sign out the current user."""
        keys_to_remove = [
            "google_user", "google_token", "google_authenticated",
            "logged_in", "portal", "show_login", "staff_role",
            "staff_logged_in", "current_staff_id", "current_patient_id"
        ]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def render_sign_in_button(self, button_text: str = "Sign in with Google") -> bool:
        """
        Render Google Sign-In button.
        Returns True if user clicks the button.
        """
        if not self.is_configured:
            st.warning("⚠️ Google Sign-In not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
            return False
        
        # Custom Google button styling
        st.markdown("""
        <style>
        .google-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
            color: #444;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            margin: 10px auto;
            max-width: 300px;
        }
        .google-btn:hover {
            background: #f8f9fa;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .google-logo {
            width: 20px;
            height: 20px;
            margin-right: 12px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        auth_url = self.get_auth_url()
        
        # Google logo SVG (official colors)
        google_logo = """<svg viewBox="0 0 24 24" class="google-logo"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>"""
        
        st.markdown(f"""
        <a href="{auth_url}" class="google-btn" target="_self">
            {google_logo}
            {button_text}
        </a>
        """, unsafe_allow_html=True)
        
        return False
    
    def render_user_profile(self, user: UserInfo, show_signout: bool = True):
        """Render user profile section."""
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if user.picture:
                st.image(user.picture, width=60)
            else:
                st.markdown("👤")
        
        with col2:
            st.markdown(f"**{user.name}**")
            st.caption(user.email)
        
        if show_signout:
            if st.button("🚪 Sign Out", key="google_signout"):
                self.sign_out()
                st.rerun()


# Singleton instance
google_auth_service = GoogleAuthService()


def render_google_login_option():
    """Render Google login option for the landing page."""
    st.markdown("---")
    st.markdown("##### Or sign in with")
    
    google_auth_service.render_sign_in_button()
    
    # Handle callback
    user = google_auth_service.handle_callback()
    if user:
        st.success(f"Welcome, {user.name}!")
        st.rerun()


def get_authenticated_user() -> Optional[UserInfo]:
    """Get the currently authenticated Google user."""
    return google_auth_service.get_current_user()


def is_authenticated() -> bool:
    """Check if user is authenticated via Google."""
    return st.session_state.get("google_authenticated", False)


# Demo/Test mode when Google is not configured
def render_demo_login():
    """Render demo login when Google OAuth is not configured."""
    st.info("🔧 **Demo Mode** - Google OAuth not configured")
    
    with st.expander("📋 Setup Google Authentication", expanded=False):
        st.markdown("""
        To enable Google Sign-In:
        
        1. **Create Google Cloud Project**
           - Go to [Google Cloud Console](https://console.cloud.google.com)
           - Create a new project
        
        2. **Enable OAuth**
           - Go to APIs & Services → OAuth consent screen
           - Configure consent screen
        
        3. **Create Credentials**
           - Go to APIs & Services → Credentials
           - Create OAuth 2.0 Client ID
           - Add redirect URI: `http://localhost:8501/`
        
        4. **Set Environment Variables**
           Create a `.env` file:
           ```
           GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
           GOOGLE_CLIENT_SECRET=your-secret
           ```
        
        5. **Restart the app**
        """)
    
    # Demo user selection
    st.markdown("##### Demo Login")
    demo_user = st.selectbox(
        "Select demo user",
        ["Admin User", "Dr. Sharma (Doctor)", "Nurse Priya", "Patient: Ramesh Kumar"],
        key="demo_user_select"
    )
    
    if st.button("🔓 Login as Demo User", use_container_width=True):
        # Create demo user session
        demo_users = {
            "Admin User": {"email": "admin@vitalflow.ai", "name": "Admin User", "role": "admin"},
            "Dr. Sharma (Doctor)": {"email": "dr.sharma@vitalflow.ai", "name": "Dr. Sharma", "role": "doctor"},
            "Nurse Priya": {"email": "priya@vitalflow.ai", "name": "Nurse Priya", "role": "nurse"},
            "Patient: Ramesh Kumar": {"email": "ramesh@email.com", "name": "Ramesh Kumar", "role": "patient"}
        }
        
        user_data = demo_users.get(demo_user, demo_users["Admin User"])
        st.session_state.google_user = user_data
        st.session_state.google_authenticated = True
        st.session_state.demo_mode = True
        
        # Auto-route based on role
        role = user_data.get("role", "admin")
        if role == "admin":
            st.session_state.portal = "admin"
        elif role in ["doctor", "nurse"]:
            st.session_state.portal = "staff"
            st.session_state.staff_role = "Doctor" if role == "doctor" else "Nurse"
        elif role == "patient":
            st.session_state.portal = "patient"
        
        st.session_state.logged_in = True
        st.rerun()
