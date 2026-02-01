"""
Event bus for real-time updates across VitalFlow modules.
Simple pub-sub pattern for decoupled communication.
"""
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading


class EventType(str, Enum):
    """Available event types in the system."""
    # Patient Events
    PATIENT_ADMITTED = "patient_admitted"
    PATIENT_DISCHARGED = "patient_discharged"
    PATIENT_TRANSFERRED = "patient_transferred"
    PATIENT_STATUS_CHANGED = "patient_status_changed"
    PATIENT_VITALS_UPDATED = "patient_vitals_updated"
    
    # Bed Events
    BED_ASSIGNED = "bed_assigned"
    BED_RELEASED = "bed_released"
    BED_SWAP_INITIATED = "bed_swap_initiated"
    BED_SWAP_COMPLETED = "bed_swap_completed"
    
    # Staff Events
    STAFF_PUNCH_IN = "staff_punch_in"
    STAFF_PUNCH_OUT = "staff_punch_out"
    STAFF_ASSIGNED = "staff_assigned"
    STAFF_FATIGUE_WARNING = "staff_fatigue_warning"
    
    # Alert Events
    CODE_BLUE = "code_blue"
    VITALS_WARNING = "vitals_warning"
    VITALS_CRITICAL = "vitals_critical"
    
    # Ambulance Events
    AMBULANCE_DISPATCHED = "ambulance_dispatched"
    AMBULANCE_ARRIVING = "ambulance_arriving"
    AMBULANCE_ARRIVED = "ambulance_arrived"
    
    # Stock Management Events
    STOCK_LOW = "stock_low"
    STOCK_CRITICAL = "stock_critical"
    STOCK_REORDER = "stock_reorder"
    STOCK_RESTOCKED = "stock_restocked"
    
    # Prescription Events
    PRESCRIPTION_UPLOADED = "prescription_uploaded"
    PRESCRIPTION_SCANNED = "prescription_scanned"
    PRESCRIPTION_VERIFIED = "prescription_verified"
    MEDICINE_ALERT = "medicine_alert"
    MEDICINE_GIVEN = "medicine_given"
    MEDICINE_MISSED = "medicine_missed"
    
    # Patient Report Events
    VITALS_RECORDED = "vitals_recorded"
    RECOVERY_UPDATED = "recovery_updated"
    MEAL_SERVED = "meal_served"
    DISCHARGE_ESTIMATED = "discharge_estimated"
    
    # Doctor Alert Events
    DOCTOR_ALERT_CRITICAL = "doctor_alert_critical"
    DOCTOR_ALERT_ACKNOWLEDGED = "doctor_alert_acknowledged"
    DOCTOR_ALERT_ESCALATED = "doctor_alert_escalated"
    DOCTOR_ON_LEAVE = "doctor_on_leave"
    
    # System Events
    STATE_UPDATED = "state_updated"
    DECISION_LOGGED = "decision_logged"


@dataclass
class Event:
    """Event data structure."""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


class EventBus:
    """
    Simple event bus for publish-subscribe pattern.
    Thread-safe for concurrent access.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize event bus."""
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 100
        self._global_subscribers: List[Callable] = []
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to all events.
        
        Args:
            callback: Function to call for any event
        """
        self._global_subscribers.append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event
            callback: Callback to remove
            
        Returns:
            True if callback was removed
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                return True
            except ValueError:
                return False
        return False
    
    def publish(self, event_type: EventType, data: Dict[str, Any], source: str = "system") -> Event:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source of the event
            
        Returns:
            The published Event object
        """
        event = Event(event_type=event_type, data=data, source=source)
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify specific subscribers
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event subscriber: {e}")
        
        # Notify global subscribers
        for callback in self._global_subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in global event subscriber: {e}")
        
        return event
    
    def get_history(self, event_type: EventType = None, limit: int = 50) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        if event_type:
            filtered = [e for e in self._event_history if e.event_type == event_type]
            return filtered[-limit:]
        return self._event_history[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()
    
    def get_subscriber_count(self, event_type: EventType = None) -> int:
        """Get number of subscribers for an event type."""
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(subs) for subs in self._subscribers.values()) + len(self._global_subscribers)


