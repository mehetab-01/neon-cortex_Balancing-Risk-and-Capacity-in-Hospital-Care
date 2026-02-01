"""
VitalFlow AI - Google OAuth Configuration
==========================================

Setup Instructions for Google Authentication:

1. Go to Google Cloud Console (https://console.cloud.google.com)

2. Create a new project or select existing:
   - Click "Select a project" dropdown
   - Click "New Project"
   - Name: "VitalFlow AI"
   - Click "Create"

3. Enable Google OAuth API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" or "Google Identity"
   - Click "Enable"

4. Configure OAuth Consent Screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" (or "Internal" for organization)
   - Fill required fields:
     * App name: VitalFlow AI
     * User support email: your-email@example.com
     * Developer contact: your-email@example.com
   - Click "Save and Continue"
   - Add scopes: email, profile, openid
   - Save and continue through remaining steps

5. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Web application"
   - Name: "VitalFlow AI Web Client"
   - Authorized JavaScript origins:
     * http://localhost:8501
     * http://localhost:8502
   - Authorized redirect URIs:
     * http://localhost:8501/
     * http://localhost:8501/callback
   - Click "Create"
   - Download JSON or copy Client ID and Client Secret

6. Update the credentials below with your values

7. Install required package:
   pip install streamlit-google-auth

"""

import os
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from project root
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed

@dataclass
class GoogleOAuthConfig:
    """Google OAuth Configuration"""
    
    # Replace these with your actual credentials
    client_id: str = os.getenv(
        "GOOGLE_CLIENT_ID", 
        "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
    )
    client_secret: str = os.getenv(
        "GOOGLE_CLIENT_SECRET", 
        "YOUR_GOOGLE_CLIENT_SECRET"
    )
    
    # OAuth settings
    redirect_uri: str = "http://localhost:8501/"
    scopes: list = None
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = [
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ]
    
    @property
    def is_configured(self) -> bool:
        """Check if OAuth is properly configured"""
        return (
            self.client_id != "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com" and
            self.client_secret != "YOUR_GOOGLE_CLIENT_SECRET"
        )


# Environment variable template for .env file
ENV_TEMPLATE = """
# Google OAuth Configuration
# Copy this to your .env file and fill in your credentials

GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
"""


def get_oauth_config() -> GoogleOAuthConfig:
    """Get the OAuth configuration instance"""
    return GoogleOAuthConfig()


def create_env_template():
    """Create a .env.template file with OAuth placeholders"""
    template_path = os.path.join(os.path.dirname(__file__), "..", ".env.template")
    with open(template_path, "w") as f:
        f.write(ENV_TEMPLATE.strip())
    return template_path


# Google Auth integration helper (for streamlit-google-auth package)
def init_google_auth(st_module):
    """
    Initialize Google Auth with Streamlit
    
    Usage:
        from config.google_auth import init_google_auth
        user_info = init_google_auth(st)
        if user_info:
            st.write(f"Welcome, {user_info['name']}!")
    """
    try:
        from streamlit_google_auth import Authenticate
        
        config = get_oauth_config()
        
        if not config.is_configured:
            st_module.warning("⚠️ Google OAuth not configured. Using mock authentication.")
            return None
        
        authenticator = Authenticate(
            secret_credentials_file=None,  # We use env vars instead
            cookie_name="vitalflow_auth",
            cookie_key="vitalflow_secret_key",
            redirect_uri=config.redirect_uri,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )
        
        return authenticator
        
    except ImportError:
        st_module.warning("📦 Install streamlit-google-auth: `pip install streamlit-google-auth`")
        return None
    except Exception as e:
        st_module.error(f"Auth error: {e}")
        return None


# Alternative: Simple OAuth flow without external package
class SimpleGoogleAuth:
    """
    Simple Google OAuth implementation using requests
    For production, consider using streamlit-google-auth or similar
    """
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    def __init__(self, config: Optional[GoogleOAuthConfig] = None):
        self.config = config or get_oauth_config()
    
    def get_auth_url(self, state: str = "random_state") -> str:
        """Generate Google OAuth authorization URL"""
        import urllib.parse
        
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "access_type": "offline",
            "state": state,
            "prompt": "consent"
        }
        
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    def exchange_code(self, code: str) -> Optional[dict]:
        """Exchange authorization code for tokens"""
        try:
            import requests
            
            response = requests.post(self.TOKEN_URL, data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.config.redirect_uri
            })
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception:
            return None
    
    def get_user_info(self, access_token: str) -> Optional[dict]:
        """Get user information from Google"""
        try:
            import requests
            
            response = requests.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception:
            return None


# Quick setup checker
def check_setup():
    """Check if Google OAuth is properly set up"""
    config = get_oauth_config()
    
    print("=" * 50)
    print("VitalFlow AI - Google OAuth Setup Check")
    print("=" * 50)
    
    if config.is_configured:
        print("✅ Google OAuth credentials are configured")
        print(f"   Client ID: {config.client_id[:20]}...")
    else:
        print("❌ Google OAuth NOT configured")
        print("   Please follow the setup instructions above")
        print("   Or set environment variables:")
        print("   - GOOGLE_CLIENT_ID")
        print("   - GOOGLE_CLIENT_SECRET")
    
    print("=" * 50)
    return config.is_configured


if __name__ == "__main__":
    check_setup()
