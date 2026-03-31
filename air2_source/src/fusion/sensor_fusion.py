"""
Sensor Fusion Module
Multi-sensor data fusion
"""

import numpy as np
from typing import Dict, List, Tuple
import logging


class KalmanFilter:
    """Kalman filter for sensor fusion"""
    
    def __init__(self, state_dim: int, meas_dim: int):
        self.state_dim = state_dim
        self.meas_dim = meas_dim
        
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim)
        self.Q = np.eye(state_dim) * 0.01
        self.R = np.eye(meas_dim) * 0.1
    
    def predict(self, F: np.ndarray):
        """Predict step"""
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
    
    def update(self, z: np.ndarray, H: np.ndarray):
        """Update step"""
        y = z - H @ self.x
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)
        
        self.x = self.x + K @ y
        self.P = (np.eye(self.state_dim) - K @ H) @ self.P


class ExtendedKalmanFilter:
    """EKF for nonlinear systems"""
    
    def __init__(self, state_dim: int, meas_dim: int):
        self.kf = KalmanFilter(state_dim, meas_dim)
    
    def predict(self, f, F_func, *args):
        """Predict with nonlinear function"""
        self.kf.x = f(self.kf.x, *args)
        F = F_func(self.kf.x, *args)
        self.kf.P = F @ self.kf.P @ F.T + self.kf.Q
    
    def update(self, h, H_func, z, *args):
        """Update with nonlinear measurement"""
        z_pred = h(self.kf.x, *args)
        H = H_func(self.kf.x, *args)
        
        y = z - z_pred
        S = H @ self.kf.P @ H.T + self.kf.R
        K = self.kf.P @ H.T @ np.linalg.inv(S)
        
        self.kf.x = self.kf.x + K @ y
        self.kf.P = (np.eye(self.kf.state_dim) - K @ H) @ self.kf.P
    
    @property
    def state(self):
        return self.kf.x
    
    @property
    def covariance(self):
        return self.kf.P


class SensorFusion:
    """Multi-sensor fusion"""
    
    def __init__(self):
        self.filters = {}
    
    def add_sensor(self, name: str, state_dim: int, meas_dim: int):
        """Add sensor"""
        self.filters[name] = KalmanFilter(state_dim, meas_dim)
    
    def predict(self, name: str, F: np.ndarray):
        """Predict"""
        if name in self.filters:
            self.filters[name].predict(F)
    
    def update(self, name: str, z: np.ndarray, H: np.ndarray):
        """Update"""
        if name in self.filters:
            self.filters[name].update(z, H)
    
    def get_fused_state(self) -> np.ndarray:
        """Get fused state"""
        if not self.filters:
            return np.array([])
        
        # Simple average
        states = [f.x for f in self.filters.values()]
        return np.mean(states, axis=0)


# Example
if __name__ == "__main__":
    print("Testing Sensor Fusion...")
    
    fusion = SensorFusion()
    fusion.add_sensor("gps", 3, 3)
    fusion.add_sensor("baro", 3, 1)
    
    z = np.array([1.0, 2.0, 3.0])
    H = np.eye(3)
    fusion.update("gps", z, H)
    
    print(f"Fused: {fusion.get_fused_state()}")