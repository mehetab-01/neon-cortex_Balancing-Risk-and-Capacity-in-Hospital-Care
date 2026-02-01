"""
Medicine Stock Manager for VitalFlow AI.
Tracks medicine inventory, monitors daily usage, generates restock alerts.
Auto-books medicines after medical staff verification.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_enum_value
from .state import hospital_state


class StockStatus(str, Enum):
    """Medicine stock status"""
    FULL = "Full"               # 100-80%
    ADEQUATE = "Adequate"       # 80-60%
    LOW = "Low"                 # 60-40%
    CRITICAL = "Critical"       # Below 40% - ALERT TRIGGERED
    OUT_OF_STOCK = "Out of Stock"


class OrderStatus(str, Enum):
    """Medicine order status"""
    PENDING_VERIFICATION = "Pending Verification"
    VERIFIED = "Verified"
    ORDER_PLACED = "Order Placed"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


@dataclass
class MedicineStock:
    """Individual medicine stock entry"""
    medicine_id: str
    name: str
    category: str  # Antibiotic, Painkiller, Cardiac, etc.
    unit: str  # tablets, ml, vials, etc.
    
    # Stock levels
    initial_stock: int
    current_stock: int
    minimum_threshold: int  # When to trigger alert (40% of initial)
    reorder_quantity: int
    
    # Usage tracking
    daily_usage_history: List[Dict] = field(default_factory=list)  # [{date, quantity, patient_id}]
    average_daily_usage: float = 0.0
    
    # Pricing
    unit_price: float = 0.0
    supplier: str = ""
    
    # Timestamps
    last_restocked: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    
    def get_stock_percentage(self) -> float:
        """Get current stock as percentage of initial"""
        if self.initial_stock == 0:
            return 0.0
        return (self.current_stock / self.initial_stock) * 100
    
    def get_status(self) -> StockStatus:
        """Get current stock status"""
        percentage = self.get_stock_percentage()
        if percentage >= 80:
            return StockStatus.FULL
        elif percentage >= 60:
            return StockStatus.ADEQUATE
        elif percentage >= 40:
            return StockStatus.LOW
        elif percentage > 0:
            return StockStatus.CRITICAL
        else:
            return StockStatus.OUT_OF_STOCK
    
    def calculate_average_usage(self, days: int = 7) -> float:
        """Calculate average daily usage over last N days"""
        if not self.daily_usage_history:
            return 0.0
        
        cutoff = datetime.now() - timedelta(days=days)
        recent_usage = [
            u for u in self.daily_usage_history 
            if datetime.fromisoformat(u.get("date", datetime.now().isoformat())) > cutoff
        ]
        
        if not recent_usage:
            return 0.0
        
        total = sum(u.get("quantity", 0) for u in recent_usage)
        self.average_daily_usage = total / days
        return self.average_daily_usage
    
    def estimate_days_remaining(self) -> int:
        """Estimate days until stock runs out"""
        if self.average_daily_usage <= 0:
            return 999  # Unknown, assume plenty
        return int(self.current_stock / self.average_daily_usage)
    
    def to_dict(self) -> Dict:
        return {
            "medicine_id": self.medicine_id,
            "name": self.name,
            "category": self.category,
            "unit": self.unit,
            "initial_stock": self.initial_stock,
            "current_stock": self.current_stock,
            "stock_percentage": round(self.get_stock_percentage(), 1),
            "status": get_enum_value(self.get_status()),
            "minimum_threshold": self.minimum_threshold,
            "average_daily_usage": round(self.average_daily_usage, 2),
            "days_remaining": self.estimate_days_remaining(),
            "unit_price": self.unit_price,
            "supplier": self.supplier,
            "last_restocked": self.last_restocked.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None
        }


@dataclass
class MedicineOrder:
    """Order for restocking medicines"""
    order_id: str
    medicines: List[Dict]  # [{medicine_id, name, quantity, unit_price}]
    total_amount: float
    status: OrderStatus
    
    # Verification
    generated_by: str = "AI"
    verified_by: Optional[str] = None
    verification_time: Optional[datetime] = None
    verification_notes: str = ""
    
    # Order details
    supplier: str = ""
    contact_number: str = ""
    expected_delivery: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "medicines": self.medicines,
            "total_amount": self.total_amount,
            "status": get_enum_value(self.status),
            "generated_by": self.generated_by,
            "verified_by": self.verified_by,
            "verification_time": self.verification_time.isoformat() if self.verification_time else None,
            "verification_notes": self.verification_notes,
            "supplier": self.supplier,
            "contact_number": self.contact_number,
            "expected_delivery": self.expected_delivery.isoformat() if self.expected_delivery else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class StockManager:
    """
    Medicine Stock Management System.
    
    Features:
    - Track medicine inventory with initial stock = 100%
    - Monitor daily usage from nurse/doctor updates
    - Generate alerts when usage exceeds 40% threshold
    - Auto-book medicines after staff verification
    - Call/notify medicine traders
    """
    
    def __init__(self):
        self.medicines: Dict[str, MedicineStock] = {}
        self.orders: Dict[str, MedicineOrder] = {}
        self.usage_log: List[Dict] = []
        self.alerts: List[Dict] = []
        self.order_counter = 0
        
        # Supplier contacts
        self.suppliers: Dict[str, Dict] = {
            "MediPharm Distributors": {
                "contact": "+91-9876543210",
                "email": "orders@medipharm.com",
                "categories": ["Antibiotic", "Painkiller", "General"]
            },
            "CardioMed Supplies": {
                "contact": "+91-9876543211",
                "email": "orders@cardiomed.com",
                "categories": ["Cardiac", "Emergency"]
            },
            "NeuroPharma India": {
                "contact": "+91-9876543212",
                "email": "orders@neuropharma.com",
                "categories": ["Neurological", "Psychiatric"]
            }
        }
        
        # Initialize with sample medicines
        self._initialize_stock()
    
    def _initialize_stock(self):
        """Initialize with sample medicine stock"""
        sample_medicines = [
            # Cardiac medicines
            {"id": "MED-001", "name": "Aspirin 325mg", "category": "Cardiac", "unit": "tablets", "stock": 500, "price": 2.5},
            {"id": "MED-002", "name": "Clopidogrel 75mg", "category": "Cardiac", "unit": "tablets", "stock": 300, "price": 15.0},
            {"id": "MED-003", "name": "Nitroglycerin 0.4mg", "category": "Cardiac", "unit": "tablets", "stock": 200, "price": 25.0},
            {"id": "MED-004", "name": "Metoprolol 50mg", "category": "Cardiac", "unit": "tablets", "stock": 400, "price": 8.0},
            
            # Antibiotics
            {"id": "MED-005", "name": "Amoxicillin 500mg", "category": "Antibiotic", "unit": "capsules", "stock": 600, "price": 12.0},
            {"id": "MED-006", "name": "Azithromycin 500mg", "category": "Antibiotic", "unit": "tablets", "stock": 400, "price": 45.0},
            {"id": "MED-007", "name": "Ceftriaxone 1g", "category": "Antibiotic", "unit": "vials", "stock": 150, "price": 180.0},
            
            # Painkillers
            {"id": "MED-008", "name": "Paracetamol 500mg", "category": "Painkiller", "unit": "tablets", "stock": 1000, "price": 1.5},
            {"id": "MED-009", "name": "Ibuprofen 400mg", "category": "Painkiller", "unit": "tablets", "stock": 800, "price": 3.0},
            {"id": "MED-010", "name": "Tramadol 50mg", "category": "Painkiller", "unit": "tablets", "stock": 200, "price": 12.0},
            
            # Emergency medicines
            {"id": "MED-011", "name": "Adrenaline 1mg/ml", "category": "Emergency", "unit": "vials", "stock": 100, "price": 85.0},
            {"id": "MED-012", "name": "Atropine 0.6mg", "category": "Emergency", "unit": "vials", "stock": 80, "price": 45.0},
            {"id": "MED-013", "name": "Dexamethasone 4mg", "category": "Emergency", "unit": "vials", "stock": 120, "price": 55.0},
            
            # Respiratory
            {"id": "MED-014", "name": "Salbutamol Nebulizer", "category": "Respiratory", "unit": "ml", "stock": 500, "price": 35.0},
            {"id": "MED-015", "name": "Budesonide 0.5mg", "category": "Respiratory", "unit": "vials", "stock": 200, "price": 65.0},
        ]
        
        for med in sample_medicines:
            self.add_medicine(
                medicine_id=med["id"],
                name=med["name"],
                category=med["category"],
                unit=med["unit"],
                initial_stock=med["stock"],
                unit_price=med["price"]
            )
    
    def add_medicine(self, medicine_id: str, name: str, category: str, unit: str,
                     initial_stock: int, unit_price: float = 0.0, supplier: str = "") -> MedicineStock:
        """Add a new medicine to inventory"""
        medicine = MedicineStock(
            medicine_id=medicine_id,
            name=name,
            category=category,
            unit=unit,
            initial_stock=initial_stock,
            current_stock=initial_stock,
            minimum_threshold=int(initial_stock * 0.4),  # 40% threshold
            reorder_quantity=int(initial_stock * 0.5),   # Reorder 50% of initial
            unit_price=unit_price,
            supplier=supplier
        )
        self.medicines[medicine_id] = medicine
        return medicine
    
    def record_usage(self, medicine_id: str, quantity: int, patient_id: str,
                     recorded_by: str, notes: str = "") -> Dict:
        """
        Record medicine usage (called when nurse/doctor gives medicine to patient).
        This updates the stock and checks for threshold alerts.
        """
        if medicine_id not in self.medicines:
            return {"success": False, "error": f"Medicine {medicine_id} not found"}
        
        medicine = self.medicines[medicine_id]
        
        if medicine.current_stock < quantity:
            return {
                "success": False,
                "error": f"Insufficient stock. Available: {medicine.current_stock} {medicine.unit}"
            }
        
        # Update stock
        old_stock = medicine.current_stock
        medicine.current_stock -= quantity
        medicine.last_used = datetime.now()
        
        # Record usage
        usage_entry = {
            "date": datetime.now().isoformat(),
            "quantity": quantity,
            "patient_id": patient_id,
            "recorded_by": recorded_by,
            "notes": notes,
            "stock_before": old_stock,
            "stock_after": medicine.current_stock
        }
        medicine.daily_usage_history.append(usage_entry)
        self.usage_log.append({
            "medicine_id": medicine_id,
            "medicine_name": medicine.name,
            **usage_entry
        })
        
        # Recalculate average usage
        medicine.calculate_average_usage()
        
        # Check for threshold alert
        alert = self._check_threshold_alert(medicine)
        
        hospital_state.log_decision(
            "MEDICINE_USED",
            f"{quantity} {medicine.unit} of {medicine.name} given to patient {patient_id} by {recorded_by}. Stock: {medicine.current_stock}/{medicine.initial_stock} ({medicine.get_stock_percentage():.1f}%)"
        )
        
        result = {
            "success": True,
            "medicine": medicine.to_dict(),
            "usage_recorded": usage_entry
        }
        
        if alert:
            result["alert"] = alert
        
        return result
    
    def _check_threshold_alert(self, medicine: MedicineStock) -> Optional[Dict]:
        """Check if medicine has crossed 40% threshold and generate alert"""
        percentage = medicine.get_stock_percentage()
        
        if percentage <= 40 and medicine.get_status() in [StockStatus.CRITICAL, StockStatus.OUT_OF_STOCK]:
            # Check if we already have a pending order for this medicine
            pending_orders = [
                o for o in self.orders.values()
                if o.status in [OrderStatus.PENDING_VERIFICATION, OrderStatus.VERIFIED, OrderStatus.ORDER_PLACED]
                and any(m["medicine_id"] == medicine.medicine_id for m in o.medicines)
            ]
            
            if not pending_orders:
                alert = {
                    "alert_id": f"STOCK-ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "type": "STOCK_CRITICAL",
                    "medicine_id": medicine.medicine_id,
                    "medicine_name": medicine.name,
                    "current_stock": medicine.current_stock,
                    "stock_percentage": round(percentage, 1),
                    "average_daily_usage": medicine.average_daily_usage,
                    "days_remaining": medicine.estimate_days_remaining(),
                    "recommended_order_quantity": medicine.reorder_quantity,
                    "timestamp": datetime.now().isoformat(),
                    "action_required": "VERIFICATION_NEEDED"
                }
                self.alerts.append(alert)
                
                hospital_state.log_decision(
                    "STOCK_ALERT",
                    f"⚠️ {medicine.name} stock CRITICAL at {percentage:.1f}%. Only {medicine.estimate_days_remaining()} days remaining. Awaiting medical staff verification for restock."
                )
                
                # Auto-generate order pending verification
                self._generate_pending_order(medicine)
                
                return alert
        
        return None
    
    def _generate_pending_order(self, medicine: MedicineStock) -> MedicineOrder:
        """Generate a pending order for medical staff verification"""
        self.order_counter += 1
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{self.order_counter:04d}"
        
        # Find appropriate supplier
        supplier_name = ""
        supplier_contact = ""
        for name, info in self.suppliers.items():
            if medicine.category in info["categories"] or "General" in info["categories"]:
                supplier_name = name
                supplier_contact = info["contact"]
                break
        
        order = MedicineOrder(
            order_id=order_id,
            medicines=[{
                "medicine_id": medicine.medicine_id,
                "name": medicine.name,
                "quantity": medicine.reorder_quantity,
                "unit": medicine.unit,
                "unit_price": medicine.unit_price,
                "total": medicine.reorder_quantity * medicine.unit_price
            }],
            total_amount=medicine.reorder_quantity * medicine.unit_price,
            status=OrderStatus.PENDING_VERIFICATION,
            supplier=supplier_name,
            contact_number=supplier_contact
        )
        
        self.orders[order_id] = order
        return order
    
    def verify_and_place_order(self, order_id: str, verified_by: str, 
                                approve: bool, notes: str = "",
                                modified_quantities: Optional[Dict[str, int]] = None) -> Dict:
        """
        Medical staff verifies and approves/modifies the AI-generated order.
        This is the HUMAN-IN-THE-LOOP step.
        """
        if order_id not in self.orders:
            return {"success": False, "error": f"Order {order_id} not found"}
        
        order = self.orders[order_id]
        
        if order.status != OrderStatus.PENDING_VERIFICATION:
            return {"success": False, "error": f"Order already processed. Status: {get_enum_value(order.status)}"}
        
        order.verified_by = verified_by
        order.verification_time = datetime.now()
        order.verification_notes = notes
        order.updated_at = datetime.now()
        
        if not approve:
            order.status = OrderStatus.CANCELLED
            hospital_state.log_decision(
                "ORDER_CANCELLED",
                f"Order {order_id} cancelled by {verified_by}. Reason: {notes}"
            )
            return {"success": True, "order": order.to_dict(), "action": "cancelled"}
        
        # Apply modifications if any
        if modified_quantities:
            new_total = 0.0
            for med in order.medicines:
                if med["medicine_id"] in modified_quantities:
                    med["quantity"] = modified_quantities[med["medicine_id"]]
                    med["total"] = med["quantity"] * med["unit_price"]
                new_total += med["total"]
            order.total_amount = new_total
        
        order.status = OrderStatus.VERIFIED
        
        hospital_state.log_decision(
            "ORDER_VERIFIED",
            f"✅ Order {order_id} verified by {verified_by}. Total: Rs. {order.total_amount:.2f}. Ready to place with {order.supplier}."
        )
        
        return {
            "success": True,
            "order": order.to_dict(),
            "action": "verified",
            "next_step": "Call supplier or confirm to place order"
        }
    
    def place_order_with_supplier(self, order_id: str, placed_by: str) -> Dict:
        """
        Actually place the order with supplier (after verification).
        In real system, this would trigger API call/SMS to supplier.
        """
        if order_id not in self.orders:
            return {"success": False, "error": f"Order {order_id} not found"}
        
        order = self.orders[order_id]
        
        if order.status != OrderStatus.VERIFIED:
            return {"success": False, "error": f"Order must be verified first. Current status: {get_enum_value(order.status)}"}
        
        order.status = OrderStatus.ORDER_PLACED
        order.expected_delivery = datetime.now() + timedelta(hours=24)  # Assume next day delivery
        order.updated_at = datetime.now()
        
        # Generate order summary for supplier call
        order_summary = self._generate_order_summary(order)
        
        hospital_state.log_decision(
            "ORDER_PLACED",
            f"📞 Order {order_id} placed with {order.supplier}. Contact: {order.contact_number}. Expected delivery: {order.expected_delivery.strftime('%Y-%m-%d %H:%M')}"
        )
        
        return {
            "success": True,
            "order": order.to_dict(),
            "supplier_call_script": order_summary,
            "action": "order_placed"
        }
    
    def _generate_order_summary(self, order: MedicineOrder) -> str:
        """Generate summary for supplier call"""
        lines = [
            f"Hospital Medicine Order - {order.order_id}",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "-" * 40,
            "Medicines Required:",
        ]
        
        for med in order.medicines:
            lines.append(f"  • {med['name']}: {med['quantity']} {med['unit']} @ Rs.{med['unit_price']}/unit")
        
        lines.extend([
            "-" * 40,
            f"Total Order Value: Rs. {order.total_amount:.2f}",
            f"Verified By: {order.verified_by}",
            f"Expected Delivery: Urgent (within 24 hours)",
            "",
            "Please confirm order and provide delivery timeline."
        ])
        
        return "\n".join(lines)
    
    def receive_delivery(self, order_id: str, received_by: str, 
                         quantities_received: Optional[Dict[str, int]] = None) -> Dict:
        """Mark order as delivered and update stock"""
        if order_id not in self.orders:
            return {"success": False, "error": f"Order {order_id} not found"}
        
        order = self.orders[order_id]
        
        if order.status not in [OrderStatus.ORDER_PLACED, OrderStatus.IN_TRANSIT]:
            return {"success": False, "error": f"Cannot receive order. Status: {get_enum_value(order.status)}"}
        
        order.status = OrderStatus.DELIVERED
        order.updated_at = datetime.now()
        
        # Update medicine stock
        for med in order.medicines:
            medicine_id = med["medicine_id"]
            if medicine_id in self.medicines:
                quantity = quantities_received.get(medicine_id, med["quantity"]) if quantities_received else med["quantity"]
                medicine = self.medicines[medicine_id]
                medicine.current_stock += quantity
                medicine.last_restocked = datetime.now()
                
                hospital_state.log_decision(
                    "STOCK_RESTOCKED",
                    f"📦 {medicine.name} restocked. Added: {quantity} {medicine.unit}. New stock: {medicine.current_stock}/{medicine.initial_stock} ({medicine.get_stock_percentage():.1f}%)"
                )
        
        return {
            "success": True,
            "order": order.to_dict(),
            "received_by": received_by,
            "action": "delivered"
        }
    
    def get_stock_summary(self) -> Dict:
        """Get overall stock summary"""
        total_medicines = len(self.medicines)
        critical_count = sum(1 for m in self.medicines.values() if m.get_status() == StockStatus.CRITICAL)
        low_count = sum(1 for m in self.medicines.values() if m.get_status() == StockStatus.LOW)
        out_of_stock = sum(1 for m in self.medicines.values() if m.get_status() == StockStatus.OUT_OF_STOCK)
        
        return {
            "total_medicines": total_medicines,
            "status_breakdown": {
                "full": sum(1 for m in self.medicines.values() if m.get_status() == StockStatus.FULL),
                "adequate": sum(1 for m in self.medicines.values() if m.get_status() == StockStatus.ADEQUATE),
                "low": low_count,
                "critical": critical_count,
                "out_of_stock": out_of_stock
            },
            "alerts_pending": len([a for a in self.alerts if a.get("action_required") == "VERIFICATION_NEEDED"]),
            "orders_pending_verification": len([o for o in self.orders.values() if o.status == OrderStatus.PENDING_VERIFICATION]),
            "critical_medicines": [m.to_dict() for m in self.medicines.values() if m.get_status() in [StockStatus.CRITICAL, StockStatus.OUT_OF_STOCK]]
        }
    
    def get_medicine_stock(self, medicine_id: str) -> Optional[Dict]:
        """Get stock details for a specific medicine"""
        if medicine_id in self.medicines:
            return self.medicines[medicine_id].to_dict()
        return None
    
    def get_all_medicines(self) -> List[Dict]:
        """Get all medicines with stock info"""
        return [m.to_dict() for m in self.medicines.values()]
    
    def get_pending_orders(self) -> List[Dict]:
        """Get orders pending verification"""
        return [
            o.to_dict() for o in self.orders.values()
            if o.status == OrderStatus.PENDING_VERIFICATION
        ]
    
    def get_all_orders(self) -> List[Dict]:
        """Get all orders"""
        return [o.to_dict() for o in self.orders.values()]
    
    def get_usage_history(self, medicine_id: Optional[str] = None, 
                          days: int = 7) -> List[Dict]:
        """Get medicine usage history"""
        cutoff = datetime.now() - timedelta(days=days)
        
        history = [
            u for u in self.usage_log
            if datetime.fromisoformat(u["date"]) > cutoff
        ]
        
        if medicine_id:
            history = [u for u in history if u["medicine_id"] == medicine_id]
        
        return sorted(history, key=lambda x: x["date"], reverse=True)
    
    def search_medicine(self, query: str) -> List[Dict]:
        """Search medicines by name or category"""
        query_lower = query.lower()
        return [
            m.to_dict() for m in self.medicines.values()
            if query_lower in m.name.lower() or query_lower in m.category.lower()
        ]


# Global instance
stock_manager = StockManager()
