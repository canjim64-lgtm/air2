"""
Autonomous Re-entry Guidance (ARG) for AirOne Professional v4.0
PID-based cross-track error correction for steerable parachute descent.
"""
import logging
import math
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReentryGuidance:
    def __init__(self, kp: float = 0.5, ki: float = 0.01, kd: float = 0.1):
        self.logger = logging.getLogger(f"{__name__}.ARG")
        self.kp, self.ki, self.kd = kp, ki, kd
        self.prev_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()
        self.logger.info(f"Re-entry Guidance Initialized (PID: {kp}, {ki}, {kd}).")

    def calculate_steering(self, current_pos: tuple, target_pos: tuple, current_heading: float) -> Dict[str, Any]:
        """Calculates steering deflection (-1.0 to 1.0) to reach target."""
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        
        # Calculate target heading (Azimuth)
        dlon = math.radians(target_pos[1] - current_pos[1])
        lat1, lat2 = math.radians(current_pos[0]), math.radians(target_pos[0])
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        target_heading = (math.degrees(math.atan2(y, x)) + 360) % 360
        
        # Cross-track error (Heading error)
        error = (target_heading - current_heading + 180) % 360 - 180
        
        # PID Logic
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        self.prev_error = error
        
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        # Clamping output to servo limits
        steering_deflection = max(-1.0, min(1.0, output / 45.0))
        
        return {
            "target_heading_deg": round(target_heading, 2),
            "heading_error_deg": round(error, 2),
            "steering_deflection": round(steering_deflection, 3),
            "distance_to_target_m": round(self._haversine(current_pos, target_pos), 1)
        }

    def _haversine(self, pos1, pos2):
        R = 6371000
        phi1, phi2 = math.radians(pos1[0]), math.radians(pos2[0])
        dphi = math.radians(pos2[0] - pos1[0])
        dlambda = math.radians(pos2[1] - pos1[1])
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    arg = ReentryGuidance()
    print(arg.calculate_steering((34.0, -118.0), (34.1, -118.1), 45.0))
