"""
VitalFlow AI - Backend API Contract
====================================

This file defines the API contract that the backend team should implement.
The frontend expects these endpoints to be available.

Base URL: http://localhost:8000/api (configurable via VITALFLOW_API_URL env var)
WebSocket: ws://localhost:8000/ws (configurable via VITALFLOW_WS_URL env var)

Authentication: Bearer token in Authorization header (optional for hackathon)
"""

# ============================================
# REST API ENDPOINTS
# ============================================

API_ENDPOINTS = {
    # ==========================================
    # HOSPITAL DATA (READ)
    # ==========================================
    
    "GET_HOSPITAL": {
        "method": "GET",
        "endpoint": "/api/hospital/{hospital_id}",
        "description": "Get complete hospital data",
        "params": {
            "hospital_id": "string - Hospital identifier (e.g., 'H001')"
        },
        "response": {
            "hospital": {
                "id": "string",
                "name": "string",
                "total_beds": "int",
                "occupied_beds": "int",
                "icu_available": "int",
                "emergency_available": "int",
                "general_available": "int",
                "lat": "float",
                "lon": "float",
                "address": "string"
            },
            "floors": ["Floor objects"],
            "beds": ["Bed objects"],
            "patients": ["Patient objects"],
            "staff": ["Staff objects"],
            "decisions": ["AIDecision objects"],
            "stats": "Stats object",
            "last_updated": "ISO datetime string"
        }
    },
    
    "GET_HOSPITALS": {
        "method": "GET",
        "endpoint": "/api/hospitals",
        "description": "Get all hospitals in network",
        "response": [
            {
                "id": "string",
                "name": "string",
                "lat": "float",
                "lon": "float",
                "address": "string",
                "total_beds": "int",
                "occupied_beds": "int",
                "available_beds": "int",
                "icu_total": "int",
                "icu_available": "int",
                "icu_percentage": "float",
                "occupancy_rate": "float"
            }
        ]
    },
    
    "GET_PATIENTS": {
        "method": "GET",
        "endpoint": "/api/hospital/{hospital_id}/patients",
        "description": "Get patients with optional filtering",
        "params": {
            "hospital_id": "string - Hospital identifier"
        },
        "query_params": {
            "floor": "int (optional) - Filter by floor number",
            "status": "string (optional) - Filter by status: Critical, Serious, Stable, Recovering"
        },
        "response": ["Patient objects"]
    },
    
    "GET_BEDS": {
        "method": "GET",
        "endpoint": "/api/hospital/{hospital_id}/beds",
        "description": "Get beds with optional filtering",
        "params": {
            "hospital_id": "string - Hospital identifier"
        },
        "query_params": {
            "floor": "int (optional) - Filter by floor number",
            "type": "string (optional) - Filter by type: ICU, Emergency, General",
            "available": "bool (optional) - Filter only available beds"
        },
        "response": ["Bed objects"]
    },
    
    "GET_STAFF": {
        "method": "GET",
        "endpoint": "/api/hospital/{hospital_id}/staff",
        "description": "Get staff with optional filtering",
        "params": {
            "hospital_id": "string - Hospital identifier"
        },
        "query_params": {
            "role": "string (optional) - Filter by role: Doctor, Nurse, Wardboy, Driver",
            "on_duty": "bool (optional) - Filter only on-duty staff"
        },
        "response": ["Staff objects"]
    },
    
    "GET_DECISIONS": {
        "method": "GET",
        "endpoint": "/api/hospital/{hospital_id}/decisions",
        "description": "Get AI decision history",
        "params": {
            "hospital_id": "string - Hospital identifier"
        },
        "query_params": {
            "limit": "int (default: 20) - Max decisions to return",
            "severity": "string (optional) - Filter: CRITICAL, WARNING, INFO",
            "action": "string (optional) - Filter: BED_SWAP, ALERT, STAFF_ASSIGN, etc."
        },
        "response": ["AIDecision objects - sorted by timestamp DESC"]
    },
    
    "GET_STATS": {
        "method": "GET",
        "endpoint": "/api/hospital/{hospital_id}/stats",
        "description": "Get current hospital statistics",
        "params": {
            "hospital_id": "string - Hospital identifier"
        },
        "response": {
            "total_beds": "int",
            "occupied_beds": "int",
            "available_beds": "int",
            "icu_total": "int",
            "icu_available": "int",
            "emergency_total": "int",
            "emergency_available": "int",
            "general_total": "int",
            "general_available": "int",
            "critical_patients": "int",
            "serious_patients": "int",
            "stable_patients": "int",
            "recovering_patients": "int",
            "staff_on_duty": "int",
            "total_staff": "int",
            "admissions_last_hour": "int",
            "discharges_last_hour": "int"
        }
    },
    
    # ==========================================
    # ACTIONS (WRITE)
    # ==========================================
    
    "TRANSFER_PATIENT": {
        "method": "POST",
        "endpoint": "/api/hospital/{hospital_id}/patient/transfer",
        "description": "Initiate patient transfer to another hospital",
        "params": {
            "hospital_id": "string - Source hospital identifier"
        },
        "body": {
            "patient_id": "string - Patient to transfer",
            "to_hospital": "string - Destination hospital ID",
            "transfer_type": "string - 'Ambulance', 'Critical Care Unit', 'Regular Transport'",
            "priority": "string - 'Emergency', 'Urgent', 'Standard'"
        },
        "response": {
            "success": "bool",
            "transfer_id": "string",
            "patient_id": "string",
            "from_hospital": "string",
            "to_hospital": "string",
            "status": "string - 'initiated', 'in_transit', 'completed'",
            "estimated_arrival": "string",
            "message": "string"
        }
    },
    
    "SWAP_BEDS": {
        "method": "POST",
        "endpoint": "/api/hospital/{hospital_id}/bed/swap",
        "description": "Swap patients between beds or move to empty bed",
        "params": {
            "hospital_id": "string - Hospital identifier"
        },
        "body": {
            "patient1_id": "string - First patient to move",
            "bed1_id": "string - Current bed of patient1",
            "patient2_id": "string (optional) - Second patient for swap",
            "bed2_id": "string - Target bed",
            "reason": "string - Reason for swap"
        },
        "response": {
            "success": "bool",
            "swap_id": "string",
            "message": "string"
        }
    },
    
    "ADMIT_PATIENT": {
        "method": "POST",
        "endpoint": "/api/hospital/{hospital_id}/patient/admit",
        "description": "Admit new patient to hospital",
        "params": {
            "hospital_id": "string - Hospital identifier"
        },
        "body": {
            "patient": {
                "name": "string",
                "age": "int",
                "diagnosis": "string",
                "status": "string - PatientStatus",
                "spo2": "int",
                "heart_rate": "int",
                "blood_pressure": "string",
                "temperature": "float"
            },
            "bed_id": "string - Bed to assign"
        },
        "response": {
            "success": "bool",
            "patient_id": "string - Generated patient ID",
            "bed_id": "string",
            "message": "string"
        }
    },
    
    "DISCHARGE_PATIENT": {
        "method": "POST",
        "endpoint": "/api/hospital/{hospital_id}/patient/{patient_id}/discharge",
        "description": "Discharge patient from hospital",
        "params": {
            "hospital_id": "string - Hospital identifier",
            "patient_id": "string - Patient identifier"
        },
        "body": {
            "discharge_notes": "string (optional)"
        },
        "response": {
            "success": "bool",
            "patient_id": "string",
            "status": "string",
            "discharged_at": "ISO datetime",
            "message": "string"
        }
    },
    
    "APPROVE_DECISION": {
        "method": "POST",
        "endpoint": "/api/decision/{decision_id}/approve",
        "description": "Approve an AI decision",
        "params": {
            "decision_id": "string - Decision identifier"
        },
        "body": {
            "approved_by": "string - Admin/user name"
        },
        "response": {
            "success": "bool",
            "decision_id": "string",
            "status": "string",
            "approved_by": "string",
            "approved_at": "ISO datetime"
        }
    },
    
    "OVERRIDE_DECISION": {
        "method": "POST",
        "endpoint": "/api/decision/{decision_id}/override",
        "description": "Override/reject an AI decision",
        "params": {
            "decision_id": "string - Decision identifier"
        },
        "body": {
            "override_reason": "string - Why decision was overridden",
            "overridden_by": "string - Admin/user name"
        },
        "response": {
            "success": "bool",
            "decision_id": "string",
            "status": "string",
            "override_reason": "string",
            "overridden_by": "string",
            "overridden_at": "ISO datetime"
        }
    },
    
    # ==========================================
    # HEALTH CHECK
    # ==========================================
    
    "HEALTH_CHECK": {
        "method": "GET",
        "endpoint": "/api/health",
        "description": "Check backend API health",
        "response": {
            "status": "string - 'healthy'",
            "timestamp": "ISO datetime",
            "version": "string"
        }
    },
}

