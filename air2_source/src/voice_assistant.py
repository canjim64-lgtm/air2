"""
AirOne Professional v4.0 - Voice Assistant
Text-to-speech and voice command support
"""
# -*- coding: utf-8 -*-

import logging
from typing import Optional, Callable, List, Dict, Any
import threading
import time

logger = logging.getLogger(__name__)


class VoiceAssistant:
    """Voice assistant for AirOne"""
    
    def __init__(self):
        self.engine = None
        self.available = False
        self.voice_commands: Dict[str, Callable] = {}
        self.listening = False
        
        # Try to initialize TTS
        self._init_tts()
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            # Try pyttsx3 first
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Configure voice
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
            
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 0.9)
            
            self.available = True
            logger.info("Voice assistant initialized")
        except ImportError:
            logger.warning("pyttsx3 not available - voice features disabled")
            self.available = False
        except Exception as e:
            logger.error(f"Failed to initialize voice assistant: {e}")
            self.available = False
    
    def speak(self, text: str, async_mode: bool = False):
        """Speak text"""
        if not self.available:
            # Fallback: print to console
            print(f"[VOICE] {text}")
            return
        
        if async_mode:
            thread = threading.Thread(target=self._speak_impl, args=(text,))
            thread.daemon = True
            thread.start()
        else:
            self._speak_impl(text)
    
    def _speak_impl(self, text: str):
        """Internal speak implementation"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Speech failed: {e}")
    
    def register_command(self, command: str, callback: Callable):
        """Register voice command"""
        self.voice_commands[command.lower()] = callback
        logger.info(f"Registered voice command: {command}")
    
    def process_command(self, command: str) -> bool:
        """Process voice command"""
        command = command.lower().strip()
        
        if command in self.voice_commands:
            try:
                self.voice_commands[command]()
                return True
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                return False
        
        return False
    
    def start_listening(self):
        """Start listening for voice commands"""
        self.listening = True
        logger.info("Voice assistant listening...")
    
    def stop_listening(self):
        """Stop listening"""
        self.listening = False
        logger.info("Voice assistant stopped")


class AnnouncementSystem:
    """System announcements"""
    
    def __init__(self, voice_assistant: Optional[VoiceAssistant] = None):
        self.voice = voice_assistant or VoiceAssistant()
        self.announcement_queue: List[str] = []
        self.announcing = False
    
    def announce(self, message: str, priority: str = "normal"):
        """Make an announcement"""
        if priority == "critical":
            # Critical announcements are immediate
            self.voice.speak(f"Critical Alert: {message}", async_mode=True)
        else:
            self.announcement_queue.append(message)
            if not self.announcing:
                self._process_queue()
    
    def _process_queue(self):
        """Process announcement queue"""
        self.announcing = True
        
        while self.announcement_queue:
            message = self.announcement_queue.pop(0)
            self.voice.speak(message)
            time.sleep(0.5)
        
        self.announcing = False
    
    def announce_telemetry(self, telemetry: Dict[str, Any]):
        """Announce telemetry data"""
        altitude = telemetry.get('altitude', 0)
        velocity = telemetry.get('velocity', 0)
        
        self.announce(f"Altitude {altitude:.0f} meters, velocity {velocity:.0f} meters per second")


class EventNarrator:
    """Narrate system events"""
    
    def __init__(self, voice_assistant: Optional[VoiceAssistant] = None):
        self.voice = voice_assistant or VoiceAssistant()
        self.event_templates = {
            'startup': "AirOne Professional version 4.0 starting up",
            'shutdown': "AirOne Professional shutting down",
            'connected': "Telemetry link established",
            'disconnected': "Telemetry link lost",
            'warning': "Warning: {message}",
            'error': "Error: {message}",
            'success': "Operation completed successfully",
            'milestone': "Milestone achieved: {message}"
        }
    
    def narrate(self, event_type: str, **kwargs):
        """Narrate an event"""
        template = self.event_templates.get(event_type, "{message}")
        message = template.format(**kwargs)
        self.voice.speak(message, async_mode=True)
    
    def narrate_startup(self):
        """Narrate system startup"""
        self.narrate('startup')
    
    def narrate_shutdown(self):
        """Narrate system shutdown"""
        self.narrate('shutdown')
    
    def narrate_warning(self, message: str):
        """Narrate warning"""
        self.narrate('warning', message=message)
    
    def narrate_error(self, message: str):
        """Narrate error"""
        self.narrate('error', message=message)


# Global voice assistant instance
_voice_assistant: Optional[VoiceAssistant] = None


def get_voice_assistant() -> VoiceAssistant:
    """Get global voice assistant"""
    global _voice_assistant
    if _voice_assistant is None:
        _voice_assistant = VoiceAssistant()
    return _voice_assistant


def speak(text: str):
    """Quick speak function"""
    get_voice_assistant().speak(text)


def announce(message: str):
    """Quick announce function"""
    get_voice_assistant().speak(message, async_mode=True)


if __name__ == "__main__":
    # Test voice assistant
    print("="*70)
    print("  AirOne Professional v4.0 - Voice Assistant Test")
    print("="*70)
    print()
    
    assistant = VoiceAssistant()
    
    if assistant.available:
        print("Voice assistant is available!")
        print()
        
        # Test speech
        print("Testing speech synthesis...")
        assistant.speak("Welcome to AirOne Professional version 4.0")
        time.sleep(2)
        
        assistant.speak("All systems operational")
        time.sleep(1)
        
        # Test announcements
        print("\nTesting announcements...")
        announcer = AnnouncementSystem(assistant)
        announcer.announce("System initialization complete")
        time.sleep(1)
        
        announcer.announce("Battery level at 95 percent", priority="normal")
        time.sleep(1)
        
        announcer.announce("High temperature detected", priority="critical")
        time.sleep(2)
        
        # Test event narrator
        print("\nTesting event narrator...")
        narrator = EventNarrator(assistant)
        narrator.narrate_startup()
        time.sleep(1)
        
        narrator.narrate_warning("Low signal strength")
        time.sleep(1)
        
        narrator.narrate('milestone', message="Altitude milestone reached")
        time.sleep(1)
        
        print("\nVoice assistant test complete!")
    else:
        print("Voice assistant not available.")
        print("Install pyttsx3: pip install pyttsx3")
    
    print()
    print("="*70)
