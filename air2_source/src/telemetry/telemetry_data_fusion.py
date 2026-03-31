"""
Telemetry Data Fusion Module
Multi-source telemetry integration and fusion for AirOne
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import queue
import time
import logging
from collections import deque


class DataSource(Enum):
    """Telemetry data sources"""
    PRIMARY_RADIO = "primary_radio"
    SECONDARY_RADIO = "secondary_radio"
    GPS = "gps"
    BAROMETER = "barometer"
    IMU = "imu"
    TEMPERATURE_SENSOR = "temperature"
    PRESSURE_SENSOR = "pressure"
    BATTERY_MONITOR = "battery"


class SensorStatus(Enum):
    """Sensor status"""
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNCALIBRATED = "uncalibrated"


@dataclass
class SensorReading:
    """Individual sensor reading"""
    source: DataSource
    value: float
    timestamp: float
    status: SensorStatus = SensorStatus.NOMINAL
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FusedTelemetry:
    """Fused telemetry result"""
    timestamp: float
    position: Optional[Tuple[float, float, float]] = None  # lat, lon, alt
    velocity: Optional[Tuple[float, float, float]] = None  # vx, vy, vz
    acceleration: Optional[Tuple[float, float, float]] = None
    attitude: Optional[Tuple[float, float, float]] = None  # roll, pitch, yaw
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    humidity: Optional[float] = None
    battery: Optional[float] = None
    data_quality: float = 1.0
    sources_used: List[DataSource] = field(default_factory=list)


class SensorModel:
    """Model for individual sensor characteristics"""
    
    def __init__(self, source: DataSource, 
                 noise_std: float = 0.1,
                 bias: float = 0.0,
                 drift_rate: float = 0.0):
        self.source = source
        self.noise_std = noise_std
        self.bias = bias
        self.drift_rate = drift_rate
        self.last_calibration = datetime.now()
        self.calibration_count = 0
        
    def add_noise(self, true_value: float) -> float:
        """Add sensor noise to true value"""
        noise = np.random.normal(0, self.noise_std)
        return true_value + self.bias + noise
    
    def calibrate(self, reference_value: float, measured_value: float):
        """Calibrate sensor based on reference"""
        self.bias = measured_value - reference_value
        self.last_calibration = datetime.now()
        self.calibration_count += 1


class TelemetryFusionEngine:
    """Multi-sensor telemetry fusion engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FusionEngine")
        
        # Sensor models
        self.sensors: Dict[DataSource, SensorModel] = {}
        self._init_sensor_models()
        
        # Data buffers
        self.buffers: Dict[DataSource, deque] = {
            source: deque(maxlen=100) for source in DataSource
        }
        
        # Fusion state
        self.last_fused: Optional[FusedTelemetry] = None
        self.fusion_history: deque = deque(maxlen=1000)
        
        # Configuration
        self.max_source_age = 5.0  # seconds
        self.min_sources = 2
        
        self.logger.info("Telemetry Fusion Engine initialized")
    
    def _init_sensor_models(self):
        """Initialize sensor models"""
        self.sensors[DataSource.PRIMARY_RADIO] = SensorModel(
            DataSource.PRIMARY_RADIO, noise_std=0.5
        )
        self.sensors[DataSource.GPS] = SensorModel(
            DataSource.GPS, noise_std=1.0
        )
        self.sensors[DataSource.BAROMETER] = SensorModel(
            DataSource.BAROMETER, noise_std=0.01
        )
        self.sensors[DataSource.IMU] = SensorModel(
            DataSource.IMU, noise_std=0.05
        )
        self.sensors[DataSource.TEMPERATURE_SENSOR] = SensorModel(
            DataSource.TEMPERATURE_SENSOR, noise_std=0.5
        )
        self.sensors[DataSource.BATTERY_MONITOR] = SensorModel(
            DataSource.BATTERY_MONITOR, noise_std=0.1
        )
    
    def add_reading(self, source: DataSource, value: float, 
                    timestamp: Optional[float] = None,
                    metadata: Optional[Dict] = None):
        """Add sensor reading"""
        if timestamp is None:
            timestamp = time.time()
        
        # Apply sensor model
        if source in self.sensors:
            value = self.sensors[source].add_noise(value)
        
        reading = SensorReading(
            source=source,
            value=value,
            timestamp=timestamp,
            metadata=metadata or {}
        )
        
        self.buffers[source].append(reading)
    
    def fuse(self) -> Optional[FusedTelemetry]:
        """Fuse current sensor readings"""
        current_time = time.time()
        
        # Collect recent readings
        recent_readings: Dict[DataSource, SensorReading] = {}
        
        for source, buffer in self.buffers.items():
            if not buffer:
                continue
                
            # Get most recent reading
            latest = buffer[-1]
            
            # Check age
            age = current_time - latest.timestamp
            if age < self.max_source_age:
                recent_readings[source] = latest
        
        if len(recent_readings) < self.min_sources:
            return None
        
        # Start fusion
        fused = FusedTelemetry(timestamp=current_time)
        sources_used = []
        
        # Fuse position
        if DataSource.GPS in recent_readings:
            gps = recent_readings[DataSource.GPS]
            # In real system, would extract lat/lon from GPS data
            fused.position = (34.0, -118.0, 1000.0)
            sources_used.append(DataSource.GPS)
        
        # Fuse altitude from barometer
        if DataSource.BAROMETER in recent_readings:
            baro = recent_readings[DataSource.BAROMETER]
            # Convert pressure to altitude (simplified)
            altitude = 44330 * (1 - (baro.value / 101325)**0.1903)
            if fused.position:
                fused.position = (fused.position[0], fused.position[1], altitude)
            else:
                fused.position = (0, 0, altitude)
            sources_used.append(DataSource.BAROMETER)
        
        # Fuse velocity from IMU (integration)
        if DataSource.IMU in recent_readings:
            imu = recent_readings[DataSource.IMU]
            fused.velocity = (0, 0, imu.value)
            sources_used.append(DataSource.IMU)
        
        # Fuse temperature
        if DataSource.TEMPERATURE_SENSOR in recent_readings:
            temp = recent_readings[DataSource.TEMPERATURE_SENSOR]
            fused.temperature = temp.value
            sources_used.append(DataSource.TEMPERATURE_SENSOR)
        
        # Fuse battery
        if DataSource.BATTERY_MONITOR in recent_readings:
            battery = recent_readings[DataSource.BATTERY_MONITOR]
            fused.battery = battery.value
            sources_used.append(DataSource.BATTERY_SENSOR)
        
        # Calculate quality
        fused.data_quality = len(sources_used) / len(DataSource)
        fused.sources_used = sources_used
        
        self.last_fused = fused
        self.fusion_history.append(fused)
        
        return fused
    
    def get_weighted_reading(self, source: DataSource, 
                            reference_sources: List[DataSource]) -> float:
        """Get weighted reading using multiple sources"""
        if source not in self.buffers or not self.buffers[source]:
            return 0.0
        
        # Get latest value
        value = self.buffers[source][-1].value
        
        # Weight based on sensor quality
        if source in self.sensors:
            # Lower noise = higher weight
            weight = 1.0 / (self.sensors[source].noise_std + 0.01)
            return value * weight
        
        return value
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fusion statistics"""
        return {
            'sources_active': sum(1 for b in self.buffers.values() if b),
            'fusion_count': len(self.fusion_history),
            'last_fused': self.last_fused.timestamp if self.last_fused else None
        }


class KalmanFilterFusion:
    """Kalman filter based fusion for position/velocity"""
    
    def __init__(self):
        # State: [x, y, z, vx, vy, vz]
        self.state = np.zeros(6)
        self.covariance = np.eye(6) * 100
        
        # Process noise
        self.Q = np.eye(6) * 0.01
        
    def predict(self, dt: float):
        """Predict step"""
        # State transition matrix
        F = np.eye(6)
        F[0, 3] = dt  # x += vx * dt
        F[1, 4] = dt
        F[2, 5] = dt
        
        # Predict state
        self.state = F @ self.state
        
        # Predict covariance
        self.covariance = F @ self.covariance @ F.T + self.Q
    
    def update(self, measurement: np.ndarray, R: np.ndarray, 
               H: np.ndarray):
        """Update with measurement"""
        # Innovation
        y = measurement - H @ self.state
        
        # Innovation covariance
        S = H @ self.covariance @ H.T + R
        
        # Kalman gain
        K = self.covariance @ H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ y
        
        # Update covariance
        I = np.eye(6)
        self.covariance = (I - K @ H) @ self.covariance
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get current position"""
        return tuple(self.state[:3])
    
    def get_velocity(self) -> Tuple[float, float, float]:
        """Get current velocity"""
        return tuple(self.state[3:])


