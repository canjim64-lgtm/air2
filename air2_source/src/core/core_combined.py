"""
AirOne v3 - Core Systems Integration
===================================

This file combines the core functionality of the AirOne v3 system:
- Core system operations and management
- Sensor fusion algorithms
- Simulation engine
"""

import numpy as np
import time
import threading
import queue
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import math
import json

# ###########################################################################
# CORE SYSTEM OPERATIONS (from core.py)
# ###########################################################################

@dataclass
class TelemetryRecord:
    """Standardized telemetry record"""
    timestamp: float = 0.0
    altitude: float = 0.0
    velocity: float = 0.0
    temperature: float = 0.0
    pressure: float = 0.0
    voltage: float = 0.0
    current: float = 0.0
    gps_lat: float = 0.0
    gps_lon: float = 0.0
    gps_alt: float = 0.0
    imu_ax: float = 0.0
    imu_ay: float = 0.0
    imu_az: float = 0.0
    imu_gx: float = 0.0
    imu_gy: float = 0.0
    imu_gz: float = 0.0
    status_flags: int = 0
    checksum: int = 0

class SystemState(Enum):
    """System operational states"""
    IDLE = "idle"
    ARMED = "armed"
    FLIGHT = "flight"
    DESCENT = "descent"
    RECOVERY = "recovery"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class CoreSystem:
    """Main core system controller"""
    
    def __init__(self):
        self.state = SystemState.IDLE
        self.telemetry_buffer = []
        self.max_buffer_size = 10000
        self.system_clock = time.time()
        self.logger = logging.getLogger("CoreSystem")
        
        # System components
        self.sensors_active = False
        self.actuators_active = False
        self.communication_active = False
        
        # Performance metrics
        self.metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'uptime': 0.0,
            'telemetry_rate': 0.0
        }
        
        # Threading
        self.main_thread = None
        self.running = False
        
        self.logger.info("Core system initialized")
    
    def start(self):
        """Start the core system"""
        self.running = True
        self.system_clock = time.time()
        
        # Start main processing thread
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        self.state = SystemState.IDLE
        self.logger.info("Core system started")
    
    def stop(self):
        """Stop the core system"""
        self.running = False
        
        if self.main_thread:
            self.main_thread.join(timeout=2.0)
        
        self.state = SystemState.SHUTDOWN
        self.logger.info("Core system stopped")
    
    def _main_loop(self):
        """Main system processing loop"""
        last_telemetry_time = time.time()
        telemetry_count = 0
        
        while self.running:
            current_time = time.time()
            
            # Process system tasks
            self._process_system_tasks()
            
            # Update metrics
            self._update_metrics()
            
            # Throttle telemetry rate
            if current_time - last_telemetry_time >= 0.1:  # 10Hz
                self._generate_telemetry()
                last_telemetry_time = current_time
                telemetry_count += 1
            
            # Update telemetry rate metric
            if current_time - self.system_clock >= 1.0:
                self.metrics['telemetry_rate'] = telemetry_count
                telemetry_count = 0
                self.system_clock = current_time
            
            time.sleep(0.01)  # 100Hz loop
    
    def _process_system_tasks(self):
        """Process system-level tasks"""
        # Check system health
        self._check_system_health()
        
        # Process commands
        self._process_commands()
        
        # Update state machine
        self._update_state_machine()
    
    def _check_system_health(self):
        """Check system health and status"""
        # Check CPU usage
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 90:
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
            if memory_percent > 90:
                self.logger.warning(f"High memory usage: {memory_percent}%")
                
            self.metrics['cpu_usage'] = cpu_percent
            self.metrics['memory_usage'] = memory_percent
        except ImportError:
            # Fallback without psutil
            self.metrics['cpu_usage'] = 15.0
            self.metrics['memory_usage'] = 30.0
            
        # Check disk usage
        try:
            disk_usage = psutil.disk_usage('/').percent
            self.metrics['disk_usage'] = disk_usage
        except:
            self.metrics['disk_usage'] = 50.0
            
        # Check telemetry buffer health
        buffer_usage = len(self.telemetry_buffer) / self.max_buffer_size
        if buffer_usage > 0.8:
            self.logger.warning(f"Telemetry buffer at {buffer_usage*100:.1f}% capacity")

    def _process_commands(self):
        """Process incoming commands"""
        # Process command queue if available
        if hasattr(self, 'command_queue') and not self.command_queue.empty():
            try:
                command, params = self.command_queue.get_nowait()
                self.logger.info(f"Processing command: {command}")
                self._execute_command(command, params)
            except Exception as e:
                self.logger.error(f"Command processing error: {e}")

    def _execute_command(self, command: str, params: Dict[str, Any]):
        """Execute a specific command"""
        command_handlers = {
            'ARM': self._cmd_arm,
            'DISARM': self._cmd_disarm,
            'START': self._cmd_start,
            'STOP': self._cmd_stop,
            'CALIBRATE': self._cmd_calibrate,
            'RESET': self._cmd_reset
        }
        
        if command in command_handlers:
            command_handlers[command](params)
        else:
            self.logger.warning(f"Unknown command: {command}")

    def _cmd_arm(self, params):
        """Arm system command"""
        if self.state == SystemState.IDLE:
            self.state = SystemState.ARMED
            self.logger.info("System ARMED")

    def _cmd_disarm(self, params):
        """Disarm system command"""
        if self.state == SystemState.ARMED:
            self.state = SystemState.IDLE
            self.logger.info("System DISARMED")

    def _cmd_start(self, params):
        """Start operations command"""
        if self.state == SystemState.ARMED:
            self.state = SystemState.FLIGHT
            self.logger.info("Operations STARTED")

    def _cmd_stop(self, params):
        """Stop operations command"""
        self.state = SystemState.IDLE
        self.logger.info("Operations STOPPED")

    def _cmd_calibrate(self, params):
        """Calibrate sensors command"""
        self.logger.info("Calibrating sensors...")
        time.sleep(0.5)  # Simulate calibration
        self.logger.info("Calibration complete")

    def _cmd_reset(self, params):
        """Reset system command"""
        self.state = SystemState.IDLE
        self.telemetry_buffer.clear()
        self.logger.info("System RESET")

    def _update_state_machine(self):
        """Update system state machine"""
        # State transition logic based on telemetry
        if self.telemetry_buffer:
            latest = self.telemetry_buffer[-1]
            
            # Auto-transition based on altitude
            if self.state == SystemState.ARMED and latest.altitude > 10:
                self.state = SystemState.FLIGHT
                self.logger.info("Auto-transition to FLIGHT (altitude > 10m)")
                
            elif self.state == SystemState.FLIGHT and latest.velocity < 0 and latest.altitude > 50:
                # Check if descending from high altitude
                prev = self.telemetry_buffer[-2] if len(self.telemetry_buffer) > 1 else latest
                if prev.velocity >= 0:
                    self.logger.info("Apogee detected - transitioning to DESCENT")
                    
            elif self.state == SystemState.FLIGHT and latest.altitude < 5:
                self.state = SystemState.RECOVERY
                self.logger.info("Auto-transition to RECOVERY (landing detected)")

    def _generate_telemetry(self):
        """Generate simulated telemetry data and add to buffer."""
        # Simulate sensor readings
        altitude = self._simulate_altitude()
        velocity = self._simulate_velocity()
        temperature = self._simulate_temperature()
        pressure = self._simulate_pressure()
        voltage = self._simulate_voltage()
        current = self._simulate_current() # Assuming a _simulate_current method will be added

        # Create a TelemetryRecord
        record = TelemetryRecord(
            timestamp=time.time(),
            altitude=altitude,
            velocity=velocity,
            temperature=temperature,
            pressure=pressure,
            voltage=voltage,
            current=current,
            # Placeholder for other sensor data, will be updated by fusion
            gps_lat=0.0, gps_lon=0.0, gps_alt=0.0,
            imu_ax=0.0, imu_ay=0.0, imu_az=0.0,
            imu_gx=0.0, imu_gy=0.0, imu_gz=0.0,
            status_flags=0,
            checksum=0
        )
        
        # Add to buffer
        self.telemetry_buffer.append(record)
        
        # Limit buffer size
        if len(self.telemetry_buffer) > self.max_buffer_size:
            self.telemetry_buffer.pop(0)

    def _simulate_altitude(self) -> float:
        """Simulate altitude data using realistic flight profile"""
        elapsed = time.time() - self.system_clock if self.system_clock > 0 else 0
        
        # Simulate typical rocket flight profile
        if elapsed < 3:
            # Pre-launch
            return 100.0
        elif elapsed < 6:
            # Powered ascent (0-3s after launch)
            return 100.0 + 50 * (elapsed - 3)**2
        elif elapsed < 15:
            # Coasting ascent
            return 550.0 + 30 * (elapsed - 6) - 2 * (elapsed - 6)**2
        elif elapsed < 25:
            # Descent with parachute
            return max(100.0, 600.0 - 40 * (elapsed - 15))
        else:
            # Landed
            return 100.0

    def _simulate_velocity(self) -> float:
        """Simulate velocity data"""
        elapsed = time.time() - self.system_clock if self.system_clock > 0 else 0
        
        if elapsed < 3:
            return 0.0  # Pre-launch
        elif elapsed < 6:
            return 50 * (elapsed - 3)  # Powered ascent
        elif elapsed < 10:
            return 150 - 15 * (elapsed - 6)  # Coasting
        elif elapsed < 25:
            return -5.0  # Descent with parachute
        else:
            return 0.0  # Landed

    def _simulate_temperature(self) -> float:
        """Simulate temperature data with altitude variation"""
        altitude = self._simulate_altitude()
        base_temp = 25.0
        
        # Temperature decreases with altitude (lapse rate ~6.5°C per km)
        temp_at_altitude = base_temp - (altitude - 100) * 0.0065
        
        # Add small variations
        variation = math.sin(time.time() * 0.1) * 2
        
        return max(-20, min(40, temp_at_altitude + variation))

    def _simulate_pressure(self) -> float:
        """Simulate pressure data using barometric formula"""
        altitude = self._simulate_altitude()
        
        # Barometric formula: P = P0 * (1 - L*h/T0)^(g*M/(R*L))
        P0 = 101325.0  # Sea level pressure (Pa)
        L = 0.0065     # Temperature lapse rate (K/m)
        T0 = 288.15    # Sea level temperature (K)
        g = 9.80665    # Gravity (m/s²)
        M = 0.0289644  # Molar mass of air (kg/mol)
        R = 8.31447    # Universal gas constant (J/(mol·K))
        
        exponent = (g * M) / (R * L)
        pressure = P0 * (1 - L * (altitude - 100) / T0) ** exponent
        
        return pressure  # Return in Pascals

    def _simulate_voltage(self) -> float:
        """Simulate battery voltage with load variation"""
        elapsed = time.time() - self.system_clock if self.system_clock > 0 else 0
        
        # Start at 12.6V (fully charged LiPo)
        base_voltage = 12.6
        
        # Discharge over time (simulate 30 minute flight)
        discharge = min(0.8, elapsed / 1800)  # Max 0.8V drop
        
        # Add load variation during high-power events
        if 3 < elapsed < 6:  # During motor burn
            load_drop = 0.3
        elif 15 < elapsed < 20:  # During parachute deployment
            load_drop = 0.1
        else:
            load_drop = 0.05
            
        return base_voltage - discharge - load_drop

    def _simulate_current(self) -> float:
        """Simulate current draw based on flight phase."""
        elapsed = time.time() - self.system_clock if self.system_clock > 0 else 0
        
        if elapsed < 3: # Pre-launch
            return 0.1 # Idle current
        elif elapsed < 6: # Powered ascent
            return 5.0 + random.uniform(0.5, 1.0) # High current draw
        elif elapsed < 15: # Coasting ascent
            return 0.5 + random.uniform(0.1, 0.2) # Moderate current
        elif elapsed < 25: # Descent with parachute
            return 0.3 + random.uniform(0.05, 0.1) # Low current
        else: # Landed
            return 0.1 + random.uniform(0.01, 0.05) # Very low idle current

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and metrics."""
        return {
            'state': self.state.value,
            'running': self.running,
            'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0.0,
            'telemetry_buffer_size': len(self.telemetry_buffer),
            'metrics': self.metrics
        }
    
    def get_telemetry(self, count: int = 1) -> List[TelemetryRecord]:
        """Get the last 'count' telemetry records from the buffer."""
        return list(self.telemetry_buffer)[-count:]

# ###########################################################################
# SENSOR FUSION ALGORITHMS (from fusion.py)
# ###########################################################################

class SensorFusionCore:
    """Core sensor fusion algorithms"""
    
    def __init__(self):
        self.logger = logging.getLogger("SensorFusion")
        
        # State variables
        self.position = np.array([0.0, 0.0, 0.0])  # x, y, z
        self.velocity = np.array([0.0, 0.0, 0.0])  # vx, vy, vz
        self.acceleration = np.array([0.0, 0.0, 0.0])  # ax, ay, az
        self.orientation = np.array([0.0, 0.0, 0.0, 1.0])  # qx, qy, qz, qw (quaternion)
        
        # Covariance matrices
        self.state_covariance = np.eye(13) * 0.1  # [pos, vel, acc, orient]
        
        # Process noise
        self.process_noise = np.eye(13) * 0.01
        
        # Sensor biases
        self.gyro_bias = np.array([0.0, 0.0, 0.0])
        self.accel_bias = np.array([0.0, 0.0, 0.0])
        
        # Timing
        self.last_update_time = time.time()
        
        self.logger.info("Sensor fusion core initialized")
    
    def initialize_state(self, initial_position, initial_velocity, initial_orientation):
        """Initialize state with known values"""
        self.position = np.array(initial_position)
        self.velocity = np.array(initial_velocity)
        self.orientation = np.array(initial_orientation)
        
        # Reset covariance
        self.state_covariance = np.eye(13) * 0.001
    
    def predict(self, dt: float):
        """Prediction step of the filter"""
        # Update state based on motion model
        # Position update: x_new = x_old + v*dt + 0.5*a*dt^2
        self.position = self.position + self.velocity * dt + 0.5 * self.acceleration * dt**2
        
        # Velocity update: v_new = v_old + a*dt
        self.velocity = self.velocity + self.acceleration * dt
        
        # For orientation, we would integrate angular velocities
        # This is a simplified approach
        # In practice, you'd use quaternion integration
        
        # Update covariance
        F = self._compute_state_transition_matrix(dt)
        self.state_covariance = F @ self.state_covariance @ F.T + self.process_noise * dt
    
    def update_imu(self, accel_data: np.ndarray, gyro_data: np.ndarray, dt: float):
        """Update state with IMU measurements"""
        # Correct for biases
        corrected_accel = accel_data - self.accel_bias
        corrected_gyro = gyro_data - self.gyro_bias
        
        # Update acceleration estimate
        # Transform accelerometer data to inertial frame if needed
        self.acceleration = corrected_accel
        
        # Update orientation using gyroscope data
        self._integrate_gyro(corrected_gyro, dt)
        
        # Compute Jacobian for measurement model
        H = self._compute_imu_measurement_matrix()
        
        # Measurement noise for IMU
        R = np.diag([0.01, 0.01, 0.01, 0.001, 0.001, 0.001])  # [acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z]
        
        # Innovation
        z_pred = self._predict_imu_measurement()
        innovation = np.concatenate([corrected_accel, corrected_gyro]) - z_pred
        
        # Innovation covariance
        S = H @ self.state_covariance @ H.T + R
        
        # Kalman gain
        K = self.state_covariance @ H.T @ np.linalg.inv(S)
        
        # Update state
        state_update = K @ innovation
        self._apply_state_update(state_update)
        
        # Update covariance
        I_KH = np.eye(13) - K @ H
        self.state_covariance = I_KH @ self.state_covariance @ I_KH.T + K @ R @ K.T
    
    def update_gps(self, gps_position: np.ndarray, gps_velocity: np.ndarray):
        """Update state with GPS measurements"""
        # Measurement vector: [pos_x, pos_y, pos_z, vel_x, vel_y, vel_z]
        z = np.concatenate([gps_position, gps_velocity])
        
        # Measurement matrix: extracts position and velocity from state
        H = np.zeros((6, 13))
        H[0:3, 0:3] = np.eye(3)  # Position mapping
        H[3:6, 3:6] = np.eye(3)  # Velocity mapping
        
        # Measurement noise for GPS
        R = np.diag([2.0, 2.0, 4.0, 0.5, 0.5, 0.5])  # [pos_std, vel_std]
        
        # Innovation
        x_state = np.concatenate([self.position, self.velocity, self.acceleration, self.orientation])
        z_pred = H @ x_state
        innovation = z - z_pred
        
        # Innovation covariance
        S = H @ self.state_covariance @ H.T + R
        
        # Kalman gain
        K = self.state_covariance @ H.T @ np.linalg.inv(S)
        
        # Update state
        state_update = K @ innovation
        self._apply_state_update(state_update)
        
        # Update covariance
        I_KH = np.eye(13) - K @ H
        self.state_covariance = I_KH @ self.state_covariance @ I_KH.T + K @ R @ K.T
    
    def update_barometer(self, pressure: float):
        """Update state with barometric pressure measurement"""
        # Convert pressure to altitude
        # Simplified conversion: altitude ≈ (1 - (P/P0)^(1/5.255)) * 44330
        P0 = 101325.0  # Standard pressure at sea level (Pa)
        altitude = (1 - pow(pressure / P0, 1/5.255)) * 44330.0
        
        # Measurement matrix for altitude (maps to z-component of position)
        H = np.zeros((1, 13))
        H[0, 2] = 1.0  # Map to z position
        
        # Predicted measurement
        z_pred = self.position[2]
        
        # Innovation
        innovation = altitude - z_pred
        
        # Measurement noise
        R = np.array([[1.0]])  # 1m standard deviation
        
        # Innovation covariance
        S = H @ self.state_covariance @ H.T + R
        
        # Kalman gain
        K = self.state_covariance @ H.T @ np.linalg.inv(S)
        
        # Update state
        state_update = K.flatten() * innovation
        self._apply_state_update(state_update)
        
        # Update covariance
        I_KH = np.eye(13) - K @ H
        self.state_covariance = I_KH @ self.state_covariance @ I_KH.T + K @ R @ K.T
    
    def _compute_state_transition_matrix(self, dt: float) -> np.ndarray:
        """Compute state transition matrix for prediction"""
        F = np.eye(13)
        
        # Position from velocity: r_new = r_old + v*dt
        F[0:3, 3:6] = np.eye(3) * dt
        
        # Velocity from acceleration: v_new = v_old + a*dt
        F[3:6, 6:9] = np.eye(3) * dt
        
        # For simplicity, we're not modeling orientation dynamics here
        # In a real implementation, you'd include quaternion kinematics
        
        return F
    
    def _integrate_gyro(self, gyro_data: np.ndarray, dt: float):
        """Integrate gyroscope data to update orientation"""
        # Convert angular velocity to quaternion derivative
        omega_norm = np.linalg.norm(gyro_data)
        
        if omega_norm > 1e-6:  # Avoid division by zero
            # Quaternion derivative: dq/dt = 0.5 * omega_quat * q
            half_dt = 0.5 * dt
            omega_quat = np.array([gyro_data[0]*half_dt, gyro_data[1]*half_dt, gyro_data[2]*half_dt, 0])
            
            # Integrate: q_new = q_old + dq/dt * dt
            dq = self._quat_multiply(omega_quat, self.orientation)
            self.orientation = self.orientation + dq
            
            # Normalize quaternion
            self.orientation = self.orientation / np.linalg.norm(self.orientation)
    
    def _quat_multiply(self, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """Multiply two quaternions"""
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        
        w = w1*w2 - x1*x2 - y1*y2 - z1*z2
        x = w1*x2 + x1*w2 + y1*z2 - z1*y2
        y = w1*y2 - x1*z2 + y1*w2 + z1*x2
        z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        
        return np.array([w, x, y, z])
    
    def _compute_imu_measurement_matrix(self) -> np.ndarray:
        """Compute measurement matrix for IMU"""
        # This is a simplified version
        # In reality, the relationship between state and IMU measurements is nonlinear
        H = np.zeros((6, 13))
        # Map acceleration and angular velocity appropriately
        # This assumes direct measurement of acceleration and gyro
        return H
    
    def _predict_imu_measurement(self) -> np.ndarray:
        """Predict IMU measurement from current state"""
        # Transform acceleration from world frame to body frame
        # Simplified transformation assuming small angles
        accel_body = self.acceleration.copy()
        
        # Add gravity component (assuming z-axis points down)
        accel_body[2] += 9.80665
        
        # Gyro prediction (angular rates) - simplified
        gyro_body = np.array([0.0, 0.0, 0.0])
        
        return np.concatenate([accel_body, gyro_body])

    def _apply_state_update(self, state_update: np.ndarray):
        """Apply state update vector to state variables"""
        # Update position
        self.position = self.position + state_update[0:3]

        # Update velocity
        self.velocity = self.velocity + state_update[3:6]

        # Update acceleration
        self.acceleration = self.acceleration + state_update[6:9]

        # Update orientation (with normalization)
        self.orientation = self.orientation + state_update[9:13]
        norm = np.linalg.norm(self.orientation)
        if norm > 0:
            self.orientation = self.orientation / norm

    def get_fused_state(self) -> Dict[str, np.ndarray]:
        """Get the current fused state"""
        return {
            'position': self.position.copy(),
            'velocity': self.velocity.copy(),
            'acceleration': self.acceleration.copy(),
            'orientation': self.orientation.copy(),
            'timestamp': time.time()
        }

class ExtendedKalmanFilter:
    """Extended Kalman Filter for nonlinear systems"""
    
    def __init__(self, state_dim: int, measurement_dim: int):
        self.state_dim = state_dim
        self.measurement_dim = measurement_dim
        
        # Initialize state and covariance
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim) * 1.0
        
        # Process and measurement noise
        self.Q = np.eye(state_dim) * 0.1
        self.R = np.eye(measurement_dim) * 1.0
        
        self.logger = logging.getLogger("ExtendedKalmanFilter")
    
    def predict(self, F_func, dt: float):
        """Prediction step with nonlinear state transition"""
        # Get state transition Jacobian
        F = F_func(self.x, dt)
        
        # Predict state
        self.x = self._state_transition(self.x, dt)
        
        # Predict covariance
        self.P = F @ self.P @ F.T + self.Q * dt
    
    def update(self, measurement: np.ndarray, H_func):
        """Update step with nonlinear measurement model"""
        # Get measurement Jacobian
        H = H_func(self.x)
        
        # Predict measurement
        z_pred = self._measurement_model(self.x)
        
        # Innovation
        y = measurement - z_pred
        
        # Innovation covariance
        S = H @ self.P @ H.T + self.R
        
        # Kalman gain
        K = self.P @ H.T @ np.linalg.inv(S)
        
        # Update state
        self.x = self.x + K @ y
        
        # Update covariance
        I_KH = np.eye(self.state_dim) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R @ K.T
    
    def _state_transition(self, x: np.ndarray, dt: float) -> np.ndarray:
        """Nonlinear state transition function for position, velocity, and acceleration under gravity."""
        # State vector x: [pos_x, pos_y, pos_z, vel_x, vel_y, vel_z, acc_x, acc_y, acc_z, orient_x, orient_y, orient_z, orient_w]
        x_new = x.copy()
        
        # Position update: p_new = p_old + v*dt + 0.5*a*dt^2
        x_new[0:3] = x[0:3] + x[3:6] * dt + 0.5 * x[6:9] * dt**2
        
        # Velocity update: v_new = v_old + a*dt (including gravity in z-component)
        # Assuming acc_z includes measured acceleration and gravity affects vel_z
        gravity_accel = np.array([0.0, 0.0, -9.80665]) # Constant gravity
        x_new[3:6] = x[3:6] + (x[6:9] + gravity_accel) * dt
        
        # Acceleration model: typically assumed constant or slowly changing
        # For a simple model, acceleration is just propagated forward or set by external inputs
        
        # Orientation update: (simplified, assuming angular velocities are zero in this step)
        
        return x_new

    def _measurement_model(self, x: np.ndarray) -> np.ndarray:
        """Nonlinear measurement model function to predict sensor readings from state."""
        # Predict measurements from the state vector x
        # Assuming measurements can be position (x, y, z) and velocity (vx, vy, vz) from GPS
        # or just position (z) from barometer
        
        # Example: Predict position and velocity measurements
        predicted_position = x[0:3]
        predicted_velocity = x[3:6]
        
        # Concatenate expected measurements based on self.measurement_dim
        if self.measurement_dim == 3: # e.g., for barometer (altitude/pos_z)
            return np.array([predicted_position[2]])
        elif self.measurement_dim == 6: # e.g., for GPS (pos_x,y,z, vel_x,y,z)
            return np.concatenate([predicted_position, predicted_velocity])
        # Add more cases for IMU, etc.
        
        return np.zeros(self.measurement_dim) # Fallback


# ###########################################################################
# SIMULATION ENGINE (from simulation.py)
# ###########################################################################

class SimulationEngine:
    """Advanced simulation engine for CanSat operations"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger("SimulationEngine")
        
        # Simulation state
        self.running = False
        self.paused = False
        self.current_time = 0.0
        self.start_time = 0.0
        self.simulation_speed = 1.0  # 1.0 = real-time, >1 = faster, <1 = slower
        
        # Physical parameters
        self.mass = self.config.get('mass', 1.0)  # kg
        self.drag_coefficient = self.config.get('drag_coefficient', 0.75)
        self.cross_sectional_area = self.config.get('cross_sectional_area', 0.01)  # m^2
        self.gravity = self.config.get('gravity', 9.81)  # m/s^2
        self.air_density_sea_level = 1.225  # kg/m^3
        
        # Initial conditions
        self.position = np.array(self.config.get('initial_position', [0.0, 0.0, 0.0]))  # [x, y, z] in meters
        self.velocity = np.array(self.config.get('initial_velocity', [0.0, 0.0, 0.0]))  # [vx, vy, vz] in m/s
        self.acceleration = np.array([0.0, 0.0, 0.0])
        
        # Environmental parameters
        self.wind_speed = np.array(self.config.get('wind_speed', [0.0, 0.0, 0.0]))  # [wx, wy, wz] in m/s
        self.wind_turbulence = self.config.get('wind_turbulence', 0.1)
        
        # Sensors simulation
        self.ground_truth = {
            'position': self.position.copy(),
            'velocity': self.velocity.copy(),
            'acceleration': self.acceleration.copy(),
            'timestamp': self.current_time
        }
        
        # Threading
        self.simulation_thread = None
        self.telemetry_queue = queue.Queue()
        
        # Callbacks
        self.telemetry_callback = None
        
        self.logger.info("Simulation engine initialized")
    
    def start(self):
        """Start the simulation"""
        if self.running:
            self.logger.warning("Simulation already running")
            return False
        
        self.running = True
        self.paused = False
        self.start_time = time.time()
        self.current_time = 0.0
        
        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
        
        self.logger.info("Simulation started")
        return True
    
    def stop(self):
        """Stop the simulation"""
        self.running = False
        
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2.0)
        
        self.logger.info("Simulation stopped")
    
    def pause(self):
        """Pause the simulation"""
        self.paused = True
        self.logger.info("Simulation paused")
    
    def resume(self):
        """Resume the simulation"""
        self.paused = False
        self.logger.info("Simulation resumed")
    
    def reset(self):
        """Reset simulation to initial conditions"""
        self.current_time = 0.0
        self.position = np.array(self.config.get('initial_position', [0.0, 0.0, 0.0]))
        self.velocity = np.array(self.config.get('initial_velocity', [0.0, 0.0, 0.0]))
        self.acceleration = np.array([0.0, 0.0, 0.0])
        
        self.logger.info("Simulation reset to initial conditions")
    
    def set_initial_conditions(self, position, velocity):
        """Set new initial conditions"""
        self.position = np.array(position)
        self.velocity = np.array(velocity)
        self.acceleration = np.array([0.0, 0.0, 0.0])
        
        self.logger.info(f"Initial conditions set: pos={position}, vel={velocity}")
    
    def _simulation_loop(self):
        """Main simulation loop"""
        last_update_time = time.time()
        
        while self.running:
            current_real_time = time.time()
            dt_real = current_real_time - last_update_time
            
            if not self.paused:
                # Calculate simulation time step
                dt_sim = dt_real * self.simulation_speed
                
                # Update simulation
                self._update_physics(dt_sim)
                self._update_sensors()
                
                # Update simulation time
                self.current_time += dt_sim
            
            # Control loop rate
            time.sleep(0.01)  # ~100Hz
            last_update_time = current_real_time
    
    def _update_physics(self, dt: float):
        """Update physics simulation"""
        # Calculate forces
        gravity_force = np.array([0.0, 0.0, -self.mass * self.gravity])
        
        # Calculate air density at current altitude (simplified model)
        altitude = self.position[2]  # Assuming z is altitude
        air_density = self._calculate_air_density(altitude)
        
        # Calculate drag force: F_drag = 0.5 * rho * v^2 * Cd * A
        relative_velocity = self.velocity - self.wind_speed
        speed = np.linalg.norm(relative_velocity)
        
        if speed > 0:
            drag_magnitude = 0.5 * air_density * speed**2 * self.drag_coefficient * self.cross_sectional_area
            drag_direction = -relative_velocity / speed  # Opposite to velocity direction
            drag_force = drag_direction * drag_magnitude
        else:
            drag_force = np.array([0.0, 0.0, 0.0])
        
        # Total force
        total_force = gravity_force + drag_force
        
        # Update acceleration (F = ma => a = F/m)
        self.acceleration = total_force / self.mass
        
        # Update velocity and position using kinematic equations
        self.velocity = self.velocity + self.acceleration * dt
        
        # Add wind effects with some turbulence
        wind_effect = self.wind_speed + np.random.normal(0, self.wind_turbulence, 3) * dt
        self.position = self.position + (self.velocity + wind_effect) * dt
    
    def _calculate_air_density(self, altitude: float) -> float:
        """Calculate air density at given altitude"""
        # Simplified barometric formula
        if altitude > 11000:  # Above troposphere
            # Use different formula for higher altitudes
            return max(0.0, self.air_density_sea_level * math.exp(-altitude / 7000.0))
        else:
            # Standard atmosphere model
            temperature = 288.15 - 0.0065 * altitude  # K
            pressure = 101325 * math.pow(1 - 0.0065 * altitude / 288.15, 5.255)
            return pressure / (287.05 * temperature)  # Ideal gas law
    
    def _update_sensors(self):
        """Simulate sensor readings with noise"""
        # Add realistic sensor noise
        pos_noise = np.random.normal(0, 0.1, 3)  # 0.1m std dev for position
        vel_noise = np.random.normal(0, 0.05, 3)  # 0.05m/s std dev for velocity
        acc_noise = np.random.normal(0, 0.01, 3)  # 0.01m/s^2 std dev for acceleration
        
        # Simulate sensor readings
        noisy_position = self.position + pos_noise
        noisy_velocity = self.velocity + vel_noise
        noisy_acceleration = self.acceleration + acc_noise
        
        # Simulate IMU readings
        imu_acc = noisy_acceleration + np.array([0, 0, self.gravity])  # Include gravity
        imu_gyro = self._estimate_angular_velocity()
        
        # Simulate GPS readings (every 10th update to simulate 10Hz GPS)
        if int(self.current_time * 10) % 1 == 0:
            gps_position = noisy_position
            gps_velocity = noisy_velocity
        else:
            gps_position = None
            gps_velocity = None
        
        # Simulate barometer reading
        baro_pressure = self._altitude_to_pressure(noisy_position[2])
        
        # Create telemetry record
        telemetry = {
            'timestamp': self.current_time,
            'ground_truth': {
                'position': self.position.copy(),
                'velocity': self.velocity.copy(),
                'acceleration': self.acceleration.copy()
            },
            'sensors': {
                'imu': {
                    'acceleration': imu_acc,
                    'gyro': imu_gyro
                },
                'gps': {
                    'position': gps_position,
                    'velocity': gps_velocity
                },
                'barometer': {
                    'pressure': baro_pressure,
                    'altitude': noisy_position[2]
                },
                'position': noisy_position,
                'velocity': noisy_velocity
            }
        }
        
        # Add to queue and call callback if set
        try:
            self.telemetry_queue.put_nowait(telemetry)
        except queue.Full:
            # Drop telemetry if queue is full
            self.logger.debug("Telemetry queue full, dropping packet")

        if self.telemetry_callback:
            try:
                self.telemetry_callback(telemetry)
            except Exception as e:
                self.logger.error(f"Telemetry callback error: {e}")
    
    def _estimate_angular_velocity(self) -> np.ndarray:
        """Estimate angular velocity (simplified)"""
        # In a real simulation, this would come from attitude dynamics
        # For now, return small random values
        return np.random.normal(0, 0.01, 3)
    
    def _altitude_to_pressure(self, altitude: float) -> float:
        """Convert altitude to barometric pressure"""
        # Simplified conversion based on barometric formula
        P0 = 101325.0  # Standard pressure at sea level (Pa)
        return P0 * math.pow(1 - (0.0065 * altitude) / 288.15, 5.255)
    
    def get_latest_telemetry(self) -> Optional[Dict]:
        """Get the latest telemetry from the queue"""
        try:
            # Get the most recent telemetry (clear older ones)
            latest = None
            while not self.telemetry_queue.empty():
                latest = self.telemetry_queue.get_nowait()
            return latest
        except queue.Empty:
            return None
    
    def set_telemetry_callback(self, callback):
        """Set callback for telemetry updates"""
        self.telemetry_callback = callback
    
    def get_simulation_state(self) -> Dict[str, Any]:
        """Get current simulation state"""
        return {
            'running': self.running,
            'paused': self.paused,
            'current_time': self.current_time,
            'simulation_speed': self.simulation_speed,
            'position': self.position.tolist(),
            'velocity': self.velocity.tolist(),
            'acceleration': self.acceleration.tolist(),
            'queue_size': self.telemetry_queue.qsize()
        }

