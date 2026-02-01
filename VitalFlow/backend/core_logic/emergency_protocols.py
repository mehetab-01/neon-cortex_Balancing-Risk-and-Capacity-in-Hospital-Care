"""
Emergency Protocol Engine for VitalFlow AI.
Provides STRICT, PRE-DEFINED medical protocols.
NEVER invents medicines - only uses protocol-defined actions.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Patient, PatientStatus
from shared.utils import get_enum_value


class EmergencyType(str, Enum):
    """Types of medical emergencies"""
    HEART_ATTACK = "Heart Attack (MI)"
    STROKE = "Stroke"
    RESPIRATORY_FAILURE = "Respiratory Failure"
    SEPSIS = "Sepsis"
    CARDIAC_ARREST = "Cardiac Arrest"
    TRAUMA = "Trauma/Bleeding"
    ANAPHYLAXIS = "Anaphylaxis"
    DIABETIC_EMERGENCY = "Diabetic Emergency"
    SEIZURE = "Seizure"
    POISONING = "Poisoning"
    BURNS = "Burns"
    DROWNING = "Drowning"


@dataclass
class EmergencyProtocol:
    """Structured emergency protocol"""
    emergency_type: EmergencyType
    priority: int  # 1-5, 1 is most urgent
    destination: str  # ICU, Cath Lab, Trauma Bay, etc.
    equipment: List[str]
    medications: List[str]
    immediate_actions: List[str]
    monitoring: List[str]
    contraindications: List[str]
    time_critical: bool
    golden_hour: Optional[int]  # Minutes for critical intervention


# ============== PROTOCOL DATABASE ==============
EMERGENCY_PROTOCOLS: Dict[EmergencyType, EmergencyProtocol] = {
    
    EmergencyType.HEART_ATTACK: EmergencyProtocol(
        emergency_type=EmergencyType.HEART_ATTACK,
        priority=1,
        destination="ICU / Cath Lab",
        equipment=[
            "12-lead ECG machine",
            "Oxygen mask with reservoir",
            "Suction apparatus",
            "IV line setup",
            "Defibrillator on standby",
            "Cardiac monitor",
            "Pulse oximeter",
            "Emergency crash cart"
        ],
        medications=[
            "Aspirin 325mg (chewable) - IMMEDIATE",
            "Clopidogrel 300mg loading dose",
            "Nitroglycerin 0.4mg sublingual",
            "Heparin 5000 units IV bolus",
            "Morphine 2-4mg IV for pain",
            "Metoprolol 5mg IV (if no contraindication)",
            "Atorvastatin 80mg",
            "Oxygen therapy if SpO2 < 94%"
        ],
        immediate_actions=[
            "Call CODE STEMI if ST elevation",
            "Establish IV access immediately",
            "Administer Aspirin FIRST",
            "12-lead ECG within 10 minutes",
            "Prepare for cath lab if STEMI",
            "Continuous cardiac monitoring",
            "Keep patient calm and still"
        ],
        monitoring=[
            "Continuous ECG monitoring",
            "SpO2 every 5 minutes",
            "Blood pressure every 10 minutes",
            "Pain assessment using 0-10 scale",
            "Watch for arrhythmias"
        ],
        contraindications=[
            "No Nitroglycerin if SBP < 90mmHg",
            "No Nitroglycerin if recent PDE5 inhibitor use",
            "No Morphine if respiratory depression",
            "No Metoprolol if HR < 60 or SBP < 100"
        ],
        time_critical=True,
        golden_hour=90  # Door-to-balloon time target
    ),
    
    EmergencyType.STROKE: EmergencyProtocol(
        emergency_type=EmergencyType.STROKE,
        priority=1,
        destination="ICU / Stroke Unit",
        equipment=[
            "CT scanner (emergency)",
            "Blood pressure monitor",
            "IV line setup",
            "Oxygen delivery system",
            "Neurological assessment tools",
            "Foley catheter",
            "NG tube if swallowing impaired"
        ],
        medications=[
            "tPA (Alteplase) 0.9mg/kg IV - IF ELIGIBLE",
            "Labetalol 10-20mg IV for BP control",
            "Nicardipine drip if BP > 185/110",
            "Aspirin 325mg (after CT rules out bleed)",
            "Normal Saline IV",
            "Mannitol 20% if cerebral edema"
        ],
        immediate_actions=[
            "FAST assessment (Face, Arms, Speech, Time)",
            "Note exact time of symptom onset",
            "CT scan STAT to rule out hemorrhage",
            "Blood glucose check",
            "NPO (nothing by mouth)",
            "Elevate head of bed 30 degrees",
            "Neuro checks every 15 minutes"
        ],
        monitoring=[
            "Neurological status every 15 min",
            "Blood pressure every 5 min during tPA",
            "Watch for signs of bleeding",
            "Swallowing assessment before food/water",
            "GCS (Glasgow Coma Scale)"
        ],
        contraindications=[
            "No tPA if > 4.5 hours from onset",
            "No tPA if hemorrhage on CT",
            "No tPA if recent surgery",
            "No anticoagulants if bleeding stroke"
        ],
        time_critical=True,
        golden_hour=270  # 4.5 hours for tPA eligibility
    ),
    
    EmergencyType.RESPIRATORY_FAILURE: EmergencyProtocol(
        emergency_type=EmergencyType.RESPIRATORY_FAILURE,
        priority=1,
        destination="ICU",
        equipment=[
            "High-flow oxygen system",
            "Non-rebreather mask",
            "Nebulizer",
            "BiPAP/CPAP machine",
            "Ventilator on standby",
            "Intubation tray",
            "Suction apparatus",
            "Pulse oximeter",
            "ABG kit"
        ],
        medications=[
            "Salbutamol 2.5mg nebulized",
            "Ipratropium 0.5mg nebulized",
            "Methylprednisolone 125mg IV",
            "Magnesium Sulfate 2g IV (for asthma)",
            "Epinephrine if severe bronchospasm",
            "Sedatives for intubation if needed"
        ],
        immediate_actions=[
            "High-flow oxygen immediately",
            "Position upright if possible",
            "ABG (arterial blood gas)",
            "Nebulized bronchodilators",
            "Prepare for intubation if worsening",
            "Call respiratory therapist"
        ],
        monitoring=[
            "Continuous SpO2",
            "Respiratory rate every 5 min",
            "Work of breathing assessment",
            "ABG after 30 minutes",
            "Peak flow if able"
        ],
        contraindications=[
            "Avoid sedatives before securing airway",
            "No beta-blockers in acute asthma"
        ],
        time_critical=True,
        golden_hour=None
    ),
    
    EmergencyType.SEPSIS: EmergencyProtocol(
        emergency_type=EmergencyType.SEPSIS,
        priority=1,
        destination="ICU",
        equipment=[
            "Large bore IV access (2 lines)",
            "Central line kit",
            "Arterial line kit",
            "Foley catheter with urinometer",
            "Blood culture bottles",
            "Lactate testing",
            "Vasopressor infusion pumps"
        ],
        medications=[
            "Normal Saline 30ml/kg IV bolus STAT",
            "Broad-spectrum antibiotics within 1 hour:",
            "  - Piperacillin-Tazobactam 4.5g IV OR",
            "  - Meropenem 1g IV",
            "Norepinephrine if MAP < 65 despite fluids",
            "Vasopressin 0.03 units/min (adjunct)",
            "Hydrocortisone 200mg/day if refractory shock"
        ],
        immediate_actions=[
            "Draw blood cultures BEFORE antibiotics",
            "Administer antibiotics within 1 HOUR",
            "Aggressive fluid resuscitation",
            "Measure serum lactate",
            "Insert Foley catheter",
            "Source control (drain abscess, remove infected device)"
        ],
        monitoring=[
            "MAP (Mean Arterial Pressure) target > 65",
            "Urine output > 0.5 ml/kg/hr",
            "Lactate clearance",
            "Central venous pressure if available",
            "ScvO2 if central line"
        ],
        contraindications=[
            "Avoid nephrotoxic drugs if AKI",
            "Adjust antibiotics for allergies"
        ],
        time_critical=True,
        golden_hour=60  # Antibiotics within 1 hour
    ),
    
    EmergencyType.CARDIAC_ARREST: EmergencyProtocol(
        emergency_type=EmergencyType.CARDIAC_ARREST,
        priority=1,
        destination="ICU",
        equipment=[
            "Defibrillator/AED",
            "CPR board",
            "Bag-valve-mask (Ambu bag)",
            "Intubation tray",
            "IV/IO access kit",
            "Emergency crash cart",
            "Suction",
            "Capnography"
        ],
        medications=[
            "Epinephrine 1mg IV/IO every 3-5 min",
            "Amiodarone 300mg IV (first dose for VF/pVT)",
            "Amiodarone 150mg IV (second dose)",
            "Lidocaine 1-1.5mg/kg (alternative to amiodarone)",
            "Sodium Bicarbonate 50mEq (if prolonged arrest)",
            "Calcium Chloride 1g (if hyperkalemia/hypocalcemia)",
            "Magnesium 2g (if Torsades de Pointes)"
        ],
        immediate_actions=[
            "START CPR IMMEDIATELY - 100-120/min",
            "Call CODE BLUE",
            "Attach defibrillator",
            "Shock if VF/pVT (200J biphasic)",
            "Epinephrine after 2nd shock",
            "Advanced airway after initial resuscitation",
            "Identify reversible causes (H's and T's)"
        ],
        monitoring=[
            "Continuous ECG",
            "End-tidal CO2 (ETCO2 > 10 for effective CPR)",
            "Pulse check every 2 min",
            "Quality of CPR (rate, depth, recoil)"
        ],
        contraindications=[
            "Do not stop CPR for > 10 seconds",
            "Check for DNR/POLST before stopping"
        ],
        time_critical=True,
        golden_hour=10  # Brain damage begins in minutes
    ),
    
    EmergencyType.TRAUMA: EmergencyProtocol(
        emergency_type=EmergencyType.TRAUMA,
        priority=1,
        destination="Trauma Bay / OR",
        equipment=[
            "Trauma shears",
            "C-spine collar",
            "Backboard",
            "Large bore IV (2 lines)",
            "Rapid infuser",
            "Blood warmer",
            "Chest tube tray",
            "FAST ultrasound",
            "Massive transfusion protocol"
        ],
        medications=[
            "Tranexamic Acid (TXA) 1g IV within 3 hours",
            "Packed RBCs (O-negative if emergency)",
            "Fresh Frozen Plasma 1:1 with PRBCs",
            "Platelets if massive transfusion",
            "Normal Saline (limited, prefer blood)",
            "Tetanus prophylaxis",
            "Antibiotics for open fractures"
        ],
        immediate_actions=[
            "A - Airway with C-spine protection",
            "B - Breathing: Check for tension pneumothorax",
            "C - Circulation: Stop bleeding, IV access",
            "D - Disability: GCS, pupils",
            "E - Exposure: Full exam, prevent hypothermia",
            "Activate massive transfusion if needed",
            "FAST exam for internal bleeding"
        ],
        monitoring=[
            "Vital signs every 5 min",
            "Urine output",
            "Hemoglobin/hematocrit",
            "Coagulation studies",
            "Base deficit/lactate"
        ],
        contraindications=[
            "Avoid excessive crystalloids",
            "No TXA after 3 hours from injury"
        ],
        time_critical=True,
        golden_hour=60
    ),
    
    EmergencyType.ANAPHYLAXIS: EmergencyProtocol(
        emergency_type=EmergencyType.ANAPHYLAXIS,
        priority=1,
        destination="ICU / Emergency",
        equipment=[
            "Epinephrine auto-injector",
            "Oxygen with non-rebreather",
            "IV access kit",
            "Intubation tray (airway may swell)",
            "Nebulizer"
        ],
        medications=[
            "Epinephrine 0.3-0.5mg IM (thigh) - FIRST LINE",
            "Repeat Epinephrine every 5-15 min if needed",
            "Normal Saline 1-2L IV bolus",
            "Diphenhydramine 50mg IV",
            "Ranitidine 50mg IV",
            "Methylprednisolone 125mg IV",
            "Albuterol nebulized for bronchospasm"
        ],
        immediate_actions=[
            "EPINEPHRINE IM IMMEDIATELY",
            "Remove allergen if possible",
            "Call for help",
            "Position: legs elevated (unless breathing difficulty)",
            "High-flow oxygen",
            "Large bore IV access",
            "Prepare for intubation if stridor"
        ],
        monitoring=[
            "Airway patency",
            "Blood pressure every 5 min",
            "SpO2 continuous",
            "Watch for biphasic reaction (4-8 hours)"
        ],
        contraindications=[
            "Do NOT delay Epinephrine",
            "Antihistamines are NOT first-line"
        ],
        time_critical=True,
        golden_hour=None
    ),
    
    EmergencyType.DIABETIC_EMERGENCY: EmergencyProtocol(
        emergency_type=EmergencyType.DIABETIC_EMERGENCY,
        priority=2,
        destination="ICU / Emergency",
        equipment=[
            "Glucometer",
            "IV access kit",
            "Insulin infusion pump",
            "Arterial blood gas kit",
            "Cardiac monitor"
        ],
        medications=[
            "FOR HYPOGLYCEMIA (glucose < 70):",
            "  - Dextrose 50% 25-50ml IV push",
            "  - Glucagon 1mg IM if no IV access",
            "FOR DKA/HHS (high glucose):",
            "  - Normal Saline 1L/hr initially",
            "  - Regular Insulin 0.1 units/kg/hr IV",
            "  - Potassium replacement when K < 5.3",
            "  - Sodium Bicarbonate if pH < 6.9"
        ],
        immediate_actions=[
            "Check blood glucose STAT",
            "If LOW: Give Dextrose immediately",
            "If HIGH: Start IV fluids and insulin",
            "Check electrolytes and ABG",
            "Monitor for cerebral edema (DKA)",
            "Identify precipitating cause (infection, MI)"
        ],
        monitoring=[
            "Blood glucose every 1 hour",
            "Potassium every 2 hours",
            "Anion gap",
            "Mental status",
            "Fluid balance"
        ],
        contraindications=[
            "No insulin until potassium > 3.3",
            "Avoid rapid glucose correction (cerebral edema)"
        ],
        time_critical=True,
        golden_hour=None
    ),
    
    EmergencyType.SEIZURE: EmergencyProtocol(
        emergency_type=EmergencyType.SEIZURE,
        priority=2,
        destination="Emergency / ICU if status",
        equipment=[
            "Suction apparatus",
            "Oxygen",
            "IV access kit",
            "Padded side rails",
            "Glucometer"
        ],
        medications=[
            "Lorazepam 4mg IV/IM (first-line)",
            "Diazepam 10mg IV or 20mg rectal",
            "Midazolam 10mg IM if no IV",
            "Phenytoin/Fosphenytoin 20mg/kg IV (load)",
            "Levetiracetam 60mg/kg IV (alternative)",
            "Dextrose 50% if hypoglycemia"
        ],
        immediate_actions=[
            "Protect patient from injury",
            "Turn to side (recovery position)",
            "Do NOT restrain or put anything in mouth",
            "Time the seizure",
            "Check glucose",
            "Give benzodiazepine if > 5 min"
        ],
        monitoring=[
            "Duration of seizure",
            "Post-ictal state",
            "Vital signs",
            "Oxygen saturation",
            "Repeat seizures"
        ],
        contraindications=[
            "Avoid excessive sedation",
            "Phenytoin contraindicated in heart block"
        ],
        time_critical=True,
        golden_hour=30  # Status epilepticus after 5 min
    )
}


class EmergencyProtocolEngine:
    """
    Engine for matching patients to appropriate emergency protocols.
    NEVER invents medicines - only uses pre-defined protocols.
    """
    
    def __init__(self):
        self.protocols = EMERGENCY_PROTOCOLS
    
    def detect_emergency_type(self, patient: Patient) -> Optional[EmergencyType]:
        """
        Detect emergency type based on patient diagnosis and vitals.
        
        Args:
            patient: Patient object
            
        Returns:
            EmergencyType or None
        """
        diagnosis = patient.diagnosis.lower() if patient.diagnosis else ""
        status = get_enum_value(patient.status)
        
        # Keyword matching for emergency types
        emergency_keywords = {
            EmergencyType.HEART_ATTACK: ["heart attack", "mi", "myocardial", "chest pain", "stemi", "nstemi", "cardiac"],
            EmergencyType.STROKE: ["stroke", "cva", "cerebrovascular", "hemiplegia", "aphasia", "tia"],
            EmergencyType.RESPIRATORY_FAILURE: ["respiratory", "breathing", "hypoxia", "asthma", "copd", "pneumonia"],
            EmergencyType.SEPSIS: ["sepsis", "septic", "infection", "fever", "bacteremia"],
            EmergencyType.CARDIAC_ARREST: ["cardiac arrest", "code blue", "asystole", "vfib", "pulseless"],
            EmergencyType.TRAUMA: ["trauma", "accident", "injury", "bleeding", "fracture", "wound"],
            EmergencyType.ANAPHYLAXIS: ["anaphylaxis", "allergic", "allergy", "angioedema", "bee sting"],
            EmergencyType.DIABETIC_EMERGENCY: ["diabetic", "dka", "hypoglycemia", "hyperglycemia", "ketoacidosis"],
            EmergencyType.SEIZURE: ["seizure", "epilepsy", "convulsion", "fitting"]
        }
        
        for emergency_type, keywords in emergency_keywords.items():
            for keyword in keywords:
                if keyword in diagnosis:
                    return emergency_type
        
        # Vital-based detection
        if patient.spo2 < 85:
            return EmergencyType.RESPIRATORY_FAILURE
        
        if patient.heart_rate > 150 or patient.heart_rate < 40:
            if status == "Critical":
                return EmergencyType.CARDIAC_ARREST
        
        return None
    
    def get_protocol(self, emergency_type: EmergencyType) -> Optional[EmergencyProtocol]:
        """Get protocol for emergency type"""
        return self.protocols.get(emergency_type)
    
    def get_protocol_for_patient(self, patient: Patient) -> Dict:
        """
        Get complete protocol response for a patient.
        
        Args:
            patient: Patient object
            
        Returns:
            Dict with protocol details and actions
        """
        emergency_type = self.detect_emergency_type(patient)
        
        if not emergency_type:
            return {
                "detected": False,
                "message": "No specific emergency protocol detected. Apply standard care.",
                "patient_id": patient.id,
                "patient_name": patient.name
            }
        
        protocol = self.get_protocol(emergency_type)
        
        if not protocol:
            return {
                "detected": True,
                "emergency_type": emergency_type.value,
                "message": "Protocol not found in database",
                "patient_id": patient.id
            }
        
        return {
            "detected": True,
            "patient_id": patient.id,
            "patient_name": patient.name,
            "emergency_type": emergency_type.value,
            "priority": protocol.priority,
            "destination": protocol.destination,
            "time_critical": protocol.time_critical,
            "golden_hour_minutes": protocol.golden_hour,
            "equipment": protocol.equipment,
            "medications": protocol.medications,
            "immediate_actions": protocol.immediate_actions,
            "monitoring": protocol.monitoring,
            "contraindications": protocol.contraindications,
            "trust_log": f"Protocol {emergency_type.value} activated for {patient.name}. "
                        f"This is a {'TIME-CRITICAL' if protocol.time_critical else 'standard'} emergency. "
                        f"Destination: {protocol.destination}. "
                        f"{'Golden hour: ' + str(protocol.golden_hour) + ' minutes.' if protocol.golden_hour else ''}"
        }
    
    def get_all_protocols(self) -> List[Dict]:
        """Get summary of all available protocols"""
        return [
            {
                "type": p.emergency_type.value,
                "priority": p.priority,
                "destination": p.destination,
                "time_critical": p.time_critical,
                "golden_hour": p.golden_hour,
                "medication_count": len(p.medications),
                "equipment_count": len(p.equipment)
            }
            for p in self.protocols.values()
        ]
    
    def list_protocols(self) -> List[str]:
        """List all available protocol types"""
        return [e.value for e in EmergencyType]
    
    def get_protocol_by_name(self, name: str) -> Optional[Dict]:
        """
        Get protocol by string name.
        
        Args:
            name: Protocol name (e.g., 'heart_attack', 'stroke', 'Heart Attack (MI)')
            
        Returns:
            Protocol dict or None
        """
        # Normalize input
        name_lower = name.lower().replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "")
        
        # Simple mapping for common shorthand
        shortcuts = {
            "heart_attack": EmergencyType.HEART_ATTACK,
            "mi": EmergencyType.HEART_ATTACK,
            "myocardial_infarction": EmergencyType.HEART_ATTACK,
            "stroke": EmergencyType.STROKE,
            "respiratory": EmergencyType.RESPIRATORY_FAILURE,
            "respiratory_failure": EmergencyType.RESPIRATORY_FAILURE,
            "sepsis": EmergencyType.SEPSIS,
            "cardiac_arrest": EmergencyType.CARDIAC_ARREST,
            "trauma": EmergencyType.TRAUMA,
            "anaphylaxis": EmergencyType.ANAPHYLAXIS,
            "diabetic": EmergencyType.DIABETIC_EMERGENCY,
            "diabetic_emergency": EmergencyType.DIABETIC_EMERGENCY,
            "dka": EmergencyType.DIABETIC_EMERGENCY,
            "seizure": EmergencyType.SEIZURE,
        }
        
        # Check shortcuts first
        if name_lower in shortcuts:
            protocol = self.protocols.get(shortcuts[name_lower])
            if protocol:
                return self._protocol_to_dict(protocol)
        
        # Try to match by value
        for emergency_type in EmergencyType:
            type_value = emergency_type.value.lower().replace(" ", "_").replace("(", "").replace(")", "")
            if name_lower in type_value or type_value in name_lower:
                protocol = self.protocols.get(emergency_type)
                if protocol:
                    return self._protocol_to_dict(protocol)
        
        return None
    
    def _protocol_to_dict(self, protocol: EmergencyProtocol) -> Dict:
        """Convert protocol to dict"""
        return {
            "name": protocol.emergency_type.value,
            "priority": protocol.priority,
            "destination": protocol.destination,
            "time_critical": protocol.time_critical,
            "golden_hour_minutes": protocol.golden_hour,
            "equipment": protocol.equipment,
            "medications": protocol.medications,
            "immediate_actions": protocol.immediate_actions,
            "monitoring": protocol.monitoring,
            "contraindications": protocol.contraindications
        }


# Singleton instance
emergency_protocol_engine = EmergencyProtocolEngine()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing Emergency Protocol Engine...")
    print("=" * 60)
    
    # Test protocol detection
    from shared.models import Patient, PatientStatus
    
    test_cases = [
        Patient(id="P1", name="Heart Attack Patient", age=55, status=PatientStatus.CRITICAL, 
                spo2=88, heart_rate=120, diagnosis="Acute Myocardial Infarction"),
        Patient(id="P2", name="Stroke Patient", age=68, status=PatientStatus.CRITICAL,
                spo2=94, heart_rate=90, diagnosis="Acute Ischemic Stroke"),
        Patient(id="P3", name="Sepsis Patient", age=45, status=PatientStatus.SERIOUS,
                spo2=92, heart_rate=110, diagnosis="Severe Sepsis from UTI"),
        Patient(id="P4", name="Trauma Patient", age=30, status=PatientStatus.CRITICAL,
                spo2=90, heart_rate=130, diagnosis="Multiple Trauma from MVA"),
    ]
    
    for patient in test_cases:
        print(f"\n📋 Patient: {patient.name}")
        print(f"   Diagnosis: {patient.diagnosis}")
        
        result = emergency_protocol_engine.get_protocol_for_patient(patient)
        
        if result["detected"]:
            print(f"   🚨 Emergency Type: {result['emergency_type']}")
            print(f"   📍 Destination: {result['destination']}")
            print(f"   ⏱️  Time Critical: {result['time_critical']}")
            if result.get('golden_hour_minutes'):
                print(f"   ⏰ Golden Hour: {result['golden_hour_minutes']} minutes")
            print(f"   💊 Medications: {len(result['medications'])} items")
            print(f"   🔧 Equipment: {len(result['equipment'])} items")
        else:
            print(f"   ℹ️  {result['message']}")
    
    print("\n" + "=" * 60)
    print("✅ Emergency Protocol Engine Test Complete!")
