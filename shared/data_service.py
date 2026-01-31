"""
VitalFlow AI - Data Service Layer
Clean API endpoints for backend integration
"""

import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class DataSource(Enum):
    MOCK = "mock"
    API = "api"


@dataclass
class APIConfig:
    base_url: str = os.getenv("VITALFLOW_API_URL", "http://localhost:8000/api")
    api_key: str = os.getenv("VITALFLOW_API_KEY", "")
    timeout: int = 10


CURRENT_DATA_SOURCE = DataSource.MOCK
API_CONFIG = APIConfig()
_mock_cache: Dict[str, Any] = {}


def _api_get(endpoint: str, params: Dict = None) -> Optional[Dict]:
    try:
        headers = {"Content-Type": "application/json"}
        if API_CONFIG.api_key:
            headers["Authorization"] = f"Bearer {API_CONFIG.api_key}"
        response = requests.get(
            f"{API_CONFIG.base_url}{endpoint}",
            headers=headers,
            params=params,
            timeout=API_CONFIG.timeout
        )
        response.raise_for_status()
        return response.json()
    except:
        return None


def _api_post(endpoint: str, data: Dict) -> Optional[Dict]:
    try:
        headers = {"Content-Type": "application/json"}
        if API_CONFIG.api_key:
            headers["Authorization"] = f"Bearer {API_CONFIG.api_key}"
        response = requests.post(
            f"{API_CONFIG.base_url}{endpoint}",
            headers=headers,
            json=data,
            timeout=API_CONFIG.timeout
        )
        response.raise_for_status()
        return response.json()
    except:
        return None


def _get_mock_data(hospital_id: str = "H001") -> Dict:
    global _mock_cache
    from shared.mock_data import generate_hospital_data, generate_network_hospitals
    
    if f"hospital_{hospital_id}" not in _mock_cache:
        _mock_cache[f"hospital_{hospital_id}"] = generate_hospital_data(hospital_id)
        _mock_cache["network"] = generate_network_hospitals()
    return _mock_cache[f"hospital_{hospital_id}"]


def refresh_mock_data(hospital_id: str = "H001"):
    global _mock_cache
    from shared.mock_data import generate_hospital_data, generate_network_hospitals
    _mock_cache[f"hospital_{hospital_id}"] = generate_hospital_data(hospital_id)
    _mock_cache["network"] = generate_network_hospitals()


# READ ENDPOINTS
def get_hospital_data(hospital_id: str = "H001") -> Dict:
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_get(f"/hospital/{hospital_id}")
        if data:
            return data
    return _get_mock_data(hospital_id)


def get_network_hospitals() -> List[Dict]:
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_get("/hospitals")
        if data:
            return data
    _get_mock_data()
    return _mock_cache.get("network", [])


def get_patients(hospital_id: str = "H001", floor: int = None, status: str = None) -> List[Dict]:
    if CURRENT_DATA_SOURCE == DataSource.API:
        params = {}
        if floor:
            params['floor'] = floor
        if status:
            params['status'] = status
        data = _api_get(f"/hospital/{hospital_id}/patients", params)
        if data:
            return data
    
    data = _get_mock_data(hospital_id)
    patients = data.get('patients', [])
    if status:
        patients = [p for p in patients if p.get('status') == status]
    return patients


def get_beds(hospital_id: str = "H001", floor: int = None, available_only: bool = False) -> List[Dict]:
    if CURRENT_DATA_SOURCE == DataSource.API:
        params = {}
        if floor:
            params['floor'] = floor
        if available_only:
            params['available'] = True
        data = _api_get(f"/hospital/{hospital_id}/beds", params)
        if data:
            return data
    
    data = _get_mock_data(hospital_id)
    beds = data.get('beds', [])
    if floor:
        beds = [b for b in beds if b.get('floor') == floor]
    if available_only:
        beds = [b for b in beds if not b.get('is_occupied')]
    return beds


