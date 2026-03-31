#!/usr/bin/env python3
"""
AirOne v4.0 - Flight Controller
=================================

Real flight control simulation and monitoring.
"""

import sys
import time
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


class FlightController:
    """Advanced Flight Controller"""
    
    def __init__(self):
        self.position = {"latitude": 42.0, "longitude": -75.0, "altitude": 0.0, "heading": 0.0}
        self.velocity = {"horizontal": 0.0, "vertical": 0.0, "speed": 0.0}
        self.orientation = {"pitch": 0.0, "roll": 0.0, "yaw": 0.0}
        self.environment = {"temperature": 20.0, "pressure": 1013.25, "density": 1.225, "wind_speed": 5.0}
        self.params = {"mass": 1.0, "wing_area": 0.1, "lift_coef": 0.8, "drag_coef": 0.05, "thrust": 0.0, "max_thrust": 10.0}
        self.limits = {"max_altitude": 3000.0, "max_speed": 50.0, "max_vertical_speed": 10.0}
        self.status = "GROUND"
        self.mission_time = 0.0
        self.battery = 100.0
        
    def update(self, dt: float = 0.1):
        """Update flight simulation"""
        thrust = self.params["thrust"]
        dynamic_pressure = 0.5 * self.environment["density"] * self.velocity["speed"] ** 2
        lift = dynamic_pressure * self.params["wing_area"] * self.params["lift_coef"]
        drag = 0.5 * self.environment["density"] * self.velocity["speed"] ** 2 * self.params["wing_area"] * self.params["drag_coef"]
        gravity = 9.81 * self.params["mass"]
        net_force = thrust - drag - gravity * math.sin(math.radians(self.orientation["pitch"]))
        acceleration = net_force / self.params["mass"]
        self.velocity["speed"] += acceleration * dt
        self.velocity["speed"] = max(0, min(self.velocity["speed"], self.limits["max_speed"]))
        vertical_component = math.sin(math.radians(self.orientation["pitch"]))
        self.velocity["vertical"] = self.velocity["speed"] * vertical_component
        self.position["altitude"] += self.velocity["vertical"] * dt
        self.position["altitude"] = max(0, self.position["altitude"])
        if self.velocity["speed"] > 0.1:
            horizontal_speed = self.velocity["speed"] * math.cos(math.radians(self.orientation["pitch"]))
            heading_rad = math.radians(self.position["heading"])
            lat_change = horizontal_speed * math.cos(heading_rad) * dt / 111320
            lon_change = horizontal_speed * math.sin(heading_rad) * dt / (111320 * math.cos(math.radians(self.position["latitude"])))
            self.position["latitude"] += lat_change
            self.position["longitude"] += lon_change
        self.orientation["yaw"] = self.position["heading"]
        self.environment["temperature"] = max(-50, 20.0 - self.position["altitude"] * 0.0065)
        self.environment["pressure"] = max(100, 1013.25 * (1 - 0.0065 * self.position["altitude"] / 288.15) ** 5.2561)
        self.environment["density"] = self.environment["pressure"] / (287.05 * (self.environment["temperature"] + 273.15))
        self.environment["wind_speed"] = max(0, min(20, self.environment["wind_speed"] + random.uniform(-0.5, 0.5)))
        if self.position["altitude"] < 1.0:
            self.status = "GROUND"
        elif self.velocity["vertical"] > 1.0:
            self.status = "ASCENT"
        elif self.velocity["vertical"] < -1.0:
            self.status = "DESCENT"
        else:
            self.status = "CRUISE"
        self.mission_time += dt
        self.battery = max(0, self.battery - thrust * 0.01 * dt)
        
    def set_thrust(self, thrust: float):
        self.params["thrust"] = thrust * self.params["max_thrust"]
        
    def set_pitch(self, pitch: float):
        self.orientation["pitch"] = max(-45, min(45, pitch))
        
    def set_heading(self, heading: float):
        self.position["heading"] = heading % 360
        
    def get_state(self) -> Dict[str, Any]:
        return {"timestamp": datetime.now().isoformat(), "position": self.position.copy(), "velocity": self.velocity.copy(), "orientation": self.orientation.copy(), "status": self.status, "mission_time": round(self.mission_time, 2), "battery": round(self.battery, 1)}
        
    def get_telemetry(self) -> Dict[str, Any]:
        return {"altitude": round(self.position["altitude"], 2), "speed": round(self.velocity["speed"], 2), "vertical_speed": round(self.velocity["vertical"], 2), "latitude": round(self.position["latitude"], 6), "longitude": round(self.position["longitude"], 6), "heading": round(self.position["heading"], 1), "temperature": round(self.environment["temperature"], 1), "pressure": round(self.environment["pressure"], 1), "battery": round(self.battery, 1), "status": self.status, "mission_time": round(self.mission_time, 1)}


class Autopilot:
    """Autopilot System"""
    
    def __init__(self, flight_controller: FlightController):
        self.fc = flight_controller
        self.enabled = False
        self.mode = "MANUAL"
        self.target_altitude = 500.0
        self.target_heading = 0.0
        self.target_speed = 20.0
        
    def enable(self, mode: str = "ALTITUDE_HOLD"):
        self.enabled = True
        self.mode = mode
        
    def disable(self):
        self.enabled = False
        self.mode = "MANUAL"
        
    def update(self):
        if not self.enabled:
            return
        if self.mode == "ALTITUDE_HOLD":
            error = self.target_altitude - self.fc.position["altitude"]
            self.fc.set_pitch(error / 50)
            heading_error = (self.target_heading - self.fc.position["heading"] + 180) % 360 - 180
            self.fc.orientation["roll"] = heading_error / 20
            speed_error = self.target_speed - self.fc.velocity["speed"]
            self.fc.set_thrust(max(0, min(1, speed_error / 20)))


if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║              AirOne v4.0 - Flight Controller              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    fc = FlightController()
    ap = Autopilot(fc)
    print("Flight Controller Initialized")
    print(f"Initial Status: {fc.status}")
    print("\nEnabling Autopilot (Altitude Hold at 500m)...")
    ap.enable("ALTITUDE_HOLD")
    ap.set_target_altitude(500.0)
    ap.set_target_speed(25.0)
    print("\nSimulating flight for 30 seconds...\n")
    for t in range(300):
        ap.update()
        fc.update(0.1)
        if t % 30 == 0:
            state = fc.get_telemetry()
            print(f"t={state['mission_time']:6.1f}s | Alt: {state['altitude']:7.1f}m | Speed: {state['speed']:5.1f}m/s | Status: {state['status']}")
    print("\n" + "=" * 60)
    final_state = fc.get_state()
    print(f"Final Position: {final_state['position']['latitude']:.6f}, {final_state['position']['longitude']:.6f}")
    print(f"Final Altitude: {final_state['position']['altitude']:.1f}m")
    print(f"Flight Time: {final_state['mission_time']:.1f}s")
    print(f"Battery: {final_state['battery']:.1f}%")
    print("=" * 60)