# ###########################################################################
# MAIN EXECUTION BLOCK
# ###########################################################################

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚀 Launching AirOne v3 Core Systems Integration Test Suite 🚀")
    
    # Test Core System
    print("\n--- Testing Core System ---")
    core_sys = CoreSystem()
    core_sys.start()
    
    time.sleep(1)  # Let it run briefly
    
    status = core_sys.get_system_status()
    print(f"Core System Status: {status['state']}")
    print(f"Telemetry Buffer Size: {status['telemetry_buffer_size']}")
    
    telemetry = core_sys.get_telemetry(5)
    print(f"Retrieved {len(telemetry)} telemetry records")
    
    core_sys.stop()
    
    # Test Sensor Fusion
    print("\n--- Testing Sensor Fusion ---")
    fusion_core = SensorFusionCore()
    
    # Initialize with some values
    fusion_core.initialize_state(
        initial_position=[0, 0, 0],
        initial_velocity=[0, 0, 0],
        initial_orientation=[0, 0, 0, 1]
    )
    
    # Simulate some IMU data
    accel_data = np.array([0.1, 0.05, 9.75])  # Slightly off from gravity
    gyro_data = np.array([0.01, -0.02, 0.005])
    
    dt = 0.01  # 100Hz
    fusion_core.update_imu(accel_data, gyro_data, dt)
    
    state = fusion_core.get_fused_state()
    print(f"Fused Position: {state['position']}")
    print(f"Fused Velocity: {state['velocity']}")
    print(f"Fused Orientation: {state['orientation']}")
    
    # Test Simulation Engine
    print("\n--- Testing Simulation Engine ---")
    sim_config = {
        'initial_position': [0, 0, 100],  # Start at 100m altitude
        'initial_velocity': [10, 0, 0],   # Moving horizontally at 10m/s
        'mass': 1.5,
        'drag_coefficient': 0.8
    }
    
    sim_engine = SimulationEngine(sim_config)
    sim_engine.start()
    
    time.sleep(2)  # Run simulation for 2 seconds
    
    sim_state = sim_engine.get_simulation_state()
    print(f"Simulation Position: {sim_state['position']}")
    print(f"Simulation Velocity: {sim_state['velocity']}")
    print(f"Current Time: {sim_state['current_time']:.2f}s")
    
    latest_telemetry = sim_engine.get_latest_telemetry()
    if latest_telemetry:
        print(f"Latest altitude: {latest_telemetry['sensors']['barometer']['altitude']:.2f}m")
    
    sim_engine.stop()
    
    print("\n✅ Core Systems Integration test suite finished.")