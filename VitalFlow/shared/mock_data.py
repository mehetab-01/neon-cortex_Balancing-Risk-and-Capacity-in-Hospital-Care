"""
Faker-based mock data generation for VitalFlow AI.
Generates realistic hospital data for demos and testing.
"""
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.models import (
    Patient, Bed, Staff, Ambulance,
    PatientStatus, BedType, StaffRole, StaffStatus
)
from shared.constants import BED_DISTRIBUTION, WARD_NAMES

# Try to import Faker, fallback to basic random if not available
try:
    from faker import Faker
    fake = Faker('en_IN')  # Indian locale
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False
    print("Faker not installed. Run: pip install faker")


# Indian names fallback
INDIAN_FIRST_NAMES = [
    "Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Suresh", "Kavita",
    "Arun", "Neha", "Sanjay", "Pooja", "Rahul", "Sunita", "Deepak", "Meera",
    "Anand", "Lakshmi", "Vijay", "Geeta", "Mohan", "Rani", "Krishna", "Sita"
]

INDIAN_LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Reddy", "Nair", "Iyer", "Rao",
    "Gupta", "Mehta", "Joshi", "Shah", "Verma", "Agarwal", "Kapoor", "Desai"
]

DIAGNOSES = [
    # Critical
    ("Cardiac Arrest", PatientStatus.CRITICAL),
    ("Acute Myocardial Infarction", PatientStatus.CRITICAL),
    ("Severe Respiratory Failure", PatientStatus.CRITICAL),
    ("Major Trauma - MVA", PatientStatus.CRITICAL),
    ("Septic Shock", PatientStatus.CRITICAL),
    ("Stroke - Hemorrhagic", PatientStatus.CRITICAL),
    
    # Serious
    ("Pneumonia with Hypoxia", PatientStatus.SERIOUS),
    ("Diabetic Ketoacidosis", PatientStatus.SERIOUS),
    ("Acute Appendicitis", PatientStatus.SERIOUS),
    ("Severe Dehydration", PatientStatus.SERIOUS),
    ("Chest Pain - Rule Out MI", PatientStatus.SERIOUS),
    ("COPD Exacerbation", PatientStatus.SERIOUS),
    
    # Stable
    ("Controlled Hypertension", PatientStatus.STABLE),
    ("Stable Angina", PatientStatus.STABLE),
    ("Viral Gastroenteritis", PatientStatus.STABLE),
    ("Mild Pneumonia", PatientStatus.STABLE),
    ("UTI - Uncomplicated", PatientStatus.STABLE),
    ("Post-Surgery Recovery", PatientStatus.STABLE),
    
    # Recovering
    ("Post Cardiac Surgery - Day 3", PatientStatus.RECOVERING),
    ("Recovering from Pneumonia", PatientStatus.RECOVERING),
    ("Fracture - Post Fixation", PatientStatus.RECOVERING),
    ("Post Appendectomy", PatientStatus.RECOVERING),
]

SPECIALIZATIONS = [
    "Cardiology", "Pulmonology", "Emergency Medicine", "Internal Medicine",
    "Surgery", "Orthopedics", "Neurology", "Pediatrics", "Oncology", "Nephrology"
]


def generate_name() -> str:
    """Generate a realistic Indian name."""
    if FAKER_AVAILABLE:
        return fake.name()
    first = random.choice(INDIAN_FIRST_NAMES)
    last = random.choice(INDIAN_LAST_NAMES)
    return f"{first} {last}"


def generate_phone() -> str:
    """Generate Indian mobile number."""
    if FAKER_AVAILABLE:
        return fake.phone_number()
    return f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}"


