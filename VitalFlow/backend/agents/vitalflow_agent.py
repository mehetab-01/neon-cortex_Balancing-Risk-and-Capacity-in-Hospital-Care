"""
VitalFlow Autonomous Agent - The Brain of the Hospital.

This is the main decision loop that continuously:
1. OBSERVE - Monitor vitals, beds, staff, ambulances, CCTV
2. REASON - Analyze risks, predict capacity issues, identify critical patients
3. DECIDE - Determine appropriate action
4. ACT - Execute decisions (alert staff, swap beds, prepare equipment)
5. EXPLAIN - Log every decision with human-readable justification

CORE PRINCIPLE: If safety conflicts with efficiency, SAFETY ALWAYS WINS.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Patient, Bed, Staff, PatientStatus, BedType, StaffRole
from shared.utils import get_enum_value
from shared.events import event_bus, EventType
from backend.core_logic.state import hospital_state
from backend.core_logic.bed_manager import bed_manager
from backend.core_logic.staff_manager import staff_manager
from backend.core_logic.triage_engine import triage_engine
from backend.core_logic.emergency_protocols import emergency_protocol_engine
from backend.core_logic.ambulance_manager import ambulance_manager
from backend.core_logic.billing_agent import billing_agent


class ActionType(str, Enum):
    """Types of actions the agent can take"""
    OBSERVE_ONLY = "Observe Only"
    ESCALATE_CARE = "Escalate Care"
    SWAP_BEDS = "Swap Beds"
    ALERT_STAFF = "Alert Staff"
    PREPARE_EQUIPMENT = "Prepare Equipment"
    DIVERT_HOSPITAL = "Divert to Another Hospital"
    TRIGGER_CODE = "Trigger Emergency Code"
    ASSIGN_STAFF = "Assign Staff"
    UPDATE_PRIORITY = "Update Priority"
    REQUEST_APPROVAL = "Request Doctor Approval"


class AlertSeverity(str, Enum):
    """Severity levels for alerts"""
    INFO = "Info"
    WARNING = "Warning"
    URGENT = "Urgent"
    CRITICAL = "Critical"
    CODE_BLUE = "Code Blue"


@dataclass
class AgentObservation:
    """Snapshot of hospital state at observation time"""
    timestamp: datetime
    
    # Patient observations
    critical_patients: List[Dict] = field(default_factory=list)
    worsening_patients: List[Dict] = field(default_factory=list)
    unassigned_patients: List[Dict] = field(default_factory=list)
    
    # Bed observations
    icu_occupancy: float = 0.0
    er_occupancy: float = 0.0
    total_occupancy: float = 0.0
    beds_available: Dict = field(default_factory=dict)
    
    # Staff observations
    fatigued_staff: List[Dict] = field(default_factory=list)
    available_doctors: int = 0
    available_nurses: int = 0
    
    # Ambulance observations
    incoming_ambulances: List[Dict] = field(default_factory=list)
    ambulances_needing_preclearance: List[Dict] = field(default_factory=list)
    
    # CCTV/Alert observations
    fall_alerts: List[Dict] = field(default_factory=list)
    
    # Overall risk assessment
    risk_level: str = "Normal"
    concerns: List[str] = field(default_factory=list)


@dataclass
class AgentDecision:
    """A decision made by the agent"""
    decision_id: str
    timestamp: datetime
    action_type: ActionType
    severity: AlertSeverity
    target: str  # Patient ID, Bed ID, Staff ID, etc.
    reason: str
    details: Dict = field(default_factory=dict)
    requires_approval: bool = False
    approved_by: Optional[str] = None
    executed: bool = False
    outcome: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action_type.value,
            "severity": self.severity.value,
            "target": self.target,
            "reason": self.reason,
            "details": self.details,
            "requires_approval": self.requires_approval,
            "executed": self.executed,
            "outcome": self.outcome
        }


class VitalFlowAgent:
    """
    The autonomous brain of the hospital.
    
    Mission: Balance patient risk, bed capacity, staff workload, 
    and time-critical emergencies while care is IN PROGRESS.
    
    Primary Objectives:
    → SAVE LIVES
    → REDUCE DELAYS
    → PREVENT STAFF OVERLOAD
    → MAINTAIN FULL TRANSPARENCY
    """
    
    def __init__(self):
        self.is_running = False
        self.loop_interval_seconds = 5  # Check every 5 seconds
        self.decision_counter = 0
        self.decisions: List[AgentDecision] = []
        self.pending_approvals: List[AgentDecision] = []
        self._thread: Optional[threading.Thread] = None
        
        # Thresholds
        self.CRITICAL_SPO2 = 88
        self.CRITICAL_HR_LOW = 45
        self.CRITICAL_HR_HIGH = 140
        self.WORSENING_THRESHOLD = 3  # SpO2 drop of 3% triggers concern
        self.ICU_CAPACITY_THRESHOLD = 80  # 80% triggers pre-emptive action
    
    def _generate_decision_id(self) -> str:
        """Generate unique decision ID"""
        self.decision_counter += 1
        return f"DEC-{datetime.now().strftime('%Y%m%d')}-{self.decision_counter:04d}"
    
    # ============== OBSERVE ==============
    def observe(self) -> AgentObservation:
        """
        OBSERVE phase: Gather all relevant hospital state data.
        
        Monitors:
        - Patient vitals (SpO2, HR, BP, status)
        - Bed occupancy
        - Staff availability and fatigue
        - Incoming ambulances
        - CCTV events
        """
        obs = AgentObservation(timestamp=datetime.now())
        
        # ===== PATIENT OBSERVATIONS =====
        for patient in hospital_state.patients.values():
            status_str = get_enum_value(patient.status)
            
            # Critical patients
            if status_str == "Critical" or patient.spo2 < self.CRITICAL_SPO2:
                obs.critical_patients.append({
                    "id": patient.id,
                    "name": patient.name,
                    "status": status_str,
                    "spo2": patient.spo2,
                    "heart_rate": patient.heart_rate,
                    "bed_id": patient.bed_id,
                    "has_doctor": patient.assigned_doctor_id is not None
                })
            
            # Patients without bed or staff
            if not patient.bed_id or not patient.assigned_doctor_id:
                obs.unassigned_patients.append({
                    "id": patient.id,
                    "name": patient.name,
                    "status": status_str,
                    "bed_id": patient.bed_id,
                    "doctor_id": patient.assigned_doctor_id
                })
        
        # ===== BED OBSERVATIONS =====
        occupancy = bed_manager.get_bed_occupancy()
        
        for bed_type_str, data in occupancy.items():
            if data["total"] > 0:
                rate = (data["occupied"] / data["total"]) * 100
                if bed_type_str == "ICU":
                    obs.icu_occupancy = rate
                elif bed_type_str == "Emergency":
                    obs.er_occupancy = rate
                
                obs.beds_available[bed_type_str] = data["available"]
        
        stats = hospital_state.get_stats()
        obs.total_occupancy = stats.get("occupancy_rate", 0)
        
        # ===== STAFF OBSERVATIONS =====
        staff_summary = staff_manager.get_staff_status_summary()
        obs.available_doctors = staff_summary["doctors"]["available"]
        obs.available_nurses = staff_summary["nurses"]["available"]
        
        for warning in staff_summary.get("fatigue_warnings", []):
            obs.fatigued_staff.append(warning)
        
        # ===== AMBULANCE OBSERVATIONS =====
        active_ambulances = ambulance_manager.get_active_ambulances()
        obs.incoming_ambulances = active_ambulances
        
        for amb in active_ambulances:
            if amb["eta_minutes"] <= ambulance_manager.PRE_CLEARANCE_THRESHOLD_MINUTES:
                if amb["preclearance_status"] != "Fully Cleared":
                    obs.ambulances_needing_preclearance.append(amb)
        
        # ===== RISK ASSESSMENT =====
        obs.concerns = []
        
        if obs.critical_patients:
            obs.concerns.append(f"{len(obs.critical_patients)} critical patients")
        
        if obs.icu_occupancy >= self.ICU_CAPACITY_THRESHOLD:
            obs.concerns.append(f"ICU at {obs.icu_occupancy:.0f}% capacity")
        
        if obs.available_doctors == 0:
            obs.concerns.append("No doctors available")
        
        if obs.fatigued_staff:
            obs.concerns.append(f"{len(obs.fatigued_staff)} staff approaching fatigue")
        
        if obs.ambulances_needing_preclearance:
            obs.concerns.append(f"{len(obs.ambulances_needing_preclearance)} ambulances need pre-clearance")
        
        # Determine overall risk level
        if len([c for c in obs.concerns if "critical" in c.lower() or "No doctors" in c]) > 0:
            obs.risk_level = "HIGH"
        elif len(obs.concerns) >= 2:
            obs.risk_level = "ELEVATED"
        elif obs.concerns:
            obs.risk_level = "MODERATE"
        else:
            obs.risk_level = "NORMAL"
        
        return obs
    
    # ============== REASON ==============
    def reason(self, observation: AgentObservation) -> List[AgentDecision]:
        """
        REASON phase: Analyze observations and determine necessary actions.
        
        Reasoning includes:
        - Is someone becoming critical?
        - Will capacity fail soon?
        - Can a bed swap save a life?
        - Is staff safe to assign?
        - Is emergency protocol required?
        """
        decisions = []
        
        # ===== CRITICAL PATIENT REASONING =====
        for patient_data in observation.critical_patients:
            patient = hospital_state.patients.get(patient_data["id"])
            if not patient:
                continue
            
            # Check if patient needs ICU but isn't in one
            if patient.bed_id:
                bed = hospital_state.beds.get(patient.bed_id)
                bed_type = get_enum_value(bed.bed_type) if bed else None
                
                if bed_type != "ICU" and patient.spo2 < self.CRITICAL_SPO2:
                    decisions.append(AgentDecision(
                        decision_id=self._generate_decision_id(),
                        timestamp=datetime.now(),
                        action_type=ActionType.SWAP_BEDS,
                        severity=AlertSeverity.CRITICAL,
                        target=patient.id,
                        reason=f"Patient {patient.name} is CRITICAL (SpO2: {patient.spo2}%) but in {bed_type} bed. "
                               f"ICU transfer required.",
                        details={
                            "patient_id": patient.id,
                            "current_bed": patient.bed_id,
                            "required_bed_type": "ICU",
                            "spo2": patient.spo2,
                            "heart_rate": patient.heart_rate
                        },
                        requires_approval=True
                    ))
            
            # Check if patient needs emergency protocol
            protocol = emergency_protocol_engine.get_protocol_for_patient(patient)
            if protocol.get("detected"):
                if not patient_data.get("has_doctor"):
                    decisions.append(AgentDecision(
                        decision_id=self._generate_decision_id(),
                        timestamp=datetime.now(),
                        action_type=ActionType.ALERT_STAFF,
                        severity=AlertSeverity.CRITICAL,
                        target=patient.id,
                        reason=f"Emergency protocol {protocol['emergency_type']} detected for {patient.name}. "
                               f"No doctor assigned. Immediate attention required.",
                        details=protocol
                    ))
        
        # ===== CAPACITY REASONING =====
        if observation.icu_occupancy >= 100:
            # ICU full - preemptively find swap candidates
            swap_candidate = bed_manager.find_swap_candidate(BedType.ICU)
            if swap_candidate:
                decisions.append(AgentDecision(
                    decision_id=self._generate_decision_id(),
                    timestamp=datetime.now(),
                    action_type=ActionType.OBSERVE_ONLY,
                    severity=AlertSeverity.WARNING,
                    target="ICU",
                    reason=f"ICU at 100% capacity. Swap candidate identified: {swap_candidate.name} "
                           f"(Stability: {bed_manager._calculate_stability_score(swap_candidate)}/100). "
                           f"Ready for swap if critical patient arrives.",
                    details={
                        "swap_candidate_id": swap_candidate.id,
                        "swap_candidate_name": swap_candidate.name,
                        "stability_score": bed_manager._calculate_stability_score(swap_candidate)
                    }
                ))
        elif observation.icu_occupancy >= self.ICU_CAPACITY_THRESHOLD:
            decisions.append(AgentDecision(
                decision_id=self._generate_decision_id(),
                timestamp=datetime.now(),
                action_type=ActionType.OBSERVE_ONLY,
                severity=AlertSeverity.INFO,
                target="ICU",
                reason=f"ICU approaching capacity ({observation.icu_occupancy:.0f}%). "
                       f"Monitoring for potential swap needs."
            ))
        
        # ===== UNASSIGNED PATIENT REASONING =====
        for patient_data in observation.unassigned_patients:
            if not patient_data.get("doctor_id") and observation.available_doctors > 0:
                decisions.append(AgentDecision(
                    decision_id=self._generate_decision_id(),
                    timestamp=datetime.now(),
                    action_type=ActionType.ASSIGN_STAFF,
                    severity=AlertSeverity.WARNING,
                    target=patient_data["id"],
                    reason=f"Patient {patient_data['name']} has no doctor assigned. "
                           f"{observation.available_doctors} doctors available."
                ))
        
        # ===== AMBULANCE REASONING =====
        for amb in observation.ambulances_needing_preclearance:
            decisions.append(AgentDecision(
                decision_id=self._generate_decision_id(),
                timestamp=datetime.now(),
                action_type=ActionType.PREPARE_EQUIPMENT,
                severity=AlertSeverity.URGENT,
                target=amb["ambulance_id"],
                reason=f"Ambulance {amb['ambulance_id']} arriving in {amb['eta_minutes']} minutes. "
                       f"Pre-clearance status: {amb['preclearance_status']}. Action required.",
                details=amb
            ))
        
        # ===== STAFF FATIGUE REASONING =====
        for staff_warning in observation.fatigued_staff:
            decisions.append(AgentDecision(
                decision_id=self._generate_decision_id(),
                timestamp=datetime.now(),
                action_type=ActionType.ALERT_STAFF,
                severity=AlertSeverity.WARNING,
                target=staff_warning["staff_id"],
                reason=f"Staff {staff_warning['name']} ({staff_warning['role']}) approaching fatigue limit. "
                       f"{staff_warning['warning']}. Consider relief."
            ))
        
        return decisions
    
    # ============== DECIDE ==============
    def decide(self, decisions: List[AgentDecision]) -> List[AgentDecision]:
        """
        DECIDE phase: Prioritize and validate decisions.
        
        Rules:
        - Safety always wins over efficiency
        - Irreversible actions require approval
        - Never hallucinate resources
        """
        # Sort by severity (most critical first)
        severity_order = {
            AlertSeverity.CODE_BLUE: 0,
            AlertSeverity.CRITICAL: 1,
            AlertSeverity.URGENT: 2,
            AlertSeverity.WARNING: 3,
            AlertSeverity.INFO: 4
        }
        
        decisions.sort(key=lambda d: severity_order.get(d.severity, 5))
        
        # Mark irreversible actions as requiring approval
        for decision in decisions:
            if decision.action_type in [ActionType.SWAP_BEDS, ActionType.DIVERT_HOSPITAL]:
                decision.requires_approval = True
        
        return decisions
    
    # ============== ACT ==============
    def act(self, decisions: List[AgentDecision]) -> List[Dict]:
        """
        ACT phase: Execute decisions.
        
        Actions:
        - Send notifications
        - Trigger voice alerts
        - Update system state
        - Assign tasks
        """
        results = []
        
        for decision in decisions:
            result = {"decision_id": decision.decision_id, "executed": False, "outcome": ""}
            
            if decision.requires_approval and not decision.approved_by:
                # Queue for approval
                self.pending_approvals.append(decision)
                result["outcome"] = "Queued for doctor/admin approval"
                
            elif decision.action_type == ActionType.OBSERVE_ONLY:
                result["executed"] = True
                result["outcome"] = "Observation logged"
                decision.executed = True
                
            elif decision.action_type == ActionType.ASSIGN_STAFF:
                # Auto-assign staff
                patient_id = decision.target
                patient = hospital_state.patients.get(patient_id)
                if patient:
                    staff_manager.assign_doctor_to_patient(patient)
                    result["executed"] = True
                    result["outcome"] = f"Doctor assigned to patient {patient_id}"
                    decision.executed = True
                    
            elif decision.action_type == ActionType.ALERT_STAFF:
                # Log alert (in real system, would send push notification)
                result["executed"] = True
                result["outcome"] = "Alert sent to relevant staff"
                decision.executed = True
                
                # Publish event
                event_bus.publish(EventType.STAFF_ALERT, {
                    "decision": decision.to_dict(),
                    "timestamp": datetime.now().isoformat()
                })
                
            elif decision.action_type == ActionType.PREPARE_EQUIPMENT:
                # Trigger pre-clearance for ambulance
                amb_id = decision.target
                result["executed"] = True
                result["outcome"] = f"Equipment preparation triggered for ambulance {amb_id}"
                decision.executed = True
                
            elif decision.action_type == ActionType.SWAP_BEDS and decision.approved_by:
                # Execute approved swap
                patient = hospital_state.patients.get(decision.target)
                if patient:
                    success, message = bed_manager.execute_swap(patient)
                    result["executed"] = success
                    result["outcome"] = message
                    decision.executed = success
                    decision.outcome = message
            
            results.append(result)
            decision.outcome = result["outcome"]
            self.decisions.append(decision)
        
        return results
    
    # ============== EXPLAIN ==============
    def explain(self, decisions: List[AgentDecision]) -> List[Dict]:
        """
        EXPLAIN phase: Generate human-readable explanations for all decisions.
        
        Trust logs include:
        - What happened
        - WHY it happened
        - Simple language doctors trust
        """
        explanations = []
        
        for decision in decisions:
            explanation = {
                "decision_id": decision.decision_id,
                "timestamp": decision.timestamp.isoformat(),
                "summary": f"[{decision.severity.value}] {decision.action_type.value}: {decision.target}",
                "reason": decision.reason,
                "action_taken": decision.outcome if decision.executed else "Pending approval",
                "trust_log": self._generate_trust_log(decision)
            }
            explanations.append(explanation)
            
            # Log to hospital state
            hospital_state.log_decision(
                f"AGENT_{decision.action_type.value.upper().replace(' ', '_')}",
                explanation["trust_log"],
                decision.to_dict()
            )
        
        return explanations
    
    def _generate_trust_log(self, decision: AgentDecision) -> str:
        """Generate human-readable trust log entry"""
        if decision.action_type == ActionType.SWAP_BEDS:
            return (f"VitalFlow detected that patient requires ICU care based on critical vitals. "
                    f"The system identified a stable patient who can be safely moved to general ward, "
                    f"freeing the ICU bed. This decision follows the Tetris protocol for optimal bed utilization "
                    f"while prioritizing patient safety.")
        
        elif decision.action_type == ActionType.ALERT_STAFF:
            if "fatigue" in decision.reason.lower():
                return (f"VitalFlow is monitoring staff fatigue levels to prevent burnout and ensure "
                        f"patient safety. This staff member is approaching the safe working hour limit "
                        f"and should be considered for relief.")
            return f"VitalFlow has generated this alert based on: {decision.reason}"
        
        elif decision.action_type == ActionType.PREPARE_EQUIPMENT:
            return (f"An ambulance is approaching and VitalFlow is pre-clearing resources "
                    f"to minimize delay upon arrival. Bed, staff, and equipment are being prepared "
                    f"based on the reported patient condition.")
        
        else:
            return f"VitalFlow decision: {decision.reason}"
    
    # ============== MAIN LOOP ==============
    def run_cycle(self) -> Dict:
        """
        Run one complete decision cycle:
        OBSERVE → REASON → DECIDE → ACT → EXPLAIN
        """
        cycle_start = datetime.now()
        
        # 1. OBSERVE
        observation = self.observe()
        
        # 2. REASON
        decisions = self.reason(observation)
        
        # 3. DECIDE
        decisions = self.decide(decisions)
        
        # 4. ACT
        results = self.act(decisions)
        
        # 5. EXPLAIN
        explanations = self.explain(decisions)
        
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        
        return {
            "cycle_time": cycle_start.isoformat(),
            "duration_seconds": round(cycle_duration, 3),
            "observation": {
                "risk_level": observation.risk_level,
                "concerns": observation.concerns,
                "critical_patients": len(observation.critical_patients),
                "icu_occupancy": observation.icu_occupancy,
                "available_doctors": observation.available_doctors
            },
            "decisions_made": len(decisions),
            "actions_executed": sum(1 for r in results if r["executed"]),
            "pending_approvals": len(self.pending_approvals),
            "explanations": explanations
        }
    
    def start(self):
        """Start the autonomous decision loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        hospital_state.log_decision(
            "AGENT_STARTED",
            "VitalFlow autonomous agent started. Monitoring hospital in real-time.",
            {"interval_seconds": self.loop_interval_seconds}
        )
    
    def stop(self):
        """Stop the autonomous decision loop"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=10)
        
        hospital_state.log_decision(
            "AGENT_STOPPED",
            "VitalFlow autonomous agent stopped.",
            {}
        )
    
    def _run_loop(self):
        """Internal loop runner"""
        while self.is_running:
            try:
                self.run_cycle()
            except Exception as e:
                hospital_state.log_decision(
                    "AGENT_ERROR",
                    f"Error in decision cycle: {str(e)}",
                    {"error": str(e)}
                )
            
            time.sleep(self.loop_interval_seconds)
    
    def approve_decision(self, decision_id: str, approved_by: str) -> Dict:
        """Approve a pending decision"""
        for decision in self.pending_approvals:
            if decision.decision_id == decision_id:
                decision.approved_by = approved_by
                self.pending_approvals.remove(decision)
                
                # Execute the approved decision
                results = self.act([decision])
                
                hospital_state.log_decision(
                    "DECISION_APPROVED",
                    f"Decision {decision_id} approved by {approved_by}",
                    {"decision": decision.to_dict(), "approved_by": approved_by}
                )
                
                return {
                    "success": True,
                    "decision_id": decision_id,
                    "approved_by": approved_by,
                    "result": results[0] if results else None
                }
        
        return {"success": False, "error": "Decision not found in pending approvals"}
    
    def reject_decision(self, decision_id: str, rejected_by: str, reason: str) -> Dict:
        """Reject a pending decision"""
        for decision in self.pending_approvals:
            if decision.decision_id == decision_id:
                self.pending_approvals.remove(decision)
                decision.outcome = f"Rejected by {rejected_by}: {reason}"
                self.decisions.append(decision)
                
                hospital_state.log_decision(
                    "DECISION_REJECTED",
                    f"Decision {decision_id} rejected by {rejected_by}. Reason: {reason}",
                    {"decision_id": decision_id, "rejected_by": rejected_by, "reason": reason}
                )
                
                return {"success": True, "decision_id": decision_id}
        
        return {"success": False, "error": "Decision not found"}
    
    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "is_running": self.is_running,
            "total_decisions": len(self.decisions),
            "pending_approvals": len(self.pending_approvals),
            "loop_interval_seconds": self.loop_interval_seconds,
            "recent_decisions": [d.to_dict() for d in self.decisions[-10:]],
            "pending": [d.to_dict() for d in self.pending_approvals]
        }
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get list of decisions awaiting approval"""
        return [d.to_dict() for d in self.pending_approvals]


