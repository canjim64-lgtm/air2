"""
AirOne v3 - Data Models, Database & Pipeline
===========================================

This file contains all data-related functionality for the AirOne v3 system,
consolidating data models, database operations, and data pipeline functionality
into a single comprehensive module.

This file consolidates:
- src/data/data_models.py (Data models and structures)
- src/data/database.py (Database operations)
- src/data/pipeline.py (Data pipeline)
- src/data/advanced_pipeline.py (Advanced pipeline features)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
import time
import sqlite3
import json
import threading
import queue
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import csv
import io
import gzip
import pickle
import struct
import zlib
import os
import sys
from pathlib import Path
import hashlib
import hmac
import secrets
import string
import base64
import math
import random
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import ctypes # Potentially used for shared memory/inter-process communication in advanced pipelines
import mmap # Potentially used for shared memory in advanced pipelines
import signal
import atexit
import weakref
import gc
import resource
import psutil
import cpuinfo
import pkg_resources
import importlib
import ast # For code analysis in advanced pipelines
import dis # For bytecode analysis in advanced pipelines
import inspect # For dynamic introspection in advanced pipelines
import types # For dynamic type creation/checking
import copy
import collections
import heapq
import bisect
import itertools
import functools
import operator
import re
import uuid
import urllib.parse # For URL handling in data sources

# The following imports are retained based on common use cases in advanced data/pipeline systems,
# even if their direct use isn't immediately obvious from the file structure,
# as they represent general capabilities a "combined_data" module might leverage.
# If future code relies on them, they are available.
# Otherwise, they would be further pruned if a deeper code analysis showed no usage.

# No tkinter, email, http, xml, or low-level encoding/test modules unless specifically used in the logic.

logger = logging.getLogger(__name__)

# ###########################################################################
# DATA MODELS (from data_models.py)
# ###########################################################################

@dataclass
class TelemetryData:
    """Standardized telemetry data model"""
    timestamp: float
    altitude: float
    velocity: float
    temperature: float
    pressure: float
    battery_voltage: float
    battery_percent: float
    signal_strength: float
    latitude: float
    longitude: float
    mission_phase: str
    quality_score: float = 1.0
    packet_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    sensor_readings: Dict[str, Any] = field(default_factory=dict)
    anomalies_detected: List[str] = field(default_factory=list)
    predicted_values: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MissionEvent:
    """Standardized mission event model"""
    event_id: str
    timestamp: datetime
    event_type: str
    description: str
    severity: str # info, warning, error, critical
    related_telemetry_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None

@dataclass
class SystemLog:
    """Standardized system log entry model"""
    log_id: str
    timestamp: datetime
    level: str # INFO, WARNING, ERROR, DEBUG
    module: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

# ###########################################################################
# DATABASE OPERATIONS (from database.py)
# ###########################################################################

class DatabaseManager:
    """Manages SQLite database operations for telemetry, events, and logs"""
    
    def __init__(self, db_path: str = "airone_data.db"):
        self.db_path = db_path
        self.conn = None
        self.lock = threading.Lock()
        
    def connect(self):
        """Establish database connection"""
        with self.lock:
            if self.conn is None:
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row  # Access columns by name
                self._create_tables()
            return self.conn
            
    def close(self):
        """Close database connection"""
        with self.lock:
            if self.conn:
                self.conn.close()
                self.conn = None
                
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Telemetry table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                packet_id TEXT PRIMARY KEY,
                timestamp REAL,
                altitude REAL,
                velocity REAL,
                temperature REAL,
                pressure REAL,
                battery_voltage REAL,
                battery_percent REAL,
                signal_strength REAL,
                latitude REAL,
                longitude REAL,
                mission_phase TEXT,
                quality_score REAL,
                session_id TEXT,
                sensor_readings TEXT,
                anomalies_detected TEXT,
                predicted_values TEXT
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT,
                event_type TEXT,
                description TEXT,
                severity TEXT,
                related_telemetry_id TEXT,
                context TEXT,
                user_id TEXT
            )
        """)
        
        # Logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                log_id TEXT PRIMARY KEY,
                timestamp TEXT,
                level TEXT,
                module TEXT,
                message TEXT,
                context TEXT
            )
        """)
        
        self.conn.commit()
    
    def insert_telemetry(self, data: TelemetryData):
        """Insert a telemetry record"""
        with self.lock:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO telemetry (
                    packet_id, timestamp, altitude, velocity, temperature, pressure,
                    battery_voltage, battery_percent, signal_strength, latitude, longitude,
                    mission_phase, quality_score, session_id, sensor_readings,
                    anomalies_detected, predicted_values
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.packet_id, data.timestamp, data.altitude, data.velocity, data.temperature,
                data.pressure, data.battery_voltage, data.battery_percent, data.signal_strength,
                data.latitude, data.longitude, data.mission_phase, data.quality_score,
                data.session_id, json.dumps(data.sensor_readings),
                json.dumps(data.anomalies_detected), json.dumps(data.predicted_values)
            ))
            self.conn.commit()
            
    def insert_event(self, event: MissionEvent):
        """Insert an event record"""
        with self.lock:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO events (
                    event_id, timestamp, event_type, description, severity,
                    related_telemetry_id, context, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.timestamp.isoformat(), event.event_type,
                event.description, event.severity, event.related_telemetry_id,
                json.dumps(event.context), event.user_id
            ))
            self.conn.commit()
            
    def insert_log(self, log_entry: SystemLog):
        """Insert a system log entry"""
        with self.lock:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO logs (
                    log_id, timestamp, level, module, message, context
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                log_entry.log_id, log_entry.timestamp.isoformat(), log_entry.level,
                log_entry.module, log_entry.message, json.dumps(log_entry.context)
            ))
            self.conn.commit()
    
    def get_telemetry_by_time(self, start_time: float, end_time: float) -> List[TelemetryData]:
        """Retrieve telemetry data within a time range"""
        with self.lock:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM telemetry WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp
            """, (start_time, end_time))
            
            rows = cursor.fetchall()
            return [TelemetryData(**self._row_to_telemetry_dict(row)) for row in rows]
            
    def _row_to_telemetry_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to TelemetryData dictionary"""
        data = dict(row)
        data['sensor_readings'] = json.loads(data['sensor_readings'])
        data['anomalies_detected'] = json.loads(data['anomalies_detected'])
        data['predicted_values'] = json.loads(data['predicted_values'])
        return data

    def get_all_telemetry(self, limit: int = 1000) -> List[TelemetryData]:
        """Retrieve all telemetry data up to a limit"""
        with self.lock:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [TelemetryData(**self._row_to_telemetry_dict(row)) for row in rows]

    def get_all_events(self, limit: int = 1000) -> List[MissionEvent]:
        """Retrieve all mission events up to a limit"""
        with self.lock:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [MissionEvent(**self._row_to_event_dict(row)) for row in rows]
    
    def _row_to_event_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to MissionEvent dictionary"""
        data = dict(row)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['context'] = json.loads(data['context'])
        return data

    def get_all_logs(self, limit: int = 1000) -> List[SystemLog]:
        """Retrieve all system logs up to a limit"""
        with self.lock:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [SystemLog(**self._row_to_log_dict(row)) for row in rows]
    
    def _row_to_log_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to SystemLog dictionary"""
        data = dict(row)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['context'] = json.loads(data['context'])
        return data

# ###########################################################################
# DATA PIPELINE (from pipeline.py & advanced_pipeline.py)
# ###########################################################################

class DataProcessor(ABC):
    """Abstract base class for data processors"""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data"""
        pass

