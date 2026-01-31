"""
VitalFlow AI - Constants and Configuration
"""

# Color Codes for Patient Status
STATUS_COLORS = {
    "Critical": "#FF4B4B",      # Red
    "Serious": "#FFA500",       # Orange
    "Stable": "#00CC66",        # Green
    "Recovering": "#4DA6FF",    # Blue
    "Empty": "#FFFFFF",         # White
}

# Emoji indicators
STATUS_EMOJI = {
    "Critical": "🔴",
    "Serious": "🟠",
    "Stable": "🟢",
    "Recovering": "🔵",
    "Empty": "⬜",
}

# Floor Configuration
FLOOR_CONFIG = {
    1: {"name": "Emergency Department", "bed_type": "Emergency", "beds": 20},
    2: {"name": "ICU Complex", "bed_type": "ICU", "beds": 15},
    3: {"name": "General Ward A", "bed_type": "General", "beds": 30},
    4: {"name": "General Ward B", "bed_type": "General", "beds": 30},
    5: {"name": "General Ward C", "bed_type": "General", "beds": 25},
}

# Vital Signs Thresholds
VITAL_THRESHOLDS = {
    "spo2": {
        "critical": 90,
        "serious": 94,
        "stable": 97,
    },
    "heart_rate": {
        "low_critical": 40,
        "low_serious": 50,
        "high_serious": 100,
        "high_critical": 120,
    },
}

# Refresh Interval (seconds)
AUTO_REFRESH_INTERVAL = 5

# Map Center (Mumbai, India)
MAP_CENTER = [19.0760, 72.8777]
MAP_ZOOM = 12

# Hospitals in Network
NETWORK_HOSPITALS = [
    {
        "id": "H001",
        "name": "VitalFlow Central Hospital",
        "lat": 19.0760,
        "lon": 72.8777,
        "address": "Marine Drive, Mumbai"
    },
    {
        "id": "H002", 
        "name": "VitalFlow North Wing",
        "lat": 19.1136,
        "lon": 72.8697,
        "address": "Bandra West, Mumbai"
    },
    {
        "id": "H003",
        "name": "VitalFlow South Medical",
        "lat": 19.0176,
        "lon": 72.8562,
        "address": "Colaba, Mumbai"
    },
    {
        "id": "H004",
        "name": "VitalFlow East Care",
        "lat": 19.0596,
        "lon": 72.9295,
        "address": "Chembur, Mumbai"
    },
]
