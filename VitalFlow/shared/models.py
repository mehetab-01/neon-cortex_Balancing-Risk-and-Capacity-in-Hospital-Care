"""
Shared Pydantic models for VitalFlow AI.
Used across frontend, backend, and simulation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PatientStatus(str, Enum):
    CRITICAL = "Critical"
    SERIOUS = "Serious"
    STABLE = "Stable"
    RECOVERING = "Recovering"
    DISCHARGED = "Discharged"


class BedType(str, Enum):
    ICU = "ICU"
    EMERGENCY = "Emergency"
    GENERAL = "General"
    PEDIATRIC = "Pediatric"
    MATERNITY = "Maternity"


class StaffRole(str, Enum):
    DOCTOR = "Doctor"
    NURSE = "Nurse"
    WARDBOY = "Wardboy"
    DRIVER = "Driver"
    ADMIN = "Admin"


class StaffStatus(str, Enum):
    AVAILABLE = "Available"
    BUSY = "Busy"
    ON_BREAK = "On Break"
    OFF_DUTY = "Off Duty"


class Patient(BaseModel):
    id: str
    name: str
    age: int
    gender: str = "Unknown"
    diagnosis: str = ""
    status: PatientStatus = PatientStatus.STABLE
    spo2: float = 98.0
    heart_rate: int = 75
    blood_pressure: str = "120/80"
    temperature: float = 98.6
    bed_id: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    assigned_nurse_id: Optional[str] = None
    admission_time: datetime = Field(default_factory=datetime.now)
    eta_minutes: Optional[int] = None  # For incoming ambulance patients
    ambulance_id: Optional[str] = None
    priority: int = 5  # 1-5, 1 is most urgent
    notes: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class Bed(BaseModel):
    id: str
    bed_type: BedType
    ward: str = "General Ward"
    floor: int = 1
    is_occupied: bool = False
    patient_id: Optional[str] = None
    last_sanitized: Optional[datetime] = None

    class Config:
        use_enum_values = True


class Staff(BaseModel):
    id: str
    name: str
    role: StaffRole
    status: StaffStatus = StaffStatus.AVAILABLE
    shift_start: Optional[datetime] = None
    current_patient_ids: List[str] = Field(default_factory=list)
    phone: str = ""
    specialization: str = ""
    floor_assigned: Optional[int] = None

    class Config:
        use_enum_values = True


class Ambulance(BaseModel):
    id: str
    driver_id: Optional[str] = None
    patient_id: Optional[str] = None
    current_location: tuple = (0.0, 0.0)  # lat, lng
    destination: tuple = (0.0, 0.0)
    eta_minutes: int = 0
    status: str = "Available"  # Available, En Route, At Scene, Returning


class Hospital(BaseModel):
    id: str = "VITALFLOW_MAIN"
    name: str = "VitalFlow General Hospital"
    location: tuple = (19.0760, 72.8777)  # Mumbai coordinates
    total_beds: int = 50
    floors: int = 5


class DecisionLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    action: str
    reason: str
    details: dict = Field(default_factory=dict)


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing Pydantic Models...")
    
    # Test Patient
    patient = Patient(
        id="P001",
        name="John Doe",
        age=45,
        diagnosis="Cardiac Arrest",
        status=PatientStatus.CRITICAL,
        spo2=85.0,
        heart_rate=140
    )
    print(f"✓ Patient created: {patient.name}, Status: {patient.status}")
    
    # Test Bed
    bed = Bed(
        id="ICU-01",
        bed_type=BedType.ICU,
        ward="ICU Ward",
        floor=3
    )
    print(f"✓ Bed created: {bed.id}, Type: {bed.bed_type}")
    
    # Test Staff
    staff = Staff(
        id="D001",
        name="Dr. Smith",
        role=StaffRole.DOCTOR,
        specialization="Cardiology"
    )
    print(f"✓ Staff created: {staff.name}, Role: {staff.role}")
    
    # Test serialization
    patient_dict = patient.dict()
    assert patient_dict["name"] == "John Doe"
    print("✓ Serialization works correctly")
    
    print("\n✅ All model tests passed!")
