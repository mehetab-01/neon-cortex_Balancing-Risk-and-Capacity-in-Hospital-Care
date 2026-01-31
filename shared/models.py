"""
VitalFlow AI - Shared Data Models
Pydantic models for Patient, Bed, Staff, and Hospital entities
"""

from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BedType(Enum):
    ICU = "ICU"
    GENERAL = "General"
    EMERGENCY = "Emergency"


class PatientStatus(Enum):
    CRITICAL = "Critical"
    SERIOUS = "Serious"
    STABLE = "Stable"
    RECOVERING = "Recovering"


class StaffRole(Enum):
    DOCTOR = "Doctor"
    NURSE = "Nurse"
    WARDBOY = "Wardboy"
    DRIVER = "Driver"


class Patient(BaseModel):
    id: str
    name: str
    age: int
    diagnosis: str
    status: PatientStatus
    spo2: int  # 0-100
    heart_rate: int
    blood_pressure: str  # e.g., "120/80"
    temperature: float  # in Celsius
    bed_id: Optional[str] = None
    admitted_at: datetime
    assigned_doctor: Optional[str] = None
    notes: Optional[str] = None


class Bed(BaseModel):
    id: str
    floor: int
    bed_type: BedType
    is_occupied: bool
    patient_id: Optional[str] = None
    room_number: str


class Staff(BaseModel):
    id: str
    name: str
    role: StaffRole
    is_on_duty: bool
    shift_start: Optional[datetime] = None
    fatigue_level: int = 0  # 0-100
    assigned_patients: List[str] = []


class Hospital(BaseModel):
    id: str
    name: str
    total_beds: int
    occupied_beds: int
    icu_available: int
    emergency_available: int
    general_available: int
    lat: float
    lon: float
    address: str


class AIDecision(BaseModel):
    id: str
    timestamp: datetime
    action: str
    reason: str
    patient_id: Optional[str] = None
    from_bed: Optional[str] = None
    to_bed: Optional[str] = None
    severity: str = "INFO"  # INFO, WARNING, CRITICAL


class Floor(BaseModel):
    floor_number: int
    name: str
    bed_type: BedType
    total_beds: int
    beds: List[Bed]