# Singleton instance
event_bus = EventBus()


# ============== CONVENIENCE FUNCTIONS ==============

def emit_patient_admitted(patient_id: str, patient_name: str, priority: int, bed_id: str = None):
    """Emit patient admitted event."""
    event_bus.publish(
        EventType.PATIENT_ADMITTED,
        {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "priority": priority,
            "bed_id": bed_id
        }
    )


def emit_vitals_warning(patient_id: str, bed_id: str, spo2: float, heart_rate: int):
    """Emit vitals warning event."""
    event_bus.publish(
        EventType.VITALS_WARNING,
        {
            "patient_id": patient_id,
            "bed_id": bed_id,
            "spo2": spo2,
            "heart_rate": heart_rate
        }
    )


def emit_bed_swap(patient_out: str, patient_in: str, bed_freed: str, bed_assigned: str):
    """Emit bed swap event."""
    event_bus.publish(
        EventType.BED_SWAP_COMPLETED,
        {
            "patient_out": patient_out,
            "patient_in": patient_in,
            "bed_freed": bed_freed,
            "bed_assigned": bed_assigned
        }
    )


def emit_fatigue_warning(staff_id: str, staff_name: str, hours_worked: float):
    """Emit staff fatigue warning event."""
    event_bus.publish(
        EventType.STAFF_FATIGUE_WARNING,
        {
            "staff_id": staff_id,
            "staff_name": staff_name,
            "hours_worked": hours_worked
        }
    )


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing EventBus...")
    
    # Reset for testing
    bus = EventBus()
    bus._subscribers.clear()
    bus._global_subscribers.clear()
    bus.clear_history()
    
    # Test subscriber
    received_events = []
    
    def on_patient_admitted(event: Event):
        received_events.append(event)
        print(f"  Received: {event.event_type.value} - {event.data}")
    
    # Subscribe
    bus.subscribe(EventType.PATIENT_ADMITTED, on_patient_admitted)
    print("✓ Subscribed to PATIENT_ADMITTED")
    
    # Publish
    event = bus.publish(
        EventType.PATIENT_ADMITTED,
        {"patient_id": "P001", "patient_name": "John Doe", "priority": 1}
    )
    
    assert len(received_events) == 1
    assert received_events[0].data["patient_id"] == "P001"
    print("✓ Event published and received")
    
    # Test global subscriber
    all_events = []
    
    def on_any_event(event: Event):
        all_events.append(event)
    
    bus.subscribe_all(on_any_event)
    
    bus.publish(EventType.BED_ASSIGNED, {"bed_id": "ICU-01"})
    bus.publish(EventType.VITALS_WARNING, {"patient_id": "P001", "spo2": 88})
    
    assert len(all_events) == 2
    print("✓ Global subscriber works")
    
    # Test history
    history = bus.get_history()
    assert len(history) == 3  # 3 events total
    print(f"✓ Event history: {len(history)} events")
    
    # Test filtered history
    patient_events = bus.get_history(EventType.PATIENT_ADMITTED)
    assert len(patient_events) == 1
    print("✓ Filtered history works")
    
    # Test convenience functions
    emit_vitals_warning("P002", "GEN-01", 85.0, 140)
    assert len(bus.get_history(EventType.VITALS_WARNING)) == 2
    print("✓ Convenience functions work")
    
    # Test subscriber count
    count = bus.get_subscriber_count()
    assert count >= 2
    print(f"✓ Subscriber count: {count}")
    
    # Test unsubscribe
    result = bus.unsubscribe(EventType.PATIENT_ADMITTED, on_patient_admitted)
    assert result == True
    print("✓ Unsubscribe works")
    
    print("\n✅ All EventBus tests passed!")
