"""
Adaptive Parachute Deployment Algorithm for AirOne Professional v4.0
Dynamically calculates the optimal deployment altitude to minimize landing drift.
"""
import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AdaptiveParachuteDeployer:
    def __init__(self, parachute_cd: float = 1.5, parachute_area: float = 1.0, mass_kg: float = 1.5):
        self.logger = logging.getLogger(f"{__name__}.AdaptiveParachuteDeployer")
        self.cd = parachute_cd
        self.area = parachute_area
        self.mass = mass_kg
        self.gravity = 9.81
        self.air_density = 1.225 # sea level approx
        self.deployed = False
        
        # Calculate terminal velocity under canopy
        # Vt = sqrt(2mg / rho * A * Cd)
        self.chute_terminal_velocity = math.sqrt((2 * self.mass * self.gravity) / (self.air_density * self.area * self.cd))
        self.logger.info(f"Adaptive Parachute Deployer Initialized. Canopy V_t: {self.chute_terminal_velocity:.2f} m/s")

    def calculate_deployment_solution(self, current_alt: float, current_vel_z: float, 
                                      wind_speed_ms: float, target_lz_distance_m: float) -> Dict[str, Any]:
        """
        Calculates if the parachute should be deployed now to hit the target landing zone.
        """
        if self.deployed:
            return {"status": "ALREADY_DEPLOYED", "action": "NONE"}

        if current_vel_z >= 0:
            return {"status": "ASCENDING_OR_APOGEE", "action": "WAIT"}

        # Estimated drift if we deploy right now
        # Time to ground = Alt / Canopy_Vt
        time_under_canopy = current_alt / self.chute_terminal_velocity
        estimated_drift = time_under_canopy * wind_speed_ms
        
        # Difference between estimated drift and distance to target
        drift_error = estimated_drift - target_lz_distance_m
        
        action = "WAIT"
        reason = "Drift would overshoot target"
        
        # If drift error is negative, we need to fall faster (freefall) before deploying
        # If drift error is near zero, DEPLOY!
        # If drift error is positive, we waited too long or wind is too strong
        
        if drift_error > 0:
            action = "DEPLOY_IMMEDIATELY"
            reason = "Overshoot risk increasing. Deploy to arrest fall."
            self.deployed = True
            self.logger.critical(f"PARACHUTE DEPLOYED AT {current_alt:.1f}m! (Drift Error: {drift_error:.1f}m)")
        elif abs(drift_error) < 50.0: # 50m tolerance window
            action = "DEPLOY_OPTIMAL"
            reason = "Optimal deployment window reached."
            self.deployed = True
            self.logger.info(f"OPTIMAL PARACHUTE DEPLOYMENT AT {current_alt:.1f}m.")
        elif current_alt <= 200.0: # Hard deck
            action = "DEPLOY_HARD_DECK"
            reason = "Hard deck reached. Deploying for safety."
            self.deployed = True
            self.logger.warning(f"HARD DECK PARACHUTE DEPLOYMENT AT {current_alt:.1f}m.")
            
        return {
            "status": "CALCULATED",
            "action": action,
            "reason": reason,
            "time_under_canopy_s": round(time_under_canopy, 1),
            "estimated_drift_m": round(estimated_drift, 1),
            "target_drift_error_m": round(drift_error, 1)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    deployer = AdaptiveParachuteDeployer()
    # High altitude, high wind, target is 1000m away
    print(deployer.calculate_deployment_solution(2000, -50, 10.0, 1000.0))
    # Optimal window
    print(deployer.calculate_deployment_solution(500, -50, 10.0, 1000.0))
