"""
Cognitive Frequency Hopping (CFH) for AirOne Professional v4.0
Noise-aware frequency selection for resilient radio communication.
"""
import logging
import random
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CognitiveHoppingEngine:
    def __init__(self, frequency_pool: List[float] = [433.0, 434.5, 868.0, 915.0]):
        self.logger = logging.getLogger(f"{__name__}.CognitiveHoppingEngine")
        self.frequency_pool = frequency_pool
        self.current_freq = frequency_pool[0]
        self.interference_threshold = -85.0 # dBm
        self.logger.info(f"Cognitive Hopping Engine Initialized. Pool: {frequency_pool} MHz.")

    def evaluate_spectrum(self, noise_data: Dict[float, float]) -> Dict[str, Any]:
        """Analyzes spectrum noise map and selects the cleanest available frequency."""
        current_noise = noise_data.get(self.current_freq, -110.0)
        needs_hop = current_noise > self.interference_threshold
        
        result = {
            "current_frequency": self.current_freq,
            "status": "NOMINAL",
            "hop_required": needs_hop,
            "measured_noise": current_noise
        }
        
        if needs_hop:
            # Find frequency with minimum noise
            cleanest_freq = min(noise_data, key=noise_data.get)
            if cleanest_freq != self.current_freq:
                self.logger.warning(f"JAMMING DETECTED on {self.current_freq}MHz ({current_noise}dBm). Hopping to {cleanest_freq}MHz.")
                self.current_freq = cleanest_freq
                result["status"] = "HOP_COMPLETE"
                result["current_frequency"] = self.current_freq
            else:
                result["status"] = "ALL_CHANNELS_JAMMED"
                self.logger.critical("Spectrum saturated. No clean channels available.")
                
        return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfh = CognitiveHoppingEngine()
    # Mock spectrum scan
    scan = {433.0: -75.0, 434.5: -105.0, 868.0: -90.0, 915.0: -95.0}
    print(cfh.evaluate_spectrum(scan))
