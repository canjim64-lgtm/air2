"""
Advanced Mission Control System
================================

Complete mission control with real-time monitoring, autonomous
decision-making, and intelligent recovery systems.

Features:
- Real-time mission monitoring
- Autonomous decision engine
- Recovery system coordination
- Multi-mission support

Author: AirOne Professional Development Team
Version: 4.0
"""

import numpy as np
import json
import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from collections import deque
from datetime import datetime, timedelta
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlightPhase:
    """Flight phase definitions"""
    PRE_LAUNCH = "pre_launch"
    LAUNCH = "launch"
    ASCENT = "ascent"
    APOGEE = "apogee"
    DESCENT = "descent"
    RECOVERY = "recovery"
    LANDED = "landed"


class MissionState:
    """
    Complete mission state tracking.
    """
    
    def __init__(self, mission_id: str = "default"):
        self.mission_id = mission_id
        self.phase = FlightPhase.PRE_LAUNCH
        self.start_time = None
        self.end_time = None
        
        # Telemetry tracking
        self.max_altitude = 0
        self.min_altitude = 0
        self.peak_velocity = 0
        self.ground_speed = 0
        
        # Location tracking
        self.launch_lat = 0
        self.launch_lon = 0
        self.current_lat = 0
        self.current_lon = 0
        self.current_alt = 0
        
        # Status tracking
        self.parachute_deployed = False
        self.antenna_deployed = False
        self.camera_active = False
        
        # Events
        self.events = []
        self.alerts = []
        
        # Timing
        self.apogee_time = None
        self.descent_start_time = None
        self.landing_time = None
        
        logger.info(f"Mission {mission_id} created in PRE_LAUNCH phase")
    
    def update(self, telemetry: Dict[str, Any]):
        """Update mission state with new telemetry."""
        # Update altitude
        self.current_alt = telemetry.get('altitude', 0)
        if self.current_alt > self.max_altitude:
            self.max_altitude = self.current_alt
            
        # Update velocity
        velocity = telemetry.get('velocity', 0)
        if abs(velocity) > abs(self.peak_velocity):
            self.peak_velocity = velocity
            
        # Update location
        self.current_lat = telemetry.get('gps_lat', self.current_lat)
        self.current_lon = telemetry.get('gps_lon', self.current_lon)
        
        # Determine phase
        self._update_phase(telemetry)
    
    def _update_phase(self, telemetry: Dict[str, Any]):
        """Update flight phase based on telemetry."""
        velocity = telemetry.get('velocity', 0)
        altitude = telemetry.get('altitude', 0)
        
        if self.phase == FlightPhase.PRE_LAUNCH:
            if altitude > 100:  # Launched
                self.phase = FlightPhase.LAUNCH
                self._add_event("LAUNCH", "CanSat launched", "INFO")
                
        elif self.phase == FlightPhase.LAUNCH:
            if velocity < 0:  # Started descending
                self.phase = FlightPhase.ASCENT
                
        elif self.phase == FlightPhase.ASCENT:
            if velocity >= 0 and altitude > 500:  # Reached apogee
                self.phase = FlightPhase.APOGEE
                self.apogee_time = time.time()
                self._add_event("APOGEE", f"Apogee reached: {self.max_altitude:.0f}m", "INFO")
                
        elif self.phase == FlightPhase.APOGEE:
            if velocity < -5:  # Started descent
                self.phase = FlightPhase.DESCENT
                self.descent_start_time = time.time()
                self._add_event("DESCENT", "Descent started", "INFO")
                
        elif self.phase == FlightPhase.DESCENT:
            if altitude < 50:  # Near ground
                self.phase = FlightPhase.RECOVERY
                self._add_event("RECOVERY", "Recovery phase initiated", "INFO")
                
        elif self.phase == FlightPhase.RECOVERY:
            if altitude <= 0:
                self.phase = FlightPhase.LANDED
                self.landing_time = time.time()
                self.end_time = self.landing_time
                self._add_event("LANDED", "CanSat has landed", "CRITICAL")
    
    def _add_event(self, event_type: str, description: str, severity: str):
        """Add event to log."""
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'description': description,
            'severity': severity,
            'altitude': self.current_alt,
            'phase': self.phase
        }
        self.events.append(event)
        logger.info(f"Mission Event [{severity}]: {event_type} - {description}")
    
    def add_alert(self, alert_type: str, message: str, severity: str = "WARNING"):
        """Add alert to mission."""
        alert = {
            'timestamp': time.time(),
            'type': alert_type,
            'message': message,
            'severity': severity,
            'phase': self.phase,
            'altitude': self.current_alt
        }
        self.alerts.append(alert)
        logger.warning(f"Mission Alert [{severity}]: {message}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get mission summary."""
        duration = 0
        if self.start_time:
            end = self.end_time or time.time()
            duration = end - self.start_time
        
        return {
            'mission_id': self.mission_id,
            'phase': self.phase,
            'duration_sec': duration,
            'max_altitude': self.max_altitude,
            'peak_velocity': self.peak_velocity,
            'current_position': {
                'lat': self.current_lat,
                'lon': self.current_lon,
                'alt': self.current_alt
            },
            'events_count': len(self.events),
            'alerts_count': len(self.alerts),
            'parachute_deployed': self.parachute_deployed
        }


class DecisionEngine:
    """
    Autonomous decision-making engine.
    Makes decisions based on AI analysis and mission rules.
    """
    
    def __init__(self, mission_state: MissionState):
        self.mission = mission_state
        self.rules = []
        self.ai_enabled = True
        
        # Default decision thresholds
        self.thresholds = {
            'max_descent_rate': 25,  # m/s
            'min_battery_voltage': 3.0,  # V
            'max_altitude_change': 100,  # m/s (for anomaly detection)
            'min_rssi': -90  # dBm
        }
        
        # Decision history
        self.decisions = deque(maxlen=100)
        
        logger.info("Decision Engine initialized")
    
    def evaluate(self, telemetry: Dict[str, Any], 
                 ai_analysis: Optional[Dict] = None) -> List[Dict]:
        """
        Evaluate conditions and make decisions.
        
        Args:
            telemetry: Current telemetry
            ai_analysis: Optional AI system analysis results
            
        Returns:
            List of decisions made
        """
        decisions = []
        
        # 1. Check descent rate (parachute deployment decision)
        velocity = telemetry.get('velocity', 0)
        if velocity < -self.thresholds['max_descent_rate'] and not self.mission.parachute_deployed:
            decision = {
                'type': 'PARACHUTE_CHECK',
                'action': 'Verify parachute deployment',
                'reason': f"Descent rate {abs(velocity):.1f} m/s exceeds threshold",
                'priority': 'HIGH'
            }
            decisions.append(decision)
            self.mission.add_alert('DESCENT_RATE', decision['reason'])
        
        # 2. Check battery voltage
        voltage = telemetry.get('voltage', 0)
        if voltage < self.thresholds['min_battery_voltage']:
            decision = {
                'type': 'LOW_BATTERY',
                'action': 'Initiate power conservation',
                'reason': f"Battery voltage {voltage:.2f}V below threshold",
                'priority': 'CRITICAL'
            }
            decisions.append(decision)
            self.mission.add_alert('BATTERY', decision['reason'], 'CRITICAL')
        
        # 3. Check signal strength
        rssi = telemetry.get('rssi', 0)
        if rssi < self.thresholds['min_rssi']:
            decision = {
                'type': 'WEAK_SIGNAL',
                'action': 'Increase transmission power / adjust antenna',
                'reason': f"RSSI {rssi}dBm below threshold",
                'priority': 'MEDIUM'
            }
            decisions.append(decision)
        
        # 4. Check altitude anomaly (if AI analysis available)
        if ai_analysis and 'systems' in ai_analysis:
            systems = ai_analysis['systems']
            
            # Autoencoder anomaly
            if 'autoencoder' in systems:
                if systems['autoencoder'].get('anomaly', False):
                    decision = {
                        'type': 'ANOMALY_DETECTED',
                        'action': 'Log anomaly and continue monitoring',
                        'reason': f"AI detected anomaly: {systems['autoencoder'].get('severity', 'unknown')}",
                        'priority': 'HIGH'
                    }
                    decisions.append(decision)
            
            # Physics violation
            if 'physics_analysis' in systems:
                if not systems['physics_analysis'].get('physics_compliant', True):
                    decision = {
                        'type': 'PHYSICS_VIOLATION',
                        'action': 'Switch to backup sensors',
                        'reason': "Telemetry violates physics constraints",
                        'priority': 'CRITICAL'
                    }
                    decisions.append(decision)
            
            # Landing prediction
            if 'landing_prediction' in systems:
                pred = systems['landing_prediction']
                pred_time = pred.get('predicted_landing_time_sec', 999)
                if pred_time < 60:
                    decision = {
                        'type': 'IMMINENT_LANDING',
                        'action': 'Prepare recovery team',
                        'reason': f"Predicted landing in {pred_time:.0f} seconds",
                        'priority': 'HIGH'
                    }
                    decisions.append(decision)
        
        # 5. Phase-specific decisions
        if self.mission.phase == FlightPhase.DESCENT and not self.mission.parachute_deployed:
            if self.mission.current_alt < 700:  # Deploy parachute below 700m
                decision = {
                    'type': 'PARACHUTE_DEPLOY',
                    'action': 'Command parachute deployment',
                    'reason': 'Altitude below 700m - standard deployment altitude',
                    'priority': 'HIGH'
                }
                decisions.append(decision)
                self.mission.parachute_deployed = True
        
        # Store decisions
        for d in decisions:
            d['timestamp'] = time.time()
            d['phase'] = self.mission.phase
            self.decisions.append(d)
        
        return decisions
    
    def set_threshold(self, key: str, value: float):
        """Update decision threshold."""
        if key in self.thresholds:
            self.thresholds[key] = value
            logger.info(f"Updated threshold: {key} = {value}")


class RecoverySystem:
    """
    Recovery coordination and tracking system.
    """
    
    def __init__(self):
        self.recovery_team_contacted = False
        self.predicted_landing_zone = None
        self.actual_landing_position = None
        self.search_radius = 500  # meters
        
        # Recovery status
        self.status = "STANDING_BY"
        self.last_update = None
        
        logger.info("Recovery System initialized")
    
    def update_prediction(self, predicted_lat: float, predicted_lon: float,
                        confidence: float, radius_m: float):
        """Update predicted landing zone."""
        self.predicted_landing_zone = {
            'latitude': predicted_lat,
            'longitude': predicted_lon,
            'confidence': confidence,
            'search_radius': radius_m,
            'timestamp': time.time()
        }
        self.last_update = time.time()
        
        logger.info(f"Landing predicted: {predicted_lat:.5f}, {predicted_lon:.5f} (conf: {confidence:.1%})")
    
    def contact_recovery_team(self, location: Dict):
        """Contact recovery team with landing info."""
        if not self.recovery_team_contacted:
            self.status = "TEAM_DISPATCHED"
            self.recovery_team_contacted = True
            logger.info(f"Recovery team dispatched to: {location}")
            return True
        return False
    
    def confirm_landing(self, lat: float, lon: float):
        """Confirm actual landing position."""
        self.actual_landing_position = {
            'latitude': lat,
            'longitude': lon,
            'timestamp': time.time()
        }
        self.status = "LANDED"
        
        if self.predicted_landing_zone:
            # Calculate accuracy
            import math
            dlat = lat - self.predicted_landing_zone['latitude']
            dlon = lon - self.predicted_landing_zone['longitude']
            distance = math.sqrt(dlat**2 + dlon**2) * 111000  # Approximate meters
            
            logger.info(f"Landing accuracy: {distance:.0f}m from prediction")
            return distance
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get recovery system status."""
        return {
            'status': self.status,
            'team_contacted': self.recovery_team_contacted,
            'predicted_zone': self.predicted_landing_zone,
            'actual_position': self.actual_landing_position,
            'search_radius': self.search_radius
        }


class MissionController:
    """
    Complete mission control system integrating all components.
    """
    
    def __init__(self, mission_id: str = "MISSION_001"):
        # Core components
        self.mission_state = MissionState(mission_id)
        self.decision_engine = DecisionEngine(self.mission_state)
        self.recovery_system = RecoverySystem()
        
        # Data management
        self.telemetry_buffer = deque(maxlen=10000)
        self.command_queue = queue.Queue()
        
        # Threading
        self.is_running = False
        self.processing_thread = None
        
        # Callbacks
        self.on_decision = None
        self.on_event = None
        self.on_alert = None
        
        # Statistics
        self.packets_received = 0
        self.decisions_made = 0
        self.start_time = None
        
        logger.info(f"Mission Controller initialized: {mission_id}")
    
    def start_mission(self):
        """Start mission operations."""
        self.is_running = True
        self.start_time = time.time()
        self.mission_state.start_time = self.start_time
        self.mission_state.phase = FlightPhase.PRE_LAUNCH
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logger.info(f"Mission {self.mission_state.mission_id} started")
    
    def stop_mission(self):
        """Stop mission operations."""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
        
        self.mission_state.end_time = time.time()
        logger.info(f"Mission {self.mission_state.mission_id} stopped")
    
    def process_telemetry(self, telemetry: Dict[str, Any], 
                         ai_analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process incoming telemetry with AI analysis.
        
        Args:
            telemetry: Raw telemetry data
            ai_analysis: Optional pre-computed AI analysis
            
        Returns:
            Processing result with decisions
        """
        self.packets_received += 1
        
        # Update mission state
        self.mission_state.update(telemetry)
        
        # Store in buffer
        self.telemetry_buffer.append({
            'timestamp': time.time(),
            'telemetry': telemetry,
            'ai_analysis': ai_analysis
        })
        
        # Run decision engine
        decisions = self.decision_engine.evaluate(telemetry, ai_analysis)
        self.decisions_made += len(decisions)
        
        # Handle decisions
        for decision in decisions:
            self._handle_decision(decision)
            
            # Callback
            if self.on_decision:
                self.on_decision(decision)
        
        # Update recovery prediction
        if 'landing_prediction' in (ai_analysis.get('systems', {}) if ai_analysis else {}):
            landing = ai_analysis['systems']['landing_prediction']
            self.recovery_system.update_prediction(
                telemetry.get('gps_lat', 0),
                telemetry.get('gps_lon', 0),
                landing.get('confidence', 0.5),
                500
            )
        
        # Build response
        result = {
            'packet_id': self.packets_received,
            'mission_state': self.mission_state.get_summary(),
            'decisions': decisions,
            'recovery_status': self.recovery_system.get_status(),
            'timestamp': time.time()
        }
        
        return result
    
    def _handle_decision(self, decision: Dict):
        """Handle a decision (send commands, etc.)."""
        # Queue command for transmission
        self.command_queue.put({
            'type': decision['type'],
            'action': decision['action'],
            'priority': decision.get('priority', 'MEDIUM'),
            'timestamp': time.time()
        })
        
        # Log event
        if decision['priority'] in ['HIGH', 'CRITICAL']:
            self.mission_state._add_event(
                decision['type'],
                decision['reason'],
                decision['priority']
            )
    
    def _processing_loop(self):
        """Background processing loop."""
        while self.is_running:
            try:
                # Process any queued commands
                if not self.command_queue.empty():
                    cmd = self.command_queue.get_nowait()
                    logger.info(f"Command: {cmd['type']} - {cmd['action']}")
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    def send_command(self, command: str, parameters: Dict = None) -> bool:
        """
        Send command to CanSat.
        
        Args:
            command: Command string
            parameters: Command parameters
            
        Returns:
            True if command sent successfully
        """
        # In production, would transmit via radio
        logger.info(f"Sending command: {command} with params: {parameters}")
        
        self.command_queue.put({
            'type': 'USER_COMMAND',
            'command': command,
            'parameters': parameters or {},
            'timestamp': time.time()
        })
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get mission statistics."""
        duration = 0
        if self.start_time:
            duration = time.time() - self.start_time
        
        return {
            'mission_id': self.mission_state.mission_id,
            'phase': self.mission_state.phase,
            'duration_sec': duration,
            'packets_received': self.packets_received,
            'decisions_made': self.decisions_made,
            'events_count': len(self.mission_state.events),
            'alerts_count': len(self.mission_state.alerts),
            'telemetry_buffer_size': len(self.telemetry_buffer),
            'pending_commands': self.command_queue.qsize()
        }
    
    def export_mission_log(self, filepath: str) -> str:
        """Export complete mission log."""
        log_data = {
            'mission_id': self.mission_state.mission_id,
            'summary': self.mission_state.get_summary(),
            'events': self.mission_state.events,
            'alerts': self.mission_state.alerts,
            'decisions': list(self.decision_engine.decisions),
            'recovery': self.recovery_system.get_status()
        }
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return f"Mission log exported to {filepath}"


def demo_mission_control():
    """Demo function for mission control system."""
    print("\n" + "="*60)
    print("  AirOne v4.0 - Mission Control System Demo")
    print("="*60)
    
    # Create mission controller
    print("\n1. Initializing Mission Controller...")
    controller = MissionController("CANARY_FLIGHT_001")
    
    # Simulate telemetry
    print("\n2. Simulating flight telemetry...")
    
    # Pre-launch
    telemetry = {'altitude': 0, 'velocity': 0, 'gps_lat': 45.0, 'gps_lon': -122.0, 'voltage': 3.7, 'rssi': -50}
    result = controller.process_telemetry(telemetry)
    print(f"   Phase: {result['mission_state']['phase']}")
    
    # Launch
    telemetry = {'altitude': 100, 'velocity': 50, 'gps_lat': 45.001, 'gps_lon': -122.0, 'voltage': 3.6, 'rssi': -55}
    result = controller.process_telemetry(telemetry)
    print(f"   Phase: {result['mission_state']['phase']}, Max Alt: {result['mission_state']['max_altitude']}m")
    
    # Ascent
    for alt in [500, 1000, 2000, 3000, 3500]:
        telemetry = {'altitude': alt, 'velocity': 30, 'gps_lat': 45.005, 'gps_lon': -122.0, 'voltage': 3.5, 'rssi': -60}
        result = controller.process_telemetry(telemetry)
    
    print(f"   Phase: {result['mission_state']['phase']}, Max Alt: {result['mission_state']['max_altitude']}m")
    
    # Apogee to descent
    for alt in [3400, 3000, 2000, 1000, 500, 200]:
        velocity = -10 if alt < 3500 else 10
        telemetry = {'altitude': alt, 'velocity': velocity, 'gps_lat': 45.01, 'gps_lon': -122.0, 'voltage': 3.4, 'rssi': -65}
        result = controller.process_telemetry(telemetry)
    
    print(f"   Phase: {result['mission_state']['phase']}")
    
    # Decisions made
    print(f"\n3. Decision Summary:")
    stats = controller.get_statistics()
    print(f"   Packets received: {stats['packets_received']}")
    print(f"   Decisions made: {stats['decisions_made']}")
    print(f"   Events logged: {stats['events_count']}")
    print(f"   Alerts: {stats['alerts_count']}")
    
    # Export log
    print("\n4. Exporting mission log...")
    controller.export_mission_log('/tmp/mission_log.json')
    print("   Exported to /tmp/mission_log.json")
    
    # Recovery status
    print("\n5. Recovery System Status:")
    recovery = result['recovery_status']
    print(f"   Status: {recovery['status']}")
    
    controller.stop_mission()
    
    print("\n" + "="*60)
    print("  Mission Control Demo Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    demo_mission_control()