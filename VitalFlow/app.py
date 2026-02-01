"""
VitalFlow AI - FastAPI Backend Server
Run with: uvicorn app:app --reload --port 8000
"""
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our modules
from shared.models import Patient, Bed, Staff, PatientStatus, BedType, StaffRole, StaffStatus
from shared.utils import get_enum_value
from backend.core_logic.state import hospital_state
from backend.core_logic.bed_manager import bed_manager
from backend.core_logic.staff_manager import staff_manager
from backend.core_logic.triage_engine import triage_engine
from backend.core_logic.emergency_protocols import emergency_protocol_engine as protocol_engine
from backend.core_logic.ambulance_manager import ambulance_manager
from backend.core_logic.billing_agent import billing_agent
from backend.core_logic.stock_manager import stock_manager
from backend.core_logic.patient_report import patient_report_system
from backend.core_logic.prescription_scanner import prescription_scanner
from backend.core_logic.doctor_alerts import doctor_alert_system, DoctorStatus, AlertPriority
from backend.ai_services.medicine_ai import medicine_ai
from backend.ai_services.voice_alerts import voice_service
from backend.ai_services.fall_detector import fall_detector
from backend.agents.vitalflow_agent import vitalflow_agent

# ============== APP SETUP ==============
app = FastAPI(
    title="VitalFlow AI",
    description="Hospital Command Center - Balancing Risk and Capacity",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== REQUEST MODELS ==============
class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str = "Unknown"
    diagnosis: str = ""
    status: str = "Stable"
    spo2: float = 98.0
    heart_rate: int = 75
    blood_pressure: str = "120/80"
    temperature: float = 98.6

class VitalsUpdate(BaseModel):
    spo2: Optional[float] = None
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    temperature: Optional[float] = None

class StaffCreate(BaseModel):
    name: str
    role: str  # Doctor, Nurse, Wardboy, Driver
    specialization: str = ""
    phone: str = ""

class AmbulanceRegister(BaseModel):
    ambulance_id: str
    patient_name: str = "Unknown"
    patient_age: int = 40
    condition: str = "Unknown"
    severity: str = "Critical"  # Critical, Serious, Stable
    eta_minutes: int = 15
    location: str = ""
    contact: str = ""

class AlertVerify(BaseModel):
    verified_by: str
    is_emergency: bool
    notes: str = ""

class ApprovalRequest(BaseModel):
    decision_id: str
    approved_by: str
    approve: bool
    notes: str = ""

# New Request Models for Stock, Prescriptions, Reports, and Alerts
class MedicineUsage(BaseModel):
    medicine_id: str
    quantity: int
    patient_id: str
    recorded_by: str
    notes: str = ""

class OrderVerification(BaseModel):
    verified_by: str
    approve: bool
    notes: str = ""
    modified_quantities: Optional[dict] = None

class VitalsRecord(BaseModel):
    recorded_by: str
    spo2: float = 98.0
    heart_rate: int = 75
    blood_pressure: str = "120/80"
    temperature: float = 98.6
    respiratory_rate: int = 16
    notes: str = ""

class ConsultationNote(BaseModel):
    doctor_id: str
    doctor_name: str
    findings: str
    diagnosis: str
    treatment_plan: str
    next_visit: Optional[str] = None
    priority: str = "Routine"

class PrescriptionUpload(BaseModel):
    patient_id: str
    patient_name: str
    doctor_id: str
    doctor_name: str
    uploaded_by: str
    raw_text: str
    image_path: Optional[str] = None

class MedicineConfirmation(BaseModel):
    given_by: str
    notes: str = ""

class DoctorStatusUpdate(BaseModel):
    status: str
    location: str = ""
    on_leave_until: Optional[str] = None
    leave_reason: str = ""

class PatientTracking(BaseModel):
    patient_id: str
    patient_name: str
    bed_id: str
    ward: str
    primary_doctor_id: str
    primary_doctor_name: str
    criticality_level: int = 3
    next_visit: Optional[str] = None

class CriticalityUpdate(BaseModel):
    criticality_level: int
    condition: str = ""
    vitals: str = ""

class AlertAcknowledge(BaseModel):
    response: str = ""
    coming_eta: Optional[int] = None

# ============== DASHBOARD ENDPOINTS ==============
@app.get("/")
def root():
    """Health check and welcome message"""
    return {
        "message": "🏥 VitalFlow AI - Hospital Command Center",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/api/dashboard",
            "patients": "/api/patients",
            "beds": "/api/beds",
            "staff": "/api/staff",
            "alerts": "/api/alerts",
            "docs": "/docs"
        }
    }

