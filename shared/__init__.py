"""
VitalFlow AI - Shared Module
"""

from .models import (
    BedType, PatientStatus, StaffRole,
    Patient, Bed, Staff, Hospital, AIDecision, Floor,
)

from .constants import (
    STATUS_COLORS, STATUS_EMOJI, FLOOR_CONFIG,
    VITAL_THRESHOLDS, AUTO_REFRESH_INTERVAL,
    MAP_CENTER, MAP_ZOOM, NETWORK_HOSPITALS,
)

from .mock_data import (
    generate_hospital_data, generate_network_hospitals,
    generate_patient, generate_ai_decisions,
)

from .data_service import (
    get_hospital_data, get_network_hospitals, get_patients,
    get_beds, get_staff, get_ai_decisions, get_hospital_stats, get_floors,
    transfer_patient, swap_beds, admit_patient, discharge_patient,
    approve_decision, override_decision, refresh_mock_data,
    check_backend_health, set_data_source, get_current_config, DataSource,
)

__all__ = [
    # Models
    "BedType", "PatientStatus", "StaffRole",
    "Patient", "Bed", "Staff", "Hospital", "AIDecision", "Floor",
    # Constants
    "STATUS_COLORS", "STATUS_EMOJI", "FLOOR_CONFIG", "VITAL_THRESHOLDS",
    "AUTO_REFRESH_INTERVAL", "MAP_CENTER", "MAP_ZOOM", "NETWORK_HOSPITALS",
    # Mock Data
    "generate_hospital_data", "generate_network_hospitals",
    "generate_patient", "generate_ai_decisions",
    # Data Service
    "get_hospital_data", "get_network_hospitals", "get_patients",
    "get_beds", "get_staff", "get_ai_decisions", "get_hospital_stats", "get_floors",
    "transfer_patient", "swap_beds", "admit_patient", "discharge_patient",
    "approve_decision", "override_decision", "refresh_mock_data",
    "check_backend_health", "set_data_source", "get_current_config", "DataSource",
]
