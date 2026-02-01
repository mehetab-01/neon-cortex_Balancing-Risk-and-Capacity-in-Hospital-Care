"""
Patient triage and priority calculations.
Handles incoming patient processing, status updates, and priority-based decisions.
"""
import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Patient, Bed, PatientStatus, BedType
from shared.constants import VitalThresholds, TriagePriority
from shared.utils import get_enum_value
from .state import hospital_state
from .bed_manager import bed_manager
from .staff_manager import staff_manager


class TriageEngine:
    """
    Handles patient triage, priority calculations, and status management.
    Core decision-making engine for patient flow.
    """
    
    def calculate_priority(self, patient: Patient) -> int:
        """
        Calculate triage priority (1-5, 1 is most urgent).
        Based on: status, vitals, special conditions
        
        Priority Levels:
        1 - RESUSCITATION: Immediate life-threatening
        2 - EMERGENCY: High risk of deterioration  
        3 - URGENT: Requires prompt care
        4 - SEMI_URGENT: Serious but stable
        5 - NON_URGENT: Minor issues
        
        Args:
            patient: Patient object to evaluate
            
        Returns:
            Priority level (1-5)
        """
        priority = 5  # Default low priority
        
        # ========== STATUS-BASED PRIORITY ==========
        if patient.status == PatientStatus.CRITICAL:
            priority = 1
        elif patient.status == PatientStatus.SERIOUS:
            priority = 2
        elif patient.status == PatientStatus.STABLE:
            priority = 3
        elif patient.status == PatientStatus.RECOVERING:
            priority = 4
        else:
            priority = 5
        
        # ========== VITALS OVERRIDE ==========
        # SpO2 checks - can upgrade priority
        if patient.spo2 < VitalThresholds.SPO2_CRITICAL:  # < 85%
            priority = 1  # Override to critical
        elif patient.spo2 < VitalThresholds.SPO2_LOW:  # < 90%
            priority = min(priority, 2)
        
        # Heart rate checks
        if (patient.heart_rate > VitalThresholds.HR_CRITICAL_HIGH or 
            patient.heart_rate < VitalThresholds.HR_CRITICAL_LOW):
            priority = 1  # Override to critical
        elif (patient.heart_rate > VitalThresholds.HR_HIGH or 
              patient.heart_rate < VitalThresholds.HR_LOW):
            priority = min(priority, 2)
        
        # Temperature checks (if abnormal)
        if hasattr(patient, 'temperature'):
            if patient.temperature >= VitalThresholds.TEMP_HIGH_FEVER:  # >= 103°F
                priority = min(priority, 2)
            elif patient.temperature >= VitalThresholds.TEMP_FEVER:  # >= 100.4°F
                priority = min(priority, 3)
            elif patient.temperature <= VitalThresholds.TEMP_HYPOTHERMIA:  # <= 95°F
                priority = min(priority, 2)
        
        # ========== SPECIAL CONDITIONS ==========
        # Check for dangerous diagnosis keywords
        if patient.diagnosis:
            diagnosis_lower = patient.diagnosis.lower()
            critical_keywords = ['cardiac arrest', 'stroke', 'heart attack', 'trauma', 
                               'hemorrhage', 'respiratory failure', 'sepsis', 'anaphylaxis']
            urgent_keywords = ['chest pain', 'difficulty breathing', 'severe pain',
                             'fracture', 'head injury', 'burns']
            
            if any(kw in diagnosis_lower for kw in critical_keywords):
                priority = 1
            elif any(kw in diagnosis_lower for kw in urgent_keywords):
                priority = min(priority, 2)
        
        return priority
    
    def get_priority_label(self, priority: int) -> str:
        """
        Get human-readable label for priority level.
        
        Args:
            priority: Priority level (1-5)
            
        Returns:
            Label string
        """
        labels = {
            1: "🔴 RESUSCITATION",
            2: "🟠 EMERGENCY",
            3: "🟡 URGENT",
            4: "🟢 SEMI-URGENT",
            5: "🔵 NON-URGENT"
        }
        return labels.get(priority, "⚪ UNKNOWN")
    
    def update_patient_vitals(self, patient_id: str, new_vitals: dict) -> Dict:
        """
        Update patient vitals and auto-adjust status if needed.
        This is called by the simulation when vitals change.
        
        Args:
            patient_id: ID of patient to update
            new_vitals: Dict with vital updates (spo2, heart_rate, temperature, etc.)
            
        Returns:
            Dict with update results
        """
        patient = hospital_state.patients.get(patient_id)
        if not patient:
            return {"success": False, "message": "Patient not found"}
        
        old_status = patient.status
        old_priority = self.calculate_priority(patient)
        
        # Update vitals
        if 'spo2' in new_vitals:
            patient.spo2 = new_vitals['spo2']
        if 'heart_rate' in new_vitals:
            patient.heart_rate = new_vitals['heart_rate']
        if 'blood_pressure' in new_vitals:
            patient.blood_pressure = new_vitals['blood_pressure']
        if 'temperature' in new_vitals:
            patient.temperature = new_vitals['temperature']
        
        # ========== AUTO-STATUS UPGRADE LOGIC ==========
        status_changed = False
        bed_changed = False
        
        # Check for critical conditions
        is_critical = (
            patient.spo2 < VitalThresholds.SPO2_CRITICAL or
            patient.heart_rate < VitalThresholds.HR_CRITICAL_LOW or
            patient.heart_rate > VitalThresholds.HR_CRITICAL_HIGH
        )
        
        is_serious = (
            patient.spo2 < VitalThresholds.SPO2_LOW or
            patient.heart_rate < VitalThresholds.HR_LOW or
            patient.heart_rate > VitalThresholds.HR_HIGH
        )
        
        # Upgrade status if vitals are dangerous
        if is_critical and patient.status != PatientStatus.CRITICAL:
            patient.status = PatientStatus.CRITICAL
            status_changed = True
            
            hospital_state.log_decision(
                "STATUS_UPGRADE_CRITICAL",
                f"Patient {patient.name} auto-upgraded to CRITICAL due to dangerous vitals (SpO2: {patient.spo2}%, HR: {patient.heart_rate})",
                {
                    "patient_id": patient_id,
                    "old_status": get_enum_value(old_status),
                    "new_status": get_enum_value(patient.status),
                    "spo2": patient.spo2,
                    "heart_rate": patient.heart_rate
                }
            )
            
        elif is_serious and patient.status not in [PatientStatus.CRITICAL, PatientStatus.SERIOUS]:
            patient.status = PatientStatus.SERIOUS
            status_changed = True
            
            hospital_state.log_decision(
                "STATUS_UPGRADE_SERIOUS",
                f"Patient {patient.name} auto-upgraded to SERIOUS due to declining vitals (SpO2: {patient.spo2}%, HR: {patient.heart_rate})",
                {
                    "patient_id": patient_id,
                    "old_status": get_enum_value(old_status),
                    "new_status": get_enum_value(patient.status)
                }
            )
        
        # Check for recovery (improvement)
        is_recovering = (
            patient.spo2 >= VitalThresholds.SPO2_NORMAL_MIN and
            VitalThresholds.HR_NORMAL_MIN <= patient.heart_rate <= VitalThresholds.HR_NORMAL_MAX
        )
        
        if is_recovering and patient.status == PatientStatus.SERIOUS:
            patient.status = PatientStatus.STABLE
            status_changed = True
            
            hospital_state.log_decision(
                "STATUS_IMPROVEMENT",
                f"Patient {patient.name} improved from SERIOUS to STABLE (SpO2: {patient.spo2}%, HR: {patient.heart_rate})",
                {"patient_id": patient_id}
            )
        
        # ========== BED REASSIGNMENT IF NEEDED ==========
        if status_changed and patient.status == PatientStatus.CRITICAL and patient.bed_id:
            current_bed = hospital_state.beds.get(patient.bed_id)
            if current_bed and current_bed.bed_type != BedType.ICU:
                # Patient needs ICU but isn't in one - trigger swap
                success, message = bed_manager.execute_swap(patient)
                if success:
                    bed_changed = True
        
        new_priority = self.calculate_priority(patient)
        hospital_state.save()
        
        return {
            "success": True,
            "patient_id": patient_id,
            "status_changed": status_changed,
            "old_status": get_enum_value(old_status),
            "new_status": get_enum_value(patient.status),
            "old_priority": old_priority,
            "new_priority": new_priority,
            "bed_changed": bed_changed,
            "current_bed": patient.bed_id
        }
    
    def process_incoming_patient(self, patient: Patient, auto_assign_staff: bool = True) -> Dict:
        """
        Process a new incoming patient (e.g., from ambulance or walk-in).
        Handles registration, triage, bed assignment, and staff assignment.
        
        Args:
            patient: Patient object to process
            auto_assign_staff: If True, automatically assign doctor and nurse
            
        Returns:
            Dict with processing results
        """
        result = {
            "success": False,
            "patient_id": patient.id,
            "priority": None,
            "priority_label": None,
            "bed_assigned": None,
            "doctor_assigned": None,
            "nurse_assigned": None,
            "message": "",
            "actions_taken": []
        }
        
        # Step 1: Calculate priority
        priority = self.calculate_priority(patient)
        patient.priority = priority
        result["priority"] = priority
        result["priority_label"] = self.get_priority_label(priority)
        result["actions_taken"].append(f"Triage priority set to {priority}")
        
        # Step 2: Register patient in system
        if patient.id not in hospital_state.patients:
            hospital_state.patients[patient.id] = patient
            result["actions_taken"].append("Patient registered in system")
        
        # Step 3: Bed Assignment
        if priority == 1:  # Critical - use Tetris swap if needed
            success, message = bed_manager.execute_swap(patient)
            result["bed_assigned"] = patient.bed_id
            result["actions_taken"].append(f"Bed: {message}")
        else:
            # Try to find best available bed
            bed = bed_manager.find_best_bed(patient)
            if bed:
                bed_manager.assign_patient_to_bed(patient.id, bed.id)
                result["bed_assigned"] = bed.id
                result["actions_taken"].append(f"Assigned to bed {bed.id}")
            else:
                result["actions_taken"].append("No beds currently available - patient in queue")
        
        # Step 4: Staff Assignment
        if auto_assign_staff:
            # Assign doctor
            doctor = staff_manager.assign_doctor_to_patient(patient.id)
            if doctor:
                result["doctor_assigned"] = doctor.name
                result["actions_taken"].append(f"Doctor {doctor.name} assigned")
            else:
                result["actions_taken"].append("No doctor available - pending assignment")
            
            # Assign nurse
            nurse = staff_manager.assign_nurse_to_patient(patient.id)
            if nurse:
                result["nurse_assigned"] = nurse.name
                result["actions_taken"].append(f"Nurse {nurse.name} assigned")
            else:
                result["actions_taken"].append("No nurse available - pending assignment")
        
        # Step 5: Log the admission
        hospital_state.log_decision(
            "PATIENT_ADMITTED",
            f"New patient {patient.name} admitted with priority {priority} ({self.get_priority_label(priority)})",
            {
                "patient_id": patient.id,
                "name": patient.name,
                "priority": priority,
                "diagnosis": patient.diagnosis,
                "spo2": patient.spo2,
                "heart_rate": patient.heart_rate,
                "bed": result["bed_assigned"],
                "doctor": result["doctor_assigned"]
            }
        )
        
        result["success"] = True
        result["message"] = f"Patient processed successfully with priority {priority}"
        
        hospital_state.save()
        return result
    
    def discharge_patient(self, patient_id: str, reason: str = "Recovery") -> Dict:
        """
        Discharge a patient from the hospital.
        Releases bed and unassigns staff.
        
        Args:
            patient_id: ID of patient to discharge
            reason: Reason for discharge
            
        Returns:
            Dict with discharge results
        """
        patient = hospital_state.patients.get(patient_id)
        if not patient:
            return {"success": False, "message": "Patient not found"}
        
        result = {
            "success": True,
            "patient_id": patient_id,
            "patient_name": patient.name,
            "freed_bed": patient.bed_id,
            "actions_taken": []
        }
        
        # Release bed
        if patient.bed_id:
            bed_manager.release_bed(patient.bed_id)
            result["actions_taken"].append(f"Released bed {patient.bed_id}")
        
        # Unassign staff
        staff_manager.unassign_staff_from_patient(patient_id)
        result["actions_taken"].append("Staff unassigned")
        
        # Update patient status
        patient.status = PatientStatus.DISCHARGED
        patient.bed_id = None
        
        hospital_state.log_decision(
            "PATIENT_DISCHARGED",
            f"Patient {patient.name} discharged. Reason: {reason}",
            {
                "patient_id": patient_id,
                "reason": reason,
                "freed_bed": result["freed_bed"]
            }
        )
        
        # Remove from active patients
        del hospital_state.patients[patient_id]
        
        hospital_state.save()
        return result
    
    def get_patient_queue(self) -> List[Dict]:
        """
        Get list of patients sorted by priority.
        
        Returns:
            List of patient info dicts sorted by priority (most urgent first)
        """
        patients_with_priority = []
        
        for patient in hospital_state.patients.values():
            priority = self.calculate_priority(patient)
            patients_with_priority.append({
                "patient_id": patient.id,
                "name": patient.name,
                "priority": priority,
                "priority_label": self.get_priority_label(priority),
                "status": get_enum_value(patient.status),
                "spo2": patient.spo2,
                "heart_rate": patient.heart_rate,
                "bed_id": patient.bed_id,
                "has_doctor": patient.assigned_doctor_id is not None,
                "has_nurse": patient.assigned_nurse_id is not None
            })
        
        # Sort by priority (1 = most urgent = first)
        patients_with_priority.sort(key=lambda x: (x["priority"], x["name"]))
        
        return patients_with_priority
    
    def get_critical_alerts(self) -> List[Dict]:
        """
        Get list of patients with critical conditions needing immediate attention.
        
        Returns:
            List of alert dicts
        """
        alerts = []
        
        for patient in hospital_state.patients.values():
            priority = self.calculate_priority(patient)
            
            if priority == 1:
                alert = {
                    "type": "CRITICAL",
                    "patient_id": patient.id,
                    "patient_name": patient.name,
                    "bed_id": patient.bed_id or "UNASSIGNED",
                    "condition": [],
                    "urgency": "IMMEDIATE"
                }
                
                if patient.spo2 < VitalThresholds.SPO2_CRITICAL:
                    alert["condition"].append(f"Dangerously low SpO2: {patient.spo2}%")
                if patient.heart_rate < VitalThresholds.HR_CRITICAL_LOW:
                    alert["condition"].append(f"Critically low HR: {patient.heart_rate} bpm")
                if patient.heart_rate > VitalThresholds.HR_CRITICAL_HIGH:
                    alert["condition"].append(f"Critically high HR: {patient.heart_rate} bpm")
                if patient.status == PatientStatus.CRITICAL:
                    alert["condition"].append(f"Status: {get_enum_value(patient.status)}")
                
                alerts.append(alert)
            
            elif priority == 2 and patient.status == PatientStatus.SERIOUS:
                alerts.append({
                    "type": "WARNING",
                    "patient_id": patient.id,
                    "patient_name": patient.name,
                    "bed_id": patient.bed_id or "UNASSIGNED",
                    "condition": [f"Status: {get_enum_value(patient.status)}", 
                                  f"SpO2: {patient.spo2}%", 
                                  f"HR: {patient.heart_rate}"],
                    "urgency": "URGENT"
                })
        
        return alerts
    
    def get_triage_summary(self) -> Dict:
        """
        Get summary of current triage situation.
        
        Returns:
            Dict with triage statistics
        """
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        waiting_for_bed = 0
        waiting_for_doctor = 0
        
        for patient in hospital_state.patients.values():
            priority = self.calculate_priority(patient)
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            if not patient.bed_id:
                waiting_for_bed += 1
            if not patient.assigned_doctor_id:
                waiting_for_doctor += 1
        
        return {
            "total_patients": len(hospital_state.patients),
            "by_priority": {
                f"P{k} ({self.get_priority_label(k)})": v 
                for k, v in priority_counts.items()
            },
            "critical_count": priority_counts[1],
            "emergency_count": priority_counts[2],
            "waiting_for_bed": waiting_for_bed,
            "waiting_for_doctor": waiting_for_doctor,
            "alerts": len(self.get_critical_alerts())
        }