@app.get("/api/dashboard")
def get_dashboard():
    """Get complete dashboard data"""
    stats = hospital_state.get_stats()
    triage_summary = triage_engine.get_triage_summary()
    staff_summary = staff_manager.get_staff_status_summary()
    alerts = triage_engine.get_critical_alerts()
    queue = triage_engine.get_patient_queue()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "hospital_stats": stats,
        "triage_summary": triage_summary,
        "staff_summary": staff_summary,
        "critical_alerts": alerts[:5],
        "patient_queue": queue[:10],
        "recent_decisions": hospital_state.get_recent_decisions(5)
    }

# ============== PATIENT ENDPOINTS ==============
@app.get("/api/patients")
def get_patients():
    """Get all patients"""
    patients = []
    for p in hospital_state.patients.values():
        patients.append({
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "status": get_enum_value(p.status),
            "spo2": p.spo2,
            "heart_rate": p.heart_rate,
            "bed_id": p.bed_id,
            "doctor_id": p.assigned_doctor_id,
            "nurse_id": p.assigned_nurse_id,
            "priority": triage_engine.calculate_priority(p),
            "diagnosis": p.diagnosis
        })
    return {"patients": patients, "count": len(patients)}

@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: str):
    """Get single patient details"""
    patient = hospital_state.patients.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get medicine recommendations
    recs = medicine_ai.get_preparation_checklist(patient)
    
    return {
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "status": get_enum_value(patient.status),
            "spo2": patient.spo2,
            "heart_rate": patient.heart_rate,
            "blood_pressure": patient.blood_pressure,
            "temperature": patient.temperature,
            "bed_id": patient.bed_id,
            "diagnosis": patient.diagnosis,
            "priority": triage_engine.calculate_priority(patient)
        },
        "recommendations": recs
    }

@app.post("/api/patients")
def create_patient(data: PatientCreate):
    """Admit a new patient"""
    # Generate ID
    patient_id = f"P-{datetime.now().strftime('%H%M%S')}"
    
    # Map status string to enum
    status_map = {
        "Critical": PatientStatus.CRITICAL,
        "Serious": PatientStatus.SERIOUS,
        "Stable": PatientStatus.STABLE,
        "Recovering": PatientStatus.RECOVERING
    }
    status = status_map.get(data.status, PatientStatus.STABLE)
    
    patient = Patient(
        id=patient_id,
        name=data.name,
        age=data.age,
        gender=data.gender,
        diagnosis=data.diagnosis,
        status=status,
        spo2=data.spo2,
        heart_rate=data.heart_rate,
        blood_pressure=data.blood_pressure,
        temperature=data.temperature
    )
    
    # Process through triage
    result = triage_engine.process_incoming_patient(patient)
    
    return {
        "success": True,
        "patient_id": patient_id,
        "result": result
    }

@app.put("/api/patients/{patient_id}/vitals")
def update_vitals(patient_id: str, data: VitalsUpdate):
    """Update patient vitals"""
    result = triage_engine.update_patient_vitals(
        patient_id,
        spo2=data.spo2,
        heart_rate=data.heart_rate,
        blood_pressure=data.blood_pressure,
        temperature=data.temperature
    )
    return result

@app.post("/api/patients/{patient_id}/discharge")
def discharge_patient(patient_id: str):
    """Discharge a patient"""
    result = triage_engine.discharge_patient(patient_id)
    return result

# ============== BED ENDPOINTS ==============
@app.get("/api/beds")
def get_beds():
    """Get all beds with status"""
    beds = []
    for b in hospital_state.beds.values():
        patient_name = None
        if b.patient_id:
            patient = hospital_state.patients.get(b.patient_id)
            patient_name = patient.name if patient else None
        
        beds.append({
            "id": b.id,
            "type": get_enum_value(b.bed_type),
            "ward": b.ward,
            "floor": b.floor,
            "is_occupied": b.is_occupied,
            "patient_id": b.patient_id,
            "patient_name": patient_name
        })
    return {"beds": beds, "occupancy": bed_manager.get_bed_occupancy()}

@app.get("/api/beds/available")
def get_available_beds(bed_type: Optional[str] = None):
    """Get available beds, optionally filtered by type"""
    if bed_type:
        type_map = {"ICU": BedType.ICU, "Emergency": BedType.EMERGENCY, "General": BedType.GENERAL}
        bt = type_map.get(bed_type)
        if bt:
            beds = bed_manager.get_available_beds(bt)
        else:
            beds = []
    else:
        beds = []
        for bt in BedType:
            beds.extend(bed_manager.get_available_beds(bt))
    
    return {"available_beds": [{"id": b.id, "type": get_enum_value(b.bed_type)} for b in beds]}

