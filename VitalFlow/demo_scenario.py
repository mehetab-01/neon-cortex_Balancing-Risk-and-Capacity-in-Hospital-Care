"""
VitalFlow AI - Demo Scenario for Judges
A step-by-step demonstration of the hospital command center's capabilities.

This module provides an interactive demo that showcases:
1. Continuous Patient Monitoring
2. AI-Driven Escalation
3. ICU Bed Allocation (Tetris Algorithm)
4. Ambulance Emergency Handling
5. Fall Detection via CCTV
6. Automated Billing
"""
import streamlit as st
import sys
import time
import random
from pathlib import Path
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ================= AUDIT LOGGER =================

class AuditLogger:
    """Real-time audit logging for transparency and accountability."""
    
    def __init__(self):
        self.logs: List[Dict] = []
    
    def log(self, action: str, reason: str, severity: str = "info"):
        """Log an action with timestamp and reason."""
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": action,
            "reason": reason,
            "severity": severity
        }
        self.logs.append(entry)
        return entry
    
    def get_recent(self, count: int = 10) -> List[Dict]:
        """Get most recent log entries."""
        return self.logs[-count:]
    
    def clear(self):
        """Clear all logs."""
        self.logs = []


# ================= CORE ENTITIES =================

@dataclass
class DemoPatient:
    """Patient entity for demo."""
    name: str
    location: str
    insurance: bool = True
    vitals_stream: deque = field(default_factory=lambda: deque(maxlen=5))
    risk: int = 0
    in_icu: bool = False
    services: List[str] = field(default_factory=list)
    medicines: List[str] = field(default_factory=list)
    spo2: int = 98
    heart_rate: int = 75
    bp: str = "120/80"
    
    def update_vitals(self, simulate_critical: bool = False):
        """Update vitals with simulated data."""
        if simulate_critical:
            vitals = random.randint(75, 95)  # High risk
        else:
            vitals = random.randint(30, 60)  # Normal
        
        self.vitals_stream.append(vitals)
        self.risk = int(sum(self.vitals_stream) / len(self.vitals_stream))
        
        # Update other vitals
        if self.risk > 70:
            self.spo2 = random.randint(85, 92)
            self.heart_rate = random.randint(110, 140)
            self.bp = f"{random.randint(150, 180)}/{random.randint(90, 110)}"
        else:
            self.spo2 = random.randint(95, 99)
            self.heart_rate = random.randint(60, 85)
            self.bp = f"{random.randint(110, 130)}/{random.randint(70, 85)}"


@dataclass
class DemoStaff:
    """Staff entity for demo."""
    name: str
    role: str
    active_cases: int = 0
    specialization: str = ""


@dataclass
class DemoBed:
    """Bed entity for demo."""
    bed_id: str
    bed_type: str = "ICU"
    patient: Optional[DemoPatient] = None


# ================= EMERGENCY PROTOCOL ENGINE =================

class EmergencyProtocolEngine:
    """AI-driven emergency protocol selection."""
    
    PROTOCOLS = {
        "heart_attack": {
            "name": "Cardiac Emergency Protocol",
            "medicines": ["Aspirin 325mg", "Nitroglycerin SL", "Heparin IV", "Morphine PRN"],
            "trolley": "Cardiac Crash Trolley",
            "equipment": ["Defibrillator", "ECG Monitor", "Oxygen Cylinder"],
            "ot_required": True,
            "priority": 1
        },
        "trauma": {
            "name": "Trauma Protocol",
            "medicines": ["IV Fluids 1L", "Tranexamic Acid", "Tetanus Toxoid", "Broad-spectrum Antibiotics"],
            "trolley": "Trauma Trolley",
            "equipment": ["Cervical Collar", "Splints", "Wound Care Kit"],
            "ot_required": True,
            "priority": 1
        },
        "stroke": {
            "name": "Stroke Protocol",
            "medicines": ["tPA (if eligible)", "Aspirin", "Antihypertensives"],
            "trolley": "Neuro Trolley",
            "equipment": ["CT Scanner Ready", "BP Monitor"],
            "ot_required": False,
            "priority": 1
        },
        "respiratory_failure": {
            "name": "Respiratory Emergency Protocol",
            "medicines": ["Bronchodilators", "Corticosteroids", "Oxygen"],
            "trolley": "Respiratory Trolley",
            "equipment": ["Ventilator", "BiPAP", "Intubation Kit"],
            "ot_required": False,
            "priority": 2
        }
    }
    
    def execute(self, condition: str, audit: AuditLogger) -> Optional[Dict]:
        """Execute emergency protocol."""
        protocol = self.PROTOCOLS.get(condition)
        if not protocol:
            audit.log("Protocol Lookup Failed", f"Unknown condition: {condition}", "error")
            return None
        audit.log("Emergency Protocol Loaded", f"{protocol['name']}", "critical")
        return protocol


