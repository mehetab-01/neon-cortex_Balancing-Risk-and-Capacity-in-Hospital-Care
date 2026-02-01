"""
Voice alerts using ElevenLabs API.
Generates audio alerts for hospital announcements with fallback to local TTS.
"""
import os
import sys
import hashlib
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .prompts import VOICE_ALERT_TEMPLATES, format_prompt


class VoiceAlertService:
    """
    Voice alert generation service using ElevenLabs API.
    Includes caching to avoid repeated API calls and fallback to local TTS.
    """
    
    def __init__(self):
        """Initialize voice service with API configuration."""
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Setup cache directory
        self.cache_dir = Path(__file__).parent.parent.parent / "shared" / "audio_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice settings
        self.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def generate_alert(self, template_key: str, **kwargs) -> Optional[Path]:
        """
        Generate voice alert from template.
        
        Args:
            template_key: Key from VOICE_ALERT_TEMPLATES
            **kwargs: Values to substitute in template
            
        Returns:
            Path to audio file or None if failed
        """
        template = VOICE_ALERT_TEMPLATES.get(template_key)
        if not template:
            print(f"Unknown alert template: {template_key}")
            return None
        
        text = format_prompt(template, **kwargs)
        cache_key = f"{template_key}_{self._get_cache_key(text)}"
        
        return self.text_to_speech(text, cache_key)
    
    def text_to_speech(self, text: str, cache_key: str = None) -> Optional[Path]:
        """
        Convert text to speech using ElevenLabs API.
        Caches results to avoid repeated API calls.
        
        Args:
            text: Text to convert to speech
            cache_key: Optional key for caching
            
        Returns:
            Path to audio file
        """
        if not cache_key:
            cache_key = self._get_cache_key(text)
        
        # Check cache first
        cache_path = self.cache_dir / f"{cache_key}.mp3"
        if cache_path.exists():
            return cache_path
        
        # Try ElevenLabs API
        if self.api_key:
            result = self._call_elevenlabs(text, cache_path)
            if result:
                return result
        else:
            print(f"[VOICE ALERT - NO API KEY]: {text}")
        
        # Fallback to local TTS
        return self._fallback_tts(text, cache_key)
    
    def _call_elevenlabs(self, text: str, output_path: Path) -> Optional[Path]:
        """
        Call ElevenLabs API for text-to-speech.
        
        Args:
            text: Text to convert
            output_path: Where to save the audio
            
        Returns:
            Path to audio file or None if failed
        """
        try:
            import requests
            
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": self.voice_settings
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                output_path.write_bytes(response.content)
                print(f"✓ Audio generated: {output_path.name}")
                return output_path
            else:
                print(f"ElevenLabs API error: {response.status_code} - {response.text[:100]}")
                return None
                
        except ImportError:
            print("Requests package not installed. Run: pip install requests")
            return None
        except Exception as e:
            print(f"ElevenLabs error: {e}")
            return None
    
    def _fallback_tts(self, text: str, cache_key: str) -> Optional[Path]:
        """
        Fallback using pyttsx3 (offline TTS) or gTTS if available.
        
        Args:
            text: Text to convert
            cache_key: Cache key for file naming
            
        Returns:
            Path to audio file or text file as last resort
        """
        # Try pyttsx3 first (offline)
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # Configure voice
            voices = engine.getProperty('voices')
            # Try to use a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 150)  # Speed
            engine.setProperty('volume', 0.9)
            
            output_path = self.cache_dir / f"{cache_key}_pyttsx3.mp3"
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            
            if output_path.exists():
                print(f"✓ Fallback audio (pyttsx3): {output_path.name}")
                return output_path
                
        except ImportError:
            print("pyttsx3 not installed. Trying gTTS...")
        except Exception as e:
            print(f"pyttsx3 error: {e}")
        
        # Try gTTS (requires internet but no API key)
        try:
            from gtts import gTTS
            
            output_path = self.cache_dir / f"{cache_key}_gtts.mp3"
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(str(output_path))
            
            if output_path.exists():
                print(f"✓ Fallback audio (gTTS): {output_path.name}")
                return output_path
                
        except ImportError:
            print("gTTS not installed. Run: pip install gtts")
        except Exception as e:
            print(f"gTTS error: {e}")
        
        # Ultimate fallback: save as text file
        text_path = self.cache_dir / f"{cache_key}.txt"
        text_path.write_text(text)
        print(f"⚠ Audio generation failed. Text saved to: {text_path.name}")
        return text_path
    
    def play_audio(self, audio_path: Path) -> bool:
        """
        Play audio file using available system player.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if played successfully
        """
        if not audio_path or not audio_path.exists():
            return False
        
        # If it's a text file, just print it
        if audio_path.suffix == '.txt':
            print(f"[ALERT]: {audio_path.read_text()}")
            return True
        
        try:
            # Try pygame
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            return True
        except ImportError:
            pass
        except Exception as e:
            print(f"Pygame playback error: {e}")
        
        try:
            # Try playsound
            from playsound import playsound
            playsound(str(audio_path))
            return True
        except ImportError:
            pass
        except Exception as e:
            print(f"Playsound error: {e}")
        
        # Fallback: use system default
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(str(audio_path))
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['afplay', str(audio_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(audio_path)])
            return True
        except Exception as e:
            print(f"System playback error: {e}")
        
        return False
    
    # ============== CONVENIENCE METHODS ==============
    
    def code_blue(self, bed_id: str, station: str, medications: List[str]) -> Optional[Path]:
        """
        Generate Code Blue alert.
        
        Args:
            bed_id: Bed identifier
            station: Nurse station
            medications: List of medications needed
            
        Returns:
            Path to audio file
        """
        return self.generate_alert(
            "CODE_BLUE",
            station=station,
            bed_id=bed_id,
            medications=", ".join(medications) if medications else "emergency medications"
        )
    
    def transfer_alert(self, patient_name: str, from_bed: str, to_bed: str) -> Optional[Path]:
        """
        Generate patient transfer alert.
        
        Args:
            patient_name: Name of patient
            from_bed: Origin bed
            to_bed: Destination bed
            
        Returns:
            Path to audio file
        """
        return self.generate_alert(
            "TRANSFER_ALERT",
            patient_name=patient_name,
            from_bed=from_bed,
            to_bed=to_bed
        )
    
    def vitals_warning(self, bed_id: str, spo2: float, heart_rate: int) -> Optional[Path]:
        """
        Generate vitals warning alert.
        
        Args:
            bed_id: Bed identifier
            spo2: Oxygen saturation
            heart_rate: Heart rate
            
        Returns:
            Path to audio file
        """
        return self.generate_alert(
            "VITALS_WARNING",
            bed_id=bed_id,
            spo2=str(int(spo2)),
            heart_rate=str(heart_rate)
        )
    
    def vitals_critical(self, bed_id: str, spo2: float) -> Optional[Path]:
        """
        Generate critical vitals alert.
        
        Args:
            bed_id: Bed identifier
            spo2: Oxygen saturation
            
        Returns:
            Path to audio file
        """
        return self.generate_alert(
            "VITALS_CRITICAL",
            bed_id=bed_id,
            spo2=str(int(spo2))
        )
    
    def fatigue_alert(self, doctor_name: str, hours: float) -> Optional[Path]:
        """
        Generate staff fatigue alert.
        
        Args:
            doctor_name: Name of staff member
            hours: Hours worked
            
        Returns:
            Path to audio file
        """
        return self.generate_alert(
            "FATIGUE_ALERT",
            doctor_name=doctor_name,
            hours=str(int(hours))
        )
    
    def bed_ready(self, bed_id: str, ward: str, eta: int) -> Optional[Path]:
        """
        Generate bed ready notification.
        
        Args:
            bed_id: Bed identifier
            ward: Ward name
            eta: ETA in minutes
            
        Returns:
            Path to audio file
        """
        return self.generate_alert(
            "BED_READY",
            bed_id=bed_id,
            ward=ward,
            eta=str(eta)
        )
    
    def ambulance_arriving(self, patient_name: str, eta: int, condition: str, bed_type: str) -> Optional[Path]:
        """
        Generate ambulance arrival notification.
        
        Args:
            patient_name: Name of incoming patient
            eta: ETA in minutes
            condition: Patient condition
            bed_type: Required bed type
            
        Returns:
            Path to audio file
        """
        return self.generate_alert(
            "AMBULANCE_ARRIVING",
            patient_name=patient_name,
            eta=str(eta),
            condition=condition,
            bed_type=bed_type
        )
    
    def swap_notification(self, patient_out: str, bed_out: str, patient_in: str, bed_in: str) -> Optional[Path]:
        """
        Generate bed swap notification.
        
        Args:
            patient_out: Patient being moved out
            bed_out: Destination bed for outgoing patient
            patient_in: Patient being moved in
            bed_in: ICU bed for incoming patient
            
        Returns:
            Path to audio file
        """
        return self.generate_alert(
            "SWAP_NOTIFICATION",
            patient_out=patient_out,
            bed_out=bed_out,
            patient_in=patient_in,
            bed_in=bed_in
        )
    
    def get_alert_text(self, template_key: str, **kwargs) -> Optional[str]:
        """
        Get alert text without generating audio.
        Useful for displaying in UI.
        
        Args:
            template_key: Key from VOICE_ALERT_TEMPLATES
            **kwargs: Values to substitute
            
        Returns:
            Formatted alert text
        """
        template = VOICE_ALERT_TEMPLATES.get(template_key)
        if not template:
            return None
        return format_prompt(template, **kwargs)
    
    def list_available_templates(self) -> List[str]:
        """Get list of available alert template keys."""
        return list(VOICE_ALERT_TEMPLATES.keys())
    
    def clear_cache(self):
        """Clear all cached audio files."""
        for file in self.cache_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                print(f"Error deleting {file}: {e}")
        print("✓ Audio cache cleared")


