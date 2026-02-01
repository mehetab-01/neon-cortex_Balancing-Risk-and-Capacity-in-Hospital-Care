"""
Ambulance Management for VitalFlow AI.
Tracks ambulance GPS, ETA, pre-clearance logic, and hospital diversion.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Patient, PatientStatus, Ambulance, BedType
from shared.utils import get_enum_value
from .state import hospital_state
from .bed_manager import bed_manager
from .staff_manager import staff_manager


class AmbulanceStatus(str, Enum):
    """Ambulance operational status"""
    AVAILABLE = "Available"
    DISPATCHED = "Dispatched"
    EN_ROUTE = "En Route"
    ON_SCENE = "On Scene"
    TRANSPORTING = "Transporting"
    AT_HOSPITAL = "At Hospital"
    OUT_OF_SERVICE = "Out of Service"


class PreClearanceStatus(str, Enum):
    """Pre-clearance status for incoming ambulance"""
    PENDING = "Pending"
    BED_RESERVED = "Bed Reserved"
    STAFF_ASSIGNED = "Staff Assigned"
    EQUIPMENT_READY = "Equipment Ready"
    FULLY_CLEARED = "Fully Cleared"
    DIVERTED = "Diverted to Another Hospital"
    FAILED = "Failed - No Capacity"


@dataclass
class AmbulanceTracking:
    """Real-time ambulance tracking data"""
    ambulance_id: str
    patient_info: Optional[Dict] = None
    status: AmbulanceStatus = AmbulanceStatus.AVAILABLE
    eta_minutes: int = 0
    gps_lat: float = 0.0
    gps_lng: float = 0.0
    destination_hospital: str = "VitalFlow General"
    dispatch_time: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    
    # Pre-clearance tracking
    preclearance_status: PreClearanceStatus = PreClearanceStatus.PENDING
    reserved_bed_id: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    assigned_nurse_id: Optional[str] = None
    equipment_prepared: List[str] = field(default_factory=list)
    
    # Communication log
    alerts_sent: List[Dict] = field(default_factory=list)


class AmbulanceManager:
    """
    Manages ambulance tracking and pre-clearance logic.
    
    Key Features:
    - Real-time ETA tracking
    - Automatic pre-clearance at T-10 minutes
    - Bed reservation and swap if needed
    - Staff pre-assignment
    - Equipment preparation
    - Hospital diversion if unsafe
    """
    
    PRE_CLEARANCE_THRESHOLD_MINUTES = 10  # Start pre-clearance at T-10 min
    CRITICAL_THRESHOLD_MINUTES = 5  # Escalate at T-5 min
    
    def __init__(self):
        self.active_ambulances: Dict[str, AmbulanceTracking] = {}
        self.completed_transports: List[Dict] = []
    
    def register_ambulance(self, ambulance_id: str, 
                          patient_info: Dict,
                          eta_minutes: int,
                          gps_lat: float = 0.0,
                          gps_lng: float = 0.0) -> AmbulanceTracking:
        """
        Register an incoming ambulance with patient information.
        
        Args:
            ambulance_id: Unique ambulance identifier
            patient_info: Dict with patient details (name, age, condition, vitals)
            eta_minutes: Estimated time of arrival in minutes
            gps_lat: GPS latitude
            gps_lng: GPS longitude
            
        Returns:
            AmbulanceTracking object
        """
        now = datetime.now()
        
        tracking = AmbulanceTracking(
            ambulance_id=ambulance_id,
            patient_info=patient_info,
            status=AmbulanceStatus.TRANSPORTING,
            eta_minutes=eta_minutes,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            dispatch_time=now,
            estimated_arrival=now + timedelta(minutes=eta_minutes)
        )
        
        self.active_ambulances[ambulance_id] = tracking
        
        hospital_state.log_decision(
            "AMBULANCE_REGISTERED",
            f"Ambulance {ambulance_id} registered. ETA: {eta_minutes} min. "
            f"Patient: {patient_info.get('name', 'Unknown')} - {patient_info.get('condition', 'Unknown')}",
            {
                "ambulance_id": ambulance_id,
                "eta_minutes": eta_minutes,
                "patient_info": patient_info
            }
        )
        
        # Check if pre-clearance should start immediately
        if eta_minutes <= self.PRE_CLEARANCE_THRESHOLD_MINUTES:
            self._initiate_preclearance(ambulance_id)
        
        return tracking
    
    def update_eta(self, ambulance_id: str, new_eta_minutes: int, 
                   gps_lat: float = None, gps_lng: float = None) -> bool:
        """
        Update ambulance ETA and GPS position.
        
        Args:
            ambulance_id: Ambulance ID
            new_eta_minutes: Updated ETA
            gps_lat: Updated GPS latitude
            gps_lng: Updated GPS longitude
            
        Returns:
            Success status
        """
        if ambulance_id not in self.active_ambulances:
            return False
        
        tracking = self.active_ambulances[ambulance_id]
        old_eta = tracking.eta_minutes
        tracking.eta_minutes = new_eta_minutes
        tracking.estimated_arrival = datetime.now() + timedelta(minutes=new_eta_minutes)
        
        if gps_lat is not None:
            tracking.gps_lat = gps_lat
        if gps_lng is not None:
            tracking.gps_lng = gps_lng
        
        # Check if pre-clearance should start
        if old_eta > self.PRE_CLEARANCE_THRESHOLD_MINUTES and \
           new_eta_minutes <= self.PRE_CLEARANCE_THRESHOLD_MINUTES:
            self._initiate_preclearance(ambulance_id)
        
        # Escalate if critical threshold reached
        if new_eta_minutes <= self.CRITICAL_THRESHOLD_MINUTES:
            self._escalate_preclearance(ambulance_id)
        
        return True
    
    def _initiate_preclearance(self, ambulance_id: str) -> Dict:
        """
        Initiate pre-clearance process at T-10 minutes.
        
        Steps:
        1. Predict required bed type
        2. Reserve or swap bed
        3. Assign doctor and nurse
        4. Prepare emergency equipment
        """
        if ambulance_id not in self.active_ambulances:
            return {"success": False, "error": "Ambulance not found"}
        
        tracking = self.active_ambulances[ambulance_id]
        patient_info = tracking.patient_info or {}
        result = {"ambulance_id": ambulance_id, "steps": []}
        
        # Step 1: Determine required bed type
        condition = patient_info.get("condition", "").lower()
        spo2 = patient_info.get("spo2", 95)
        
        if "critical" in condition or spo2 < 88:
            required_bed_type = BedType.ICU
        elif "serious" in condition or spo2 < 92:
            required_bed_type = BedType.EMERGENCY
        else:
            required_bed_type = BedType.GENERAL
        
        result["steps"].append({
            "action": "BED_TYPE_DETERMINED",
            "bed_type": get_enum_value(required_bed_type),
            "reason": f"Based on condition: {condition}, SpO2: {spo2}"
        })
        
        # Step 2: Reserve bed (or trigger swap)
        available_beds = bed_manager.get_available_beds(required_bed_type)
        
        if available_beds:
            # Direct reservation
            bed = available_beds[0]
            tracking.reserved_bed_id = bed.id
            tracking.preclearance_status = PreClearanceStatus.BED_RESERVED
            result["steps"].append({
                "action": "BED_RESERVED",
                "bed_id": bed.id,
                "method": "direct"
            })
        else:
            # Need to swap - create temporary patient for swap logic
            temp_patient = Patient(
                id=f"AMB-{ambulance_id}",
                name=patient_info.get("name", "Incoming Patient"),
                age=patient_info.get("age", 50),
                status=PatientStatus.CRITICAL if required_bed_type == BedType.ICU else PatientStatus.SERIOUS,
                spo2=spo2,
                heart_rate=patient_info.get("heart_rate", 100),
                diagnosis=patient_info.get("condition", "Emergency")
            )
            
            # Check if swap is possible
            swap_candidate = bed_manager.find_swap_candidate(required_bed_type)
            if swap_candidate:
                result["steps"].append({
                    "action": "SWAP_PREPARED",
                    "swap_candidate": swap_candidate.name,
                    "reason": "ICU full, stable patient identified for transfer"
                })
                tracking.preclearance_status = PreClearanceStatus.BED_RESERVED
            else:
                # Hospital cannot accommodate - consider diversion
                result["steps"].append({
                    "action": "CAPACITY_ISSUE",
                    "reason": "No beds available and no swap candidates"
                })
                tracking.preclearance_status = PreClearanceStatus.FAILED
        
        # Step 3: Assign staff
        available_doctors = staff_manager.get_available_doctors()
        if available_doctors:
            # Find best doctor for this case
            doctor = available_doctors[0]
            tracking.assigned_doctor_id = doctor.id
            result["steps"].append({
                "action": "DOCTOR_ASSIGNED",
                "doctor_id": doctor.id,
                "doctor_name": doctor.name,
                "specialization": doctor.specialization
            })
        
        available_nurses = staff_manager.get_available_nurses()
        if available_nurses:
            nurse = available_nurses[0]
            tracking.assigned_nurse_id = nurse.id
            result["steps"].append({
                "action": "NURSE_ASSIGNED",
                "nurse_id": nurse.id,
                "nurse_name": nurse.name
            })
        
        if tracking.assigned_doctor_id and tracking.assigned_nurse_id:
            tracking.preclearance_status = PreClearanceStatus.STAFF_ASSIGNED
        
        # Step 4: Prepare equipment
        equipment_list = self._get_required_equipment(condition)
        tracking.equipment_prepared = equipment_list
        result["steps"].append({
            "action": "EQUIPMENT_PREPARED",
            "items": equipment_list
        })
        
        if tracking.reserved_bed_id and tracking.assigned_doctor_id:
            tracking.preclearance_status = PreClearanceStatus.FULLY_CLEARED
        
        # Log the pre-clearance
        hospital_state.log_decision(
            "PRECLEARANCE_INITIATED",
            f"Pre-clearance started for ambulance {ambulance_id}. "
            f"Bed: {tracking.reserved_bed_id or 'SWAP NEEDED'}, "
            f"Doctor: {tracking.assigned_doctor_id or 'PENDING'}",
            result
        )
        
        tracking.alerts_sent.append({
            "time": datetime.now().isoformat(),
            "type": "PRECLEARANCE",
            "details": result
        })
        
        return result
    
    def _escalate_preclearance(self, ambulance_id: str):
        """Escalate at T-5 minutes - ensure everything is ready"""
        if ambulance_id not in self.active_ambulances:
            return
        
        tracking = self.active_ambulances[ambulance_id]
        
        if tracking.preclearance_status != PreClearanceStatus.FULLY_CLEARED:
            hospital_state.log_decision(
                "PRECLEARANCE_ESCALATION",
                f"⚠️ URGENT: Ambulance {ambulance_id} arriving in {tracking.eta_minutes} min "
                f"but pre-clearance incomplete. Status: {tracking.preclearance_status.value}",
                {"ambulance_id": ambulance_id, "status": tracking.preclearance_status.value}
            )
    
    def _get_required_equipment(self, condition: str) -> List[str]:
        """Get required equipment based on condition"""
        condition = condition.lower()
        
        base_equipment = [
            "Vital signs monitor",
            "IV stand and supplies",
            "Oxygen supply"
        ]
        
        if "cardiac" in condition or "heart" in condition or "chest pain" in condition:
            return base_equipment + [
                "ECG machine",
                "Defibrillator",
                "Crash cart",
                "Aspirin",
                "Nitroglycerin"
            ]
        elif "stroke" in condition:
            return base_equipment + [
                "CT scan preparation",
                "Blood pressure medications",
                "Neuro assessment tools"
            ]
        elif "trauma" in condition or "accident" in condition:
            return base_equipment + [
                "Trauma kit",
                "Blood products on standby",
                "Surgical instruments",
                "C-spine collar"
            ]
        elif "respiratory" in condition or "breathing" in condition:
            return base_equipment + [
                "Nebulizer",
                "BiPAP machine",
                "Intubation tray",
                "Ventilator on standby"
            ]
        else:
            return base_equipment + ["Emergency cart"]
    
    def check_hospital_capacity(self) -> Dict:
        """
        Check if hospital can safely accept new emergency patients.
        
        Returns:
            Dict with capacity status and diversion recommendation
        """
        stats = hospital_state.get_stats()
        occupancy = bed_manager.get_bed_occupancy()
        staff_summary = staff_manager.get_staff_summary()
        
        icu_occupancy = occupancy.get("ICU", {})
        icu_available = icu_occupancy.get("available", 0)
        
        emergency_occupancy = occupancy.get("Emergency", {})
        er_available = emergency_occupancy.get("available", 0)
        
        doctors_available = staff_summary["doctors"]["available"]
        nurses_available = staff_summary["nurses"]["available"]
        
        # Determine if hospital is safe for new patients
        is_safe = True
        concerns = []
        
        if icu_available == 0:
            concerns.append("ICU at full capacity")
            # Check if swap is possible
            swap_candidate = bed_manager.find_swap_candidate(BedType.ICU)
            if not swap_candidate:
                is_safe = False
                concerns.append("No stable patients for ICU swap")
        
        if er_available == 0:
            concerns.append("Emergency room at full capacity")
        
        if doctors_available == 0:
            is_safe = False
            concerns.append("No doctors available")
        
        if nurses_available < 2:
            concerns.append("Limited nursing staff")
        
        # Check for fatigue
        if staff_summary["fatigue_warnings"]:
            concerns.append(f"{len(staff_summary['fatigue_warnings'])} staff approaching fatigue limit")
        
        return {
            "is_safe": is_safe,
            "can_accept_critical": icu_available > 0 or bed_manager.find_swap_candidate(BedType.ICU) is not None,
            "can_accept_emergency": er_available > 0,
            "concerns": concerns,
            "recommendation": "ACCEPT" if is_safe else "CONSIDER_DIVERSION",
            "icu_available": icu_available,
            "er_available": er_available,
            "doctors_available": doctors_available,
            "nurses_available": nurses_available
        }
    
    def recommend_diversion(self, ambulance_id: str) -> Dict:
        """
        Recommend diversion to another hospital if unsafe.
        
        Args:
            ambulance_id: Ambulance ID
            
        Returns:
            Diversion recommendation
        """
        capacity = self.check_hospital_capacity()
        
        if capacity["is_safe"]:
            return {
                "divert": False,
                "message": "Hospital can safely accept patient",
                "ambulance_id": ambulance_id
            }
        
        # Simulate nearby hospitals (in real system, this would query city network)
        nearby_hospitals = [
            {"name": "City General Hospital", "distance_km": 3.2, "icu_available": 2},
            {"name": "Apollo Emergency Center", "distance_km": 5.1, "icu_available": 1},
            {"name": "Government Medical College", "distance_km": 7.8, "icu_available": 3}
        ]
        
        # Find best alternative
        best_option = min(nearby_hospitals, key=lambda h: h["distance_km"])
        
        if ambulance_id in self.active_ambulances:
            self.active_ambulances[ambulance_id].preclearance_status = PreClearanceStatus.DIVERTED
        
        hospital_state.log_decision(
            "DIVERSION_RECOMMENDED",
            f"⚠️ Recommending diversion of ambulance {ambulance_id} to {best_option['name']}. "
            f"Reason: {', '.join(capacity['concerns'])}",
            {
                "ambulance_id": ambulance_id,
                "recommended_hospital": best_option,
                "concerns": capacity["concerns"]
            }
        )
        
        return {
            "divert": True,
            "ambulance_id": ambulance_id,
            "reason": capacity["concerns"],
            "recommended_hospital": best_option["name"],
            "distance_km": best_option["distance_km"],
            "icu_available_there": best_option["icu_available"],
            "message": f"Divert to {best_option['name']} ({best_option['distance_km']} km away)"
        }
    
    def ambulance_arrived(self, ambulance_id: str) -> Dict:
        """
        Handle ambulance arrival at hospital.
        
        Args:
            ambulance_id: Ambulance ID
            
        Returns:
            Arrival handling result
        """
        if ambulance_id not in self.active_ambulances:
            return {"success": False, "error": "Ambulance not tracked"}
        
        tracking = self.active_ambulances[ambulance_id]
        tracking.status = AmbulanceStatus.AT_HOSPITAL
        
        result = {
            "ambulance_id": ambulance_id,
            "arrival_time": datetime.now().isoformat(),
            "preclearance_status": tracking.preclearance_status.value,
            "reserved_bed": tracking.reserved_bed_id,
            "assigned_doctor": tracking.assigned_doctor_id,
            "assigned_nurse": tracking.assigned_nurse_id,
            "equipment_ready": tracking.equipment_prepared
        }
        
        hospital_state.log_decision(
            "AMBULANCE_ARRIVED",
            f"Ambulance {ambulance_id} arrived. Bed: {tracking.reserved_bed_id}, "
            f"Doctor: {tracking.assigned_doctor_id}",
            result
        )
        
        # Move to completed
        self.completed_transports.append({
            "ambulance_id": ambulance_id,
            "tracking": tracking,
            "arrival_time": datetime.now()
        })
        
        del self.active_ambulances[ambulance_id]
        
        return result
    
    def get_active_ambulances(self) -> List[Dict]:
        """Get all active ambulance trackings"""
        return [
            {
                "ambulance_id": t.ambulance_id,
                "status": t.status.value,
                "eta_minutes": t.eta_minutes,
                "patient_info": t.patient_info,
                "preclearance_status": t.preclearance_status.value,
                "reserved_bed": t.reserved_bed_id,
                "assigned_doctor": t.assigned_doctor_id,
                "gps": {"lat": t.gps_lat, "lng": t.gps_lng}
            }
            for t in self.active_ambulances.values()
        ]
    
    def get_ambulance_status(self, ambulance_id: str) -> Optional[Dict]:
        """Get status of specific ambulance"""
        if ambulance_id not in self.active_ambulances:
            return None
        
        t = self.active_ambulances[ambulance_id]
        return {
            "ambulance_id": t.ambulance_id,
            "status": t.status.value,
            "eta_minutes": t.eta_minutes,
            "estimated_arrival": t.estimated_arrival.isoformat() if t.estimated_arrival else None,
            "patient_info": t.patient_info,
            "preclearance_status": t.preclearance_status.value,
            "reserved_bed": t.reserved_bed_id,
            "assigned_doctor": t.assigned_doctor_id,
            "assigned_nurse": t.assigned_nurse_id,
            "equipment_prepared": t.equipment_prepared,
            "gps": {"lat": t.gps_lat, "lng": t.gps_lng},
            "alerts_sent": t.alerts_sent
        }


# Singleton instance
ambulance_manager = AmbulanceManager()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing Ambulance Manager...")
    print("=" * 60)
    
    # Reset state
    hospital_state.clear_all()
    
    # Setup beds and staff
    from shared.models import Bed, Staff, StaffRole
    
    for i in range(3):
        bed = Bed(id=f"ICU-0{i+1}", bed_type=BedType.ICU, ward="ICU", floor=1)
        hospital_state.add_bed(bed)
    for i in range(2):
        bed = Bed(id=f"ER-0{i+1}", bed_type=BedType.EMERGENCY, ward="ER", floor=1)
        hospital_state.add_bed(bed)
    
    doc = Staff(id="D001", name="Dr. Kumar", role=StaffRole.DOCTOR, specialization="Emergency")
    nurse = Staff(id="N001", name="Nurse Priya", role=StaffRole.NURSE)
    hospital_state.add_staff(doc)
    hospital_state.add_staff(nurse)
    staff_manager.punch_in("D001")
    staff_manager.punch_in("N001")
    
    print("\n📋 Setup: 3 ICU beds, 2 ER beds, 1 doctor, 1 nurse")
    
    # Test 1: Register ambulance
    print("\n🚑 TEST 1: Register incoming ambulance")
    tracking = ambulance_manager.register_ambulance(
        ambulance_id="AMB-101",
        patient_info={
            "name": "Ramesh Kumar",
            "age": 55,
            "condition": "Chest pain, suspected heart attack",
            "spo2": 88,
            "heart_rate": 120
        },
        eta_minutes=8,
        gps_lat=19.0760,
        gps_lng=72.8777
    )
    print(f"   Registered: {tracking.ambulance_id}")
    print(f"   ETA: {tracking.eta_minutes} minutes")
    print(f"   Pre-clearance: {tracking.preclearance_status.value}")
    
    # Test 2: Check capacity
    print("\n🏥 TEST 2: Hospital capacity check")
    capacity = ambulance_manager.check_hospital_capacity()
    print(f"   Safe to accept: {capacity['is_safe']}")
    print(f"   ICU available: {capacity['icu_available']}")
    print(f"   Doctors available: {capacity['doctors_available']}")
    
    # Test 3: Ambulance arrives
    print("\n🏥 TEST 3: Ambulance arrival")
    result = ambulance_manager.ambulance_arrived("AMB-101")
    print(f"   Bed assigned: {result['reserved_bed']}")
    print(f"   Doctor assigned: {result['assigned_doctor']}")
    
    print("\n" + "=" * 60)
    print("✅ Ambulance Manager Test Complete!")
