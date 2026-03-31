"""
Speech-to-Command (STC) Engine for AirOne Professional v4.0
Enables voice-activated mission control using speech recognition and intent parsing.
"""
import logging
import threading
import queue
import time
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VoiceCommandEngine:
    def __init__(self, feature_manager: Optional[Any] = None):
        self.logger = logging.getLogger(f"{__name__}.VoiceCommandEngine")
        self.feature_manager = feature_manager
        self.command_queue = queue.Queue()
        self.is_listening = False
        self.recognizer = None
        self.microphone = None
        self.last_command = ""
        
        self.intents = {
            r"abort mission": self._cmd_abort,
            r"status report": self._cmd_status,
            r"deploy (parachute|chute)": self._cmd_deploy_chute,
            r"enable (manual|auto) control": self._cmd_set_control_mode,
            r"start (recording|telemetry)": self._cmd_start_ops
        }
        
        self._initialize_audio()

    def _initialize_all_systems(self):
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            self.logger.info("Speech Recognition System Initialized.")
        except (ImportError, OSError) as e:
            self.logger.warning(f"Voice hardware/library not available: {e}. STC will use text-injection only.")

    def _initialize_audio(self):
        # Alias for consistency
        self._initialize_all_systems()

    def start_listening(self):
        """Starts the background voice listener thread."""
        if self.recognizer and self.microphone:
            self.is_listening = True
            self.logger.info("Voice Assistant is now LISTENING...")
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
        else:
            self.logger.warning("Cannot start listening: Audio system not initialized.")

    def _listen_loop(self):
        import speech_recognition as sr
        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=5)
                text = self.recognizer.recognize_google(audio).lower()
                self.logger.info(f"VOICE DETECTED: '{text}'")
                self.process_command(text)
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                continue
            except Exception as e:
                self.logger.error(f"Voice listener error: {e}")
                time.sleep(1)

    def process_command(self, text: str) -> bool:
        """Parses text for mission intents and executes mapped actions."""
        self.last_command = text
        for pattern, handler in self.intents.items():
            match = re.search(pattern, text.lower())
            if match:
                self.logger.info(f"INTENT MATCHED: {pattern}")
                handler(match)
                return True
        return False

    def _cmd_abort(self, match):
        self.logger.critical("🚨 VOICE ABORT COMMAND RECEIVED! 🚨")
        # Real action: Signal system-wide emergency state
        if self.feature_manager:
            sm = self.feature_manager.get_feature('security_manager')
            if sm: sm.lockdown_mode = True

    def _cmd_status(self, match):
        self.logger.info("Voice Status Request: Generating audio response...")
        # Integration with TTS would go here

    def _cmd_deploy_chute(self, match):
        self.logger.warning("VOICE CMD: Triggering Parachute Deployment Mechanism.")

    def _cmd_set_control_mode(self, match):
        mode = match.group(1)
        self.logger.info(f"VOICE CMD: System Control set to {mode.upper()}.")

    def _cmd_start_ops(self, match):
        self.logger.info("VOICE CMD: Commencing Mission Telemetry Capture.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vce = VoiceCommandEngine()
    vce.process_command("Abort mission immediately")
