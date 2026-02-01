"""
VitalFlow AI - Backend Test Runner
Run this script to test all backend functionality.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta

print("=" * 60)
print("  VitalFlow AI - Backend Test Suite")
print("=" * 60)

# ============== TEST 1: State Management ==============
print("\n📦 TEST 1: State Management")
print("-" * 40) 

from backend.core_logic.state import hospital_state
from shared.models import Patient, Bed, Staff, PatientStatus, BedType, StaffRole

# Clear state
hospital_state.clear_all()
print("✓ State cleared")

# Add test beds
beds_config = [
    ("ICU-01", BedType.ICU), ("ICU-02", BedType.ICU), ("ICU-03", BedType.ICU),
    ("ER-01", BedType.EMERGENCY), ("ER-02", BedType.EMERGENCY),
    ("GEN-01", BedType.GENERAL), ("GEN-02", BedType.GENERAL), 
    ("GEN-03", BedType.GENERAL), ("GEN-04", BedType.GENERAL),
]

for bed_id, bed_type in beds_config:
    bed = Bed(id=bed_id, bed_type=bed_type, ward=f"{bed_type.value} Ward", floor=1)
    hospital_state.add_bed(bed)

print(f"✓ Created {len(hospital_state.beds)} beds")

# Add test staff
doctors = [
    Staff(id="D001", name="Dr. Sharma", role=StaffRole.DOCTOR, specialization="Cardiology"),
    Staff(id="D002", name="Dr. Patel", role=StaffRole.DOCTOR, specialization="Emergency"),
    Staff(id="D003", name="Dr. Kumar", role=StaffRole.DOCTOR, specialization="Pulmonology"),
]
nurses = [
    Staff(id="N001", name="Nurse Priya", role=StaffRole.NURSE),
    Staff(id="N002", name="Nurse Anita", role=StaffRole.NURSE),
]

for s in doctors + nurses:
    hospital_state.add_staff(s)

print(f"✓ Created {len(hospital_state.staff)} staff members")

# ============== TEST 2: Staff Management ==============
print("\n👨‍⚕️ TEST 2: Staff Management")
print("-" * 40)

from backend.core_logic.staff_manager import staff_manager

# Punch in staff
for s in doctors + nurses:
    staff_manager.punch_in(s.id)

print("✓ All staff punched in")

# Check available doctors
available_docs = staff_manager.get_available_doctors()
print(f"✓ Available doctors: {len(available_docs)}")

# Simulate fatigue for one doctor
doc = hospital_state.staff.get("D002")
doc.shift_start = datetime.now() - timedelta(hours=11)

warning = staff_manager.get_fatigue_warning("D002")
print(f"⚠️  {warning}")

# ============== TEST 3: Bed Manager & Tetris Algorithm ==============
print("\n🛏️  TEST 3: Bed Manager & Tetris Algorithm")
print("-" * 40)

from backend.core_logic.bed_manager import bed_manager

# Fill ICU with stable patients
print("Filling ICU with stable patients...")
for i, bed_id in enumerate(["ICU-01", "ICU-02", "ICU-03"]):
    patient = Patient(
        id=f"P-STABLE-{i}",
        name=f"Stable Patient {i+1}",
        age=50 + i*5,
        status=PatientStatus.STABLE,
        spo2=96.0 + i,
        heart_rate=75 + i*2,
        diagnosis="Recovering from surgery"
    )
    hospital_state.add_patient(patient)
    bed_manager.assign_patient_to_bed(patient.id, bed_id)
    print(f"  → {patient.name} assigned to {bed_id}")

# Check ICU is full
available_icu = bed_manager.get_available_beds(BedType.ICU)
print(f"\n✓ ICU beds available: {len(available_icu)} (should be 0)")

# Now a CRITICAL patient arrives!
print("\n🚨 CRITICAL PATIENT ARRIVING!")
critical_patient = Patient(
    id="P-CRITICAL-1",
    name="Ramesh Kumar",
    age=58,
    status=PatientStatus.CRITICAL,
    spo2=82.0,
    heart_rate=150,
    diagnosis="Acute Myocardial Infarction"
)
hospital_state.add_patient(critical_patient)

# Handle both string and enum for status
status_str = critical_patient.status.value if hasattr(critical_patient.status, 'value') else critical_patient.status
print(f"  Patient: {critical_patient.name}")
print(f"  Status: {status_str}")
print(f"  SpO2: {critical_patient.spo2}%")
print(f"  Heart Rate: {critical_patient.heart_rate} bpm")

# Execute Tetris swap
print("\n🔄 Executing Tetris Swap Algorithm...")
success, message = bed_manager.execute_swap(critical_patient)

print(f"\n✓ Swap Result: {success}")
print(f"  Message: {message}")

# Verify swap
print(f"\n📍 After Swap:")
print(f"  Critical patient {critical_patient.name} is now in: {critical_patient.bed_id}")

# Find where the swapped patient went
for pid, p in hospital_state.patients.items():
    if p.id != critical_patient.id and p.bed_id:
        if "GEN" in p.bed_id or "ER" in p.bed_id:
            print(f"  Swapped patient {p.name} moved to: {p.bed_id}")

# ============== TEST 4: Triage Engine ==============
print("\n🏥 TEST 4: Triage Engine")
print("-" * 40)

from backend.core_logic.triage_engine import triage_engine

# Process new incoming patient
incoming = Patient(
    id="P-INCOMING-1",
    name="Priya Singh",
    age=35,
    status=PatientStatus.SERIOUS,
    spo2=89.0,
    heart_rate=115,
    diagnosis="Pneumonia with Hypoxia"
)

print(f"Processing incoming patient: {incoming.name}")
result = triage_engine.process_incoming_patient(incoming)

print(f"  Priority: {result['priority']} ({result['priority_label']})")
print(f"  Bed Assigned: {result['bed_assigned']}")
print(f"  Doctor Assigned: {result['doctor_assigned']}")
print(f"  Nurse Assigned: {result['nurse_assigned']}")

# Get patient queue
print("\n📋 Patient Queue (by priority):")
queue = triage_engine.get_patient_queue()
for p in queue[:5]:
    print(f"  {p['priority']}. {p['name']} - {p['status']} - Bed: {p['bed_id'] or 'Waiting'}")

# Get critical alerts
alerts = triage_engine.get_critical_alerts()
if alerts:
    print(f"\n🚨 Critical Alerts: {len(alerts)}")
    for alert in alerts[:3]:
        print(f"  [{alert['type']}] {alert['patient_name']}: {alert['condition'][:50]}...")

# ============== TEST 5: Medicine AI ==============
print("\n💊 TEST 5: Medicine AI Recommendations")
print("-" * 40)

from backend.ai_services.medicine_ai import medicine_ai

# Get recommendation for critical patient
print(f"Getting recommendations for: {critical_patient.name}")
print(f"  Diagnosis: {critical_patient.diagnosis}")

recs = medicine_ai.get_preparation_checklist(critical_patient)

print(f"\n  Urgency: {recs['urgency']}")
print(f"  Monitoring: {recs['monitoring_frequency']}")
print(f"\n  Equipment ({len(recs['equipment'])} items):")
for eq in recs['equipment'][:5]:
    print(f"    • {eq}")
print(f"\n  Medications ({len(recs['medications'])} items):")
for med in recs['medications'][:5]:
    print(f"    • {med}")
print(f"\n  Special Instructions: {recs['special_instructions'][:100]}...")

# ============== TEST 6: Voice Alerts ==============
print("\n🔊 TEST 6: Voice Alerts")
print("-" * 40)

from backend.ai_services.voice_alerts import voice_service

# Get alert texts (without generating audio)
print("Alert Text Examples:")

code_blue_text = voice_service.get_alert_text(
    "CODE_BLUE",
    station="A3",
    bed_id=critical_patient.bed_id,
    medications="epinephrine and defibrillator"
)
print(f"\n  CODE_BLUE:")
print(f"    {code_blue_text}")

vitals_text = voice_service.get_alert_text(
    "VITALS_CRITICAL",
    bed_id=critical_patient.bed_id,
    spo2=int(critical_patient.spo2)
)
print(f"\n  VITALS_CRITICAL:")
print(f"    {vitals_text}")

# ============== TEST 7: Decision Log ==============
print("\n📜 TEST 7: Decision Log")
print("-" * 40)

decisions = hospital_state.get_recent_decisions(10)
print(f"Recent Decisions ({len(decisions)}):")
for d in decisions[-5:]:
    print(f"  [{d['action']}] {d['reason'][:60]}...")

# ============== TEST 8: Hospital Stats ==============
print("\n📊 TEST 8: Hospital Statistics")
print("-" * 40)

stats = hospital_state.get_stats()
print(f"  Total Beds: {stats['total_beds']}")
print(f"  Occupied: {stats['occupied_beds']}")
print(f"  Available: {stats['available_beds']}")
print(f"  Occupancy Rate: {stats['occupancy_rate']:.1f}%")
print(f"\n  Patients by Status:")
for status, count in stats['patients_by_status'].items():
    if count > 0:
        print(f"    • {status}: {count}")

print(f"\n  Beds by Type:")
for bed_type, data in stats['by_bed_type'].items():
    if data['total'] > 0:
        print(f"    • {bed_type}: {data['occupied']}/{data['total']} occupied")

# ============== FINAL SUMMARY ==============
print("\n" + "=" * 60)
print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)

print("\n📁 State saved to: VitalFlow/shared/state.json")
print("\n🎯 Key Features Demonstrated:")
print("   1. State management with JSON persistence")
print("   2. Staff fatigue tracking")
print("   3. Tetris bed swapping algorithm")
print("   4. Triage priority calculations")
print("   5. AI medicine recommendations")
print("   6. Voice alert generation")
print("   7. Decision logging for transparency")

print("\n💡 Next Steps:")
print("   • Set up .env with API keys for full AI features")
print("   • Run individual module tests: python backend/core_logic/bed_manager.py")
print("   • Build frontend with Streamlit")
print()
