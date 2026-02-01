"""
Backend package initialization.
"""
from backend.core_logic import (
    hospital_state,
    bed_manager,
    staff_manager,
    triage_engine
)

from backend.ai_services import (
    medicine_ai,
    voice_service,
    bed_detector
)

__all__ = [
    # Core Logic
    "hospital_state",
    "bed_manager", 
    "staff_manager",
    "triage_engine",
    
    # AI Services
    "medicine_ai",
    "voice_service",
    "bed_detector"
]
