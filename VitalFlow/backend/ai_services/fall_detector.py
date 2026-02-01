"""
Fall and Immobility Detection for VitalFlow AI.
Uses CCTV analysis to detect falls and prolonged immobility.

Alert Triggers:
- Person detected lying on floor
- Person motionless for ≥ 2 minutes

Workflow:
1. Alert floor admin
2. Admin verifies event  
3. If emergency confirmed: assign nurse, notify doctor, trigger triage
4. Log incident and response
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from backend.core_logic.state import hospital_state


class AlertType(str, Enum):
    """Types of CCTV alerts"""
    FALL_DETECTED = "Fall Detected"
    IMMOBILITY = "Prolonged Immobility"
    PERSON_DOWN = "Person Down"
    NO_MOVEMENT = "No Movement Detected"


class AlertStatus(str, Enum):
    """Status of an alert"""
    PENDING = "Pending Verification"
    VERIFIED_EMERGENCY = "Verified Emergency"
    FALSE_ALARM = "False Alarm"
    RESOLVED = "Resolved"


@dataclass
class CCTVAlert:
    """A CCTV-triggered alert"""
    alert_id: str
    alert_type: AlertType
    location: str  # Camera/zone ID
    zone_name: str  # Human-readable location
    timestamp: datetime
    status: AlertStatus = AlertStatus.PENDING
    
    # Detection details
    confidence: float = 0.0
    duration_seconds: float = 0.0
    frame_snapshot: Optional[bytes] = None
    
    # Response tracking
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    assigned_nurse_id: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    patient_id: Optional[str] = None  # If identified
    
    # Resolution
    resolution_notes: str = ""
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "type": self.alert_type.value,
            "location": self.location,
            "zone_name": self.zone_name,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "confidence": self.confidence,
            "duration_seconds": self.duration_seconds,
            "verified_by": self.verified_by,
            "assigned_nurse": self.assigned_nurse_id,
            "resolution": self.resolution_notes
        }


@dataclass
class ZoneTracking:
    """Tracking data for a monitored zone"""
    zone_id: str
    zone_name: str
    last_movement_time: datetime = field(default_factory=datetime.now)
    person_detected: bool = False
    person_standing: bool = True
    person_lying: bool = False
    immobility_start: Optional[datetime] = None
    alert_triggered: bool = False


class FallDetector:
    """
    CCTV fall and immobility detection system.
    
    Features:
    - Fall detection using pose estimation (simulated)
    - Immobility detection (no movement for 2+ minutes)
    - Alert workflow with verification
    - Integration with hospital state
    """
    
    IMMOBILITY_THRESHOLD_SECONDS = 120  # 2 minutes
    FALL_CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self):
        self.zones: Dict[str, ZoneTracking] = {}
        self.alerts: Dict[str, CCTVAlert] = {}
        self.alert_counter = 0
        self.is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Initialize default zones
        self._init_default_zones()
    
    def _init_default_zones(self):
        """Initialize default monitoring zones"""
        default_zones = [
            ("ZONE-ICU-1", "ICU Corridor"),
            ("ZONE-ICU-2", "ICU Room 1"),
            ("ZONE-ER-1", "Emergency Room"),
            ("ZONE-WARD-1", "General Ward A"),
            ("ZONE-WARD-2", "General Ward B"),
            ("ZONE-LOBBY", "Main Lobby"),
            ("ZONE-STAIR-1", "Stairwell A"),
            ("ZONE-BATH-1", "Washroom Area"),
        ]
        
        for zone_id, zone_name in default_zones:
            self.zones[zone_id] = ZoneTracking(
                zone_id=zone_id,
                zone_name=zone_name
            )
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        self.alert_counter += 1
        return f"CCTV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.alert_counter:03d}"
    
    def add_zone(self, zone_id: str, zone_name: str):
        """Add a new monitoring zone"""
        self.zones[zone_id] = ZoneTracking(
            zone_id=zone_id,
            zone_name=zone_name
        )
    
    def analyze_frame(self, zone_id: str, frame: Optional['np.ndarray'] = None) -> Dict:
        """
        Analyze a camera frame for falls and immobility.
        
        In real implementation, this would use:
        - OpenPose or MediaPipe for pose estimation
        - YOLOv8 for person detection
        - Background subtraction for movement
        
        Args:
            zone_id: ID of the camera zone
            frame: Camera frame (or None for simulation)
            
        Returns:
            Analysis results
        """
        if zone_id not in self.zones:
            return {"error": "Zone not found"}
        
        zone = self.zones[zone_id]
        now = datetime.now()
        
        # === SIMULATION MODE ===
        # In production, this would use actual CV analysis
        if frame is None or not CV2_AVAILABLE:
            return self._simulate_analysis(zone_id)
        
        # === REAL CV ANALYSIS ===
        results = {
            "zone_id": zone_id,
            "zone_name": zone.zone_name,
            "timestamp": now.isoformat(),
            "person_detected": False,
            "person_lying": False,
            "movement_detected": False,
            "fall_detected": False,
            "immobility_alert": False
        }
        
        # Person detection using color/motion analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Simple movement detection
        if hasattr(zone, '_prev_frame') and zone._prev_frame is not None:
            diff = cv2.absdiff(zone._prev_frame, gray)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            movement_pixels = np.sum(thresh > 0)
            movement_ratio = movement_pixels / thresh.size
            
            results["movement_detected"] = movement_ratio > 0.01
            
            if results["movement_detected"]:
                zone.last_movement_time = now
                zone.immobility_start = None
        
        zone._prev_frame = gray.copy()
        
        # Check for immobility
        if zone.person_detected and not results["movement_detected"]:
            if zone.immobility_start is None:
                zone.immobility_start = now
            else:
                immobility_duration = (now - zone.immobility_start).total_seconds()
                if immobility_duration >= self.IMMOBILITY_THRESHOLD_SECONDS:
                    results["immobility_alert"] = True
                    results["immobility_duration"] = immobility_duration
        
        return results
    
    def _simulate_analysis(self, zone_id: str) -> Dict:
        """
        Simulate CV analysis for demo/testing.
        Randomly generates events for testing the workflow.
        """
        import random
        
        zone = self.zones[zone_id]
        now = datetime.now()
        
        # Base probabilities (very low to avoid spam)
        fall_prob = 0.002  # 0.2% chance per check
        immobility_prob = 0.001
        
        results = {
            "zone_id": zone_id,
            "zone_name": zone.zone_name,
            "timestamp": now.isoformat(),
            "simulation": True,
            "person_detected": random.random() > 0.3,
            "person_lying": False,
            "movement_detected": True,
            "fall_detected": False,
            "immobility_alert": False
        }
        
        # Simulate occasional fall
        if random.random() < fall_prob:
            results["fall_detected"] = True
            results["person_lying"] = True
            results["confidence"] = random.uniform(0.7, 0.95)
        
        # Simulate occasional immobility (only if not already in alert)
        if not zone.alert_triggered and random.random() < immobility_prob:
            if zone.immobility_start is None:
                zone.immobility_start = now - timedelta(seconds=130)
            results["immobility_alert"] = True
            results["immobility_duration"] = 130
        
        return results
    
    def process_detection(self, analysis: Dict) -> Optional[CCTVAlert]:
        """
        Process analysis results and create alerts if needed.
        
        Args:
            analysis: Results from analyze_frame
            
        Returns:
            CCTVAlert if alert triggered, None otherwise
        """
        zone_id = analysis.get("zone_id")
        if not zone_id or zone_id not in self.zones:
            return None
        
        zone = self.zones[zone_id]
        
        # Check for fall detection
        if analysis.get("fall_detected"):
            if not zone.alert_triggered:
                zone.alert_triggered = True
                zone.person_lying = True
                
                alert = CCTVAlert(
                    alert_id=self._generate_alert_id(),
                    alert_type=AlertType.FALL_DETECTED,
                    location=zone_id,
                    zone_name=zone.zone_name,
                    timestamp=datetime.now(),
                    confidence=analysis.get("confidence", 0.8)
                )
                
                self.alerts[alert.alert_id] = alert
                self._log_alert(alert)
                return alert
        
        # Check for immobility
        if analysis.get("immobility_alert"):
            if not zone.alert_triggered:
                zone.alert_triggered = True
                
                alert = CCTVAlert(
                    alert_id=self._generate_alert_id(),
                    alert_type=AlertType.IMMOBILITY,
                    location=zone_id,
                    zone_name=zone.zone_name,
                    timestamp=datetime.now(),
                    duration_seconds=analysis.get("immobility_duration", 120),
                    confidence=0.9
                )
                
                self.alerts[alert.alert_id] = alert
                self._log_alert(alert)
                return alert
        
        return None
    
    def _log_alert(self, alert: CCTVAlert):
        """Log alert to hospital decision log"""
        hospital_state.log_decision(
            f"CCTV_{alert.alert_type.value.upper().replace(' ', '_')}",
            f"⚠️ {alert.alert_type.value} in {alert.zone_name}. "
            f"Confidence: {alert.confidence:.0%}. Awaiting verification.",
            alert.to_dict()
        )
    
    def verify_alert(self, alert_id: str, verified_by: str, 
                    is_emergency: bool, notes: str = "") -> Dict:
        """
        Verify an alert (admin confirms or denies).
        
        Args:
            alert_id: Alert ID to verify
            verified_by: Staff ID who verified
            is_emergency: True if confirmed emergency, False if false alarm
            notes: Verification notes
            
        Returns:
            Verification result
        """
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.verified_by = verified_by
        alert.verified_at = datetime.now()
        
        if is_emergency:
            alert.status = AlertStatus.VERIFIED_EMERGENCY
            alert.resolution_notes = notes or "Emergency confirmed"
            
            # Log and trigger response
            hospital_state.log_decision(
                "CCTV_EMERGENCY_CONFIRMED",
                f"🚨 EMERGENCY CONFIRMED: {alert.alert_type.value} in {alert.zone_name}. "
                f"Verified by {verified_by}. Initiating response.",
                {"alert_id": alert_id, "verified_by": verified_by}
            )
            
            return {
                "success": True,
                "alert_id": alert_id,
                "status": "EMERGENCY_CONFIRMED",
                "message": "Alert verified as emergency. Response initiated.",
                "next_steps": [
                    "Assign nurse to location",
                    "Notify on-duty doctor",
                    "Prepare for potential admission"
                ]
            }
        else:
            alert.status = AlertStatus.FALSE_ALARM
            alert.resolution_notes = notes or "False alarm - no action needed"
            alert.resolved_at = datetime.now()
            
            # Reset zone
            zone = self.zones.get(alert.location)
            if zone:
                zone.alert_triggered = False
                zone.immobility_start = None
            
            hospital_state.log_decision(
                "CCTV_FALSE_ALARM",
                f"ℹ️ False alarm: {alert.alert_type.value} in {alert.zone_name}. "
                f"Verified by {verified_by}.",
                {"alert_id": alert_id, "verified_by": verified_by, "notes": notes}
            )
            
            return {
                "success": True,
                "alert_id": alert_id,
                "status": "FALSE_ALARM",
                "message": "Alert marked as false alarm."
            }
    
    def assign_response(self, alert_id: str, nurse_id: str = None, 
                       doctor_id: str = None) -> Dict:
        """
        Assign staff to respond to verified emergency.
        
        Args:
            alert_id: Alert ID
            nurse_id: Nurse to assign
            doctor_id: Doctor to notify
            
        Returns:
            Assignment result
        """
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        
        if alert.status != AlertStatus.VERIFIED_EMERGENCY:
            return {"success": False, "error": "Alert not verified as emergency"}
        
        if nurse_id:
            alert.assigned_nurse_id = nurse_id
        if doctor_id:
            alert.assigned_doctor_id = doctor_id
        
        hospital_state.log_decision(
            "CCTV_RESPONSE_ASSIGNED",
            f"Response assigned for {alert.zone_name}: "
            f"Nurse: {nurse_id or 'None'}, Doctor: {doctor_id or 'None'}",
            {"alert_id": alert_id, "nurse_id": nurse_id, "doctor_id": doctor_id}
        )
        
        return {
            "success": True,
            "alert_id": alert_id,
            "nurse_assigned": nurse_id,
            "doctor_notified": doctor_id
        }
    
    def resolve_alert(self, alert_id: str, resolution_notes: str,
                     patient_id: str = None) -> Dict:
        """
        Resolve an alert after response.
        
        Args:
            alert_id: Alert ID
            resolution_notes: How the incident was resolved
            patient_id: Patient ID if patient was created/identified
            
        Returns:
            Resolution result
        """
        if alert_id not in self.alerts:
            return {"success": False, "error": "Alert not found"}
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolution_notes = resolution_notes
        alert.resolved_at = datetime.now()
        alert.patient_id = patient_id
        
        # Reset zone
        zone = self.zones.get(alert.location)
        if zone:
            zone.alert_triggered = False
            zone.immobility_start = None
            zone.person_lying = False
        
        hospital_state.log_decision(
            "CCTV_ALERT_RESOLVED",
            f"✅ Alert resolved in {alert.zone_name}: {resolution_notes}",
            {"alert_id": alert_id, "patient_id": patient_id}
        )
        
        return {
            "success": True,
            "alert_id": alert_id,
            "status": "RESOLVED",
            "duration_seconds": (alert.resolved_at - alert.timestamp).total_seconds()
        }
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all non-resolved alerts"""
        return [
            alert.to_dict() 
            for alert in self.alerts.values()
            if alert.status not in [AlertStatus.RESOLVED, AlertStatus.FALSE_ALARM]
        ]
    
    def get_alert(self, alert_id: str) -> Optional[Dict]:
        """Get specific alert details"""
        if alert_id in self.alerts:
            return self.alerts[alert_id].to_dict()
        return None
    
    def get_zone_status(self) -> List[Dict]:
        """Get status of all monitored zones"""
        return [
            {
                "zone_id": zone.zone_id,
                "zone_name": zone.zone_name,
                "person_detected": zone.person_detected,
                "person_lying": zone.person_lying,
                "alert_active": zone.alert_triggered,
                "last_movement": zone.last_movement_time.isoformat()
            }
            for zone in self.zones.values()
        ]
    
    # ===== SIMULATION FOR DEMO =====
    def simulate_fall(self, zone_id: str = None) -> Dict:
        """
        Simulate a fall event for demonstration.
        
        Args:
            zone_id: Zone to simulate fall in (default: random)
            
        Returns:
            Simulated alert
        """
        import random
        
        if zone_id is None:
            zone_id = random.choice(list(self.zones.keys()))
        
        if zone_id not in self.zones:
            return {"error": "Zone not found"}
        
        zone = self.zones[zone_id]
        zone.alert_triggered = True
        zone.person_lying = True
        
        alert = CCTVAlert(
            alert_id=self._generate_alert_id(),
            alert_type=AlertType.FALL_DETECTED,
            location=zone_id,
            zone_name=zone.zone_name,
            timestamp=datetime.now(),
            confidence=random.uniform(0.75, 0.95)
        )
        
        self.alerts[alert.alert_id] = alert
        self._log_alert(alert)
        
        return {
            "simulated": True,
            "alert": alert.to_dict()
        }
    
    def simulate_immobility(self, zone_id: str = None) -> Dict:
        """
        Simulate an immobility event for demonstration.
        
        Args:
            zone_id: Zone to simulate immobility in
            
        Returns:
            Simulated alert
        """
        import random
        
        if zone_id is None:
            zone_id = random.choice(list(self.zones.keys()))
        
        if zone_id not in self.zones:
            return {"error": "Zone not found"}
        
        zone = self.zones[zone_id]
        zone.alert_triggered = True
        
        alert = CCTVAlert(
            alert_id=self._generate_alert_id(),
            alert_type=AlertType.IMMOBILITY,
            location=zone_id,
            zone_name=zone.zone_name,
            timestamp=datetime.now(),
            duration_seconds=random.randint(120, 180),
            confidence=0.9
        )
        
        self.alerts[alert.alert_id] = alert
        self._log_alert(alert)
        
        return {
            "simulated": True,
            "alert": alert.to_dict()
        }


