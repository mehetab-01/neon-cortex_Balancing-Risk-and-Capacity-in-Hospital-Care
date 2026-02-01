"""
AI Services module initialization.
Exports all AI services for easy importing.
"""
from .prompts import (
    MEDICINE_RECOMMENDATION_PROMPT,
    VOICE_ALERT_TEMPLATES,
    TRIAGE_DECISION_PROMPT,
    format_prompt,
    get_voice_alert
)

from .medicine_ai import medicine_ai, MedicineAI
from .voice_alerts import voice_service, VoiceAlertService
from .cv_detector import bed_detector, BedDetector

__all__ = [
    # Prompts
    "MEDICINE_RECOMMENDATION_PROMPT",
    "VOICE_ALERT_TEMPLATES",
    "TRIAGE_DECISION_PROMPT",
    "format_prompt",
    "get_voice_alert",
    
    # Services
    "medicine_ai",
    "MedicineAI",
    "voice_service",
    "VoiceAlertService",
    "bed_detector",
    "BedDetector"
]
