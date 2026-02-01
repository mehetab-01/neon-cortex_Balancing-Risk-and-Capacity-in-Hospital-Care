"""
Person Analysis using YOLOv8-Pose
Analyzes detected persons for:
- Pose estimation (standing, sitting, lying)
- Fall detection
- Movement tracking
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from .model_setup import CORE_KEYPOINTS, UPPER_BODY_KEYPOINTS, LOWER_BODY_KEYPOINTS


@dataclass
class PersonDetection:
    """Detected person with pose analysis."""
    person_id: int
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2 (normalized 0-1)
    keypoints: Optional[List[Tuple[float, float, float]]] = None  # x, y, confidence
    confidence: float = 0.0
    
    # Pose analysis
    pose: str = "unknown"  # standing, sitting, lying, fallen
    is_lying: bool = False
    is_moving: bool = True
    
    # Tracking
    last_seen: datetime = None
    stationary_since: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_seen is None:
            self.last_seen = datetime.now()


class PersonAnalyzer:
    """
    Analyzes detected persons for fall detection.
    Uses pose keypoints to determine body orientation.
    """
    
    # Thresholds
    LYING_ASPECT_RATIO_THRESHOLD = 1.5  # Width > 1.5x height suggests lying
    VERTICAL_ALIGNMENT_THRESHOLD = 0.3  # Keypoint vertical spread
    CONFIDENCE_THRESHOLD = 0.5  # Minimum keypoint confidence
    
    def __init__(self):
        self.tracked_persons: Dict[int, PersonDetection] = {}
        self.person_id_counter = 0
    
    def analyze_pose(self, 
                     bbox: Tuple[float, float, float, float],
                     keypoints: Optional[List[Tuple[float, float, float]]] = None) -> PersonDetection:
        """
        Analyze a detected person's pose.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2) normalized 0-1
            keypoints: List of (x, y, confidence) for each keypoint
            
        Returns:
            PersonDetection with pose analysis
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        
        # Assign ID
        person_id = self._get_or_create_person_id(bbox)
        
        detection = PersonDetection(
            person_id=person_id,
            bbox=bbox,
            keypoints=keypoints,
            confidence=0.0
        )
        
        # ========== ASPECT RATIO ANALYSIS ==========
        # Lying person has width > height typically
        aspect_ratio = width / height if height > 0 else 1
        
        if aspect_ratio > self.LYING_ASPECT_RATIO_THRESHOLD:
            detection.is_lying = True
            detection.pose = "lying"
        
        # ========== KEYPOINT ANALYSIS (if available) ==========
        if keypoints and len(keypoints) >= 17:
            pose_from_keypoints = self._analyze_keypoints(keypoints)
            
            if pose_from_keypoints:
                detection.pose = pose_from_keypoints
                detection.is_lying = pose_from_keypoints in ["lying", "fallen"]
            
            # Calculate average confidence
            confidences = [kp[2] for kp in keypoints if kp[2] > 0]
            if confidences:
                detection.confidence = sum(confidences) / len(confidences)
        
        # Update tracking
        self.tracked_persons[person_id] = detection
        
        return detection
    
    def _get_or_create_person_id(self, bbox: Tuple[float, float, float, float]) -> int:
        """Simple person tracking by bbox overlap."""
        # Find existing person with similar bbox
        for pid, person in self.tracked_persons.items():
            if self._bbox_iou(bbox, person.bbox) > 0.3:
                return pid
        
        # New person
        self.person_id_counter += 1
        return self.person_id_counter
    
    def _bbox_iou(self, bbox1: Tuple, bbox2: Tuple) -> float:
        """Calculate Intersection over Union of two bboxes."""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x1 >= x2 or y1 >= y2:
            return 0.0
        
        inter_area = (x2 - x1) * (y2 - y1)
        
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        
        union_area = area1 + area2 - inter_area
        
        return inter_area / union_area if union_area > 0 else 0
    
    def _analyze_keypoints(self, keypoints: List[Tuple[float, float, float]]) -> str:
        """
        Analyze keypoints to determine pose.
        
        Key insights:
        - Standing: shoulders above hips above ankles (vertical alignment)
        - Sitting: shoulders and hips at similar height, ankles lower
        - Lying: all keypoints at similar height (horizontal alignment)
        - Fallen: lying + not in bed zone + sudden change
        """
        try:
            # Get core keypoints (shoulders and hips)
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]
            left_hip = keypoints[11]
            right_hip = keypoints[12]
            
            # Check confidence
            core_kps = [left_shoulder, right_shoulder, left_hip, right_hip]
            if not all(kp[2] > self.CONFIDENCE_THRESHOLD for kp in core_kps):
                return None  # Low confidence
            
            # Calculate body angle
            shoulder_center = (
                (left_shoulder[0] + right_shoulder[0]) / 2,
                (left_shoulder[1] + right_shoulder[1]) / 2
            )
            hip_center = (
                (left_hip[0] + right_hip[0]) / 2,
                (left_hip[1] + right_hip[1]) / 2
            )
            
            # Vertical difference (normalized)
            vertical_diff = abs(shoulder_center[1] - hip_center[1])
            horizontal_diff = abs(shoulder_center[0] - hip_center[0])
            
            # Calculate body angle from vertical
            if vertical_diff < 0.01:  # Avoid division by zero
                angle = 90  # Nearly horizontal
            else:
                angle = math.degrees(math.atan(horizontal_diff / vertical_diff))
            
            # Classify pose based on angle
            if angle < 20:
                return "standing"
            elif angle < 45:
                return "sitting"
            else:
                return "lying"
            
        except (IndexError, TypeError):
            return None
    
    def check_movement(self, person_id: int, 
                       current_bbox: Tuple[float, float, float, float],
                       movement_threshold: float = 0.02) -> bool:
        """
        Check if a person has moved since last detection.
        
        Args:
            person_id: Person ID to check
            current_bbox: Current bounding box
            movement_threshold: Minimum movement to be considered "moving"
            
        Returns:
            True if person is moving
        """
        if person_id not in self.tracked_persons:
            return True  # New person, assume moving
        
        previous = self.tracked_persons[person_id]
        prev_bbox = previous.bbox
        
        # Calculate center movement
        prev_center = (
            (prev_bbox[0] + prev_bbox[2]) / 2,
            (prev_bbox[1] + prev_bbox[3]) / 2
        )
        curr_center = (
            (current_bbox[0] + current_bbox[2]) / 2,
            (current_bbox[1] + current_bbox[3]) / 2
        )
        
        movement = math.sqrt(
            (curr_center[0] - prev_center[0]) ** 2 +
            (curr_center[1] - prev_center[1]) ** 2
        )
        
        is_moving = movement > movement_threshold
        
        # Update stationary tracking
        if not is_moving:
            if previous.stationary_since is None:
                previous.stationary_since = datetime.now()
        else:
            previous.stationary_since = None
        
        previous.is_moving = is_moving
        previous.last_seen = datetime.now()
        
        return is_moving
    
    def get_stationary_duration(self, person_id: int) -> float:
        """
        Get how long a person has been stationary (in seconds).
        
        Returns:
            Seconds stationary, or 0 if moving
        """
        if person_id not in self.tracked_persons:
            return 0
        
        person = self.tracked_persons[person_id]
        
        if person.stationary_since is None:
            return 0
        
        duration = (datetime.now() - person.stationary_since).total_seconds()
        return duration


# Singleton instance
person_analyzer = PersonAnalyzer()


if __name__ == "__main__":
    # Test pose analysis
    print("Testing person analysis...")
    
    # Simulate standing person (tall bbox)
    standing_bbox = (0.4, 0.2, 0.6, 0.9)
    result = person_analyzer.analyze_pose(standing_bbox)
    print(f"Standing test: pose={result.pose}, is_lying={result.is_lying}")
    
    # Simulate lying person (wide bbox)
    lying_bbox = (0.1, 0.7, 0.9, 0.95)
    result = person_analyzer.analyze_pose(lying_bbox)
    print(f"Lying test: pose={result.pose}, is_lying={result.is_lying}")
