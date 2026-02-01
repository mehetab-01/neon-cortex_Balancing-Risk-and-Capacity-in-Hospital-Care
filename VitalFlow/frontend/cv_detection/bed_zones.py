"""
Bed Zone Detection
Defines hospital bed regions to distinguish between:
- Person lying on a bed (normal)
- Person fallen on the floor (emergency)
"""
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class BedZone:
    """Represents a bed area in the camera view."""
    zone_id: str
    bed_id: str  # Links to hospital bed ID
    # Bounding box coordinates (x1, y1, x2, y2) normalized 0-1
    x1: float
    y1: float
    x2: float
    y2: float
    floor: int
    ward: str
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this bed zone."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2
    
    def contains_bbox(self, bbox: Tuple[float, float, float, float], 
                      overlap_threshold: float = 0.5) -> bool:
        """
        Check if a bounding box overlaps with this bed zone.
        
        Args:
            bbox: (x1, y1, x2, y2) of the detected person
            overlap_threshold: Minimum overlap ratio to consider "on bed"
            
        Returns:
            True if person is likely on the bed
        """
        bx1, by1, bx2, by2 = bbox
        
        # Calculate intersection
        inter_x1 = max(self.x1, bx1)
        inter_y1 = max(self.y1, by1)
        inter_x2 = min(self.x2, bx2)
        inter_y2 = min(self.y2, by2)
        
        if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
            return False  # No intersection
        
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        bbox_area = (bx2 - bx1) * (by2 - by1)
        
        if bbox_area == 0:
            return False
        
        overlap_ratio = inter_area / bbox_area
        return overlap_ratio >= overlap_threshold
    
    def to_dict(self) -> Dict:
        return {
            "zone_id": self.zone_id,
            "bed_id": self.bed_id,
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "floor": self.floor,
            "ward": self.ward
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BedZone':
        return cls(**data)


class BedZoneManager:
    """
    Manages bed zone definitions for each camera.
    Allows checking if a fallen person is on a bed or on the floor.
    """
    
    def __init__(self):
        self.cameras: Dict[str, List[BedZone]] = {}
        self.config_path = Path(__file__).parent / "bed_zones_config.json"
        self._load_config()
    
    def _load_config(self):
        """Load bed zone configuration from file."""
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                for camera_id, zones in data.items():
                    self.cameras[camera_id] = [
                        BedZone.from_dict(z) for z in zones
                    ]
            except Exception as e:
                print(f"Error loading bed zones config: {e}")
    
    def save_config(self):
        """Save bed zone configuration to file."""
        data = {
            camera_id: [z.to_dict() for z in zones]
            for camera_id, zones in self.cameras.items()
        }
        self.config_path.write_text(json.dumps(data, indent=2))
    
    def add_camera(self, camera_id: str):
        """Register a new camera."""
        if camera_id not in self.cameras:
            self.cameras[camera_id] = []
    
    def add_bed_zone(self, camera_id: str, zone: BedZone):
        """Add a bed zone to a camera."""
        if camera_id not in self.cameras:
            self.cameras[camera_id] = []
        self.cameras[camera_id].append(zone)
        self.save_config()
    
    def remove_bed_zone(self, camera_id: str, zone_id: str) -> bool:
        """Remove a bed zone from a camera."""
        if camera_id not in self.cameras:
            return False
        
        original_count = len(self.cameras[camera_id])
        self.cameras[camera_id] = [
            z for z in self.cameras[camera_id] if z.zone_id != zone_id
        ]
        
        if len(self.cameras[camera_id]) < original_count:
            self.save_config()
            return True
        return False
    
    def is_on_bed(self, camera_id: str, 
                  person_bbox: Tuple[float, float, float, float]) -> Tuple[bool, Optional[str]]:
        """
        Check if a person is on a bed in the given camera view.
        
        Args:
            camera_id: Camera identifier
            person_bbox: Bounding box of detected person (x1, y1, x2, y2)
            
        Returns:
            Tuple of (is_on_bed, bed_id or None)
        """
        if camera_id not in self.cameras:
            return False, None
        
        for zone in self.cameras[camera_id]:
            if zone.contains_bbox(person_bbox, overlap_threshold=0.5):
                return True, zone.bed_id
        
        return False, None
    
    def get_floor_area(self, camera_id: str, 
                       frame_width: int, 
                       frame_height: int) -> List[Tuple[int, int, int, int]]:
        """
        Get the floor area (non-bed areas) for visualization.
        
        Returns:
            List of floor area bounding boxes in pixel coordinates
        """
        # In a simple implementation, the floor is everything not in a bed zone
        # For visualization, we return the complement of bed zones
        return []  # Would require more complex polygon math
    
    def setup_demo_zones(self, camera_id: str = "CAM-ICU-1"):
        """Setup demo bed zones for testing."""
        self.cameras[camera_id] = [
            # Bed 1 - left side of frame
            BedZone(
                zone_id=f"{camera_id}-BED1",
                bed_id="ICU-01",
                x1=0.05, y1=0.3,
                x2=0.35, y2=0.7,
                floor=4,
                ward="ICU"
            ),
            # Bed 2 - right side of frame
            BedZone(
                zone_id=f"{camera_id}-BED2",
                bed_id="ICU-02",
                x1=0.65, y1=0.3,
                x2=0.95, y2=0.7,
                floor=4,
                ward="ICU"
            )
        ]
        self.save_config()
        print(f"✅ Demo bed zones configured for {camera_id}")


# Singleton instance
bed_zone_manager = BedZoneManager()


if __name__ == "__main__":
    # Setup demo zones
    bed_zone_manager.setup_demo_zones()
    
    # Test
    test_bbox = (0.1, 0.4, 0.3, 0.6)  # Person on bed 1
    is_on_bed, bed_id = bed_zone_manager.is_on_bed("CAM-ICU-1", test_bbox)
    print(f"Test 1 - On bed: {is_on_bed}, Bed ID: {bed_id}")
    
    test_bbox_floor = (0.4, 0.8, 0.6, 0.95)  # Person on floor
    is_on_bed, bed_id = bed_zone_manager.is_on_bed("CAM-ICU-1", test_bbox_floor)
    print(f"Test 2 - On bed: {is_on_bed}, Bed ID: {bed_id}")