# ============== STAFF ENDPOINTS ==============
@app.get("/api/staff")
def get_staff():
    """Get all staff members"""
    staff_list = []
    for s in hospital_state.staff.values():
        hours = staff_manager.get_hours_worked(s.id)
        staff_list.append({
            "id": s.id,
            "name": s.name,
            "role": get_enum_value(s.role),
            "status": get_enum_value(s.status),
            "specialization": s.specialization,
            "hours_worked": round(hours, 1) if hours else 0,
            "is_fatigued": staff_manager.is_fatigued(s.id),
            "patient_count": len(s.current_patient_ids)
        })
    return {"staff": staff_list, "summary": staff_manager.get_staff_summary()}

@app.post("/api/staff")
def create_staff(data: StaffCreate):
    """Add new staff member"""
    staff_id = f"S-{datetime.now().strftime('%H%M%S')}"
    
    role_map = {
        "Doctor": StaffRole.DOCTOR,
        "Nurse": StaffRole.NURSE,
        "Wardboy": StaffRole.WARDBOY,
        "Driver": StaffRole.DRIVER
    }
    role = role_map.get(data.role, StaffRole.NURSE)
    
    staff = Staff(
        id=staff_id,
        name=data.name,
        role=role,
        specialization=data.specialization,
        phone=data.phone
    )
    
    hospital_state.add_staff(staff)
    staff_manager.punch_in(staff_id)
    
    return {"success": True, "staff_id": staff_id}

@app.post("/api/staff/{staff_id}/punch-in")
def punch_in(staff_id: str):
    """Staff punch in"""
    success = staff_manager.punch_in(staff_id)
    if not success:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"success": True, "message": f"Staff {staff_id} punched in"}

@app.post("/api/staff/{staff_id}/punch-out")
def punch_out(staff_id: str):
    """Staff punch out"""
    success = staff_manager.punch_out(staff_id)
    if not success:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"success": True, "message": f"Staff {staff_id} punched out"}

# ============== ALERTS ENDPOINTS ==============
@app.get("/api/alerts")
def get_alerts():
    """Get all critical alerts"""
    alerts = triage_engine.get_critical_alerts()
    return {"alerts": alerts, "count": len(alerts)}

@app.get("/api/alerts/voice/{alert_type}")
def get_voice_alert(alert_type: str, bed_id: str = "BED-01", spo2: int = 85):
    """Get voice alert text for a specific alert type"""
    text = voice_service.get_alert_text(alert_type.upper(), bed_id=bed_id, spo2=spo2)
    return {"alert_type": alert_type, "text": text}

# ============== AI ENDPOINTS ==============
@app.get("/api/ai/recommendations/{patient_id}")
def get_ai_recommendations(patient_id: str):
    """Get AI-powered medicine recommendations for a patient"""
    patient = hospital_state.patients.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    recs = medicine_ai.get_preparation_checklist(patient)
    return {"patient_id": patient_id, "recommendations": recs}

# ============== DECISIONS LOG ==============
@app.get("/api/decisions")
def get_decisions(limit: int = 20):
    """Get recent automated decisions"""
    decisions = hospital_state.get_recent_decisions(limit)
    return {"decisions": decisions, "count": len(decisions)}

# ============== TETRIS SWAP ==============
@app.post("/api/tetris/swap")
def execute_tetris_swap(patient_id: str):
    """Manually trigger Tetris swap for a patient"""
    patient = hospital_state.patients.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    success, message = bed_manager.execute_swap(patient)
    return {"success": success, "message": message}

