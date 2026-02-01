"""
Model Setup for YOLOv8-Pose
Downloads and configures pretrained YOLOv8 pose estimation model
NO TRAINING REQUIRED - Uses pretrained weights
"""
import os
from pathlib import Path
from typing import Optional, Tuple

# Model configuration
MODEL_NAME = "yolov8n-pose.pt"  # Nano model for speed
MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-pose.pt"

# Model storage path
MODELS_DIR = Path(__file__).parent / "models"


def ensure_models_dir():
    """Ensure models directory exists."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


def get_model_path() -> Path:
    """Get the path to the YOLOv8-Pose model."""
    return ensure_models_dir() / MODEL_NAME


def is_model_downloaded() -> bool:
    """Check if the model is already downloaded."""
    model_path = get_model_path()
    return model_path.exists() and model_path.stat().st_size > 1000000  # > 1MB


def download_model() -> Tuple[bool, str]:
    """
    Download the YOLOv8-Pose model.
    The ultralytics library handles this automatically.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        from ultralytics import YOLO
        
        # This will automatically download the model if not present
        model = YOLO(MODEL_NAME)
        
        return True, f"Model ready: {MODEL_NAME}"
        
    except ImportError:
        return False, "ultralytics not installed. Run: pip install ultralytics"
    except Exception as e:
        return False, f"Error downloading model: {str(e)}"


def load_pose_model() -> Optional['YOLO']:
    """
    Load the YOLOv8-Pose model for inference.
    
    Returns:
        YOLO model instance or None if failed
    """
    try:
        from ultralytics import YOLO
        
        # Load the pose estimation model
        model = YOLO(MODEL_NAME)
        
        print(f"✅ YOLOv8-Pose model loaded: {MODEL_NAME}")
        return model
        
    except ImportError:
        print("❌ ultralytics not installed")
        return None
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None


# Keypoint indices for YOLOv8-Pose (COCO format)
KEYPOINT_NAMES = {
    0: "nose",
    1: "left_eye",
    2: "right_eye",
    3: "left_ear",
    4: "right_ear",
    5: "left_shoulder",
    6: "right_shoulder",
    7: "left_elbow",
    8: "right_elbow",
    9: "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip",
    13: "left_knee",
    14: "right_knee",
    15: "left_ankle",
    16: "right_ankle"
}

# Key body parts for fall detection
UPPER_BODY_KEYPOINTS = [0, 1, 2, 3, 4, 5, 6]  # Head and shoulders
LOWER_BODY_KEYPOINTS = [11, 12, 13, 14, 15, 16]  # Hips and legs
CORE_KEYPOINTS = [5, 6, 11, 12]  # Shoulders and hips


if __name__ == "__main__":
    print("Setting up YOLOv8-Pose model...")
    
    if is_model_downloaded():
        print(f"✅ Model already present: {get_model_path()}")
    else:
        print("Downloading model...")
        success, message = download_model()
        print(message)
    
    # Test loading
    print("\nTesting model load...")
    model = load_pose_model()
    if model:
        print("✅ Model ready for inference")
    else:
        print("❌ Model loading failed")