# ============================================
# WEBSOCKET ENDPOINTS
# ============================================

WEBSOCKET_ENDPOINTS = {
    "HOSPITAL_UPDATES": {
        "endpoint": "/ws/hospital/{hospital_id}/updates",
        "description": "Real-time updates for a hospital",
        "message_types": {
            "PATIENT_UPDATE": {
                "description": "Patient vitals or status changed",
                "payload": {
                    "type": "PATIENT_UPDATE",
                    "patient_id": "string",
                    "changes": {"field": "new_value"},
                    "timestamp": "ISO datetime"
                }
            },
            "BED_UPDATE": {
                "description": "Bed occupancy changed",
                "payload": {
                    "type": "BED_UPDATE",
                    "bed_id": "string",
                    "is_occupied": "bool",
                    "patient_id": "string or null",
                    "timestamp": "ISO datetime"
                }
            },
            "DECISION_NEW": {
                "description": "New AI decision made",
                "payload": {
                    "type": "DECISION_NEW",
                    "decision": "AIDecision object",
                    "timestamp": "ISO datetime"
                }
            },
            "ALERT": {
                "description": "Critical alert triggered",
                "payload": {
                    "type": "ALERT",
                    "severity": "string - CRITICAL, WARNING",
                    "message": "string",
                    "patient_id": "string (optional)",
                    "timestamp": "ISO datetime"
                }
            },
            "STAFF_UPDATE": {
                "description": "Staff status changed",
                "payload": {
                    "type": "STAFF_UPDATE",
                    "staff_id": "string",
                    "changes": {"field": "new_value"},
                    "timestamp": "ISO datetime"
                }
            },
            "STATS_UPDATE": {
                "description": "Hospital stats refreshed",
                "payload": {
                    "type": "STATS_UPDATE",
                    "stats": "Stats object",
                    "timestamp": "ISO datetime"
                }
            }
        }
    }
}

