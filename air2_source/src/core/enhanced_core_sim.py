"""
Enhanced Core Simulation for AirOne v3.0
Contains simulation engine and telemetry records with advanced physics modeling
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from scipy.integrate import odeint


class MissionPhase(Enum):
    """Different phases of a mission"""
    PRE_LAUNCH = "pre_launch"
    LAUNCH = "launch"
    ASCENT = "ascent"
    APOGEE_TRANSITION = "apogee_transition"
    APOGEE = "apogee"
    DESCENT_WITH_CHUTE = "descent_with_chute"
    DESCENT_UNDER_CHUTE = "descent_under_chute"
    RECOVERY = "recovery"


@dataclass
class TelemetryRecord:
    """Record of telemetry data"""
    timestamp: datetime
    altitude: float
    velocity: float
    temperature: float
    pressure: float
    latitude: float
    longitude: float
    battery_level: float
    phase: MissionPhase
    gps_fix: bool = True
    radio_signal_strength: float = -100.0
    acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyroscope: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    magnetometer: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    acceleration_total: float = 0.0
    flight_angle: float = 0.0  # Angle of flight in radians
    mach_number: float = 0.0   # Mach number
    dynamic_pressure: float = 0.0  # Dynamic pressure in Pa
    g_force: float = 1.0       # G-force experienced
    wind_speed: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Wind speed vector (x, y, z)
    air_density: float = 1.225 # Air density in kg/m³
    additional_data: Dict[str, Any] = field(default_factory=dict)


class PhysicsCalculator:
    """Advanced physics calculator for realistic flight dynamics"""

    def __init__(self):
        # Physical constants
        self.g = 9.80665  # Gravitational acceleration (m/s²)
        self.rho_0 = 1.225  # Sea level air density (kg/m³)
        self.p_0 = 101325.0  # Sea level pressure (Pa)
        self.temp_0 = 288.15  # Sea level temperature (K)
        self.R = 287.05  # Specific gas constant for air (J/(kg·K))
        self.L = 0.0065  # Temperature lapse rate (K/m)
        self.gamma = 1.4  # Specific heat ratio for air

    def air_density_at_altitude(self, altitude: float) -> float:
        """Calculate air density at given altitude using international standard atmosphere"""
        if altitude < 11000:  # Troposphere
            temp = self.temp_0 - self.L * altitude
            pressure = self.p_0 * (temp / self.temp_0) ** (self.g / (self.L * self.R))
        else:  # Stratosphere approximation
            temp = 216.65  # Constant temperature in lower stratosphere
            pressure = self.p_0 * math.exp(-self.g * (altitude - 11000) / (self.R * temp))

        density = pressure / (self.R * temp)
        return max(density, 0.001)  # Prevent zero/negative density

    def speed_of_sound(self, altitude: float) -> float:
        """Calculate speed of sound at given altitude"""
        if altitude < 11000:
            temp = self.temp_0 - self.L * altitude
        else:
            temp = 216.65

        # Speed of sound in m/s
        speed = math.sqrt(self.gamma * self.R * temp)
        return max(speed, 1.0)  # Prevent zero speed

    def dynamic_pressure(self, velocity: float, altitude: float) -> float:
        """Calculate dynamic pressure at given velocity and altitude"""
        rho = self.air_density_at_altitude(altitude)
        q = 0.5 * rho * velocity**2
        return q

    def drag_force(self, velocity: float, altitude: float, drag_coefficient: float = 0.75,
                   reference_area: float = 0.01) -> float:
        """Calculate drag force"""
        rho = self.air_density_at_altitude(altitude)
        v_sq = max(velocity**2, 0.01)  # Prevent zero velocity issues
        drag = 0.5 * rho * v_sq * drag_coefficient * reference_area
        return drag

    def reynolds_number(self, velocity: float, altitude: float, characteristic_length: float = 0.1) -> float:
        """Calculate Reynolds number"""
        rho = self.air_density_at_altitude(altitude)
        # Dynamic viscosity approximation (simplified)
        temp = self.temp_0 - self.L * altitude if altitude < 11000 else 216.65
        # Sutherland's law approximation for air viscosity
        mu = 1.458e-6 * (temp ** 1.5) / (temp + 110.4)
        re = (rho * abs(velocity) * characteristic_length) / mu
        return re

    def terminal_velocity(self, mass: float, drag_coefficient: float = 0.75,
                         reference_area: float = 0.01, altitude: float = 0) -> float:
        """Calculate terminal velocity"""
        rho = self.air_density_at_altitude(altitude)
        weight = mass * self.g
        v_term = math.sqrt((2 * weight) / (rho * drag_coefficient * reference_area))
        return v_term


class AdvancedFlightDynamics:
    """Advanced flight dynamics simulator with realistic physics"""

    def __init__(self):
        self.physics = PhysicsCalculator()
        self.mass = 5.0  # Mass of the CanSat in kg
        self.drag_coefficient = 0.75  # Drag coefficient
        self.chute_drag_coefficient = 2.2  # Parachute drag coefficient
        self.reference_area = 0.01  # Reference area in m²
        self.chute_area = 0.5  # Parachute area in m²

    def equations_of_motion(self, state, t, chute_deployed=False):
        """
        System of differential equations for flight dynamics
        state = [altitude, velocity]
        """
        altitude, velocity = state

        # Calculate forces
        weight = self.mass * self.physics.g
        drag_coeff = self.chute_drag_coefficient if chute_deployed else self.drag_coefficient
        ref_area = self.chute_area if chute_deployed else self.reference_area

        drag = self.physics.drag_force(abs(velocity), altitude, drag_coeff, ref_area)

        # Determine direction of drag force
        drag_direction = -np.sign(velocity)  # Drag opposes motion

        # Net force (positive is upward)
        if velocity >= 0:  # Moving upward
            net_force = -weight - drag
        else:  # Moving downward
            net_force = -weight + drag

        # Acceleration (F = ma => a = F/m)
        acceleration = net_force / self.mass

        # Return derivatives [d(altitude)/dt, d(velocity)/dt]
        return [velocity, acceleration]

    def simulate_trajectory(self, initial_altitude: float, initial_velocity: float,
                          time_points: np.ndarray, chute_deployed: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """Simulate trajectory using ODE solver"""
        initial_state = [initial_altitude, initial_velocity]

        solution = odeint(self.equations_of_motion, initial_state, time_points,
                         args=(chute_deployed,))

        altitudes = solution[:, 0]
        velocities = solution[:, 1]

        return altitudes, velocities


class EnhancedSimulationEngine:
    """Enhanced simulation engine for AirOne system with advanced physics modeling"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.is_running = False
        self.current_time = 0.0
        self.mission_phase = MissionPhase.PRE_LAUNCH
        self.telemetry_history = []

        # Physics calculator
        self.physics = PhysicsCalculator()
        self.flight_dynamics = AdvancedFlightDynamics()

        # Flight state variables
        self.altitude = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.latitude = 34.0522  # Default starting latitude
        self.longitude = -118.2437  # Default starting longitude
        self.temperature = 20.0
        self.pressure = 1013.25
        self.battery_level = 100.0

        # Mission-specific parameters
        self.apogee_time = None
        self.apogee_altitude = 0.0
        self.chute_deployed = False
        self.motor_burn_time = 8.0  # Time motor burns in seconds
        self.chute_deploy_altitude = 300.0  # Altitude to deploy parachute

        # Wind conditions (can be varied over time)
        self.wind_vector = (2.0, 0.0, 0.0)  # (eastward, northward, vertical) in m/s

        # Flight statistics
        self.max_velocity = 0.0
        self.max_acceleration = 0.0
        self.max_mach_number = 0.0

    def start_simulation(self):
        """Start the simulation"""
        self.is_running = True
        self.current_time = 0.0
        self.mission_phase = MissionPhase.PRE_LAUNCH
        self.apogee_time = None
        self.apogee_altitude = 0.0
        self.chute_deployed = False
        self.telemetry_history = []
        print("Enhanced simulation engine started with advanced physics modeling")

    def stop_simulation(self):
        """Stop the simulation"""
        self.is_running = False
        print("Enhanced simulation engine stopped")

    def update(self, dt: float) -> Optional[TelemetryRecord]:
        """Update simulation and return new telemetry with advanced physics"""
        if not self.is_running:
            return None

        self.current_time += dt

        # Update flight dynamics based on mission phase
        self._update_flight_dynamics(dt)

        # Determine current mission phase
        self._update_mission_phase()

        # Calculate advanced physics parameters
        air_density = self.physics.air_density_at_altitude(self.altitude)
        speed_of_sound = self.physics.speed_of_sound(self.altitude)
        mach_number = abs(self.velocity) / speed_of_sound if speed_of_sound > 0 else 0
        dynamic_pressure = self.physics.dynamic_pressure(abs(self.velocity), self.altitude)

        # Calculate g-force (acceleration in terms of g's)
        g_force = abs(self.acceleration) / self.physics.g if self.physics.g > 0 else 1.0

        # Calculate flight angle (angle of velocity vector with horizontal)
        # For simplicity, assuming vertical flight for now
        flight_angle = math.pi / 2 if self.velocity != 0 else 0  # Vertical flight

        # Update statistics
        self.max_velocity = max(self.max_velocity, abs(self.velocity))
        self.max_acceleration = max(self.max_acceleration, abs(self.acceleration))
        self.max_mach_number = max(self.max_mach_number, mach_number)

        # Calculate GPS drift due to wind and horizontal movement
        # Simple model: wind affects position over time
        wind_drift_east = self.wind_vector[0] * dt
        wind_drift_north = self.wind_vector[1] * dt

        # Convert to approximate lat/long changes (very simplified)
        # 1 degree latitude ~ 111 km, 1 degree longitude ~ 111*cos(lat) km
        lat_change = wind_drift_north / 111000.0  # Rough conversion
        long_change = wind_drift_east / (111000.0 * math.cos(math.radians(self.latitude)))

        self.latitude += lat_change
        self.longitude += long_change

        # Create telemetry record with advanced parameters
        record = TelemetryRecord(
            timestamp=datetime.now(),
            altitude=self.altitude,
            velocity=self.velocity,
            acceleration=(0.0, 0.0, self.acceleration),  # Z-axis acceleration
            temperature=self.temperature,
            pressure=self.pressure,
            latitude=self.latitude,
            longitude=self.longitude,
            battery_level=max(100 - (self.current_time / 100), 20),
            phase=self.mission_phase,
            gps_fix=True,
            radio_signal_strength=-50 + (self.altitude / 1000) * 10,
            acceleration_total=abs(self.acceleration),
            flight_angle=flight_angle,
            mach_number=mach_number,
            dynamic_pressure=dynamic_pressure,
            g_force=g_force,
            wind_speed=self.wind_vector,
            air_density=air_density
        )

        self.telemetry_history.append(record)

        # Limit history size
        if len(self.telemetry_history) > 10000:
            self.telemetry_history = self.telemetry_history[-5000:]

        return record

    def _update_flight_dynamics(self, dt: float):
        """Update flight dynamics based on current mission phase"""
        if self.current_time < self.motor_burn_time:
            # Power ascent phase - rocket motor firing
            self.mission_phase = MissionPhase.LAUNCH
            thrust = 200.0  # Thrust in Newtons (example value)
            drag = self.flight_dynamics.physics.drag_force(
                self.velocity, self.altitude,
                self.flight_dynamics.drag_coefficient,
                self.flight_dynamics.reference_area
            )
            weight = self.flight_dynamics.mass * self.flight_dynamics.physics.g

            net_force = thrust - weight - drag if self.velocity >= 0 else thrust - weight + drag
            self.acceleration = net_force / self.flight_dynamics.mass
            self.velocity += self.acceleration * dt
            self.altitude += self.velocity * dt
        else:
            # Ballistic phase - coasting and descent
            # Use simplified physics for real-time simulation
            if self.altitude > 0:
                drag = self.flight_dynamics.physics.drag_force(
                    abs(self.velocity), self.altitude,
                    self.chute_drag_coefficient if self.chute_deployed else self.flight_dynamics.drag_coefficient,
                    self.chute_area if self.chute_deployed else self.flight_dynamics.reference_area
                )
                weight = self.flight_dynamics.mass * self.flight_dynamics.physics.g

                # Determine net force direction
                if self.velocity >= 0:  # Moving upward
                    net_force = -weight - drag
                else:  # Moving downward
                    net_force = -weight + drag

                self.acceleration = net_force / self.flight_dynamics.mass
                self.velocity += self.acceleration * dt
                self.altitude += self.velocity * dt

                # Deploy parachute if needed
                if not self.chute_deployed and self.altitude <= self.chute_deploy_altitude and self.velocity < 0:
                    self.chute_deployed = True
                    print(f"Parachute deployed at t={self.current_time:.2f}s, alt={self.altitude:.2f}m")

        # Ensure altitude doesn't go negative
        if self.altitude < 0:
            self.altitude = 0
            self.velocity = 0
            self.acceleration = 0

    def _update_mission_phase(self):
        """Update mission phase based on current flight conditions"""
        if self.current_time < 1.0:
            self.mission_phase = MissionPhase.PRE_LAUNCH
        elif self.current_time < self.motor_burn_time:
            self.mission_phase = MissionPhase.LAUNCH
        elif self.velocity > 0 and self.altitude > self.apogee_altitude:
            # Ascending toward apogee
            self.apogee_altitude = self.altitude
            self.apogee_time = self.current_time
            self.mission_phase = MissionPhase.ASCENT
        elif self.velocity > -1.0 and self.velocity < 1.0 and self.altitude > 0.95 * self.apogee_altitude:
            # Near apogee - very low velocity at peak altitude
            self.mission_phase = MissionPhase.APOGEE
        elif self.velocity < 0 and not self.chute_deployed:
            # Descending without parachute (before deployment or if it fails)
            self.mission_phase = MissionPhase.DESCENT_WITH_CHUTE # Assuming DESCENT_WITH_CHUTE implicitly means "falling"
        elif self.velocity < 0 and self.chute_deployed:
            # Descending under parachute
            self.mission_phase = MissionPhase.DESCENT_UNDER_CHUTE
        elif self.altitude <= 0 and abs(self.velocity) < 1.0:
            # On ground, not moving significantly
            self.mission_phase = MissionPhase.RECOVERY
        elif self.velocity < 0:  # Falling but chute not deployed yet
            self.mission_phase = MissionPhase.ASCENT  # Actually descending, but keeping same enum for now

    def get_flight_statistics(self) -> Dict[str, Any]:
        """Get comprehensive flight statistics"""
        return {
            'max_altitude': self.apogee_altitude,
            'max_velocity': self.max_velocity,
            'max_acceleration': self.max_acceleration,
            'max_mach_number': self.max_mach_number,
            'flight_time': self.current_time,
            'apogee_time': self.apogee_time,
            'chute_deployed': self.chute_deployed,
            'total_distance_traveled': sum([
                abs(record.velocity) * 0.1 for record in self.telemetry_history[-100:]
            ]) if self.telemetry_history else 0,
            'battery_consumption_rate': (100 - self.battery_level) / self.current_time if self.current_time > 0 else 0
        }

    def get_real_time_data(self) -> Dict[str, Any]:
        """Get real-time flight data for display"""
        return {
            'time': self.current_time,
            'altitude': self.altitude,
            'velocity': self.velocity,
            'acceleration': self.acceleration,
            'phase': self.mission_phase.value,
            'mach_number': self.physics.speed_of_sound(self.altitude),
            'dynamic_pressure': self.physics.dynamic_pressure(abs(self.velocity), self.altitude),
            'air_density': self.physics.air_density_at_altitude(self.altitude),
            'battery_level': self.battery_level,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'chute_deployed': self.chute_deployed
        }

    def set_wind_conditions(self, wind_vector: Tuple[float, float, float]):
        """Set wind conditions (eastward, northward, vertical) in m/s"""
        self.wind_vector = wind_vector

    def set_vehicle_params(self, mass: float, drag_coefficient: float = 0.75,
                          reference_area: float = 0.01):
        """Set vehicle physical parameters"""
        self.flight_dynamics.mass = mass
        self.flight_dynamics.drag_coefficient = drag_coefficient
        self.flight_dynamics.reference_area = reference_area