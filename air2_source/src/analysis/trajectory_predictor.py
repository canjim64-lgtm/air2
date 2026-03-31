"""
Hypersonic Trajectory Predictor for AirOne Professional v4.0
Calculates descent profiles modeling aerodynamic drag, ballistic coefficients, and Mach speeds.
"""
import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TrajectoryPredictor:
    def __init__(self, mass_kg: float = 1.5, cross_sectional_area_m2: float = 0.05, drag_coefficient: float = 0.75):
        self.logger = logging.getLogger(f"{__name__}.TrajectoryPredictor")
        self.mass = mass_kg
        self.area = cross_sectional_area_m2
        self.cd = drag_coefficient
        self.gravity = 9.80665
        self.gas_constant = 287.05
        # Precompute Ballistic Coefficient (kg/m^2)
        self.ballistic_coefficient = self.mass / (self.cd * self.area)
        self.logger.info(f"Trajectory Predictor Initialized. Ballistic Coefficient: {self.ballistic_coefficient:.2f} kg/m^2")

    def _get_air_density(self, altitude_m: float) -> float:
        """Simplified standard atmosphere density calculation."""
        # Sea level density
        rho0 = 1.225
        # Scale height
        H = 8500.0
        return rho0 * math.exp(-altitude_m / H)

    def _get_speed_of_sound(self, altitude_m: float) -> float:
        """Approximates speed of sound based on altitude temperature profile."""
        temp_c = max(-56.5, 15.0 - (0.0065 * altitude_m))
        temp_k = temp_c + 273.15
        return math.sqrt(1.4 * self.gas_constant * temp_k)

    def predict_descent(self, current_altitude_m: float, vertical_velocity_m_s: float) -> Dict[str, Any]:
        """Predicts terminal velocity and aerodynamic stresses based on current state."""
        rho = self._get_air_density(current_altitude_m)
        sos = self._get_speed_of_sound(current_altitude_m)
        
        # Current Mach number
        mach_number = abs(vertical_velocity_m_s) / sos if sos > 0 else 0
        
        # Calculate Terminal Velocity at this altitude
        # V_t = sqrt((2 * m * g) / (rho * A * Cd))
        terminal_velocity = math.sqrt((2 * self.mass * self.gravity) / (rho * self.area * self.cd)) if rho > 0 else float('inf')
        
        # Calculate aerodynamic pressure (Dynamic Pressure q = 0.5 * rho * v^2)
        dynamic_pressure_pa = 0.5 * rho * (vertical_velocity_m_s ** 2)
        
        status = "NOMINAL"
        if mach_number >= 5.0:
            status = "HYPERSONIC_DESCENT"
        elif mach_number >= 1.0:
            status = "SUPERSONIC_DESCENT"
        elif dynamic_pressure_pa > 50000:
            status = "MAX_Q_STRESS"

        return {
            "status": status,
            "mach_number": round(mach_number, 3),
            "dynamic_pressure_pa": round(dynamic_pressure_pa, 2),
            "estimated_terminal_velocity_m_s": round(terminal_velocity, 2),
            "ballistic_coefficient": round(self.ballistic_coefficient, 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tp = TrajectoryPredictor(mass_kg=2.0, cross_sectional_area_m2=0.01, drag_coefficient=0.5)
    print(tp.predict_descent(30000, -800)) # High altitude, high speed
