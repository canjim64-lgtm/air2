"""
Radio Doppler Shift Compensator for AirOne Professional v4.0
Calculates frequency shift based on the relative velocity vector for phase-locked loop (PLL) tuning.
"""
import logging
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DopplerCompensator:
    def __init__(self, carrier_freq_hz: float = 433e6):
        self.logger = logging.getLogger(f"{__name__}.DopplerCompensator")
        self.carrier_freq = carrier_freq_hz
        self.c = 299792458.0 # m/s
        self.station_pos = np.array([0.0, 0.0, 0.0]) # ECEF local coords
        self.logger.info(f"Doppler Compensator Initialized for {carrier_freq_hz/1e6} MHz.")

    def calculate_shift(self, sat_pos: np.ndarray, sat_vel: np.ndarray) -> Dict[str, Any]:
        """Calculates the expected Doppler shift for SDR frequency correction."""
        # Relative position vector from Ground Station to CanSat
        rel_pos = sat_pos - self.station_pos
        distance = np.linalg.norm(rel_pos)
        
        if distance == 0:
            return {"status": "ZERO_DISTANCE", "doppler_shift_hz": 0.0, "corrected_freq_hz": self.carrier_freq}
            
        # Line of sight unit vector
        los_unit = rel_pos / distance
        
        # Radial velocity (projection of velocity onto line of sight)
        # Positive means moving away, negative means moving closer
        v_radial = np.dot(sat_vel, los_unit)
        
        # Doppler equation: f_r = f_t * (c / (c + v_radial))
        received_freq = self.carrier_freq * (self.c / (self.c + v_radial))
        doppler_shift = received_freq - self.carrier_freq
        
        action = "NOMINAL"
        if abs(doppler_shift) > 5000: # > 5kHz shift requires active SDR retuning
            action = "APPLY_PLL_CORRECTION"
            self.logger.info(f"High Doppler Shift: {doppler_shift:.1f} Hz. Retuning SDR...")

        return {
            "status": action,
            "radial_velocity_m_s": round(float(v_radial), 2),
            "doppler_shift_hz": round(float(doppler_shift), 2),
            "expected_rx_freq_hz": round(float(received_freq), 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dc = DopplerCompensator()
    # Sat at 10km altitude, moving laterally at 7500 m/s (LEO speed)
    pos = np.array([0.0, 0.0, 10000.0])
    vel = np.array([7500.0, 0.0, -100.0])
    print(dc.calculate_shift(pos, vel))
