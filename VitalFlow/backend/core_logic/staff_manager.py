"""
Staff management with fatigue tracking.
Ensures patient safety by preventing overworked staff from handling critical cases.
"""
import sys
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Staff, StaffRole, StaffStatus, Patient, PatientStatus
from shared.constants import StaffConfig
from shared.utils import get_enum_value
from .state import hospital_state


class StaffManager:
    """
    Manages staff operations including shift tracking, fatigue monitoring,
    and intelligent assignment based on workload and fatigue levels.
    """
    
    FATIGUE_THRESHOLD_HOURS = StaffConfig.FATIGUE_THRESHOLD_HOURS  # 12 hours
    WARNING_THRESHOLD_HOURS = StaffConfig.WARNING_THRESHOLD_HOURS  # 10 hours
    MAX_PATIENTS_PER_DOCTOR = StaffConfig.MAX_PATIENTS_PER_DOCTOR  # 5
    MAX_PATIENTS_PER_NURSE = StaffConfig.MAX_PATIENTS_PER_NURSE    # 8
    
    def punch_in(self, staff_id: str) -> bool:
        """
        Record staff starting their shift.
        
        Args:
            staff_id: ID of staff member
            
        Returns:
            True if punch-in successful
        """
        staff = hospital_state.staff.get(staff_id)
        if not staff:
            return False
        
        staff.shift_start = datetime.now()
        staff.status = StaffStatus.AVAILABLE
        
        # Handle both string and Enum for role
        role_str = staff.role.value if hasattr(staff.role, 'value') else staff.role
        
        hospital_state.log_decision(
            "STAFF_PUNCH_IN",
            f"{staff.name} ({role_str}) started shift",
            {"staff_id": staff_id, "time": staff.shift_start.isoformat()}
        )
        
        hospital_state.save()
        return True
    
    def punch_out(self, staff_id: str) -> bool:
        """
        Record staff ending their shift.
        Automatically unassigns from all patients.
        
        Args:
            staff_id: ID of staff member
            
        Returns:
            True if punch-out successful
        """
        staff = hospital_state.staff.get(staff_id)
        if not staff:
            return False
        
        hours_worked = self.get_hours_worked(staff_id)
        
        # Unassign from all patients
        for patient in hospital_state.patients.values():
            if patient.assigned_doctor_id == staff_id:
                patient.assigned_doctor_id = None
            if patient.assigned_nurse_id == staff_id:
                patient.assigned_nurse_id = None
        
        staff.shift_start = None
        staff.status = StaffStatus.OFF_DUTY
        staff.current_patient_ids = []
        
        hospital_state.log_decision(
            "STAFF_PUNCH_OUT",
            f"{staff.name} ended shift after {hours_worked:.1f} hours",
            {"staff_id": staff_id, "hours_worked": hours_worked}
        )
        
        hospital_state.save()
        return True
    
    def get_hours_worked(self, staff_id: str) -> float:
        """
        Calculate hours since punch in.
        
        Args:
            staff_id: ID of staff member
            
        Returns:
            Hours worked as float (0 if not punched in)
        """
        staff = hospital_state.staff.get(staff_id)
        if not staff or not staff.shift_start:
            return 0.0
        
        # Handle both datetime and string formats
        if isinstance(staff.shift_start, str):
            shift_start = datetime.fromisoformat(staff.shift_start)
        else:
            shift_start = staff.shift_start
        
        delta = datetime.now() - shift_start
        return delta.total_seconds() / 3600  # Convert to hours
    
    def is_fatigued(self, staff_id: str) -> bool:
        """
        Check if staff has exceeded fatigue threshold.
        
        Args:
            staff_id: ID of staff member
            
        Returns:
            True if fatigued (worked >= threshold hours)
        """
        hours = self.get_hours_worked(staff_id)
        return hours >= self.FATIGUE_THRESHOLD_HOURS
    
    def get_fatigue_warning(self, staff_id: str) -> Optional[str]:
        """
        Return warning message if approaching or exceeding fatigue limit.
        
        Args:
            staff_id: ID of staff member
            
        Returns:
            Warning message or None if no warning
        """
        hours = self.get_hours_worked(staff_id)
        staff = hospital_state.staff.get(staff_id)
        
        if not staff:
            return None
        
        if hours >= self.FATIGUE_THRESHOLD_HOURS:
            return f"⛔ FATIGUE LIMIT REACHED ({hours:.1f}h). {staff.name} should not handle new critical cases."
        elif hours >= self.WARNING_THRESHOLD_HOURS:
            remaining = self.FATIGUE_THRESHOLD_HOURS - hours
            return f"⚠️ {staff.name} approaching fatigue limit ({hours:.1f}h / {self.FATIGUE_THRESHOLD_HOURS}h). {remaining:.1f}h remaining."
        
        return None
    
    def get_fatigue_level(self, staff_id: str) -> str:
        """
        Get fatigue level as a category.
        
        Args:
            staff_id: ID of staff member
            
        Returns:
            "fresh", "normal", "tired", or "fatigued"
        """
        hours = self.get_hours_worked(staff_id)
        
        if hours < 4:
            return "fresh"
        elif hours < self.WARNING_THRESHOLD_HOURS:
            return "normal"
        elif hours < self.FATIGUE_THRESHOLD_HOURS:
            return "tired"
        else:
            return "fatigued"
    
    def get_available_staff(self, role: StaffRole = None, exclude_fatigued: bool = True) -> List[Staff]:
        """
        Get list of available staff, optionally filtered by role and fatigue.
        
        Args:
            role: Optional role to filter by
            exclude_fatigued: If True, exclude fatigued staff
            
        Returns:
            List of available Staff objects
        """
        available = []
        
        for staff in hospital_state.staff.values():
            # Check role filter
            if role and staff.role != role:
                continue
            
            # Check status
            if staff.status not in [StaffStatus.AVAILABLE, StaffStatus.BUSY]:
                continue
            
            # Check fatigue
            if exclude_fatigued and self.is_fatigued(staff.id):
                continue
            
            available.append(staff)
        
        return available
    
    def get_available_doctors(self, exclude_fatigued: bool = True) -> List[Staff]:
        """
        Get list of available doctors.
        
        Args:
            exclude_fatigued: If True, exclude fatigued doctors
            
        Returns:
            List of available doctor Staff objects
        """
        return self.get_available_staff(StaffRole.DOCTOR, exclude_fatigued)
    
    def get_available_nurses(self, exclude_fatigued: bool = True) -> List[Staff]:
        """
        Get list of available nurses.
        
        Args:
            exclude_fatigued: If True, exclude fatigued nurses
            
        Returns:
            List of available nurse Staff objects
        """
        return self.get_available_staff(StaffRole.NURSE, exclude_fatigued)
    
    def get_patient_count(self, staff_id: str) -> int:
        """
        Get number of patients assigned to a staff member.
        
        Args:
            staff_id: ID of staff member
            
        Returns:
            Number of assigned patients
        """
        staff = hospital_state.staff.get(staff_id)
        if not staff:
            return 0
        return len(staff.current_patient_ids)
    
    def can_take_more_patients(self, staff_id: str) -> bool:
        """
        Check if staff member can take more patients.
        
        Args:
            staff_id: ID of staff member
            
        Returns:
            True if staff can take more patients
        """
        staff = hospital_state.staff.get(staff_id)
        if not staff:
            return False
        
        current_count = self.get_patient_count(staff_id)
        
        if staff.role == StaffRole.DOCTOR:
            return current_count < self.MAX_PATIENTS_PER_DOCTOR
        elif staff.role == StaffRole.NURSE:
            return current_count < self.MAX_PATIENTS_PER_NURSE
        else:
            return True  # No limit for other roles
    
    def _calculate_assignment_score(self, staff: Staff, patient: Patient) -> float:
        """
        Calculate how suitable a staff member is for a patient.
        Higher score = better match.
        
        Factors:
        - Workload (fewer patients = higher score)
        - Fatigue (less tired = higher score)
        - Specialization match (if applicable)
        
        Args:
            staff: Staff member to evaluate
            patient: Patient to assign
            
        Returns:
            Assignment score (0-100)
        """
        score = 100.0
        
        # Workload factor (max 40 points deduction)
        current_patients = self.get_patient_count(staff.id)
        max_patients = self.MAX_PATIENTS_PER_DOCTOR if staff.role == StaffRole.DOCTOR else self.MAX_PATIENTS_PER_NURSE
        workload_ratio = current_patients / max_patients
        score -= workload_ratio * 40
        
        # Fatigue factor (max 30 points deduction)
        hours = self.get_hours_worked(staff.id)
        if hours >= self.FATIGUE_THRESHOLD_HOURS:
            score -= 30
        elif hours >= self.WARNING_THRESHOLD_HOURS:
            score -= 20
        elif hours >= 6:
            score -= 10
        
        # Specialization bonus (up to 20 points)
        if staff.specialization and patient.diagnosis:
            diagnosis_lower = patient.diagnosis.lower()
            spec_lower = staff.specialization.lower()
            
            # Simple keyword matching
            if spec_lower in diagnosis_lower or diagnosis_lower in spec_lower:
                score += 20
            elif any(word in diagnosis_lower for word in spec_lower.split()):
                score += 10
        
        # Critical patient penalty for tired staff
        if patient.status == PatientStatus.CRITICAL and hours >= self.WARNING_THRESHOLD_HOURS:
            score -= 20
        
        return max(0, score)
    
    def assign_doctor_to_patient(self, patient_id: str, prefer_specialist: bool = True) -> Optional[Staff]:
        """
        Assign best available doctor to patient.
        Excludes fatigued doctors for critical cases.
        
        Args:
            patient_id: ID of patient
            prefer_specialist: If True, prefer doctors with matching specialization
            
        Returns:
            Assigned Staff object or None
        """
        patient = hospital_state.patients.get(patient_id)
        if not patient:
            return None
        
        # For critical patients, always exclude fatigued doctors
        exclude_fatigued = patient.status == PatientStatus.CRITICAL
        
        available_doctors = self.get_available_doctors(exclude_fatigued=exclude_fatigued)
        
        if not available_doctors:
            # If no fresh doctors for critical patient, try all available
            if exclude_fatigued:
                available_doctors = self.get_available_doctors(exclude_fatigued=False)
                if available_doctors:
                    hospital_state.log_decision(
                        "FATIGUE_WARNING",
                        f"No fresh doctors available for critical patient. Assigning tired doctor with warning.",
                        {"patient_id": patient_id}
                    )
        
        if not available_doctors:
            hospital_state.log_decision(
                "ASSIGNMENT_FAILED",
                f"No doctors available for patient {patient.name}",
                {"patient_id": patient_id}
            )
            return None
        
        # Filter to only those who can take more patients
        available_doctors = [d for d in available_doctors if self.can_take_more_patients(d.id)]
        
        if not available_doctors:
            return None
        
        # Score and sort doctors
        scored = [(doc, self._calculate_assignment_score(doc, patient)) 
                  for doc in available_doctors]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        best_doctor = scored[0][0]
        
        # Make assignment
        patient.assigned_doctor_id = best_doctor.id
        best_doctor.current_patient_ids.append(patient_id)
        if best_doctor.status == StaffStatus.AVAILABLE:
            best_doctor.status = StaffStatus.BUSY
        
        hospital_state.log_decision(
            "DOCTOR_ASSIGNED",
            f"Dr. {best_doctor.name} ({best_doctor.specialization or 'General'}) assigned to {patient.name}",
            {
                "doctor_id": best_doctor.id,
                "patient_id": patient_id,
                "doctor_patients": len(best_doctor.current_patient_ids),
                "hours_worked": self.get_hours_worked(best_doctor.id)
            }
        )
        
        hospital_state.save()
        return best_doctor
    
    def assign_nurse_to_patient(self, patient_id: str) -> Optional[Staff]:
        """
        Assign best available nurse to patient.
        
        Args:
            patient_id: ID of patient
            
        Returns:
            Assigned Staff object or None
        """
        patient = hospital_state.patients.get(patient_id)
        if not patient:
            return None
        
        exclude_fatigued = patient.status == PatientStatus.CRITICAL
        available_nurses = self.get_available_nurses(exclude_fatigued=exclude_fatigued)
        
        if not available_nurses and exclude_fatigued:
            available_nurses = self.get_available_nurses(exclude_fatigued=False)
        
        if not available_nurses:
            return None
        
        # Filter to those who can take more patients
        available_nurses = [n for n in available_nurses if self.can_take_more_patients(n.id)]
        
        if not available_nurses:
            return None
        
        # Score and sort nurses
        scored = [(nurse, self._calculate_assignment_score(nurse, patient)) 
                  for nurse in available_nurses]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        best_nurse = scored[0][0]
        
        # Make assignment
        patient.assigned_nurse_id = best_nurse.id
        best_nurse.current_patient_ids.append(patient_id)
        if best_nurse.status == StaffStatus.AVAILABLE:
            best_nurse.status = StaffStatus.BUSY
        
        hospital_state.log_decision(
            "NURSE_ASSIGNED",
            f"Nurse {best_nurse.name} assigned to {patient.name}",
            {
                "nurse_id": best_nurse.id,
                "patient_id": patient_id,
                "nurse_patients": len(best_nurse.current_patient_ids)
            }
        )
        
        hospital_state.save()
        return best_nurse
    
    def unassign_staff_from_patient(self, patient_id: str) -> bool:
        """
        Unassign all staff from a patient (for discharge/transfer).
        
        Args:
            patient_id: ID of patient
            
        Returns:
            True if successful
        """
        patient = hospital_state.patients.get(patient_id)
        if not patient:
            return False
        
        # Unassign doctor
        if patient.assigned_doctor_id:
            doctor = hospital_state.staff.get(patient.assigned_doctor_id)
            if doctor and patient_id in doctor.current_patient_ids:
                doctor.current_patient_ids.remove(patient_id)
                if not doctor.current_patient_ids:
                    doctor.status = StaffStatus.AVAILABLE
            patient.assigned_doctor_id = None
        
        # Unassign nurse
        if patient.assigned_nurse_id:
            nurse = hospital_state.staff.get(patient.assigned_nurse_id)
            if nurse and patient_id in nurse.current_patient_ids:
                nurse.current_patient_ids.remove(patient_id)
                if not nurse.current_patient_ids:
                    nurse.status = StaffStatus.AVAILABLE
            patient.assigned_nurse_id = None
        
        hospital_state.save()
        return True
    
    def get_staff_status_summary(self) -> Dict[str, any]:
        """
        Get summary of staff status by role.
        
        Returns:
            Dictionary with staff statistics
        """
        summary = {
            "doctors": {"total": 0, "available": 0, "fatigued": 0},
            "nurses": {"total": 0, "available": 0, "fatigued": 0},
            "wardboys": {"total": 0, "available": 0},
            "drivers": {"total": 0, "available": 0},
            "fatigue_warnings": []
        }
        
        for staff in hospital_state.staff.values():
            role_key = get_enum_value(staff.role).lower() + "s"
            if role_key not in summary:
                continue
            
            summary[role_key]["total"] += 1
            
            if staff.status in [StaffStatus.AVAILABLE, StaffStatus.BUSY]:
                if not self.is_fatigued(staff.id):
                    summary[role_key]["available"] += 1
                elif role_key in ["doctors", "nurses"]:
                    summary[role_key]["fatigued"] += 1
            
            # Collect fatigue warnings
            warning = self.get_fatigue_warning(staff.id)
            if warning:
                summary["fatigue_warnings"].append({
                    "staff_id": staff.id,
                    "name": staff.name,
                    "role": get_enum_value(staff.role),
                    "warning": warning
                })
        
        return summary