class TelemetryValidator(DataProcessor):
    """Validates telemetry data against expected ranges and types"""
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(self, telemetry_data: TelemetryData) -> Optional[TelemetryData]:
        """Validate a single telemetry data point"""
        if not isinstance(telemetry_data, TelemetryData):
            self.logger.error("Invalid data type for validation: expected TelemetryData")
            return None

        # Check required fields and types
        for field_name, field_type in self.schema.items():
            value = getattr(telemetry_data, field_name, None)
            if value is None and self.schema[field_name].get('required', False):
                self.logger.warning(f"Validation failed: Missing required field '{field_name}'")
                return None
            if value is not None and not isinstance(value, field_type.get('type')):
                self.logger.warning(f"Validation failed: Invalid type for '{field_name}', expected {field_type.get('type')}")
                return None
            
            # Check range if specified
            if 'min' in field_type and value < field_type['min']:
                self.logger.warning(f"Validation failed: '{field_name}' below minimum ({field_type['min']})")
                return None
            if 'max' in field_type and value > field_type['max']:
                self.logger.warning(f"Validation failed: '{field_name}' above maximum ({field_type['max']})")
                return None

        telemetry_data.quality_score = 0.9 # Placeholder for actual quality assessment
        return telemetry_data


class TelemetryScaler(DataProcessor):
    """Scales telemetry data using min-max or standard scaling"""
    
    def __init__(self, method: str = 'minmax', feature_ranges: Dict[str, Tuple[float, float]] = None):
        self.method = method
        self.scalers = {}
        self.feature_ranges = feature_ranges or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(self, telemetry_data: TelemetryData) -> TelemetryData:
        """Scale telemetry data"""
        scaled_data = copy.deepcopy(telemetry_data)
        numeric_fields = ['altitude', 'velocity', 'temperature', 'pressure', 'battery_voltage', 'battery_percent', 'signal_strength', 'latitude', 'longitude']

        for field_name in numeric_fields:
            value = getattr(scaled_data, field_name)
            if value is not None and isinstance(value, (int, float)):
                if field_name in self.feature_ranges:
                    min_val, max_val = self.feature_ranges[field_name]
                    if min_val != max_val:
                        scaled_value = (value - min_val) / (max_val - min_val)
                        setattr(scaled_data, field_name, scaled_value)
                    else:
                        setattr(scaled_data, field_name, 0.5) # Default if range is zero
                else:
                    self.logger.warning(f"No scaling range defined for {field_name}")

        return scaled_data