# ============== INIT DATA ==============
@app.post("/api/init")
def initialize_demo_data():
    """Initialize with demo data"""
    hospital_state.clear_all()
    
    # Add beds
    beds_config = [
        ("ICU-01", BedType.ICU), ("ICU-02", BedType.ICU), ("ICU-03", BedType.ICU),
        ("ER-01", BedType.EMERGENCY), ("ER-02", BedType.EMERGENCY),
        ("GEN-01", BedType.GENERAL), ("GEN-02", BedType.GENERAL), 
        ("GEN-03", BedType.GENERAL), ("GEN-04", BedType.GENERAL),
    ]
    for bed_id, bed_type in beds_config:
        bed = Bed(id=bed_id, bed_type=bed_type, ward=f"{get_enum_value(bed_type)} Ward", floor=1)
        hospital_state.add_bed(bed)
    
    # Add staff
    staff_data = [
        ("D001", "Dr. Sharma", StaffRole.DOCTOR, "Cardiology"),
        ("D002", "Dr. Patel", StaffRole.DOCTOR, "Emergency"),
        ("D003", "Dr. Kumar", StaffRole.DOCTOR, "Pulmonology"),
        ("N001", "Nurse Priya", StaffRole.NURSE, ""),
        ("N002", "Nurse Anita", StaffRole.NURSE, ""),
    ]
    for sid, name, role, spec in staff_data:
        s = Staff(id=sid, name=name, role=role, specialization=spec)
        hospital_state.add_staff(s)
        staff_manager.punch_in(sid)
    
    # Add sample patients
    patients_data = [
        ("P001", "Ramesh Kumar", 58, PatientStatus.CRITICAL, 82.0, 150, "Acute MI"),
        ("P002", "Priya Singh", 35, PatientStatus.SERIOUS, 89.0, 115, "Pneumonia"),
        ("P003", "Amit Verma", 45, PatientStatus.STABLE, 96.0, 78, "Post-surgery"),
    ]
    for pid, name, age, status, spo2, hr, diag in patients_data:
        p = Patient(id=pid, name=name, age=age, status=status, spo2=spo2, heart_rate=hr, diagnosis=diag)
        triage_engine.process_incoming_patient(p)
    
    return {
        "success": True,
        "message": "Demo data initialized",
        "beds": len(hospital_state.beds),
        "staff": len(hospital_state.staff),
        "patients": len(hospital_state.patients)
    }

# ============== EMERGENCY PROTOCOLS ==============
@app.get("/api/protocols/{emergency_type}")
def get_protocol(emergency_type: str):
    """Get emergency protocol for a specific condition"""
    protocol = protocol_engine.get_protocol_by_name(emergency_type)
    if not protocol:
        # Try to match partial
        available = protocol_engine.list_protocols()
        raise HTTPException(status_code=404, detail=f"Protocol not found. Available: {available}")
    return {"protocol": protocol}

@app.get("/api/protocols")
def list_protocols():
    """List all available emergency protocols"""
    return {"protocols": protocol_engine.list_protocols()}

@app.get("/api/protocols/for-patient/{patient_id}")
def get_protocol_for_patient(patient_id: str):
    """Get recommended protocol based on patient diagnosis"""
    patient = hospital_state.patients.get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    protocol = protocol_engine.get_protocol_for_patient(patient)
    return {
        "patient_id": patient_id,
        "diagnosis": patient.diagnosis,
        "protocol": protocol
    }

# ============== AMBULANCE MANAGEMENT ==============
@app.get("/api/ambulances")
def get_ambulances():
    """Get all tracked ambulances"""
    ambulances = ambulance_manager.get_active_ambulances()
    return {"ambulances": ambulances, "count": len(ambulances)}

@app.post("/api/ambulances/register")
def register_ambulance(data: AmbulanceRegister):
    """Register incoming ambulance"""
    patient_info = {
        "name": data.patient_name,
        "age": data.patient_age,
        "condition": data.condition,
        "severity": data.severity,
        "contact": data.contact,
        "pickup_location": data.location
    }
    
    result = ambulance_manager.register_ambulance(
        ambulance_id=data.ambulance_id,
        patient_info=patient_info,
        eta_minutes=data.eta_minutes
    )
    
    return {
        "success": True,
        "ambulance_id": result.ambulance_id,
        "message": f"Ambulance {data.ambulance_id} registered successfully",
        "eta_minutes": result.eta_minutes,
        "pre_clearance_at_minutes": ambulance_manager.PRE_CLEARANCE_THRESHOLD_MINUTES,
        "status": result.status.value
    }

@app.put("/api/ambulances/{ambulance_id}/eta")
def update_ambulance_eta(ambulance_id: str, eta_minutes: int):
    """Update ambulance ETA"""
    result = ambulance_manager.update_eta(ambulance_id, eta_minutes)
    return result

