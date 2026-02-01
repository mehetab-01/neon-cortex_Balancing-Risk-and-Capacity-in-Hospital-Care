"""
Central state store for the hospital.
Uses a simple in-memory store with JSON persistence for hackathon.
Implements Singleton pattern for global state access.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import Lock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Patient, Bed, Staff, Hospital, PatientStatus, BedType, StaffRole


class HospitalState:
    """
    Singleton class for managing hospital state.
    Thread-safe with automatic JSON persistence.
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize state containers"""
        self.patients: Dict[str, Patient] = {}
        self.beds: Dict[str, Bed] = {}
        self.staff: Dict[str, Staff] = {}
        self.ambulances: Dict[str, Any] = {}
        self.decision_log: List[dict] = []
        self.hospital = Hospital()
        
        # File path for persistence
        self.state_file = Path(__file__).parent.parent.parent / "shared" / "state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to load existing state
        self._load_state()
    
    def _load_state(self) -> bool:
        """Load state from JSON file if exists"""
        try:
            if self.state_file.exists():
                data = json.loads(self.state_file.read_text())
                
                # Reconstruct Patient objects
                for pid, pdata in data.get("patients", {}).items():
                    if isinstance(pdata.get("status"), str):
                        pdata["status"] = PatientStatus(pdata["status"])
                    self.patients[pid] = Patient(**pdata)
                
                # Reconstruct Bed objects
                for bid, bdata in data.get("beds", {}).items():
                    if isinstance(bdata.get("bed_type"), str):
                        bdata["bed_type"] = BedType(bdata["bed_type"])
                    self.beds[bid] = Bed(**bdata)
                
                # Reconstruct Staff objects
                for sid, sdata in data.get("staff", {}).items():
                    if isinstance(sdata.get("role"), str):
                        sdata["role"] = StaffRole(sdata["role"])
                    self.staff[sid] = Staff(**sdata)
                
                self.decision_log = data.get("decision_log", [])
                return True
        except Exception as e:
            print(f"Warning: Could not load state: {e}")
        return False
    
    def save(self) -> bool:
        """Persist state to JSON for frontend to read"""
        with self._lock:
            try:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "patients": {k: v.dict() for k, v in self.patients.items()},
                    "beds": {k: v.dict() for k, v in self.beds.items()},
                    "staff": {k: v.dict() for k, v in self.staff.items()},
                    "decision_log": self.decision_log[-50:],  # Last 50 decisions
                    "stats": self.get_stats()
                }
                self.state_file.write_text(json.dumps(data, default=str, indent=2))
                return True
            except Exception as e:
                print(f"Error saving state: {e}")
                return False
    
    def log_decision(self, action: str, reason: str, details: dict = None) -> None:
        """
        Log an AI decision for transparency.
        Useful for debugging and showing decision history in UI.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "reason": reason,
            "details": details or {}
        }
        self.decision_log.append(entry)
        
        # Print to console for debugging
        print(f"[DECISION] {action}: {reason}")
        
        # Auto-save after each decision
        self.save()
    
    def get_stats(self) -> dict:
        """Get current hospital statistics"""
        total_beds = len(self.beds)
        occupied_beds = sum(1 for b in self.beds.values() if b.is_occupied)
        
        stats_by_type = {}
        for bed_type in BedType:
            beds_of_type = [b for b in self.beds.values() if b.bed_type == bed_type]
            occupied = sum(1 for b in beds_of_type if b.is_occupied)
            stats_by_type[bed_type.value] = {
                "total": len(beds_of_type),
                "occupied": occupied,
                "available": len(beds_of_type) - occupied
            }
        
        patients_by_status = {}
        for status in PatientStatus:
            count = sum(1 for p in self.patients.values() if p.status == status)
            patients_by_status[status.value] = count
        
        return {
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": total_beds - occupied_beds,
            "occupancy_rate": (occupied_beds / total_beds * 100) if total_beds > 0 else 0,
            "by_bed_type": stats_by_type,
            "patients_by_status": patients_by_status,
            "total_patients": len(self.patients),
            "total_staff": len(self.staff)
        }
    
    def add_patient(self, patient: Patient) -> bool:
        """Add a new patient to the system"""
        if patient.id in self.patients:
            return False
        self.patients[patient.id] = patient
        self.save()
        return True
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID"""
        return self.patients.get(patient_id)
    
    def update_patient(self, patient_id: str, updates: dict) -> bool:
        """Update patient attributes"""
        patient = self.patients.get(patient_id)
        if not patient:
            return False
        
        for key, value in updates.items():
            if hasattr(patient, key):
                setattr(patient, key, value)
        
        self.save()
        return True
    
    def remove_patient(self, patient_id: str) -> bool:
        """Remove patient from system (discharge)"""
        if patient_id in self.patients:
            del self.patients[patient_id]
            self.save()
            return True
        return False
    
    def add_bed(self, bed: Bed) -> bool:
        """Add a new bed to the system"""
        if bed.id in self.beds:
            return False
        self.beds[bed.id] = bed
        self.save()
        return True
    
    def get_bed(self, bed_id: str) -> Optional[Bed]:
        """Get bed by ID"""
        return self.beds.get(bed_id)
    
    def add_staff(self, staff_member: Staff) -> bool:
        """Add a new staff member"""
        if staff_member.id in self.staff:
            return False
        self.staff[staff_member.id] = staff_member
        self.save()
        return True
    
    def get_staff(self, staff_id: str) -> Optional[Staff]:
        """Get staff member by ID"""
        return self.staff.get(staff_id)
    
    def clear_all(self) -> None:
        """Clear all state (for testing/reset)"""
        self.patients.clear()
        self.beds.clear()
        self.staff.clear()
        self.decision_log.clear()
        self.save()
    
    def get_recent_decisions(self, count: int = 10) -> List[dict]:
        """Get recent decision log entries"""
        return self.decision_log[-count:]


# Singleton instance - import this in other modules
hospital_state = HospitalState()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing HospitalState...")
    
    # Reset state for testing
    state = HospitalState()
    state.clear_all()
    
    # Test singleton pattern
    state2 = HospitalState()
    assert state is state2, "Singleton pattern failed"
    print("✓ Singleton pattern works")
    
    # Test adding patient
    patient = Patient(
        id="TEST-P001",
        name="Test Patient",
        age=30,
        diagnosis="Test Diagnosis",
        status=PatientStatus.STABLE,
        spo2=95.0,
        heart_rate=80
    )
    assert state.add_patient(patient), "Failed to add patient"
    print("✓ Patient added successfully")
    
    # Test getting patient
    retrieved = state.get_patient("TEST-P001")
    assert retrieved is not None, "Failed to retrieve patient"
    assert retrieved.name == "Test Patient"
    print("✓ Patient retrieved successfully")
    
    # Test adding bed
    bed = Bed(
        id="TEST-BED-001",
        bed_type=BedType.ICU,
        ward="ICU Ward",
        floor=4
    )
    assert state.add_bed(bed), "Failed to add bed"
    print("✓ Bed added successfully")
    
    # Test adding staff
    staff = Staff(
        id="TEST-D001",
        name="Dr. Test",
        role=StaffRole.DOCTOR,
        specialization="Testing"
    )
    assert state.add_staff(staff), "Failed to add staff"
    print("✓ Staff added successfully")
    
    # Test logging decision
    state.log_decision(
        "TEST_ACTION",
        "This is a test decision",
        {"test_key": "test_value"}
    )
    decisions = state.get_recent_decisions(1)
    assert len(decisions) == 1
    assert decisions[0]["action"] == "TEST_ACTION"
    print("✓ Decision logging works")
    
    # Test stats
    stats = state.get_stats()
    assert stats["total_patients"] == 1
    assert stats["total_beds"] == 1
    print(f"✓ Stats: {stats['total_patients']} patients, {stats['total_beds']} beds")
    
    # Test persistence
    assert state.save(), "Failed to save state"
    print("✓ State saved to JSON")
    
    # Clean up
    state.clear_all()
    print("✓ State cleared")
    
    print("\n✅ All HospitalState tests passed!")