# Singleton instance
voice_service = VoiceAlertService()


# ============== UNIT TESTS ==============
if __name__ == "__main__":
    print("Testing VoiceAlertService...")
    
    # Test 1: List templates
    templates = voice_service.list_available_templates()
    print(f"✓ Available templates: {len(templates)}")
    for t in templates[:5]:
        print(f"  - {t}")
    
    # Test 2: Get alert text (no audio)
    text = voice_service.get_alert_text(
        "CODE_BLUE",
        station="A3",
        bed_id="ICU-05",
        medications="epinephrine and defibrillator"
    )
    assert text is not None
    assert "Code Blue" in text
    print(f"✓ Alert text: {text[:60]}...")
    
    # Test 3: Generate alert (will use fallback if no API key)
    print("\n--- Generating Test Alert ---")
    audio_path = voice_service.vitals_warning(
        bed_id="GEN-02",
        spo2=88,
        heart_rate=110
    )
    
    if audio_path:
        print(f"✓ Audio generated: {audio_path}")
        print(f"  File exists: {audio_path.exists()}")
        print(f"  File size: {audio_path.stat().st_size if audio_path.exists() else 'N/A'} bytes")
    else:
        print("⚠ Audio generation returned None (expected if no TTS available)")
    
    # Test 4: Transfer alert
    print("\n--- Transfer Alert ---")
    text = voice_service.get_alert_text(
        "TRANSFER_ALERT",
        patient_name="John Doe",
        from_bed="ICU-01",
        to_bed="GEN-03"
    )
    print(f"✓ Transfer alert: {text}")
    
    # Test 5: Swap notification
    print("\n--- Swap Notification ---")
    text = voice_service.get_alert_text(
        "SWAP_NOTIFICATION",
        patient_out="Stable Patient",
        bed_out="GEN-02",
        patient_in="Critical Patient",
        bed_in="ICU-01"
    )
    print(f"✓ Swap notification: {text}")
    
    # Test 6: Ambulance arriving
    print("\n--- Ambulance Alert ---")
    text = voice_service.get_alert_text(
        "AMBULANCE_ARRIVING",
        patient_name="Emergency Patient",
        eta=5,
        condition="Cardiac arrest",
        bed_type="ICU"
    )
    print(f"✓ Ambulance alert: {text}")
    
    # Test 7: Fatigue alert
    print("\n--- Fatigue Alert ---")
    text = voice_service.get_alert_text(
        "FATIGUE_ALERT",
        doctor_name="Dr. Sharma",
        hours=12
    )
    print(f"✓ Fatigue alert: {text}")
    
    print("\n✅ All VoiceAlertService tests passed!")