@app.get("/api/ambulances/{ambulance_id}")
def get_ambulance(ambulance_id: str):
    """Get ambulance details including pre-clearance status"""
    tracking = ambulance_manager.get_ambulance_tracking(ambulance_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Ambulance not found")
    return tracking

@app.get("/api/ambulances/diversion-check")
def check_diversion():
    """Check if incoming ambulances should be diverted"""
    result = ambulance_manager.recommend_diversion()
    return result

# ============== BILLING ==============
@app.get("/api/billing/{patient_id}")
def get_patient_bill(patient_id: str):
    """Get current bill for a patient"""
    bill = billing_agent.get_current_bill(patient_id)
    if not bill:
        # Create new bill if doesn't exist
        patient = hospital_state.patients.get(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        from backend.core_logic.billing_agent import InsuranceType
        billing_agent.start_billing(patient_id, InsuranceType.NONE)
        bill = billing_agent.get_current_bill(patient_id)
    return bill

@app.post("/api/billing/{patient_id}/medicine")
def add_medicine_to_bill(patient_id: str, medicine_name: str, quantity: int = 1):
    """Add medicine to patient bill"""
    result = billing_agent.add_medicine(patient_id, medicine_name, quantity)
    return result

@app.post("/api/billing/{patient_id}/procedure")
def add_procedure_to_bill(patient_id: str, procedure_name: str):
    """Add procedure to patient bill"""
    result = billing_agent.add_procedure(patient_id, procedure_name)
    return result

@app.post("/api/billing/{patient_id}/bed-charge")
def add_bed_charge(patient_id: str, bed_type: str, days: float = 1.0):
    """Add bed charges to bill"""
    from shared.models import BedType as BT
    bed_type_map = {"icu": BT.ICU, "emergency": BT.EMERGENCY, "general": BT.GENERAL}
    bt = bed_type_map.get(bed_type.lower(), BT.GENERAL)
    result = billing_agent.add_bed_charges(patient_id, bt, days)
    return result

@app.post("/api/billing/{patient_id}/apply-insurance")
def apply_insurance(patient_id: str, insurance_type: str):
    """Apply insurance scheme to bill"""
    from backend.core_logic.billing_agent import InsuranceType
    insurance_map = {
        "ayushman": InsuranceType.AYUSHMAN_BHARAT,
        "ayushman_bharat": InsuranceType.AYUSHMAN_BHARAT,
        "esi": InsuranceType.ESI,
        "cghs": InsuranceType.CGHS,
        "private": InsuranceType.PRIVATE,
        "none": InsuranceType.NONE
    }
    ins = insurance_map.get(insurance_type.lower(), InsuranceType.NONE)
    result = billing_agent.apply_insurance_scheme(patient_id, ins)
    return result

@app.post("/api/billing/{patient_id}/finalize")
def finalize_bill(patient_id: str):
    """Finalize and generate itemized bill"""
    bill = billing_agent.finalize_bill(patient_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

@app.get("/api/billing/price-list")
def get_price_list():
    """Get medicine and procedure price list"""
    return {"price_list": billing_agent.PRICE_LIST}

# ============== CCTV / FALL DETECTION ==============
@app.get("/api/cctv/zones")
def get_cctv_zones():
    """Get all monitored CCTV zones"""
    return {"zones": fall_detector.get_zone_status()}

@app.get("/api/cctv/alerts")
def get_cctv_alerts():
    """Get active CCTV alerts"""
    return {"alerts": fall_detector.get_active_alerts()}

@app.get("/api/cctv/alerts/{alert_id}")
def get_cctv_alert(alert_id: str):
    """Get specific CCTV alert details"""
    alert = fall_detector.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert": alert}

@app.post("/api/cctv/alerts/{alert_id}/verify")
def verify_cctv_alert(alert_id: str, data: AlertVerify):
    """Verify a CCTV alert (admin confirms or denies)"""
    result = fall_detector.verify_alert(
        alert_id=alert_id,
        verified_by=data.verified_by,
        is_emergency=data.is_emergency,
        notes=data.notes
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/cctv/alerts/{alert_id}/assign")
def assign_cctv_response(alert_id: str, nurse_id: str = None, doctor_id: str = None):
    """Assign staff to respond to verified CCTV alert"""
    result = fall_detector.assign_response(alert_id, nurse_id, doctor_id)
    return result

@app.post("/api/cctv/alerts/{alert_id}/resolve")
def resolve_cctv_alert(alert_id: str, notes: str, patient_id: str = None):
    """Resolve a CCTV alert"""
    result = fall_detector.resolve_alert(alert_id, notes, patient_id)
    return result

@app.post("/api/cctv/simulate/fall")
def simulate_fall(zone_id: str = None):
    """Simulate a fall event for testing"""
    result = fall_detector.simulate_fall(zone_id)
    return result

@app.post("/api/cctv/simulate/immobility")
def simulate_immobility(zone_id: str = None):
    """Simulate an immobility event for testing"""
    result = fall_detector.simulate_immobility(zone_id)
    return result

# ============== VITALFLOW AGENT ==============
@app.get("/api/agent/status")
def get_agent_status():
    """Get VitalFlow agent status"""
    return vitalflow_agent.get_status()

@app.post("/api/agent/start")
def start_agent():
    """Start the autonomous VitalFlow agent"""
    vitalflow_agent.start()
    return {"success": True, "message": "VitalFlow Agent started", "status": "running"}

@app.post("/api/agent/stop")
def stop_agent():
    """Stop the VitalFlow agent"""
    vitalflow_agent.stop()
    return {"success": True, "message": "VitalFlow Agent stopped", "status": "stopped"}

@app.post("/api/agent/cycle")
def run_agent_cycle():
    """Manually trigger one agent decision cycle"""
    decisions = vitalflow_agent.run_cycle()
    return {
        "decisions_made": len(decisions),
        "decisions": [d.to_dict() if hasattr(d, 'to_dict') else str(d) for d in decisions]
    }

@app.get("/api/agent/pending-approvals")
def get_pending_approvals():
    """Get decisions awaiting human approval"""
    pending = vitalflow_agent.get_pending_approvals()
    return {"pending": pending, "count": len(pending)}

@app.post("/api/agent/approve")
def approve_decision(data: ApprovalRequest):
    """Approve or reject a pending decision"""
    if data.approve:
        result = vitalflow_agent.approve_decision(data.decision_id, data.approved_by, data.notes)
    else:
        result = vitalflow_agent.reject_decision(data.decision_id, data.approved_by, data.notes)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/agent/history")
def get_agent_history(limit: int = 50):
    """Get agent decision history"""
    return {"history": vitalflow_agent.decision_history[-limit:]}


# ============== STOCK MANAGEMENT ENDPOINTS ==============
@app.get("/api/stock")
def get_stock_summary():
    """Get medicine stock summary"""
    return stock_manager.get_stock_summary()

@app.get("/api/stock/medicines")
def get_all_medicines():
    """Get all medicines with stock info"""
    return {"medicines": stock_manager.get_all_medicines()}

@app.get("/api/stock/medicines/{medicine_id}")
def get_medicine_stock(medicine_id: str):
    """Get stock for specific medicine"""
    stock = stock_manager.get_medicine_stock(medicine_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return stock

@app.post("/api/stock/usage")
def record_medicine_usage(data: MedicineUsage):
    """Record medicine usage (by nurse/doctor)"""
    result = stock_manager.record_usage(
        medicine_id=data.medicine_id,
        quantity=data.quantity,
        patient_id=data.patient_id,
        recorded_by=data.recorded_by,
        notes=data.notes
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/stock/orders")
def get_stock_orders():
    """Get all medicine orders"""
    return {"orders": stock_manager.get_all_orders()}

@app.get("/api/stock/orders/pending")
def get_pending_orders():
    """Get orders pending verification"""
    return {"orders": stock_manager.get_pending_orders()}

@app.post("/api/stock/orders/{order_id}/verify")
def verify_order(order_id: str, data: OrderVerification):
    """Verify and approve/reject medicine order (Human-in-the-loop)"""
    result = stock_manager.verify_and_place_order(
        order_id=order_id,
        verified_by=data.verified_by,
        approve=data.approve,
        notes=data.notes,
        modified_quantities=data.modified_quantities
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/stock/orders/{order_id}/place")
def place_order(order_id: str, placed_by: str):
    """Place verified order with supplier"""
    result = stock_manager.place_order_with_supplier(order_id, placed_by)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/stock/orders/{order_id}/receive")
def receive_delivery(order_id: str, received_by: str):
    """Mark order as delivered and update stock"""
    result = stock_manager.receive_delivery(order_id, received_by)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/stock/usage-history")
def get_usage_history(medicine_id: Optional[str] = None, days: int = 7):
    """Get medicine usage history"""
    return {"history": stock_manager.get_usage_history(medicine_id, days)}

@app.get("/api/stock/search")
def search_medicines(query: str):
    """Search medicines by name or category"""
    return {"results": stock_manager.search_medicine(query)}


# ============== PATIENT REPORT ENDPOINTS ==============
@app.post("/api/reports/{patient_id}/initialize")
def initialize_patient_report(patient_id: str, patient_name: str):
    """Initialize daily report for patient"""
    report = patient_report_system.initialize_patient_report(
        patient_id=patient_id,
        patient_name=patient_name,
        admission_date=datetime.now()
    )
    return {"success": True, "report": report.to_dict()}

@app.post("/api/reports/{patient_id}/vitals")
def record_patient_vitals(patient_id: str, data: VitalsRecord):
    """Record patient vitals (by nurse/doctor)"""
    result = patient_report_system.record_vitals(
        patient_id=patient_id,
        recorded_by=data.recorded_by,
        spo2=data.spo2,
        heart_rate=data.heart_rate,
        blood_pressure=data.blood_pressure,
        temperature=data.temperature,
        respiratory_rate=data.respiratory_rate,
        notes=data.notes
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/reports/{patient_id}/consultation")
def add_consultation(patient_id: str, data: ConsultationNote):
    """Add doctor consultation note"""
    next_visit = None
    if data.next_visit:
        next_visit = datetime.fromisoformat(data.next_visit)
    
    result = patient_report_system.add_consultation_note(
        patient_id=patient_id,
        doctor_id=data.doctor_id,
        doctor_name=data.doctor_name,
        findings=data.findings,
        diagnosis=data.diagnosis,
        treatment_plan=data.treatment_plan,
        next_visit=next_visit,
        priority=data.priority
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/reports/{patient_id}")
def get_patient_report(patient_id: str):
    """Get patient daily report"""
    report = patient_report_system.get_patient_report(patient_id)
    if not report:
        raise HTTPException(status_code=404, detail="Patient report not found")
    return report

@app.get("/api/reports/{patient_id}/patient-view")
def get_patient_view(patient_id: str):
    """Get patient-friendly view of their report"""
    view = patient_report_system.get_patient_view(patient_id)
    if not view:
        raise HTTPException(status_code=404, detail="Patient report not found")
    return view

@app.get("/api/reports/{patient_id}/summary")
def get_daily_summary(patient_id: str):
    """Get daily summary for shift handover"""
    summary = patient_report_system.get_daily_summary(patient_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Patient report not found")
    return summary

@app.post("/api/reports/{patient_id}/meal/{meal_id}")
def update_meal_status(patient_id: str, meal_id: str, status: str, served_by: Optional[str] = None):
    """Update meal status"""
    from backend.core_logic.patient_report import MealStatus
    meal_status = MealStatus(status)
    result = patient_report_system.update_meal_status(patient_id, meal_id, meal_status, served_by)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/reports/{patient_id}/medicines/upcoming")
def get_upcoming_medicines(patient_id: str, hours: int = 2):
    """Get medicines due in next N hours"""
    return {"medicines": patient_report_system.get_upcoming_medicines(patient_id, hours)}


# ============== PRESCRIPTION SCANNER ENDPOINTS ==============
@app.post("/api/prescriptions/upload")
def upload_prescription(data: PrescriptionUpload):
    """Upload prescription for AI scanning"""
    result = prescription_scanner.upload_prescription(
        patient_id=data.patient_id,
        patient_name=data.patient_name,
        doctor_id=data.doctor_id,
        doctor_name=data.doctor_name,
        uploaded_by=data.uploaded_by,
        raw_text=data.raw_text,
        image_path=data.image_path
    )
    return result

@app.get("/api/prescriptions/{prescription_id}")
def get_prescription(prescription_id: str):
    """Get prescription details"""
    prescription = prescription_scanner.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription

@app.get("/api/prescriptions/{prescription_id}/details")
def get_medicine_details(prescription_id: str):
    """Get detailed AI-generated medicine information"""
    result = prescription_scanner.get_medicine_details(prescription_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result

@app.post("/api/prescriptions/{prescription_id}/verify")
def verify_prescription(prescription_id: str, verified_by: str, approved: bool, notes: str = ""):
    """Verify AI-parsed prescription"""
    result = prescription_scanner.verify_prescription(prescription_id, verified_by, approved, notes)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/prescriptions/patient/{patient_id}")
def get_patient_prescriptions(patient_id: str):
    """Get all prescriptions for a patient"""
    return {"prescriptions": prescription_scanner.get_patient_prescriptions(patient_id)}

@app.get("/api/prescriptions/alerts/pending")
def get_pending_medicine_alerts(hours: int = 1):
    """Get medicine alerts due within next N hours"""
    return {"alerts": prescription_scanner.get_pending_alerts(hours)}

@app.post("/api/prescriptions/alerts/{alert_id}/send")
def send_medicine_alert(alert_id: str):
    """Send medicine alert to nurse"""
    result = prescription_scanner.send_alert(alert_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/prescriptions/alerts/{alert_id}/acknowledge")
def acknowledge_medicine_alert(alert_id: str, acknowledged_by: str):
    """Nurse acknowledges medicine alert"""
    result = prescription_scanner.acknowledge_alert(alert_id, acknowledged_by)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/prescriptions/alerts/{alert_id}/confirm")
def confirm_medicine_given(alert_id: str, data: MedicineConfirmation):
    """Confirm medicine was given to patient"""
    result = prescription_scanner.confirm_medicine_given(alert_id, data.given_by, data.notes)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/prescriptions/alerts/{alert_id}/missed")
def mark_medicine_missed(alert_id: str, reason: str = ""):
    """Mark medicine as missed"""
    result = prescription_scanner.mark_medicine_missed(alert_id, reason)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/prescriptions/patient/{patient_id}/history")
def get_medicine_history(patient_id: str):
    """Get medicine administration history for patient"""
    return prescription_scanner.get_patient_medicine_history(patient_id)

@app.post("/api/prescriptions/alerts/check")
def check_due_alerts():
    """Check and send alerts for medicines due in 1 hour"""
    alerts = prescription_scanner.check_and_send_due_alerts()
    return {"sent_alerts": alerts, "count": len(alerts)}


# ============== DOCTOR ALERT ENDPOINTS ==============
@app.get("/api/doctor-alerts/doctors")
def get_doctors_status():
    """Get all doctors' status summary"""
    return doctor_alert_system.get_doctor_status_summary()

@app.post("/api/doctor-alerts/doctors/{doctor_id}/status")
def update_doctor_status(doctor_id: str, data: DoctorStatusUpdate):
    """Update doctor availability status"""
    on_leave_until = None
    if data.on_leave_until:
        on_leave_until = datetime.fromisoformat(data.on_leave_until)
    
    status = DoctorStatus(data.status)
    result = doctor_alert_system.update_doctor_status(
        doctor_id=doctor_id,
        status=status,
        location=data.location,
        on_leave_until=on_leave_until,
        leave_reason=data.leave_reason
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/doctor-alerts/track-patient")
def track_patient(data: PatientTracking):
    """Start tracking patient for critical alerts"""
    next_visit = None
    if data.next_visit:
        next_visit = datetime.fromisoformat(data.next_visit)
    
    tracking = doctor_alert_system.track_patient(
        patient_id=data.patient_id,
        patient_name=data.patient_name,
        bed_id=data.bed_id,
        ward=data.ward,
        primary_doctor_id=data.primary_doctor_id,
        primary_doctor_name=data.primary_doctor_name,
        criticality_level=data.criticality_level,
        next_visit=next_visit
    )
    return {"success": True, "tracking": tracking.to_dict()}

@app.post("/api/doctor-alerts/patients/{patient_id}/criticality")
def update_patient_criticality(patient_id: str, data: CriticalityUpdate):
    """Update patient criticality (triggers alerts if critical)"""
    result = doctor_alert_system.update_patient_criticality(
        patient_id=patient_id,
        criticality_level=data.criticality_level,
        condition=data.condition,
        vitals=data.vitals
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/doctor-alerts/alerts")
def get_doctor_alerts(doctor_id: Optional[str] = None):
    """Get pending alerts for doctors"""
    return {"alerts": doctor_alert_system.get_pending_alerts(doctor_id)}

@app.post("/api/doctor-alerts/alerts/{alert_id}/acknowledge")
def acknowledge_doctor_alert(alert_id: str, doctor_id: str, data: AlertAcknowledge):
    """Doctor acknowledges the alert"""
    result = doctor_alert_system.acknowledge_alert(
        alert_id=alert_id,
        doctor_id=doctor_id,
        response=data.response,
        coming_eta=data.coming_eta
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/doctor-alerts/alerts/{alert_id}/responding")
def mark_doctor_responding(alert_id: str):
    """Mark that doctor is on the way"""
    result = doctor_alert_system.mark_doctor_responding(alert_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/doctor-alerts/alerts/{alert_id}/resolve")
def resolve_doctor_alert(alert_id: str, notes: str = ""):
    """Resolve the alert"""
    result = doctor_alert_system.resolve_alert(alert_id, notes)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.post("/api/doctor-alerts/alerts/{alert_id}/escalate")
def escalate_alert(alert_id: str):
    """Escalate alert to backup doctor"""
    result = doctor_alert_system.escalate_alert(alert_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/doctor-alerts/critical-patients")
def get_critical_patients():
    """Get all critical patients being tracked"""
    return {"patients": doctor_alert_system.get_critical_patients()}

@app.get("/api/doctor-alerts/history")
def get_alert_history(patient_id: Optional[str] = None, doctor_id: Optional[str] = None):
    """Get alert history"""
    return {"history": doctor_alert_system.get_alert_history(patient_id, doctor_id)}

@app.post("/api/doctor-alerts/check-escalations")
def check_escalations():
    """Check and escalate pending alerts that timed out"""
    escalated = doctor_alert_system.check_and_escalate_pending_alerts()
    return {"escalated": escalated, "count": len(escalated)}


# ============== RUN ==============
if __name__ == "__main__":
    import uvicorn
    print("\n🏥 Starting VitalFlow AI Backend Server...")
    print("📍 API Docs: http://localhost:8000/docs")
    print("📍 Dashboard: http://localhost:8000/api/dashboard\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
