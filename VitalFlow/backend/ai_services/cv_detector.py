"""
Computer vision for bed occupancy detection.
Uses OpenCV to analyze video feeds (simulated for hackathon).
"""
import sys
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not installed. Run: pip install opencv-python")


class BedDetector:
    """
    Computer vision service for bed occupancy detection.
    Uses OpenCV for real camera analysis with simulation fallback.
    """
    
    def __init__(self):
        """Initialize bed detector with default configuration."""
        # Define ROIs (regions of interest) for each bed in a ward camera view
        # Format: {bed_id: (x, y, width, height)}
        # These would be calibrated for real cameras
        self.bed_rois = {
            "BED-1": (50, 50, 200, 150),
            "BED-2": (300, 50, 200, 150),
            "BED-3": (550, 50, 200, 150),
            "BED-4": (50, 250, 200, 150),
            "BED-5": (300, 250, 200, 150),
            "BED-6": (550, 250, 200, 150),
        }
        
        # Threshold for considering a bed occupied
        self.occupancy_threshold = 0.3  # 30% pixel difference from empty
        
        # Store reference "empty bed" images for comparison
        self.empty_references: Dict[str, 'np.ndarray'] = {}
        
        # Movement detection threshold
        self.movement_threshold = 0.1
        
        # Last detected states for change detection
        self._last_states: Dict[str, bool] = {}
    
    def configure_beds(self, bed_config: Dict[str, Tuple[int, int, int, int]]):
        """
        Configure bed ROIs for a specific ward layout.
        
        Args:
            bed_config: Dict mapping bed_id to (x, y, width, height)
        """
        self.bed_rois = bed_config
    
    def calibrate_empty_beds(self, frame: 'np.ndarray', bed_ids: List[str] = None):
        """
        Capture reference images of empty beds for comparison.
        Call this during setup with an empty ward.
        
        Args:
            frame: Image frame of empty ward
            bed_ids: Optional list of bed IDs to calibrate (default: all)
        """
        if not CV2_AVAILABLE:
            print("OpenCV not available for calibration")
            return
        
        bed_ids = bed_ids or list(self.bed_rois.keys())
        
        for bed_id in bed_ids:
            if bed_id in self.bed_rois:
                roi = self.bed_rois[bed_id]
                x, y, w, h = roi
                self.empty_references[bed_id] = frame[y:y+h, x:x+w].copy()
                print(f"✓ Calibrated empty reference for {bed_id}")
    
    def detect_occupancy(self, frame: 'np.ndarray') -> Dict[str, bool]:
        """
        Analyze frame and return occupancy status for each bed.
        
        Args:
            frame: Current camera frame
            
        Returns:
            Dict mapping bed_id to is_occupied boolean
        """
        if not CV2_AVAILABLE:
            return self.simulate_occupancy()
        
        results = {}
        
        for bed_id, roi in self.bed_rois.items():
            x, y, w, h = roi
            
            # Bounds checking
            if y + h > frame.shape[0] or x + w > frame.shape[1]:
                results[bed_id] = False
                continue
            
            current_roi = frame[y:y+h, x:x+w]
            
            if bed_id in self.empty_references:
                # Compare with empty reference
                is_occupied = self._compare_regions(
                    self.empty_references[bed_id],
                    current_roi
                )
            else:
                # Fallback: use pixel intensity analysis
                is_occupied = self._analyze_intensity(current_roi)
            
            results[bed_id] = is_occupied
        
        return results
    
    def _compare_regions(self, reference: 'np.ndarray', current: 'np.ndarray') -> bool:
        """
        Compare current region with empty reference.
        
        Args:
            reference: Empty bed reference image
            current: Current bed region image
            
        Returns:
            True if significantly different (likely occupied)
        """
        if not CV2_AVAILABLE:
            return False
        
        if reference.shape != current.shape:
            current = cv2.resize(current, (reference.shape[1], reference.shape[0]))
        
        # Convert to grayscale for comparison
        ref_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
        cur_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        ref_blur = cv2.GaussianBlur(ref_gray, (5, 5), 0)
        cur_blur = cv2.GaussianBlur(cur_gray, (5, 5), 0)
        
        # Calculate absolute difference
        diff = cv2.absdiff(ref_blur, cur_blur)
        
        # Apply threshold to get binary difference
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Calculate percentage of changed pixels
        changed_pixels = np.sum(thresh > 0)
        total_pixels = thresh.size
        change_ratio = changed_pixels / total_pixels
        
        return change_ratio > self.occupancy_threshold
    
    def _analyze_intensity(self, roi: 'np.ndarray') -> bool:
        """
        Fallback method: analyze pixel intensity patterns.
        Occupied beds typically have more variation.
        
        Args:
            roi: Region of interest to analyze
            
        Returns:
            True if likely occupied based on intensity analysis
        """
        if not CV2_AVAILABLE:
            return False
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        std_dev = np.std(gray)
        mean_val = np.mean(gray)
        
        # Higher standard deviation suggests presence of a person
        # Also check for skin-tone color presence
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Skin color range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_ratio = np.sum(skin_mask > 0) / skin_mask.size
        
        # Combine criteria
        return std_dev > 40 or skin_ratio > 0.05
    
    def detect_movement(self, prev_frame: 'np.ndarray', curr_frame: 'np.ndarray') -> Dict[str, float]:
        """
        Detect movement in each bed region.
        
        Args:
            prev_frame: Previous camera frame
            curr_frame: Current camera frame
            
        Returns:
            Dict mapping bed_id to movement intensity (0-1)
        """
        if not CV2_AVAILABLE:
            return {bed_id: 0.0 for bed_id in self.bed_rois}
        
        movement = {}
        
        for bed_id, roi in self.bed_rois.items():
            x, y, w, h = roi
            
            prev_roi = prev_frame[y:y+h, x:x+w]
            curr_roi = curr_frame[y:y+h, x:x+w]
            
            # Convert to grayscale
            prev_gray = cv2.cvtColor(prev_roi, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(curr_roi, cv2.COLOR_BGR2GRAY)
            
            # Calculate frame difference
            diff = cv2.absdiff(prev_gray, curr_gray)
            
            # Calculate movement intensity
            movement_intensity = np.mean(diff) / 255.0
            movement[bed_id] = min(1.0, movement_intensity * 3)  # Scale up for visibility
        
        return movement
    
    def get_occupancy_changes(self, current_occupancy: Dict[str, bool]) -> List[Dict]:
        """
        Detect changes in occupancy since last check.
        
        Args:
            current_occupancy: Current occupancy state
            
        Returns:
            List of change events
        """
        changes = []
        
        for bed_id, is_occupied in current_occupancy.items():
            if bed_id in self._last_states:
                was_occupied = self._last_states[bed_id]
                if is_occupied != was_occupied:
                    changes.append({
                        "bed_id": bed_id,
                        "event": "OCCUPIED" if is_occupied else "VACANT",
                        "previous": was_occupied,
                        "current": is_occupied
                    })
            
            self._last_states[bed_id] = is_occupied
        
        return changes
    
    def process_video_feed(self, video_source = 0, callback = None) -> None:
        """
        Process live video feed (for demo).
        
        Args:
            video_source: 0 for webcam, or path to video file
            callback: Optional function to call with each frame's occupancy
        """
        if not CV2_AVAILABLE:
            print("OpenCV not available. Using simulation mode.")
            return
        
        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            print(f"Failed to open video source: {video_source}")
            return
        
        print("Starting video processing. Press 'q' to quit, 'c' to calibrate.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect occupancy
            occupancy = self.detect_occupancy(frame)
            
            # Check for changes
            changes = self.get_occupancy_changes(occupancy)
            for change in changes:
                print(f"[EVENT] {change['bed_id']}: {change['event']}")
            
            # Callback if provided
            if callback:
                callback(occupancy, changes)
            
            # Draw ROIs and status
            annotated = self._annotate_frame(frame, occupancy)
            
            cv2.imshow("VitalFlow Bed Detection", annotated)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Calibrate empty beds
                self.calibrate_empty_beds(frame)
                print("✓ Calibration complete")
        
        cap.release()
        cv2.destroyAllWindows()
    
    def _annotate_frame(self, frame: 'np.ndarray', occupancy: Dict[str, bool]) -> 'np.ndarray':
        """
        Draw bounding boxes and labels on frame.
        
        Args:
            frame: Original frame
            occupancy: Occupancy status dict
            
        Returns:
            Annotated frame
        """
        if not CV2_AVAILABLE:
            return frame
        
        annotated = frame.copy()
        
        for bed_id, roi in self.bed_rois.items():
            x, y, w, h = roi
            is_occupied = occupancy.get(bed_id, False)
            
            # Color: Red if occupied, Green if empty
            color = (0, 0, 255) if is_occupied else (0, 255, 0)
            label = f"{bed_id}: {'OCCUPIED' if is_occupied else 'EMPTY'}"
            
            cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
            
            # Background for text
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, (x, y-25), (x + text_w + 4, y), color, -1)
            cv2.putText(annotated, label, (x+2, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Title
        cv2.putText(annotated, "VitalFlow AI - Bed Detection", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        return annotated
    
    # ============== SIMULATION MODE ==============
    
    def simulate_occupancy(self, num_beds: int = 6, occupancy_rate: float = 0.7) -> Dict[str, bool]:
        """
        Generate simulated occupancy data for demo.
        
        Args:
            num_beds: Number of beds to simulate
            occupancy_rate: Probability of bed being occupied
            
        Returns:
            Dict mapping bed_id to occupancy status
        """
        results = {}
        for i in range(1, num_beds + 1):
            bed_id = f"BED-{i}"
            results[bed_id] = random.random() < occupancy_rate
        
        return results
    
    def simulate_with_dynamics(self, current_state: Dict[str, bool] = None, 
                               change_probability: float = 0.05) -> Dict[str, bool]:
        """
        Simulate occupancy with realistic state changes.
        
        Args:
            current_state: Current occupancy state (or None to initialize)
            change_probability: Probability of any bed changing state
            
        Returns:
            Updated occupancy state
        """
        if current_state is None:
            return self.simulate_occupancy()
        
        new_state = current_state.copy()
        
        for bed_id in new_state:
            if random.random() < change_probability:
                new_state[bed_id] = not new_state[bed_id]
        
        return new_state
    
    def create_demo_visualization(self, occupancy: Dict[str, bool], 
                                  title: str = "WARD A - LIVE VIEW") -> 'np.ndarray':
        """
        Create a simple visualization for demo without real camera.
        
        Args:
            occupancy: Dict mapping bed_id to occupancy status
            title: Title for the visualization
            
        Returns:
            NumPy array image of the ward visualization
        """
        if not CV2_AVAILABLE:
            print("OpenCV not available for visualization")
            return None
        
        # Create blank "ward" image
        img = np.ones((500, 800, 3), dtype=np.uint8) * 240  # Light gray background
        
        # Draw beds as rectangles
        bed_positions = [
            (50, 80), (300, 80), (550, 80),
            (50, 300), (300, 300), (550, 300)
        ]
        
        for i, (x, y) in enumerate(bed_positions):
            bed_id = f"BED-{i+1}"
            is_occupied = occupancy.get(bed_id, False)
            
            # Bed frame (dark gray)
            cv2.rectangle(img, (x, y), (x+200, y+150), (80, 80, 80), 3)
            
            # Fill color based on occupancy
            fill_color = (180, 180, 255) if is_occupied else (180, 255, 180)  # Light red/green
            cv2.rectangle(img, (x+5, y+5), (x+195, y+145), fill_color, -1)
            
            # Bed label
            cv2.putText(img, bed_id, (x+65, y+50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # Status label
            status = "OCCUPIED" if is_occupied else "EMPTY"
            status_color = (0, 0, 200) if is_occupied else (0, 150, 0)
            cv2.putText(img, status, (x+55, y+90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            
            # Person icon if occupied
            if is_occupied:
                # Head
                cv2.circle(img, (x+100, y+30), 12, (50, 50, 50), -1)
                # Body
                cv2.rectangle(img, (x+85, y+45), (x+115, y+120), (50, 50, 50), -1)
                # Blanket
                cv2.rectangle(img, (x+70, y+80), (x+130, y+130), (100, 100, 200), -1)
        
        # Title
        cv2.rectangle(img, (0, 0), (800, 50), (60, 60, 60), -1)
        cv2.putText(img, title, (250, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Stats
        total = len(occupancy)
        occupied = sum(1 for v in occupancy.values() if v)
        available = total - occupied
        
        stats_text = f"Occupied: {occupied} | Available: {available} | Total: {total}"
        cv2.putText(img, stats_text, (230, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return img
    
    def run_demo(self, duration_frames: int = 100, delay_ms: int = 500):
        """
        Run a demo visualization with simulated occupancy changes.
        
        Args:
            duration_frames: Number of frames to display
            delay_ms: Delay between frames in milliseconds
        """
        if not CV2_AVAILABLE:
            print("OpenCV not available. Running text-only simulation...")
            state = self.simulate_occupancy()
            for i in range(10):
                state = self.simulate_with_dynamics(state, 0.2)
                print(f"\n--- Frame {i+1} ---")
                for bed_id, is_occupied in state.items():
                    status = "🔴 OCCUPIED" if is_occupied else "🟢 EMPTY"
                    print(f"  {bed_id}: {status}")
            return
        
        print("Running VitalFlow Bed Detection Demo...")
        print("Press 'q' to quit")
        
        state = self.simulate_occupancy()
        
        for frame_num in range(duration_frames):
            # Simulate state changes
            state = self.simulate_with_dynamics(state, 0.05)
            
            # Check for changes
            changes = self.get_occupancy_changes(state)
            for change in changes:
                print(f"[Frame {frame_num}] {change['bed_id']}: {change['event']}")
            
            # Create visualization
            img = self.create_demo_visualization(state)
            
            if img is not None:
                cv2.imshow("VitalFlow Bed Detection Demo", img)
                
                if cv2.waitKey(delay_ms) & 0xFF == ord('q'):
                    break
        
        cv2.destroyAllWindows()
        print("Demo complete.")


# Singleton instance
bed_detector = BedDetector()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing BedDetector...")
    print(f"OpenCV available: {CV2_AVAILABLE}")
    
    # Test 1: Configure beds
    detector = BedDetector()
    print(f"✓ Default beds configured: {list(detector.bed_rois.keys())}")
    
    # Test 2: Simulate occupancy
    occupancy = detector.simulate_occupancy(6, 0.5)
    print(f"✓ Simulated occupancy: {occupancy}")
    
    occupied_count = sum(1 for v in occupancy.values() if v)
    print(f"  Occupied: {occupied_count}/6")
    
    # Test 3: Dynamic simulation
    print("\n--- Dynamic Simulation ---")
    state = detector.simulate_occupancy()
    for i in range(5):
        state = detector.simulate_with_dynamics(state, 0.3)
        changes = detector.get_occupancy_changes(state)
        if changes:
            for c in changes:
                print(f"  Frame {i+1}: {c['bed_id']} → {c['event']}")
    print("✓ Dynamic simulation works")
    
    # Test 4: Visualization (if OpenCV available)
    if CV2_AVAILABLE:
        print("\n--- Visualization Test ---")
        img = detector.create_demo_visualization(occupancy, "TEST WARD")
        if img is not None:
            print(f"✓ Visualization created: {img.shape}")
            # Optionally display
            # cv2.imshow("Test", img)
            # cv2.waitKey(2000)
            # cv2.destroyAllWindows()
    else:
        print("⚠ Skipping visualization test (OpenCV not available)")
    
    # Test 5: Custom bed configuration
    custom_config = {
        "ICU-1": (0, 0, 100, 100),
        "ICU-2": (150, 0, 100, 100),
    }
    detector.configure_beds(custom_config)
    assert "ICU-1" in detector.bed_rois
    print("✓ Custom bed configuration works")
    
    print("\n✅ All BedDetector tests passed!")
    
    # Uncomment to run interactive demo
    # detector.run_demo(duration_frames=50, delay_ms=500)