# ================= AMBULANCE AGENT =================

class AmbulanceAgent:
    """Ambulance coordination and field data transmission."""
    
    def calculate_eta(self, distance_km: float) -> int:
        """Calculate ETA in minutes (avg speed 40 km/h in city)."""
        return int(distance_km / 40 * 60)
    
    def send_field_data(self, patient: DemoPatient, audit: AuditLogger):
        """Send real-time vitals from ambulance."""
        patient.update_vitals(simulate_critical=True)
        audit.log("Ambulance Vitals Transmitted", 
                 f"Patient: {patient.name}, Risk Score: {patient.risk}%", 
                 "warning" if patient.risk > 70 else "info")


# ================= VISION AGENT (CCTV) =================

class VisionAgent:
    """YOLOv8-Pose based fall detection."""
    
    def detect_fall(self, inactive_minutes: int) -> bool:
        """Detect potential fall based on inactivity."""
        return inactive_minutes >= 2
    
    def analyze_pose(self) -> Dict:
        """Simulate pose analysis."""
        return {
            "person_detected": True,
            "pose_confidence": random.uniform(0.85, 0.98),
            "fall_probability": random.uniform(0.7, 0.95),
            "zone": "General Ward - Bed 7"
        }


# ================= BED MANAGER (TETRIS ALGORITHM) =================

class DemoBedManager:
    """ICU Bed management with Tetris-style swapping."""
    
    def __init__(self):
        self.icu_beds = [
            DemoBed("ICU-1", "ICU"),
            DemoBed("ICU-2", "ICU"),
            DemoBed("ICU-3", "ICU")
        ]
        self.general_beds = [
            DemoBed("GEN-1", "General"),
            DemoBed("GEN-2", "General"),
            DemoBed("GEN-3", "General"),
            DemoBed("GEN-4", "General")
        ]
    
    def find_free_icu(self) -> Optional[DemoBed]:
        """Find an available ICU bed."""
        return next((b for b in self.icu_beds if b.patient is None), None)
    
    def find_recovery_candidate(self) -> Optional[DemoBed]:
        """Find a recovering patient who can be moved out of ICU."""
        candidates = [
            bed for bed in self.icu_beds 
            if bed.patient and bed.patient.risk < 40
        ]
        if candidates:
            # Return the one with lowest risk (most stable)
            return min(candidates, key=lambda b: b.patient.risk)
        return None
    
    def find_free_general(self) -> Optional[DemoBed]:
        """Find an available general bed."""
        return next((b for b in self.general_beds if b.patient is None), None)


# ================= STAFF MANAGER =================

class DemoStaffManager:
    """Staff assignment with workload balancing."""
    
    def __init__(self):
        self.doctors = [
            DemoStaff("Dr. Sharma", "Doctor", 2, "Cardiology"),
            DemoStaff("Dr. Patel", "Doctor", 3, "Emergency Medicine"),
            DemoStaff("Dr. Reddy", "Doctor", 1, "Internal Medicine")
        ]
        self.nurses = [
            DemoStaff("Nurse Priya", "Nurse", 4),
            DemoStaff("Nurse Anjali", "Nurse", 3),
            DemoStaff("Nurse Kavita", "Nurse", 5)
        ]
    
    def assign_doctor_nurse(self) -> tuple:
        """Assign least-loaded doctor and nurse."""
        doctor = min(self.doctors, key=lambda d: d.active_cases)
        nurse = min(self.nurses, key=lambda n: n.active_cases)
        doctor.active_cases += 1
        nurse.active_cases += 1
        return doctor, nurse
    
    def get_specialist(self, specialization: str) -> Optional[DemoStaff]:
        """Get a specialist doctor."""
        for doc in self.doctors:
            if doc.specialization.lower() == specialization.lower():
                return doc
        return None


# ================= VITAL FLOW AI CORE =================

