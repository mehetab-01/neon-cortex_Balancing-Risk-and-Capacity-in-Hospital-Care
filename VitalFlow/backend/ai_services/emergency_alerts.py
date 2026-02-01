"""
VitalFlow AI - Emergency Notification Service
Handles emergency alerts with ElevenLabs TTS and call notifications.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

from .voice_alerts import VoiceAlertService


class EmergencyType(str, Enum):
    """Types of emergencies."""
    CODE_BLUE = "Code Blue"          # Cardiac arrest
    CODE_RED = "Code Red"            # Fire
    CODE_ORANGE = "Code Orange"      # Hazardous spill
    CODE_PINK = "Code Pink"          # Infant/child abduction
    CODE_GREY = "Code Grey"          # Combative person
    FALL_DETECTED = "Fall Detected"  # CCTV fall detection
    CRITICAL_VITALS = "Critical Vitals"  # Patient vital signs critical
    STAFF_EMERGENCY = "Staff Emergency"  # Staff member needs help


@dataclass
class EmergencyAlert:
    """Emergency alert data structure."""
    id: str
    emergency_type: EmergencyType
    location: str
    description: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    staff_id: Optional[str] = None
    timestamp: datetime = None
    phone_to_call: Optional[str] = None
    audio_path: Optional[Path] = None
    is_acknowledged: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EmergencyNotificationService:
    """
    Emergency notification service with ElevenLabs TTS.
    Generates voice alerts and provides call-to-action with phone numbers.
    """
    
    def __init__(self):
        self.voice_service = VoiceAlertService()
        self.emergency_phone = os.getenv("EMERGENCY_PHONE", "108")
        self.hospital_phone = os.getenv("HOSPITAL_PHONE", "+91-1234567890")
        self.admin_phone = os.getenv("ADMIN_PHONE", "+91-9876543210")
        
        # Store active alerts
        self.active_alerts: Dict[str, EmergencyAlert] = {}
        self.alert_history: List[EmergencyAlert] = []
        
        # Alert templates for TTS
        self.alert_messages = {
            EmergencyType.CODE_BLUE: (
                "ATTENTION! CODE BLUE! CODE BLUE! "
                "Cardiac arrest at {location}. "
                "Patient {patient_name} requires immediate resuscitation. "
                "All available medical staff respond immediately. "
                "Call {phone} for emergency assistance."
            ),
            EmergencyType.CODE_RED: (
                "ATTENTION! CODE RED! CODE RED! "
                "Fire emergency at {location}. "
                "Evacuate the area immediately. "
                "Do not use elevators. "
                "Call {phone} for fire department."
            ),
            EmergencyType.FALL_DETECTED: (
                "ALERT! Fall detected at {location}. "
                "Patient {patient_name} may need immediate assistance. "
                "Nearest staff please respond. "
                "If patient is unresponsive, call {phone}."
            ),
            EmergencyType.CRITICAL_VITALS: (
                "WARNING! Critical vital signs detected. "
                "Patient {patient_name} at {location}. "
                "SpO2 and heart rate are at dangerous levels. "
                "Assigned doctor please respond immediately. "
                "For emergency, call {phone}."
            ),
            EmergencyType.STAFF_EMERGENCY: (
                "ATTENTION! Staff emergency at {location}. "
                "Staff member requires immediate assistance. "
                "Security and medical team respond. "
                "Call {phone} if additional help needed."
            ),
        }
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        import uuid
        return f"EMRG-{uuid.uuid4().hex[:8].upper()}"
    
    def create_emergency_alert(
        self,
        emergency_type: EmergencyType,
        location: str,
        description: str,
        patient_id: str = None,
        patient_name: str = None,
        staff_id: str = None,
        auto_play: bool = True
    ) -> EmergencyAlert:
        """
        Create and announce an emergency alert.
        
        Args:
            emergency_type: Type of emergency
            location: Location of emergency (bed ID, room, zone)
            description: Additional details
            patient_id: Optional patient ID
            patient_name: Optional patient name
            staff_id: Optional staff ID who triggered
            auto_play: Whether to play audio automatically
            
        Returns:
            EmergencyAlert object
        """
        alert_id = self._generate_alert_id()
        
        # Determine phone number based on emergency type
        if emergency_type in [EmergencyType.CODE_BLUE, EmergencyType.CODE_RED]:
            phone = self.emergency_phone
        else:
            phone = self.hospital_phone
        
        # Create alert object
        alert = EmergencyAlert(
            id=alert_id,
            emergency_type=emergency_type,
            location=location,
            description=description,
            patient_id=patient_id,
            patient_name=patient_name or "Unknown Patient",
            staff_id=staff_id,
            phone_to_call=phone,
            timestamp=datetime.now()
        )
        
        # Generate TTS audio
        message = self._format_alert_message(alert)
        audio_path = self.voice_service.text_to_speech(message, f"emergency_{alert_id}")
        alert.audio_path = audio_path
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Play audio if requested
        if auto_play and audio_path:
            self.voice_service.play_audio(audio_path)
        
        # Log the alert
        self._log_alert(alert)
        
        return alert
    
    def _format_alert_message(self, alert: EmergencyAlert) -> str:
        """Format alert message for TTS."""
        template = self.alert_messages.get(
            alert.emergency_type,
            "Emergency alert at {location}. {description}. Call {phone} for assistance."
        )
        
        return template.format(
            location=alert.location,
            patient_name=alert.patient_name or "patient",
            description=alert.description,
            phone=alert.phone_to_call
        )
    
    def _log_alert(self, alert: EmergencyAlert):
        """Log alert to hospital state."""
        try:
            from backend.core_logic.state import hospital_state
            hospital_state.log_decision(
                f"EMERGENCY_{alert.emergency_type.name}",
                f"{alert.emergency_type.value} at {alert.location}: {alert.description}",
                {
                    "alert_id": alert.id,
                    "patient_id": alert.patient_id,
                    "phone": alert.phone_to_call,
                    "timestamp": alert.timestamp.isoformat()
                }
            )
            hospital_state.save()
        except Exception as e:
            print(f"Error logging alert: {e}")
    
    def acknowledge_alert(self, alert_id: str, staff_id: str = None) -> bool:
        """
        Acknowledge an active alert.
        
        Args:
            alert_id: ID of alert to acknowledge
            staff_id: ID of staff member acknowledging
            
        Returns:
            True if acknowledged successfully
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.is_acknowledged = True
            
            # Log acknowledgment
            try:
                from backend.core_logic.state import hospital_state
                hospital_state.log_decision(
                    "ALERT_ACKNOWLEDGED",
                    f"Alert {alert_id} acknowledged by staff {staff_id or 'Unknown'}",
                    {"alert_id": alert_id, "staff_id": staff_id}
                )
            except:
                pass
            
            # Move to history
            del self.active_alerts[alert_id]
            return True
        return False
    
    def get_active_alerts(self) -> List[EmergencyAlert]:
        """Get list of active (unacknowledged) alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 20) -> List[EmergencyAlert]:
        """Get recent alert history."""
        return self.alert_history[-limit:]
    
    # ============== CONVENIENCE METHODS ==============
    
    def code_blue_alert(
        self, 
        location: str, 
        patient_name: str = None,
        patient_id: str = None
    ) -> EmergencyAlert:
        """Trigger Code Blue (cardiac arrest) alert."""
        return self.create_emergency_alert(
            EmergencyType.CODE_BLUE,
            location=location,
            description="Cardiac arrest - immediate resuscitation required",
            patient_name=patient_name,
            patient_id=patient_id
        )
    
    def fall_detected_alert(
        self,
        location: str,
        patient_name: str = None,
        patient_id: str = None,
        confidence: float = 0.0
    ) -> EmergencyAlert:
        """Trigger fall detection alert from CCTV."""
        return self.create_emergency_alert(
            EmergencyType.FALL_DETECTED,
            location=location,
            description=f"Fall detected by CCTV system (confidence: {confidence:.1f}%)",
            patient_name=patient_name,
            patient_id=patient_id
        )
    
    def critical_vitals_alert(
        self,
        location: str,
        patient_name: str,
        patient_id: str,
        vitals: Dict = None
    ) -> EmergencyAlert:
        """Trigger critical vitals alert."""
        vitals_str = ""
        if vitals:
            vitals_str = f"SpO2: {vitals.get('spo2', 'N/A')}%, HR: {vitals.get('heart_rate', 'N/A')}"
        
        return self.create_emergency_alert(
            EmergencyType.CRITICAL_VITALS,
            location=location,
            description=f"Critical vital signs - {vitals_str}",
            patient_name=patient_name,
            patient_id=patient_id
        )
    
    def custom_emergency_alert(
        self,
        message: str,
        location: str,
        phone: str = None
    ) -> EmergencyAlert:
        """
        Create custom emergency alert with specific message.
        
        Args:
            message: Custom message to announce
            location: Location of emergency
            phone: Phone number to call
            
        Returns:
            EmergencyAlert object
        """
        alert_id = self._generate_alert_id()
        
        alert = EmergencyAlert(
            id=alert_id,
            emergency_type=EmergencyType.STAFF_EMERGENCY,
            location=location,
            description=message,
            phone_to_call=phone or self.hospital_phone
        )
        
        # Generate custom TTS with phone number
        full_message = f"{message}. For immediate assistance, call {alert.phone_to_call}."
        audio_path = self.voice_service.text_to_speech(full_message, f"custom_{alert_id}")
        alert.audio_path = audio_path
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        if audio_path:
            self.voice_service.play_audio(audio_path)
        
        return alert
    
    def play_alert(self, alert_id: str) -> bool:
        """Replay an alert's audio."""
        alert = self.active_alerts.get(alert_id)
        if alert and alert.audio_path:
            return self.voice_service.play_audio(alert.audio_path)
        return False
    
    def get_emergency_phone_info(self) -> Dict[str, str]:
        """Get emergency contact information."""
        return {
            "emergency": self.emergency_phone,
            "hospital": self.hospital_phone,
            "admin": self.admin_phone
        }


# Singleton instance
emergency_service = EmergencyNotificationService()


# Convenience functions
def trigger_code_blue(location: str, patient_name: str = None) -> EmergencyAlert:
    """Quick Code Blue alert."""
    return emergency_service.code_blue_alert(location, patient_name)


def trigger_fall_alert(location: str, patient_name: str = None, confidence: float = 0.0) -> EmergencyAlert:
    """Quick fall detection alert."""
    return emergency_service.fall_detected_alert(location, patient_name, confidence=confidence)


def trigger_critical_vitals(location: str, patient_name: str, vitals: Dict) -> EmergencyAlert:
    """Quick critical vitals alert."""
    return emergency_service.critical_vitals_alert(location, patient_name, None, vitals)


def announce_emergency(message: str, location: str, phone: str = None) -> EmergencyAlert:
    """Announce custom emergency with TTS."""
    return emergency_service.custom_emergency_alert(message, location, phone)
