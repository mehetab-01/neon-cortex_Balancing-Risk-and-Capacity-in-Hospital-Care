"""
Billing Agent for VitalFlow AI.
Tracks medicines, procedures, equipment, bed duration.
Generates transparent, itemized bills with insurance/scheme deductions.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import Patient, Bed, BedType
from shared.utils import get_enum_value
from .state import hospital_state


class BillItemType(str, Enum):
    """Types of billable items"""
    BED_CHARGE = "Bed Charge"
    MEDICINE = "Medicine"
    PROCEDURE = "Procedure"
    EQUIPMENT = "Equipment"
    CONSULTATION = "Consultation"
    INVESTIGATION = "Investigation"
    NURSING = "Nursing Care"
    EMERGENCY = "Emergency Services"
    ICU_CHARGE = "ICU Charge"
    AMBULANCE = "Ambulance Service"
    MISC = "Miscellaneous"


class InsuranceType(str, Enum):
    """Insurance/Scheme types"""
    NONE = "No Insurance"
    PRIVATE = "Private Insurance"
    AYUSHMAN_BHARAT = "Ayushman Bharat"
    ESI = "ESI"
    CGHS = "CGHS"
    STATE_SCHEME = "State Health Scheme"
    CORPORATE = "Corporate Insurance"


@dataclass
class BillItem:
    """Single billable item"""
    item_id: str
    item_type: BillItemType
    description: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    timestamp: datetime
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "item_id": self.item_id,
            "type": get_enum_value(self.item_type),
            "description": self.description,
            "quantity": self.quantity,
            "unit": self.unit,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes
        }


@dataclass
class PatientBill:
    """Complete bill for a patient"""
    patient_id: str
    patient_name: str
    admission_time: datetime
    discharge_time: Optional[datetime] = None
    items: List[BillItem] = field(default_factory=list)
    insurance_type: InsuranceType = InsuranceType.NONE
    insurance_id: str = ""
    insurance_coverage_percent: float = 0.0
    
    # Calculated fields
    gross_total: float = 0.0
    insurance_deduction: float = 0.0
    scheme_deduction: float = 0.0
    tax: float = 0.0
    net_payable: float = 0.0
    
    # Status
    is_finalized: bool = False
    payment_status: str = "Pending"
    
    def calculate_totals(self):
        """Calculate all bill totals"""
        self.gross_total = sum(item.total_price for item in self.items)
        
        # Apply insurance
        if self.insurance_type != InsuranceType.NONE:
            self.insurance_deduction = self.gross_total * (self.insurance_coverage_percent / 100)
        
        # Tax (if applicable)
        taxable_amount = self.gross_total - self.insurance_deduction - self.scheme_deduction
        self.tax = 0  # No tax on healthcare in India
        
        self.net_payable = max(0, taxable_amount + self.tax)


# ============== PRICE LIST ==============
PRICE_LIST = {
    # Bed charges per day
    "bed_icu": 8000,
    "bed_emergency": 3000,
    "bed_general": 1500,
    "bed_pediatric": 2000,
    "bed_maternity": 2500,
    
    # Common medicines
    "aspirin_325mg": 10,
    "clopidogrel_75mg": 25,
    "nitroglycerin_0.4mg": 50,
    "heparin_5000u": 150,
    "morphine_10mg": 80,
    "epinephrine_1mg": 120,
    "atropine_1mg": 45,
    "amiodarone_150mg": 200,
    "normal_saline_1l": 80,
    "dextrose_50ml": 60,
    "antibiotics_iv": 350,
    "insulin_10u": 40,
    "oxygen_per_hour": 100,
    
    # Procedures
    "ecg": 500,
    "xray": 800,
    "ct_scan": 5000,
    "mri": 12000,
    "blood_test": 1200,
    "urine_test": 300,
    "echocardiogram": 3500,
    "intubation": 2000,
    "cpr": 5000,
    "defibrillation": 3000,
    "suturing": 1500,
    "catheterization": 2500,
    
    # Equipment usage
    "ventilator_per_hour": 500,
    "monitor_per_day": 1000,
    "nebulizer_session": 200,
    "defibrillator_use": 2000,
    
    # Consultations
    "doctor_consultation": 500,
    "specialist_consultation": 1000,
    "emergency_consultation": 1500,
    
    # Nursing
    "nursing_per_shift": 500,
    "special_nursing": 1000,
    
    # Ambulance
    "ambulance_basic": 2000,
    "ambulance_als": 5000
}

# Insurance coverage rules
INSURANCE_COVERAGE = {
    InsuranceType.AYUSHMAN_BHARAT: {
        "max_coverage": 500000,
        "coverage_percent": 100,
        "eligible_items": [BillItemType.BED_CHARGE, BillItemType.MEDICINE, 
                          BillItemType.PROCEDURE, BillItemType.ICU_CHARGE]
    },
    InsuranceType.ESI: {
        "max_coverage": 200000,
        "coverage_percent": 100,
        "eligible_items": "all"
    },
    InsuranceType.CGHS: {
        "max_coverage": 300000,
        "coverage_percent": 90,
        "eligible_items": "all"
    },
    InsuranceType.PRIVATE: {
        "max_coverage": 1000000,
        "coverage_percent": 80,
        "eligible_items": "all"
    },
    InsuranceType.CORPORATE: {
        "max_coverage": 500000,
        "coverage_percent": 85,
        "eligible_items": "all"
    }
}


class BillingAgent:
    """
    Automatic billing agent for tracking and generating patient bills.
    
    Features:
    - Real-time tracking of medicines, procedures, equipment
    - Automatic bed charge calculation
    - Insurance/scheme application
    - Itemized bill generation
    - Final approval workflow
    """
    
    def __init__(self):
        self.active_bills: Dict[str, PatientBill] = {}
        self.finalized_bills: List[PatientBill] = []
        self._item_counter = 0
    
    def _generate_item_id(self) -> str:
        """Generate unique item ID"""
        self._item_counter += 1
        return f"ITM-{self._item_counter:06d}"
    
    def start_billing(self, patient_id: str, 
                     insurance_type: InsuranceType = InsuranceType.NONE,
                     insurance_id: str = "") -> PatientBill:
        """
        Start billing for a patient upon admission.
        
        Args:
            patient_id: Patient ID
            insurance_type: Type of insurance/scheme
            insurance_id: Insurance policy number
            
        Returns:
            PatientBill object
        """
        patient = hospital_state.patients.get(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        # Get insurance coverage
        coverage_percent = 0
        if insurance_type in INSURANCE_COVERAGE:
            coverage_percent = INSURANCE_COVERAGE[insurance_type]["coverage_percent"]
        
        bill = PatientBill(
            patient_id=patient_id,
            patient_name=patient.name,
            admission_time=patient.admission_time,
            insurance_type=insurance_type,
            insurance_id=insurance_id,
            insurance_coverage_percent=coverage_percent
        )
        
        self.active_bills[patient_id] = bill
        
        # Add initial consultation charge
        self.add_item(
            patient_id=patient_id,
            item_type=BillItemType.CONSULTATION,
            description="Emergency Consultation",
            quantity=1,
            unit="visit",
            unit_price=PRICE_LIST["emergency_consultation"]
        )
        
        hospital_state.log_decision(
            "BILLING_STARTED",
            f"Billing started for {patient.name}. Insurance: {get_enum_value(insurance_type)}",
            {"patient_id": patient_id, "insurance": get_enum_value(insurance_type)}
        )
        
        return bill
    
    def add_item(self, patient_id: str,
                item_type: BillItemType,
                description: str,
                quantity: float,
                unit: str,
                unit_price: float,
                notes: str = "") -> BillItem:
        """
        Add a billable item to patient's bill.
        
        Args:
            patient_id: Patient ID
            item_type: Type of item
            description: Item description
            quantity: Quantity
            unit: Unit of measurement
            unit_price: Price per unit
            notes: Additional notes
            
        Returns:
            BillItem added
        """
        if patient_id not in self.active_bills:
            # Auto-start billing if not started
            self.start_billing(patient_id)
        
        bill = self.active_bills[patient_id]
        
        item = BillItem(
            item_id=self._generate_item_id(),
            item_type=item_type,
            description=description,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            timestamp=datetime.now(),
            notes=notes
        )
        
        bill.items.append(item)
        bill.calculate_totals()
        
        return item
    
    def add_medicine(self, patient_id: str, medicine_name: str, 
                    quantity: float = 1, notes: str = "") -> BillItem:
        """Add medicine to bill"""
        # Look up price
        price_key = medicine_name.lower().replace(" ", "_").replace("-", "_")
        unit_price = PRICE_LIST.get(price_key, 100)  # Default ₹100 if not found
        
        return self.add_item(
            patient_id=patient_id,
            item_type=BillItemType.MEDICINE,
            description=medicine_name,
            quantity=quantity,
            unit="dose",
            unit_price=unit_price,
            notes=notes
        )
    
    def add_procedure(self, patient_id: str, procedure_name: str,
                     notes: str = "") -> BillItem:
        """Add procedure to bill"""
        price_key = procedure_name.lower().replace(" ", "_").replace("-", "_")
        unit_price = PRICE_LIST.get(price_key, 500)
        
        return self.add_item(
            patient_id=patient_id,
            item_type=BillItemType.PROCEDURE,
            description=procedure_name,
            quantity=1,
            unit="procedure",
            unit_price=unit_price,
            notes=notes
        )
    
    def add_bed_charges(self, patient_id: str, bed_type: BedType, 
                       days: float) -> BillItem:
        """Add bed charges for duration"""
        bed_type_str = get_enum_value(bed_type).lower()
        price_key = f"bed_{bed_type_str}"
        unit_price = PRICE_LIST.get(price_key, PRICE_LIST["bed_general"])
        
        item_type = BillItemType.ICU_CHARGE if bed_type == BedType.ICU else BillItemType.BED_CHARGE
        
        return self.add_item(
            patient_id=patient_id,
            item_type=item_type,
            description=f"{get_enum_value(bed_type)} Bed - {days} days",
            quantity=days,
            unit="days",
            unit_price=unit_price
        )
    
    def add_equipment_usage(self, patient_id: str, equipment_name: str,
                           hours: float) -> BillItem:
        """Add equipment usage charges"""
        price_key = equipment_name.lower().replace(" ", "_")
        unit_price = PRICE_LIST.get(price_key, 200)
        
        return self.add_item(
            patient_id=patient_id,
            item_type=BillItemType.EQUIPMENT,
            description=equipment_name,
            quantity=hours,
            unit="hours",
            unit_price=unit_price
        )
    
    def calculate_bed_duration(self, patient_id: str) -> float:
        """Calculate bed duration in days"""
        patient = hospital_state.patients.get(patient_id)
        if not patient:
            return 0
        
        admission = patient.admission_time
        now = datetime.now()
        duration = now - admission
        
        # Minimum 1 day, then calculate fractional days
        days = max(1, duration.total_seconds() / (24 * 3600))
        return round(days, 2)
    
    def finalize_bill(self, patient_id: str) -> Dict:
        """
        Finalize bill upon discharge.
        Calculates all final charges and applies insurance.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Finalized bill summary
        """
        if patient_id not in self.active_bills:
            return {"error": "No active bill for patient"}
        
        bill = self.active_bills[patient_id]
        patient = hospital_state.patients.get(patient_id)
        
        # Add final bed charges
        if patient and patient.bed_id:
            bed = hospital_state.beds.get(patient.bed_id)
            if bed:
                days = self.calculate_bed_duration(patient_id)
                self.add_bed_charges(patient_id, bed.bed_type, days)
        
        # Calculate final totals
        bill.discharge_time = datetime.now()
        bill.calculate_totals()
        bill.is_finalized = True
        
        # Move to finalized
        self.finalized_bills.append(bill)
        del self.active_bills[patient_id]
        
        hospital_state.log_decision(
            "BILL_FINALIZED",
            f"Bill finalized for {bill.patient_name}. "
            f"Gross: ₹{bill.gross_total:.2f}, Net Payable: ₹{bill.net_payable:.2f}",
            {
                "patient_id": patient_id,
                "gross_total": bill.gross_total,
                "insurance_deduction": bill.insurance_deduction,
                "net_payable": bill.net_payable
            }
        )
        
        return self.get_bill_summary(bill)
    
    def get_bill_summary(self, bill: PatientBill) -> Dict:
        """Generate bill summary"""
        # Group items by type
        items_by_type = {}
        for item in bill.items:
            type_name = get_enum_value(item.item_type)
            if type_name not in items_by_type:
                items_by_type[type_name] = {"items": [], "subtotal": 0}
            items_by_type[type_name]["items"].append(item.to_dict())
            items_by_type[type_name]["subtotal"] += item.total_price
        
        return {
            "patient_id": bill.patient_id,
            "patient_name": bill.patient_name,
            "admission_time": bill.admission_time.isoformat(),
            "discharge_time": bill.discharge_time.isoformat() if bill.discharge_time else None,
            "duration_days": self.calculate_bed_duration(bill.patient_id) if not bill.discharge_time else None,
            
            "items_by_category": items_by_type,
            "total_items": len(bill.items),
            
            "gross_total": round(bill.gross_total, 2),
            "insurance_type": get_enum_value(bill.insurance_type),
            "insurance_deduction": round(bill.insurance_deduction, 2),
            "scheme_deduction": round(bill.scheme_deduction, 2),
            "tax": round(bill.tax, 2),
            "net_payable": round(bill.net_payable, 2),
            
            "is_finalized": bill.is_finalized,
            "payment_status": bill.payment_status
        }
    
    def get_current_bill(self, patient_id: str) -> Optional[Dict]:
        """Get current bill status for a patient"""
        if patient_id not in self.active_bills:
            return None
        
        bill = self.active_bills[patient_id]
        bill.calculate_totals()
        return self.get_bill_summary(bill)
    
    def get_itemized_bill(self, patient_id: str) -> Optional[Dict]:
        """Get detailed itemized bill"""
        if patient_id not in self.active_bills:
            # Check finalized bills
            for bill in self.finalized_bills:
                if bill.patient_id == patient_id:
                    return {
                        "summary": self.get_bill_summary(bill),
                        "items": [item.to_dict() for item in bill.items]
                    }
            return None
        
        bill = self.active_bills[patient_id]
        return {
            "summary": self.get_bill_summary(bill),
            "items": [item.to_dict() for item in bill.items]
        }
    
    def apply_insurance_scheme(self, patient_id: str, 
                               insurance_type: InsuranceType,
                               insurance_id: str = "") -> Dict:
        """Apply insurance scheme to existing bill"""
        if patient_id not in self.active_bills:
            return {"error": "No active bill for patient"}
        
        bill = self.active_bills[patient_id]
        bill.insurance_type = insurance_type
        bill.insurance_id = insurance_id
        
        if insurance_type in INSURANCE_COVERAGE:
            bill.insurance_coverage_percent = INSURANCE_COVERAGE[insurance_type]["coverage_percent"]
        
        bill.calculate_totals()
        
        return {
            "success": True,
            "insurance_applied": get_enum_value(insurance_type),
            "coverage_percent": bill.insurance_coverage_percent,
            "estimated_deduction": bill.insurance_deduction,
            "new_net_payable": bill.net_payable
        }
    
    def mark_paid(self, patient_id: str, amount: float, 
                  payment_mode: str = "Cash") -> Dict:
        """Mark bill as paid"""
        # Check in finalized bills
        for bill in self.finalized_bills:
            if bill.patient_id == patient_id:
                bill.payment_status = f"Paid - {payment_mode}"
                return {
                    "success": True,
                    "amount_paid": amount,
                    "payment_mode": payment_mode,
                    "status": bill.payment_status
                }
        
        return {"error": "Bill not found or not finalized"}


# Singleton instance
billing_agent = BillingAgent()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing Billing Agent...")
    print("=" * 60)
    
    # Reset state
    hospital_state.clear_all()
    
    # Create test patient
    from shared.models import Patient, PatientStatus, Bed
    
    # Add bed
    bed = Bed(id="ICU-01", bed_type=BedType.ICU, ward="ICU", floor=1)
    hospital_state.add_bed(bed)
    
    # Add patient
    patient = Patient(
        id="P001",
        name="Ramesh Kumar",
        age=55,
        status=PatientStatus.CRITICAL,
        diagnosis="Acute Myocardial Infarction",
        bed_id="ICU-01"
    )
    hospital_state.add_patient(patient)
    
    print(f"\n👤 Patient: {patient.name}")
    print(f"   Diagnosis: {patient.diagnosis}")
    print(f"   Bed: {patient.bed_id}")
    
    # Start billing
    print("\n💰 Starting billing...")
    bill = billing_agent.start_billing(
        patient_id="P001",
        insurance_type=InsuranceType.AYUSHMAN_BHARAT,
        insurance_id="PMJAY123456"
    )
    print(f"   Insurance: {bill.insurance_type.value}")
    print(f"   Coverage: {bill.insurance_coverage_percent}%")
    
    # Add medicines
    print("\n💊 Adding medicines...")
    billing_agent.add_medicine("P001", "Aspirin 325mg", quantity=4)
    billing_agent.add_medicine("P001", "Clopidogrel 75mg", quantity=1)
    billing_agent.add_medicine("P001", "Heparin 5000U", quantity=2)
    billing_agent.add_medicine("P001", "Morphine 10mg", quantity=1)
    
    # Add procedures
    print("🔬 Adding procedures...")
    billing_agent.add_procedure("P001", "ECG")
    billing_agent.add_procedure("P001", "Echocardiogram")
    billing_agent.add_procedure("P001", "Blood Test")
    
    # Add equipment
    print("🔧 Adding equipment usage...")
    billing_agent.add_equipment_usage("P001", "Ventilator", hours=24)
    billing_agent.add_equipment_usage("P001", "Monitor", hours=48)
    
    # Get current bill
    print("\n📋 Current Bill:")
    current = billing_agent.get_current_bill("P001")
    print(f"   Items: {current['total_items']}")
    print(f"   Gross Total: ₹{current['gross_total']:.2f}")
    print(f"   Insurance Deduction: ₹{current['insurance_deduction']:.2f}")
    print(f"   Net Payable: ₹{current['net_payable']:.2f}")
    
    # Finalize
    print("\n✅ Finalizing bill...")
    final = billing_agent.finalize_bill("P001")
    print(f"\n📊 Final Bill Summary:")
    print(f"   Gross Total: ₹{final['gross_total']:.2f}")
    print(f"   Insurance ({final['insurance_type']}): -₹{final['insurance_deduction']:.2f}")
    print(f"   ─────────────────────")
    print(f"   Net Payable: ₹{final['net_payable']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Billing Agent Test Complete!")
