"""
Simulation Mode for AirOne Professional v4.0
Implements accurate physics-based CanSat simulation with real-time telemetry
"""

import logging
import sys
import time
import random
import math
import threading
import queue
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import mode manager - handle gracefully if not available
try:
    from core.mode_manager import OperationalMode, get_mode_manager
except ImportError:
    # Create placeholder
    class OperationalMode:
        SIMULATION = "simulation"
    
    def get_mode_manager():
        return None


@dataclass
class SimulationState:
    """Current state of the simulation"""
    # Position
    altitude: float = 0.0  # meters
    latitude: float = 0.0  # degrees
    longitude: float = 0.0  # degrees
    
    # Velocity
    vertical_velocity: float = 0.0  # m/s
    horizontal_velocity: float = 0.0  # m/s
    
    # Acceleration
    vertical_acceleration: float = 0.0  # m/s²
    horizontal_acceleration: float = 0.0  # m/s²
    
    # Environment
    temperature: float = 20.0  # °C
    pressure: float = 1013.25  # hPa
    humidity: float = 50.0  # %
    
    # System
    battery_voltage: float = 12.6  # V
    battery_percent: float = 100.0  # %
    signal_strength: float = -50.0  # dBm
    
    # Flight state
    flight_phase: str = "PRE_LAUNCH"  # PRE_LAUNCH, LAUNCH, ASCENT, APOGEE, DESCENT, RECOVERY
    parachute_deployed: bool = False
    
    # Timing
    simulation_time: float = 0.0  # seconds
    last_update: float = field(default_factory=time.time)


