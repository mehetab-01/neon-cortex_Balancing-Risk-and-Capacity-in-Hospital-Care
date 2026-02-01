"""
Constants and configuration values for VitalFlow AI.
"""
from enum import Enum


# Hospital Configuration
HOSPITAL_NAME = "VitalFlow General Hospital"
HOSPITAL_FLOORS = 5
TOTAL_BEDS = 50

# Bed Distribution
BED_DISTRIBUTION = {
    "ICU": 10,
    "Emergency": 10,
    "General": 20,
    "Pediatric": 5,
    "Maternity": 5
}

# Ward Names per Floor
WARD_NAMES = {
    1: "Emergency Ward",
    2: "General Ward A",
    3: "General Ward B",
    4: "ICU",
    5: "Specialized Care"
}


# Vital Signs Thresholds
class VitalThresholds:
    # SpO2 (Oxygen Saturation)
    SPO2_CRITICAL = 85
    SPO2_LOW = 90
    SPO2_NORMAL_MIN = 95
    SPO2_NORMAL_MAX = 100
    
    # Heart Rate
    HR_CRITICAL_LOW = 40
    HR_LOW = 50
    HR_NORMAL_MIN = 60
    HR_NORMAL_MAX = 100
    HR_HIGH = 120
    HR_CRITICAL_HIGH = 150
    
    # Temperature (Fahrenheit)
    TEMP_HYPOTHERMIA = 95.0
    TEMP_NORMAL_MIN = 97.0
    TEMP_NORMAL_MAX = 99.0
    TEMP_FEVER = 100.4
    TEMP_HIGH_FEVER = 103.0


# Staff Configuration
class StaffConfig:
    FATIGUE_THRESHOLD_HOURS = 12
    WARNING_THRESHOLD_HOURS = 10
    MAX_PATIENTS_PER_DOCTOR = 5
    MAX_PATIENTS_PER_NURSE = 8
    BREAK_DURATION_MINUTES = 30


# Triage Priority Levels
class TriagePriority(int, Enum):
    RESUSCITATION = 1  # Immediate life-threatening
    EMERGENCY = 2      # High risk of deterioration
    URGENT = 3         # Requires prompt care
    SEMI_URGENT = 4    # Serious but stable
    NON_URGENT = 5     # Minor issues


# Color codes for UI
PRIORITY_COLORS = {
    1: "#FF0000",  # Red - Critical
    2: "#FF6600",  # Orange - Serious
    3: "#FFCC00",  # Yellow - Urgent
    4: "#00CC00",  # Green - Semi-urgent
    5: "#0066FF",  # Blue - Non-urgent
}

STATUS_COLORS = {
    "Critical": "#FF0000",
    "Serious": "#FF6600",
    "Stable": "#00CC00",
    "Recovering": "#0066FF",
    "Discharged": "#999999"
}

BED_TYPE_COLORS = {
    "ICU": "#FF4444",
    "Emergency": "#FF8C00",
    "General": "#4CAF50",
    "Pediatric": "#2196F3",
    "Maternity": "#E91E63"
}


# API Configuration
class APIConfig:
    ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
    ELEVENLABS_DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"
    
    OPENAI_MODEL = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS = 500
    
    GEMINI_MODEL = "gemini-pro"


# Simulation Configuration
class SimulationConfig:
    VITALS_UPDATE_INTERVAL_SECONDS = 5
    AMBULANCE_SPEED_KMH = 40
    PATIENT_ARRIVAL_RATE_PER_HOUR = 3
    DEGRADATION_PROBABILITY = 0.1
    RECOVERY_PROBABILITY = 0.15


# File Paths
class FilePaths:
    STATE_FILE = "shared/state.json"
    AUDIO_CACHE_DIR = "shared/audio_cache"
    LOGS_DIR = "logs"


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing Constants...")
    
    # Test enums
    assert TriagePriority.RESUSCITATION == 1
    print(f"✓ TriagePriority.RESUSCITATION = {TriagePriority.RESUSCITATION}")
    
    # Test thresholds
    assert VitalThresholds.SPO2_CRITICAL == 85
    print(f"✓ Critical SpO2 threshold = {VitalThresholds.SPO2_CRITICAL}")
    
    # Test colors
    assert PRIORITY_COLORS[1] == "#FF0000"
    print(f"✓ Priority 1 color = {PRIORITY_COLORS[1]}")
    
    # Test bed distribution
    total = sum(BED_DISTRIBUTION.values())
    assert total == TOTAL_BEDS
    print(f"✓ Total beds from distribution = {total}")
    
    print("\n✅ All constant tests passed!")
