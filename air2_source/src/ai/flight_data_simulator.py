"""
AirOne v4.0 - Flight Data Simulator
Generates realistic flight simulation data for model training
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import random
import math
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlightPhase(Enum):
    """Flight phases for simulation"""
    PRE_LAUNCH = "pre_launch"
    LAUNCH = "launch"
    ASCENT = "ascent"
    CRUISE = "cruise"
    APOGEE = "apogee"
    DESCENT = "descent"
    RECOVERY = "recovery"
    LANDED = "landed"


class FlightMode(Enum):
    """Flight modes"""
    MANUAL = "manual"
    AUTO = "auto"
    STABILIZED = "stabilized"
    ACRO = "acro"
    RETURN_TO_HOME = "return_to_home"
    LAND = "land"


@dataclass
class FlightTelemetry:
    """Flight telemetry data structure"""
    timestamp: str
    flight_time: float
    phase: str
    flight_mode: str
    
    # Position
    altitude: float
    gps_latitude: float
    gps_longitude: float
    gps_altitude: float
    
    # Velocity & Acceleration
    velocity: float
    ground_speed: float
    air_speed: float
    climb_rate: float
    acceleration: float
    
    # Orientation
    pitch: float
    roll: float
    yaw: float
    
    # Control
    throttle: float
    motor_rpm: float
    
    # Power
    battery_voltage: float
    battery_current: float
    battery_percentage: float
    power_consumption: float
    
    # Environment
    temperature: float
    pressure: float
    wind_speed: float
    wind_direction: float
    
    # System
    rssi: float
    snr: float
    satellites: int
    
    # Metadata
    mission_time: float
    distance_from_home: float


class FlightPhysicsModel:
    """
    Physics-based flight simulation model
    """

    def __init__(self, aircraft_params: Optional[Dict] = None):
        # Aircraft parameters
        self.mass = aircraft_params.get('mass', 1.5) if aircraft_params else 1.5  # kg
        self.wing_area = aircraft_params.get('wing_area', 0.5) if aircraft_params else 0.5  # m²
        self.max_thrust = aircraft_params.get('max_thrust', 30) if aircraft_params else 30  # N
        self.drag_coefficient = aircraft_params.get('drag_coefficient', 0.05) if aircraft_params else 0.05
        self.battery_capacity = aircraft_params.get('battery_capacity', 5000) if aircraft_params else 5000  # mAh
        
        # Physics constants
        self.gravity = 9.81  # m/s²
        self.air_density = 1.225  # kg/m³ at sea level
        
        # State
        self.altitude = 0.0
        self.velocity = 0.0
        self.climb_rate = 0.0
        self.battery_mah = self.battery_capacity
        self.flight_time = 0.0

    def reset(self):
        """Reset physics state"""
        self.altitude = 0.0
        self.velocity = 0.0
        self.climb_rate = 0.0
        self.battery_mah = self.battery_capacity
        self.flight_time = 0.0

    def update(self, throttle: float, pitch: float, dt: float = 0.1) -> Dict[str, float]:
        """
        Update physics state
        
        Args:
            throttle: Throttle input (0-1)
            pitch: Pitch angle (degrees)
            dt: Time step (seconds)
            
        Returns:
            Updated state dictionary
        """
        # Convert pitch to radians
        pitch_rad = math.radians(pitch)
        
        # Calculate forces
        thrust = self.max_thrust * throttle
        drag = 0.5 * self.air_density * self.velocity**2 * self.drag_coefficient * self.wing_area
        
        # Net force in direction of motion
        net_force = thrust * math.cos(pitch_rad) - drag - self.mass * self.gravity * math.sin(pitch_rad)
        
        # Acceleration
        acceleration = net_force / self.mass
        
        # Update velocity
        self.velocity += acceleration * dt
        self.velocity = max(0, self.velocity)  # Can't have negative speed
        
        # Update climb rate
        self.climb_rate = self.velocity * math.sin(pitch_rad)
        
        # Update altitude
        self.altitude += self.climb_rate * dt
        self.altitude = max(0, self.altitude)  # Can't go below ground
        
        # Update battery
        current_draw = throttle * 30 + 2  # 30A at full throttle + 2A baseline
        self.battery_mah -= current_draw * 1000 * dt / 3600  # Convert to mAh
        
        # Update flight time
        self.flight_time += dt
        
        return {
            'altitude': self.altitude,
            'velocity': self.velocity,
            'climb_rate': self.climb_rate,
            'acceleration': acceleration,
            'battery_mah': self.battery_mah,
            'flight_time': self.flight_time
        }


class FlightDataSimulator:
    """
    Generates realistic flight simulation data
    
    Simulates various flight phases, conditions, and anomalies
    for comprehensive model training
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Simulation parameters
        self.simulation_rate = self.config.get('simulation_rate', 10)  # Hz
        self.start_latitude = self.config.get('start_latitude', 40.7128)
        self.start_longitude = self.config.get('start_longitude', -74.0060)
        self.start_altitude = self.config.get('start_altitude', 10)  # meters
        
        # Environment
        self.base_temperature = self.config.get('base_temperature', 20)  # °C
        self.base_pressure = self.config.get('base_pressure', 101325)  # Pa
        self.wind_speed = self.config.get('wind_speed', 5)  # m/s
        self.wind_direction = self.config.get('wind_direction', 270)  # degrees
        
        # Aircraft
        self.physics = FlightPhysicsModel(self.config.get('aircraft', {}))
        
        # Flight state
        self.current_phase = FlightPhase.PRE_LAUNCH
        self.flight_mode = FlightMode.STABILIZED
        self.mission_start = None
        self.anomaly_active = False
        self.anomaly_type = None
        
        # Noise parameters
        self.noise_params = {
            'altitude': 0.5,
            'velocity': 0.3,
            'pitch': 1.0,
            'roll': 1.0,
            'yaw': 2.0,
            'temperature': 0.2,
            'pressure': 10
        }

    def reset(self):
        """Reset simulation state"""
        self.physics.reset()
        self.current_phase = FlightPhase.PRE_LAUNCH
        self.flight_mode = FlightMode.STABILIZED
        self.mission_start = None
        self.anomaly_active = False
        self.anomaly_type = None

    def generate_telemetry(self, override: Optional[Dict] = None) -> FlightTelemetry:
        """
        Generate single telemetry record
        
        Args:
            override: Optional values to override
            
        Returns:
            FlightTelemetry object
        """
        if self.mission_start is None:
            self.mission_start = datetime.now()
        
        # Update physics
        if self.current_phase != FlightPhase.PRE_LAUNCH:
            throttle, pitch = self._get_control_inputs()
            state = self.physics.update(throttle, pitch, 1.0 / self.simulation_rate)
        
        # Generate base telemetry
        now = datetime.now()
        flight_time = (now - self.mission_start).total_seconds()
        
        telemetry = FlightTelemetry(
            timestamp=now.isoformat(),
            flight_time=flight_time,
            phase=self.current_phase.value,
            flight_mode=self.flight_mode.value,
            
            # Position
            altitude=self.physics.altitude + self._noise('altitude'),
            gps_latitude=self.start_latitude + self._small_offset(),
            gps_longitude=self.start_longitude + self._small_offset(),
            gps_altitude=self.physics.altitude + self._noise('altitude'),
            
            # Velocity & Acceleration
            velocity=self.physics.velocity + self._noise('velocity'),
            ground_speed=self.physics.velocity * 0.95 + self._noise('velocity'),
            air_speed=self.physics.velocity + self._noise('velocity'),
            climb_rate=self.physics.climb_rate + self._noise('velocity') * 2,
            acceleration=self.physics.climb_rate / 0.1 + self._noise('velocity') * 5,
            
            # Orientation
            pitch=self._noise('pitch'),
            roll=self._noise('roll'),
            yaw=self._noise('yaw'),
            
            # Control
            throttle=self._get_throttle_for_phase(),
            motor_rpm=self._get_throttle_for_phase() * 10000 + random.uniform(-100, 100),
            
            # Power
            battery_voltage=16.8 - (1 - self.physics.battery_mah / self.physics.battery_capacity) * 2.8,
            battery_current=self._get_throttle_for_phase() * 25 + 2,
            battery_percentage=max(0, self.physics.battery_mah / self.physics.battery_capacity * 100),
            power_consumption=(self._get_throttle_for_phase() * 25 + 2) * 16.8,
            
            # Environment
            temperature=self.base_temperature + self._noise('temperature'),
            pressure=self.base_pressure - self.physics.altitude * 12 + self._noise('pressure'),
            wind_speed=self.wind_speed + random.uniform(-2, 2),
            wind_direction=self.wind_direction + random.uniform(-30, 30),
            
            # System
            rssi=-40 - random.uniform(0, 30),
            snr=20 + random.uniform(-5, 10),
            satellites=random.randint(8, 15),
            
            # Metadata
            mission_time=flight_time,
            distance_from_home=self._calculate_distance_from_home()
        )
        
        # Apply overrides
        if override:
            for key, value in override.items():
                if hasattr(telemetry, key):
                    setattr(telemetry, key, value)
        
        # Apply anomalies if active
        if self.anomaly_active:
            telemetry = self._apply_anomaly(telemetry)
        
        # Update phase based on state
        self._update_phase()
        
        return telemetry

    def _get_control_inputs(self) -> Tuple[float, float]:
        """Get control inputs based on flight phase"""
        phase_controls = {
            FlightPhase.PRE_LAUNCH: (0.0, 0.0),
            FlightPhase.LAUNCH: (1.0, 45.0),
            FlightPhase.ASCENT: (0.8, 30.0),
            FlightPhase.CRUISE: (0.5, 5.0),
            FlightPhase.APOGEE: (0.2, 0.0),
            FlightPhase.DESCENT: (0.3, -10.0),
            FlightPhase.RECOVERY: (0.4, -5.0),
            FlightPhase.LANDED: (0.0, 0.0)
        }
        
        base_throttle, base_pitch = phase_controls.get(self.current_phase, (0.5, 0.0))
        
        # Add variation
        throttle = base_throttle + random.uniform(-0.1, 0.1)
        pitch = base_pitch + random.uniform(-5, 5)
        
        return max(0, min(1, throttle)), pitch

    def _get_throttle_for_phase(self) -> float:
        """Get expected throttle for current phase"""
        phase_throttle = {
            FlightPhase.PRE_LAUNCH: 0.0,
            FlightPhase.LAUNCH: 1.0,
            FlightPhase.ASCENT: 0.8,
            FlightPhase.CRUISE: 0.5,
            FlightPhase.APOGEE: 0.2,
            FlightPhase.DESCENT: 0.3,
            FlightPhase.RECOVERY: 0.4,
            FlightPhase.LANDED: 0.0
        }
        return phase_throttle.get(self.current_phase, 0.5)

    def _update_phase(self):
        """Update flight phase based on current state"""
        altitude = self.physics.altitude
        climb_rate = self.physics.climb_rate
        battery = self.physics.battery_mah / self.physics.battery_capacity * 100
        
        # Check if we should force a transition for demonstration
        if self.config.get('force_transition', False):
            flight_time = self.physics.flight_time
            if flight_time > 2 and self.current_phase == FlightPhase.PRE_LAUNCH:
                self.current_phase = FlightPhase.LAUNCH
            elif flight_time > 5 and self.current_phase == FlightPhase.LAUNCH:
                self.current_phase = FlightPhase.ASCENT
            elif flight_time > 15 and self.current_phase == FlightPhase.ASCENT:
                self.current_phase = FlightPhase.APOGEE
            elif flight_time > 20 and self.current_phase == FlightPhase.APOGEE:
                self.current_phase = FlightPhase.DESCENT
            elif flight_time > 40 and self.current_phase == FlightPhase.DESCENT:
                self.current_phase = FlightPhase.RECOVERY
            elif flight_time > 50 and self.current_phase == FlightPhase.RECOVERY:
                self.current_phase = FlightPhase.LANDED
            return

        if altitude < 5 and self.current_phase == FlightPhase.PRE_LAUNCH:
            return  # Stay in pre-launch
        
        if altitude > 5 and self.current_phase == FlightPhase.PRE_LAUNCH:
            self.current_phase = FlightPhase.LAUNCH
        
        if altitude > 100 and climb_rate > 0:
            self.current_phase = FlightPhase.ASCENT
        
        if altitude > 500 and climb_rate > 0:
            self.current_phase = FlightPhase.CRUISE
        
        if climb_rate < 0.5 and climb_rate > -0.5 and altitude > 400:
            self.current_phase = FlightPhase.APOGEE
        
        if climb_rate < -1 and altitude > 100:
            self.current_phase = FlightPhase.DESCENT
        
        if altitude < 100 and altitude > 10:
            self.current_phase = FlightPhase.RECOVERY
        
        if altitude < 5:
            self.current_phase = FlightPhase.LANDED
        
        # Battery-based phase change
        if battery < 15 and self.current_phase not in [FlightPhase.LANDED, FlightPhase.RECOVERY]:
            self.current_phase = FlightPhase.RECOVERY

    def _calculate_distance_from_home(self) -> float:
        """Calculate distance from home position"""
        # Simplified calculation
        lat_offset = (self.start_latitude - self.start_latitude) * 111000  # meters per degree
        lon_offset = (self.start_longitude - self.start_longitude) * 111000 * math.cos(math.radians(self.start_latitude))
        return math.sqrt(lat_offset**2 + lon_offset**2)

    def _noise(self, feature: str) -> float:
        """Add realistic sensor noise"""
        std = self.noise_params.get(feature, 0.1)
        return random.gauss(0, std)

    def _small_offset(self) -> float:
        """Generate small GPS offset"""
        return random.uniform(-0.0001, 0.0001)

    def _apply_anomaly(self, telemetry: FlightTelemetry) -> FlightTelemetry:
        """Apply anomaly effects to telemetry"""
        if self.anomaly_type == 'motor_failure':
            telemetry.motor_rpm *= 0.5
            telemetry.throttle *= 0.5
            telemetry.climb_rate = -5
        
        elif self.anomaly_type == 'sensor_drift':
            telemetry.altitude += random.uniform(10, 30)
            telemetry.gps_altitude += random.uniform(10, 30)
        
        elif self.anomaly_type == 'battery_sag':
            telemetry.battery_voltage *= 0.85
            telemetry.battery_percentage *= 0.8
        
        elif self.anomaly_type == 'gps_loss':
            telemetry.satellites = 0
            telemetry.rssi = -100
        
        elif self.anomaly_type == 'wind_gust':
            telemetry.wind_speed = self.wind_speed * 3
            telemetry.roll += random.uniform(-15, 15)
        
        return telemetry

    def activate_anomaly(self, anomaly_type: str):
        """Activate a specific anomaly"""
        self.anomaly_active = True
        self.anomaly_type = anomaly_type
        logger.info(f"Anomaly activated: {anomaly_type}")

    def deactivate_anomaly(self):
        """Deactivate current anomaly"""
        self.anomaly_active = False
        self.anomaly_type = None

    def generate_flight_sequence(self, duration_seconds: float,
                                 include_anomalies: bool = False) -> List[FlightTelemetry]:
        """
        Generate complete flight sequence
        
        Args:
            duration_seconds: Duration of flight
            include_anomalies: Whether to include anomalies
            
        Returns:
            List of FlightTelemetry objects
        """
        self.reset()
        self.mission_start = datetime.now()
        
        telemetry_list = []
        n_samples = int(duration_seconds * self.simulation_rate)
        
        anomaly_events = []
        if include_anomalies and n_samples > 100:
            # Schedule random anomalies
            n_anomalies = random.randint(1, 3)
            for _ in range(n_anomalies):
                start_idx = random.randint(50, n_samples - 50)
                duration = random.randint(10, 30)
                anomaly_type = random.choice([
                    'motor_failure', 'sensor_drift', 'battery_sag', 
                    'gps_loss', 'wind_gust'
                ])
                anomaly_events.append({
                    'start': start_idx,
                    'end': start_idx + duration,
                    'type': anomaly_type
                })
        
        for i in range(n_samples):
            # Check for anomaly events
            for event in anomaly_events:
                if event['start'] <= i <= event['end']:
                    self.activate_anomaly(event['type'])
                    break
                elif i > event['end']:
                    self.deactivate_anomaly()
            
            telemetry = self.generate_telemetry()
            telemetry_list.append(telemetry)
        
        self.deactivate_anomaly()
        
        return telemetry_list

    def generate_labeled_dataset(self, n_flights: int = 10,
                                 duration_range: Tuple[float, float] = (60, 300),
                                 include_anomalies: bool = True) -> List[Dict[str, Any]]:
        """
        Generate labeled dataset for training
        
        Args:
            n_flights: Number of flights to simulate
            duration_range: Range of flight durations
            include_anomalies: Include anomalous flights
            
        Returns:
            List of labeled flight records
        """
        dataset = []
        
        for flight_idx in range(n_flights):
            duration = random.uniform(*duration_range)
            flight_telemetry = self.generate_flight_sequence(
                duration, include_anomalies
            )
            
            for i, telemetry in enumerate(flight_telemetry):
                record = asdict(telemetry)
                
                # Add labels for next-step prediction
                if i < len(flight_telemetry) - 1:
                    next_telemetry = flight_telemetry[i + 1]
                    record['next_altitude'] = next_telemetry.altitude
                    record['next_velocity'] = next_telemetry.velocity
                    record['next_battery'] = next_telemetry.battery_percentage
                
                # Add anomaly label
                record['is_anomaly'] = self.anomaly_active or telemetry.rssi < -65
                
                dataset.append(record)
            
            logger.info(f"Generated flight {flight_idx + 1}/{n_flights}: {len(flight_telemetry)} samples")
        
        logger.info(f"Total dataset: {len(dataset)} samples")
        return dataset

    def to_dataframe(self, dataset: List[Dict]) -> Any:
        """Convert dataset to pandas DataFrame"""
        try:
            import pandas as pd
            return pd.DataFrame(dataset)
        except ImportError:
            logger.warning("pandas not available, returning list")
            return dataset


# Convenience functions
def create_flight_simulator(config: Optional[Dict] = None) -> FlightDataSimulator:
    """Create and return a Flight Data Simulator instance"""
    return FlightDataSimulator(config)


def generate_training_dataset(n_flights: int = 10,
                              duration_range: Tuple[float, float] = (60, 300),
                              include_anomalies: bool = True) -> List[Dict]:
    """Generate training dataset with default settings"""
    simulator = FlightDataSimulator()
    return simulator.generate_labeled_dataset(n_flights, duration_range, include_anomalies)


__all__ = [
    'FlightDataSimulator',
    'create_flight_simulator',
    'generate_training_dataset',
    'FlightPhysicsModel',
    'FlightTelemetry',
    'FlightPhase',
    'FlightMode'
]
