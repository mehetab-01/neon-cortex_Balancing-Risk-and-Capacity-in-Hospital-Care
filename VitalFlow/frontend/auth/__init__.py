"""
VitalFlow Authentication Package
"""
from .google_auth import (
    GoogleAuthService,
    google_auth_service,
    UserInfo,
    render_google_login_option,
    get_authenticated_user,
    is_authenticated,
    render_demo_login
)