def generate_patient(
    patient_id: str = None,
    status: PatientStatus = None,
    min_age: int = 18,
    max_age: int = 85
) -> Patient:
    """
    Generate a random patient.
    
    Args:
        patient_id: Optional specific ID
        status: Optional specific status
        min_age: Minimum age
        max_age: Maximum age
        
    Returns:
        Patient object
    """
    if patient_id is None:
        patient_id = f"P-{random.randint(1000, 9999)}"
    
    # Select diagnosis (which determines status if not specified)
    diagnosis, default_status = random.choice(DIAGNOSES)
    if status is None:
        status = default_status
    
    # Generate vitals based on status
    if status == PatientStatus.CRITICAL:
        spo2 = random.uniform(75, 88)
        heart_rate = random.choice([random.randint(35, 50), random.randint(140, 180)])
        temp = random.uniform(99, 104)
    elif status == PatientStatus.SERIOUS:
        spo2 = random.uniform(88, 93)
        heart_rate = random.randint(100, 130)
        temp = random.uniform(99, 102)
    elif status == PatientStatus.STABLE:
        spo2 = random.uniform(94, 97)
        heart_rate = random.randint(70, 100)
        temp = random.uniform(97, 99)
    else:  # Recovering
        spo2 = random.uniform(96, 99)
        heart_rate = random.randint(65, 85)
        temp = random.uniform(97, 98.6)
    
    # Blood pressure
    if status == PatientStatus.CRITICAL:
        bp_sys = random.randint(70, 90) if random.random() < 0.5 else random.randint(180, 220)
        bp_dia = random.randint(40, 60) if bp_sys < 100 else random.randint(100, 130)
    elif status == PatientStatus.SERIOUS:
        bp_sys = random.randint(90, 100) if random.random() < 0.3 else random.randint(150, 180)
        bp_dia = random.randint(60, 70) if bp_sys < 110 else random.randint(90, 110)
    else:
        bp_sys = random.randint(110, 140)
        bp_dia = random.randint(70, 90)
    
    return Patient(
        id=patient_id,
        name=generate_name(),
        age=random.randint(min_age, max_age),
        gender=random.choice(["Male", "Female"]),
        diagnosis=diagnosis,
        status=status,
        spo2=round(spo2, 1),
        heart_rate=heart_rate,
        blood_pressure=f"{bp_sys}/{bp_dia}",
        temperature=round(temp, 1),
        admission_time=datetime.now() - timedelta(hours=random.randint(0, 72)),
        priority=1 if status == PatientStatus.CRITICAL else (2 if status == PatientStatus.SERIOUS else 3)
    )


def generate_beds() -> List[Bed]:
    """
    Generate all beds for the hospital based on BED_DISTRIBUTION.
    
    Returns:
        List of Bed objects
    """
    beds = []
    
    for bed_type_str, count in BED_DISTRIBUTION.items():
        bed_type = BedType(bed_type_str)
        
        # Determine floor and ward
        if bed_type == BedType.ICU:
            floor = 4
            ward = "ICU Ward"
        elif bed_type == BedType.EMERGENCY:
            floor = 1
            ward = "Emergency Ward"
        elif bed_type == BedType.PEDIATRIC:
            floor = 5
            ward = "Pediatric Ward"
        elif bed_type == BedType.MATERNITY:
            floor = 5
            ward = "Maternity Ward"
        else:
            floor = random.choice([2, 3])
            ward = f"General Ward {'A' if floor == 2 else 'B'}"
        
        for i in range(count):
            bed_id = f"{bed_type.value[:3].upper()}-{i+1:02d}"
            beds.append(Bed(
                id=bed_id,
                bed_type=bed_type,
                ward=ward,
                floor=floor,
                is_occupied=False,
                last_sanitized=datetime.now() - timedelta(hours=random.randint(1, 8))
            ))
    
    return beds


def generate_staff() -> List[Staff]:
    """
    Generate hospital staff.
    
    Returns:
        List of Staff objects
    """
    staff = []
    
    # Doctors (10)
    for i in range(10):
        staff.append(Staff(
            id=f"D{i+1:03d}",
            name=f"Dr. {generate_name().split()[-1]}",
            role=StaffRole.DOCTOR,
            status=StaffStatus.AVAILABLE,
            specialization=random.choice(SPECIALIZATIONS),
            phone=generate_phone(),
            floor_assigned=random.choice([1, 2, 3, 4, 5]),
            shift_start=datetime.now() - timedelta(hours=random.randint(0, 8))
        ))
    
    # Nurses (20)
    for i in range(20):
        staff.append(Staff(
            id=f"N{i+1:03d}",
            name=f"Nurse {generate_name().split()[0]}",
            role=StaffRole.NURSE,
            status=StaffStatus.AVAILABLE,
            phone=generate_phone(),
            floor_assigned=random.choice([1, 2, 3, 4, 5]),
            shift_start=datetime.now() - timedelta(hours=random.randint(0, 10))
        ))
    
    # Ward Boys (10)
    for i in range(10):
        staff.append(Staff(
            id=f"W{i+1:03d}",
            name=generate_name().split()[0],
            role=StaffRole.WARDBOY,
            status=StaffStatus.AVAILABLE,
            phone=generate_phone(),
            floor_assigned=random.choice([1, 2, 3, 4, 5])
        ))
    
    # Drivers (5)
    for i in range(5):
        staff.append(Staff(
            id=f"DR{i+1:03d}",
            name=generate_name().split()[0],
            role=StaffRole.DRIVER,
            status=StaffStatus.AVAILABLE,
            phone=generate_phone()
        ))
    
    return staff