# Singleton instance
staff_manager = StaffManager()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing StaffManager...")
    
    # Reset state
    hospital_state.clear_all()
    
    # Create test staff
    doctors = [
        Staff(id="D001", name="Dr. Sharma", role=StaffRole.DOCTOR, specialization="Cardiology"),
        Staff(id="D002", name="Dr. Patel", role=StaffRole.DOCTOR, specialization="Emergency"),
        Staff(id="D003", name="Dr. Kumar", role=StaffRole.DOCTOR, specialization="General"),
    ]
    
    nurses = [
        Staff(id="N001", name="Nurse Priya", role=StaffRole.NURSE),
        Staff(id="N002", name="Nurse Anita", role=StaffRole.NURSE),
    ]
    
    for s in doctors + nurses:
        hospital_state.add_staff(s)
    
    print(f"✓ Created {len(hospital_state.staff)} staff members")
    
    # Test punch in
    assert staff_manager.punch_in("D001"), "Punch in should succeed"
    assert staff_manager.punch_in("D002"), "Punch in should succeed"
    assert staff_manager.punch_in("N001"), "Punch in should succeed"
    print("✓ Staff punched in")
    
    # Test hours worked (should be very small since just punched in)
    hours = staff_manager.get_hours_worked("D001")
    assert hours < 0.1, "Hours should be minimal"
    print(f"✓ Hours worked: {hours:.4f}")
    
    # Test available doctors
    available = staff_manager.get_available_doctors()
    assert len(available) == 2, f"Should have 2 available doctors, got {len(available)}"
    print(f"✓ Available doctors: {len(available)}")
    
    # Create test patient
    patient = Patient(
        id="P001",
        name="Cardiac Patient",
        age=55,
        diagnosis="Cardiac Arrest",
        status=PatientStatus.CRITICAL,
        spo2=85.0,
        heart_rate=140
    )
    hospital_state.add_patient(patient)
    
    # Test doctor assignment
    assigned_doc = staff_manager.assign_doctor_to_patient("P001")
    assert assigned_doc is not None, "Should assign a doctor"
    print(f"✓ Assigned doctor: {assigned_doc.name} ({assigned_doc.specialization})")
    
    # Verify assignment
    assert patient.assigned_doctor_id == assigned_doc.id
    assert "P001" in assigned_doc.current_patient_ids
    print("✓ Assignment verified")
    
    # Test nurse assignment
    assigned_nurse = staff_manager.assign_nurse_to_patient("P001")
    assert assigned_nurse is not None, "Should assign a nurse"
    print(f"✓ Assigned nurse: {assigned_nurse.name}")
    
    # Test fatigue simulation
    # Manually set shift start to 11 hours ago
    doctor = hospital_state.staff.get("D002")
    doctor.shift_start = datetime.now() - timedelta(hours=11)
    
    warning = staff_manager.get_fatigue_warning("D002")
    assert warning is not None, "Should have fatigue warning"
    assert "approaching" in warning.lower() or "⚠️" in warning
    print(f"✓ Fatigue warning: {warning}")
    
    # Set to 13 hours (fatigued)
    doctor.shift_start = datetime.now() - timedelta(hours=13)
    
    is_fatigued = staff_manager.is_fatigued("D002")
    assert is_fatigued, "Should be fatigued"
    print("✓ Fatigue detection works")
    
    warning = staff_manager.get_fatigue_warning("D002")
    assert "LIMIT REACHED" in warning or "⛔" in warning
    print(f"✓ Fatigue limit warning: {warning}")
    
    # Test available doctors excluding fatigued
    available = staff_manager.get_available_doctors(exclude_fatigued=True)
    fatigued_excluded = all(s.id != "D002" for s in available)
    assert fatigued_excluded, "Fatigued doctor should be excluded"
    print("✓ Fatigued doctors excluded from availability")
    
    # Test staff status summary
    summary = staff_manager.get_staff_status_summary()
    print(f"✓ Staff summary: {summary['doctors']}")
    assert summary["doctors"]["fatigued"] == 1
    assert len(summary["fatigue_warnings"]) >= 1
    
    # Test punch out
    assert staff_manager.punch_out("D001"), "Punch out should succeed"
    doctor = hospital_state.staff.get("D001")
    assert doctor.status == StaffStatus.OFF_DUTY
    print("✓ Staff punch out works")
    
    # Clean up
    hospital_state.clear_all()
    
    print("\n✅ All StaffManager tests passed!")
