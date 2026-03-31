"""
Advanced Sensor Fusion Engine
EKF, UKF, and Particle Filter implementations for multi-sensor fusion
"""

import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple, List
from scipy.linalg import cholesky

logger = logging.getLogger(__name__)

class ExtendedKalmanFilter:
    """
    Extended Kalman Filter for nonlinear state estimation.
    State vector: [altitude, velocity, acceleration, temperature, pressure]
    """
    
    def __init__(self, state_dim: int = 5, meas_dim: int = 3):
        self.state_dim = state_dim
        self.meas_dim = meas_dim
        
        # State estimate
        self.x = np.zeros(state_dim)
        
        # Covariance matrix
        self.P = np.eye(state_dim) * 10.0
        
        # Process noise
        self.Q = np.eye(state_dim) * 0.1
        
        # Measurement noise
        self.R = np.eye(meas_dim) * 1.0
        
        logger.info(f"EKF initialized: state_dim={state_dim}, meas_dim={meas_dim}")
    
    def predict(self, dt: float, control_input: Optional[np.ndarray] = None):
        """
        Prediction step using motion model.
        
        Args:
            dt: Time step
            control_input: Optional control input
        """
        # Simple motion model: x_k+1 = F * x_k
        F = np.eye(self.state_dim)
        F[0, 1] = dt  # altitude += velocity * dt
        F[1, 2] = dt  # velocity += acceleration * dt
        
        # Predict state
        self.x = F @ self.x
        
        # Predict covariance
        self.P = F @ self.P @ F.T + self.Q
    
    def update(self, measurement: np.ndarray, measurement_jacobian: np.ndarray):
        """
        Update step with measurement.
        
        Args:
            measurement: Measurement vector
            measurement_jacobian: Jacobian of measurement function (H matrix)
        """
        H = measurement_jacobian
        
        # Innovation
        y = measurement - H @ self.x
        
        # Innovation covariance
        S = H @ self.P @ H.T + self.R[:len(measurement), :len(measurement)]
        
        # Kalman gain
        K = self.P @ H.T @ np.linalg.inv(S)
        
        # Update state
        self.x = self.x + K @ y
        
        # Update covariance
        I = np.eye(self.state_dim)
        self.P = (I - K @ H) @ self.P
    
    def get_state(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get current state estimate and covariance"""
        return self.x.copy(), self.P.copy()


class UnscentedKalmanFilter:
    """
    Unscented Kalman Filter for highly nonlinear systems.
    Uses sigma points instead of linearization.
    """
    
    def __init__(self, state_dim: int = 5, meas_dim: int = 3):
        self.state_dim = state_dim
        self.meas_dim = meas_dim
        
        # State estimate
        self.x = np.zeros(state_dim)
        
        # Covariance
        self.P = np.eye(state_dim) * 10.0
        
        # Process and measurement noise
        self.Q = np.eye(state_dim) * 0.1
        self.R = np.eye(meas_dim) * 1.0
        
        # UKF parameters
        self.alpha = 1e-3
        self.beta = 2.0
        self.kappa = 0.0
        
        self.lambda_ = self.alpha**2 * (state_dim + self.kappa) - state_dim
        
        # Weights
        self.Wm = np.zeros(2 * state_dim + 1)
        self.Wc = np.zeros(2 * state_dim + 1)
        
        self.Wm[0] = self.lambda_ / (state_dim + self.lambda_)
        self.Wc[0] = self.lambda_ / (state_dim + self.lambda_) + (1 - self.alpha**2 + self.beta)
        
        for i in range(1, 2 * state_dim + 1):
            self.Wm[i] = 1.0 / (2 * (state_dim + self.lambda_))
            self.Wc[i] = 1.0 / (2 * (state_dim + self.lambda_))
        
        logger.info(f"UKF initialized: state_dim={state_dim}")
    
    def _generate_sigma_points(self) -> np.ndarray:
        """Generate sigma points using unscented transform"""
        n = self.state_dim
        sigma_points = np.zeros((2 * n + 1, n))
        
        # Mean
        sigma_points[0] = self.x
        
        # Compute matrix square root
        try:
            U = cholesky((n + self.lambda_) * self.P, lower=False)
        except np.linalg.LinAlgError:
            # Fallback if Cholesky fails
            U = np.sqrt((n + self.lambda_)) * np.eye(n)
        
        # Positive sigma points
        for i in range(n):
            sigma_points[i + 1] = self.x + U[i]
        
        # Negative sigma points
        for i in range(n):
            sigma_points[n + i + 1] = self.x - U[i]
        
        return sigma_points
    
    def predict(self, dt: float):
        """Prediction step using sigma points"""
        # Generate sigma points
        sigma_points = self._generate_sigma_points()
        
        # Propagate sigma points through motion model
        F = np.eye(self.state_dim)
        F[0, 1] = dt
        F[1, 2] = dt
        
        sigma_points_pred = (F @ sigma_points.T).T
        
        # Compute predicted mean
        self.x = np.sum(self.Wm[:, np.newaxis] * sigma_points_pred, axis=0)
        
        # Compute predicted covariance
        self.P = self.Q.copy()
        for i in range(2 * self.state_dim + 1):
            diff = sigma_points_pred[i] - self.x
            self.P += self.Wc[i] * np.outer(diff, diff)
    
    def update(self, measurement: np.ndarray):
        """Update step with measurement"""
        # Generate sigma points
        sigma_points = self._generate_sigma_points()
        
        # Transform sigma points to measurement space
        H = np.eye(self.meas_dim, self.state_dim)
        meas_sigma_points = (H @ sigma_points.T).T
        
        # Predicted measurement
        z_pred = np.sum(self.Wm[:, np.newaxis] * meas_sigma_points, axis=0)
        
        # Innovation covariance
        S = self.R[:len(measurement), :len(measurement)].copy()
        for i in range(2 * self.state_dim + 1):
            diff = meas_sigma_points[i, :len(measurement)] - z_pred[:len(measurement)]
            S += self.Wc[i] * np.outer(diff, diff)
        
        # Cross-covariance
        Pxz = np.zeros((self.state_dim, len(measurement)))
        for i in range(2 * self.state_dim + 1):
            diff_x = sigma_points[i] - self.x
            diff_z = meas_sigma_points[i, :len(measurement)] - z_pred[:len(measurement)]
            Pxz += self.Wc[i] * np.outer(diff_x, diff_z)
        
        # Kalman gain
        K = Pxz @ np.linalg.inv(S)
        
        # Update state
        self.x = self.x + K @ (measurement - z_pred[:len(measurement)])
        
        # Update covariance
        self.P = self.P - K @ S @ K.T
    
    def get_state(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get current state estimate and covariance"""
        return self.x.copy(), self.P.copy()


class FusionEngine:
    """
    Multi-sensor fusion engine with outlier rejection.
    Combines EKF/UKF with statistical outlier detection.
    """
    
    def __init__(self, use_ukf: bool = False):
        self.use_ukf = use_ukf
        
        if use_ukf:
            self.filter = UnscentedKalmanFilter()
        else:
            self.filter = ExtendedKalmanFilter()
        
        # Outlier rejection threshold (Mahalanobis distance)
        self.outlier_threshold = 3.0
        
        # Sensor health tracking
        self.sensor_health: Dict[str, float] = {}
        
        logger.info(f"FusionEngine initialized (filter={'UKF' if use_ukf else 'EKF'})")
    
    def fuse_measurements(self, measurements: Dict[str, float], dt: float) -> Dict[str, Any]:
        """
        Fuse multi-sensor measurements.
        
        Args:
            measurements: Dict of sensor measurements
            dt: Time step
        
        Returns:
            Fused state estimate
        """
        # Prediction step
        self.filter.predict(dt)
        
        # Update with each measurement (with outlier rejection)
        for sensor_name, value in measurements.items():
            # For Mahalanobis distance, we need the predicted measurement and its covariance
            # This requires knowing H and R for each measurement, which are currently hardcoded in update
            # Simplified approach for now:

            
            # Update filter
            if sensor_name == 'altitude':
                meas = np.array([value])
                H = np.array([[1, 0, 0, 0, 0]])
            elif sensor_name == 'pressure':
                meas = np.array([value])
                H = np.array([[0, 0, 0, 0, 1]])
            elif sensor_name == 'temperature':
                meas = np.array([value])
                H = np.array([[0, 0, 0, 1, 0]])
            else:
                continue

            # Perform Mahalanobis distance outlier check
            # Predict measurement (z_pred = H @ x)
            z_pred = H @ self.filter.x
            # Innovation covariance (S = H @ P @ H.T + R)
            S = H @ self.filter.P @ H.T + self.filter.R[:len(meas), :len(meas)]
            # Innovation (y = meas - z_pred)
            y = meas - z_pred

            # Mahalanobis distance (d^2 = y.T @ inv(S) @ y)
            try:
                mahalanobis_d_sq = y.T @ np.linalg.inv(S) @ y
                if mahalanobis_d_sq > self.outlier_threshold**2: # Compare to chi-squared threshold
                    logger.warning(f"Outlier rejected by Mahalanobis distance: {sensor_name}={value} (d^2={mahalanobis_d_sq:.2f})")
                    self.sensor_health[sensor_name] = self.sensor_health.get(sensor_name, 1.0) * 0.9 # Degrade health
                    continue # Skip update for this measurement
            except np.linalg.LinAlgError:
                logger.warning(f"Mahalanobis distance calculation failed for {sensor_name}. Skipping outlier check.")

            if self.use_ukf:
                self.filter.update(meas)
            else:
                self.filter.update(meas, H)
            
            # Update sensor health
            self.sensor_health[sensor_name] = min(1.0, self.sensor_health.get(sensor_name, 0.5) + 0.1)
        
        # Get fused state
        state, covariance = self.filter.get_state()
        
        return {
            'altitude': state[0],
            'velocity': state[1],
            'acceleration': state[2],
            'temperature': state[3],
            'pressure': state[4],
            'covariance': covariance,
            'sensor_health': self.sensor_health.copy()
        }
    
if __name__ == "__main__":
    # Test fusion engine
    logging.basicConfig(level=logging.INFO)
    
    # Test EKF
    print("Testing EKF:")
    fusion_ekf = FusionEngine(use_ukf=False)
    
    measurements = {
        'altitude': 1000.0,
        'temperature': 25.0,
        'pressure': 101325.0
    }
    
    result = fusion_ekf.fuse_measurements(measurements, dt=0.1)
    print(f"  Fused altitude: {result['altitude']:.2f} m")
    print(f"  Fused velocity: {result['velocity']:.2f} m/s")
    print(f"  Sensor health: {result['sensor_health']}")
    
    # Test UKF
    print("\nTesting UKF:")
    fusion_ukf = FusionEngine(use_ukf=True)
    result = fusion_ukf.fuse_measurements(measurements, dt=0.1)
    print(f"  Fused altitude: {result['altitude']:.2f} m")
    print(f"  Fused velocity: {result['velocity']:.2f} m/s")


import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class KalmanFuser1D:
    """1D Kalman Sensor Fusion (e.g., GPS + Baro Altitude)"""
    
    def __init__(self, process_noise=1e-4, measurement_noise_a=1.0, measurement_noise_b=2.0):
        # State: [value, rate]
        self.x = np.array([0.0, 0.0]) 
        self.P = np.eye(2) * 100.0
        self.Q = np.eye(2) * process_noise
        self.dt = 0.1
        
        # Measurement variances
        self.R_a = measurement_noise_a # Primary (e.g. Baro)
        self.R_b = measurement_noise_b # Secondary (e.g. GPS)
        
        self.F = np.array([[1.0, self.dt], [0.0, 1.0]])
        self.H = np.array([[1.0, 0.0]]) # Measurement maps to value
        
    def predict(self, dt=None):
        if dt: 
            self.dt = dt
            self.F[0, 1] = dt
            
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x[0]
        
    def update(self, z, R_noise):
        """Update with a measurement z and its variance R_noise"""
        # Check initialization (if x is still 0 and P high, we might jump, 
        # but explicit init is better)
        if self.x[0] == 0.0 and self.x[1] == 0.0 and z != 0.0:
             self.x[0] = z
             
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + R_noise
        K = self.P @ self.H.T * (1/S) # Scalar inverse for 1D measurement
        
        self.x = self.x + K.flatten() * y
        I = np.eye(2)
        self.P = (I - K @ self.H) @ self.P
        return self.x[0]

class AltitudeFuser:
    """Fuses Barometer and GPS altitude"""
    def __init__(self):
        # Baro is smoother (R=2.0), GPS is noisy but undrifting (R=10.0)
        self.kf = KalmanFuser1D(process_noise=0.1, measurement_noise_a=2.0, measurement_noise_b=10.0)
        
    def process(self, baro_alt: float, gps_alt: float, dt: float) -> Tuple[float, float]:
        """Returns (Fused Altitude, Vertical Velocity)"""
        self.kf.predict(dt)
        
        # Sequential update: Baro first
        self.kf.update(baro_alt, self.kf.R_a)

        # GPS update if valid (non-zero or check validity flag in real system)
        if hasattr(gps_alt, 'valid') and not gps_alt.valid:
             # GPS data is marked as invalid, skip update
             self.logger.debug("GPS data invalid, skipping update")
        else:
             self.kf.update(gps_alt, self.kf.R_b)

        return self.kf.x[0], self.kf.x[1]

class AttitudeFuser:
    """Complementary Filter for Attitude (Gyro + Accel)"""
    def __init__(self, alpha=0.98):
        self.alpha = alpha
        self.roll = 0.0
        self.pitch = 0.0
        
    def process(self, accel: Tuple[float, float, float], gyro: Tuple[float, float, float], dt: float) -> Tuple[float, float]:
        ax, ay, az = accel
        gx, gy, gz = gyro
        
        # Pitch/Roll from Accel
        roll_acc = np.degrees(np.arctan2(ay, az))
        pitch_acc = np.degrees(np.arctan2(-ax, np.sqrt(ay**2 + az**2)))
        
        # Integrate Gyro
        self.roll = self.alpha * (self.roll + gx * dt) + (1 - self.alpha) * roll_acc
        self.pitch = self.alpha * (self.pitch + gy * dt) + (1 - self.alpha) * pitch_acc
        
        return self.roll, self.pitch

class HeadingFuser:
    """Tilt-Compensated Compass Fusion (Mag + Gyro + Accel)"""
    def __init__(self, alpha=0.95):
        self.alpha = alpha
        self.heading = 0.0
        
    def process(self, mag: Tuple[float, float, float], roll: float, pitch: float, gyro_z: float, dt: float) -> float:
        mx, my, mz = mag
        
        # Tilt compensation
        # Normalize Mag?
        norm = np.sqrt(mx**2 + my**2 + mz**2)
        if norm > 0:
            mx, my, mz = mx/norm, my/norm, mz/norm
            
        r_rad = np.radians(roll)
        p_rad = np.radians(pitch)
        
        # Tilt compensated mag x, y
        # Xh = mx * np.cos(p_rad) + mz * np.sin(p_rad)
        # Yh = mx * np.sin(r_rad) * np.sin(p_rad) + my * np.cos(r_rad) - mz * np.sin(r_rad) * np.cos(p_rad)
        
        Xh = mx * np.cos(p_rad) + mz * np.sin(p_rad)
        Yh = mx * np.sin(r_rad) * np.sin(p_rad) + my * np.cos(r_rad) - mz * np.sin(r_rad) * np.cos(p_rad)
        
        # Mag Heading
        mag_heading = np.degrees(np.arctan2(-Yh, Xh))
        if mag_heading < 0: mag_heading += 360
        
        # Gyro Integration (Yaw)
        # Note: Gyro drifts, Mag is absolute reference
        self.heading = self.alpha * (self.heading + gyro_z * dt) + (1 - self.alpha) * mag_heading
        self.heading %= 360.0
        
        return self.heading

class PositionFuser:
    """2D Kalman for Position (Lat, Lon)"""
    def __init__(self):
        # State: [Lat, VelN, Lon, VelE]
        self.x = np.zeros(4)
        self.P = np.eye(4) * 100.0
        # Process Noise
        self.Q = np.eye(4) * 1e-5
        # Measure Noise (GPS)
        self.R = np.eye(2) * 5.0 # meters error approx
        
    def update(self, lat, lon, dt):
        # F matrix (Constant Velocity)
        # Convert Lat/Lon to meters for local approximation?
        # 1 deg Lat ~ 111132 m
        # 1 deg Lon ~ 111132 * cos(lat)
        
        if lat == 0.0 and lon == 0.0: return lat, lon # Invalid
        
        deg_to_m_lat = 111132.0
        deg_to_m_lon = 111132.0 * np.cos(np.radians(lat))
        
        # F: x = x + v*dt
        # We work in Degrees for state? Or Meters?
        # Kalman works best in linear cartesian.
        # Let's keep state in Degrees/sec for simplicity or convert?
        # Degrees is easier for direct update, but velocity is usually m/s.
        
        # Hybrid: State [Lat, Vel_N_deg, Lon, Vel_E_deg]
        F = np.eye(4)
        F[0, 1] = dt
        F[2, 3] = dt
        
        # Predict
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
        
        # Update
        z = np.array([lat, lon])
        H = np.array([
            [1, 0, 0, 0],
            [0, 0, 1, 0]
        ])
        
        y = z - H @ self.x
        S = H @ self.P @ self.H.T + self.R # R needs to be in Degree^2 ?
        # 5m error in degrees ~ 5/111000 ~ 4.5e-5
        R_deg = np.eye(2) * (4.5e-5 ** 2)
        
        # Recalculate S with correct R
        S = H @ self.P @ H.T + R_deg
        
        K = self.P @ H.T @ np.linalg.inv(S)
        
        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ H) @ self.P
        
        return self.x[0], self.x[2]