def generate_ambulance(ambulance_id: str = None, with_patient: bool = False) -> Ambulance:
    """
    Generate an ambulance.
    
    Args:
        ambulance_id: Optional specific ID
        with_patient: Whether to include a patient
        
    Returns:
        Ambulance object
    """
    if ambulance_id is None:
        ambulance_id = f"AMB-{random.randint(100, 999)}"
    
    # Mumbai area coordinates
    lat = 19.0 + random.uniform(-0.1, 0.1)
    lng = 72.8 + random.uniform(-0.1, 0.1)
    
    # Hospital location
    hospital_lat, hospital_lng = 19.0760, 72.8777
    
    patient_id = None
    eta = 0
    status = "Available"
    
    if with_patient:
        patient_id = f"P-AMB-{random.randint(100, 999)}"
        eta = random.randint(3, 20)
        status = "En Route"
    
    return Ambulance(
        id=ambulance_id,
        patient_id=patient_id,
        current_location=(lat, lng),
        destination=(hospital_lat, hospital_lng),
        eta_minutes=eta,
        status=status
    )


def generate_incoming_patient() -> Patient:
    """
    Generate an incoming patient (ambulance case).
    Typically more critical.
    
    Returns:
        Patient object with ambulance details
    """
    # Incoming patients are usually critical or serious
    status = random.choice([PatientStatus.CRITICAL, PatientStatus.CRITICAL, PatientStatus.SERIOUS])
    patient = generate_patient(status=status)
    
    patient.ambulance_id = f"AMB-{random.randint(100, 999)}"
    patient.eta_minutes = random.randint(3, 15)
    
    return patient


def populate_hospital_state(
    occupancy_rate: float = 0.7,
    include_incoming: bool = True
) -> Dict:
    """
    Generate complete hospital state with patients, beds, and staff.
    
    Args:
        occupancy_rate: Percentage of beds to fill
        include_incoming: Whether to include incoming ambulance patients
        
    Returns:
        Dict with patients, beds, staff
    """
    beds = generate_beds()
    staff = generate_staff()
    patients = []
    
    # Assign patients to beds
    for bed in beds:
        if random.random() < occupancy_rate:
            # Determine patient status based on bed type
            if bed.bed_type == BedType.ICU:
                status = random.choice([PatientStatus.CRITICAL, PatientStatus.SERIOUS])
            elif bed.bed_type == BedType.EMERGENCY:
                status = random.choice([PatientStatus.SERIOUS, PatientStatus.STABLE])
            else:
                status = random.choice([PatientStatus.STABLE, PatientStatus.RECOVERING])
            
            patient = generate_patient(status=status)
            patient.bed_id = bed.id
            
            # Assign doctor and nurse
            doctors = [s for s in staff if s.role == StaffRole.DOCTOR and len(s.current_patient_ids) < 5]
            nurses = [s for s in staff if s.role == StaffRole.NURSE and len(s.current_patient_ids) < 8]
            
            if doctors:
                doc = random.choice(doctors)
                patient.assigned_doctor_id = doc.id
                doc.current_patient_ids.append(patient.id)
            
            if nurses:
                nurse = random.choice(nurses)
                patient.assigned_nurse_id = nurse.id
                nurse.current_patient_ids.append(patient.id)
            
            patients.append(patient)
            bed.is_occupied = True
            bed.patient_id = patient.id
    
    # Add incoming patients
    incoming = []
    if include_incoming:
        for _ in range(random.randint(1, 3)):
            incoming.append(generate_incoming_patient())
    
    return {
        "beds": beds,
        "staff": staff,
        "patients": patients,
        "incoming": incoming
    }