# Singleton instance
triage_engine = TriageEngine()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing TriageEngine...")
    
    # Reset state
    hospital_state.clear_all()
    
    # Setup beds
    beds_config = [
        ("ICU-01", BedType.ICU), ("ICU-02", BedType.ICU),
        ("ER-01", BedType.EMERGENCY), ("ER-02", BedType.EMERGENCY),
        ("GEN-01", BedType.GENERAL), ("GEN-02", BedType.GENERAL), ("GEN-03", BedType.GENERAL)
    ]
    for bed_id, bed_type in beds_config:
        hospital_state.add_bed(Bed(id=bed_id, bed_type=bed_type, ward=f"{bed_type.value} Ward"))
    
    # Setup staff
    from shared.models import Staff, StaffRole
    doctors = [
        Staff(id="D001", name="Dr. Sharma", role=StaffRole.DOCTOR, specialization="Cardiology"),
        Staff(id="D002", name="Dr. Patel", role=StaffRole.DOCTOR, specialization="Emergency"),
    ]
    nurses = [
        Staff(id="N001", name="Nurse Priya", role=StaffRole.NURSE),
    ]
    for s in doctors + nurses:
        hospital_state.add_staff(s)
        staff_manager.punch_in(s.id)
    
    print(f"✓ Setup complete: {len(hospital_state.beds)} beds, {len(hospital_state.staff)} staff")
    
    # Test 1: Priority calculation
    stable_patient = Patient(
        id="P-STABLE",
        name="Stable Patient",
        age=40,
        status=PatientStatus.STABLE,
        spo2=97.0,
        heart_rate=75
    )
    priority = triage_engine.calculate_priority(stable_patient)
    assert priority == 3, f"Stable patient should be priority 3, got {priority}"
    print(f"✓ Stable patient priority: {priority}")
    
    # Test 2: Critical by vitals
    critical_patient = Patient(
        id="P-CRITICAL",
        name="Critical Patient",
        age=60,
        status=PatientStatus.STABLE,  # Status says stable but vitals are critical
        spo2=80.0,  # Critical!
        heart_rate=160,  # Critical!
        diagnosis="Cardiac Arrest"
    )
    priority = triage_engine.calculate_priority(critical_patient)
    assert priority == 1, f"Critical vitals should override to priority 1, got {priority}"
    print(f"✓ Critical vitals priority: {priority}")
    
    # Test 3: Process incoming patient
    result = triage_engine.process_incoming_patient(critical_patient)
    assert result["success"], "Should process successfully"
    assert result["priority"] == 1
    assert result["bed_assigned"] is not None
    print(f"✓ Incoming patient processed: {result['message']}")
    print(f"  Actions: {result['actions_taken']}")
    
    # Test 4: Update vitals with auto-status upgrade
    patient = hospital_state.patients.get("P-CRITICAL")
    update_result = triage_engine.update_patient_vitals("P-CRITICAL", {
        "spo2": 95.0,  # Improved
        "heart_rate": 85  # Improved
    })
    print(f"✓ Vitals updated: {update_result}")
    
    # Test 5: Get patient queue
    # Add a few more patients
    for i, (status, spo2, hr) in enumerate([
        (PatientStatus.SERIOUS, 88, 110),
        (PatientStatus.STABLE, 96, 78),
        (PatientStatus.RECOVERING, 98, 72)
    ]):
        p = Patient(
            id=f"P-{i}",
            name=f"Patient {i}",
            age=30 + i * 10,
            status=status,
            spo2=spo2,
            heart_rate=hr
        )
        triage_engine.process_incoming_patient(p)
    
    queue = triage_engine.get_patient_queue()
    print(f"✓ Patient queue ({len(queue)} patients):")
    for p in queue:
        print(f"  - {p['name']}: Priority {p['priority']} ({p['priority_label']})")
    
    # Verify queue is sorted by priority
    priorities = [p["priority"] for p in queue]
    assert priorities == sorted(priorities), "Queue should be sorted by priority"
    print("✓ Queue is correctly sorted by priority")
    
    # Test 6: Critical alerts
    alerts = triage_engine.get_critical_alerts()
    print(f"✓ Critical alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  - [{alert['type']}] {alert['patient_name']}: {alert['condition']}")
    
    # Test 7: Triage summary
    summary = triage_engine.get_triage_summary()
    print(f"✓ Triage summary: {summary['total_patients']} patients")
    print(f"  Critical: {summary['critical_count']}, Emergency: {summary['emergency_count']}")
    
    # Test 8: Discharge patient
    discharge_result = triage_engine.discharge_patient("P-0", "Recovery")
    assert discharge_result["success"]
    print(f"✓ Patient discharged: {discharge_result['actions_taken']}")
    
    # Verify patient removed
    assert "P-0" not in hospital_state.patients
    print("✓ Discharged patient removed from system")
    
    # Clean up
    hospital_state.clear_all()
    
    print("\n✅ All TriageEngine tests passed!")