class SensorFusionEngine:
    """Main Fusion Engine"""
    def __init__(self):
        self.alt_fuser = AltitudeFuser()
        self.att_fuser = AttitudeFuser()
        self.head_fuser = HeadingFuser()
        self.pos_fuser = PositionFuser()
        
    def update(self, record) -> 'TelemetryRecord': # Type hint string to avoid circular import if needed
        """Update record with fused values"""
        dt = 0.1 # Fixed step or calc from record.timestamp
        
        # Altitude Fusion
        fused_alt, vert_vel = self.alt_fuser.process(
            record.pressure_alt if hasattr(record, 'pressure_alt') else record.altitude_baro,
            record.altitude_gnss,
            dt
        )
        record.altitude_fused = fused_alt
        record.vertical_velocity = vert_vel
        
        # Attitude Fusion
        r, p = self.att_fuser.process(
            (record.accel_x, record.accel_y, record.accel_z),
            (record.gyro_x, record.gyro_y, record.gyro_z),
            dt
        )
        record.roll = r
        record.pitch = p
        
        # Heading Fusion
        h = self.head_fuser.process(
            (record.mag_x, record.mag_y, record.mag_z),
            r, p,
            record.gyro_z,
            dt
        )
        record.heading = h
        
        # Position Fusion
        lat, lon = self.pos_fuser.update(record.latitude, record.longitude, dt)
        record.latitude_fused = lat
        record.longitude_fused = lon
        
        return record