class AnomalyDetector(DataProcessor):
    """Detects anomalies in telemetry data"""
    
    def __init__(self, model: Any = None):
        self.model = model
        self.training_data = []
        self.logger = logging.getLogger(self.__class__.__name__)

        if self.model is None:
            try:
                from sklearn.ensemble import IsolationForest
                self.model = IsolationForest(contamination=0.05, random_state=42)
                self.logger.info("Default IsolationForest model initialized for AnomalyDetector.")
            except ImportError:
                self.logger.error("Scikit-learn not available. Anomaly detection will be rudimentary.")
                self.model = None

    def _train_model(self, data: List[TelemetryData]):
        """Train the anomaly detection model (if applicable)"""
        if self.model is None or not hasattr(self.model, 'fit'):
            self.logger.warning("Anomaly detection model is not trainable or not initialized.")
            return

        numeric_data = []
        for td in data:
            numeric_data.append([
                td.altitude, td.velocity, td.temperature, td.pressure,
                td.battery_voltage, td.battery_percent, td.signal_strength,
                td.latitude, td.longitude
            ])
        
        if len(numeric_data) < 100: # Need sufficient data for training
            self.logger.warning("Insufficient data for training anomaly detector.")
            return

        X = np.array(numeric_data)
        try:
            self.model.fit(X)
            self.training_data = X # Store for future re-training if needed
            self.logger.info("Anomaly detection model trained successfully.")
        except Exception as e:
            self.logger.error(f"Error training anomaly detection model: {e}")

    def process(self, telemetry_data: TelemetryData) -> TelemetryData:
        """Detect anomalies in telemetry data"""
        if self.model is None:
            self.logger.warning("No anomaly detection model available. Skipping anomaly detection.")
            return telemetry_data

        features = np.array([[
            telemetry_data.altitude, telemetry_data.velocity, telemetry_data.temperature,
            telemetry_data.pressure, telemetry_data.battery_voltage, telemetry_data.battery_percent,
            telemetry_data.signal_strength, telemetry_data.latitude, telemetry_data.longitude
        ]])
        
        try:
            prediction = self.model.predict(features)
            if prediction[0] == -1: # -1 indicates an anomaly
                telemetry_data.anomalies_detected.append("IsolationForest_Anomaly")
                self.logger.warning(f"Anomaly detected in packet {telemetry_data.packet_id}")
            else:
                if "IsolationForest_Anomaly" in telemetry_data.anomalies_detected:
                    telemetry_data.anomalies_detected.remove("IsolationForest_Anomaly") # Clear if no longer anomaly

        except Exception as e:
            self.logger.error(f"Error during anomaly detection: {e}")
            telemetry_data.anomalies_detected.append("AnomalyDetection_Error")

        return telemetry_data


