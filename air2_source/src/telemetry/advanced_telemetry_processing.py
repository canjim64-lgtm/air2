"""
Advanced Telemetry Processing and Mission Control for AirOne v3.0
Implements comprehensive telemetry processing, mission control, and event detection
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
import json
import threading
import queue
import time
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import warnings
warnings.filterwarnings('ignore')


class MissionPhase(Enum):
    """Mission phases for the CanSat mission"""
    BOOT = "boot"
    SECURE_INIT = "secure_init"
    PRELAUNCH = "prelaunch"
    ASCENT = "ascent"
    APOGEE = "apogee"
    DESCENT = "descent"
    LANDED = "landed"
    ARCHIVED = "archived"
    EMERGENCY = "emergency"


class EventType(Enum):
    """Types of events that can occur during mission"""
    BOUNDARY_LAYER_TRANSITION = "boundary_layer_transition"
    ATMOSPHERIC_INVERSION_DETECTED = "atmospheric_inversion"
    PARACHUTE_DEPLOYMENT = "parachute_deployment"
    RADIATION_SPIKE = "radiation_spike"
    GAS_PLUME_DETECTED = "gas_plume_detected"
    TEMPERATURE_ANOMALY = "temperature_anomaly"
    PRESSURE_ANOMALY = "pressure_anomaly"
    ALTITUDE_MISMATCH = "altitude_mismatch"
    COMM_LINK_LOSS = "comm_link_loss"
    POWER_LOW = "power_low"
    SYSTEM_ERROR = "system_error"
    MISSION_SUCCESS = "mission_success"
    MISSION_ABORT = "mission_abort"


@dataclass
class TelemetryRecord:
    """Record of telemetry data with comprehensive fields"""
    timestamp: datetime
    packet_id: str
    session_id: str
    mission_time: float
    altitude: float
    velocity: float
    temperature: float
    pressure: float
    latitude: float
    longitude: float
    battery_level: float
    radio_signal_strength: float
    acceleration_x: float = 0.0
    acceleration_y: float = 0.0
    acceleration_z: float = 0.0
    radiation_level: float = 0.0
    gas_concentration: float = 0.0
    uv_index: float = 0.0
    magnetic_field_x: float = 0.0
    magnetic_field_y: float = 0.0
    magnetic_field_z: float = 0.0
    tvoc_ppb: float = 0.0
    eco2_ppm: float = 0.0
    humidity: float = 0.0
    co2_level: float = 0.0
    no2_level: float = 0.0
    nh3_level: float = 0.0
    checksum: str = ""
    quality: int = 4  # 0-4 scale
    encrypted: bool = False
    compression_ratio: float = 1.0
    phase: MissionPhase = MissionPhase.PRELAUNCH
    event_flags: List[EventType] = field(default_factory=list)
    additional_data: Dict[str, Any] = field(default_factory=dict)


class EventDetector:
    """Advanced event detection system for mission-critical events"""
    
    def __init__(self):
        self.event_history = []
        self.max_event_history = 1000
        self.boundary_layer_threshold = 0.5  # Rate of change threshold
        self.inversion_threshold = 0.2      # Temperature gradient threshold
        self.radiation_spike_threshold = 1.0  # Multiplier above baseline
        self.gas_plume_threshold = 2.0      # Concentration multiplier
        self.anomaly_threshold = 3.0        # Standard deviations
        
        # Baseline values for comparison
        self.baseline_temperature = 20.0
        self.baseline_radiation = 0.1
        self.baseline_gas = 400.0
        self.baseline_pressure = 1013.25
        
        # Historical data for trend analysis
        self.temp_history = []
        self.pressure_history = []
        self.altitude_history = []
        self.radiation_history = []
        self.gas_history = []
        self.max_history_size = 100
    
    def detect_events(self, record: TelemetryRecord) -> List[EventType]:
        """Detect events in the telemetry record"""
        detected_events = []
        
        # Update historical data
        self._update_history(record)
        
        # Check for boundary layer transitions (rapid altitude/temperature changes)
        if self._detect_boundary_layer_transition():
            detected_events.append(EventType.BOUNDARY_LAYER_TRANSITION)
        
        # Check for atmospheric inversions
        if self._detect_atmospheric_inversion():
            detected_events.append(EventType.ATMOSPHERIC_INVERSION_DETECTED)
        
        # Check for parachute deployment (sudden velocity change)
        if self._detect_parachute_deployment():
            detected_events.append(EventType.PARACHUTE_DEPLOYMENT)
        
        # Check for radiation spikes
        if self._detect_radiation_spike(record.radiation_level):
            detected_events.append(EventType.RADIATION_SPIKE)
        
        # Check for gas plume detection
        if self._detect_gas_plume(record.gas_concentration):
            detected_events.append(EventType.GAS_PLUME_DETECTED)
        
        # Check for temperature anomalies
        if self._detect_temperature_anomaly(record.temperature):
            detected_events.append(EventType.TEMPERATURE_ANOMALY)
        
        # Check for pressure anomalies
        if self._detect_pressure_anomaly(record.pressure):
            detected_events.append(EventType.PRESSURE_ANOMALY)
        
        # Check for altitude mismatches
        if self._detect_altitude_mismatch(record.altitude, record.pressure):
            detected_events.append(EventType.ALTITUDE_MISMATCH)
        
        # Check for power low
        if record.battery_level < 20:
            detected_events.append(EventType.POWER_LOW)
        
        # Add to event history
        for event in detected_events:
            self._add_event_to_history(event, record)
        
        return detected_events
    
    def _update_history(self, record: TelemetryRecord):
        """Update historical data for trend analysis"""
        # Update temperature history
        self.temp_history.append(record.temperature)
        if len(self.temp_history) > self.max_history_size:
            self.temp_history.pop(0)
        
        # Update pressure history
        self.pressure_history.append(record.pressure)
        if len(self.pressure_history) > self.max_history_size:
            self.pressure_history.pop(0)
        
        # Update altitude history
        self.altitude_history.append(record.altitude)
        if len(self.altitude_history) > self.max_history_size:
            self.altitude_history.pop(0)
        
        # Update radiation history
        self.radiation_history.append(record.radiation_level)
        if len(self.radiation_history) > self.max_history_size:
            self.radiation_history.pop(0)
        
        # Update gas history
        self.gas_history.append(record.gas_concentration)
        if len(self.gas_history) > self.max_history_size:
            self.gas_history.pop(0)
    
    def _detect_boundary_layer_transition(self) -> bool:
        """Detect boundary layer transitions based on rapid changes"""
        if len(self.altitude_history) < 10:
            return False
        
        # Calculate rate of change for altitude and temperature
        alt_changes = np.diff(self.altitude_history[-10:])
        temp_changes = np.diff(self.temp_history[-10:])
        
        avg_alt_change = np.mean(np.abs(alt_changes))
        avg_temp_change = np.mean(np.abs(temp_changes))
        
        # Check if changes exceed threshold
        return (avg_alt_change > self.boundary_layer_threshold or 
                avg_temp_change > self.boundary_layer_threshold)
    
    def _detect_atmospheric_inversion(self) -> bool:
        """Detect atmospheric inversions based on temperature gradient"""
        if len(self.altitude_history) < 5 or len(self.temp_history) < 5:
            return False
        
        # Calculate temperature gradient with altitude
        altitudes = np.array(self.altitude_history[-5:])
        temps = np.array(self.temp_history[-5:])
        
        # Sort by altitude
        sorted_indices = np.argsort(altitudes)
        sorted_alts = altitudes[sorted_indices]
        sorted_temps = temps[sorted_indices]
        
        # Calculate gradient (dT/dh)
        if len(sorted_alts) > 1 and (sorted_alts[-1] - sorted_alts[0]) != 0:
            gradient = (sorted_temps[-1] - sorted_temps[0]) / (sorted_alts[-1] - sorted_alts[0])
            
            # Inversion occurs when temperature increases with altitude
            return gradient > self.inversion_threshold
        
        return False
    
    def _detect_parachute_deployment(self) -> bool:
        """Detect parachute deployment based on sudden velocity change"""
        if len(self.altitude_history) < 3:
            return False
        
        # Calculate velocity from altitude changes
        recent_alts = self.altitude_history[-3:]
        time_interval = 0.1  # Assuming 100ms intervals
        
        velocities = np.diff(recent_alts) / time_interval
        if len(velocities) < 2:
            return False
        
        # Check for sudden deceleration (parachute deployment)
        velocity_change = velocities[-1] - velocities[0]
        
        # Parachute deployment causes sudden decrease in descent rate
        return velocity_change > 50.0  # Significant deceleration
    
    def _detect_radiation_spike(self, current_radiation: float) -> bool:
        """Detect radiation spikes above baseline"""
        if len(self.radiation_history) < 10:
            return current_radiation > self.baseline_radiation * self.radiation_spike_threshold
        
        # Use recent baseline
        recent_baseline = np.mean(self.radiation_history[-10:])
        return current_radiation > recent_baseline * self.radiation_spike_threshold
    
    def _detect_gas_plume(self, current_gas: float) -> bool:
        """Detect gas plume based on concentration spikes"""
        if len(self.gas_history) < 10:
            return current_gas > self.baseline_gas * self.gas_plume_threshold
        
        # Use recent baseline
        recent_baseline = np.mean(self.gas_history[-10:])
        return current_gas > recent_baseline * self.gas_plume_threshold
    
    def _detect_temperature_anomaly(self, current_temp: float) -> bool:
        """Detect temperature anomalies using statistical methods"""
        if len(self.temp_history) < 10:
            return False
        
        # Calculate statistics
        temp_mean = np.mean(self.temp_history[-10:])
        temp_std = np.std(self.temp_history[-10:])
        
        if temp_std == 0:
            return False
        
        # Calculate z-score
        z_score = abs(current_temp - temp_mean) / temp_std
        return z_score > self.anomaly_threshold
    
    def _detect_pressure_anomaly(self, current_pressure: float) -> bool:
        """Detect pressure anomalies using statistical methods"""
        if len(self.pressure_history) < 10:
            return False
        
        # Calculate statistics
        press_mean = np.mean(self.pressure_history[-10:])
        press_std = np.std(self.pressure_history[-10:])
        
        if press_std == 0:
            return False
        
        # Calculate z-score
        z_score = abs(current_pressure - press_mean) / press_std
        return z_score > self.anomaly_threshold
    
    def _detect_altitude_mismatch(self, altitude: float, pressure: float) -> bool:
        """Detect mismatch between altitude and pressure readings"""
        # Calculate expected pressure from altitude using barometric formula
        # P = P0 * exp(-h/H) where H is scale height (~8400m)
        expected_pressure = self.baseline_pressure * np.exp(-altitude / 8400.0)
        
        # Calculate difference
        pressure_diff = abs(pressure - expected_pressure)
        
        # Allow 5% tolerance
        tolerance = 0.05 * expected_pressure
        return pressure_diff > tolerance
    
    def _add_event_to_history(self, event: EventType, record: TelemetryRecord):
        """Add event to history"""
        event_entry = {
            'timestamp': record.timestamp,
            'event_type': event.value,
            'mission_time': record.mission_time,
            'altitude': record.altitude,
            'values': {
                'temperature': record.temperature,
                'pressure': record.pressure,
                'radiation': record.radiation_level,
                'gas': record.gas_concentration
            }
        }
        
        self.event_history.append(event_entry)
        if len(self.event_history) > self.max_event_history:
            self.event_history.pop(0)
    
    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent events"""
        return self.event_history[-count:]