# Singleton instance
vitalflow_agent = VitalFlowAgent()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing VitalFlow Agent...")
    print("=" * 60)
    
    # Reset state
    hospital_state.clear_all()
    
    # Setup test environment
    from shared.models import Bed, Staff
    
    # Add beds
    for i in range(3):
        bed = Bed(id=f"ICU-0{i+1}", bed_type=BedType.ICU, ward="ICU", floor=1)
        hospital_state.add_bed(bed)
    for i in range(2):
        bed = Bed(id=f"ER-0{i+1}", bed_type=BedType.EMERGENCY, ward="ER", floor=1)
        hospital_state.add_bed(bed)
    for i in range(4):
        bed = Bed(id=f"GEN-0{i+1}", bed_type=BedType.GENERAL, ward="General", floor=1)
        hospital_state.add_bed(bed)
    
    # Add staff
    doctors = [
        Staff(id="D001", name="Dr. Sharma", role=StaffRole.DOCTOR, specialization="Cardiology"),
        Staff(id="D002", name="Dr. Patel", role=StaffRole.DOCTOR, specialization="Emergency"),
    ]
    nurses = [
        Staff(id="N001", name="Nurse Priya", role=StaffRole.NURSE),
        Staff(id="N002", name="Nurse Anita", role=StaffRole.NURSE),
    ]
    
    for s in doctors + nurses:
        hospital_state.add_staff(s)
        staff_manager.punch_in(s.id)
    
    # Add patients with varying conditions
    patients = [
        Patient(id="P001", name="Critical Patient", age=60, status=PatientStatus.CRITICAL,
                spo2=85, heart_rate=140, diagnosis="Heart Attack", bed_id="ER-01"),
        Patient(id="P002", name="Stable Patient 1", age=45, status=PatientStatus.STABLE,
                spo2=97, heart_rate=72, diagnosis="Post-surgery", bed_id="ICU-01"),
        Patient(id="P003", name="Stable Patient 2", age=50, status=PatientStatus.STABLE,
                spo2=96, heart_rate=75, diagnosis="Observation", bed_id="ICU-02"),
    ]
    
    for p in patients:
        hospital_state.add_patient(p)
        bed_manager.assign_patient_to_bed(p.id, p.bed_id)
    
    print("📋 Setup: 9 beds, 4 staff, 3 patients (1 critical in ER, 2 stable in ICU)")
    
    # Run one decision cycle
    print("\n🧠 Running VitalFlow Decision Cycle...")
    result = vitalflow_agent.run_cycle()
    
    print(f"\n📊 Cycle Results:")
    print(f"   Risk Level: {result['observation']['risk_level']}")
    print(f"   Concerns: {result['observation']['concerns']}")
    print(f"   Decisions Made: {result['decisions_made']}")
    print(f"   Actions Executed: {result['actions_executed']}")
    print(f"   Pending Approvals: {result['pending_approvals']}")
    
    print("\n📜 Explanations:")
    for exp in result['explanations']:
        print(f"\n   [{exp['summary']}]")
        print(f"   Reason: {exp['reason'][:100]}...")
        print(f"   Trust Log: {exp['trust_log'][:100]}...")
    
    # Check pending approvals
    pending = vitalflow_agent.get_pending_approvals()
    if pending:
        print(f"\n⏳ Pending Approvals: {len(pending)}")
        for p in pending:
            print(f"   - {p['decision_id']}: {p['reason'][:60]}...")
            
            # Simulate approval
            approval = vitalflow_agent.approve_decision(p['decision_id'], "Dr. Admin")
            print(f"   → Approved by Dr. Admin: {approval['success']}")
    
    print("\n" + "=" * 60)
    print("✅ VitalFlow Agent Test Complete!")
