"""
Predictive RF Link Analyzer for AirOne Professional v4.0
Implements a Free-Space Path Loss (FSPL) model and Horizon-Line-of-Sight prediction.
"""
import logging
import math
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class PredictiveLinkAnalyzer:
    def __init__(self, frequency_mhz: float = 433.0, tx_power_dbm: float = 20.0):
        self.logger = logging.getLogger(f"{__name__}.PredictiveLinkAnalyzer")
        self.frequency = frequency_mhz * 1e6 # Hz
        self.tx_power = tx_power_dbm
        self.ant_gain_tx = 2.15 # dBi (Dipole)
        self.ant_gain_rx = 5.0  # dBi (Directional)
        self.speed_of_light = 299792458
        self.earth_radius = 6371000
        self.rx_sensitivity = -115.0 # dBm
        self.history: List[Dict[str, float]] = []
        self.logger.info(f"Predictive Link Analyzer Initialized. TX Power: {tx_power_dbm}dBm, Freq: {frequency_mhz}MHz.")

    def calculate_link_margin(self, distance_m: float) -> float:
        """Calculates expected RSSI using Friis Transmission Equation."""
        if distance_m <= 0: return self.tx_power + self.ant_gain_tx + self.ant_gain_rx
        
        # FSPL = 20log10(d) + 20log10(f) + 20log10(4pi/c)
        fspl = 20 * math.log10(distance_m) + 20 * math.log10(self.frequency) + 20 * math.log10(4 * math.pi / self.speed_of_light)
        expected_rssi = self.tx_power + self.ant_gain_tx + self.ant_gain_rx - fspl
        return expected_rssi

    def update(self, altitude: float, distance_from_station: float, rssi: float) -> Dict[str, Any]:
        """Analyzes telemetry to predict link risk and time-to-loss."""
        expected_rssi = self.calculate_link_margin(distance_from_station)
        fading_margin = rssi - self.rx_sensitivity
        
        # Calculate geometric horizon
        horizon_dist = math.sqrt(2 * self.earth_radius * max(altitude, 0.1))
        los_margin = horizon_dist - distance_from_station
        
        # Link budget health
        link_quality = min(1.0, fading_margin / 40.0) # Normalized 0-1
        
        self.history.append({"t": time.time(), "rssi": rssi, "dist": distance_from_station})
        if len(self.history) > 30: self.history.pop(0)

        # Predict time to LOS (Geometric)
        time_to_los = -1.0
        if len(self.history) > 5:
            dist_delta = self.history[-1]['dist'] - self.history[0]['dist']
            if dist_delta > 0: # Moving away
                speed = dist_delta / (self.history[-1]['t'] - self.history[0]['t'])
                time_to_los = max(0, los_margin / speed)

        risk = "LOW"
        if los_margin < 500 or fading_margin < 10: risk = "CRITICAL"
        elif los_margin < 2000 or fading_margin < 20: risk = "HIGH"
        elif los_margin < 5000: risk = "MEDIUM"

        return {
            "link_risk_level": risk,
            "expected_rssi_dbm": round(expected_rssi, 2),
            "actual_rssi_dbm": round(rssi, 2),
            "fading_margin_db": round(fading_margin, 2),
            "los_margin_m": round(los_margin, 2),
            "time_to_los_s": round(time_to_los, 1) if time_to_los > 0 else "N/A",
            "link_quality": round(link_quality, 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    analyzer = PredictiveLinkAnalyzer()
    print(analyzer.update(altitude=3000, distance_from_station=150000, rssi=-95))
