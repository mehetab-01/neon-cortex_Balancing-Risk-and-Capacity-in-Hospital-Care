"""
Doctor Alert System for VitalFlow AI.
Handles critical emergency alerts when doctors are on leave or
when patients become critical before scheduled visits.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_enum_value
from .state import hospital_state


class AlertPriority(str, Enum):
    """Alert priority levels"""
    CRITICAL = "Critical"       # Life-threatening, immediate response
    URGENT = "Urgent"           # Serious, respond within 15 min
    HIGH = "High"               # Important, respond within 30 min
    MEDIUM = "Medium"           # Needs attention within 1 hour
    LOW = "Low"                 # Routine notification


class DoctorStatus(str, Enum):
    """Doctor availability status"""
    AVAILABLE = "Available"
    BUSY = "Busy"
    IN_SURGERY = "In Surgery"
    ON_ROUNDS = "On Rounds"
    ON_BREAK = "On Break"
    ON_LEAVE = "On Leave"
    OFF_DUTY = "Off Duty"
    EMERGENCY_RECALL = "Emergency Recall"


class AlertType(str, Enum):
    """Types of alerts"""
    CRITICAL_PATIENT = "Critical Patient"
    PATIENT_DETERIORATING = "Patient Deteriorating"
    CODE_BLUE = "Code Blue"
    EMERGENCY_ADMISSION = "Emergency Admission"
    DOCTOR_NEEDED = "Doctor Needed"
    SCHEDULED_VISIT_CRITICAL = "Scheduled Visit Critical"
    POST_OP_COMPLICATION = "Post-Op Complication"


class AlertStatus(str, Enum):
    """Alert status"""
    PENDING = "Pending"
    SENT = "Sent"
    ACKNOWLEDGED = "Acknowledged"
    DOCTOR_RESPONDING = "Doctor Responding"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"
    EXPIRED = "Expired"


@dataclass
class DoctorInfo:
    """Doctor information for alerts"""
    doctor_id: str
    name: str
    specialization: str
    phone: str
    email: str = ""
    status: DoctorStatus = DoctorStatus.AVAILABLE
    current_location: str = ""
    
    # Schedule
    next_available: Optional[datetime] = None
    scheduled_patients: List[str] = field(default_factory=list)  # patient_ids
    
    # Leave info
    on_leave_until: Optional[datetime] = None
    leave_reason: str = ""
    
    # Emergency contact
    emergency_reachable: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "doctor_id": self.doctor_id,
            "name": self.name,
            "specialization": self.specialization,
            "phone": self.phone,
            "email": self.email,
            "status": get_enum_value(self.status),
            "current_location": self.current_location,
            "next_available": self.next_available.isoformat() if self.next_available else None,
            "scheduled_patients": self.scheduled_patients,
            "on_leave_until": self.on_leave_until.isoformat() if self.on_leave_until else None,
            "leave_reason": self.leave_reason,
            "emergency_reachable": self.emergency_reachable
        }


@dataclass
class PatientCriticality:
    """Patient criticality tracking"""
    patient_id: str
    patient_name: str
    bed_id: str
    ward: str
    
    # Assigned doctor
    primary_doctor_id: str
    primary_doctor_name: str
    
    # Criticality
    criticality_level: int = 3  # 1-5, 1 being most critical
    current_condition: str = ""
    vitals_summary: str = ""
    
    # Schedule
    next_doctor_visit: Optional[datetime] = None
    last_doctor_visit: Optional[datetime] = None
    
    # Alert tracking
    alert_sent: bool = False
    alert_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "bed_id": self.bed_id,
            "ward": self.ward,
            "primary_doctor_id": self.primary_doctor_id,
            "primary_doctor_name": self.primary_doctor_name,
            "criticality_level": self.criticality_level,
            "current_condition": self.current_condition,
            "vitals_summary": self.vitals_summary,
            "next_doctor_visit": self.next_doctor_visit.isoformat() if self.next_doctor_visit else None,
            "last_doctor_visit": self.last_doctor_visit.isoformat() if self.last_doctor_visit else None,
            "alert_count": self.alert_count
        }


@dataclass
class DoctorAlert:
    """Critical alert to doctor"""
    alert_id: str
    alert_type: AlertType
    priority: AlertPriority
    
    # Patient info
    patient_id: str
    patient_name: str
    patient_condition: str
    bed_id: str
    ward: str
    
    # Doctor info
    doctor_id: str
    doctor_name: str
    doctor_status: DoctorStatus
    
    # Alert details
    message: str
    urgency_reason: str
    recommended_action: str
    
    # Timestamps
    created_at: datetime
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Status
    status: AlertStatus = AlertStatus.PENDING
    response_notes: str = ""
    
    # Escalation
    escalation_level: int = 0
    escalated_to: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "alert_type": get_enum_value(self.alert_type),
            "priority": get_enum_value(self.priority),
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "patient_condition": self.patient_condition,
            "bed_id": self.bed_id,
            "ward": self.ward,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "doctor_status": get_enum_value(self.doctor_status),
            "message": self.message,
            "urgency_reason": self.urgency_reason,
            "recommended_action": self.recommended_action,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "status": get_enum_value(self.status),
            "response_notes": self.response_notes,
            "escalation_level": self.escalation_level,
            "escalated_to": self.escalated_to
        }


class DoctorAlertSystem:
    """
    Doctor Alert System for VitalFlow AI.
    
    Features:
    - Critical emergency alerts even when doctor is on leave
    - Alerts when patient becomes critical before scheduled visit
    - Priority-based escalation
    - Backup doctor assignment
    - Complete alert tracking
    """
    
    def __init__(self):
        self.doctors: Dict[str, DoctorInfo] = {}
        self.patient_tracking: Dict[str, PatientCriticality] = {}
        self.alerts: Dict[str, DoctorAlert] = {}
        self.alert_counter = 0
        
        # Escalation settings
        self.escalation_timeout_minutes = {
            AlertPriority.CRITICAL: 5,
            AlertPriority.URGENT: 15,
            AlertPriority.HIGH: 30,
            AlertPriority.MEDIUM: 60,
            AlertPriority.LOW: 120
        }
        
        # Backup doctors by specialization
        self.backup_doctors: Dict[str, List[str]] = {}  # specialization -> [doctor_ids]
        
        # Initialize with sample doctors
        self._initialize_doctors()
    
    def _initialize_doctors(self):
        """Initialize sample doctors"""
        sample_doctors = [
            {"id": "DOC-001", "name": "Dr. Sharma", "spec": "Cardiology", "phone": "+91-9876543001"},
            {"id": "DOC-002", "name": "Dr. Patel", "spec": "Emergency", "phone": "+91-9876543002"},
            {"id": "DOC-003", "name": "Dr. Kumar", "spec": "Pulmonology", "phone": "+91-9876543003"},
            {"id": "DOC-004", "name": "Dr. Reddy", "spec": "Cardiology", "phone": "+91-9876543004"},
            {"id": "DOC-005", "name": "Dr. Singh", "spec": "General", "phone": "+91-9876543005"},
        ]
        
        for doc in sample_doctors:
            self.register_doctor(
                doctor_id=doc["id"],
                name=doc["name"],
                specialization=doc["spec"],
                phone=doc["phone"]
            )
    
    def register_doctor(self, doctor_id: str, name: str, specialization: str,
                        phone: str, email: str = "") -> DoctorInfo:
        """Register a doctor in the alert system"""
        doctor = DoctorInfo(
            doctor_id=doctor_id,
            name=name,
            specialization=specialization,
            phone=phone,
            email=email
        )
        self.doctors[doctor_id] = doctor
        
        # Add to backup list
        if specialization not in self.backup_doctors:
            self.backup_doctors[specialization] = []
        if doctor_id not in self.backup_doctors[specialization]:
            self.backup_doctors[specialization].append(doctor_id)
        
        return doctor
    
    def update_doctor_status(self, doctor_id: str, status: DoctorStatus,
                             location: str = "", on_leave_until: Optional[datetime] = None,
                             leave_reason: str = "") -> Dict:
        """Update doctor availability status"""
        if doctor_id not in self.doctors:
            return {"success": False, "error": "Doctor not found"}
        
        doctor = self.doctors[doctor_id]
        doctor.status = status
        doctor.current_location = location
        
        if status == DoctorStatus.ON_LEAVE:
            doctor.on_leave_until = on_leave_until
            doctor.leave_reason = leave_reason
            
            hospital_state.log_decision(
                "DOCTOR_ON_LEAVE",
                f"📅 {doctor.name} marked on leave until {on_leave_until.strftime('%d %b %Y') if on_leave_until else 'TBD'}. Reason: {leave_reason}"
            )
        
        return {"success": True, "doctor": doctor.to_dict()}
    
    def track_patient(self, patient_id: str, patient_name: str,
                      bed_id: str, ward: str,
                      primary_doctor_id: str, primary_doctor_name: str,
                      criticality_level: int = 3,
                      next_visit: Optional[datetime] = None) -> PatientCriticality:
        """Start tracking a patient for critical alerts"""
        tracking = PatientCriticality(
            patient_id=patient_id,
            patient_name=patient_name,
            bed_id=bed_id,
            ward=ward,
            primary_doctor_id=primary_doctor_id,
            primary_doctor_name=primary_doctor_name,
            criticality_level=criticality_level,
            next_doctor_visit=next_visit
        )
        self.patient_tracking[patient_id] = tracking
        return tracking
    
    def update_patient_criticality(self, patient_id: str, criticality_level: int,
                                    condition: str = "", vitals: str = "") -> Dict:
        """
        Update patient criticality level.
        Triggers alerts if patient becomes critical.
        """
        if patient_id not in self.patient_tracking:
            return {"success": False, "error": "Patient not being tracked"}
        
        tracking = self.patient_tracking[patient_id]
        old_level = tracking.criticality_level
        tracking.criticality_level = criticality_level
        tracking.current_condition = condition
        tracking.vitals_summary = vitals
        
        result = {"success": True, "tracking": tracking.to_dict()}
        
        # Check if patient became more critical
        if criticality_level < old_level and criticality_level <= 2:
            # Patient is critical (level 1 or 2), check doctor availability
            alert = self._handle_critical_patient(tracking)
            if alert:
                result["alert"] = alert.to_dict()
        
        return result
    
    def _handle_critical_patient(self, tracking: PatientCriticality) -> Optional[DoctorAlert]:
        """Handle a critical patient - send alerts as needed"""
        doctor_id = tracking.primary_doctor_id
        
        if doctor_id not in self.doctors:
            return None
        
        doctor = self.doctors[doctor_id]
        
        # Determine alert priority based on criticality
        priority = AlertPriority.CRITICAL if tracking.criticality_level == 1 else AlertPriority.URGENT
        
        # Check if doctor is on leave or unavailable
        if doctor.status in [DoctorStatus.ON_LEAVE, DoctorStatus.OFF_DUTY]:
            return self._create_emergency_alert(
                tracking, doctor, priority,
                alert_type=AlertType.CRITICAL_PATIENT,
                urgency_reason=f"Doctor is {get_enum_value(doctor.status)} but patient is CRITICAL",
                recommended_action="Please respond if possible or backup doctor will be contacted"
            )
        
        # Check if next visit is scheduled but patient became critical
        if tracking.next_doctor_visit and tracking.next_doctor_visit > datetime.now():
            time_until_visit = tracking.next_doctor_visit - datetime.now()
            if time_until_visit > timedelta(minutes=30):
                return self._create_emergency_alert(
                    tracking, doctor, priority,
                    alert_type=AlertType.SCHEDULED_VISIT_CRITICAL,
                    urgency_reason=f"Patient critical BEFORE scheduled visit. Next visit in {int(time_until_visit.total_seconds() / 60)} minutes.",
                    recommended_action="Please come immediately - patient cannot wait until scheduled time"
                )
        
        return None
    
    def _create_emergency_alert(self, tracking: PatientCriticality,
                                 doctor: DoctorInfo,
                                 priority: AlertPriority,
                                 alert_type: AlertType,
                                 urgency_reason: str,
                                 recommended_action: str) -> DoctorAlert:
        """Create and send emergency alert to doctor"""
        self.alert_counter += 1
        alert_id = f"DOC-ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.alert_counter:04d}"
        
        # Generate message based on criticality
        message = self._generate_alert_message(tracking, doctor, alert_type)
        
        alert = DoctorAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            priority=priority,
            patient_id=tracking.patient_id,
            patient_name=tracking.patient_name,
            patient_condition=tracking.current_condition,
            bed_id=tracking.bed_id,
            ward=tracking.ward,
            doctor_id=doctor.doctor_id,
            doctor_name=doctor.name,
            doctor_status=doctor.status,
            message=message,
            urgency_reason=urgency_reason,
            recommended_action=recommended_action,
            created_at=datetime.now(),
            status=AlertStatus.PENDING
        )
        
        self.alerts[alert_id] = alert
        tracking.alert_sent = True
        tracking.alert_count += 1
        
        # Auto-send alert
        self._send_alert(alert)
        
        hospital_state.log_decision(
            "DOCTOR_EMERGENCY_ALERT",
            f"🚨 CRITICAL ALERT to {doctor.name}: {message}"
        )
        
        return alert
    
    def _generate_alert_message(self, tracking: PatientCriticality,
                                doctor: DoctorInfo, alert_type: AlertType) -> str:
        """Generate alert message"""
        criticality_emoji = "🔴" if tracking.criticality_level == 1 else "🟠"
        
        if alert_type == AlertType.CRITICAL_PATIENT and doctor.status == DoctorStatus.ON_LEAVE:
            return (f"{criticality_emoji} URGENT: Patient {tracking.patient_name} in {tracking.ward} "
                   f"(Bed: {tracking.bed_id}) is CRITICAL. You are on leave but we need your guidance. "
                   f"Condition: {tracking.current_condition}. Please respond if possible.")
        
        elif alert_type == AlertType.SCHEDULED_VISIT_CRITICAL:
            return (f"{criticality_emoji} URGENT: Patient {tracking.patient_name} became CRITICAL "
                   f"before your scheduled visit. Location: {tracking.ward}, Bed {tracking.bed_id}. "
                   f"Condition: {tracking.current_condition}. Please come immediately.")
        
        else:
            return (f"{criticality_emoji} ALERT: Patient {tracking.patient_name} needs immediate attention. "
                   f"Location: {tracking.ward}, Bed {tracking.bed_id}. "
                   f"Criticality: Level {tracking.criticality_level}. {tracking.current_condition}")
    
    def _send_alert(self, alert: DoctorAlert):
        """Send alert to doctor (via SMS/Call/Push notification)"""
        alert.status = AlertStatus.SENT
        alert.sent_at = datetime.now()
        
        # In production, this would trigger actual notifications
        # For now, we log the action
        doctor = self.doctors.get(alert.doctor_id)
        if doctor:
            # Simulate notification
            hospital_state.log_decision(
                "ALERT_SENT",
                f"📱 Alert sent to {doctor.name} ({doctor.phone}): {alert.message}"
            )
    
    def acknowledge_alert(self, alert_id: str, doctor_id: str,
                          response: str = "", coming_eta: Optional[int] = None) -> Dict:
        """Doctor acknowledges the alert"""
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()
        alert.response_notes = response
        
        if coming_eta:
            alert.response_notes += f" ETA: {coming_eta} minutes"
        
        # Update doctor status
        if doctor_id in self.doctors:
            self.doctors[doctor_id].status = DoctorStatus.EMERGENCY_RECALL
        
        hospital_state.log_decision(
            "ALERT_ACKNOWLEDGED",
            f"✅ {alert.doctor_name} acknowledged alert for {alert.patient_name}. Response: {response}. ETA: {coming_eta or 'ASAP'} min"
        )
        
        return {"success": True, "alert": alert.to_dict()}
    
    def mark_doctor_responding(self, alert_id: str) -> Dict:
        """Mark that doctor is on the way"""
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.DOCTOR_RESPONDING
        
        hospital_state.log_decision(
            "DOCTOR_RESPONDING",
            f"🏃 {alert.doctor_name} is responding to alert for {alert.patient_name}"
        )
        
        return {"success": True, "alert": alert.to_dict()}
    
    def resolve_alert(self, alert_id: str, resolution_notes: str = "") -> Dict:
        """Resolve the alert"""
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        alert.response_notes = resolution_notes
        
        hospital_state.log_decision(
            "ALERT_RESOLVED",
            f"✅ Alert {alert_id} resolved for {alert.patient_name}. Notes: {resolution_notes}"
        )
        
        return {"success": True, "alert": alert.to_dict()}
    
    def escalate_alert(self, alert_id: str) -> Dict:
        """Escalate alert to backup doctor"""
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        original_doctor = self.doctors.get(alert.doctor_id)
        
        if not original_doctor:
            return {"success": False, "error": "Original doctor not found"}
        
        # Find backup doctor
        backup_doctor = self._find_backup_doctor(original_doctor.specialization, alert.doctor_id)
        
        if not backup_doctor:
            hospital_state.log_decision(
                "ESCALATION_FAILED",
                f"⚠️ No backup doctor available for specialization: {original_doctor.specialization}"
            )
            return {"success": False, "error": "No backup doctor available"}
        
        # Create new alert for backup doctor
        alert.escalation_level += 1
        alert.escalated_to = backup_doctor.doctor_id
        alert.status = AlertStatus.ESCALATED
        
        # Create new alert for backup
        new_alert = self._create_emergency_alert(
            self.patient_tracking[alert.patient_id],
            backup_doctor,
            alert.priority,
            alert.alert_type,
            f"ESCALATED from {original_doctor.name}: {alert.urgency_reason}",
            alert.recommended_action
        )
        
        hospital_state.log_decision(
            "ALERT_ESCALATED",
            f"⬆️ Alert escalated from {original_doctor.name} to {backup_doctor.name} for {alert.patient_name}"
        )
        
        return {
            "success": True,
            "original_alert": alert.to_dict(),
            "escalated_alert": new_alert.to_dict(),
            "backup_doctor": backup_doctor.to_dict()
        }
    
    def _find_backup_doctor(self, specialization: str, exclude_doctor_id: str) -> Optional[DoctorInfo]:
        """Find an available backup doctor"""
        # First try same specialization
        if specialization in self.backup_doctors:
            for doc_id in self.backup_doctors[specialization]:
                if doc_id != exclude_doctor_id and doc_id in self.doctors:
                    doctor = self.doctors[doc_id]
                    if doctor.status in [DoctorStatus.AVAILABLE, DoctorStatus.BUSY, DoctorStatus.ON_ROUNDS]:
                        return doctor
        
        # Try emergency doctors
        if "Emergency" in self.backup_doctors:
            for doc_id in self.backup_doctors["Emergency"]:
                if doc_id in self.doctors:
                    doctor = self.doctors[doc_id]
                    if doctor.status in [DoctorStatus.AVAILABLE, DoctorStatus.BUSY]:
                        return doctor
        
        # Try any available doctor
        for doctor in self.doctors.values():
            if doctor.doctor_id != exclude_doctor_id and doctor.status == DoctorStatus.AVAILABLE:
                return doctor
        
        return None
    
    def check_and_escalate_pending_alerts(self) -> List[Dict]:
        """Check for alerts that need escalation"""
        escalated = []
        now = datetime.now()
        
        for alert in self.alerts.values():
            if alert.status == AlertStatus.SENT:
                timeout = self.escalation_timeout_minutes.get(alert.priority, 30)
                if alert.sent_at and (now - alert.sent_at).total_seconds() > timeout * 60:
                    result = self.escalate_alert(alert.alert_id)
                    if result["success"]:
                        escalated.append(result)
        
        return escalated
    
    def get_pending_alerts(self, doctor_id: Optional[str] = None) -> List[Dict]:
        """Get pending alerts, optionally filtered by doctor"""
        pending_statuses = [AlertStatus.PENDING, AlertStatus.SENT]
        
        alerts = [
            a.to_dict() for a in self.alerts.values()
            if a.status in pending_statuses
            and (doctor_id is None or a.doctor_id == doctor_id)
        ]
        
        return sorted(alerts, key=lambda x: (
            0 if x["priority"] == "Critical" else 1 if x["priority"] == "Urgent" else 2,
            x["created_at"]
        ))
    
    def get_doctor_status_summary(self) -> Dict:
        """Get summary of all doctors' status"""
        status_counts = {}
        for status in DoctorStatus:
            status_counts[get_enum_value(status)] = sum(
                1 for d in self.doctors.values() if d.status == status
            )
        
        return {
            "total_doctors": len(self.doctors),
            "status_breakdown": status_counts,
            "on_leave": [d.to_dict() for d in self.doctors.values() if d.status == DoctorStatus.ON_LEAVE],
            "available": [d.to_dict() for d in self.doctors.values() if d.status == DoctorStatus.AVAILABLE]
        }
    
    def get_critical_patients(self) -> List[Dict]:
        """Get all critical patients being tracked"""
        return [
            t.to_dict() for t in self.patient_tracking.values()
            if t.criticality_level <= 2
        ]
    
    def get_alert_history(self, patient_id: Optional[str] = None,
                          doctor_id: Optional[str] = None) -> List[Dict]:
        """Get alert history"""
        alerts = list(self.alerts.values())
        
        if patient_id:
            alerts = [a for a in alerts if a.patient_id == patient_id]
        if doctor_id:
            alerts = [a for a in alerts if a.doctor_id == doctor_id]
        
        return [a.to_dict() for a in sorted(alerts, key=lambda x: x.created_at, reverse=True)]


# Global instance
doctor_alert_system = DoctorAlertSystem()