class VitalFlowAI:
    """
    The Brain of VitalFlow Hospital Command Center.
    
    Features:
    - Continuous patient monitoring
    - AI-driven escalation
    - Tetris bed allocation
    - Emergency protocol execution
    - Fall detection integration
    - Automated billing
    """
    
    def __init__(self):
        self.audit = AuditLogger()
        self.beds = DemoBedManager()
        self.staff = DemoStaffManager()
        self.protocol_engine = EmergencyProtocolEngine()
        self.ambulance = AmbulanceAgent()
        self.vision = VisionAgent()
    
    def monitor_patient(self, patient: DemoPatient, simulate_critical: bool = False) -> Dict:
        """Continuous monitoring with risk assessment."""
        patient.update_vitals(simulate_critical)
        
        status = "normal"
        if patient.risk > 75:
            status = "critical"
            self.audit.log("⚠️ CRITICAL VITALS", 
                          f"{patient.name} Risk={patient.risk}%", "critical")
        elif patient.risk > 50:
            status = "warning"
            self.audit.log("Elevated Risk", 
                          f"{patient.name} Risk={patient.risk}%", "warning")
        else:
            self.audit.log("Vitals Normal", 
                          f"{patient.name} Risk={patient.risk}%", "info")
        
        return {
            "patient": patient.name,
            "risk": patient.risk,
            "status": status,
            "spo2": patient.spo2,
            "heart_rate": patient.heart_rate,
            "bp": patient.bp
        }
    
    def escalate(self, patient: DemoPatient) -> Dict:
        """Escalate critical patient with staff assignment."""
        doctor, nurse = self.staff.assign_doctor_nurse()
        
        self.audit.log("🚨 ESCALATION TRIGGERED", 
                      f"Patient {patient.name} requires immediate attention", "critical")
        self.audit.log("👨‍⚕️ Doctor Assigned", 
                      f"{doctor.name} ({doctor.specialization})", "info")
        self.audit.log("👩‍⚕️ Nurse Assigned", 
                      f"{nurse.name}", "info")
        
        return {
            "escalated": True,
            "doctor": doctor,
            "nurse": nurse,
            "patient": patient
        }
    
    def allocate_icu(self, patient: DemoPatient) -> Dict:
        """Allocate ICU bed using Tetris algorithm."""
        result = {"success": False, "action": "", "details": ""}
        
        # First, try to find a free ICU bed
        bed = self.beds.find_free_icu()
        
        if bed:
            bed.patient = patient
            patient.in_icu = True
            patient.location = bed.bed_id
            
            self.audit.log("🛏️ ICU Bed Assigned", 
                          f"{patient.name} → {bed.bed_id}", "info")
            
            result = {
                "success": True,
                "action": "direct_allocation",
                "bed": bed.bed_id,
                "details": f"Direct ICU allocation to {bed.bed_id}"
            }
        else:
            # ICU Full - Tetris Algorithm
            self.audit.log("⚠️ ICU FULL", 
                          "Initiating Tetris Swap Algorithm", "warning")
            
            recovery_bed = self.beds.find_recovery_candidate()
            
            if recovery_bed:
                old_patient = recovery_bed.patient
                general_bed = self.beds.find_free_general()
                
                if general_bed:
                    # Perform the swap
                    self.audit.log("🔄 TETRIS SWAP", 
                                  f"Moving {old_patient.name} (Risk:{old_patient.risk}%) to General Ward", 
                                  "warning")
                    
                    # Move recovering patient to general
                    general_bed.patient = old_patient
                    old_patient.in_icu = False
                    old_patient.location = general_bed.bed_id
                    
                    # Assign critical patient to ICU
                    recovery_bed.patient = patient
                    patient.in_icu = True
                    patient.location = recovery_bed.bed_id
                    
                    self.audit.log("✅ ICU Reallocated", 
                                  f"{patient.name} → {recovery_bed.bed_id}", "info")
                    
                    result = {
                        "success": True,
                        "action": "tetris_swap",
                        "bed": recovery_bed.bed_id,
                        "swapped_patient": old_patient.name,
                        "details": f"Swapped {old_patient.name} to {general_bed.bed_id}, {patient.name} to ICU"
                    }
                else:
                    self.audit.log("❌ No General Beds", 
                                  "Cannot perform swap", "error")
                    result = {
                        "success": False,
                        "action": "failed",
                        "details": "No general beds available for swap"
                    }
            else:
                self.audit.log("❌ No Recovery Candidates", 
                              "All ICU patients are critical", "error")
                result = {
                    "success": False,
                    "action": "failed",
                    "details": "All ICU patients are critical - no swap possible"
                }
        
        return result
    
    def handle_ambulance_call(self, patient: DemoPatient, condition: str, distance: float) -> Dict:
        """Handle incoming ambulance emergency."""
        # Calculate ETA
        eta = self.ambulance.calculate_eta(distance)
        self.audit.log("🚑 AMBULANCE INCOMING", 
                      f"ETA: {eta} minutes, Distance: {distance}km", "critical")
        
        # Get field vitals
        self.ambulance.send_field_data(patient, self.audit)
        
        # Load protocol
        protocol = self.protocol_engine.execute(condition, self.audit)
        
        if protocol:
            # Prepare equipment
            self.audit.log("🛒 TROLLEY READY", 
                          f"Prepare {protocol['trolley']}", "warning")
            
            for med in protocol['medicines']:
                self.audit.log("💊 Medicine Staged", med, "info")
            
            # Pre-allocate ICU
            icu_result = self.allocate_icu(patient)
            
            return {
                "eta": eta,
                "distance": distance,
                "protocol": protocol,
                "icu_allocation": icu_result,
                "patient": patient
            }
        
        return {"error": "Protocol not found"}
    
    def handle_fall_event(self, inactive_minutes: int) -> Dict:
        """Handle fall detection from CCTV."""
        if self.vision.detect_fall(inactive_minutes):
            pose_data = self.vision.analyze_pose()
            
            self.audit.log("🚨 FALL DETECTED", 
                          f"Zone: {pose_data['zone']}, Confidence: {pose_data['fall_probability']:.0%}", 
                          "critical")
            self.audit.log("📹 Pose Analysis", 
                          f"No movement for {inactive_minutes} minutes", "warning")
            
            # Auto-assign staff
            doctor, nurse = self.staff.assign_doctor_nurse()
            self.audit.log("👨‍⚕️ Emergency Response", 
                          f"{doctor.name} and {nurse.name} dispatched", "info")
            
            return {
                "fall_detected": True,
                "pose_data": pose_data,
                "inactive_minutes": inactive_minutes,
                "responders": {"doctor": doctor, "nurse": nurse}
            }
        
        return {"fall_detected": False}
    
    def generate_bill(self, patient: DemoPatient) -> Dict:
        """Generate itemized bill."""
        items = []
        
        # Base charges
        base = 5000
        items.append({"item": "Consultation & Admission", "amount": base})
        
        # ICU charges
        if patient.in_icu:
            icu_charge = 15000
            items.append({"item": "ICU Care (per day)", "amount": icu_charge})
        else:
            room_charge = 2000
            items.append({"item": "General Ward (per day)", "amount": room_charge})
        
        # Medicines
        if patient.medicines:
            med_charge = len(patient.medicines) * 500
            items.append({"item": f"Medicines ({len(patient.medicines)} items)", "amount": med_charge})
        
        # Calculate total
        subtotal = sum(item["amount"] for item in items)
        
        # Insurance discount
        discount = 0
        if patient.insurance:
            discount = subtotal * 0.7  # 70% covered
            items.append({"item": "Insurance Coverage (70%)", "amount": -discount})
        
        total = subtotal - discount
        
        self.audit.log("💰 Bill Generated", f"₹{int(total)} (Patient: {patient.name})", "info")
        
        return {
            "patient": patient.name,
            "items": items,
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "insurance": patient.insurance
        }


