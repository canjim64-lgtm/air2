"""
DeepSeek R1 8B Integration Module
Local LLM for telemetry analysis and voice alerts
Uses DeepSeek R1 8B for all AI operations
"""

import subprocess
import json
import threading
import queue
from typing import Dict, List, Optional


class DeepSeekIntegration:
    """DeepSeek R1 8B local LLM integration"""
    
    def __init__(self, model_path: str = "deepseek-r1:8b"):
        self.model_path = model_path
        self.ollama_available = False
        self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama is available"""
        try:
            result = subprocess.run(["ollama", "list"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                self.ollama_available = True
        except:
            self.ollama_available = False
    
    def generate(self, prompt: str, system: str = None) -> str:
        """Generate response from DeepSeek"""
        if not self.ollama_available:
            return "[DeepSeek not available - install Ollama]"
        
        cmd = ["ollama", "run", self.model_path]
        if system:
            cmd.insert(3, system)
        
        try:
            result = subprocess.run(cmd, 
                                  input=prompt,
                                  capture_output=True, 
                                  text=True, timeout=60)
            return result.stdout
        except:
            return "[LLM timeout]"
    
    def analyze_telemetry(self, data: Dict) -> str:
        """Analyze telemetry with DeepSeek"""
        prompt = f"Analyze this CanSat telemetry: {json.dumps(data)}"
        return self.generate(prompt, "You are a CanSat flight analyst.")
    
    def voice_alert(self, condition: str) -> str:
        """Generate voice alert message"""
        prompt = f"Create a short safety warning for: {condition}"
        return self.generate(prompt, "Create a brief safety message.")
    
    def summarize_flight(self, csv_data: str) -> str:
        """Summarize flight data"""
        prompt = f"Summarize this flight CSV: {csv_data[:2000]}"
        return self.generate(prompt, "Write a professional flight summary.")


class VoiceAlertSystem:
    """Automated voice alerts for safety"""
    
    def __init__(self):
        self.deepseek = DeepSeekIntegration()
        self.thresholds = {
            'radiation': 2.5,  # µSv/h
            'voc': 500,  # ppm
            'altitude': 50  # meters
        }
    
    def check_and_alert(self, telemetry: Dict) -> Optional[str]:
        """Check conditions and generate alert"""
        alerts = []
        
        if telemetry.get('radiation', 0) > self.thresholds['radiation']:
            alerts.append("High radiation detected")
        
        if telemetry.get('voc', 0) > self.thresholds['voc']:
            alerts.append("Toxic VOC levels detected")
        
        if telemetry.get('altitude', 100) < self.thresholds['altitude']:
            alerts.append("Approaching landing zone")
        
        if alerts:
            return self.deepseek.voice_alert(", ".join(alerts))
        return None


class AutomatedReportGenerator:
    """Generate flight reports using DeepSeek"""
    
    def __init__(self):
        self.deepseek = DeepSeekIntegration()
    
    def generate_report(self, flight_data: Dict) -> str:
        """Generate environmental report"""
        return self.deepseek.summarize_flight(json.dumps(flight_data))


# Example
if __name__ == "__main__":
    ds = DeepSeekIntegration()
    print("DeepSeek R1 8B Integration Ready")
    print(f"Ollama available: {ds.ollama_available}")