"""
Core bed management with the "Tetris" swapping algorithm.
This is the heart of VitalFlow's intelligent bed allocation system.

The Tetris Algorithm:
- When ICU is full and a critical patient arrives
- Find the most stable patient currently in ICU
- Swap them to General Ward to free up ICU bed
- Assign the critical patient to the freed ICU bed
"""
import sys
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Patient, Bed, BedType, PatientStatus
from shared.utils import get_enum_value
from .state import hospital_state


class BedManager:
    """
    Manages all bed operations including the Tetris swapping algorithm.
    """
    
    def get_available_beds(self, bed_type: BedType = None) -> List[Bed]:
        """
        Get all available beds, optionally filtered by type.
        
        Args:
            bed_type: Optional BedType to filter by
            
        Returns:
            List of available Bed objects
        """
        available = []
        for bed in hospital_state.beds.values():
            if not bed.is_occupied:
                if bed_type is None or bed.bed_type == bed_type:
                    available.append(bed)
        return available
    
    def get_bed_occupancy(self) -> Dict[str, Dict[str, int]]:
        """
        Return occupancy stats by bed type.
        
        Returns:
            Dict with format: {bed_type: {total, occupied, available}}
        """
        stats = {}
        for bed_type in BedType:
            beds_of_type = [b for b in hospital_state.beds.values() 
                          if b.bed_type == bed_type or b.bed_type == bed_type.value]
            occupied = sum(1 for b in beds_of_type if b.is_occupied)
            stats[get_enum_value(bed_type)] = {
                "total": len(beds_of_type),
                "occupied": occupied,
                "available": len(beds_of_type) - occupied
            }
        return stats
    
    def get_recommended_bed_type(self, patient: Patient) -> BedType:
        """
        Determine the recommended bed type based on patient status.
        
        Args:
            patient: Patient object
            
        Returns:
            Recommended BedType
        """
        if patient.status == PatientStatus.CRITICAL:
            return BedType.ICU
        elif patient.status == PatientStatus.SERIOUS:
            # Serious patients prefer ICU but can use Emergency
            return BedType.ICU
        elif patient.status == PatientStatus.STABLE:
            return BedType.GENERAL
        elif patient.status == PatientStatus.RECOVERING:
            return BedType.GENERAL
        else:
            return BedType.GENERAL
    
    def find_best_bed(self, patient: Patient) -> Optional[Bed]:
        """
        Find the best bed for a patient based on their status.
        
        Priority order:
        - Critical -> ICU first, then Emergency
        - Serious -> ICU, Emergency, then General
        - Stable/Recovering -> General Ward
        
        Args:
            patient: Patient object
            
        Returns:
            Best available Bed or None if no beds available
        """
        status = patient.status
        
        # Define bed type priority based on patient status
        if status == PatientStatus.CRITICAL:
            priority_order = [BedType.ICU, BedType.EMERGENCY]
        elif status == PatientStatus.SERIOUS:
            priority_order = [BedType.ICU, BedType.EMERGENCY, BedType.GENERAL]
        else:
            priority_order = [BedType.GENERAL, BedType.EMERGENCY]
        
        # Try each bed type in priority order
        for bed_type in priority_order:
            available = self.get_available_beds(bed_type)
            if available:
                # Return first available bed of this type
                return available[0]
        
        return None
    
    def check_bed_available(self, bed_type: BedType) -> bool:
        """
        Check if any bed of given type is available.
        
        Args:
            bed_type: Type of bed to check
            
        Returns:
            True if at least one bed is available
        """
        return len(self.get_available_beds(bed_type)) > 0
    
    def assign_patient_to_bed(self, patient_id: str, bed_id: str) -> bool:
        """
        Assign a patient to a specific bed.
        
        Args:
            patient_id: ID of patient to assign
            bed_id: ID of bed to assign to
            
        Returns:
            True if assignment successful
        """
        patient = hospital_state.patients.get(patient_id)
        bed = hospital_state.beds.get(bed_id)
        
        if not patient or not bed:
            return False
        
        if bed.is_occupied and bed.patient_id != patient_id:
            return False  # Bed is occupied by someone else
        
        # Release old bed if patient was in one
        if patient.bed_id and patient.bed_id != bed_id:
            old_bed = hospital_state.beds.get(patient.bed_id)
            if old_bed:
                old_bed.is_occupied = False
                old_bed.patient_id = None
        
        # Assign to new bed
        bed.is_occupied = True
        bed.patient_id = patient_id
        patient.bed_id = bed_id
        
        hospital_state.save()
        return True
    
    def release_bed(self, bed_id: str) -> bool:
        """
        Release a bed (discharge/transfer).
        
        Args:
            bed_id: ID of bed to release
            
        Returns:
            True if release successful
        """
        bed = hospital_state.beds.get(bed_id)
        if not bed:
            return False
        
        # Clear patient's bed reference
        if bed.patient_id:
            patient = hospital_state.patients.get(bed.patient_id)
            if patient:
                patient.bed_id = None
        
        # Release the bed
        bed.is_occupied = False
        bed.patient_id = None
        bed.last_sanitized = datetime.now()
        
        hospital_state.save()
        return True
    
    # ============== THE TETRIS ALGORITHM ==============
    
    def _calculate_stability_score(self, patient: Patient) -> float:
        """
        Calculate how stable a patient is (0-100).
        Higher score = more stable = better candidate for downgrade to lower-care bed.
        
        Scoring:
        - Status-based: 0-40 points
        - SpO2-based: 0-30 points
        - Heart rate-based: 0-30 points
        
        Args:
            patient: Patient to evaluate
            
        Returns:
            Stability score (0-100)
        """
        score = 0.0
        
        # Status-based score (40 points max)
        status_scores = {
            PatientStatus.RECOVERING: 40,
            PatientStatus.STABLE: 30,
            PatientStatus.SERIOUS: 10,
            PatientStatus.CRITICAL: 0,
            PatientStatus.DISCHARGED: 50  # Should not be in bed anyway
        }
        score += status_scores.get(patient.status, 0)
        
        # SpO2-based score (30 points max)
        if patient.spo2 >= 98:
            score += 30
        elif patient.spo2 >= 95:
            score += 25
        elif patient.spo2 >= 92:
            score += 15
        elif patient.spo2 >= 90:
            score += 10
        elif patient.spo2 >= 85:
            score += 5
        # Below 85: 0 points
        
        # Heart rate-based score (30 points max)
        hr = patient.heart_rate
        if 60 <= hr <= 100:
            score += 30  # Normal range
        elif 55 <= hr <= 110:
            score += 20  # Slightly off
        elif 50 <= hr <= 120:
            score += 10  # Concerning but stable
        elif 45 <= hr <= 130:
            score += 5   # Needs monitoring
        # Outside these ranges: 0 points
        
        return score
    
    def find_swap_candidate(self, required_bed_type: BedType) -> Optional[Patient]:
        """
        Find the most stable patient in beds of required_type.
        This patient is the best candidate for moving OUT to make room.
        
        Priority for swapping (most stable first):
        1. RECOVERING patients with best vitals
        2. STABLE patients with good vitals (SpO2 > 95, HR 60-100)
        3. STABLE patients with acceptable vitals
        
        Args:
            required_bed_type: Type of bed we need to free up
            
        Returns:
            Best swap candidate Patient or None
        """
        candidates = []
        
        for bed in hospital_state.beds.values():
            # Only consider beds of the required type that are occupied
            if bed.bed_type == required_bed_type and bed.is_occupied:
                patient = hospital_state.patients.get(bed.patient_id)
                if patient:
                    # Don't swap critical patients
                    if patient.status == PatientStatus.CRITICAL:
                        continue
                    
                    score = self._calculate_stability_score(patient)
                    candidates.append((patient, score))
        
        if not candidates:
            return None
        
        # Sort by stability score (higher = more stable = better swap candidate)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Only return if the best candidate has reasonable stability
        best_candidate, best_score = candidates[0]
        if best_score >= 30:  # Minimum threshold for swapping
            return best_candidate
        
        return None
    
    def execute_swap(self, incoming_patient: Patient) -> Tuple[bool, str]:
        """
        THE CORE TETRIS OPERATION.
        
        Algorithm:
        1. Determine what bed type the incoming patient needs
        2. Try to find a direct bed first
        3. If no bed available, find most stable patient in that bed type
        4. Find available lower-level bed for the stable patient
        5. Execute the swap: stable patient → lower bed, incoming → freed bed
        
        Args:
            incoming_patient: Critical/serious patient needing a bed
            
        Returns:
            Tuple of (success, message)
        """
        # Determine required bed type
        if incoming_patient.status == PatientStatus.CRITICAL:
            required_type = BedType.ICU
            fallback_types = [BedType.EMERGENCY]
        elif incoming_patient.status == PatientStatus.SERIOUS:
            required_type = BedType.ICU
            fallback_types = [BedType.EMERGENCY, BedType.GENERAL]
        else:
            required_type = BedType.GENERAL
            fallback_types = [BedType.EMERGENCY]
        
        # Step 1: Try to find a direct bed
        available = self.get_available_beds(required_type)
        if available:
            success = self.assign_patient_to_bed(incoming_patient.id, available[0].id)
            if success:
                hospital_state.log_decision(
                    "DIRECT_ASSIGN",
                    f"Bed available, direct assignment to {available[0].id}",
                    {
                        "patient_id": incoming_patient.id,
                        "patient_name": incoming_patient.name,
                        "bed_id": available[0].id,
                        "bed_type": get_enum_value(required_type)
                    }
                )
                return True, f"Assigned to {available[0].id}"
        
        # Step 2: Try fallback bed types for non-critical patients
        if incoming_patient.status != PatientStatus.CRITICAL:
            for fallback_type in fallback_types:
                available = self.get_available_beds(fallback_type)
                if available:
                    success = self.assign_patient_to_bed(incoming_patient.id, available[0].id)
                    if success:
                        hospital_state.log_decision(
                            "FALLBACK_ASSIGN",
                            f"Primary bed type full, assigned to {get_enum_value(fallback_type)}",
                            {
                                "patient_id": incoming_patient.id,
                                "bed_id": available[0].id,
                                "preferred_type": get_enum_value(required_type),
                                "actual_type": get_enum_value(fallback_type)
                            }
                        )
                        return True, f"Assigned to {available[0].id} ({get_enum_value(fallback_type)})"
        
        # Step 3: No direct bed - initiate SWAP (only for critical/serious patients)
        if incoming_patient.status not in [PatientStatus.CRITICAL, PatientStatus.SERIOUS]:
            return False, "No beds available and patient not critical enough for swap"
        
        # Find swap candidate in the required bed type
        swap_candidate = self.find_swap_candidate(required_type)
        if not swap_candidate:
            # Try to find in fallback types
            for fallback_type in fallback_types:
                swap_candidate = self.find_swap_candidate(fallback_type)
                if swap_candidate:
                    required_type = fallback_type
                    break
        
        if not swap_candidate:
            hospital_state.log_decision(
                "SWAP_FAILED",
                "No stable patients available for swap",
                {
                    "patient_id": incoming_patient.id,
                    "required_type": get_enum_value(required_type)
                }
            )
            return False, "No stable patients available for swap"
        
        # Step 4: Find a lower-level bed for the swap candidate
        downgrade_types = [BedType.GENERAL, BedType.EMERGENCY]
        downgrade_bed = None
        
        for downgrade_type in downgrade_types:
            if downgrade_type != required_type:  # Don't move to same type
                available = self.get_available_beds(downgrade_type)
                if available:
                    downgrade_bed = available[0]
                    break
        
        if not downgrade_bed:
            hospital_state.log_decision(
                "SWAP_FAILED",
                "No lower-level beds available for swap",
                {
                    "patient_id": incoming_patient.id,
                    "swap_candidate": swap_candidate.id
                }
            )
            return False, "No lower-level beds available for swap"
        
        # Step 5: Execute the swap
        old_bed_id = swap_candidate.bed_id
        old_bed = hospital_state.beds.get(old_bed_id)
        
        if not old_bed:
            return False, "Swap candidate's bed not found"
        
        # Calculate stability score for logging
        stability_score = self._calculate_stability_score(swap_candidate)
        
        # Move stable patient to downgrade bed
        self.release_bed(old_bed_id)
        self.assign_patient_to_bed(swap_candidate.id, downgrade_bed.id)
        
        # Move critical patient to freed bed
        self.assign_patient_to_bed(incoming_patient.id, old_bed_id)
        
        # Log the decision with full details
        hospital_state.log_decision(
            "SWAP_EXECUTED",
            f"ICU full. Moved {swap_candidate.name} (Stability: {stability_score:.0f}/100) to {get_enum_value(downgrade_bed.bed_type)} to accommodate critical patient {incoming_patient.name} (SpO2: {incoming_patient.spo2}%, HR: {incoming_patient.heart_rate})",
            {
                "swapped_out_patient": swap_candidate.id,
                "swapped_out_name": swap_candidate.name,
                "swapped_out_stability": stability_score,
                "swapped_in_patient": incoming_patient.id,
                "swapped_in_name": incoming_patient.name,
                "freed_bed": old_bed_id,
                "downgrade_bed": downgrade_bed.id,
                "incoming_spo2": incoming_patient.spo2,
                "incoming_hr": incoming_patient.heart_rate
            }
        )
        
        return True, f"Swap executed: {swap_candidate.name} → {downgrade_bed.id}, {incoming_patient.name} → {old_bed_id}"
    
    def get_bed_status_summary(self) -> str:
        """
        Get a human-readable summary of bed status.
        
        Returns:
            Formatted string with bed status
        """
        occupancy = self.get_bed_occupancy()
        lines = ["=== BED STATUS SUMMARY ==="]
        
        for bed_type, stats in occupancy.items():
            available = stats['available']
            total = stats['total']
            status = "🔴 FULL" if available == 0 else f"🟢 {available}/{total}"
            lines.append(f"{bed_type}: {status}")
        
        return "\n".join(lines)


