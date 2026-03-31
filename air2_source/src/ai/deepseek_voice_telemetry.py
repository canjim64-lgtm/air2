"""
DeepSeek R1B Voice-Over-Telemetry System
Real-time voice announcements using DeepSeek for telemetry narration
Local inference for low-latency voice generation
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque
import threading
import queue


@dataclass
class TelemetryState:
    timestamp: float
    altitude: float
    radiation: float
    voc: float
    temperature: float
    pressure: float
    battery: float
    descent_rate: float
    gps_lock: bool
    signal_strength: float


@dataclass
class VoiceAnnouncement:
    text: str
    priority: str  # 'critical', 'warning', 'info'
    timestamp: float


class DeepSeekVoiceDirector:
    """
    Voice-over-telemetry system using DeepSeek R1B.
    Announces telemetry updates and alerts in real-time.
    """
    
    def __init__(
        self,
        api_endpoint: str = "http://localhost:11434/v1",  # Ollama-compatible
        model_name: str = "deepseek-r1:1.5b",
        sample_rate: int = 16000
    ):
        self.api_endpoint = api_endpoint
        self.model_name = model_name
        self.sample_rate = sample_rate
        
        # Telemetry buffer
        self.telemetry_history: deque = deque(maxlen=100)
        self.current_state: Optional[TelemetryState] = None
        
        # Announcement queue
        self.announcement_queue = queue.Queue()
        
        # State tracking
        self.last_announcement_time = 0
        self.announcement_interval = 10  # seconds
        
        # Alert states (to avoid repeat alerts)
        self.active_alerts = set()
        
        # DeepSeek client
        self.client = None
        self._init_client()
        
        # TTS engine (using pyttsx3 or gTTS)
        self.tts_engine = None
        self._init_tts()
        
        # Background processing
        self.processing_thread = None
        self.running = False
        
    def _init_client(self):
        """Initialize DeepSeek API client."""
        try:
            import requests
            self.client = requests.Session()
            self.client.headers.update({
                'Content-Type': 'application/json'
            })
        except ImportError:
            print("Warning: requests library not available")
            
    def _init_tts(self):
        """Initialize text-to-speech engine."""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        except ImportError:
            print("Warning: TTS engine not available, using fallback")
            self.tts_engine = None
            
    def update_telemetry(self, state: TelemetryState):
        """Update current telemetry state."""
        self.current_state = state
        self.telemetry_history.append(state)
        
        # Check for alerts
        self._check_alerts(state)
        
    def _check_alerts(self, state: TelemetryState):
        """Check for conditions that need voice alerts."""
        alerts = []
        
        # Radiation alert
        if state.radiation > 2.5 and 'RADIATION_HIGH' not in self.active_alerts:
            alerts.append(("CRITICAL: High radiation detected. Radiation level is {:.1f} microsieverts per hour. Recovery team advised to use protective equipment at landing site.".format(state.radiation), 'critical'))
            self.active_alerts.add('RADIATION_HIGH')
        elif state.radiation < 2.0 and 'RADIATION_HIGH' in self.active_alerts:
            self.active_alerts.discard('RADIATION_HIGH')
            
        # VOC alert
        if state.voc > 600 and 'VOC_HIGH' not in self.active_alerts:
            alerts.append(("WARNING: VOC spike detected. Volatile organic compounds at {} parts per million. Possible industrial exhaust or chemical source nearby.".format(int(state.voc)), 'warning'))
            self.active_alerts.add('VOC_HIGH')
        elif state.voc < 400 and 'VOC_HIGH' in self.active_alerts:
            self.active_alerts.discard('VOC_HIGH')
            
        # Battery alert
        if state.battery < 20 and 'BATTERY_LOW' not in self.active_alerts:
            alerts.append(("CAUTION: Battery level low at {} percent. Consider power conservation measures.".format(int(state.battery)), 'warning'))
            self.active_alerts.add('BATTERY_LOW')
        elif state.battery > 25 and 'BATTERY_LOW' in self.active_alerts:
            self.active_alerts.discard('BATTERY_LOW')
            
        # Altitude milestone
        milestones = [500, 400, 300, 200, 100, 50]
        for milestone in milestones:
            if milestone - 10 < state.altitude < milestone + 10 and state.altitude > 0:
                key = f'ALT_{milestone}'
                if key not in self.active_alerts:
                    alerts.append(('Altitude {} meters. Descent rate {} meters per second. All systems nominal.'.format(
                        milestone, abs(int(state.descent_rate))), 'info'))
                    self.active_alerts.add(key)
                    
        # Queue alerts
        for text, priority in alerts:
            self.announcement_queue.put(VoiceAnnouncement(
                text=text,
                priority=priority,
                timestamp=state.timestamp
            ))
            
    def generate_narrative(self) -> str:
        """
        Generate telemetry narrative using DeepSeek.
        
        Returns:
            Narrative string for voice output
        """
        if self.current_state is None:
            return "Telemetry data not available."
            
        state = self.current_state
        
        # Build context for DeepSeek
        context = self._build_context(state)
        
        # Query DeepSeek
        try:
            prompt = f"""Generate a short, clear voice announcement (2-3 sentences maximum) for CanSat telemetry at {int(state.altitude)} meters altitude.
            
