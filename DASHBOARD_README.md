# VitalFlow AI 🏥
## Hospital Command Center - Admin Dashboard

A modern, warm-themed hospital management dashboard built with Streamlit.

### 🎨 Design Theme
- **Color Palette:** Warm Ochre (#c4a35a) + Cream (#faf8f5)
- **Font:** DM Sans
- **Style:** Clean, minimal, no gradients

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application

**Option A: Run Home Page (Auth)**
```bash
cd frontend
streamlit run home/app.py
```

**Option B: Run Admin Dashboard Directly**
```bash
cd frontend
streamlit run admin_dashboard/app.py
```

---

## 📁 Project Structure

```
frontend/
├── home/
│   └── app.py          # Landing page with Sign In / Sign Up
├── admin_dashboard/
│   └── app.py          # Hospital command center dashboard
├── config/
│   └── google_auth.py  # Google OAuth configuration
└── main.py             # Main entry point

shared/
├── models.py           # Pydantic data models
├── constants.py        # App constants
├── mock_data.py        # Mock data generators
├── data_service.py     # Backend API integration
└── api_contract.py     # API documentation for backend team
```

---

## 🔐 Authentication

### Demo Accounts
| Email | Password | Role |
|-------|----------|------|
| admin@vitalflow.ai | admin123 | Admin |
| doctor@vitalflow.ai | doctor123 | Doctor |
| nurse@vitalflow.ai | nurse123 | Nurse |

### Google OAuth Setup
See [frontend/config/google_auth.py](frontend/config/google_auth.py) for detailed setup instructions.

---

## 🎯 Features

### Dashboard Tabs
1. **Overview** - Key metrics, alerts, quick actions
2. **Bed Management** - Real-time bed status grid
3. **Patient Queue** - Critical patients requiring attention
4. **AI Decisions** - AI recommendations with approve/override

### Key Capabilities
- ✅ Real-time bed occupancy tracking
- ✅ AI-powered patient prioritization
- ✅ Network-wide hospital coordination
- ✅ Staff allocation optimization
- ✅ Critical alert system

---

## 🔧 Backend Integration

The frontend includes a `data_service.py` that defines all API endpoints needed.
Backend team can refer to `api_contract.py` for the complete API specification.

### API Endpoints Required
```
GET  /api/hospital/{id}           # Hospital details
GET  /api/hospital/{id}/beds      # Bed status
GET  /api/hospital/{id}/patients  # Patient list
POST /api/hospital/{id}/transfer  # Patient transfer
GET  /api/ai/decisions            # AI decisions
POST /api/ai/decisions/{id}/approve
POST /api/ai/decisions/{id}/override
```

---

## 👥 Team - Neon Cortex

- Sayali - Admin Dashboard (this module)
- [Other team members]

---

© 2026 VitalFlow AI · Neon Cortex Hackathon