# ============================================
# DATA MODELS
# ============================================

DATA_MODELS = {
    "Patient": {
        "id": "string - Unique identifier (e.g., 'P1234')",
        "name": "string - Full name",
        "age": "int - Age in years",
        "diagnosis": "string - Primary diagnosis",
        "status": "string - 'Critical', 'Serious', 'Stable', 'Recovering'",
        "spo2": "int - Oxygen saturation (0-100)",
        "heart_rate": "int - Heart rate in bpm",
        "blood_pressure": "string - Format: '120/80'",
        "temperature": "float - Body temperature in Celsius",
        "bed_id": "string or null - Assigned bed ID",
        "admitted_at": "ISO datetime - Admission timestamp",
        "assigned_doctor": "string or null - Doctor name",
        "notes": "string or null - Additional notes"
    },
    
    "Bed": {
        "id": "string - Unique identifier (e.g., 'ICU-201')",
        "floor": "int - Floor number (1-5)",
        "bed_type": "string - 'ICU', 'Emergency', 'General'",
        "is_occupied": "bool - Whether bed has a patient",
        "patient_id": "string or null - Current patient ID",
        "room_number": "string - Room identifier"
    },
    
    "Staff": {
        "id": "string - Unique identifier (e.g., 'S001')",
        "name": "string - Full name",
        "role": "string - 'Doctor', 'Nurse', 'Wardboy', 'Driver'",
        "is_on_duty": "bool - Currently working",
        "shift_start": "ISO datetime or null - Shift start time",
        "fatigue_level": "int - 0-100 fatigue score",
        "assigned_patients": "list[string] - Patient IDs assigned"
    },
    
    "AIDecision": {
        "id": "string - Unique identifier (e.g., 'DEC0001')",
        "timestamp": "ISO datetime - When decision was made",
        "action": "string - 'BED_SWAP', 'ALERT', 'STAFF_ASSIGN', 'DISCHARGE_RECOMMEND', 'ICU_TRANSFER'",
        "reason": "string - Human-readable explanation",
        "patient_id": "string or null - Related patient",
        "from_bed": "string or null - Source bed (for transfers)",
        "to_bed": "string or null - Target bed (for transfers)",
        "severity": "string - 'CRITICAL', 'WARNING', 'INFO'"
    },
    
    "Floor": {
        "floor_number": "int - Floor number",
        "name": "string - Floor name (e.g., 'ICU Complex')",
        "bed_type": "string - Primary bed type",
        "total_beds": "int - Total beds on floor",
        "beds": "list[Bed] - All beds on this floor"
    },
    
    "Hospital": {
        "id": "string - Unique identifier",
        "name": "string - Hospital name",
        "total_beds": "int",
        "occupied_beds": "int",
        "icu_available": "int",
        "emergency_available": "int",
        "general_available": "int",
        "lat": "float - Latitude",
        "lon": "float - Longitude",
        "address": "string - Physical address"
    }
}