class MultiSourceIntegrator:
    """Integrate data from multiple sources"""
    
    def __init__(self):
        self.fusion_engine = TelemetryFusionEngine()
        self.kalman_fusion = KalmanFilterFusion()
        
    def integrate(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate sensor data"""
        
        # Add readings to fusion engine
        for source_str, value in sensor_data.items():
            try:
                source = DataSource(source_str)
                self.fusion_engine.add_reading(source, value)
            except ValueError:
                pass
        
        # Get fused telemetry
        fused = self.fusion_engine.fuse()
        
        result = {
            'timestamp': time.time(),
            'fused': fused is not None
        }
        
        if fused:
            if fused.position:
                result['position'] = fused.position
            if fused.velocity:
                result['velocity'] = fused.velocity
            if fused.temperature:
                result['temperature'] = fused.temperature
            result['quality'] = fused.data_quality
        
        return result


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Telemetry Data Fusion...")
    
    # Test Fusion Engine
    print("\n1. Testing Fusion Engine...")
    fusion = TelemetryFusionEngine()
    
    # Add sensor readings
    fusion.add_reading(DataSource.GPS, 34.0, metadata={'type': 'latitude'})
    fusion.add_reading(DataSource.GPS, -118.0, metadata={'type': 'longitude'})
    fusion.add_reading(DataSource.BAROMETER, 101325.0)
    fusion.add_reading(DataSource.TEMPERATURE_SENSOR, 25.0)
    fusion.add_reading(DataSource.BATTERY_MONITOR, 12.5)
    
    # Fuse
    result = fusion.fuse()
    if result:
        print(f"   Fused position: {result.position}")
        print(f"   Temperature: {result.temperature}")
        print(f"   Quality: {result.data_quality:.2f}")
    
    # Test Kalman Filter Fusion
    print("\n2. Testing Kalman Filter Fusion...")
    kf = KalmanFilterFusion()
    
    # Simulate GPS updates
    for i in range(10):
        kf.predict(1.0)  # 1 second update
        
        # Simulated GPS measurement
        gps_meas = np.array([34.0 + i*0.001, -118.0 + i*0.001, 1000.0 + i])
        R = np.eye(3) * 1.0  # GPS noise
        H = np.eye(3, 6)  # Observe position only
        kf.update(gps_meas, R, H)
        
    pos = kf.get_position()
    print(f"   Kalman position: {pos}")
    
    # Test Multi-Source Integrator
    print("\n3. Testing Multi-Source Integrator...")
    integrator = MultiSourceIntegrator()
    
    sensor_data = {
        'gps': 34.0,
        'barometer': 101300.0,
        'temperature': 22.0,
        'battery': 12.4
    }
    
    result = integrator.integrate(sensor_data)
    print(f"   Integration result: {result}")
    
    print("\n✅ Telemetry Data Fusion test completed!")