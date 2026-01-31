# VitalFlow AI - Staff Mobile Interface

## 📱 Overview
Mobile-optimized Streamlit interface for hospital staff (Doctor, Nurse, Ward Boy, Driver). Designed for touch-friendly interaction and ready to be wrapped with Appilix for mobile app deployment.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation
```bash
cd VitalFlow
pip install -r requirements.txt
```

### Run the App
```bash
cd frontend/staff_mobile
streamlit run app.py --server.port 8501
```

Access at: `http://localhost:8501`

## 📁 Project Structure
```
VitalFlow/
├── frontend/
│   └── staff_mobile/
│       ├── app.py                 # Main entry - Role selector
│       ├── pages/
│       │   ├── doctor_view.py     # Doctor dashboard
│       │   ├── nurse_view.py      # Nurse task management
│       │   ├── wardboy_view.py    # Transfer tickets
│       │   └── driver_view.py     # Ambulance trip management
│       ├── components/
│       │   ├── vitals_chart.py    # Vitals visualization
│       │   ├── task_card.py       # Task/transfer cards
│       │   └── action_button.py   # Mobile-optimized buttons
│       └── services/
│           └── api_service.py     # Backend API integration
│
└── shared/
    ├── constants.py               # Enums and config
    ├── models.py                  # Pydantic data models
    └── mock_data.py               # Test data generation
```

## 👨‍⚕️ Features by Role

### Doctor View
- ✅ Punch In/Out with shift tracking
- ⚠️ Fatigue warnings (10h caution, 12h max)
- 🚨 Critical patient alerts with vitals
- 📋 Transfer approval workflow
- 📊 Mini vitals charts (SpO2, Heart Rate)

### Nurse View
- ✅ AI-generated task checklist
- 🔊 Voice alert notifications
- 🛏️ Bed assignment overview
- 🚨 Code Blue emergency banner
- 📊 Task progress tracking

### Ward Boy View
- 🛏️ Transfer ticket queue
- ✅ Mark complete workflow
- 🔄 Priority-sorted transfers
- 📊 Completion statistics

### Driver View
- 🚑 Emergency trip initiation
- 🏥 Hospital bed confirmation display
- ⏱️ ETA tracking
- 🔄 Trip state management (IDLE → EN_ROUTE → LOADED → ARRIVING)

## 🔌 Backend Integration

### API Service
All backend communication goes through `services/api_service.py`:

```python
from services.api_service import api_service

# Staff actions
api_service.punch_in(staff_id)
api_service.punch_out(staff_id, hours_worked)

# Transfer management
api_service.approve_transfer(transfer_id, doctor_id)
api_service.decline_transfer(transfer_id, doctor_id, reason)
api_service.complete_transfer(transfer_id, staff_id)

# Task management
api_service.complete_task(task_id, staff_id)

# Ambulance trips
api_service.start_trip(driver_id, pickup_location, patient_name)
api_service.update_trip_state(trip_id, driver_id, new_state)
api_service.end_trip(trip_id, driver_id)
```

### Open Endpoints
Configure backend URL via environment variable:
```bash
export VITALFLOW_API_URL="http://your-backend:8000/api/v1"
export VITALFLOW_USE_MOCK="false"  # Set to false for production
```

### API Endpoints (for backend team)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/staff/{id}/punch-in` | Staff punch in |
| POST | `/api/v1/staff/{id}/punch-out` | Staff punch out |
| GET | `/api/v1/staff/{id}/status` | Get staff status |
| GET | `/api/v1/transfers/pending` | Get pending transfers |
| POST | `/api/v1/transfers/{id}/approve` | Approve transfer |
| POST | `/api/v1/transfers/{id}/decline` | Decline transfer |
| POST | `/api/v1/transfers/{id}/complete` | Mark transfer complete |
| GET | `/api/v1/tasks` | Get tasks |
| POST | `/api/v1/tasks/{id}/complete` | Complete task |
| POST | `/api/v1/ambulance/trips` | Start trip |
| PATCH | `/api/v1/ambulance/trips/{id}/state` | Update trip state |
| POST | `/api/v1/ambulance/trips/{id}/complete` | End trip |
| GET | `/api/v1/patients/critical` | Get critical patients |
| GET | `/api/v1/patients/{id}/vitals` | Get patient vitals |
| GET | `/api/v1/alerts` | Get alerts |

### Action Logging
All actions are logged to `shared/actions.json` for backend sync:
```json
{
  "actions": [
    {
      "id": "ACT12345678",
      "type": "PUNCH_IN",
      "staff_id": "D001",
      "timestamp": "2026-01-31T10:00:00",
      "data": {},
      "is_synced": false
    }
  ]
}
```

## 🎨 Mobile Styling
- Max width: 480px (mobile optimized)
- Large touch targets (60-80px buttons)
- Dark theme with gradients
- Role-specific color schemes:
  - Doctor: Purple (#6C63FF)
  - Nurse: Green (#00C851)
  - Ward Boy: Orange (#FFBB33)
  - Driver: Blue (#33B5E5)

## 🧪 Testing
Each view can be run standalone for testing:
```bash
streamlit run pages/doctor_view.py
streamlit run pages/nurse_view.py
streamlit run pages/wardboy_view.py
streamlit run pages/driver_view.py
```

## 📱 Mobile App Wrapping (Appilix)
1. Deploy Streamlit app to cloud (Streamlit Cloud, Railway, etc.)
2. Use Appilix to wrap the URL as a mobile app
3. Configure in Appilix:
   - Full screen mode
   - Hide browser controls
   - Enable notifications (optional)

## 🔧 Environment Variables
```bash
VITALFLOW_API_URL=http://localhost:8000/api/v1
VITALFLOW_USE_MOCK=true
```

## 👥 Team Integration
- **Sayali** (Admin Dashboard): Shares models from `shared/models.py`
- **Rajat** (Backend Core): API endpoints documented above
- **Dhanshree** (AI Services): Voice alerts via `api_service.get_voice_alert_url()`
- **Mehetab** (Simulation): Reads actions from `shared/actions.json`

## 📄 License
MIT License - VitalFlow AI Hackathon Project