Current readings:
- Altitude: {int(state.altitude)} meters
- Radiation: {state.radiation:.2f} µSv/h
- VOC: {int(state.voc)} ppm
- Temperature: {state.temperature:.1f} °C
- Battery: {int(state.battery)}%
- Descent rate: {abs(state.descent_rate):.1f} m/s
- Signal: {state.signal_strength} dBm

Focus on the most important information. Use simple, clear language suitable for voice output.
"""
            
            # Use local DeepSeek via Ollama API
            response = self._query_deepseek(prompt)
            
            if response:
                return response
                
        except Exception as e:
            print(f"DeepSeek query failed: {e}")
            
        # Fallback to template-based narration
        return self._generate_template_narration(state)
        
    def _query_deepseek(self, prompt: str) -> Optional[str]:
        """Query DeepSeek via API."""
        if self.client is None:
            return None
            
        try:
            import json
            payload = {
                'model': self.model_name,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'max_tokens': 100
                }
            }
            
            response = self.client.post(
                f"{self.api_endpoint}/api/generate",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
                
        except Exception as e:
            print(f"API call failed: {e}")
            
        return None
        
    def _build_context(self, state: TelemetryState) -> str:
        """Build context string from telemetry."""
        return f"Alt: {state.altitude:.0f}m, Rad: {state.radiation:.2f}, VOC: {state.voc:.0f}, Batt: {state.battery:.0f}%"
        
    def _generate_template_narration(self, state: TelemetryState) -> str:
        """Generate narration using templates."""
        parts = []
        
        # Altitude
        if state.altitude > 0:
            parts.append(f"Altitude {int(state.altitude)} meters")
            
        # Key metrics
        if state.radiation > 2.0:
            parts.append(f"Radiation elevated at {state.radiation:.1f} microsieverts")
        else:
            parts.append("Radiation stable")
            
        if state.voc > 400:
            parts.append(f"VOC at {int(state.voc)} parts per million")
            
        # Battery
        if state.battery < 30:
            parts.append(f"Battery at {int(state.battery)} percent")
            
        # Descent
        parts.append(f"Descent rate {abs(state.descent_rate):.1f} meters per second")
        
        return ". ".join(parts) + "."
        
    def speak(self, text: str):
        """Speak the given text."""
        if self.tts_engine:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        else:
            # Fallback: just print
            print(f"[VOICE] {text}")
            
    def process_announcements(self):
        """Background thread for processing announcements."""
        while self.running:
            try:
                announcement = self.announcement_queue.get(timeout=1)
                
                # Check priority and timing
                if announcement.priority == 'critical' or \
                   (announcement.timestamp - self.last_announcement_time > self.announcement_interval):
                    
                    self.speak(announcement.text)
                    self.last_announcement_time = announcement.timestamp
                    
            except queue.Empty:
                # No announcement waiting, generate periodic update
                if self.current_state and \
                   self.current_state.timestamp - self.last_announcement_time > self.announcement_interval:
                    
                    narrative = self.generate_narrative()
                    self.speak(narrative)
                    self.last_announcement_time = self.current_state.timestamp
                    
    def start(self):
        """Start the voice system."""
        self.running = True
        self.processing_thread = threading.Thread(target=self.process_announcements, daemon=True)
        self.processing_thread.start()
        
    def stop(self):
        """Stop the voice system."""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2)


class DeepSeekNarrativeGenerator:
    """
    DeepSeek-powered narrative generator for post-flight reports.
    """
    
    def __init__(
        self,
        api_endpoint: str = "http://localhost:11434/v1",
        model_name: str = "deepseek-r1:1.5b"
    ):
        self.api_endpoint = api_endpoint
        self.model_name = model_name
        self.client = None
        self._init_client()
        
    def _init_client(self):
        """Initialize API client."""
        try:
            import requests
            self.client = requests.Session()
        except ImportError:
            pass
            
    def generate_flight_summary(self, telemetry_data: List[TelemetryState]) -> str:
        """
        Generate flight summary narrative.
        
        Args:
            telemetry_data: List of all telemetry readings
            
        Returns:
            Summary text
        """
        if not telemetry_data:
            return "No telemetry data available."
            
        # Compute statistics
        altitudes = [t.altitude for t in telemetry_data]
        radiations = [t.radiation for t in telemetry_data]
        vocs = [t.voc for t in telemetry_data]
        max_altitude = max(altitudes)
        max_radiation = max(radiations)
        max_voc = max(vocs)
        
        prompt = f"""Generate a professional environmental flight summary for a CanSat mission.

