"""
Patient Report System for VitalFlow AI.
Generates daily patient reports with recovery tracking, meal/medicine schedules,
and estimated discharge dates.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_enum_value
from .state import hospital_state


class RecoveryTrend(str, Enum):
    """Patient recovery trend"""
    IMPROVING = "Improving"
    STABLE = "Stable"
    DECLINING = "Declining"
    CRITICAL = "Critical"


class MealStatus(str, Enum):
    """Meal status"""
    SCHEDULED = "Scheduled"
    SERVED = "Served"
    CONSUMED = "Consumed"
    SKIPPED = "Skipped"
    RESTRICTED = "Restricted"


class MedicineAdminStatus(str, Enum):
    """Medicine administration status"""
    SCHEDULED = "Scheduled"
    GIVEN = "Given"
    MISSED = "Missed"
    REFUSED = "Refused"
    DELAYED = "Delayed"


@dataclass
class VitalReading:
    """Single vital reading"""
    timestamp: datetime
    recorded_by: str
    spo2: float = 98.0
    heart_rate: int = 75
    blood_pressure: str = "120/80"
    temperature: float = 98.6
    respiratory_rate: int = 16
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "recorded_by": self.recorded_by,
            "spo2": self.spo2,
            "heart_rate": self.heart_rate,
            "blood_pressure": self.blood_pressure,
            "temperature": self.temperature,
            "respiratory_rate": self.respiratory_rate,
            "notes": self.notes
        }


@dataclass
class MealEntry:
    """Meal record for patient"""
    meal_id: str
    meal_type: str  # Breakfast, Lunch, Dinner, Snack
    scheduled_time: datetime
    status: MealStatus
    diet_type: str = "Normal"  # Normal, Diabetic, Low Salt, Liquid, NPO
    served_time: Optional[datetime] = None
    served_by: Optional[str] = None
    consumption_notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "meal_id": self.meal_id,
            "meal_type": self.meal_type,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status": get_enum_value(self.status),
            "diet_type": self.diet_type,
            "served_time": self.served_time.isoformat() if self.served_time else None,
            "served_by": self.served_by,
            "consumption_notes": self.consumption_notes
        }


@dataclass
class MedicineScheduleEntry:
    """Scheduled medicine for patient"""
    schedule_id: str
    medicine_id: str
    medicine_name: str
    dosage: str
    scheduled_time: datetime
    status: MedicineAdminStatus
    prescribed_by: str
    
    # Administration details
    given_time: Optional[datetime] = None
    given_by: Optional[str] = None
    notes: str = ""
    
    # Alert tracking
    alert_sent: bool = False
    alert_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "schedule_id": self.schedule_id,
            "medicine_id": self.medicine_id,
            "medicine_name": self.medicine_name,
            "dosage": self.dosage,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status": get_enum_value(self.status),
            "prescribed_by": self.prescribed_by,
            "given_time": self.given_time.isoformat() if self.given_time else None,
            "given_by": self.given_by,
            "notes": self.notes,
            "alert_sent": self.alert_sent
        }


@dataclass
class ConsultationNote:
    """Doctor consultation note"""
    note_id: str
    doctor_id: str
    doctor_name: str
    timestamp: datetime
    findings: str
    diagnosis: str
    treatment_plan: str
    next_visit: Optional[datetime] = None
    priority: str = "Routine"  # Routine, Follow-up, Urgent
    
    def to_dict(self) -> Dict:
        return {
            "note_id": self.note_id,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "timestamp": self.timestamp.isoformat(),
            "findings": self.findings,
            "diagnosis": self.diagnosis,
            "treatment_plan": self.treatment_plan,
            "next_visit": self.next_visit.isoformat() if self.next_visit else None,
            "priority": self.priority
        }


@dataclass
class PatientDailyReport:
    """Complete daily report for a patient"""
    patient_id: str
    patient_name: str
    date: datetime
    
    # Recovery metrics
    recovery_percentage: float = 0.0
    recovery_trend: RecoveryTrend = RecoveryTrend.STABLE
    admission_date: Optional[datetime] = None
    estimated_discharge: Optional[datetime] = None
    days_admitted: int = 0
    estimated_days_remaining: int = 0
    
    # Daily records
    vitals_history: List[VitalReading] = field(default_factory=list)
    meals: List[MealEntry] = field(default_factory=list)
    medicines_given: List[MedicineScheduleEntry] = field(default_factory=list)
    consultation_notes: List[ConsultationNote] = field(default_factory=list)
    
    # Summary
    nurse_notes: str = ""
    doctor_summary: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "date": self.date.isoformat(),
            "recovery": {
                "percentage": self.recovery_percentage,
                "trend": get_enum_value(self.recovery_trend),
                "admission_date": self.admission_date.isoformat() if self.admission_date else None,
                "estimated_discharge": self.estimated_discharge.isoformat() if self.estimated_discharge else None,
                "days_admitted": self.days_admitted,
                "estimated_days_remaining": self.estimated_days_remaining
            },
            "vitals_history": [v.to_dict() for v in self.vitals_history],
            "meals": [m.to_dict() for m in self.meals],
            "medicines_given": [m.to_dict() for m in self.medicines_given],
            "consultation_notes": [c.to_dict() for c in self.consultation_notes],
            "nurse_notes": self.nurse_notes,
            "doctor_summary": self.doctor_summary
        }


class PatientReportSystem:
    """
    Patient Report System for VitalFlow AI.
    
    Features:
    - Daily recovery percentage tracking
    - Doctor consultation reports
    - Meal times (updated by nurse, viewable by patient)
    - Medicine times (updated by nurse, viewable by patient)
    - Estimated discharge date based on recovery rate
    """
    
    def __init__(self):
        self.patient_reports: Dict[str, PatientDailyReport] = {}  # patient_id -> current report
        self.report_history: Dict[str, List[PatientDailyReport]] = {}  # patient_id -> [historical reports]
        self.medicine_schedules: Dict[str, List[MedicineScheduleEntry]] = {}  # patient_id -> schedules
        self.vitals_log: Dict[str, List[VitalReading]] = {}  # patient_id -> vitals
        self.consultation_history: Dict[str, List[ConsultationNote]] = {}  # patient_id -> notes
        self.schedule_counter = 0
        self.note_counter = 0
        self.meal_counter = 0
        
        # Standard meal times
        self.meal_times = {
            "Breakfast": "08:00",
            "Lunch": "12:30",
            "Snack": "16:00",
            "Dinner": "19:30"
        }
    
    def initialize_patient_report(self, patient_id: str, patient_name: str,
                                   admission_date: datetime, diagnosis: str = "") -> PatientDailyReport:
        """Initialize daily report for a new patient"""
        report = PatientDailyReport(
            patient_id=patient_id,
            patient_name=patient_name,
            date=datetime.now(),
            admission_date=admission_date,
            days_admitted=0,
            recovery_percentage=0.0,
            recovery_trend=RecoveryTrend.STABLE
        )
        
        self.patient_reports[patient_id] = report
        self.report_history[patient_id] = []
        self.medicine_schedules[patient_id] = []
        self.vitals_log[patient_id] = []
        self.consultation_history[patient_id] = []
        
        # Generate default meal schedule for today
        self._generate_daily_meals(patient_id)
        
        hospital_state.log_decision(
            "PATIENT_REPORT_INIT",
            f"📋 Daily report system initialized for {patient_name} (ID: {patient_id})"
        )
        
        return report
    
    def _generate_daily_meals(self, patient_id: str, diet_type: str = "Normal"):
        """Generate meal schedule for the day"""
        if patient_id not in self.patient_reports:
            return
        
        report = self.patient_reports[patient_id]
        today = datetime.now().date()
        
        for meal_type, time_str in self.meal_times.items():
            self.meal_counter += 1
            hour, minute = map(int, time_str.split(":"))
            scheduled_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            meal = MealEntry(
                meal_id=f"MEAL-{patient_id}-{self.meal_counter:04d}",
                meal_type=meal_type,
                scheduled_time=scheduled_time,
                status=MealStatus.SCHEDULED,
                diet_type=diet_type
            )
            report.meals.append(meal)
    
    def record_vitals(self, patient_id: str, recorded_by: str,
                      spo2: float = 98.0, heart_rate: int = 75,
                      blood_pressure: str = "120/80", temperature: float = 98.6,
                      respiratory_rate: int = 16, notes: str = "") -> Dict:
        """Record patient vitals (by nurse/doctor)"""
        if patient_id not in self.patient_reports:
            return {"success": False, "error": "Patient report not initialized"}
        
        vital = VitalReading(
            timestamp=datetime.now(),
            recorded_by=recorded_by,
            spo2=spo2,
            heart_rate=heart_rate,
            blood_pressure=blood_pressure,
            temperature=temperature,
            respiratory_rate=respiratory_rate,
            notes=notes
        )
        
        self.vitals_log[patient_id].append(vital)
        self.patient_reports[patient_id].vitals_history.append(vital)
        
        # Update recovery based on vitals
        self._update_recovery_metrics(patient_id)
        
        hospital_state.log_decision(
            "VITALS_RECORDED",
            f"📊 Vitals recorded for patient {patient_id} by {recorded_by}. SpO2: {spo2}%, HR: {heart_rate}, BP: {blood_pressure}"
        )
        
        return {
            "success": True,
            "vital": vital.to_dict(),
            "recovery": {
                "percentage": self.patient_reports[patient_id].recovery_percentage,
                "trend": get_enum_value(self.patient_reports[patient_id].recovery_trend)
            }
        }
    
    def _update_recovery_metrics(self, patient_id: str):
        """Calculate recovery percentage based on vitals trend"""
        if patient_id not in self.patient_reports:
            return
        
        report = self.patient_reports[patient_id]
        vitals = self.vitals_log.get(patient_id, [])
        
        if len(vitals) < 2:
            return
        
        # Calculate recovery score based on vital improvements
        latest = vitals[-1]
        previous = vitals[-2] if len(vitals) >= 2 else vitals[-1]
        
        # Scoring factors (simplified)
        score = 50  # Base score
        
        # SpO2 improvement
        if latest.spo2 >= 95:
            score += 15
        elif latest.spo2 >= 90:
            score += 10
        elif latest.spo2 < 88:
            score -= 20
        
        # Heart rate normalization
        if 60 <= latest.heart_rate <= 100:
            score += 10
        elif latest.heart_rate > 120 or latest.heart_rate < 50:
            score -= 15
        
        # Temperature normalization
        if 97.5 <= latest.temperature <= 99.5:
            score += 10
        elif latest.temperature > 101 or latest.temperature < 96:
            score -= 15
        
        # Trend comparison
        if latest.spo2 > previous.spo2:
            score += 5
        elif latest.spo2 < previous.spo2:
            score -= 5
        
        # Clamp score
        report.recovery_percentage = max(0, min(100, score))
        
        # Determine trend
        if report.recovery_percentage >= 80:
            report.recovery_trend = RecoveryTrend.IMPROVING
        elif report.recovery_percentage >= 60:
            report.recovery_trend = RecoveryTrend.STABLE
        elif report.recovery_percentage >= 40:
            report.recovery_trend = RecoveryTrend.DECLINING
        else:
            report.recovery_trend = RecoveryTrend.CRITICAL
        
        # Estimate discharge date based on recovery
        self._estimate_discharge(patient_id)
    
    def _estimate_discharge(self, patient_id: str):
        """Estimate discharge date based on recovery rate"""
        if patient_id not in self.patient_reports:
            return
        
        report = self.patient_reports[patient_id]
        
        if report.admission_date:
            report.days_admitted = (datetime.now() - report.admission_date).days
        
        # Estimate remaining days based on recovery percentage
        if report.recovery_percentage >= 90:
            report.estimated_days_remaining = 1
        elif report.recovery_percentage >= 80:
            report.estimated_days_remaining = 2
        elif report.recovery_percentage >= 70:
            report.estimated_days_remaining = 3
        elif report.recovery_percentage >= 60:
            report.estimated_days_remaining = 5
        elif report.recovery_percentage >= 50:
            report.estimated_days_remaining = 7
        else:
            report.estimated_days_remaining = 10  # Need more observation
        
        report.estimated_discharge = datetime.now() + timedelta(days=report.estimated_days_remaining)
    
    def add_consultation_note(self, patient_id: str, doctor_id: str, doctor_name: str,
                               findings: str, diagnosis: str, treatment_plan: str,
                               next_visit: Optional[datetime] = None,
                               priority: str = "Routine") -> Dict:
        """Add doctor's consultation note"""
        if patient_id not in self.patient_reports:
            return {"success": False, "error": "Patient report not initialized"}
        
        self.note_counter += 1
        note = ConsultationNote(
            note_id=f"CONSULT-{patient_id}-{self.note_counter:04d}",
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            timestamp=datetime.now(),
            findings=findings,
            diagnosis=diagnosis,
            treatment_plan=treatment_plan,
            next_visit=next_visit,
            priority=priority
        )
        
        self.consultation_history[patient_id].append(note)
        self.patient_reports[patient_id].consultation_notes.append(note)
        
        hospital_state.log_decision(
            "CONSULTATION_ADDED",
            f"📝 Dr. {doctor_name} added consultation for patient {patient_id}. Priority: {priority}"
        )
        
        return {"success": True, "consultation": note.to_dict()}
    
    def update_meal_status(self, patient_id: str, meal_id: str,
                           status: MealStatus, served_by: Optional[str] = None,
                           notes: str = "") -> Dict:
        """Update meal status (by nurse)"""
        if patient_id not in self.patient_reports:
            return {"success": False, "error": "Patient report not initialized"}
        
        report = self.patient_reports[patient_id]
        
        for meal in report.meals:
            if meal.meal_id == meal_id:
                meal.status = status
                if status in [MealStatus.SERVED, MealStatus.CONSUMED]:
                    meal.served_time = datetime.now()
                    meal.served_by = served_by
                meal.consumption_notes = notes
                
                hospital_state.log_decision(
                    "MEAL_UPDATED",
                    f"🍽️ {meal.meal_type} for patient {patient_id}: {get_enum_value(status)} by {served_by}"
                )
                
                return {"success": True, "meal": meal.to_dict()}
        
        return {"success": False, "error": f"Meal {meal_id} not found"}
    
    def schedule_medicine(self, patient_id: str, medicine_id: str, medicine_name: str,
                          dosage: str, scheduled_time: datetime, prescribed_by: str) -> Dict:
        """Schedule medicine for patient"""
        if patient_id not in self.medicine_schedules:
            self.medicine_schedules[patient_id] = []
        
        self.schedule_counter += 1
        schedule = MedicineScheduleEntry(
            schedule_id=f"SCHED-{patient_id}-{self.schedule_counter:04d}",
            medicine_id=medicine_id,
            medicine_name=medicine_name,
            dosage=dosage,
            scheduled_time=scheduled_time,
            status=MedicineAdminStatus.SCHEDULED,
            prescribed_by=prescribed_by
        )
        
        self.medicine_schedules[patient_id].append(schedule)
        
        if patient_id in self.patient_reports:
            self.patient_reports[patient_id].medicines_given.append(schedule)
        
        hospital_state.log_decision(
            "MEDICINE_SCHEDULED",
            f"💊 {medicine_name} ({dosage}) scheduled for patient {patient_id} at {scheduled_time.strftime('%H:%M')} by {prescribed_by}"
        )
        
        return {"success": True, "schedule": schedule.to_dict()}
    
    def confirm_medicine_given(self, patient_id: str, schedule_id: str,
                                given_by: str, notes: str = "") -> Dict:
        """Confirm medicine was given to patient (by nurse)"""
        schedules = self.medicine_schedules.get(patient_id, [])
        
        for schedule in schedules:
            if schedule.schedule_id == schedule_id:
                schedule.status = MedicineAdminStatus.GIVEN
                schedule.given_time = datetime.now()
                schedule.given_by = given_by
                schedule.notes = notes
                
                hospital_state.log_decision(
                    "MEDICINE_GIVEN",
                    f"✅ {schedule.medicine_name} given to patient {patient_id} by {given_by}"
                )
                
                return {"success": True, "schedule": schedule.to_dict()}
        
        return {"success": False, "error": f"Schedule {schedule_id} not found"}
    
    def get_upcoming_medicines(self, patient_id: str, hours: int = 2) -> List[Dict]:
        """Get medicines due in next N hours"""
        schedules = self.medicine_schedules.get(patient_id, [])
        now = datetime.now()
        upcoming = now + timedelta(hours=hours)
        
        pending = [
            s.to_dict() for s in schedules
            if s.status == MedicineAdminStatus.SCHEDULED
            and now <= s.scheduled_time <= upcoming
        ]
        
        return sorted(pending, key=lambda x: x["scheduled_time"])
    
    def get_patient_report(self, patient_id: str) -> Optional[Dict]:
        """Get current daily report for patient"""
        if patient_id not in self.patient_reports:
            return None
        return self.patient_reports[patient_id].to_dict()
    
    def get_patient_view(self, patient_id: str) -> Optional[Dict]:
        """
        Get patient-friendly view of their report.
        Simplified for patient/family viewing.
        """
        if patient_id not in self.patient_reports:
            return None
        
        report = self.patient_reports[patient_id]
        
        # Get today's schedule
        today = datetime.now().date()
        today_meals = [m.to_dict() for m in report.meals 
                       if m.scheduled_time.date() == today]
        today_medicines = [m.to_dict() for m in report.medicines_given 
                          if m.scheduled_time.date() == today]
        
        # Latest vitals
        latest_vitals = None
        if report.vitals_history:
            latest_vitals = report.vitals_history[-1].to_dict()
        
        return {
            "patient_name": report.patient_name,
            "patient_id": report.patient_id,
            "recovery_status": {
                "percentage": report.recovery_percentage,
                "trend": get_enum_value(report.recovery_trend),
                "trend_emoji": self._get_trend_emoji(report.recovery_trend),
                "message": self._get_recovery_message(report.recovery_percentage)
            },
            "admission_info": {
                "admission_date": report.admission_date.strftime("%d %b %Y") if report.admission_date else None,
                "days_admitted": report.days_admitted,
                "estimated_discharge": report.estimated_discharge.strftime("%d %b %Y") if report.estimated_discharge else None,
                "estimated_days_remaining": report.estimated_days_remaining
            },
            "latest_vitals": latest_vitals,
            "today_schedule": {
                "meals": today_meals,
                "medicines": today_medicines
            },
            "doctor_notes": [n.to_dict() for n in report.consultation_notes[-3:]]  # Last 3 notes
        }
    
    def _get_trend_emoji(self, trend: RecoveryTrend) -> str:
        """Get emoji for recovery trend"""
        emoji_map = {
            RecoveryTrend.IMPROVING: "📈",
            RecoveryTrend.STABLE: "➡️",
            RecoveryTrend.DECLINING: "📉",
            RecoveryTrend.CRITICAL: "🚨"
        }
        return emoji_map.get(trend, "➡️")
    
    def _get_recovery_message(self, percentage: float) -> str:
        """Get patient-friendly recovery message"""
        if percentage >= 90:
            return "Excellent progress! You're almost ready for discharge."
        elif percentage >= 80:
            return "Great improvement! Recovery is on track."
        elif percentage >= 70:
            return "Good progress. Continue following the treatment plan."
        elif percentage >= 60:
            return "Steady recovery. Rest and medication are helping."
        elif percentage >= 50:
            return "Making progress. The care team is monitoring you closely."
        else:
            return "Our care team is working hard to help you recover."
    
    def get_daily_summary(self, patient_id: str) -> Optional[Dict]:
        """Get summary of the day for shift handover"""
        if patient_id not in self.patient_reports:
            return None
        
        report = self.patient_reports[patient_id]
        
        medicines_given = len([m for m in report.medicines_given 
                               if m.status == MedicineAdminStatus.GIVEN])
        medicines_pending = len([m for m in report.medicines_given 
                                 if m.status == MedicineAdminStatus.SCHEDULED])
        
        meals_served = len([m for m in report.meals 
                            if m.status in [MealStatus.SERVED, MealStatus.CONSUMED]])
        
        return {
            "patient_id": patient_id,
            "patient_name": report.patient_name,
            "date": datetime.now().isoformat(),
            "vitals_count": len(report.vitals_history),
            "latest_vitals": report.vitals_history[-1].to_dict() if report.vitals_history else None,
            "medicines": {
                "given": medicines_given,
                "pending": medicines_pending,
                "total": medicines_given + medicines_pending
            },
            "meals_served": meals_served,
            "consultations_today": len(report.consultation_notes),
            "recovery": {
                "percentage": report.recovery_percentage,
                "trend": get_enum_value(report.recovery_trend)
            },
            "estimated_discharge": report.estimated_discharge.isoformat() if report.estimated_discharge else None,
            "nurse_notes": report.nurse_notes
        }
    
    def add_nurse_notes(self, patient_id: str, notes: str, nurse_name: str) -> Dict:
        """Add nurse shift notes"""
        if patient_id not in self.patient_reports:
            return {"success": False, "error": "Patient report not initialized"}
        
        report = self.patient_reports[patient_id]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        report.nurse_notes += f"\n[{timestamp}] {nurse_name}: {notes}"
        
        return {"success": True, "notes": report.nurse_notes}


# Global instance
patient_report_system = PatientReportSystem()