class PhysicsEngine:
    """Accurate physics simulation for CanSat flight"""
    
    # Physical constants
    GRAVITY = 9.80665  # m/s²
    AIR_DENSITY_SEA_LEVEL = 1.225  # kg/m³
    GAS_CONSTANT = 287.058  # J/(kg·K)
    TEMPERATURE_LAPSE_RATE = 0.0065  # K/m
    SEA_LEVEL_TEMP = 288.15  # K
    SEA_LEVEL_PRESSURE = 101325  # Pa
    
    # CanSat properties
    CANSAT_MASS = 0.350  # kg (350g typical)
    CANSAT_AREA = 0.0045  # m² (cross-sectional area)
    DRAG_COEFFICIENT = 0.75  # typical for cylinder
    PARACHUTE_AREA = 0.5  # m²
    PARACHUTE_DRAG = 1.5  # Cd for parachute
    
    def __init__(self):
        self.state = SimulationState()
        self.running = False
        self.paused = False
        self.update_rate = 50  # Hz
        self.callbacks = []
        self.logger = logging.getLogger(__name__)
        
        # Simulation parameters
        self.launch_time = 0.0
        self.apogee_time = 0.0
        self.parachute_time = 0.0
        
        # Ground station location (default: Los Angeles area)
        self.ground_lat = 34.0522
        self.ground_lon = -118.2437
        self.ground_alt = 100.0  # meters
        
    def register_callback(self, callback):
        """Register a callback for state updates"""
        self.callbacks.append(callback)
        
    def _notify_callbacks(self):
        """Notify all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(self.get_state_dict())
            except Exception as e:
                self.logger.debug(f"Callback notification failed: {e}")
    
    def get_state_dict(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        s = self.state
        return {
            'altitude': s.altitude,
            'vertical_velocity': s.vertical_velocity,
            'horizontal_velocity': s.horizontal_velocity,
            'vertical_acceleration': s.vertical_acceleration,
            'horizontal_acceleration': s.horizontal_acceleration,
            'temperature': s.temperature,
            'pressure': s.pressure,
            'humidity': s.humidity,
            'battery_voltage': s.battery_voltage,
            'battery_percent': s.battery_percent,
            'signal_strength': s.signal_strength,
            'latitude': s.latitude,
            'longitude': s.longitude,
            'flight_phase': s.flight_phase,
            'parachute_deployed': s.parachute_deployed,
            'simulation_time': s.simulation_time,
            'timestamp': datetime.now().isoformat(),
            'mach_number': abs(s.vertical_velocity) / 343.0,  # Speed of sound at sea level
            'acceleration_g': math.sqrt(s.vertical_acceleration**2 + s.horizontal_acceleration**2) / self.GRAVITY
        }
    
    def _calculate_air_density(self, altitude: float) -> float:
        """Calculate air density at given altitude using barometric formula"""
        if altitude < 0:
            altitude = 0
        
        # Temperature at altitude
        temp = self.SEA_LEVEL_TEMP - self.TEMPERATURE_LAPSE_RATE * altitude
        
        # Pressure at altitude
        pressure = self.SEA_LEVEL_PRESSURE * (temp / self.SEA_LEVEL_TEMP) ** (
            self.GRAVITY / (self.GAS_CONSTANT * self.TEMPERATURE_LAPSE_RATE)
        )
        
        # Density from ideal gas law
        density = pressure / (self.GAS_CONSTANT * temp)
        return max(density, 0.01)  # Minimum density
    
    def _calculate_drag_force(self, velocity: float, area: float, cd: float) -> float:
        """Calculate drag force"""
        density = self._calculate_air_density(self.state.altitude)
        drag = 0.5 * density * velocity**2 * area * cd
        return drag
    
    def _calculate_temperature(self, altitude: float) -> float:
        """Calculate temperature at altitude in Celsius"""
        temp_k = self.SEA_LEVEL_TEMP - self.TEMPERATURE_LAPSE_RATE * altitude
        return temp_k - 273.15
    
    def _calculate_pressure(self, altitude: float) -> float:
        """Calculate pressure at altitude in hPa"""
        temp = self.SEA_LEVEL_TEMP - self.TEMPERATURE_LAPSE_RATE * altitude
        pressure = self.SEA_LEVEL_PRESSURE * (temp / self.SEA_LEVEL_TEMP) ** (
            self.GRAVITY / (self.GAS_CONSTANT * self.TEMPERATURE_LAPSE_RATE)
        )
        return pressure / 100.0  # Convert to hPa
    
    def _calculate_gps_offset(self, altitude: float, base_lat: float, base_lon: float) -> Tuple[float, float]:
        """Calculate GPS offset based on horizontal drift"""
        # Approximate: 1 degree latitude ≈ 111km, 1 degree longitude ≈ 111km * cos(lat)
        lat_offset = self.state.horizontal_velocity * math.sin(
            self.state.simulation_time * 0.1
        ) * 0.00001  # Small drift
        
        lon_offset = self.state.horizontal_velocity * math.cos(
            self.state.simulation_time * 0.1
        ) * 0.00001
        
        return base_lat + lat_offset, base_lon + lon_offset
    
    def start_simulation(self, launch_delay: float = 3.0):
        """Start the simulation"""
        self.running = True
        self.paused = False
        self.state = SimulationState()
        self.state.latitude = self.ground_lat
        self.state.longitude = self.ground_lon
        self.state.altitude = self.ground_alt
        self.launch_time = time.time() + launch_delay
        self.logger.info(f"🚀 Simulation starting... Launch in {launch_delay:.1f} seconds")
        
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        
    def pause_simulation(self):
        """Pause the simulation"""
        self.paused = True
        
    def resume_simulation(self):
        """Resume the simulation"""
        self.paused = False
    
    def update_physics(self, dt: float):
        """Update physics simulation"""
        if not self.running or self.paused:
            return
        
        current_time = time.time()
        elapsed = current_time - self.launch_time
        
        self.state.simulation_time += dt
        
        # Phase transitions
        if elapsed > 0 and self.state.flight_phase == "PRE_LAUNCH":
            self.state.flight_phase = "LAUNCH"
            self.logger.info("🔥 LAUNCH DETECTED!")
            
        elif elapsed > 3.5 and self.state.flight_phase == "LAUNCH":
            self.state.flight_phase = "ASCENT"
            self.logger.info("⬆️  ASCENT PHASE")
            
        elif self.state.vertical_velocity < 0 and self.state.flight_phase == "ASCENT":
            self.state.flight_phase = "APOGEE"
            self.apogee_time = elapsed
            self.logger.info(f"🎯 APOGEE REACHED at {self.state.altitude:.1f}m")
            
        elif self.state.altitude < self.ground_alt + 50 and self.state.flight_phase == "APOGEE":
            if not self.state.parachute_deployed:
                self.state.parachute_deployed = True
                self.parachute_time = elapsed
                self.logger.info("🪂 PARACHUTE DEPLOYED")
            self.state.flight_phase = "DESCENT"
            self.logger.info("⬇️  DESCENT PHASE")
            
        elif self.state.altitude <= self.ground_alt and self.state.flight_phase == "DESCENT":
            self.state.flight_phase = "RECOVERY"
            self.state.altitude = self.ground_alt
            self.state.vertical_velocity = 0
            self.state.vertical_acceleration = 0
            self.logger.info("✅ RECOVERY - Safe landing!")
            self.running = False
            return        
        # Physics calculations based on phase
        if self.state.flight_phase == "LAUNCH":
            # Powered ascent with motor thrust
            thrust = 50.0  # N (typical small rocket motor)
            drag = self._calculate_drag_force(
                self.state.vertical_velocity,
                self.CANSAT_AREA,
                self.DRAG_COEFFICIENT
            )
            net_force = thrust - self.CANSAT_MASS * self.GRAVITY - drag
            self.state.vertical_acceleration = net_force / self.CANSAT_MASS
            
        elif self.state.flight_phase == "ASCENT":
            # Ballistic ascent
            drag = self._calculate_drag_force(
                self.state.vertical_velocity,
                self.CANSAT_AREA,
                self.DRAG_COEFFICIENT
            )
            net_force = -self.CANSAT_MASS * self.GRAVITY - drag
            self.state.vertical_acceleration = net_force / self.CANSAT_MASS
            
        elif self.state.flight_phase in ["APOGEE", "DESCENT"]:
            # Descent with or without parachute
            if self.state.parachute_deployed:
                area = self.PARACHUTE_AREA
                cd = self.PARACHUTE_DRAG
            else:
                area = self.CANSAT_AREA
                cd = self.DRAG_COEFFICIENT
                
            drag = self._calculate_drag_force(
                abs(self.state.vertical_velocity),
                area,
                cd
            )
            
            # Terminal velocity calculation
            if self.state.vertical_velocity < 0:
                net_force = -self.CANSAT_MASS * self.GRAVITY + drag
            else:
                net_force = -self.CANSAT_MASS * self.GRAVITY - drag
                
            self.state.vertical_acceleration = net_force / self.CANSAT_MASS
            
        elif self.state.flight_phase == "RECOVERY":
            self.state.vertical_acceleration = 0
            self.state.vertical_velocity = 0
            
        # Update velocity and position (Euler integration)
        if self.state.flight_phase != "PRE_LAUNCH":
            self.state.vertical_velocity += self.state.vertical_acceleration * dt
            self.state.altitude += self.state.vertical_velocity * dt
            
            # Minimum altitude is ground level
            if self.state.altitude < self.ground_alt:
                self.state.altitude = self.ground_alt
                
        # Horizontal drift (simplified)
        self.state.horizontal_velocity = 5.0 * math.sin(self.state.simulation_time * 0.05)
        self.state.latitude, self.state.longitude = self._calculate_gps_offset(
            self.state.altitude,
            self.ground_lat,
            self.ground_lon
        )
        
        # Update environmental data
        self.state.temperature = self._calculate_temperature(self.state.altitude)
        self.state.pressure = self._calculate_pressure(self.state.altitude)
        self.state.humidity = max(20, 80 - self.state.altitude * 0.05)
        
        # Battery drain
        self.state.battery_percent = max(0, 100 - self.state.simulation_time * 0.01)
        self.state.battery_voltage = 12.6 - (100 - self.state.battery_percent) * 0.03
        
        # Signal strength varies with altitude and distance
        distance = math.sqrt(
            (self.state.altitude - self.ground_alt)**2 +
            (self.state.horizontal_velocity * 10)**2
        )
        self.state.signal_strength = -50 - distance * 0.01 + random.uniform(-5, 5)
        
        # Add some noise to measurements
        self.state.temperature += random.uniform(-0.5, 0.5)
        self.state.pressure += random.uniform(-1, 1)
        
        self._notify_callbacks()


class SimulationMode:
    """Simulation operational mode with accurate physics"""

    def __init__(self):
        self.logger = logging.getLogger(__name__) # Initialize logger
        self.name = "Simulation-Only Mode"
        self.description = "Accurate physics-based CanSat simulation with real-time telemetry"
        self.physics = PhysicsEngine()
        self.running = False
        self.thread = None
        self.data_history = []
        self.max_history = 1000
        self.mode_manager = get_mode_manager() # Initialize mode manager
        
    def start(self) -> bool:
        """Start the simulation mode"""
        self.logger.info(f"Starting {self.name}...")
        self.logger.info(self.description)
        
        # Set mode in manager
        if self.mode_manager:
            try:
                self.mode_manager.set_mode(OperationalMode.SIMULATION_ONLY)
            except:
                pass
        
        self.logger.info(f"📊 Physics Engine: {'✓' if self.physics else '✗'}")
        self.logger.info(f"📊 Update Rate: {self.physics.update_rate} Hz")
        self.logger.info(f"📊 Ground Station: ({self.physics.ground_lat:.4f}, {self.physics.ground_lon:.4f})")
        self.logger.info(f"📋 Flight Phases: PRE_LAUNCH → LAUNCH → ASCENT → APOGEE → DESCENT → RECOVERY")
        self.logger.info(f"⏱️  Starting simulation in 3 seconds...")
        time.sleep(3)
        
        self.running = True
        self.physics.start_simulation(launch_delay=2.0)
        
        # Start update thread
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("✅ Simulation started successfully!")
        self.logger.info("   Press Ctrl+C to stop simulation")
        
        return True    
    def _simulation_loop(self):
        """Main simulation loop"""
        dt = 1.0 / self.physics.update_rate
        last_display = time.time()
        
        while self.running:
            self.physics.update_physics(dt)
            
            # Display status every second
            if time.time() - last_display >= 1.0:
                self._display_status()
                last_display = time.time()
                
            time.sleep(dt)
    
    def _display_status(self):
        """Display current simulation status"""
        state = self.physics.get_state_dict()
        
        phase_colors = {
            'PRE_LAUNCH': '⏸️',
            'LAUNCH': '🔥',
            'ASCENT': '⬆️',
            'APOGEE': '🎯',
            'DESCENT': '⬇️',
            'RECOVERY': '✅'
        }
        
        phase_icon = phase_colors.get(state['flight_phase'], '❓')
        
        self.logger.info(f"\n{'─'*50}")
        self.logger.info(f"{phase_icon} {state['flight_phase']:12} | Time: {state['simulation_time']:6.1f}s")
        self.logger.info(f"{'─'*50}")
        self.logger.info(f"  Altitude:    {state['altitude']:>10.2f} m")
        self.logger.info(f"  Velocity:    {state['vertical_velocity']:>10.2f} m/s")
        self.logger.info(f"  Accel:       {state['acceleration_g']:>10.3f} g")
        self.logger.info(f"  Mach:        {state['mach_number']:>10.3f}")
        self.logger.info(f"  Temp:        {state['temperature']:>10.2f} °C")
        self.logger.info(f"  Pressure:    {state['pressure']:>10.2f} hPa")
        self.logger.info(f"  Battery:     {state['battery_percent']:>10.1f} %")
        self.logger.info(f"  Signal:      {state['signal_strength']:>10.1f} dBm")
        self.logger.info(f"  GPS:         {state['latitude']:.6f}, {state['longitude']:.6f}")
        
        # Store in history
        self.data_history.append(state)
        if len(self.data_history) > self.max_history:
            self.data_history.pop(0)    
    def stop(self):
        """Stop the simulation"""
        self.running = False
        self.physics.stop_simulation()
        if self.thread:
            self.thread.join(timeout=2.0)
        self.logger.info("🛑 Simulation stopped")    
    def get_telemetry(self) -> Dict[str, Any]:
        """Get current telemetry data"""
        return self.physics.get_state_dict()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics"""
        if not self.data_history:
            return {}
            
        altitudes = [d['altitude'] for d in self.data_history]
        velocities = [d['vertical_velocity'] for d in self.data_history]
        
        return {
            'max_altitude': max(altitudes),
            'max_velocity': max(velocities),
            'min_velocity': min(velocities),
            'total_samples': len(self.data_history),
            'simulation_duration': self.data_history[-1]['simulation_time'] if self.data_history else 0
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        stats = self.get_statistics()
        return {
            'running': self.running,
            'physics_engine': 'active' if self.physics else 'inactive',
            'update_rate_hz': self.physics.update_rate,
            'statistics': stats
        }


def run_standalone():
    """Run simulation in standalone mode"""
    sim = SimulationMode()
    try:
        sim.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sim.stop()


if __name__ == "__main__":
    run_standalone()
