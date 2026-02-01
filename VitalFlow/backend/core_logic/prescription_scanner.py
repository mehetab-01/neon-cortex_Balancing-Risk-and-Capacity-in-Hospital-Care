"""
Prescription Scanner for VitalFlow AI.
AI scans prescriptions, provides medicine details, generates 1-hour alerts,
and tracks medicine administration confirmation by nurses.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_enum_value
from .state import hospital_state


class PrescriptionStatus(str, Enum):
    """Prescription processing status"""
    UPLOADED = "Uploaded"
    SCANNING = "Scanning"
    PARSED = "Parsed"
    VERIFIED = "Verified"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class MedicineAlertStatus(str, Enum):
    """Medicine alert status"""
    PENDING = "Pending"
    ALERT_SENT = "Alert Sent"
    ACKNOWLEDGED = "Acknowledged"
    GIVEN = "Given"
    MISSED = "Missed"


@dataclass
class MedicineInfo:
    """Detailed medicine information from AI scan"""
    medicine_name: str
    generic_name: str
    dosage: str
    frequency: str  # OD, BD, TDS, QID, SOS
    duration_days: int
    route: str  # Oral, IV, IM, Topical
    timing: str  # Before food, After food, With food
    
    # AI-generated details
    purpose: str = ""
    mechanism: str = ""
    side_effects: List[str] = field(default_factory=list)
    precautions: List[str] = field(default_factory=list)
    interactions: List[str] = field(default_factory=list)
    
    # Schedule
    scheduled_times: List[str] = field(default_factory=list)  # ["08:00", "14:00", "20:00"]
    
    def to_dict(self) -> Dict:
        return {
            "medicine_name": self.medicine_name,
            "generic_name": self.generic_name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "duration_days": self.duration_days,
            "route": self.route,
            "timing": self.timing,
            "purpose": self.purpose,
            "mechanism": self.mechanism,
            "side_effects": self.side_effects,
            "precautions": self.precautions,
            "interactions": self.interactions,
            "scheduled_times": self.scheduled_times
        }


@dataclass
class Prescription:
    """Complete prescription record"""
    prescription_id: str
    patient_id: str
    patient_name: str
    doctor_id: str
    doctor_name: str
    
    # Upload info
    uploaded_at: datetime
    uploaded_by: str
    image_path: Optional[str] = None
    raw_text: str = ""
    
    # Parsed data
    status: PrescriptionStatus = PrescriptionStatus.UPLOADED
    medicines: List[MedicineInfo] = field(default_factory=list)
    diagnosis: str = ""
    notes: str = ""
    
    # Verification
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    
    # Validity
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "prescription_id": self.prescription_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "uploaded_at": self.uploaded_at.isoformat(),
            "uploaded_by": self.uploaded_by,
            "status": get_enum_value(self.status),
            "medicines": [m.to_dict() for m in self.medicines],
            "diagnosis": self.diagnosis,
            "notes": self.notes,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "valid_from": self.valid_from.isoformat(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None
        }


@dataclass
class MedicineAlert:
    """Alert for medicine administration"""
    alert_id: str
    prescription_id: str
    patient_id: str
    patient_name: str
    medicine_name: str
    dosage: str
    scheduled_time: datetime
    
    # Alert tracking
    status: MedicineAlertStatus = MedicineAlertStatus.PENDING
    alert_sent_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    # Administration
    given_by: Optional[str] = None
    given_at: Optional[datetime] = None
    notes: str = ""
    
    # Location
    bed_id: str = ""
    ward: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "prescription_id": self.prescription_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "medicine_name": self.medicine_name,
            "dosage": self.dosage,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status": get_enum_value(self.status),
            "alert_sent_at": self.alert_sent_at.isoformat() if self.alert_sent_at else None,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "given_by": self.given_by,
            "given_at": self.given_at.isoformat() if self.given_at else None,
            "notes": self.notes,
            "bed_id": self.bed_id,
            "ward": self.ward
        }


class PrescriptionScanner:
    """
    Prescription Scanner for VitalFlow AI.
    
    Features:
    - AI scans prescription images/text
    - Provides detailed medicine information
    - Generates 1-hour alerts before medicine time
    - Tracks nurse confirmation of medicine administration
    - Maintains complete administration history
    """
    
    def __init__(self):
        self.prescriptions: Dict[str, Prescription] = {}
        self.alerts: Dict[str, MedicineAlert] = {}
        self.prescription_counter = 0
        self.alert_counter = 0
        
        # Medicine database for AI lookup
        self.medicine_database = self._initialize_medicine_db()
        
        # Alert monitoring thread
        self._running = False
        self._alert_thread: Optional[threading.Thread] = None
    
    def _initialize_medicine_db(self) -> Dict[str, Dict]:
        """Initialize medicine information database"""
        return {
            "aspirin": {
                "generic_name": "Acetylsalicylic Acid",
                "purpose": "Blood thinner, pain relief, anti-inflammatory",
                "mechanism": "Inhibits COX enzymes, preventing platelet aggregation and reducing prostaglandin synthesis",
                "side_effects": ["Stomach upset", "Bleeding risk", "Bruising", "Tinnitus at high doses"],
                "precautions": ["Take with food", "Avoid if allergic to NSAIDs", "Monitor for bleeding"],
                "interactions": ["Blood thinners", "Ibuprofen", "Alcohol"]
            },
            "clopidogrel": {
                "generic_name": "Clopidogrel Bisulfate",
                "purpose": "Prevents blood clots in heart/vascular conditions",
                "mechanism": "Inhibits ADP-induced platelet aggregation by blocking P2Y12 receptor",
                "side_effects": ["Bleeding", "Bruising", "Stomach pain", "Diarrhea"],
                "precautions": ["Do not stop suddenly", "Inform surgeon before procedures"],
                "interactions": ["Omeprazole", "Aspirin", "Warfarin"]
            },
            "metoprolol": {
                "generic_name": "Metoprolol Tartrate/Succinate",
                "purpose": "Controls heart rate and blood pressure",
                "mechanism": "Beta-blocker that reduces heart rate and blood pressure by blocking beta-1 receptors",
                "side_effects": ["Fatigue", "Dizziness", "Cold hands/feet", "Slow heartbeat"],
                "precautions": ["Do not stop suddenly", "Monitor heart rate", "Take with food"],
                "interactions": ["Calcium channel blockers", "Digoxin", "Antidepressants"]
            },
            "amoxicillin": {
                "generic_name": "Amoxicillin Trihydrate",
                "purpose": "Antibiotic for bacterial infections",
                "mechanism": "Inhibits bacterial cell wall synthesis by binding to penicillin-binding proteins",
                "side_effects": ["Diarrhea", "Nausea", "Rash", "Allergic reactions"],
                "precautions": ["Complete full course", "Check for penicillin allergy"],
                "interactions": ["Methotrexate", "Warfarin", "Oral contraceptives"]
            },
            "paracetamol": {
                "generic_name": "Acetaminophen",
                "purpose": "Pain relief and fever reduction",
                "mechanism": "Inhibits prostaglandin synthesis in the central nervous system",
                "side_effects": ["Liver damage at high doses", "Rare allergic reactions"],
                "precautions": ["Max 4g/day", "Avoid alcohol", "Check other medicines for paracetamol"],
                "interactions": ["Warfarin", "Alcohol", "Other paracetamol-containing medicines"]
            },
            "omeprazole": {
                "generic_name": "Omeprazole",
                "purpose": "Reduces stomach acid, treats GERD and ulcers",
                "mechanism": "Proton pump inhibitor that blocks gastric acid secretion",
                "side_effects": ["Headache", "Nausea", "Vitamin B12 deficiency (long-term)"],
                "precautions": ["Take before meals", "Long-term use needs monitoring"],
                "interactions": ["Clopidogrel", "Methotrexate", "Iron supplements"]
            },
            "atorvastatin": {
                "generic_name": "Atorvastatin Calcium",
                "purpose": "Lowers cholesterol and reduces heart disease risk",
                "mechanism": "HMG-CoA reductase inhibitor that blocks cholesterol synthesis in liver",
                "side_effects": ["Muscle pain", "Liver enzyme elevation", "Digestive issues"],
                "precautions": ["Take at bedtime", "Report muscle pain", "Regular liver tests"],
                "interactions": ["Grapefruit", "Fibrates", "Cyclosporine"]
            },
            "insulin": {
                "generic_name": "Insulin (Various types)",
                "purpose": "Controls blood sugar in diabetes",
                "mechanism": "Hormone that enables cells to absorb glucose from bloodstream",
                "side_effects": ["Hypoglycemia", "Weight gain", "Injection site reactions"],
                "precautions": ["Monitor blood sugar", "Rotate injection sites", "Carry glucose"],
                "interactions": ["Beta-blockers", "Alcohol", "Other diabetes medications"]
            },
            "amlodipine": {
                "generic_name": "Amlodipine Besylate",
                "purpose": "Treats high blood pressure and chest pain (angina)",
                "mechanism": "Calcium channel blocker that relaxes blood vessels",
                "side_effects": ["Swelling in ankles", "Dizziness", "Flushing", "Fatigue"],
                "precautions": ["May cause low BP", "Stand up slowly", "Regular BP monitoring"],
                "interactions": ["Simvastatin", "Cyclosporine", "Grapefruit"]
            },
            "prednisolone": {
                "generic_name": "Prednisolone",
                "purpose": "Anti-inflammatory, treats allergies, autoimmune conditions",
                "mechanism": "Corticosteroid that suppresses immune response and inflammation",
                "side_effects": ["Weight gain", "Mood changes", "Increased infection risk", "Blood sugar elevation"],
                "precautions": ["Do not stop suddenly", "Take with food", "Monitor blood sugar"],
                "interactions": ["NSAIDs", "Diabetes medications", "Blood thinners"]
            }
        }
    
    def upload_prescription(self, patient_id: str, patient_name: str,
                            doctor_id: str, doctor_name: str,
                            uploaded_by: str, raw_text: str = "",
                            image_path: Optional[str] = None) -> Dict:
        """Upload a new prescription for scanning"""
        self.prescription_counter += 1
        prescription_id = f"RX-{datetime.now().strftime('%Y%m%d')}-{self.prescription_counter:04d}"
        
        prescription = Prescription(
            prescription_id=prescription_id,
            patient_id=patient_id,
            patient_name=patient_name,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            uploaded_at=datetime.now(),
            uploaded_by=uploaded_by,
            raw_text=raw_text,
            image_path=image_path,
            status=PrescriptionStatus.UPLOADED
        )
        
        self.prescriptions[prescription_id] = prescription
        
        hospital_state.log_decision(
            "PRESCRIPTION_UPLOADED",
            f"📋 Prescription {prescription_id} uploaded for {patient_name} by {uploaded_by}"
        )
        
        # Auto-scan the prescription
        self._scan_prescription(prescription_id)
        
        return {
            "success": True,
            "prescription": prescription.to_dict(),
            "message": "Prescription uploaded and scanning initiated"
        }
    
    def _scan_prescription(self, prescription_id: str):
        """AI scans and parses the prescription"""
        if prescription_id not in self.prescriptions:
            return
        
        prescription = self.prescriptions[prescription_id]
        prescription.status = PrescriptionStatus.SCANNING
        
        # Parse raw text for medicines (simplified parser)
        # In production, this would use OCR + NLP
        medicines = self._parse_prescription_text(prescription.raw_text)
        
        prescription.medicines = medicines
        prescription.status = PrescriptionStatus.PARSED
        
        hospital_state.log_decision(
            "PRESCRIPTION_SCANNED",
            f"🔍 Prescription {prescription_id} scanned. Found {len(medicines)} medicines."
        )
    
    def _parse_prescription_text(self, raw_text: str) -> List[MedicineInfo]:
        """Parse prescription text to extract medicines"""
        medicines = []
        
        # Simple pattern matching (in production, use ML/NLP)
        # Format: MedicineName Dosage Frequency Duration
        # Example: "Aspirin 325mg BD x 7 days"
        
        lines = raw_text.strip().split("\n") if raw_text else []
        
        frequency_map = {
            "OD": (["08:00"], "Once daily"),
            "BD": (["08:00", "20:00"], "Twice daily"),
            "TDS": (["08:00", "14:00", "20:00"], "Three times daily"),
            "QID": (["06:00", "12:00", "18:00", "24:00"], "Four times daily"),
            "SOS": ([], "As needed"),
            "HS": (["22:00"], "At bedtime"),
            "AC": (["07:30", "12:00", "19:00"], "Before meals"),
            "PC": (["09:00", "13:30", "20:30"], "After meals")
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse medicine info
            parts = line.split()
            if len(parts) >= 2:
                medicine_name = parts[0].lower()
                dosage = parts[1] if len(parts) > 1 else ""
                frequency = parts[2].upper() if len(parts) > 2 else "OD"
                duration = 7  # Default 7 days
                
                # Extract duration if present
                for p in parts:
                    match = re.search(r'(\d+)\s*days?', p, re.IGNORECASE)
                    if match:
                        duration = int(match.group(1))
                
                # Get detailed info from database
                db_info = self.medicine_database.get(medicine_name, {})
                times, freq_desc = frequency_map.get(frequency, (["08:00"], "Once daily"))
                
                med_info = MedicineInfo(
                    medicine_name=medicine_name.capitalize(),
                    generic_name=db_info.get("generic_name", medicine_name.capitalize()),
                    dosage=dosage,
                    frequency=frequency,
                    duration_days=duration,
                    route="Oral",
                    timing="After food",
                    purpose=db_info.get("purpose", "As prescribed by doctor"),
                    mechanism=db_info.get("mechanism", ""),
                    side_effects=db_info.get("side_effects", []),
                    precautions=db_info.get("precautions", []),
                    interactions=db_info.get("interactions", []),
                    scheduled_times=times
                )
                medicines.append(med_info)
        
        return medicines
    
    def get_medicine_details(self, prescription_id: str) -> Dict:
        """Get detailed AI-generated medicine information for prescription"""
        if prescription_id not in self.prescriptions:
            return {"success": False, "error": "Prescription not found"}
        
        prescription = self.prescriptions[prescription_id]
        
        detailed_medicines = []
        for med in prescription.medicines:
            detailed = med.to_dict()
            detailed["ai_explanation"] = self._generate_medicine_explanation(med)
            detailed_medicines.append(detailed)
        
        return {
            "success": True,
            "prescription_id": prescription_id,
            "patient_name": prescription.patient_name,
            "doctor_name": prescription.doctor_name,
            "medicines": detailed_medicines
        }
    
    def _generate_medicine_explanation(self, medicine: MedicineInfo) -> str:
        """Generate patient-friendly medicine explanation"""
        explanation = f"""