# ============================================
# EXAMPLE BACKEND IMPLEMENTATION (FastAPI)
# ============================================

FASTAPI_EXAMPLE = '''
# backend/main.py - Example FastAPI implementation

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(title="VitalFlow API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import your data layer
from core_logic.state import StateManager
from core_logic.bed_manager import BedManager

state = StateManager()
bed_manager = BedManager(state)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/hospital/{hospital_id}")
async def get_hospital(hospital_id: str):
    data = state.get_hospital_data(hospital_id)
    if not data:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return data


@app.get("/api/hospitals")
async def get_hospitals():
    return state.get_all_hospitals()


@app.get("/api/hospital/{hospital_id}/patients")
async def get_patients(hospital_id: str, floor: int = None, status: str = None):
    return state.get_patients(hospital_id, floor=floor, status=status)


@app.post("/api/hospital/{hospital_id}/bed/swap")
async def swap_beds(hospital_id: str, request: BedSwapRequest):
    result = bed_manager.swap_patient(
        request.patient1_id, 
        request.bed1_id,
        request.bed2_id,
        request.reason
    )
    return result


# WebSocket for real-time updates
@app.websocket("/ws/hospital/{hospital_id}/updates")
async def websocket_endpoint(websocket: WebSocket, hospital_id: str):
    await websocket.accept()
    
    # Subscribe to state changes
    async def send_update(update):
        await websocket.send_json(update)
    
    state.subscribe(hospital_id, send_update)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except:
        state.unsubscribe(hospital_id, send_update)
'''

if __name__ == "__main__":
    import json
    print("VitalFlow API Contract")
    print("=" * 50)
    print("\nEndpoints:")
    for name, spec in API_ENDPOINTS.items():
        print(f"\n{spec['method']} {spec['endpoint']}")
        print(f"  {spec['description']}")