# Singleton instance
bed_manager = BedManager()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing BedManager with Tetris Algorithm...")
    
    # Reset state
    hospital_state.clear_all()
    
    # Setup: Create some beds
    beds_config = [
        ("ICU-01", BedType.ICU), ("ICU-02", BedType.ICU), ("ICU-03", BedType.ICU),
        ("ER-01", BedType.EMERGENCY), ("ER-02", BedType.EMERGENCY),
        ("GEN-01", BedType.GENERAL), ("GEN-02", BedType.GENERAL), ("GEN-03", BedType.GENERAL)
    ]
    
    for bed_id, bed_type in beds_config:
        bed = Bed(id=bed_id, bed_type=bed_type, ward=f"{bed_type.value} Ward", floor=1)
        hospital_state.add_bed(bed)
    
    print(f"✓ Created {len(hospital_state.beds)} beds")
    
    # Test 1: Check available beds
    available_icu = bed_manager.get_available_beds(BedType.ICU)
    assert len(available_icu) == 3, "Should have 3 ICU beds available"
    print("✓ Available beds check works")
    
    # Test 2: Add patients to fill ICU
    for i in range(3):
        patient = Patient(
            id=f"P-ICU-{i}",
            name=f"ICU Patient {i}",
            age=60,
            status=PatientStatus.STABLE,  # Stable patients in ICU
            spo2=96.0,
            heart_rate=80
        )
        hospital_state.add_patient(patient)
        bed_manager.assign_patient_to_bed(patient.id, f"ICU-0{i+1}")
    
    print("✓ Filled ICU with 3 stable patients")
    
    # Verify ICU is full
    available_icu = bed_manager.get_available_beds(BedType.ICU)
    assert len(available_icu) == 0, "ICU should be full"
    print("✓ ICU is now full")
    
    # Test 3: Calculate stability scores
    patient = hospital_state.patients.get("P-ICU-0")
    score = bed_manager._calculate_stability_score(patient)
    print(f"✓ Stability score for stable patient: {score}")
    assert score >= 60, "Stable patient with good vitals should have high score"
    
    # Test 4: Find swap candidate
    candidate = bed_manager.find_swap_candidate(BedType.ICU)
    assert candidate is not None, "Should find a swap candidate"
    print(f"✓ Found swap candidate: {candidate.name}")
    
    # Test 5: THE TETRIS SWAP
    critical_patient = Patient(
        id="P-CRITICAL-1",
        name="Critical Emergency",
        age=55,
        status=PatientStatus.CRITICAL,
        spo2=82.0,  # Dangerously low
        heart_rate=145,  # Very high
        diagnosis="Cardiac Arrest"
    )
    hospital_state.add_patient(critical_patient)
    
    success, message = bed_manager.execute_swap(critical_patient)
    print(f"✓ Swap result: {success} - {message}")
    
    assert success, "Swap should succeed"
    assert critical_patient.bed_id is not None, "Critical patient should have a bed"
    assert "ICU" in critical_patient.bed_id, "Critical patient should be in ICU"
    
    # Verify swap candidate was moved
    moved_patient = hospital_state.patients.get(candidate.id)
    assert "GEN" in moved_patient.bed_id or "ER" in moved_patient.bed_id, \
        "Swapped patient should be in General or ER"
    print(f"✓ Swapped patient moved to: {moved_patient.bed_id}")
    
    # Test 6: Occupancy stats
    occupancy = bed_manager.get_bed_occupancy()
    print(f"✓ Occupancy stats: {occupancy}")
    
    # Test 7: Bed status summary
    summary = bed_manager.get_bed_status_summary()
    print(summary)
    
    # Check decision log
    decisions = hospital_state.get_recent_decisions(5)
    print(f"\n✓ Decision log has {len(decisions)} entries")
    for d in decisions:
        print(f"  - {d['action']}: {d['reason'][:50]}...")
    
    # Clean up
    hospital_state.clear_all()
    
    print("\n✅ All BedManager tests passed!")
