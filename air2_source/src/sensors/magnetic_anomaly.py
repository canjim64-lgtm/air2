"""
Magnetic Anomaly Detector (MAD) for AirOne Professional v4.0
Processes 3-axis magnetometer data to detect localized magnetic disturbances (e.g., metallic structures, mineral deposits).
"""
import logging
import math
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MagneticAnomalyDetector:
    def __init__(self, base_lat: float = 34.05, base_lon: float = -118.24):
        self.logger = logging.getLogger(f"{__name__}.MagneticAnomalyDetector")
        # Base Earth Magnetic Field approximation (in microteslas, uT)
        # Using a simplified dipole model for the baseline expected field
        self.base_lat = math.radians(base_lat)
        self.expected_field = self._calculate_expected_field(self.base_lat)
        self.baseline_magnitude = np.linalg.norm(self.expected_field)
        self.anomaly_threshold = 2.5 # uT deviation to trigger alert
        self.logger.info(f"Magnetic Anomaly Detector Initialized. Base Field: {self.baseline_magnitude:.2f} uT")

    def _calculate_expected_field(self, lat_rad: float) -> np.ndarray:
        """Simplified dipole model of Earth's magnetic field at a given latitude."""
        B0 = 31.2 # Equatorial field in uT
        Bx = B0 * math.cos(lat_rad) # North component
        By = 0.0 # East component (assuming aligned with magnetic north)
        Bz = 2 * B0 * math.sin(lat_rad) # Down component
        return np.array([Bx, By, Bz])

    def process_reading(self, mag_x: float, mag_y: float, mag_z: float) -> Dict[str, Any]:
        """Compares measured 3-axis magnetic field against the expected baseline."""
        measured_field = np.array([mag_x, mag_y, mag_z])
        measured_magnitude = np.linalg.norm(measured_field)
        
        # Calculate vector difference (anomaly vector)
        anomaly_vector = measured_field - self.expected_field
        anomaly_magnitude = np.linalg.norm(anomaly_vector)
        
        status = "NOMINAL"
        confidence = 1.0
        
        if anomaly_magnitude > self.anomaly_threshold:
            if anomaly_magnitude > self.anomaly_threshold * 5:
                status = "MAJOR_ANOMALY_DETECTED"
                confidence = 0.99
                self.logger.critical(f"MAJOR MAGNETIC ANOMALY: {anomaly_magnitude:.2f} uT deviation.")
            else:
                status = "MINOR_ANOMALY_DETECTED"
                confidence = min(0.9, anomaly_magnitude / (self.anomaly_threshold * 5))
                self.logger.warning(f"Magnetic Anomaly Detected: {anomaly_magnitude:.2f} uT deviation.")

        return {
            "status": status,
            "measured_magnitude_uT": round(measured_magnitude, 2),
            "expected_magnitude_uT": round(self.baseline_magnitude, 2),
            "anomaly_magnitude_uT": round(anomaly_magnitude, 2),
            "anomaly_vector": {
                "dx": round(anomaly_vector[0], 2),
                "dy": round(anomaly_vector[1], 2),
                "dz": round(anomaly_vector[2], 2)
            },
            "detection_confidence": round(confidence, 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mad = MagneticAnomalyDetector()
    # Nominal reading
    print(mad.process_reading(25.9, 0.0, 42.0))
    # Anomaly reading (e.g. passing over a large iron deposit)
    print(mad.process_reading(30.0, -5.0, 48.0))
