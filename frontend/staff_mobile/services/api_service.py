"""
VitalFlow AI - API Service Layer
Handles all backend communication with open endpoints
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

# File paths for state management
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARED_DIR = os.path.join(BASE_DIR, "shared")
STATE_FILE = os.path.join(SHARED_DIR, "state.json")
ACTIONS_FILE = os.path.join(SHARED_DIR, "actions.json")


class APIService:
    """
    API Service for backend integration
    All endpoints are open for integration with the backend team
    """
    
    # ==================== CONFIGURATION ====================
    # Backend API Base URL - Configure this for production
    API_BASE_URL = os.getenv("VITALFLOW_API_URL", "http://localhost:8000/api/v1")
    
    # Enable/disable mock mode (uses local files instead of API)
    USE_MOCK = os.getenv("VITALFLOW_USE_MOCK", "true").lower() == "true"
    
    def __init__(self):
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Ensure state and actions files exist"""
        os.makedirs(SHARED_DIR, exist_ok=True)
        
        if not os.path.exists(STATE_FILE):
            self._write_json(STATE_FILE, {"patients": [], "staff": [], "transfers": [], "trips": []})
        
        if not os.path.exists(ACTIONS_FILE):
            self._write_json(ACTIONS_FILE, {"actions": []})
    
    def _read_json(self, filepath: str) -> dict:
        """Read JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_json(self, filepath: str, data: dict):
        """Write JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID"""
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"
    
    # ==================== ACTION LOGGING ====================
    # All actions are logged for backend sync
    
    def log_action(self, action_type: str, staff_id: str, data: dict = None) -> dict:
        """
        Log an action for backend synchronization
        
        ENDPOINT: POST /api/v1/actions
        
        Args:
            action_type: Type of action (PUNCH_IN, PUNCH_OUT, APPROVE_TRANSFER, etc.)
            staff_id: ID of staff performing action
            data: Additional action data
            
        Returns:
            Action record with ID and timestamp
        """
        action = {
            "id": self._generate_id("ACT"),
            "type": action_type,
            "staff_id": staff_id,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
            "is_synced": False
        }
        
        # Write to local actions file
        actions_data = self._read_json(ACTIONS_FILE)
        if "actions" not in actions_data:
            actions_data["actions"] = []
        actions_data["actions"].append(action)
        self._write_json(ACTIONS_FILE, actions_data)
        
        return action
    
    # ==================== STAFF ENDPOINTS ====================
    
    def punch_in(self, staff_id: str) -> dict:
        """
        Staff punch in
        
        ENDPOINT: POST /api/v1/staff/{staff_id}/punch-in
        
        Returns:
            Updated staff record with shift_start time
        """
        action = self.log_action("PUNCH_IN", staff_id)
        return {
            "success": True,
            "staff_id": staff_id,
            "shift_start": datetime.now().isoformat(),
            "action_id": action["id"]
        }
    
    def punch_out(self, staff_id: str, hours_worked: float) -> dict:
        """
        Staff punch out
        
        ENDPOINT: POST /api/v1/staff/{staff_id}/punch-out
        
        Args:
            staff_id: Staff member ID
            hours_worked: Total hours worked this shift
            
        Returns:
            Confirmation with total hours
        """
        action = self.log_action("PUNCH_OUT", staff_id, {"hours_worked": hours_worked})
        return {
            "success": True,
            "staff_id": staff_id,
            "hours_worked": hours_worked,
            "action_id": action["id"]
        }
    
    def get_staff_status(self, staff_id: str) -> dict:
        """
        Get current staff status
        
        ENDPOINT: GET /api/v1/staff/{staff_id}/status
        
        Returns:
            Staff status including hours worked, availability, etc.
        """
        # In production, this would call the backend API
        return {
            "staff_id": staff_id,
            "is_on_duty": True,
            "hours_worked": 6.5,
            "is_available": True,
            "assigned_patients": []
        }
    
    def check_fatigue(self, staff_id: str, hours_worked: float) -> dict:
        """
        Check staff fatigue level
        
        ENDPOINT: GET /api/v1/staff/{staff_id}/fatigue-check
        
        Returns:
            Fatigue status and warnings
        """
        return {
            "staff_id": staff_id,
            "hours_worked": hours_worked,
            "is_fatigued": hours_worked >= 10,
            "is_max_hours": hours_worked >= 12,
            "warning_message": "⚠️ Fatigue Alert - No new critical cases will be assigned" if hours_worked >= 12 else None
        }
    
    # ==================== TRANSFER ENDPOINTS ====================
    
    def get_pending_transfers(self, doctor_id: str = None) -> List[dict]:
        """
        Get pending transfer requests
        
        ENDPOINT: GET /api/v1/transfers/pending?doctor_id={doctor_id}
        
        Args:
            doctor_id: Optional - filter by assigned doctor
            
        Returns:
            List of pending transfer requests
        """
        state = self._read_json(STATE_FILE)
        transfers = state.get("transfers", [])
        
        if doctor_id:
            transfers = [t for t in transfers if not t.get("is_approved") and not t.get("is_completed")]
        
        return transfers
    
    def approve_transfer(self, transfer_id: str, doctor_id: str) -> dict:
        """
        Approve a patient transfer
        
        ENDPOINT: POST /api/v1/transfers/{transfer_id}/approve
        
        Args:
            transfer_id: Transfer request ID
            doctor_id: Approving doctor ID
            
        Returns:
            Updated transfer record
        """
        action = self.log_action("APPROVE_TRANSFER", doctor_id, {"transfer_id": transfer_id})
        return {
            "success": True,
            "transfer_id": transfer_id,
            "approved_by": doctor_id,
            "approved_at": datetime.now().isoformat(),
            "action_id": action["id"]
        }
    
    def decline_transfer(self, transfer_id: str, doctor_id: str, reason: str = "") -> dict:
        """
        Decline a patient transfer
        
        ENDPOINT: POST /api/v1/transfers/{transfer_id}/decline
        
        Args:
            transfer_id: Transfer request ID
            doctor_id: Declining doctor ID
            reason: Reason for declining
            
        Returns:
            Updated transfer record
        """
        action = self.log_action("DECLINE_TRANSFER", doctor_id, {
            "transfer_id": transfer_id,
            "reason": reason
        })
        return {
            "success": True,
            "transfer_id": transfer_id,
            "declined_by": doctor_id,
            "reason": reason,
            "action_id": action["id"]
        }
    
    def complete_transfer(self, transfer_id: str, staff_id: str) -> dict:
        """
        Mark transfer as completed
        
        ENDPOINT: POST /api/v1/transfers/{transfer_id}/complete
        
        Args:
            transfer_id: Transfer request ID
            staff_id: Staff who completed the transfer
            
        Returns:
            Confirmation
        """
        action = self.log_action("COMPLETE_TRANSFER", staff_id, {"transfer_id": transfer_id})
        return {
            "success": True,
            "transfer_id": transfer_id,
            "completed_by": staff_id,
            "completed_at": datetime.now().isoformat(),
            "action_id": action["id"]
        }
    
    def get_transfer_queue(self, staff_id: str = None) -> List[dict]:
        """
        Get transfer queue for ward boys
        
        ENDPOINT: GET /api/v1/transfers/queue?assigned_to={staff_id}
        
        Returns:
            List of approved, pending transfers
        """
        state = self._read_json(STATE_FILE)
        return state.get("transfer_queue", [])
    
    # ==================== TASK ENDPOINTS ====================
    
    def get_tasks(self, staff_id: str, include_completed: bool = False) -> List[dict]:
        """
        Get tasks assigned to staff
        
        ENDPOINT: GET /api/v1/tasks?assigned_to={staff_id}&include_completed={include_completed}
        
        Args:
            staff_id: Staff member ID
            include_completed: Whether to include completed tasks
            
        Returns:
            List of tasks
        """
        state = self._read_json(STATE_FILE)
        tasks = state.get("tasks", [])
        
        tasks = [t for t in tasks if t.get("assigned_to") == staff_id]
        if not include_completed:
            tasks = [t for t in tasks if not t.get("is_completed")]
        
        return tasks
    
    def complete_task(self, task_id: str, staff_id: str) -> dict:
        """
        Mark task as completed
        
        ENDPOINT: POST /api/v1/tasks/{task_id}/complete
        
        Args:
            task_id: Task ID
            staff_id: Staff completing the task
            
        Returns:
            Confirmation
        """
        action = self.log_action("COMPLETE_TASK", staff_id, {"task_id": task_id})
        return {
            "success": True,
            "task_id": task_id,
            "completed_by": staff_id,
            "completed_at": datetime.now().isoformat(),
            "action_id": action["id"]
        }
    
    # ==================== PATIENT ENDPOINTS ====================
    
    def get_critical_patients(self, doctor_id: str = None) -> List[dict]:
        """
        Get critical patients needing attention
        
        ENDPOINT: GET /api/v1/patients/critical?doctor_id={doctor_id}
        
        Args:
            doctor_id: Optional - filter by assigned doctor
            
        Returns:
            List of critical patients
        """
        state = self._read_json(STATE_FILE)
        patients = state.get("patients", [])
        return [p for p in patients if p.get("is_critical")]
    
    def get_patient_vitals(self, patient_id: str) -> dict:
        """
        Get current patient vitals
        
        ENDPOINT: GET /api/v1/patients/{patient_id}/vitals
        
        Returns:
            Current vitals reading
        """
        return {
            "patient_id": patient_id,
            "spo2": 94.5,
            "heart_rate": 85,
            "blood_pressure": "120/80",
            "temperature": 37.2,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_vitals_history(self, patient_id: str, minutes: int = 30) -> List[dict]:
        """
        Get patient vitals history for charts
        
        ENDPOINT: GET /api/v1/patients/{patient_id}/vitals/history?minutes={minutes}
        
        Args:
            patient_id: Patient ID
            minutes: How many minutes of history to fetch
            
        Returns:
            List of vitals readings
        """
        # Return mock history - in production, fetch from backend
        from shared.mock_data import generate_vitals_history
        return generate_vitals_history(patient_id, minutes)
    
    # ==================== AMBULANCE/DRIVER ENDPOINTS ====================
    
    def start_trip(self, driver_id: str, pickup_location: str, patient_name: str = None) -> dict:
        """
        Start an emergency ambulance trip
        
        ENDPOINT: POST /api/v1/ambulance/trips
        
        Args:
            driver_id: Driver ID
            pickup_location: Pickup address
            patient_name: Optional patient name
            
        Returns:
            Trip record with ID
        """
        trip_id = self._generate_id("AMB")
        action = self.log_action("START_TRIP", driver_id, {
            "trip_id": trip_id,
            "pickup_location": pickup_location,
            "patient_name": patient_name
        })
        
        return {
            "success": True,
            "trip_id": trip_id,
            "driver_id": driver_id,
            "state": "EN_ROUTE",
            "pickup_location": pickup_location,
            "started_at": datetime.now().isoformat(),
            "action_id": action["id"]
        }
    
    def update_trip_state(self, trip_id: str, driver_id: str, new_state: str) -> dict:
        """
        Update trip state
        
        ENDPOINT: PATCH /api/v1/ambulance/trips/{trip_id}/state
        
        Args:
            trip_id: Trip ID
            driver_id: Driver ID
            new_state: New state (EN_ROUTE, PATIENT_LOADED, ARRIVING, COMPLETED)
            
        Returns:
            Updated trip record
        """
        action = self.log_action("UPDATE_TRIP_STATE", driver_id, {
            "trip_id": trip_id,
            "new_state": new_state
        })
        
        return {
            "success": True,
            "trip_id": trip_id,
            "state": new_state,
            "updated_at": datetime.now().isoformat(),
            "action_id": action["id"]
        }
    
    def get_trip_status(self, trip_id: str) -> dict:
        """
        Get current trip status including hospital confirmation
        
        ENDPOINT: GET /api/v1/ambulance/trips/{trip_id}
        
        Returns:
            Trip status with bed confirmation
        """
        return {
            "trip_id": trip_id,
            "state": "EN_ROUTE",
            "bed_confirmed": True,
            "destination_hospital": "City General Hospital",
            "confirmed_bed_id": "ICU-04",
            "eta_minutes": 12
        }
    
    def end_trip(self, trip_id: str, driver_id: str) -> dict:
        """
        End/complete an ambulance trip
        
        ENDPOINT: POST /api/v1/ambulance/trips/{trip_id}/complete
        
        Returns:
            Trip completion confirmation
        """
        action = self.log_action("END_TRIP", driver_id, {"trip_id": trip_id})
        
        return {
            "success": True,
            "trip_id": trip_id,
            "completed_at": datetime.now().isoformat(),
            "action_id": action["id"]
        }
    
    # ==================== ALERT ENDPOINTS ====================
    
    def get_alerts(self, staff_id: str, unread_only: bool = True) -> List[dict]:
        """
        Get alerts for staff member
        
        ENDPOINT: GET /api/v1/alerts?staff_id={staff_id}&unread_only={unread_only}
        
        Returns:
            List of alerts
        """
        state = self._read_json(STATE_FILE)
        alerts = state.get("alerts", [])
        
        if unread_only:
            alerts = [a for a in alerts if not a.get("is_read")]
        
        return alerts
    
    def mark_alert_read(self, alert_id: str, staff_id: str) -> dict:
        """
        Mark alert as read
        
        ENDPOINT: POST /api/v1/alerts/{alert_id}/read
        
        Returns:
            Confirmation
        """
        return {
            "success": True,
            "alert_id": alert_id,
            "read_at": datetime.now().isoformat()
        }
    
    def get_voice_alert_url(self, alert_id: str) -> str:
        """
        Get URL for voice alert audio
        
        ENDPOINT: GET /api/v1/alerts/{alert_id}/voice
        
        Returns:
            Audio URL
        """
        return f"{self.API_BASE_URL}/alerts/{alert_id}/voice.mp3"


# Singleton instance
api_service = APIService()