def get_staff(hospital_id: str = "H001", on_duty_only: bool = False) -> List[Dict]:
    if CURRENT_DATA_SOURCE == DataSource.API:
        params = {'on_duty': True} if on_duty_only else {}
        data = _api_get(f"/hospital/{hospital_id}/staff", params)
        if data:
            return data
    
    data = _get_mock_data(hospital_id)
    staff = data.get('staff', [])
    if on_duty_only:
        staff = [s for s in staff if s.get('is_on_duty')]
    return staff


def get_ai_decisions(hospital_id: str = "H001", limit: int = 20) -> List[Dict]:
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_get(f"/hospital/{hospital_id}/decisions", {'limit': limit})
        if data:
            return data
    return _get_mock_data(hospital_id).get('decisions', [])[:limit]


def get_hospital_stats(hospital_id: str = "H001") -> Dict:
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_get(f"/hospital/{hospital_id}/stats")
        if data:
            return data
    return _get_mock_data(hospital_id).get('stats', {})


def get_floors(hospital_id: str = "H001") -> List[Dict]:
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_get(f"/hospital/{hospital_id}/floors")
        if data:
            return data
    return _get_mock_data(hospital_id).get('floors', [])


# WRITE ENDPOINTS
def transfer_patient(patient_id: str, from_hospital: str, to_hospital: str, priority: str = "Standard") -> Dict:
    payload = {"patient_id": patient_id, "to_hospital": to_hospital, "priority": priority}
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_post(f"/hospital/{from_hospital}/patient/transfer", payload)
        if data:
            return data
    return {"success": True, "transfer_id": f"TRF-{datetime.now().strftime('%H%M%S')}", **payload}


def swap_beds(hospital_id: str, patient_id: str, to_bed: str, reason: str = "") -> Dict:
    payload = {"patient_id": patient_id, "to_bed": to_bed, "reason": reason}
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_post(f"/hospital/{hospital_id}/bed/swap", payload)
        if data:
            return data
    return {"success": True, "message": f"Moved to {to_bed} (mock)"}


def admit_patient(hospital_id: str, patient_data: Dict, bed_id: str) -> Dict:
    payload = {"patient": patient_data, "bed_id": bed_id}
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_post(f"/hospital/{hospital_id}/patient/admit", payload)
        if data:
            return data
    return {"success": True, "patient_id": f"P{datetime.now().strftime('%H%M%S')}", "bed_id": bed_id}


def discharge_patient(hospital_id: str, patient_id: str) -> Dict:
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_post(f"/hospital/{hospital_id}/patient/{patient_id}/discharge", {})
        if data:
            return data
    return {"success": True, "patient_id": patient_id, "discharged_at": datetime.now().isoformat()}


def approve_decision(decision_id: str) -> Dict:
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_post(f"/decision/{decision_id}/approve", {})
        if data:
            return data
    return {"success": True, "decision_id": decision_id, "status": "approved"}


def override_decision(decision_id: str, reason: str) -> Dict:
    if CURRENT_DATA_SOURCE == DataSource.API:
        data = _api_post(f"/decision/{decision_id}/override", {"reason": reason})
        if data:
            return data
    return {"success": True, "decision_id": decision_id, "status": "overridden"}


# UTILITY
def check_backend_health() -> Dict:
    if CURRENT_DATA_SOURCE == DataSource.API:
        try:
            response = requests.get(f"{API_CONFIG.base_url}/health", timeout=5)
            return {"status": "healthy" if response.ok else "unhealthy", "api_available": response.ok}
        except:
            return {"status": "unavailable", "api_available": False}
    return {"status": "mock_mode", "api_available": False}


def set_data_source(source: DataSource):
    global CURRENT_DATA_SOURCE
    CURRENT_DATA_SOURCE = source


def get_current_config() -> Dict:
    return {"data_source": CURRENT_DATA_SOURCE.value, "api_url": API_CONFIG.base_url}
