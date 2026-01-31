# VitalFlow AI - Intelligent Hospital Management System

![VitalFlow Banner](https://img.shields.io/badge/VitalFlow-AI%20Hospital%20Command-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-green?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?style=flat-square)

## 🏥 Overview

VitalFlow AI is an intelligent hospital command center that provides real-time monitoring, bed management, and AI-driven decision support for hospital administrators and staff.

## 📁 Project Structure

```
VitalFlow/
├── frontend/
│   ├── admin_dashboard/        # Admin/Dean Dashboard (Sayali)
│   │   ├── app.py              # Main Streamlit entry
│   │   ├── components/
│   │   │   ├── floor_map.py    # Visual floor layout
│   │   │   ├── city_map.py     # Multi-hospital view
│   │   │   ├── patient_cards.py # Patient status cards
│   │   │   ├── stats_panel.py  # Real-time statistics
│   │   │   └── decision_log.py # AI decision explanations
│   │   └── assets/
│   │
│   └── staff_mobile/           # Staff Mobile View (Aditya)
│
├── backend/
│   ├── core_logic/             # Core Business Logic (Rajat)
│   └── ai_services/            # AI Services (Dhanshree)
│
├── shared/
│   ├── models.py               # Pydantic data models
│   ├── constants.py            # Configuration constants
│   ├── mock_data.py            # Demo data generation
│   └── __init__.py
│
├── simulation/                 # Demo Simulation (Mehetab)
│
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Admin Dashboard

```bash
cd frontend/admin_dashboard
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 🔌 Backend Integration

The frontend is designed with clean endpoints for easy backend integration.

### Data Service Layer

All data fetching goes through `shared/data_service.py`:

```python
from shared.data_service import (
    get_hospital_data,      # GET /api/hospital/{id}
    get_network_hospitals,  # GET /api/hospitals
    get_patients,           # GET /api/hospital/{id}/patients
    get_beds,               # GET /api/hospital/{id}/beds
    get_staff,              # GET /api/hospital/{id}/staff
    get_ai_decisions,       # GET /api/hospital/{id}/decisions
    transfer_patient,       # POST /api/hospital/{id}/patient/transfer
    swap_beds,              # POST /api/hospital/{id}/bed/swap
    approve_decision,       # POST /api/decision/{id}/approve
    set_data_source,        # Switch between mock/api/json
    DataSource,
)

# Switch to real API
set_data_source(DataSource.API)
```

### API Contract

See `shared/api_contract.py` for the complete API specification including:
- All REST endpoints with request/response schemas
- WebSocket message types for real-time updates
- Data model definitions
- Example FastAPI implementation

### Configuration

Set environment variables or create `.env` file:

```bash
VITALFLOW_API_URL=http://localhost:8000/api
VITALFLOW_WS_URL=ws://localhost:8000/ws
VITALFLOW_API_KEY=your_api_key
```

### Data Source Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `mock` | Generated fake data | Development, demos |
| `api` | Real backend API | Production |
| `json` | Shared JSON file | Backend testing |

## ✨ Features

### Admin Dashboard

- **📊 Real-time Statistics** - Live bed occupancy, patient status, staff availability
- **🏥 Floor Map View** - Visual grid of beds with color-coded patient status
- **👥 Patient Management** - Search, filter, and view patient details
- **🗺️ Network Map** - Multi-hospital view with transfer capabilities
- **🤖 AI Decision Log** - Transparent AI recommendations with explanations

### Visual Indicators

| Status | Color | Meaning |
|--------|-------|---------|
| 🔴 | Red | Critical - Immediate attention required |
| 🟠 | Orange | Serious - Close monitoring needed |
| 🟢 | Green | Stable - Normal condition |
| 🔵 | Blue | Recovering - Improving |
| ⬜ | White | Empty bed |

## 🛠️ Development

### Component Architecture

Each component is designed to be modular and reusable:

```python
# Import components
from components.stats_panel import render_stats_panel
from components.floor_map import render_floor_map
from components.patient_cards import render_patient_list
from components.city_map import render_city_map
from components.decision_log import render_decision_log

# Use in your Streamlit app
render_stats_panel(stats_data)
render_floor_map(floors, patients)
```

### Data Models

```python
from shared.models import Patient, Bed, Hospital, PatientStatus

patient = Patient(
    id="P1234",
    name="John Doe",
    age=45,
    status=PatientStatus.STABLE,
    spo2=98,
    heart_rate=72,
    ...
)
```

## 🎯 Hackathon Notes

This project was built for a 10-hour hackathon. Key design decisions:

1. **Mock Data First** - Realistic data generation for impressive demos
2. **Modular Components** - Easy to extend and customize
3. **Visual Impact** - Dark theme with color-coded status indicators
4. **Fallback Support** - Works even without optional dependencies (folium)

## 👥 Team

- **Sayali** - Admin Dashboard Frontend
- **Aditya** - Staff Mobile View
- **Rajat** - Core Backend Logic
- **Dhanshree** - AI Services
- **Mehetab** - Simulation & Demo

## 📝 License

MIT License - Built with ❤️ for healthcare innovation