class MissionPhaseClassifier(DataProcessor):
    """Classifies mission phase based on telemetry data"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(self, telemetry_data: TelemetryData) -> TelemetryData:
        """Classify mission phase"""
        # Rule-based classification for simplicity
        if telemetry_data.altitude < 10 and telemetry_data.velocity < 5:
            telemetry_data.mission_phase = "PRE_LAUNCH"
        elif telemetry_data.altitude < 10 and telemetry_data.velocity > 50:
            telemetry_data.mission_phase = "LAUNCH"
        elif telemetry_data.velocity > 0 and telemetry_data.altitude > 50:
            telemetry_data.mission_phase = "ASCENT"
        elif telemetry_data.velocity < 0 and telemetry_data.altitude > 100:
            if telemetry_data.velocity < -5:
                telemetry_data.mission_phase = "DESCENT_FAST"
            else:
                telemetry_data.mission_phase = "DESCENT_PARACHUTE"
        elif telemetry_data.altitude < 50 and abs(telemetry_data.velocity) < 10:
            telemetry_data.mission_phase = "LANDING"
        else:
            telemetry_data.mission_phase = "UNKNOWN"
        return telemetry_data


class DataPipeline:
    """Sequential data processing pipeline"""
    
    def __init__(self):
        self.processors: List[DataProcessor] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def add_processor(self, processor: DataProcessor):
        """Add a data processor to the pipeline"""
        self.processors.append(processor)
        self.logger.info(f"Added processor: {processor.__class__.__name__} to pipeline.")

    def run_pipeline(self, data: Any) -> Any:
        """Run data through the pipeline"""
        processed_data = data
        for processor in self.processors:
            if processed_data is None:
                break
            try:
                processed_data = processor.process(processed_data)
            except Exception as e:
                self.logger.error(f"Error running processor {processor.__class__.__name__}: {e}")
                return None # Stop pipeline on error
        return processed_data


class RealTimeDataStream(threading.Thread):
    """Simulates a real-time data stream and feeds it into a pipeline"""
    
    def __init__(self, data_pipeline: DataPipeline, db_manager: DatabaseManager, interval: float = 0.1):
        super().__init__(daemon=True)
        self.data_pipeline = data_pipeline
        self.db_manager = db_manager
        self.interval = interval
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self.packet_count = 0
        self.session_id = str(uuid.uuid4())

        # Simulate initial flight conditions for telemetry generation
        self._altitude = 10.0
        self._velocity = 0.0
        self._temperature = 25.0
        self._pressure = 1013.25
        self._battery_voltage = 12.6
        self._battery_percent = 100.0
        self._signal_strength = -50.0
        self._latitude = 34.0
        self._longitude = -118.0
        self._mission_phase = "PRE_LAUNCH"

    def run(self):
        """Main loop for the data stream"""
        self.running = True
        self.logger.info("Real-time data stream started.")
        while self.running:
            try:
                telemetry = self._generate_simulated_telemetry()
                processed_telemetry = self.data_pipeline.run_pipeline(telemetry)
                
                if processed_telemetry:
                    self.db_manager.insert_telemetry(processed_telemetry)
                    self.logger.debug(f"Processed and inserted telemetry: {processed_telemetry.packet_id}")
                
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Error in data stream: {e}")
                time.sleep(1.0)

    def stop(self):
        """Stop the data stream"""
        self.running = False
        self.logger.info("Real-time data stream stopped.")

    def _generate_simulated_telemetry(self) -> TelemetryData:
        """Generates a single simulated telemetry data point"""
        self.packet_count += 1
        current_time = time.time()

        # Simulate flight dynamics (simplified)
        if current_time < time.time() + 10: # First 10 seconds: launch
            self._velocity += 0.5 + random.uniform(-0.1, 0.1)
            self._altitude += self._velocity * self.interval
            self._temperature -= 0.01
            self._pressure -= 0.05
            self._battery_percent -= 0.005
            self._signal_strength += random.uniform(-0.5, 0.5)
            self._mission_phase = "LAUNCH"
        else: # Later phase: descent
            self._velocity -= 0.1 + random.uniform(-0.05, 0.05)
            self._altitude += self._velocity * self.interval
            self._temperature += 0.005
            self._pressure += 0.01
            self._battery_percent -= 0.001
            self._signal_strength += random.uniform(-0.1, 0.1)
            self._mission_phase = "DESCENT"

        # Ensure values stay realistic
        self._altitude = max(0.0, self._altitude)
        self._velocity = max(-10.0, min(100.0, self._velocity))
        self._temperature = max(-20.0, min(50.0, self._temperature))
        self._pressure = max(500.0, min(1100.0, self._pressure))
        self._battery_percent = max(0.0, min(100.0, self._battery_percent))
        self._signal_strength = max(-120.0, min(-30.0, self._signal_strength))
        self._battery_voltage = 12.6 * (self._battery_percent / 100.0)

        # Simulate GPS drift
        self._latitude += random.uniform(-0.0001, 0.0001)
        self._longitude += random.uniform(-0.0001, 0.0001)

        return TelemetryData(
            packet_id=f"TLM-{self.packet_count}",
            timestamp=current_time,
            altitude=self._altitude,
            velocity=self._velocity,
            temperature=self._temperature,
            pressure=self._pressure,
            battery_voltage=self._battery_voltage,
            battery_percent=self._battery_percent,
            signal_strength=self._signal_strength,
            latitude=self._latitude,
            longitude=self._longitude,
            mission_phase=self._mission_phase,
            quality_score=random.uniform(0.8, 1.0),
            session_id=self.session_id
        )


class EventGenerator(threading.Thread):
    """Generates simulated mission events and logs them"""

    def __init__(self, db_manager: DatabaseManager, interval: float = 5.0):
        super().__init__(daemon=True)
        self.db_manager = db_manager
        self.interval = interval
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_types = ["LAUNCH_DETECTED", "APOGEE_REACHED", "PARACHUTE_DEPLOYED",
                            "LANDING_DETECTED", "BATTERY_LOW", "SIGNAL_LOSS", "SENSOR_ERROR"]
        self.user_ids = ["system", "control_ops", "mission_analyst"]

    def run(self):
        self.running = True
        self.logger.info("Event generator started.")
        while self.running:
            try:
                event = self._generate_simulated_event()
                self.db_manager.insert_event(event)
                self.logger.debug(f"Generated and inserted event: {event.event_id}")
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Error in event generator: {e}")
                time.sleep(1.0)

    def stop(self):
        self.running = False
        self.logger.info("Event generator stopped.")

    def _generate_simulated_event(self) -> MissionEvent:
        event_type = random.choice(self.event_types)
        severity = "info"
        if event_type in ["BATTERY_LOW", "SIGNAL_LOSS"]:
            severity = random.choice(["warning", "error"])
        elif event_type == "SENSOR_ERROR":
            severity = "critical"
        
        description = f"Simulated event: {event_type} occurred."
        user_id = random.choice(self.user_ids)

        return MissionEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            severity=severity,
            user_id=user_id,
            context={"simulated_source": "EventGenerator"}
        )


class SystemLogger(threading.Thread):
    """Generates simulated system logs and inserts into database"""

    def __init__(self, db_manager: DatabaseManager, interval: float = 1.0):
        super().__init__(daemon=True)
        self.db_manager = db_manager
        self.interval = interval
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self.log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        self.modules = ["telemetry_processor", "ai_engine", "comm_manager", "database_manager"]

    def run(self):
        self.running = True
        self.logger.info("System logger started.")
        while self.running:
            try:
                log_entry = self._generate_simulated_log()
                self.db_manager.insert_log(log_entry)
                self.logger.debug(f"Generated and inserted log: {log_entry.log_id}")
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Error in system logger: {e}")
                time.sleep(1.0)

    def stop(self):
        self.running = False
        self.logger.info("System logger stopped.")

    def _generate_simulated_log(self) -> SystemLog:
        level = random.choice(self.log_levels)
        module = random.choice(self.modules)
        message = f"Simulated log message for {module} at {level} level."
        
        return SystemLog(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level=level,
            module=module,
            message=message,
            context={"simulated_source": "SystemLogger"}
        )


class AdvancedPipelineCoordinator:
    """Coordinates multiple data pipelines for real-time processing"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.pipelines: Dict[str, DataPipeline] = {}
        self.input_queues: Dict[str, queue.Queue] = {}
        self.output_queue: queue.Queue = queue.Queue(maxsize=1000)
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self.thread_pool = ThreadPoolExecutor(max_workers=os.cpu_count() or 1) # Use all CPU cores

    def add_pipeline(self, name: str, pipeline: DataPipeline):
        """Add a named data pipeline"""
        self.pipelines[name] = pipeline
        self.input_queues[name] = queue.Queue(maxsize=500)
        self.logger.info(f"Added pipeline: {name}")

    def start_processing(self):
        """Start all pipeline processing threads"""
        self.running = True
        self.logger.info("Advanced pipeline coordinator started.")
        for name, input_queue in self.input_queues.items():
            self.thread_pool.submit(self._run_pipeline_worker, name, input_queue)
        self.thread_pool.submit(self._run_output_processor)
        self.logger.info(f"Started {len(self.pipelines)} pipeline workers and 1 output processor.")

    def stop_processing(self):
        """Stop all pipeline processing threads"""
        self.running = False
        self.thread_pool.shutdown(wait=True)
        self.logger.info("Advanced pipeline coordinator stopped.")

    def _run_pipeline_worker(self, name: str, input_queue: queue.Queue):
        """Worker function for a single pipeline"""
        pipeline = self.pipelines[name]
        self.logger.info(f"Pipeline worker for '{name}' started.")
        while self.running:
            try:
                data = input_queue.get(timeout=1.0)
                processed_data = pipeline.run_pipeline(data)
                if processed_data:
                    self.output_queue.put(processed_data)
                input_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in pipeline '{name}' worker: {e}")
                input_queue.task_done()
        self.logger.info(f"Pipeline worker for '{name}' stopped.")

    def _run_output_processor(self):
        """Processes data from the output queue"""
        self.logger.info("Output processor started.")
        while self.running:
            try:
                processed_data = self.output_queue.get(timeout=1.0)
                # Here, you would typically store the final processed data
                # For this example, we'll store it in the database
                if isinstance(processed_data, TelemetryData):
                    self.db_manager.insert_telemetry(processed_data)
                    self.logger.debug(f"Output processor inserted telemetry: {processed_data.packet_id}")
                else:
                    self.logger.warning(f"Output processor received unknown data type: {type(processed_data)}")
                self.output_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in output processor: {e}")
                self.output_queue.task_done()
        self.logger.info("Output processor stopped.")

    def enqueue_data(self, pipeline_name: str, data: Any) -> bool:
        """Enqueue data into a specific pipeline's input queue"""
        if pipeline_name not in self.input_queues:
            self.logger.error(f"Pipeline '{pipeline_name}' not found.")
            return False
        try:
            self.input_queues[pipeline_name].put_nowait(data)
            return True
        except queue.Full:
            self.logger.warning(f"Input queue for pipeline '{pipeline_name}' is full, data dropped.")
            return False

