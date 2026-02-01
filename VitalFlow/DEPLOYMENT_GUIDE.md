# VitalFlow AI - Deployment Guide

This guide explains how to deploy VitalFlow AI with Google Authentication.

## 🔐 Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Select a project** → **New Project**
3. Name it: `VitalFlow AI`
4. Click **Create**

### Step 2: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type → Click **Create**
3. Fill in the required fields:
   - **App name**: `VitalFlow AI`
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **Save and Continue**
5. **Scopes**: Click **Add or Remove Scopes**
   - Select: `email`, `profile`, `openid`
   - Click **Update** → **Save and Continue**
6. **Test users**: Add your email and any test users
7. Click **Save and Continue** → **Back to Dashboard**

### Step 3: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Web application**
4. Name it: `VitalFlow Web`
5. **Authorized JavaScript origins**:
   - `http://localhost:8502` (local development)
   - `https://your-app.streamlit.app` (Streamlit Cloud)
6. **Authorized redirect URIs**:
   - `http://localhost:8502/` (local - note the trailing slash!)
   - `https://your-app.streamlit.app/` (Streamlit Cloud)
7. Click **Create**
8. **Copy** the Client ID and Client Secret

---

## 🖥️ Local Development

### Option 1: Using .env file

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```env
   GOOGLE_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxx
   GOOGLE_REDIRECT_URI=http://localhost:8502/
   ```

3. Run the app:
   ```bash
   streamlit run frontend/main.py --server.port 8502
   ```

4. Open http://localhost:8502 and click **Sign in with Google**

---

## ☁️ Streamlit Cloud Deployment

### Step 1: Push to GitHub

1. Create a GitHub repository
2. Push your code (make sure `.env` is in `.gitignore`!)

### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Select your repository
4. Set main file path: `VitalFlow/frontend/main.py`
5. Click **Deploy**

### Step 3: Configure Secrets

1. In your deployed app, click **Settings** (⚙️ icon)
2. Go to **Secrets** section
3. Add your secrets in TOML format:

```toml
GOOGLE_CLIENT_ID = "123456789-abcdef.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "GOCSPX-xxxxxxxxxxxx"
GOOGLE_REDIRECT_URI = "https://your-app.streamlit.app/"
```

4. Click **Save**
5. **Important**: Update your Google Cloud Console:
   - Go to **APIs & Services** → **Credentials**
   - Edit your OAuth client
   - Add your Streamlit Cloud URL to **Authorized redirect URIs**

### Step 4: Verify Deployment

1. Open your Streamlit Cloud URL
2. Click **Sign in with Google**
3. You should be redirected to Google, then back to your app

---

## 🐳 Docker Deployment

### Using Docker Compose

1. Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  vitalflow:
    build: .
    ports:
      - "8502:8502"
    environment:
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI}
    volumes:
      - ./VitalFlow/shared:/app/shared
```

2. Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY VitalFlow/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY VitalFlow/ .

EXPOSE 8502

CMD ["streamlit", "run", "frontend/main.py", "--server.port=8502", "--server.address=0.0.0.0"]
```

3. Run:
```bash
docker-compose up -d
```

---

## 🔧 Troubleshooting

### "Google Sign-In not configured"
- Check that your `.env` file exists and has correct credentials
- Verify environment variables are loaded (restart the app)

### "redirect_uri_mismatch" Error
- Ensure the redirect URI in your code **exactly matches** the one in Google Cloud Console
- Include the trailing slash: `http://localhost:8502/`
- For Streamlit Cloud, use `https://` not `http://`

### "Access Denied" or "App not verified"
- Add yourself as a test user in OAuth consent screen
- Or publish the app (requires verification for production)

### Session Lost After Login
- Check that cookies are enabled in your browser
- Try incognito mode to rule out cookie issues

---

## 📋 Production Checklist

- [ ] Google OAuth credentials created
- [ ] Redirect URIs configured for production URL
- [ ] OAuth consent screen published (or test users added)
- [ ] Secrets configured in Streamlit Cloud
- [ ] HTTPS enabled (automatic on Streamlit Cloud)
- [ ] Test login flow end-to-end

---

## 🆘 Support

If you encounter issues:
1. Check the browser console for errors
2. Check Streamlit logs for backend errors
3. Verify all redirect URIs match exactly
4. Ensure you're using the correct port (8502)
