"""
Flight Dynamics Module
Flight dynamics and physics simulation
"""

import numpy as np
from typing import Tuple, Dict


class FlightDynamics:
    """Flight dynamics calculations"""
    
    def __init__(self, mass: float = 1.0, drag_coeff: float = 0.1):
        self.mass = mass
        self.drag_coeff = drag_coeff
    
    def calculate_forces(self, velocity: np.ndarray, altitude: float) -> np.ndarray:
        """Calculate aerodynamic forces"""
        speed = np.linalg.norm(velocity)
        drag = -self.drag_coeff * speed * velocity
        
        g = 9.81
        gravity = np.array([0, 0, -self.mass * g])
        
        return drag + gravity
    
    def calculate_lift(self, velocity: np.ndarray, angle_of_attack: float) -> float:
        """Calculate lift force"""
        speed = np.linalg.norm(velocity)
        return 0.5 * speed**2 * np.sin(angle_of_attack)


class TrajectoryCalculator:
    """Calculate flight trajectories"""
    
    def __init__(self):
        self.g = 9.81
    
    def ballistic_trajectory(self, v0: float, angle: float, altitude: float = 0) -> Dict:
        """Calculate ballistic trajectory"""
        theta = np.radians(angle)
        t_flight = 2 * v0 * np.sin(theta) / self.g
        h_max = (v0 * np.sin(theta))**2 / (2 * self.g)
        r_max = (v0**2 * np.sin(2 * theta)) / self.g
        
        return {
            'time_of_flight': t_flight,
            'max_height': h_max,
            'range': r_max,
            'initial_velocity': v0,
            'angle': angle
        }
    
    def orbital_velocity(self, altitude: float) -> float:
        """Calculate orbital velocity"""
        R = 6371000 + altitude
        mu = 3.986e14
        return np.sqrt(mu / R)


# Example
if __name__ == "__main__":
    td = FlightDynamics()
    print(f"Forces: {td.calculate_forces(np.array([10,0,0]), 100)}")