class TelemetryProcessor:
    """Advanced telemetry processor with filtering, validation, and analysis"""
    
    def __init__(self):
        self.event_detector = EventDetector()
        self.data_quality_thresholds = {
            'altitude': {'min': -100, 'max': 50000, 'std_threshold': 100},
            'temperature': {'min': -50, 'max': 100, 'std_threshold': 10},
            'pressure': {'min': 100, 'max': 120000, 'std_threshold': 500},
            'velocity': {'min': -1000, 'max': 1000, 'std_threshold': 200},
            'battery': {'min': 0, 'max': 100, 'std_threshold': 10},
            'radiation': {'min': 0, 'max': 1000, 'std_threshold': 50},
            'gas': {'min': 0, 'max': 10000, 'std_threshold': 1000}
        }
        
        # Data storage
        self.raw_data_buffer = queue.Queue(maxsize=10000)
        self.processed_data_buffer = queue.Queue(maxsize=10000)
        self.database_connection = None
        self.setup_database()
        
        # Processing statistics
        self.stats = {
            'total_packets': 0,
            'processed_packets': 0,
            'discarded_packets': 0,
            'error_packets': 0,
            'events_detected': 0,
            'last_update': datetime.now()
        }
        
        # Threading
        self.processing_thread = None
        self.running = False
        self.processing_lock = threading.Lock()
    
    def setup_database(self):
        """Setup SQLite database for telemetry storage"""
        try:
            self.database_connection = sqlite3.connect('telemetry_data.db', check_same_thread=False)
            cursor = self.database_connection.cursor()
            
            # Create telemetry table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    packet_id TEXT,
                    session_id TEXT,
                    mission_time REAL,
                    altitude REAL,
                    velocity REAL,
                    temperature REAL,
                    pressure REAL,
                    latitude REAL,
                    longitude REAL,
                    battery_level REAL,
                    radio_signal_strength REAL,
                    radiation_level REAL,
                    gas_concentration REAL,
                    uv_index REAL,
                    phase TEXT,
                    quality INTEGER,
                    events TEXT,
                    checksum TEXT
                )
            ''')
            
            # Create events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    mission_time REAL,
                    altitude REAL,
                    details TEXT
                )
            ''')
            
            self.database_connection.commit()
        except Exception as e:
            print(f"Database setup error: {e}")
    
    def add_telemetry(self, record: TelemetryRecord) -> bool:
        """Add telemetry record to processing queue"""
        try:
            self.raw_data_buffer.put(record, timeout=1.0)
            self.stats['total_packets'] += 1
            return True
        except queue.Full:
            self.stats['discarded_packets'] += 1
            return False
    
    def start_processing(self):
        """Start telemetry processing thread"""
        if self.processing_thread and self.processing_thread.is_alive():
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
    
    def stop_processing(self):
        """Stop telemetry processing"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
    
    def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Get record from queue
                record = self.raw_data_buffer.get(timeout=1.0)
                
                # Process the record
                processed_record = self._process_record(record)
                
                if processed_record:
                    # Add to processed buffer
                    try:
                        self.processed_data_buffer.put(processed_record, timeout=1.0)
                        self.stats['processed_packets'] += 1
                        
                        # Store in database
                        self._store_in_database(processed_record)

                        # Update statistics
                        self.stats['last_update'] = datetime.now()
                    except queue.Full:
                        # Processed but not stored due to buffer full
                        self.logger.debug("Telemetry buffer full, dropping record")
                
            except queue.Empty:
                continue
            except Exception as e:
                self.stats['error_packets'] += 1
                print(f"Processing error: {e}")
    
    def _process_record(self, record: TelemetryRecord) -> Optional[TelemetryRecord]:
        """Process individual telemetry record"""
        # Validate checksum
        if not self._validate_checksum(record):
            return None
        
        # Validate data ranges
        if not self._validate_data_ranges(record):
            return None
        
        # Detect events
        events = self.event_detector.detect_events(record)
        record.event_flags = events
        self.stats['events_detected'] += len(events)
        
        # Apply filters based on sensor type
        record = self._apply_filters(record)
        
        # Update quality assessment
        record.quality = self._assess_data_quality(record)
        
        return record
    
    def _validate_checksum(self, record: TelemetryRecord) -> bool:
        """Validate record checksum using zlib.crc32"""
        import zlib
        # Exclude checksum itself from calculation
        data_to_hash = f"{record.timestamp}{record.packet_id}{record.session_id}{record.mission_time}{record.altitude}{record.velocity}"
        calculated_crc = hex(zlib.crc32(data_to_hash.encode('utf-8')) & 0xFFFFFFFF)[2:]
        return record.checksum == calculated_crc
    
    def _validate_data_ranges(self, record: TelemetryRecord) -> bool:
        """Validate that data is within expected ranges"""
        checks = [
            self._check_range(record.altitude, 'altitude'),
            self._check_range(record.temperature, 'temperature'),
            self._check_range(record.pressure, 'pressure'),
            self._check_range(record.velocity, 'velocity'),
            self._check_range(record.battery_level, 'battery'),
            self._check_range(record.radiation_level, 'radiation'),
            self._check_range(record.gas_concentration, 'gas')
        ]
        
        return all(checks)
    
    def _check_range(self, value: float, param: str) -> bool:
        """Check if value is within acceptable range"""
        thresholds = self.data_quality_thresholds.get(param, {'min': -float('inf'), 'max': float('inf')})
        return thresholds['min'] <= value <= thresholds['max']
    
    def _apply_filters(self, record: TelemetryRecord) -> TelemetryRecord:
        """Apply appropriate filters to the record"""
        # In a real implementation, this would apply the filters from the data_filters module
        # For now, we'll just return the record as-is
        return record
    
    def _assess_data_quality(self, record: TelemetryRecord) -> int:
        """Assess overall data quality"""
        quality_score = 0
        total_checks = 0
        
        # Check various parameters
        for param, thresholds in self.data_quality_thresholds.items():
            value = getattr(record, param, 0)
            if isinstance(value, (int, float)):
                total_checks += 1
                
                # Check how close to center of valid range
                range_center = (thresholds['min'] + thresholds['max']) / 2
                range_width = thresholds['max'] - thresholds['min']
                if range_width > 0:
                    deviation = abs(value - range_center) / (range_width / 2)
                    
                    if deviation < 0.3:
                        quality_score += 4  # Excellent
                    elif deviation < 0.6:
                        quality_score += 3  # Good
                    elif deviation < 0.8:
                        quality_score += 2  # Fair
                    else:
                        quality_score += 1  # Poor
        
        if total_checks == 0:
            return 4  # Default to good if no checks performed
        
        average_quality = quality_score / total_checks
        
        if average_quality >= 3.5:
            return 4  # Excellent
        elif average_quality >= 2.5:
            return 3  # Good
        elif average_quality >= 1.5:
            return 2  # Fair
        else:
            return 1  # Poor
    
    def _store_in_database(self, record: TelemetryRecord):
        """Store processed record in database"""
        if not self.database_connection:
            return
        
        try:
            cursor = self.database_connection.cursor()
            
            # Insert telemetry record
            cursor.execute('''
                INSERT INTO telemetry (
                    timestamp, packet_id, session_id, mission_time, altitude, velocity,
                    temperature, pressure, latitude, longitude, battery_level,
                    radio_signal_strength, radiation_level, gas_concentration, uv_index,
                    phase, quality, events, checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.timestamp.isoformat(),
                record.packet_id,
                record.session_id,
                record.mission_time,
                record.altitude,
                record.velocity,
                record.temperature,
                record.pressure,
                record.latitude,
                record.longitude,
                record.battery_level,
                record.radio_signal_strength,
                record.radiation_level,
                record.gas_concentration,
                record.uv_index,
                record.phase.value,
                record.quality,
                json.dumps([e.value for e in record.event_flags]),
                record.checksum
            ))
            
            # Insert events if any
            for event in record.event_flags:
                cursor.execute('''
                    INSERT INTO events (timestamp, event_type, mission_time, altitude, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    record.timestamp.isoformat(),
                    event.value,
                    record.mission_time,
                    record.altitude,
                    json.dumps({
                        'temperature': record.temperature,
                        'pressure': record.pressure,
                        'radiation': record.radiation_level,
                        'gas': record.gas_concentration
                    })
                ))
            
            self.database_connection.commit()
        except Exception as e:
            print(f"Database storage error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        with self.processing_lock:
            return self.stats.copy()
    
    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recently detected events"""
        return self.event_detector.get_recent_events(count)
    
    def export_data(self, filename: str, start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None) -> bool:
        """Export telemetry data to file"""
        if not self.database_connection:
            return False
        
        try:
            cursor = self.database_connection.cursor()
            
            # Build query
            query = "SELECT * FROM telemetry WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            
            query += " ORDER BY timestamp"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=columns)
            
            # Export based on file extension
            if filename.endswith('.csv'):
                df.to_csv(filename, index=False)
            elif filename.endswith('.json'):
                df.to_json(filename, orient='records', indent=2, date_format='iso')
            elif filename.endswith('.parquet'):
                df.to_parquet(filename, index=False)
            else:
                raise ValueError(f"Unsupported export format: {filename}")
            
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False


