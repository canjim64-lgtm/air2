"""
AirOne Professional v4.0 - Mission Control Center
Real-time mission monitoring and control interface
"""
# -*- coding: utf-8 -*-

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from threading import Thread
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissionState:
    """Mission states"""
    IDLE = "IDLE"
    PRE_LAUNCH = "PRE_LAUNCH"
    LAUNCH = "LAUNCH"
    ASCENT = "ASCENT"
    APOGEE = "APOGEE"
    DESCENT = "DESCENT"
    LANDING = "LANDING"
    RECOVERY = "RECOVERY"
    ABORTED = "ABORTED"


class MissionControl:
    """Mission control center"""
    
    def __init__(self, config_file: str = "config/mission_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.state = MissionState.IDLE
        self.mission_data: Dict[str, Any] = {}
        self.telemetry_history: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False
        self.monitor_thread: Optional[Thread] = None
        
    def _load_config(self) -> Dict:
        """Load mission configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'mission': {
                'name': 'Default Mission',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'location': {
                    'latitude': 40.7128,
                    'longitude': -74.0060,
                    'altitude': 10
                }
            },
            'thresholds': {
                'max_altitude': 1000,
                'max_velocity': 100,
                'min_battery': 20,
                'min_signal': -90
            },
            'telemetry': {
                'update_interval': 1,
                'history_size': 1000
            }
        }
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register event callback"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
        logger.info(f"Registered callback for {event_type}")
    
    def _trigger_event(self, event_type: str, data: Any = None):
        """Trigger event callbacks"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Callback error for {event_type}: {e}")
    
    def start_mission(self, mission_name: Optional[str] = None):
        """Start mission"""
        if self.state != MissionState.IDLE:
            logger.warning(f"Cannot start mission - current state: {self.state}")
            return False
        
        self.state = MissionState.PRE_LAUNCH
        self._add_event("Mission started", "info")
        
        if mission_name:
            self.config['mission']['name'] = mission_name
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Mission started: {mission_name or self.config['mission']['name']}")
        self._trigger_event('mission_start', {'name': mission_name})
        
        return True
    
    def stop_mission(self, reason: str = ""):
        """Stop mission"""
        self.running = False
        self.state = MissionState.IDLE
        self._add_event(f"Mission stopped: {reason}", "warning")
        
        logger.info(f"Mission stopped: {reason}")
        self._trigger_event('mission_stop', {'reason': reason})
    
    def abort_mission(self, reason: str = "Emergency"):
        """Abort mission"""
        self.state = MissionState.ABORTED
        self._add_event(f"MISSION ABORTED: {reason}", "critical")
        
        logger.critical(f"Mission aborted: {reason}")
        self._trigger_event('mission_abort', {'reason': reason})
    
    def _monitor_loop(self):
        """Monitoring loop"""
        while self.running:
            try:
                # Update state based on telemetry
                self._update_state()
                
                # Generate simulated telemetry
                telemetry = self._generate_telemetry()
                self.telemetry_history.append(telemetry)
                
                # Check thresholds
                self._check_thresholds(telemetry)
                
                # Limit history size
                if len(self.telemetry_history) > self.config['telemetry']['history_size']:
                    self.telemetry_history = self.telemetry_history[-self.config['telemetry']['history_size']:]
                
                time.sleep(self.config['telemetry']['update_interval'])
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(1)
    
    def _update_state(self):
        """Update mission state"""
        if not self.telemetry_history:
            return
        
        latest = self.telemetry_history[-1]
        altitude = latest.get('altitude', 0)
        velocity = latest.get('velocity', 0)
        
        # State machine
        if self.state == MissionState.PRE_LAUNCH:
            if altitude > 10:
                self.state = MissionState.LAUNCH
                self._add_event("Launch detected", "info")
        
        elif self.state == MissionState.LAUNCH:
            if velocity > 0 and altitude > 100:
                self.state = MissionState.ASCENT
                self._add_event("Ascent phase", "info")
        
        elif self.state == MissionState.ASCENT:
            if velocity <= 0:
                self.state = MissionState.APOGEE
                self._add_event("Apogee reached", "success")
        
        elif self.state == MissionState.APOGEE:
            if velocity < 0:
                self.state = MissionState.DESCENT
                self._add_event("Descent phase", "info")
        
        elif self.state == MissionState.DESCENT:
            if altitude < 100:
                self.state = MissionState.LANDING
                self._add_event("Landing phase", "info")
        
        elif self.state == MissionState.LANDING:
            if altitude < 5:
                self.state = MissionState.RECOVERY
                self._add_event("Mission completed - ready for recovery", "success")
    
    def _generate_telemetry(self) -> Dict[str, Any]:
        """Generate simulated telemetry"""
        base_time = datetime.now()
        
        # Simulate flight profile
        if self.telemetry_history:
            last = self.telemetry_history[-1]
            altitude = last.get('altitude', 0)
            velocity = last.get('velocity', 0)
            
            # Simple physics simulation
            if self.state in [MissionState.LAUNCH, MissionState.ASCENT]:
                velocity += random.uniform(0.5, 2)
                altitude += velocity
            elif self.state in [MissionState.DESCENT, MissionState.LANDING]:
                velocity -= random.uniform(0.3, 1)
                altitude += velocity
            else:
                velocity = random.uniform(-5, 5)
                altitude = max(0, altitude + velocity)
        else:
            altitude = 0
            velocity = 0
        
        return {
            'timestamp': base_time.isoformat(),
            'altitude': max(0, min(altitude, 1500)),
            'velocity': max(-50, min(velocity, 150)),
            'temperature': 25 + random.uniform(-2, 2) - (altitude / 100),
            'pressure': 1013.25 - (altitude / 10) + random.uniform(-1, 1),
            'battery': max(0, 100 - (len(self.telemetry_history) / 100)),
            'signal': random.randint(-80, -40),
            'latitude': self.config['mission']['location']['latitude'] + random.uniform(-0.001, 0.001),
            'longitude': self.config['mission']['location']['longitude'] + random.uniform(-0.001, 0.001),
            'flight_phase': self.state
        }
    
    def _check_thresholds(self, telemetry: Dict[str, Any]):
        """Check telemetry thresholds"""
        thresholds = self.config['thresholds']
        
        if telemetry['altitude'] > thresholds['max_altitude']:
            self._add_event(f"Altitude warning: {telemetry['altitude']:.1f}m", "warning")
        
        if telemetry['velocity'] > thresholds['max_velocity']:
            self._add_event(f"Velocity warning: {telemetry['velocity']:.1f}m/s", "warning")
        
        if telemetry['battery'] < thresholds['min_battery']:
            self._add_event(f"Battery critical: {telemetry['battery']:.1f}%", "critical")
        
        if telemetry['signal'] < thresholds['min_signal']:
            self._add_event(f"Signal weak: {telemetry['signal']}dBm", "warning")
    
    def _add_event(self, message: str, level: str = "info"):
        """Add mission event"""
        event = {
            'id': len(self.events),
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level,
            'state': self.state
        }
        self.events.append(event)
        logger.info(f"Event: {message} ({level})")
    
    def get_current_telemetry(self) -> Dict[str, Any]:
        """Get current telemetry"""
        if self.telemetry_history:
            return self.telemetry_history[-1]
        return {}
    
    def get_mission_status(self) -> Dict[str, Any]:
        """Get mission status"""
        return {
            'state': self.state,
            'mission_name': self.config['mission']['name'],
            'start_time': self.events[0]['timestamp'] if self.events else None,
            'duration_seconds': len(self.telemetry_history) * self.config['telemetry']['update_interval'],
            'telemetry_count': len(self.telemetry_history),
            'event_count': len(self.events),
            'current_telemetry': self.get_current_telemetry(),
            'recent_events': self.events[-10:]
        }
    
    def get_telemetry_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get telemetry history"""
        return self.telemetry_history[-limit:]
    
    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get mission events"""
        return self.events[-limit:]
    
    def export_mission_data(self, filename: Optional[str] = None) -> str:
        """Export mission data to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mission_export_{timestamp}.json"
        
        filepath = Path("exports") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        data = {
            'mission': self.config['mission'],
            'status': self.get_mission_status(),
            'telemetry': self.telemetry_history,
            'events': self.events,
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Mission data exported to: {filepath}")
        return str(filepath)


# Global mission control instance
_mission_control: Optional[MissionControl] = None


def get_mission_control() -> MissionControl:
    """Get mission control instance"""
    global _mission_control
    if _mission_control is None:
        _mission_control = MissionControl()
    return _mission_control


def start_mission(name: str = "Mission"):
    """Quick function to start mission"""
    mc = get_mission_control()
    return mc.start_mission(name)


def get_status() -> Dict[str, Any]:
    """Quick function to get mission status"""
    return get_mission_control().get_mission_status()


if __name__ == "__main__":
    # Test mission control
    print("="*70)
    print("  AirOne Professional v4.0 - Mission Control Center Test")
    print("="*70)
    print()
    
    mc = MissionControl()
    
    # Register callbacks
    def on_start(data):
        print(f"  [CALLBACK] Mission started: {data['name']}")
    
    def on_event(data):
        print(f"  [CALLBACK] Event: {data}")
    
    mc.register_callback('mission_start', on_start)
    
    # Start mission
    print("Starting mission...")
    mc.start_mission("Test Flight 001")
    
    # Monitor for 10 seconds
    print("Monitoring mission (10 seconds)...")
    for i in range(10):
        status = mc.get_mission_status()
        telemetry = status.get('current_telemetry', {})
        print(f"  [{i+1}s] State: {status['state']}, Alt: {telemetry.get('altitude', 0):.1f}m, Vel: {telemetry.get('velocity', 0):.1f}m/s")
        time.sleep(1)
    
    # Get status
    print()
    print("Mission Status:")
    status = mc.get_mission_status()
    print(f"  State: {status['state']}")
    print(f"  Duration: {status['duration_seconds']}s")
    print(f"  Telemetry points: {status['telemetry_count']}")
    print(f"  Events: {status['event_count']}")
    
    # Stop mission
    print()
    print("Stopping mission...")
    mc.stop_mission("Test completed")
    
    print()
    print("="*70)
    print("  Mission Control Test Complete")
    print("="*70)