# Singleton instance
fall_detector = FallDetector()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing Fall Detector...")
    print("=" * 60)
    
    # Get zone status
    print("\n📍 Monitored Zones:")
    for zone in fall_detector.get_zone_status():
        print(f"   {zone['zone_id']}: {zone['zone_name']}")
    
    # Simulate a fall
    print("\n🚨 Simulating fall event...")
    result = fall_detector.simulate_fall("ZONE-WARD-1")
    alert = result["alert"]
    print(f"   Alert ID: {alert['alert_id']}")
    print(f"   Type: {alert['type']}")
    print(f"   Location: {alert['zone_name']}")
    print(f"   Confidence: {alert['confidence']:.0%}")
    
    # Verify as emergency
    print("\n✅ Admin verifying alert...")
    verify_result = fall_detector.verify_alert(
        alert['alert_id'],
        verified_by="ADMIN001",
        is_emergency=True,
        notes="Elderly patient fell near bed"
    )
    print(f"   Status: {verify_result['status']}")
    print(f"   Next steps: {verify_result['next_steps']}")
    
    # Assign response
    print("\n👨‍⚕️ Assigning response...")
    assign_result = fall_detector.assign_response(
        alert['alert_id'],
        nurse_id="N001",
        doctor_id="D001"
    )
    print(f"   Nurse: {assign_result['nurse_assigned']}")
    print(f"   Doctor: {assign_result['doctor_notified']}")
    
    # Resolve
    print("\n✅ Resolving alert...")
    resolve_result = fall_detector.resolve_alert(
        alert['alert_id'],
        resolution_notes="Patient assisted back to bed. Minor bruise treated.",
        patient_id="P-NEW-001"
    )
    print(f"   Status: {resolve_result['status']}")
    print(f"   Duration: {resolve_result['duration_seconds']:.0f} seconds")
    
    # Check active alerts
    print(f"\n📋 Active alerts: {len(fall_detector.get_active_alerts())}")
    
    print("\n" + "=" * 60)
    print("✅ Fall Detector Test Complete!")
