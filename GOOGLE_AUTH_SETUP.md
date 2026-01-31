# VitalFlow AI - Google OAuth Setup Guide

## Quick Setup (5 minutes)

### 1. Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Click "Select a project" → "NEW PROJECT"
3. Project name: `VitalFlow AI`
4. Click "CREATE"

### 2. Enable Google OAuth API
1. Go to **APIs & Services** → **Library**
2. Search for "Google+ API"
3. Click **ENABLE**

### 3. Configure OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External**
3. Fill in:
   - App name: `VitalFlow AI`
   - User support email: Your email
   - Developer contact: Your email
4. Click **SAVE AND CONTINUE**
5. Scopes: Click **ADD OR REMOVE SCOPES**
   - Select: `userinfo.email`, `userinfo.profile`, `openid`
6. Click **SAVE AND CONTINUE** through remaining steps

### 4. Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `VitalFlow AI Web`
5. **Authorized JavaScript origins:**
   ```
   http://localhost:8507
   ```
6. **Authorized redirect URIs:**
   ```
   http://localhost:8507
   http://localhost:8507/callback
   ```
7. Click **CREATE**
8. **Copy the Client ID and Client Secret**

### 5. Configure Your App

Create a `.env` file in the `frontend` directory:

```env
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

Or directly edit `frontend/config/google_auth.py`:

```python
client_id: str = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret: str = "YOUR_CLIENT_SECRET"
```

### 6. Install Required Package

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 requests
```

### 7. Restart the App

```bash
cd frontend
streamlit run home/app.py --server.port 8507
```

---

## Current Status

✅ **Google Auth Integration Ready**
- If credentials are configured: Real Google OAuth works
- If not configured: Falls back to email/password login
- No errors either way!

## Test It

1. **Without setup**: Use demo login `admin@vitalflow.ai` / `admin123`
2. **With setup**: Click "Continue with Google" button

---

## Troubleshooting

**Button shows "Setup Required"?**
→ You need to add your Google OAuth credentials

**"Redirect URI mismatch" error?**
→ Make sure you added `http://localhost:8507` to authorized URIs

**Still not working?**
→ Check that you enabled Google+ API in Step 2

---

For hackathons/demos, you can skip Google Auth entirely and just use the mock login! 🎯