def load_mock_data_to_state():
    """
    Load mock data into the hospital state.
    Call this to initialize the system with test data.
    """
    from backend.core_logic.state import hospital_state
    
    # Clear existing state
    hospital_state.clear_all()
    
    # Generate data
    data = populate_hospital_state(occupancy_rate=0.6)
    
    # Load into state
    for bed in data["beds"]:
        hospital_state.beds[bed.id] = bed
    
    for patient in data["patients"]:
        hospital_state.patients[patient.id] = patient
    
    for staff_member in data["staff"]:
        hospital_state.staff[staff_member.id] = staff_member
    
    hospital_state.save()
    
    stats = hospital_state.get_stats()
    print(f"✓ Mock data loaded:")
    print(f"  - Beds: {stats['total_beds']} ({stats['occupied_beds']} occupied)")
    print(f"  - Patients: {stats['total_patients']}")
    print(f"  - Staff: {stats['total_staff']}")
    
    return data


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing Mock Data Generation...")
    print(f"Faker available: {FAKER_AVAILABLE}")
    
    # Test name generation
    name = generate_name()
    print(f"✓ Generated name: {name}")
    
    # Test patient generation
    patient = generate_patient()
    print(f"✓ Generated patient: {patient.name}, {patient.age}yo, {patient.status.value}")
    print(f"  Diagnosis: {patient.diagnosis}")
    print(f"  Vitals: SpO2={patient.spo2}%, HR={patient.heart_rate}, BP={patient.blood_pressure}")
    
    # Test critical patient
    critical = generate_patient(status=PatientStatus.CRITICAL)
    assert critical.status == PatientStatus.CRITICAL
    assert critical.spo2 < 90 or critical.heart_rate > 140 or critical.heart_rate < 50
    print("✓ Critical patient has appropriate vitals")
    
    # Test bed generation
    beds = generate_beds()
    print(f"✓ Generated {len(beds)} beds")
    
    bed_counts = {}
    for bed in beds:
        bt = bed.bed_type.value
        bed_counts[bt] = bed_counts.get(bt, 0) + 1
    print(f"  Distribution: {bed_counts}")
    
    # Verify matches BED_DISTRIBUTION
    for bed_type, expected in BED_DISTRIBUTION.items():
        assert bed_counts.get(bed_type, 0) == expected, f"Mismatch for {bed_type}"
    print("✓ Bed distribution matches configuration")
    
    # Test staff generation
    staff = generate_staff()
    print(f"✓ Generated {len(staff)} staff members")
    
    role_counts = {}
    for s in staff:
        role = s.role.value
        role_counts[role] = role_counts.get(role, 0) + 1
    print(f"  Roles: {role_counts}")
    
    # Test ambulance generation
    ambulance = generate_ambulance(with_patient=True)
    print(f"✓ Generated ambulance: {ambulance.id}, Status: {ambulance.status}, ETA: {ambulance.eta_minutes}min")
    
    # Test incoming patient
    incoming = generate_incoming_patient()
    assert incoming.status in [PatientStatus.CRITICAL, PatientStatus.SERIOUS]
    print(f"✓ Generated incoming patient: {incoming.name}, {incoming.status.value}")
    
    # Test full hospital population
    print("\n--- Generating Full Hospital ---")
    data = populate_hospital_state(occupancy_rate=0.5)
    
    occupied_beds = sum(1 for b in data["beds"] if b.is_occupied)
    print(f"✓ Hospital populated:")
    print(f"  - Beds: {len(data['beds'])} ({occupied_beds} occupied)")
    print(f"  - Patients: {len(data['patients'])}")
    print(f"  - Staff: {len(data['staff'])}")
    print(f"  - Incoming: {len(data['incoming'])}")
    
    # Verify patient-bed assignments
    for patient in data["patients"][:3]:
        if patient.bed_id:
            bed = next((b for b in data["beds"] if b.id == patient.bed_id), None)
            assert bed is not None
            assert bed.patient_id == patient.id
    print("✓ Patient-bed assignments correct")
    
    print("\n✅ All mock data tests passed!")