# ================= STREAMLIT DEMO UI =================

def render_demo_page():
    """Render the interactive demo page for judges."""
    
    st.set_page_config(
        page_title="VitalFlow AI - Demo",
        page_icon="🏥",
        layout="wide"
    )
    
    st.markdown("""
    <style>
        .demo-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
        }
        .demo-title {
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .log-critical { background: rgba(255,0,0,0.1); border-left: 4px solid #ff0000; }
        .log-warning { background: rgba(255,165,0,0.1); border-left: 4px solid #ffa500; }
        .log-info { background: rgba(0,212,255,0.1); border-left: 4px solid #00d4ff; }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="demo-header">
        <div class="demo-title">🏥 VitalFlow AI Demo</div>
        <p style="color: #a0a0a0;">Balancing Risk and Capacity in Hospital Care</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize VitalFlow AI
    if "vf_ai" not in st.session_state:
        st.session_state.vf_ai = VitalFlowAI()
        st.session_state.demo_step = 0
        st.session_state.demo_patients = {}
    
    ai = st.session_state.vf_ai
    
    # Demo control
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 🎬 Interactive Demo Scenarios")
    
    with col2:
        if st.button("🔄 Reset Demo", use_container_width=True):
            st.session_state.vf_ai = VitalFlowAI()
            st.session_state.demo_step = 0
            st.session_state.demo_patients = {}
            st.rerun()
    
    # Demo tabs
    tabs = st.tabs([
        "1️⃣ Setup",
        "2️⃣ Monitoring",
        "3️⃣ Escalation",
        "4️⃣ Ambulance",
        "5️⃣ Fall Detection",
        "6️⃣ Billing",
        "📋 Audit Log"
    ])
    
    # ============ TAB 1: SETUP ============
    with tabs[0]:
        st.markdown("### 🏥 Hospital Setup")
        st.info("This simulates a hospital with ICU beds already partially occupied.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ICU Beds Status")
            
            if st.button("🛏️ Occupy ICU with Recovering Patient", key="setup_icu"):
                # Create recovering patient in ICU
                recovering = DemoPatient("Sita Devi", "ICU", insurance=True)
                recovering.risk = 35
                recovering.spo2 = 97
                recovering.heart_rate = 72
                recovering.in_icu = True
                
                # Assign to ICU-1
                ai.beds.icu_beds[0].patient = recovering
                st.session_state.demo_patients["recovering"] = recovering
                
                ai.audit.log("🛏️ ICU-1 Occupied", 
                            f"Sita Devi (Recovering, Risk: 35%)", "info")
                st.success("✅ ICU-1 now occupied by recovering patient Sita Devi")
                st.rerun()
            
            # Show ICU status
            for bed in ai.beds.icu_beds:
                if bed.patient:
                    st.markdown(f"""
                    🔴 **{bed.bed_id}**: {bed.patient.name}  
                    └ Risk: {bed.patient.risk}% | Status: {"Recovering" if bed.patient.risk < 40 else "Critical"}
                    """)
                else:
                    st.markdown(f"🟢 **{bed.bed_id}**: Available")
        
        with col2:
            st.markdown("#### Staff Available")
            
            st.markdown("**Doctors:**")
            for doc in ai.staff.doctors:
                st.write(f"👨‍⚕️ {doc.name} ({doc.specialization}) - {doc.active_cases} patients")
            
            st.markdown("**Nurses:**")
            for nurse in ai.staff.nurses:
                st.write(f"👩‍⚕️ {nurse.name} - {nurse.active_cases} patients")
    
    # ============ TAB 2: MONITORING ============
    with tabs[1]:
        st.markdown("### 📊 Continuous Patient Monitoring")
        st.info("The AI continuously monitors patient vitals and calculates risk scores.")
        
        # Create ward patient
        if "ward_patient" not in st.session_state.demo_patients:
            st.session_state.demo_patients["ward_patient"] = DemoPatient(
                "Ramesh Kumar", "General Ward", insurance=True
            )
        
        ward_patient = st.session_state.demo_patients["ward_patient"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### Patient: {ward_patient.name}")
            st.write(f"📍 Location: {ward_patient.location}")
            
            simulate_critical = st.checkbox("⚠️ Simulate Deteriorating Condition", value=False)
            
            if st.button("🔄 Update Vitals", key="update_vitals"):
                result = ai.monitor_patient(ward_patient, simulate_critical)
                st.session_state.last_vitals = result
                st.rerun()
        
        with col2:
            st.markdown("#### Current Vitals")
            
            # Display vitals
            risk_color = "🔴" if ward_patient.risk > 75 else "🟠" if ward_patient.risk > 50 else "🟢"
            
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.metric(f"{risk_color} Risk Score", f"{ward_patient.risk}%")
            with metrics_col2:
                st.metric("🫁 SpO2", f"{ward_patient.spo2}%")
            with metrics_col3:
                st.metric("💓 Heart Rate", f"{ward_patient.heart_rate} bpm")
            
            st.metric("💉 Blood Pressure", ward_patient.bp)
        
        # Risk history chart
        if ward_patient.vitals_stream:
            st.markdown("#### 📈 Risk History")
            st.line_chart(list(ward_patient.vitals_stream))
    
    # ============ TAB 3: ESCALATION & ICU ============
    with tabs[2]:
        st.markdown("### 🚨 Escalation & ICU Allocation")
        st.info("When risk exceeds 75%, the AI triggers escalation and uses the **Tetris Algorithm** to allocate ICU beds.")
        
        ward_patient = st.session_state.demo_patients.get("ward_patient")
        
        if ward_patient:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### Patient: {ward_patient.name}")
                st.write(f"Current Risk: **{ward_patient.risk}%**")
                
                if st.button("🚨 Trigger Escalation", key="escalate", type="primary"):
                    # Force high risk for demo
                    ward_patient.risk = 82
                    ward_patient.spo2 = 88
                    ward_patient.heart_rate = 125
                    
                    result = ai.escalate(ward_patient)
                    st.session_state.escalation_result = result
                    st.rerun()
                
                if st.button("🛏️ Allocate ICU Bed", key="allocate_icu"):
                    result = ai.allocate_icu(ward_patient)
                    st.session_state.icu_result = result
                    st.rerun()
            
            with col2:
                st.markdown("#### Allocation Result")
                
                if "icu_result" in st.session_state:
                    result = st.session_state.icu_result
                    
                    if result["success"]:
                        if result["action"] == "direct_allocation":
                            st.success(f"✅ Direct allocation: {result['bed']}")
                        elif result["action"] == "tetris_swap":
                            st.warning(f"""
                            🔄 **Tetris Swap Performed!**
                            - Moved {result['swapped_patient']} to General Ward
                            - {ward_patient.name} assigned to {result['bed']}
                            """)
                    else:
                        st.error(f"❌ {result['details']}")
        
        # Visual bed map
        st.markdown("---")
        st.markdown("#### 🗺️ ICU Bed Map")
        
        bed_cols = st.columns(3)
        for idx, bed in enumerate(ai.beds.icu_beds):
            with bed_cols[idx]:
                if bed.patient:
                    color = "#ff4444" if bed.patient.risk > 70 else "#ffaa00" if bed.patient.risk > 40 else "#44ff44"
                    st.markdown(f"""
                    <div style="background: {color}20; border: 2px solid {color}; 
                                border-radius: 10px; padding: 1rem; text-align: center;">
                        <strong>{bed.bed_id}</strong><br>
                        {bed.patient.name}<br>
                        Risk: {bed.patient.risk}%
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #44ff4420; border: 2px dashed #44ff44; 
                                border-radius: 10px; padding: 1rem; text-align: center;">
                        <strong>{bed.bed_id}</strong><br>
                        Available
                    </div>
                    """, unsafe_allow_html=True)
    
    # ============ TAB 4: AMBULANCE ============
    with tabs[3]:
        st.markdown("### 🚑 Ambulance Emergency Handling")
        st.info("AI receives real-time vitals from ambulance and pre-prepares the hospital.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Incoming Emergency")
            
            patient_name = st.text_input("Patient Name", "Mahesh Singh")
            condition = st.selectbox("Emergency Condition", 
                                    ["heart_attack", "trauma", "stroke", "respiratory_failure"])
            distance = st.slider("Distance (km)", 1, 30, 12)
            
            if st.button("🚨 INCOMING AMBULANCE", key="ambulance", type="primary"):
                emergency_patient = DemoPatient(patient_name, "Ambulance", insurance=True)
                st.session_state.demo_patients["emergency"] = emergency_patient
                
                result = ai.handle_ambulance_call(emergency_patient, condition, distance)
                st.session_state.ambulance_result = result
                st.rerun()
        
        with col2:
            if "ambulance_result" in st.session_state:
                result = st.session_state.ambulance_result
                
                st.markdown("#### 📍 Status")
                st.metric("⏱️ ETA", f"{result['eta']} minutes")
                
                if "protocol" in result:
                    protocol = result["protocol"]
                    st.markdown(f"**Protocol:** {protocol['name']}")
                    
                    st.markdown("**🛒 Trolley:**")
                    st.write(protocol["trolley"])
                    
                    st.markdown("**💊 Medicines:**")
                    for med in protocol["medicines"]:
                        st.write(f"  • {med}")
                    
                    st.markdown("**🔧 Equipment:**")
                    for equip in protocol["equipment"]:
                        st.write(f"  • {equip}")
    
    # ============ TAB 5: FALL DETECTION ============
    with tabs[4]:
        st.markdown("### 📹 CCTV Fall Detection (YOLOv8-Pose)")
        st.info("Computer vision detects patient inactivity and triggers alerts.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Simulate Inactivity")
            
            inactive_minutes = st.slider("Minutes of No Movement", 0, 10, 3)
            
            if st.button("🔍 Analyze CCTV Feed", key="fall_detect"):
                result = ai.handle_fall_event(inactive_minutes)
                st.session_state.fall_result = result
                st.rerun()
        
        with col2:
            if "fall_result" in st.session_state:
                result = st.session_state.fall_result
                
                if result["fall_detected"]:
                    st.error("🚨 **FALL DETECTED!**")
                    
                    pose_data = result["pose_data"]
                    st.write(f"📍 Zone: {pose_data['zone']}")
                    st.write(f"📊 Confidence: {pose_data['fall_probability']:.0%}")
                    st.write(f"⏱️ Inactive: {result['inactive_minutes']} minutes")
                    
                    st.markdown("**🚑 Responders Dispatched:**")
                    st.write(f"  • {result['responders']['doctor'].name}")
                    st.write(f"  • {result['responders']['nurse'].name}")
                else:
                    st.success("✅ No fall detected - Patient is active")
    
    # ============ TAB 6: BILLING ============
    with tabs[5]:
        st.markdown("### 💰 Automated Billing")
        st.info("AI generates itemized bills with automatic insurance processing.")
        
        # Select patient
        patient_options = list(st.session_state.demo_patients.keys())
        
        if patient_options:
            selected = st.selectbox("Select Patient", patient_options)
            patient = st.session_state.demo_patients[selected]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### Patient: {patient.name}")
                st.write(f"📍 Location: {patient.location}")
                st.write(f"🏥 ICU: {'Yes' if patient.in_icu else 'No'}")
                st.write(f"🛡️ Insurance: {'Yes' if patient.insurance else 'No'}")
                
                # Add some medicines for demo
                if st.button("💊 Add Sample Medicines"):
                    patient.medicines = ["Aspirin", "Heparin", "Oxygen"]
                    st.rerun()
                
                if st.button("📄 Generate Bill", type="primary"):
                    bill = ai.generate_bill(patient)
                    st.session_state.bill_result = bill
                    st.rerun()
            
            with col2:
                if "bill_result" in st.session_state:
                    bill = st.session_state.bill_result
                    
                    st.markdown("#### 📋 Invoice")
                    
                    for item in bill["items"]:
                        if item["amount"] >= 0:
                            st.write(f"  {item['item']}: ₹{item['amount']:,}")
                        else:
                            st.write(f"  {item['item']}: -₹{abs(item['amount']):,.0f}")
                    
                    st.markdown("---")
                    st.markdown(f"**Subtotal:** ₹{bill['subtotal']:,}")
                    if bill["insurance"]:
                        st.markdown(f"**Insurance Discount:** -₹{bill['discount']:,.0f}")
                    st.markdown(f"### **Total: ₹{bill['total']:,.0f}**")
        else:
            st.warning("No patients in demo yet. Start from Tab 1.")
    
    # ============ TAB 7: AUDIT LOG ============
    with tabs[6]:
        st.markdown("### 📋 Real-Time Audit Log")
        st.info("All AI decisions are logged for transparency and accountability.")
        
        if st.button("🗑️ Clear Logs"):
            ai.audit.clear()
            st.rerun()
        
        logs = ai.audit.get_recent(50)
        
        if logs:
            for log in reversed(logs):
                severity = log["severity"]
                bg_color = {"critical": "#ff000020", "warning": "#ffa50020", "info": "#00d4ff20"}
                border_color = {"critical": "#ff0000", "warning": "#ffa500", "info": "#00d4ff"}
                
                st.markdown(f"""
                <div style="background: {bg_color.get(severity, '#ffffff10')}; 
                            border-left: 4px solid {border_color.get(severity, '#00d4ff')};
                            padding: 0.5rem 1rem; margin: 0.3rem 0; border-radius: 5px;">
                    <small style="color: #888;">{log['timestamp']}</small>
                    <strong style="margin-left: 1rem;">{log['action']}</strong>
                    <span style="margin-left: 1rem; color: #aaa;">{log['reason']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No logs yet. Run some demo scenarios!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🏥 <strong>VitalFlow AI</strong> - Hospital Command Center</p>
        <p>Powered by Agentic AI • YOLOv8-Pose • ElevenLabs TTS</p>
        <p><small>Human-in-the-Loop Safety • Transparent Decision Making</small></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render_demo_page()