# ###########################################################################
# MAIN EXECUTION BLOCK (Test Suite)
# ###########################################################################

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # Use DEBUG for detailed pipeline logs
    logger.info("🚀 AirOne v3 Data Models, Database & Pipeline Test Suite 🚀")

    db_manager = DatabaseManager(db_path="test_airone_data.db")
    db_manager.connect()

    # Data Pipeline Setup
    data_pipeline = DataPipeline()
    schema = {
        'altitude': {'type': float, 'min': 0, 'max': 50000, 'required': True},
        'velocity': {'type': float, 'min': -500, 'max': 500, 'required': True},
        'temperature': {'type': float, 'min': -50, 'max': 100, 'required': True},
        'pressure': {'type': float, 'min': 0, 'max': 1200, 'required': True},
        'battery_percent': {'type': float, 'min': 0, 'max': 100, 'required': True},
        'signal_strength': {'type': float, 'min': -120, 'max': -30, 'required': True},
    }
    data_pipeline.add_processor(TelemetryValidator(schema))
    data_pipeline.add_processor(TelemetryScaler(feature_ranges={'altitude': (0, 50000), 'temperature': (-50, 100)}))
    data_pipeline.add_processor(AnomalyDetector())
    data_pipeline.add_processor(MissionPhaseClassifier())

    # Start Real-time Data Stream
    stream = RealTimeDataStream(data_pipeline, db_manager, interval=0.05) # 20 Hz
    stream.start()

    # Start Event Generator
    event_gen = EventGenerator(db_manager, interval=2.0)
    event_gen.start()

    # Start System Logger
    sys_logger = SystemLogger(db_manager, interval=0.5)
    sys_logger.start()

    # Advanced Pipeline Coordinator Setup (if more than one pipeline)
    coordinator = AdvancedPipelineCoordinator(db_manager)
    coordinator.add_pipeline("main_telemetry_pipeline", data_pipeline) # Can add the same or different pipelines
    coordinator.start_processing()

    print("\nSimulating data flow for 10 seconds...")
    time.sleep(10) # Run for 10 seconds

    # Stop all threads
    stream.stop()
    event_gen.stop()
    sys_logger.stop()
    coordinator.stop_processing()

    # Retrieve and print some data
    print("\nRetrieving data from database:")
    telemetry_records = db_manager.get_all_telemetry(limit=5)
    print(f"  {len(telemetry_records)} telemetry records (latest):")
    for tr in telemetry_records:
        print(f"    [{tr.timestamp:.2f}s] Alt: {tr.altitude:.2f}m, Vel: {tr.velocity:.2f}m/s, Phase: {tr.mission_phase}, Anomalies: {tr.anomalies_detected}")

    events = db_manager.get_all_events(limit=3)
    print(f"  {len(events)} mission events:")
    for ev in events:
        print(f"    [{ev.timestamp.isoformat()}] {ev.event_type} ({ev.severity}): {ev.description}")

    logs = db_manager.get_all_logs(limit=3)
    print(f"  {len(logs)} system logs:")
    for log_entry in logs:
        print(f"    [{log_entry.timestamp.isoformat()}] {log_entry.level} [{log_entry.module}]: {log_entry.message}")

    db_manager.close()
    print("\n✅ Data Models, Database & Pipeline Test Suite Completed.")