class MissionController:
    """Advanced mission controller for managing mission phases and events"""
    
    def __init__(self):
        self.current_phase = MissionPhase.BOOT
        self.previous_phase = None
        self.mission_start_time = None
        self.apogee_time = None
        self.apogee_altitude = 0.0
        self.parachute_deployed = False
        self.mission_success_criteria = {
            'min_altitude': 100,
            'max_altitude': 10000,
            'min_flight_time': 30,
            'max_flight_time': 600,
            'successful_recovery': True
        }
        self.emergency_procedures = {
            'power_critical': self._execute_power_critical_procedure,
            'comm_loss': self._execute_comm_loss_procedure,
            'parachute_failure': self._execute_parachute_failure_procedure
        }
        self.autonomous_decision_rules = {
            MissionPhase.PRELAUNCH: self._prelaunch_decisions,
            MissionPhase.ASCENT: self._ascent_decisions,
            MissionPhase.APOGEE: self._apogee_decisions,
            MissionPhase.DESCENT: self._descent_decisions,
            MissionPhase.LANDED: self._landed_decisions
        }
        
        # Mission timeline
        self.timeline = []
        self.max_timeline_entries = 1000
    
    def start_mission(self):
        """Start the mission"""
        self.mission_start_time = datetime.now()
        self.current_phase = MissionPhase.SECURE_INIT
        self._log_timeline_event("MISSION_START", "Mission started successfully")
        print("Mission started successfully")
    
    def update_mission(self, telemetry: TelemetryRecord) -> MissionPhase:
        """Update mission state based on telemetry"""
        # Store previous phase
        self.previous_phase = self.current_phase
        
        # Determine new phase based on telemetry
        new_phase = self._determine_phase(telemetry)
        
        # Execute phase transition if needed
        if new_phase != self.current_phase:
            self._execute_phase_transition(self.current_phase, new_phase, telemetry)
            self.current_phase = new_phase
        
        # Execute autonomous decisions for current phase
        self._execute_autonomous_decisions(telemetry)
        
        # Check for emergency conditions
        self._check_emergency_conditions(telemetry)
        
        return self.current_phase
    
    def _determine_phase(self, telemetry: TelemetryRecord) -> MissionPhase:
        """Determine current mission phase based on telemetry"""
        if self.current_phase == MissionPhase.BOOT:
            return MissionPhase.SECURE_INIT
        elif self.current_phase == MissionPhase.SECURE_INIT:
            return MissionPhase.PRELAUNCH
        elif self.current_phase == MissionPhase.PRELAUNCH:
            # Transition to ASCENT when velocity exceeds threshold
            if telemetry.velocity > 10.0:
                return MissionPhase.ASCENT
        elif self.current_phase == MissionPhase.ASCENT:
            # Check for apogee (velocity near zero at peak altitude)
            if (telemetry.velocity < 5.0 and 
                telemetry.altitude > self.apogee_altitude * 0.95 and
                telemetry.mission_time > 10):  # Ensure we're past initial ascent
                self.apogee_altitude = telemetry.altitude
                self.apogee_time = telemetry.timestamp
                return MissionPhase.APOGEE
        elif self.current_phase == MissionPhase.APOGEE:
            # Transition to DESCENT when descending
            if telemetry.velocity < -5.0:
                return MissionPhase.DESCENT
        elif self.current_phase == MissionPhase.DESCENT:
            # Transition to LANDED when on ground
            if (telemetry.altitude < 10 and 
                abs(telemetry.velocity) < 2.0 and 
                telemetry.mission_time > 30):  # Ensure minimum flight time
                return MissionPhase.LANDED
        
        return self.current_phase
    
    def _execute_phase_transition(self, old_phase: MissionPhase, new_phase: MissionPhase, 
                                 telemetry: TelemetryRecord):
        """Execute actions during phase transition"""
        self._log_timeline_event(
            f"PHASE_TRANSITION_{old_phase.value}_TO_{new_phase.value}",
            f"Transitioned from {old_phase.value} to {new_phase.value}",
            telemetry
        )
        
        # Execute specific actions based on transition
        if old_phase == MissionPhase.ASCENT and new_phase == MissionPhase.APOGEE:
            self._execute_apogee_procedures(telemetry)
        elif old_phase == MissionPhase.APOGEE and new_phase == MissionPhase.DESCENT:
            self._execute_descent_procedures(telemetry)
    
    def _execute_apogee_procedures(self, telemetry: TelemetryRecord):
        """Execute procedures at apogee"""
        print(f"Apogee reached at {telemetry.altitude:.2f}m, time: {telemetry.mission_time:.2f}s")
        
        # Deploy parachute if not already deployed
        if not self.parachute_deployed:
            self._deploy_parachute()
    
    def _execute_descent_procedures(self, telemetry: TelemetryRecord):
        """Execute procedures during descent"""
        print(f"Descending from apogee, current altitude: {telemetry.altitude:.2f}m")
    
    def _execute_autonomous_decisions(self, telemetry: TelemetryRecord):
        """Execute autonomous decisions based on current phase"""
        if self.current_phase in self.autonomous_decision_rules:
            self.autonomous_decision_rules[self.current_phase](telemetry)
    
    def _prelaunch_decisions(self, telemetry: TelemetryRecord):
        """Autonomous decisions during prelaunch phase"""
        # Verify all systems are nominal
        if telemetry.battery_level < 80:
            print("WARNING: Battery level below 80% during prelaunch")
    
    def _ascent_decisions(self, telemetry: TelemetryRecord):
        """Autonomous decisions during ascent phase"""
        # Monitor ascent rate and system health
        if telemetry.battery_level < 50:
            print("CRITICAL: Battery level below 50% during ascent")
        
        # Check for unexpected events
        if telemetry.temperature > 80:
            print("CRITICAL: High temperature detected during ascent")
    
    def _apogee_decisions(self, telemetry: TelemetryRecord):
        """Autonomous decisions during apogee phase"""
        # Verify apogee conditions
        if abs(telemetry.velocity) > 10:
            print("WARNING: High velocity at expected apogee")
    
    def _descent_decisions(self, telemetry: TelemetryRecord):
        """Autonomous decisions during descent phase"""
        # Monitor descent rate
        if telemetry.velocity < -100:  # Too fast
            print("WARNING: Excessive descent rate detected")
        elif telemetry.velocity > -5:  # Too slow
            print("WARNING: Slow descent rate - parachute may not be deployed properly")
    
    def _landed_decisions(self, telemetry: TelemetryRecord):
        """Autonomous decisions during landed phase"""
        # Verify landed conditions
        if abs(telemetry.velocity) > 5:
            print("WARNING: Movement detected when landed expected")
    
    def _check_emergency_conditions(self, telemetry: TelemetryRecord):
        """Check for emergency conditions and respond"""
        # Check for power critical condition
        if telemetry.battery_level < 10:
            self.emergency_procedures['power_critical'](telemetry)
        
        # Check for communication loss
        if abs(telemetry.radio_signal_strength) > 100:  # Very weak signal
            self.emergency_procedures['comm_loss'](telemetry)
    
    def _execute_power_critical_procedure(self, telemetry: TelemetryRecord):
        """Execute power critical procedure"""
        print("EMERGENCY: Power critical - reducing non-essential systems")
        # In real implementation, this would shut down non-critical systems
    
    def _execute_comm_loss_procedure(self, telemetry: TelemetryRecord):
        """Execute communication loss procedure"""
        print("EMERGENCY: Communication link loss detected")
        # In real implementation, this would attempt to restore link
    
    def _execute_parachute_failure_procedure(self, telemetry: TelemetryRecord):
        """Execute parachute failure procedure"""
        print("EMERGENCY: Parachute deployment failed - initiating backup procedures")
        # In real implementation, this would deploy backup parachute
    
    def _deploy_parachute(self):
        """Deploy parachute"""
        self.parachute_deployed = True
        print("Parachute deployed successfully")
    
    def _log_timeline_event(self, event_type: str, description: str, 
                           telemetry: Optional[TelemetryRecord] = None):
        """Log event to mission timeline"""
        event = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'description': description,
            'mission_time': telemetry.mission_time if telemetry else 0,
            'altitude': telemetry.altitude if telemetry else 0,
            'phase': self.current_phase.value
        }
        
        self.timeline.append(event)
        if len(self.timeline) > self.max_timeline_entries:
            self.timeline.pop(0)
    
    def evaluate_mission_success(self) -> Dict[str, Any]:
        """Evaluate if mission was successful"""
        success_metrics = {
            'reached_min_altitude': self.apogee_altitude >= self.mission_success_criteria['min_altitude'],
            'did_not_exceed_max_altitude': self.apogee_altitude <= self.mission_success_criteria['max_altitude'],
            'flight_time_within_range': (self.mission_start_time and 
                                        (datetime.now() - self.mission_start_time).seconds >= 
                                        self.mission_success_criteria['min_flight_time']),
            'no_critical_failures': True,  # This would be determined by checking for critical events
            'successful_recovery': self.current_phase == MissionPhase.LANDED
        }
        
        overall_success = all(success_metrics.values())
        
        return {
            'overall_success': overall_success,
            'metrics': success_metrics,
            'apogee_altitude': self.apogee_altitude,
            'flight_time': (datetime.now() - self.mission_start_time).seconds if self.mission_start_time else 0,
            'parachute_deployed': self.parachute_deployed
        }
    
    def get_mission_status(self) -> Dict[str, Any]:
        """Get current mission status"""
        return {
            'current_phase': self.current_phase.value,
            'previous_phase': self.previous_phase.value if self.previous_phase else None,
            'mission_time': (datetime.now() - self.mission_start_time).seconds if self.mission_start_time else 0,
            'apogee_reached': self.apogee_time is not None,
            'apogee_altitude': self.apogee_altitude,
            'parachute_deployed': self.parachute_deployed,
            'timeline_entries': len(self.timeline)
        }


