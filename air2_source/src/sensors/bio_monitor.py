"""
Organic Payload Bio-Monitor for AirOne Professional v4.0
Monitors physiological telemetry for biological payloads (e.g., plants, insects, astronauts).
"""
import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BioMonitor:
    def __init__(self, target_species: str = "Human"):
        self.logger = logging.getLogger(f"{__name__}.BioMonitor")
        self.target_species = target_species
        self.baseline_hr = 75.0
        self.baseline_spo2 = 98.0
        self.logger.info(f"Bio-Monitor Initialized for payload type: {self.target_species}")

    def analyze_vitals(self, current_hr: float, current_spo2: float, g_force: float, cabin_pressure_pa: float) -> Dict[str, Any]:
        """Analyzes physiological limits against G-force and pressure constraints."""
        
        status = "NOMINAL"
        hr_variance = abs(current_hr - self.baseline_hr) / self.baseline_hr
        
        # Hypoxia check (Oxygen partial pressure drop)
        if current_spo2 < 90.0:
            status = "HYPOXIA_WARNING"
            self.logger.warning(f"Bio-Payload SpO2 dropping: {current_spo2}%")
            
        if current_spo2 < 80.0:
            status = "CRITICAL_HYPOXIA"
            self.logger.critical(f"LIFE SUPPORT CRITICAL: SpO2 at {current_spo2}%")

        # G-Force Tolerance (GLOC risk)
        g_status = "SAFE"
        if g_force > 4.0:
            g_status = "HIGH_G_LOAD"
        if g_force > 9.0:
            g_status = "GLOC_RISK"
            status = "BIOLOGICAL_STRESS_CRITICAL"
            self.logger.critical(f"G-LOC RISK IMMINENT: sustained {g_force}G load.")

        return {
            "overall_health_status": status,
            "g_force_tolerance": g_status,
            "heart_rate_bpm": round(current_hr, 1),
            "blood_oxygen_spo2": round(current_spo2, 1),
            "cabin_pressure_pa": round(cabin_pressure_pa, 2),
            "stress_index": round(hr_variance * (g_force / 2.0), 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bio = BioMonitor()
    print(bio.analyze_vitals(current_hr=130.0, current_spo2=88.5, g_force=6.5, cabin_pressure_pa=70000.0))