💊 **{medicine.medicine_name}** ({medicine.generic_name})

📌 **Why prescribed:** {medicine.purpose}

⏰ **How to take:**
- Dose: {medicine.dosage}
- Frequency: {medicine.frequency} ({', '.join(medicine.scheduled_times) if medicine.scheduled_times else 'As directed'})
- Duration: {medicine.duration_days} days
- Timing: {medicine.timing}

⚠️ **Important precautions:**
{chr(10).join('• ' + p for p in medicine.precautions) if medicine.precautions else '• Follow doctor instructions'}

⚡ **Possible side effects:**
{chr(10).join('• ' + s for s in medicine.side_effects) if medicine.side_effects else '• Generally well tolerated'}

🔄 **Drug interactions to watch:**
{chr(10).join('• ' + i for i in medicine.interactions) if medicine.interactions else '• Inform doctor about other medications'}
        """
        return explanation.strip()
    
    def verify_prescription(self, prescription_id: str, verified_by: str,
                            approved: bool, notes: str = "") -> Dict:
        """Medical staff verifies the AI-parsed prescription"""
        if prescription_id not in self.prescriptions:
            return {"success": False, "error": "Prescription not found"}
        
        prescription = self.prescriptions[prescription_id]
        prescription.verified_by = verified_by
        prescription.verified_at = datetime.now()
        prescription.notes = notes
        
        if approved:
            prescription.status = PrescriptionStatus.VERIFIED
            # Generate alerts for all medicines
            self._generate_medicine_alerts(prescription)
            
            hospital_state.log_decision(
                "PRESCRIPTION_VERIFIED",
                f"✅ Prescription {prescription_id} verified by {verified_by}. {len(prescription.medicines)} medicine alerts scheduled."
            )
        else:
            prescription.status = PrescriptionStatus.CANCELLED
            hospital_state.log_decision(
                "PRESCRIPTION_REJECTED",
                f"❌ Prescription {prescription_id} rejected by {verified_by}. Reason: {notes}"
            )
        
        return {"success": True, "prescription": prescription.to_dict()}
    
    def _generate_medicine_alerts(self, prescription: Prescription):
        """Generate medicine administration alerts"""
        now = datetime.now()
        today = now.date()
        
        for med in prescription.medicines:
            for time_str in med.scheduled_times:
                # Generate alerts for each scheduled time for the duration
                for day in range(med.duration_days):
                    schedule_date = today + timedelta(days=day)
                    hour, minute = map(int, time_str.split(":"))
                    scheduled_time = datetime.combine(schedule_date, 
                                                      datetime.min.time().replace(hour=hour, minute=minute))
                    
                    # Skip if already passed
                    if scheduled_time < now:
                        continue
                    
                    self.alert_counter += 1
                    alert = MedicineAlert(
                        alert_id=f"ALERT-{self.alert_counter:06d}",
                        prescription_id=prescription.prescription_id,
                        patient_id=prescription.patient_id,
                        patient_name=prescription.patient_name,
                        medicine_name=med.medicine_name,
                        dosage=med.dosage,
                        scheduled_time=scheduled_time,
                        status=MedicineAlertStatus.PENDING
                    )
                    self.alerts[alert.alert_id] = alert
    
    def get_pending_alerts(self, within_hours: int = 1) -> List[Dict]:
        """Get alerts due within next N hours"""
        now = datetime.now()
        cutoff = now + timedelta(hours=within_hours)
        
        pending = []
        for alert in self.alerts.values():
            if (alert.status == MedicineAlertStatus.PENDING and 
                now <= alert.scheduled_time <= cutoff):
                pending.append(alert.to_dict())
        
        return sorted(pending, key=lambda x: x["scheduled_time"])
    
    def send_alert(self, alert_id: str) -> Dict:
        """Mark alert as sent (trigger notification to nurse)"""
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.status = MedicineAlertStatus.ALERT_SENT
        alert.alert_sent_at = datetime.now()
        
        hospital_state.log_decision(
            "MEDICINE_ALERT_SENT",
            f"🔔 Alert sent: {alert.medicine_name} ({alert.dosage}) for {alert.patient_name} due at {alert.scheduled_time.strftime('%H:%M')}"
        )
        
        return {
            "success": True,
            "alert": alert.to_dict(),
            "message": f"Alert sent for {alert.medicine_name}"
        }
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict:
        """Nurse acknowledges the medicine alert"""
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.status = MedicineAlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        
        hospital_state.log_decision(
            "ALERT_ACKNOWLEDGED",
            f"👍 Alert acknowledged by {acknowledged_by}: {alert.medicine_name} for {alert.patient_name}"
        )
        
        return {"success": True, "alert": alert.to_dict()}
    
    def confirm_medicine_given(self, alert_id: str, given_by: str, notes: str = "") -> Dict:
        """Nurse confirms medicine was given to patient"""
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.status = MedicineAlertStatus.GIVEN
        alert.given_by = given_by
        alert.given_at = datetime.now()
        alert.notes = notes
        
        hospital_state.log_decision(
            "MEDICINE_GIVEN_CONFIRMED",
            f"✅ Medicine confirmed: {alert.medicine_name} ({alert.dosage}) given to {alert.patient_name} by {given_by}"
        )
        
        return {
            "success": True,
            "alert": alert.to_dict(),
            "message": f"Medicine administration confirmed for {alert.patient_name}"
        }
    
    def mark_medicine_missed(self, alert_id: str, reason: str = "") -> Dict:
        """Mark medicine as missed"""
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.status = MedicineAlertStatus.MISSED
        alert.notes = reason
        
        hospital_state.log_decision(
            "MEDICINE_MISSED",
            f"⚠️ Medicine MISSED: {alert.medicine_name} for {alert.patient_name}. Reason: {reason}"
        )
        
        return {"success": True, "alert": alert.to_dict()}
    
    def get_patient_medicine_history(self, patient_id: str) -> Dict:
        """Get medicine administration history for patient"""
        patient_alerts = [a.to_dict() for a in self.alerts.values() 
                         if a.patient_id == patient_id]
        
        given = [a for a in patient_alerts if a["status"] == "Given"]
        missed = [a for a in patient_alerts if a["status"] == "Missed"]
        pending = [a for a in patient_alerts if a["status"] in ["Pending", "Alert Sent", "Acknowledged"]]
        
        return {
            "patient_id": patient_id,
            "total_scheduled": len(patient_alerts),
            "given": len(given),
            "missed": len(missed),
            "pending": len(pending),
            "compliance_rate": (len(given) / len(patient_alerts) * 100) if patient_alerts else 100,
            "history": sorted(patient_alerts, key=lambda x: x["scheduled_time"], reverse=True)
        }
    
    def get_prescription(self, prescription_id: str) -> Optional[Dict]:
        """Get prescription details"""
        if prescription_id in self.prescriptions:
            return self.prescriptions[prescription_id].to_dict()
        return None
    
    def get_patient_prescriptions(self, patient_id: str) -> List[Dict]:
        """Get all prescriptions for a patient"""
        return [p.to_dict() for p in self.prescriptions.values() 
                if p.patient_id == patient_id]
    
    def check_and_send_due_alerts(self) -> List[Dict]:
        """Check for alerts due in 1 hour and send them"""
        due_alerts = self.get_pending_alerts(within_hours=1)
        sent_alerts = []
        
        for alert_dict in due_alerts:
            alert_id = alert_dict["alert_id"]
            if self.alerts[alert_id].status == MedicineAlertStatus.PENDING:
                result = self.send_alert(alert_id)
                if result["success"]:
                    sent_alerts.append(result["alert"])
        
        return sent_alerts
    
    def start_alert_monitoring(self, check_interval_seconds: int = 300):
        """Start background thread to monitor and send alerts"""
        if self._running:
            return {"success": False, "message": "Alert monitoring already running"}
        
        self._running = True
        
        def monitor_loop():
            while self._running:
                self.check_and_send_due_alerts()
                threading.Event().wait(check_interval_seconds)
        
        self._alert_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._alert_thread.start()
        
        return {"success": True, "message": "Alert monitoring started"}
    
    def stop_alert_monitoring(self):
        """Stop alert monitoring"""
        self._running = False
        return {"success": True, "message": "Alert monitoring stopped"}


# Global instance
prescription_scanner = PrescriptionScanner()