class AdvancedTelemetryMissionControl:
    """Main class combining telemetry processing and mission control"""
    
    def __init__(self):
        self.telemetry_processor = TelemetryProcessor()
        self.mission_controller = MissionController()
        self.is_running = False
        self.session_id = f"session_{int(time.time())}"
        
        # Initialize in a safe state
        self.mission_controller.start_mission()
    
    def process_telemetry(self, record: TelemetryRecord) -> Optional[TelemetryRecord]:
        """Process incoming telemetry and update mission state"""
        # Add session ID if not present
        if not record.session_id:
            record.session_id = self.session_id
        
        # Add to processing queue
        success = self.telemetry_processor.add_telemetry(record)
        if not success:
            return None
        
        # Update mission controller with processed data
        processed_record = self._get_processed_record()
        if processed_record:
            # Update mission phase based on telemetry
            self.mission_controller.update_mission(processed_record)
        
        return processed_record
    
    def _get_processed_record(self) -> Optional[TelemetryRecord]:
        """Get a processed record from the queue"""
        try:
            return self.telemetry_processor.processed_data_buffer.get_nowait()
        except queue.Empty:
            return None
    
    def start_system(self):
        """Start the telemetry processing system"""
        self.telemetry_processor.start_processing()
        self.is_running = True
        print("Advanced Telemetry and Mission Control System started")
    
    def stop_system(self):
        """Stop the telemetry processing system"""
        self.telemetry_processor.stop_processing()
        self.is_running = False
        print("Advanced Telemetry and Mission Control System stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'telemetry_stats': self.telemetry_processor.get_statistics(),
            'mission_status': self.mission_controller.get_mission_status(),
            'system_running': self.is_running,
            'session_id': self.session_id
        }
    
    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recently detected events"""
        return self.telemetry_processor.get_recent_events(count)
    
    def export_data(self, filename: str, start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None) -> bool:
        """Export telemetry data"""
        return self.telemetry_processor.export_data(filename, start_time, end_time)


# Example usage and testing
if __name__ == "__main__":
    print("Testing Advanced Telemetry Processing and Mission Control...")
    
    # Create the system
    system = AdvancedTelemetryMissionControl()
    system.start_system()
    
    print("System initialized and started")
    
    # Create sample telemetry records
    base_time = datetime.now()
    for i in range(5):
        record = TelemetryRecord(
            timestamp=base_time + timedelta(seconds=i),
            packet_id=f"pkt_{i:04d}",
            session_id=system.session_id,
            mission_time=i,
            altitude=100.0 + i * 50,
            velocity=50.0,
            temperature=20.0 + i * 0.1,
            pressure=1013.25 - i * 10,
            latitude=34.0522,
            longitude=-118.2437,
            battery_level=95.0 - i * 0.5,
            radio_signal_strength=-50 - i,
            radiation_level=0.1 + i * 0.01,
            gas_concentration=400 + i * 10,
            uv_index=0.5 + i * 0.1,
            checksum=""
        )
        # Calculate real checksum
        import zlib
        data_to_hash = f"{record.timestamp}{record.packet_id}{record.session_id}{record.mission_time}{record.altitude}{record.velocity}"
        record.checksum = hex(zlib.crc32(data_to_hash.encode('utf-8')) & 0xFFFFFFFF)[2:]
        
        processed = system.process_telemetry(record)
        if processed:
            print(f"Processed record {i}: altitude={processed.altitude:.1f}m, phase={processed.phase.value}")
    
    # Get system status
    status = system.get_system_status()
    print(f"System status - Total packets: {status['telemetry_stats']['total_packets']}")
    print(f"Mission phase: {status['mission_status']['current_phase']}")
    
    # Get recent events
    events = system.get_recent_events(5)
    print(f"Recent events: {len(events)}")
    
    # Stop the system
    system.stop_system()
    print("Advanced Telemetry Processing and Mission Control test completed successfully!")