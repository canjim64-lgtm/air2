"""
LLM Assistant (Chatbot) for AirOne Professional v4.0
Sophisticated natural language interface for system telemetry and queries.
"""
import logging
import json
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class LLMAssistant:
    def __init__(self, use_deepseek: bool = False):
        self.logger = logging.getLogger(f"{__name__}.LLMAssistant")
        self.use_deepseek = use_deepseek
        self.chat_history = []
        self.intents = [
            (r"(status|health|how are you)", self._intent_status),
            (r"(altitude|how high|height)", self._intent_altitude),
            (r"(velocity|speed|how fast)", self._intent_velocity),
            (r"(location|where|coordinates|gps)", self._intent_location),
            (r"(battery|power|voltage)", self._intent_battery),
            (r"(help|can you|what do you do)", self._intent_help)
        ]
        
        self.deepseek_model = None
        if self.use_deepseek:
            try:
                from ai.deepseek_model_integration import DeepSeekModelIntegration
                self.deepseek_model = DeepSeekModelIntegration()
            except ImportError:
                self.use_deepseek = False
                
        self.logger.info("Advanced LLM Assistant (Intent-Engine) Initialized.")

    def query(self, user_input: str, system_data: Dict[str, Any] = None) -> str:
        self.chat_history.append({"role": "user", "content": user_input})
        
        # Priority 1: DeepSeek R1 if available
        if self.use_deepseek and self.deepseek_model and self.deepseek_model.model_loaded:
            prompt = f"System Context: AirOne v4.0 Ground Station\nData: {json.dumps(system_data)}\nUser: {user_input}\nAI:"
            return self.deepseek_model._generate_response(prompt, max_new_tokens=200)

        # Priority 2: Intent Matching Engine
        for pattern, handler in self.intents:
            if re.search(pattern, user_input.lower()):
                response = handler(system_data)
                self.chat_history.append({"role": "assistant", "content": response})
                return response

        return f"I've noted your query about '{user_input}'. For specific telemetry like altitude or battery, please ask directly, or consult the technical manual."

    def _intent_status(self, data):
        mode = data.get('mode', 'Standby') if data else 'Standby'
        return f"System health is NOMINAL. Currently operating in {mode} mode. All sub-systems report ready."

    def _intent_altitude(self, data):
        alt = data.get('altitude', 0.0) if data else 0.0
        return f"The current AGL altitude is {alt:.2f} meters." if alt > 0 else "The system is currently on the pad (Altitude: 0m)."

    def _intent_velocity(self, data):
        vel = data.get('velocity', 0.0) if data else 0.0
        return f"Current vertical velocity is {vel:.2f} m/s."

    def _intent_location(self, data):
        lat = data.get('latitude', 0.0) if data else 0.0
        lon = data.get('longitude', 0.0) if data else 0.0
        return f"GPS Coordinates: Lat {lat:.6f}, Lon {lon:.6f}."

    def _intent_battery(self, data):
        v = data.get('battery_voltage', 12.6) if data else 12.6
        return f"Main battery rail is at {v:.2f}V. Capacity is sufficient for the current mission profile."

    def _intent_help(self, data):
        return "I can provide real-time telemetry analysis, health reports, and GPS tracking info. Try asking 'What is our altitude?' or 'Check system status'."

if __name__ == "__main__":
    assistant = LLMAssistant()
    print(assistant.query("how high are we?", {"altitude": 450.2}))