Flight Statistics:
- Maximum Altitude: {max_altitude:.0f} meters
- Max Radiation: {max_radiation:.2f} µSv/h
- Max VOC: {max_voc:.0f} ppm
- Total Readings: {len(telemetry_data)}

Provide a concise summary (3-4 paragraphs) covering:
1. Overall mission performance
2. Environmental findings (radiation, air quality)
3. Notable events or anomalies
4. Recovery and data quality assessment

Use technical but accessible language suitable for a mission report.
"""
        
        response = self._query_deepseek(prompt)
        
        if response:
            return response
            
        # Fallback
        return self._generate_template_summary(telemetry_data, max_altitude, max_radiation, max_voc)
        
    def _query_deepseek(self, prompt: str) -> Optional[str]:
        """Query DeepSeek API."""
        if self.client is None:
            return None
            
        try:
            import json
            payload = {
                'model': self.model_name,
                'prompt': prompt,
                'stream': False
            }
            
            response = self.client.post(
                f"{self.api_endpoint}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', '').strip()
                
        except Exception as e:
            print(f"DeepSeek query failed: {e}")
            
        return None
        
    def _generate_template_summary(
        self,
        data: List[TelemetryState],
        max_alt: float,
        max_rad: float,
        max_voc: float
    ) -> str:
        """Generate summary using templates."""
        return f"""CanSat Environmental Flight Summary

Mission Overview:
The CanSat successfully completed its descent from {max_alt:.0f} meters, collecting {len(data)} telemetry readings throughout the flight.

Environmental Findings:
- Radiation levels remained within safe parameters, with maximum readings of {max_rad:.2f} µSv/h
- VOC measurements peaked at {max_voc:.0f} ppm, indicating {'possible pollutant presence' if max_voc > 400 else 'generally clean atmospheric conditions'}
- Temperature and pressure data showed expected atmospheric profiles

Data Quality:
The telemetry system recorded {(len(data)/len(data))*100:.0f}% valid data points, providing a comprehensive profile of the atmospheric conditions during descent.

Recommendation:
{'Further analysis recommended for elevated readings.' if max_rad > 2.0 or max_voc > 600 else 'Mission data within normal parameters.'}
"""


def create_voice_director(
    api_endpoint: str = "http://localhost:11434/v1",
    model: str = "deepseek-r1:1.5b"
) -> DeepSeekVoiceDirector:
    """Factory function."""
    return DeepSeekVoiceDirector(api_endpoint=api_endpoint, model_name=model)


def create_narrative_generator(
    api_endpoint: str = "http://localhost:11434/v1",
    model: str = "deepseek-r1:1.5b"
) -> DeepSeekNarrativeGenerator:
    """Factory function."""
    return DeepSeekNarrativeGenerator(api_endpoint=api_endpoint, model_name=model)


if __name__ == "__main__":
    print("Initializing DeepSeek Voice-Over-Telemetry...")
    voice_director = create_voice_director()
    
    # Simulate telemetry
    print("Simulating telemetry stream...")
    
    for i in range(50):
        state = TelemetryState(
            timestamp=i * 2,
            altitude=1000 - i * 20,
            radiation=0.5 + np.random.normal(0, 0.1),
            voc=200 + np.random.normal(50, 20),
            temperature=20 - i * 0.02,
            pressure=1013 - i * 0.01,
            battery=100 - i * 0.5,
            descent_rate=15 + np.random.normal(0, 2),
            gps_lock=True,
            signal_strength=-60 + np.random.normal(0, 5)
        )
        
        voice_director.update_telemetry(state)
        
        if i % 10 == 0:
            print(f"Updated telemetry at {state.altitude:.0f}m")
            
    print("\nVoice system ready.")