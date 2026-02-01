"""
Fall Detection System
Main integration module for CCTV fall and immobility detection

Emergency Logic:
- Person is lying/fallen
- NOT inside a bed zone
- Motionless for ≥ 2 minutes (10 seconds for demo)

Workflow:
1. Alert floor admin
2. Admin verifies event
3. If confirmed: assign nurse, notify doctor, trigger triage
4. Log incident
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import time

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import cv2
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

from .model_setup import load_pose_model
from .bed_zones import bed_zone_manager, BedZone
from .person_analysis import person_analyzer, PersonDetection

# Import backend for event triggering
try:
    from backend.core_logic.state import hospital_state
    from shared.events import EventBus, Event, EventType
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "Info"
    WARNING = "Warning"
    CRITICAL = "Critical"
    EMERGENCY = "Emergency"


class AlertStatus(str, Enum):
    """Status of a fall alert."""
    PENDING = "Pending Verification"
    VERIFIED = "Verified Emergency"
    FALSE_ALARM = "False Alarm"
    RESOLVED = "Resolved"


@dataclass
class FallAlert:
    """A fall detection alert."""
    alert_id: str
    camera_id: str
    zone_name: str
    timestamp: datetime
    
    # Detection details
    person_id: int
    bbox: Tuple[float, float, float, float]
    confidence: float = 0.0
    is_on_bed: bool = False
    bed_id: Optional[str] = None
    immobility_duration_seconds: float = 0.0
    
    # Status
    status: AlertStatus = AlertStatus.PENDING
    severity: AlertSeverity = AlertSeverity.WARNING
    
    # Response tracking
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    assigned_nurse_id: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    
    # Resolution
    resolution_notes: str = ""
    resolved_at: Optional[datetime] = None
    
    # Snapshot for verification
    frame_snapshot_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "camera_id": self.camera_id,
            "zone_name": self.zone_name,
            "timestamp": self.timestamp.isoformat(),
            "person_id": self.person_id,
            "confidence": self.confidence,
            "is_on_bed": self.is_on_bed,
            "immobility_seconds": self.immobility_duration_seconds,
            "status": self.status.value,
            "severity": self.severity.value,
            "verified_by": self.verified_by,
            "assigned_nurse": self.assigned_nurse_id,
            "assigned_doctor": self.assigned_doctor_id
        }


class FallDetectionSystem:
    """
    Main fall detection system integrating:
    - YOLOv8-Pose for person and pose detection
    - Bed zone awareness
    - Movement tracking
    - Alert management
    - Backend integration
    """
    
    # Configuration
    IMMOBILITY_THRESHOLD_SECONDS = 120  # 2 minutes for production
    DEMO_IMMOBILITY_THRESHOLD = 10  # 10 seconds for demo
    CONFIDENCE_THRESHOLD = 0.5
    FRAME_PROCESS_INTERVAL = 0.5  # Process every 0.5 seconds
    
    def __init__(self, demo_mode: bool = True):
        """
        Initialize the fall detection system.
        
        Args:
            demo_mode: If True, use shorter thresholds for demo
        """
        self.demo_mode = demo_mode
        self.immobility_threshold = (
            self.DEMO_IMMOBILITY_THRESHOLD if demo_mode 
            else self.IMMOBILITY_THRESHOLD_SECONDS
        )
        
        self.model = None
        self.is_initialized = False
        self.is_monitoring = False
        
        # Alert management
        self.alerts: Dict[str, FallAlert] = {}
        self.alert_counter = 0
        
        # Active monitoring
        self.active_cameras: Dict[str, bool] = {}
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_alert_callback = None
    
    def initialize(self) -> bool:
        """
        Initialize the detection system.
        Loads the YOLOv8-Pose model.
        
        Returns:
            True if successful
        """
        if self.is_initialized:
            return True
        
        try:
            self.model = load_pose_model()
            if self.model:
                self.is_initialized = True
                print("✅ Fall Detection System initialized")
                return True
            else:
                print("⚠️ Running in simulation mode (model not available)")
                self.is_initialized = True  # Allow simulation mode
                return True
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            return False
    
    def process_frame(self, 
                      frame, 
                      camera_id: str = "CAM-1") -> Dict:
        """
        Process a video frame for fall detection.
        
        Args:
            frame: Video frame (numpy array or None for simulation)
            camera_id: Camera identifier
            
        Returns:
            Dict with detection results
        """
        results = {
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat(),
            "persons_detected": 0,
            "falls_detected": 0,
            "alerts": []
        }
        
        if not self.is_initialized:
            if not self.initialize():
                return results
        
        # ========== RUN DETECTION ==========
        if self.model and frame is not None and CV_AVAILABLE:
            # Run YOLOv8-Pose
            detections = self._run_yolo_detection(frame, camera_id)
        else:
            # Simulation mode
            detections = self._simulate_detection(camera_id)
        
        results["persons_detected"] = len(detections)
        
        # ========== ANALYZE EACH DETECTION ==========
        for detection in detections:
            # Check if on bed
            is_on_bed, bed_id = bed_zone_manager.is_on_bed(
                camera_id, detection.bbox
            )
            
            # Check movement
            is_moving = person_analyzer.check_movement(
                detection.person_id, detection.bbox
            )
            
            stationary_duration = person_analyzer.get_stationary_duration(
                detection.person_id
            )
            
            # ========== FALL DETECTION LOGIC ==========
            # Alert if: lying + NOT on bed + stationary for threshold
            if detection.is_lying and not is_on_bed:
                if stationary_duration >= self.immobility_threshold:
                    # TRIGGER ALERT
                    alert = self._create_alert(
                        camera_id=camera_id,
                        detection=detection,
                        is_on_bed=is_on_bed,
                        bed_id=bed_id,
                        immobility_seconds=stationary_duration
                    )
                    
                    if alert:
                        results["falls_detected"] += 1
                        results["alerts"].append(alert.to_dict())
                        
                        # Trigger callback
                        if self.on_alert_callback:
                            self.on_alert_callback(alert)
                        
                        # Log to backend
                        self._log_to_backend(alert)
        
        return results
    
    def _run_yolo_detection(self, frame, camera_id: str) -> List[PersonDetection]:
        """Run YOLOv8-Pose detection on a frame."""
        detections = []
        
        try:
            # Run inference
            results = self.model(frame, verbose=False)
            
            for result in results:
                if result.boxes is None:
                    continue
                
                # Get frame dimensions
                h, w = frame.shape[:2]
                
                for idx, box in enumerate(result.boxes):
                    # Get normalized bounding box
                    x1, y1, x2, y2 = box.xyxyn[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    
                    if confidence < self.CONFIDENCE_THRESHOLD:
                        continue
                    
                    # Get keypoints if available
                    keypoints = None
                    if result.keypoints is not None:
                        kps = result.keypoints[idx].xyn.cpu().numpy()
                        confs = result.keypoints[idx].conf.cpu().numpy()
                        keypoints = [
                            (float(kps[i][0]), float(kps[i][1]), float(confs[i]))
                            for i in range(len(kps))
                        ]
                    
                    # Analyze pose
                    detection = person_analyzer.analyze_pose(
                        bbox=(float(x1), float(y1), float(x2), float(y2)),
                        keypoints=keypoints
                    )
                    detection.confidence = confidence
                    
                    detections.append(detection)
            
        except Exception as e:
            print(f"Detection error: {e}")
        
        return detections
    
    def _simulate_detection(self, camera_id: str) -> List[PersonDetection]:
        """Simulate detection for demo/testing."""
        import random
        
        # Randomly simulate a person
        if random.random() < 0.7:  # 70% chance of detection
            # Simulate different scenarios
            scenario = random.choice(["standing", "lying_bed", "lying_floor", "sitting"])
            
            if scenario == "standing":
                bbox = (0.4, 0.2, 0.6, 0.9)
            elif scenario == "lying_bed":
                bbox = (0.1, 0.35, 0.3, 0.65)  # On bed zone
            elif scenario == "lying_floor":
                bbox = (0.4, 0.75, 0.7, 0.95)  # On floor
            else:
                bbox = (0.3, 0.4, 0.5, 0.8)
            
            detection = person_analyzer.analyze_pose(bbox)
            detection.confidence = random.uniform(0.7, 0.95)
            
            return [detection]
        
        return []
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self.alert_counter += 1
        return f"FALL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.alert_counter:03d}"
    
    def _create_alert(self, 
                      camera_id: str,
                      detection: PersonDetection,
                      is_on_bed: bool,
                      bed_id: Optional[str],
                      immobility_seconds: float) -> Optional[FallAlert]:
        """Create a new fall alert."""
        # Check if alert already exists for this person
        existing_alert_key = f"{camera_id}_{detection.person_id}"
        
        if existing_alert_key in self.alerts:
            existing = self.alerts[existing_alert_key]
            if existing.status == AlertStatus.PENDING:
                # Update duration
                existing.immobility_duration_seconds = immobility_seconds
                return None  # Don't create duplicate
        
        # Determine severity
        if immobility_seconds > 300:  # > 5 minutes
            severity = AlertSeverity.EMERGENCY
        elif immobility_seconds > 120:  # > 2 minutes
            severity = AlertSeverity.CRITICAL
        else:
            severity = AlertSeverity.WARNING
        
        alert = FallAlert(
            alert_id=self._generate_alert_id(),
            camera_id=camera_id,
            zone_name=f"Camera {camera_id}",
            timestamp=datetime.now(),
            person_id=detection.person_id,
            bbox=detection.bbox,
            confidence=detection.confidence,
            is_on_bed=is_on_bed,
            bed_id=bed_id,
            immobility_duration_seconds=immobility_seconds,
            severity=severity
        )
        
        self.alerts[existing_alert_key] = alert
        return alert
    
    def verify_alert(self, 
                     alert_id: str, 
                     verified_by: str,
                     is_emergency: bool,
                     notes: str = "") -> bool:
        """
        Verify an alert (human-in-the-loop).
        
        Args:
            alert_id: Alert ID to verify
            verified_by: Admin/staff ID who verified
            is_emergency: True if confirmed emergency
            notes: Optional verification notes
            
        Returns:
            True if successful
        """
        # Find alert
        alert = None
        for a in self.alerts.values():
            if a.alert_id == alert_id:
                alert = a
                break
        
        if not alert:
            return False
        
        alert.verified_by = verified_by
        alert.verified_at = datetime.now()
        
        if is_emergency:
            alert.status = AlertStatus.VERIFIED
            # Trigger emergency response
            self._trigger_emergency_response(alert)
        else:
            alert.status = AlertStatus.FALSE_ALARM
            alert.resolution_notes = notes or "Verified as false alarm"
        
        return True
    
    def _trigger_emergency_response(self, alert: FallAlert):
        """Trigger emergency response workflow."""
        if not BACKEND_AVAILABLE:
            print(f"[EMERGENCY] {alert.alert_id}: Would trigger response")
            return
        
        # 1. Log to hospital state
        hospital_state.log_decision(
            "CCTV_EMERGENCY_VERIFIED",
            f"Fall detected and verified at {alert.zone_name}",
            {
                "alert_id": alert.alert_id,
                "camera_id": alert.camera_id,
                "immobility_seconds": alert.immobility_duration_seconds,
                "verified_by": alert.verified_by
            }
        )
        
        # 2. Assign nurse (would integrate with staff_manager)
        # 3. Notify doctor
        # 4. Trigger triage if needed
        
        print(f"✅ Emergency response triggered for {alert.alert_id}")
    
    def _log_to_backend(self, alert: FallAlert):
        """Log alert to backend state."""
        if not BACKEND_AVAILABLE:
            return
        
        hospital_state.log_decision(
            "CCTV_FALL_DETECTED",
            f"Potential fall detected at {alert.zone_name}. Awaiting verification.",
            {
                "alert_id": alert.alert_id,
                "camera_id": alert.camera_id,
                "confidence": alert.confidence,
                "immobility_seconds": alert.immobility_duration_seconds
            }
        )
    
    def get_pending_alerts(self) -> List[FallAlert]:
        """Get all pending (unverified) alerts."""
        return [
            a for a in self.alerts.values()
            if a.status == AlertStatus.PENDING
        ]
    
    def start_video_monitoring(self, 
                               video_source: str,
                               camera_id: str = "CAM-1") -> bool:
        """
        Start monitoring a video source.
        
        Args:
            video_source: Path to video file or camera index
            camera_id: Identifier for this camera
            
        Returns:
            True if started successfully
        """
        if not CV_AVAILABLE:
            print("OpenCV not available for video monitoring")
            return False
        
        self.active_cameras[camera_id] = True
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._video_monitoring_loop,
            args=(video_source, camera_id),
            daemon=True
        )
        self._monitor_thread.start()
        
        return True
    
    def stop_monitoring(self, camera_id: str = None):
        """Stop monitoring a camera or all cameras."""
        if camera_id:
            self.active_cameras[camera_id] = False
        else:
            for cam_id in self.active_cameras:
                self.active_cameras[cam_id] = False
    
    def _video_monitoring_loop(self, video_source: str, camera_id: str):
        """Video monitoring loop (runs in thread)."""
        try:
            if video_source.isdigit():
                cap = cv2.VideoCapture(int(video_source))
            else:
                cap = cv2.VideoCapture(video_source)
            
            if not cap.isOpened():
                print(f"Failed to open video source: {video_source}")
                return
            
            while self.active_cameras.get(camera_id, False):
                ret, frame = cap.read()
                
                if not ret:
                    # Loop video for demo
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Process frame
                results = self.process_frame(frame, camera_id)
                
                # Rate limiting
                time.sleep(self.FRAME_PROCESS_INTERVAL)
            
            cap.release()
            
        except Exception as e:
            print(f"Monitoring error: {e}")


# Singleton instance
fall_detection_system = FallDetectionSystem(demo_mode=True)


if __name__ == "__main__":
    print("Testing Fall Detection System...")
    
    # Initialize
    system = FallDetectionSystem(demo_mode=True)
    system.initialize()
    
    # Setup demo bed zones
    bed_zone_manager.setup_demo_zones("CAM-1")
    
    # Simulate some frames
    for i in range(5):
        print(f"\n--- Frame {i+1} ---")
        results = system.process_frame(None, "CAM-1")
        print(f"Persons detected: {results['persons_detected']}")
        print(f"Falls detected: {results['falls_detected']}")
        if results['alerts']:
            print(f"Alerts: {results['alerts']}")
        time.sleep(1)
    
    print("\n✅ Test complete")
