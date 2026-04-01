"""
Autonomous Control Module - Full Implementation
Self-governing flight and decision systems
"""

import numpy as np
import time
from typing import Dict, List, Tuple
from collections import deque


class FlightController:
    """Autonomous flight controller"""
    
    def __init__(self):
        self.target_position = None
        self.current_position = {'lat': 0, 'lon': 0, 'alt': 0}
        self.control_limits = {
            'max_pitch': 30,
            'max_roll': 45,
            'max_yaw_rate': 90
        }
        self.state = 'IDLE'
    
    def set_target(self, lat: float, lon: float, alt: float):
        self.target_position = {'lat': lat, 'lon': lon, 'alt': alt}
        self.state = 'ACTIVE'
    
    def compute_control(self, current: Dict) -> Dict:
        if not self.target_position:
            return {'pitch': 0, 'roll': 0, 'yaw': 0}
        
        dlat = self.target_position['lat'] - current['lat']
        dlon = self.target_position['lon'] - current['lon']
        dalt = self.target_position['alt'] - current['alt']
        
        # Heading error
        heading_error = np.degrees(np.arctan2(dlon, dlat))
        
        # Pitch from altitude error
        pitch = np.clip(dalt * 2, -self.control_limits['max_pitch'], self.control_limits['max_pitch'])
        
        # Roll from heading error
        roll = np.clip(heading_error * 1.5, -self.control_limits['max_roll'], self.control_limits['max_roll'])
        
        return {'pitch': pitch, 'roll': roll, 'yaw': 0, 'throttle': 50}


class DecisionEngine:
    """Make decisions based on state"""
    
    def __init__(self):
        self.rules = []
        self.decision_history = deque(maxlen=50)
    
    def add_rule(self, condition: callable, action: str):
        self.rules.append({'condition': condition, 'action': action})
    
    def evaluate(self, state: Dict) -> List[str]:
        decisions = []
        for rule in self.rules:
            if rule['condition'](state):
                decisions.append(rule['action'])
        self.decision_history.append({'time': time.time(), 'decisions': decisions})
        return decisions
    
    def get_emergency_actions(self, state: Dict) -> List[str]:
        if state.get('altitude', 100) < 20:
            return ['DEPLOY_PARACHUTE', 'CUT_MAIN']
        if state.get('battery', 8) < 6.5:
            return ['REDUCE_POWER', 'EMERGENCY_LANDING']
        if state.get('temperature', 20) > 70:
            return ['REDUCE_POWER', 'EMERGENCY_DESCENT']
        return []


class PathPlanner:
    """Plan flight paths"""
    
    def __init__(self):
        self.waypoints = []
        self.current_waypoint = 0
    
    def add_waypoint(self, lat: float, lon: float, alt: float, action: str = 'PASS'):
        self.waypoints.append({'lat': lat, 'lon': lon, 'alt': alt, 'action': action})
    
    def get_next_waypoint(self) -> Dict:
        if self.current_waypoint < len(self.waypoints):
            return self.waypoints[self.current_waypoint]
        return None
    
    def advance(self):
        if self.current_waypoint < len(self.waypoints) - 1:
            self.current_waypoint += 1
    
    def plan_trajectory(self, start: Dict, obstacles: List[Dict]) -> List[Dict]:
        # Simple A* inspired path
        path = [start]
        for obs in obstacles:
            # Avoid obstacle
            if self._is_collision(path[-1], obs):
                path.append(self._avoid_obstacle(path[-1], obs))
        return path
    
    def _is_collision(self, pos: Dict, obs: Dict) -> bool:
        dlat = pos.get('lat', 0) - obs.get('lat', 0)
        dlon = pos.get('lon', 0) - obs.get('lon', 0)
        dalt = pos.get('alt', 0) - obs.get('alt', 0)
        return np.sqrt(dlat**2 + dlon**2 + dalt**2) < obs.get('radius', 100)
    
    def _avoid_obstacle(self, pos: Dict, obs: Dict) -> Dict:
        return {'lat': pos['lat'] + 0.001, 'lon': pos['lon'] + 0.001, 'alt': pos['alt']}


class StateMachine:
    """Flight state machine"""
    
    def __init__(self):
        self.states = ['IDLE', 'LAUNCH', 'ASCENT', 'DESCENT', 'LANDING', 'RECOVERY']
        self.current = 'IDLE'
        self.transitions = {
            ('IDLE', 'LAUNCH'): lambda s: s.get('altitude', 0) > 0,
            ('LAUNCH', 'ASCENT'): lambda s: s.get('vertical_speed', 0) > 5,
            ('ASCENT', 'DESCENT'): lambda s: s.get('vertical_speed', 0) < 0,
            ('DESCENT', 'LANDING'): lambda s: s.get('altitude', 100) < 50,
            ('LANDING', 'RECOVERY'): lambda s: s.get('altitude', 10) < 5
        }
    
    def update(self, state: Dict):
        for (from_state, to_state), condition in self.transitions.items():
            if self.current == from_state and condition(state):
                self.current = to_state
                return to_state
        return self.current
    
    def get_state(self) -> str:
        return self.current


class SafetyMonitor:
    """Monitor safety constraints"""
    
    def __init__(self):
        self.limits = {
            'max_altitude': 30000,
            'min_altitude': 0,
            'max_speed': 50,
            'max_vertical_speed': 20
        }
        self.violations = []
    
    def check(self, telemetry: Dict) -> List[str]:
        warnings = []
        
        alt = telemetry.get('altitude', 0)
        if alt > self.limits['max_altitude']:
            warnings.append('ALTITUDE_EXCEEDED')
            self.violations.append(('ALTITUDE', time.time()))
        
        if alt < self.limits['min_altitude']:
            warnings.append('ALTITUDE_UNDER')
        
        speed = telemetry.get('horizontal_speed', 0)
        if speed > self.limits['max_speed']:
            warnings.append('SPEED_EXCEEDED')
        
        v_speed = telemetry.get('vertical_speed', 0)
        if abs(v_speed) > self.limits['max_vertical_speed']:
            warnings.append('VERTICAL_SPEED_EXCEEDED')
        
        return warnings
    
    def is_safe(self, telemetry: Dict) -> bool:
        return len(self.check(telemetry)) == 0


class EmergencyHandler:
    """Handle emergency situations"""
    
    def __init__(self):
        self.emergency_state = 'NONE'
        self.response_actions = []
    
    def trigger_emergency(self, emergency_type: str):
        self.emergency_state = emergency_type
        
        responses = {
            'LOSS_OF_SIGNAL': ['ENABLE_BEACON', 'ACTIVATE_SAFE_MODE', 'WAIT_TIMEOUT'],
            'LOW_BATTERY': ['REDUCE_POWER', 'EMERGENCY_LANDING', 'ENABLE_BEACON'],
            'SENSOR_FAILURE': ['SWITCH_TO_BACKUP', 'USE_ESTIMATED', 'SAFE_DESCENT'],
            'GPS_FAILURE': ['SWITCH_TO_VIO', 'HOLD_POSITION', 'DESCENT']
        }
        
        self.response_actions = responses.get(emergency_type, ['SAFE_DESCENT'])
    
    def get_actions(self) -> List[str]:
        return self.response_actions
    
    def clear_emergency(self):
        self.emergency_state = 'NONE'
        self.response_actions = []


if __name__ == "__main__":
    fc = FlightController()
    fc.set_target(51.5, -0.1, 500)
    print(f"Control: {fc.compute_control({'lat': 51.4, 'lon': -0.09, 'alt': 400})}")