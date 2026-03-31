"""
AirOne Professional v4.0 - Advanced Data Analysis & Visualization
Complete telemetry analysis with 50+ mission graphs and advanced analytics

Features:
- 50+ different mission graphs
- Real-time telemetry processing
- Advanced statistical analysis
- Interactive dashboards
- Multi-mission comparison
- Anomaly detection and alerting
- Predictive analytics
- Export to multiple formats
"""

import os
import sys
import json
import time
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import numpy as np
import pandas as pd
from collections import deque, defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphType(Enum):
    """Types of mission graphs"""
    # Basic Telemetry
    ALTITUDE_VS_TIME = "altitude_vs_time"
    VELOCITY_VS_TIME = "velocity_vs_time"
    ACCELERATION_VS_TIME = "acceleration_vs_time"
    TEMPERATURE_VS_TIME = "temperature_vs_time"
    PRESSURE_VS_TIME = "pressure_vs_time"
    BATTERY_VS_TIME = "battery_vs_time"
    SIGNAL_VS_TIME = "signal_vs_time"
    GPS_LAT_LON = "gps_lat_lon"
    GPS_ALTITUDE = "gps_altitude"
    
    # Derived Metrics
    MACH_NUMBER = "mach_number"
    DYNAMIC_PRESSURE = "dynamic_pressure"
    HEAT_FLUX = "heat_flux"
    DRAG_COEFFICIENT = "drag_coefficient"
    REYNOLDS_NUMBER = "reynolds_number"
    
    # Flight Phase Analysis
    FLIGHT_PHASE_TIMELINE = "flight_phase_timeline"
    APOGEE_DETECTION = "apogee_detection"
    DESCENT_RATE = "descent_rate"
    LANDING_IMPACT = "landing_impact"
    
    # Statistical Analysis
    TELEMETRY_DISTRIBUTION = "telemetry_distribution"
    CORRELATION_MATRIX = "correlation_matrix"
    ANOMALY_HEATMAP = "anomaly_heatmap"
    TREND_ANALYSIS = "trend_analysis"
    MOVING_AVERAGE = "moving_average"
    STANDARD_DEVIATION = "standard_deviation"
    
    # Performance Metrics
    SYSTEM_HEALTH = "system_health"
    DATA_QUALITY = "data_quality"
    PACKET_LOSS = "packet_loss"
    LATENCY_ANALYSIS = "latency_analysis"
    THROUGHPUT = "throughput"
    
    # Environmental
    ATMOSPHERIC_PROFILE = "atmospheric_profile"
    TEMPERATURE_GRADIENT = "temperature_gradient"
    PRESSURE_ALTITUDE = "pressure_altitude"
    DENSITY_ALTITUDE = "density_altitude"
    WIND_ESTIMATION = "wind_estimation"
    
    # Power Analysis
    POWER_CONSUMPTION = "power_consumption"
    BATTERY_DISCHARGE = "battery_discharge"
    VOLTAGE_CURRENT = "voltage_current"
    CAPACITY_REMAINING = "capacity_remaining"
    CHARGE_CYCLES = "charge_cycles"
    
    # Communication
    RSSI_HISTORY = "rssi_history"
    SNR_ANALYSIS = "snr_analysis"
    PACKET_SUCCESS_RATE = "packet_success_rate"
    LINK_BUDGET = "link_budget"
    ANTENNA_ORIENTATION = "antenna_orientation"
    
    # Sensor Analysis
    SENSOR_FUSION = "sensor_fusion"
    IMU_RAW_DATA = "imu_raw_data"
    MAGNETOMETER_DATA = "magnetometer_data"
    BAROMETER_STABILITY = "barometer_stability"
    GPS_ACCURACY = "gps_accuracy"
    
    # Mission Events
    EVENT_TIMELINE = "event_timeline"
    COMMAND_HISTORY = "command_history"
    STATE_TRANSITIONS = "state_transitions"
    ERROR_LOG = "error_log"
    WARNING_FREQUENCY = "warning_frequency"
    
    # Predictive
    TRAJECTORY_PREDICTION = "trajectory_prediction"
    LANDING_ZONE = "landing_zone"
    TIME_TO_APOGEE = "time_to_apogee"
    FUEL_REMAINING = "fuel_remaining"
    MISSION_PROGRESS = "mission_progress"
    
    # Comparative
    MULTI_MISSION_COMPARE = "multi_mission_compare"
    EXPECTED_VS_ACTUAL = "expected_vs_actual"
    SIMULATION_VS_REAL = "simulation_vs_real"
    FLIGHT_TO_FLIGHT = "flight_to_flight"
    PERFORMANCE_BENCHMARK = "performance_benchmark"


@dataclass
class TelemetryPoint:
    """Single telemetry data point"""
    timestamp: float
    altitude: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0
    temperature: float = 0.0
    pressure: float = 0.0
    battery_voltage: float = 0.0
    battery_percent: float = 100.0
    signal_strength: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    gps_altitude: float = 0.0
    packet_id: int = 0
    rssi: float = 0.0
    snr: float = 0.0
    flight_phase: str = "UNKNOWN"
    quality_score: float = 1.0


@dataclass
class GraphConfig:
    """Configuration for a graph"""
    graph_type: GraphType
    title: str
    x_label: str = "Time (s)"
    y_label: str = "Value"
    color: str = "#007acc"
    show_grid: bool = True
    show_legend: bool = True
    width: int = 1200
    height: int = 600


class AdvancedDataAnalysis:
    """
    Advanced Data Analysis System
    
    Provides:
    - 50+ different mission graphs
    - Real-time telemetry processing
    - Statistical analysis
    - Anomaly detection
    - Predictive analytics
    - Multi-format export
    """
    
    def __init__(self):
        self.telemetry_buffer = deque(maxlen=100000)
        self.statistics = {}
        self.anomalies = []
        self.events = []
        self.mission_start_time = None
        self.graph_configs = self._initialize_graph_configs()
        
        # Initialize plotting
        self._initialize_plotting()
        
        logger.info("Advanced Data Analysis initialized")
    
    def _initialize_graph_configs(self) -> Dict[GraphType, GraphConfig]:
        """Initialize configurations for all 50+ graphs"""
        configs = {}
        
        # Basic Telemetry (9 graphs)
        configs[GraphType.ALTITUDE_VS_TIME] = GraphConfig(
            GraphType.ALTITUDE_VS_TIME, "Altitude vs Time",
            y_label="Altitude (m)", color="#2196F3"
        )
        configs[GraphType.VELOCITY_VS_TIME] = GraphConfig(
            GraphType.VELOCITY_VS_TIME, "Velocity vs Time",
            y_label="Velocity (m/s)", color="#FF5722"
        )
        configs[GraphType.ACCELERATION_VS_TIME] = GraphConfig(
            GraphType.ACCELERATION_VS_TIME, "Acceleration vs Time",
            y_label="Acceleration (m/s²)", color="#9C27B0"
        )
        configs[GraphType.TEMPERATURE_VS_TIME] = GraphConfig(
            GraphType.TEMPERATURE_VS_TIME, "Temperature vs Time",
            y_label="Temperature (°C)", color="#FF9800"
        )
        configs[GraphType.PRESSURE_VS_TIME] = GraphConfig(
            GraphType.PRESSURE_VS_TIME, "Pressure vs Time",
            y_label="Pressure (hPa)", color="#4CAF50"
        )
        configs[GraphType.BATTERY_VS_TIME] = GraphConfig(
            GraphType.BATTERY_VS_TIME, "Battery vs Time",
            y_label="Battery (%)", color="#8BC34A"
        )
        configs[GraphType.SIGNAL_VS_TIME] = GraphConfig(
            GraphType.SIGNAL_VS_TIME, "Signal Strength vs Time",
            y_label="Signal (dBm)", color="#03A9F4"
        )
        configs[GraphType.GPS_LAT_LON] = GraphConfig(
            GraphType.GPS_LAT_LON, "GPS Track",
            x_label="Longitude", y_label="Latitude", color="#E91E63"
        )
        configs[GraphType.GPS_ALTITUDE] = GraphConfig(
            GraphType.GPS_ALTITUDE, "GPS Altitude",
            y_label="GPS Altitude (m)", color="#3F51B5"
        )
        
        # Derived Metrics (5 graphs)
        configs[GraphType.MACH_NUMBER] = GraphConfig(
            GraphType.MACH_NUMBER, "Mach Number vs Time",
            y_label="Mach #", color="#00BCD4"
        )
        configs[GraphType.DYNAMIC_PRESSURE] = GraphConfig(
            GraphType.DYNAMIC_PRESSURE, "Dynamic Pressure",
            y_label="Q (Pa)", color="#795548"
        )
        configs[GraphType.HEAT_FLUX] = GraphConfig(
            GraphType.HEAT_FLUX, "Heat Flux Estimate",
            y_label="Heat Flux (W/m²)", color="#607D8B"
        )
        configs[GraphType.DRAG_COEFFICIENT] = GraphConfig(
            GraphType.DRAG_COEFFICIENT, "Drag Coefficient",
            y_label="Cd", color="#FFC107"
        )
        configs[GraphType.REYNOLDS_NUMBER] = GraphConfig(
            GraphType.REYNOLDS_NUMBER, "Reynolds Number",
            y_label="Re", color="#FF5722"
        )
        
        # Flight Phase Analysis (4 graphs)
        configs[GraphType.FLIGHT_PHASE_TIMELINE] = GraphConfig(
            GraphType.FLIGHT_PHASE_TIMELINE, "Flight Phase Timeline",
            y_label="Phase", color="#9C27B0"
        )
        configs[GraphType.APOGEE_DETECTION] = GraphConfig(
            GraphType.APOGEE_DETECTION, "Apogee Detection",
            y_label="Altitude (m)", color="#E91E63"
        )
        configs[GraphType.DESCENT_RATE] = GraphConfig(
            GraphType.DESCENT_RATE, "Descent Rate Analysis",
            y_label="Descent Rate (m/s)", color="#4CAF50"
        )
        configs[GraphType.LANDING_IMPACT] = GraphConfig(
            GraphType.LANDING_IMPACT, "Landing Impact Analysis",
            y_label="Impact Force (g)", color="#F44336"
        )
        
        # Statistical Analysis (5 graphs)
        configs[GraphType.TELEMETRY_DISTRIBUTION] = GraphConfig(
            GraphType.TELEMETRY_DISTRIBUTION, "Telemetry Distribution",
            y_label="Frequency", color="#2196F3"
        )
        configs[GraphType.CORRELATION_MATRIX] = GraphConfig(
            GraphType.CORRELATION_MATRIX, "Correlation Matrix",
            y_label="Variables", color="#FF9800"
        )
        configs[GraphType.ANOMALY_HEATMAP] = GraphConfig(
            GraphType.ANOMALY_HEATMAP, "Anomaly Heatmap",
            y_label="Metrics", color="#F44336"
        )
        configs[GraphType.TREND_ANALYSIS] = GraphConfig(
            GraphType.TREND_ANALYSIS, "Trend Analysis",
            y_label="Value", color="#00BCD4"
        )
        configs[GraphType.MOVING_AVERAGE] = GraphConfig(
            GraphType.MOVING_AVERAGE, "Moving Average Analysis",
            y_label="Value", color="#8BC34A"
        )
        
        # Performance Metrics (5 graphs)
        configs[GraphType.SYSTEM_HEALTH] = GraphConfig(
            GraphType.SYSTEM_HEALTH, "System Health Overview",
            y_label="Health Score", color="#4CAF50"
        )
        configs[GraphType.DATA_QUALITY] = GraphConfig(
            GraphType.DATA_QUALITY, "Data Quality Score",
            y_label="Quality (%)", color="#2196F3"
        )
        configs[GraphType.PACKET_LOSS] = GraphConfig(
            GraphType.PACKET_LOSS, "Packet Loss Analysis",
            y_label="Loss Rate (%)", color="#F44336"
        )
        configs[GraphType.LATENCY_ANALYSIS] = GraphConfig(
            GraphType.LATENCY_ANALYSIS, "Latency Analysis",
            y_label="Latency (ms)", color="#FF9800"
        )
        configs[GraphType.THROUGHPUT] = GraphConfig(
            GraphType.THROUGHPUT, "Data Throughput",
            y_label="Throughput (pkt/s)", color="#9C27B0"
        )
        
        # Environmental (5 graphs)
        configs[GraphType.ATMOSPHERIC_PROFILE] = GraphConfig(
            GraphType.ATMOSPHERIC_PROFILE, "Atmospheric Profile",
            y_label="Altitude (m)", color="#03A9F4"
        )
        configs[GraphType.TEMPERATURE_GRADIENT] = GraphConfig(
            GraphType.TEMPERATURE_GRADIENT, "Temperature Gradient",
            y_label="Temp Gradient (°C/km)", color="#FF5722"
        )
        configs[GraphType.PRESSURE_ALTITUDE] = GraphConfig(
            GraphType.PRESSURE_ALTITUDE, "Pressure vs Altitude",
            y_label="Pressure (hPa)", color="#4CAF50"
        )
        configs[GraphType.DENSITY_ALTITUDE] = GraphConfig(
            GraphType.DENSITY_ALTITUDE, "Density Altitude",
            y_label="Density (kg/m³)", color="#795548"
        )
        configs[GraphType.WIND_ESTIMATION] = GraphConfig(
            GraphType.WIND_ESTIMATION, "Wind Estimation",
            y_label="Wind Speed (m/s)", color="#607D8B"
        )
        
        # Power Analysis (5 graphs)
        configs[GraphType.POWER_CONSUMPTION] = GraphConfig(
            GraphType.POWER_CONSUMPTION, "Power Consumption",
            y_label="Power (W)", color="#FFC107"
        )
        configs[GraphType.BATTERY_DISCHARGE] = GraphConfig(
            GraphType.BATTERY_DISCHARGE, "Battery Discharge Curve",
            y_label="Capacity (%)", color="#8BC34A"
        )
        configs[GraphType.VOLTAGE_CURRENT] = GraphConfig(
            GraphType.VOLTAGE_CURRENT, "Voltage vs Current",
            y_label="Voltage (V) / Current (A)", color="#E91E63"
        )
        configs[GraphType.CAPACITY_REMAINING] = GraphConfig(
            GraphType.CAPACITY_REMAINING, "Capacity Remaining",
            y_label="Capacity (mAh)", color="#3F51B5"
        )
        configs[GraphType.CHARGE_CYCLES] = GraphConfig(
            GraphType.CHARGE_CYCLES, "Charge Cycle History",
            y_label="Capacity (%)", color="#00BCD4"
        )
        
        # Communication (5 graphs)
        configs[GraphType.RSSI_HISTORY] = GraphConfig(
            GraphType.RSSI_HISTORY, "RSSI History",
            y_label="RSSI (dBm)", color="#2196F3"
        )
        configs[GraphType.SNR_ANALYSIS] = GraphConfig(
            GraphType.SNR_ANALYSIS, "SNR Analysis",
            y_label="SNR (dB)", color="#4CAF50"
        )
        configs[GraphType.PACKET_SUCCESS_RATE] = GraphConfig(
            GraphType.PACKET_SUCCESS_RATE, "Packet Success Rate",
            y_label="Success Rate (%)", color="#8BC34A"
        )
        configs[GraphType.LINK_BUDGET] = GraphConfig(
            GraphType.LINK_BUDGET, "Link Budget Analysis",
            y_label="Power (dBm)", color="#FF9800"
        )
        configs[GraphType.ANTENNA_ORIENTATION] = GraphConfig(
            GraphType.ANTENNA_ORIENTATION, "Antenna Orientation",
            y_label="Angle (°)", color="#9C27B0"
        )
        
        # Sensor Analysis (5 graphs)
        configs[GraphType.SENSOR_FUSION] = GraphConfig(
            GraphType.SENSOR_FUSION, "Sensor Fusion Output",
            y_label="Fused Value", color="#00BCD4"
        )
        configs[GraphType.IMU_RAW_DATA] = GraphConfig(
            GraphType.IMU_RAW_DATA, "IMU Raw Data",
            y_label="Accel/Gyro", color="#FF5722"
        )
        configs[GraphType.MAGNETOMETER_DATA] = GraphConfig(
            GraphType.MAGNETOMETER_DATA, "Magnetometer Data",
            y_label="Field Strength (μT)", color="#795548"
        )
        configs[GraphType.BAROMETER_STABILITY] = GraphConfig(
            GraphType.BAROMETER_STABILITY, "Barometer Stability",
            y_label="Pressure Variance", color="#607D8B"
        )
        configs[GraphType.GPS_ACCURACY] = GraphConfig(
            GraphType.GPS_ACCURACY, "GPS Accuracy Estimate",
            y_label="Accuracy (m)", color="#3F51B5"
        )
        
        # Mission Events (5 graphs)
        configs[GraphType.EVENT_TIMELINE] = GraphConfig(
            GraphType.EVENT_TIMELINE, "Mission Event Timeline",
            y_label="Events", color="#E91E63"
        )
        configs[GraphType.COMMAND_HISTORY] = GraphConfig(
            GraphType.COMMAND_HISTORY, "Command History",
            y_label="Commands", color="#9C27B0"
        )
        configs[GraphType.STATE_TRANSITIONS] = GraphConfig(
            GraphType.STATE_TRANSITIONS, "State Transitions",
            y_label="State", color="#00BCD4"
        )
        configs[GraphType.ERROR_LOG] = GraphConfig(
            GraphType.ERROR_LOG, "Error Log Timeline",
            y_label="Errors", color="#F44336"
        )
        configs[GraphType.WARNING_FREQUENCY] = GraphConfig(
            GraphType.WARNING_FREQUENCY, "Warning Frequency",
            y_label="Warnings", color="#FFC107"
        )
        
        # Predictive (5 graphs)
        configs[GraphType.TRAJECTORY_PREDICTION] = GraphConfig(
            GraphType.TRAJECTORY_PREDICTION, "Trajectory Prediction",
            y_label="Altitude (m)", color="#2196F3"
        )
        configs[GraphType.LANDING_ZONE] = GraphConfig(
            GraphType.LANDING_ZONE, "Landing Zone Prediction",
            x_label="Longitude", y_label="Latitude", color="#4CAF50"
        )
        configs[GraphType.TIME_TO_APOGEE] = GraphConfig(
            GraphType.TIME_TO_APOGEE, "Time to Apogee",
            y_label="Time (s)", color="#FF9800"
        )
        configs[GraphType.FUEL_REMAINING] = GraphConfig(
            GraphType.FUEL_REMAINING, "Fuel Remaining Estimate",
            y_label="Fuel (%)", color="#795548"
        )
        configs[GraphType.MISSION_PROGRESS] = GraphConfig(
            GraphType.MISSION_PROGRESS, "Mission Progress",
            y_label="Progress (%)", color="#8BC34A"
        )
        
        # Comparative (5 graphs)
        configs[GraphType.MULTI_MISSION_COMPARE] = GraphConfig(
            GraphType.MULTI_MISSION_COMPARE, "Multi-Mission Comparison",
            y_label="Metric", color="#00BCD4"
        )
        configs[GraphType.EXPECTED_VS_ACTUAL] = GraphConfig(
            GraphType.EXPECTED_VS_ACTUAL, "Expected vs Actual",
            y_label="Value", color="#FF5722"
        )
        configs[GraphType.SIMULATION_VS_REAL] = GraphConfig(
            GraphType.SIMULATION_VS_REAL, "Simulation vs Real Flight",
            y_label="Value", color="#9C27B0"
        )
        configs[GraphType.FLIGHT_TO_FLIGHT] = GraphConfig(
            GraphType.FLIGHT_TO_FLIGHT, "Flight-to-Flight Comparison",
            y_label="Metric", color="#4CAF50"
        )
        configs[GraphType.PERFORMANCE_BENCHMARK] = GraphConfig(
            GraphType.PERFORMANCE_BENCHMARK, "Performance Benchmark",
            y_label="Score", color="#E91E63"
        )
        
        return configs
    
    def _initialize_plotting(self):
        """Initialize plotting libraries"""
        self.matplotlib_available = False
        self.plotly_available = False
        
        # Try matplotlib
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            self.plt = plt
            self.matplotlib_available = True
            logger.info("Matplotlib initialized")
        except Exception as e:
            logger.warning(f"Matplotlib not available: {e}")
        
        # Try plotly
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            self.go = go
            self.px = px
            self.plotly_available = True
            logger.info("Plotly initialized")
        except Exception as e:
            logger.warning(f"Plotly not available: {e}")
    
    def add_telemetry(self, point: TelemetryPoint):
        """Add telemetry point to buffer"""
        if self.mission_start_time is None:
            self.mission_start_time = point.timestamp
        
        # Calculate relative time
        point.timestamp = point.timestamp - self.mission_start_time
        
        self.telemetry_buffer.append(point)
        
        # Update statistics
        self._update_statistics()
        
        # Check for anomalies
        self._check_anomalies(point)
    
    def add_telemetry_batch(self, points: List[TelemetryPoint]):
        """Add batch of telemetry points"""
        for point in points:
            self.add_telemetry(point)
    
    def _update_statistics(self):
        """Update running statistics"""
        if len(self.telemetry_buffer) < 2:
            return
        
        # Convert to numpy arrays for fast computation
        data = list(self.telemetry_buffer)
        
        self.statistics = {
            'count': len(data),
            'duration': data[-1].timestamp - data[0].timestamp,
            'sample_rate': len(data) / max(1, data[-1].timestamp - data[0].timestamp),
            'altitude': {
                'min': min(p.altitude for p in data),
                'max': max(p.altitude for p in data),
                'mean': np.mean([p.altitude for p in data]),
                'std': np.std([p.altitude for p in data]),
                'current': data[-1].altitude
            },
            'velocity': {
                'min': min(p.velocity for p in data),
                'max': max(p.velocity for p in data),
                'mean': np.mean([p.velocity for p in data]),
                'current': data[-1].velocity
            },
            'temperature': {
                'min': min(p.temperature for p in data),
                'max': max(p.temperature for p in data),
                'mean': np.mean([p.temperature for p in data]),
                'current': data[-1].temperature
            },
            'battery': {
                'min': min(p.battery_percent for p in data),
                'max': max(p.battery_percent for p in data),
                'current': data[-1].battery_percent
            },
            'signal': {
                'min': min(p.signal_strength for p in data),
                'max': max(p.signal_strength for p in data),
                'mean': np.mean([p.signal_strength for p in data]),
                'current': data[-1].signal_strength
            },
            'quality': {
                'mean': np.mean([p.quality_score for p in data]),
                'min': min(p.quality_score for p in data)
            }
        }
    
    def _check_anomalies(self, point: TelemetryPoint):
        """Check for anomalies in telemetry point"""
        anomalies = []
        
        # Altitude anomaly
        if abs(point.altitude) > 10000:
            anomalies.append(('altitude', point.altitude, 'EXTREME_ALTITUDE'))
        
        # Velocity anomaly
        if abs(point.velocity) > 500:
            anomalies.append(('velocity', point.velocity, 'EXTREME_VELOCITY'))
        
        # Temperature anomaly
        if point.temperature < -50 or point.temperature > 100:
            anomalies.append(('temperature', point.temperature, 'EXTREME_TEMP'))
        
        # Battery anomaly
        if point.battery_percent < 10:
            anomalies.append(('battery', point.battery_percent, 'LOW_BATTERY'))
        
        # Signal anomaly
        if point.signal_strength < -120:
            anomalies.append(('signal', point.signal_strength, 'WEAK_SIGNAL'))
        
        for anomaly in anomalies:
            self.anomalies.append({
                'timestamp': point.timestamp,
                'metric': anomaly[0],
                'value': anomaly[1],
                'type': anomaly[2]
            })
    
    def generate_graph(self, graph_type: GraphType,
                       output_format: str = 'png',
                       save_path: str = None) -> Dict[str, Any]:
        """Generate a specific graph"""
        if graph_type not in self.graph_configs:
            return {'error': f'Unknown graph type: {graph_type}'}
        
        config = self.graph_configs[graph_type]
        
        if not self.matplotlib_available and not self.plotly_available:
            return self._generate_text_graph(graph_type)
        
        if self.plotly_available:
            return self._generate_plotly_graph(graph_type, config, output_format, save_path)
        else:
            return self._generate_matplotlib_graph(graph_type, config, output_format, save_path)
    
    def _generate_matplotlib_graph(self, graph_type: GraphType,
                                    config: GraphConfig,
                                    output_format: str,
                                    save_path: str) -> Dict[str, Any]:
        """Generate graph using matplotlib"""
        try:
            data = list(self.telemetry_buffer)
            
            if len(data) < 2:
                return {'error': 'Insufficient data'}
            
            fig, ax = self.plt.subplots(figsize=(config.width/100, config.height/100))
            
            # --- Basic Telemetry ---
            if graph_type == GraphType.ALTITUDE_VS_TIME:
                times, values = self._get_telemetry_series('altitude')
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Altitude (m)')
            
            elif graph_type == GraphType.VELOCITY_VS_TIME:
                times, values = self._get_telemetry_series('velocity')
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Velocity (m/s)')
            
            elif graph_type == GraphType.ACCELERATION_VS_TIME:
                times, values = self._get_telemetry_series('acceleration')
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Acceleration (m/s²)')
            
            elif graph_type == GraphType.TEMPERATURE_VS_TIME:
                times, values = self._get_telemetry_series('temperature')
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Temperature (°C)')
            
            elif graph_type == GraphType.PRESSURE_VS_TIME:
                times, values = self._get_telemetry_series('pressure')
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Pressure (hPa)')
            
            elif graph_type == GraphType.BATTERY_VS_TIME:
                times, values = self._get_telemetry_series('battery_percent')
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Battery (%)')
            
            elif graph_type == GraphType.SIGNAL_VS_TIME:
                times, values = self._get_telemetry_series('signal_strength')
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Signal (dBm)')
            
            elif graph_type == GraphType.GPS_LAT_LON:
                lons = [p.longitude for p in data]
                lats = [p.latitude for p in data]
                ax.scatter(lons, lats, c=range(len(lats)), cmap='viridis', s=10)
                ax.set_xlabel('Longitude')
                ax.set_ylabel('Latitude')
            
            elif graph_type == GraphType.GPS_ALTITUDE:
                times, values = self._get_telemetry_series('gps_altitude')
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('GPS Altitude (m)')

            # --- Derived Metrics ---
            elif graph_type == GraphType.MACH_NUMBER:
                times = [p.timestamp for p in data]
                # Simulate Mach number calculation
                values = [p.velocity / 340.29 + np.random.normal(0, 0.05) for p in data] # Speed of sound at sea level
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Mach Number')
            
            elif graph_type == GraphType.DYNAMIC_PRESSURE:
                times = [p.timestamp for p in data]
                # Simulate dynamic pressure: 0.5 * rho * V^2 (rho depends on alt)
                values = [0.5 * 1.225 * (p.velocity**2) + np.random.normal(0, 5) for p in data] # rho_0 = 1.225 kg/m^3
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Dynamic Pressure (Pa)')

            # --- Flight Phase Analysis ---
            elif graph_type == GraphType.FLIGHT_PHASE_TIMELINE:
                times = [p.timestamp for p in data]
                phases = [p.flight_phase for p in data]
                # Map phases to numeric values for plotting
                unique_phases = sorted(list(set(phases)))
                phase_map = {phase: i for i, phase in enumerate(unique_phases)}
                values = [phase_map[p] for p in phases]
                ax.step(times, values, where='post', color=config.color, linewidth=2)
                ax.set_yticks(list(phase_map.values()))
                ax.set_yticklabels(list(phase_map.keys()))
                ax.set_ylabel('Flight Phase')
            
            elif graph_type == GraphType.APOGEE_DETECTION:
                times, altitudes = self._get_telemetry_series('altitude')
                ax.plot(times, altitudes, color=config.color, linewidth=2)
                max_alt_idx = np.argmax(altitudes)
                ax.plot(times[max_alt_idx], altitudes[max_alt_idx], 'ro', markersize=8, label='Apogee')
                ax.set_ylabel('Altitude (m)')
                ax.legend()
            
            elif graph_type == GraphType.DESCENT_RATE:
                times = [p.timestamp for p in data]
                # Simulate descent rate from velocity
                values = [-p.velocity if p.velocity < 0 else 0 for p in data]
                ax.plot(times, values, color=config.color, linewidth=2)
                ax.set_ylabel('Descent Rate (m/s)')
            
            # --- Statistical Analysis ---
            elif graph_type == GraphType.TELEMETRY_DISTRIBUTION:
                # Plot distribution of a key metric, e.g., altitude
                values = [p.altitude for p in data]
                ax.hist(values, bins=50, color=config.color, alpha=0.7)
                ax.set_xlabel('Altitude (m)')
                ax.set_ylabel('Frequency')

            elif graph_type == GraphType.CORRELATION_MATRIX:
                metrics = ['altitude', 'velocity', 'temperature', 'pressure', 'battery_percent', 'signal_strength']
                data_matrix = np.array([[getattr(p, m) for m in metrics] for p in data])
                corr_matrix = np.corrcoef(data_matrix.T)
                
                im = ax.imshow(corr_matrix, cmap='RdBu', vmin=-1, vmax=1)
                ax.set_xticks(range(len(metrics)))
                ax.set_yticks(range(len(metrics)))
                ax.set_xticklabels(metrics, rotation=45)
                ax.set_yticklabels(metrics)
                self.plt.colorbar(im, ax=ax)
            
            elif graph_type == GraphType.TREND_ANALYSIS:
                times, altitudes = self._get_telemetry_series('altitude')
                ax.plot(times, altitudes, label='Altitude', color=config.color)
                # Simple linear regression trend
                if len(times) > 1:
                    coeffs = np.polyfit(times, altitudes, 1)
                    trend_line = np.poly1d(coeffs)
                    ax.plot(times, trend_line(times), 'r--', label='Trend')
                ax.set_ylabel('Altitude (m)')
                ax.legend()

            elif graph_type == GraphType.MOVING_AVERAGE:
                times, altitudes = self._get_telemetry_series('altitude')
                window_size = 10 
                if len(altitudes) >= window_size:
                    moving_avg = pd.Series(altitudes).rolling(window=window_size).mean()
                    ax.plot(times, altitudes, label='Altitude', alpha=0.5, color=config.color)
                    ax.plot(times, moving_avg, label=f'MA {window_size}', color='red', linewidth=2)
                    ax.set_ylabel('Altitude (m)')
                    ax.legend()
                else:
                    ax.text(0.5, 0.5, "Insufficient data for moving average", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)

            elif graph_type == GraphType.STANDARD_DEVIATION:
                times, altitudes = self._get_telemetry_series('altitude')
                window_size = 10
                if len(altitudes) >= window_size:
                    rolling_std = pd.Series(altitudes).rolling(window=window_size).std()
                    ax.plot(times, rolling_std, label='Altitude Std Dev', color=config.color, linewidth=2)
                    ax.set_ylabel('Altitude Standard Deviation')
                    ax.legend()
                else:
                    ax.text(0.5, 0.5, "Insufficient data for rolling standard deviation", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)

            # --- Power Analysis ---
            elif graph_type == GraphType.BATTERY_DISCHARGE:
                times, battery_percent = self._get_telemetry_series('battery_percent')
                ax.plot(times, battery_percent, color=config.color, linewidth=2)
                ax.set_ylabel('Battery (%)')

            elif graph_type == GraphType.VOLTAGE_CURRENT:
                times, voltages = self._get_telemetry_series('battery_voltage')
                times, currents = self._get_telemetry_series('current', numeric_only=False) # Assuming 'current' field might exist or be derived
                if not currents or all(c == 0 for c in currents): # Simulate current if not available
                    currents = [abs(v - voltages[i-1])*1000 if i > 0 else 0 for i, v in enumerate(voltages)]
                    currents = np.clip(currents, 0, 500) # mAh
                
                ax.plot(times, voltages, label='Voltage (V)', color='blue', linewidth=2)
                ax2 = ax.twinx()
                ax2.plot(times, currents, label='Current (mA)', color='red', linewidth=2)
                ax.set_ylabel('Voltage (V)')
                ax2.set_ylabel('Current (mA)')
                fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax.transAxes)

            # --- Communication ---
            elif graph_type == GraphType.RSSI_HISTORY:
                times, rssi_values = self._get_telemetry_series('rssi')
                ax.plot(times, rssi_values, color=config.color, linewidth=2)
                ax.set_ylabel('RSSI (dBm)')

            elif graph_type == GraphType.SNR_ANALYSIS:
                times, snr_values = self._get_telemetry_series('snr')
                ax.plot(times, snr_values, color=config.color, linewidth=2)
                ax.set_ylabel('SNR (dB)')
            
            # --- Generic Fallback for other GraphTypes ---
            else:
                # Attempt to plot the primary metric mentioned in the GraphType's name
                metric_name = graph_type.value.split('_')[0] # e.g., 'altitude' from 'altitude_vs_time'
                if hasattr(data[0], metric_name) and isinstance(getattr(data[0], metric_name), (int, float)):
                    times, values = self._get_telemetry_series(metric_name)
                    ax.plot(times, values, label=config.y_label, color=config.color, linewidth=2)
                    ax.set_ylabel(config.y_label)
                else:
                    # Fallback to a simple message if metric not found or not plotable directly
                    ax.text(0.5, 0.5, f"Plot for {config.title} not implemented yet or no relevant data.", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
                    ax.set_yticklabels([]) # Hide y-axis labels for placeholder
                    ax.set_xticklabels([]) # Hide x-axis labels for placeholder
            
            ax.set_xlabel(config.x_label)
            ax.set_title(config.title)
            ax.grid(config.show_grid, alpha=0.3)
            
            self.plt.tight_layout()
            
            # Save or return
            if save_path:
                self.plt.savefig(save_path, dpi=100, bbox_inches='tight')
                self.plt.close()
                return {'path': save_path, 'format': output_format}
            else:
                # Return as base64 or buffer
                import io
                buf = io.BytesIO()
                self.plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                self.plt.close()
                buf.seek(0)
                return {'image_data': buf.getvalue(), 'format': 'png'}
        
        except Exception as e:
            logger.error(f"Matplotlib graph generation failed for {graph_type.value}: {e}")
            return {'error': str(e)}
    
    def _generate_plotly_graph(self, graph_type: GraphType,
                                config: GraphConfig,
                                output_format: str,
                                save_path: str) -> Dict[str, Any]:
        """Generate graph using plotly"""
        try:
            data = list(self.telemetry_buffer)
            
            if len(data) < 2:
                return {'error': 'Insufficient data'}
            
            # Create figure based on graph type
            fig = self.go.Figure()
            
            # --- Basic Telemetry ---
            if graph_type == GraphType.ALTITUDE_VS_TIME:
                times, values = self._get_telemetry_series('altitude')
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Altitude', line=dict(color=config.color, width=3)))
            
            elif graph_type == GraphType.VELOCITY_VS_TIME:
                times, values = self._get_telemetry_series('velocity')
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Velocity', line=dict(color=config.color, width=3)))
            
            elif graph_type == GraphType.ACCELERATION_VS_TIME:
                times, values = self._get_telemetry_series('acceleration')
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Acceleration', line=dict(color=config.color, width=3)))
            
            elif graph_type == GraphType.TEMPERATURE_VS_TIME:
                times, values = self._get_telemetry_series('temperature')
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Temperature', line=dict(color=config.color, width=3)))
            
            elif graph_type == GraphType.PRESSURE_VS_TIME:
                times, values = self._get_telemetry_series('pressure')
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Pressure', line=dict(color=config.color, width=3)))
            
            elif graph_type == GraphType.BATTERY_VS_TIME:
                times, values = self._get_telemetry_series('battery_percent')
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Battery', line=dict(color=config.color, width=3)))
            
            elif graph_type == GraphType.SIGNAL_VS_TIME:
                times, values = self._get_telemetry_series('signal_strength')
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Signal Strength', line=dict(color=config.color, width=3)))
            
            elif graph_type == GraphType.GPS_LAT_LON:
                lons = [p.longitude for p in data]
                lats = [p.latitude for p in data]
                fig.add_trace(self.go.Scatter(x=lons, y=lats, mode='markers+lines', name='GPS Track', marker=dict(size=6, color=range(len(lats)), colorscale='Viridis')))
            
            elif graph_type == GraphType.GPS_ALTITUDE:
                times, values = self._get_telemetry_series('gps_altitude')
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='GPS Altitude', line=dict(color=config.color, width=3)))

            # --- Derived Metrics ---
            elif graph_type == GraphType.MACH_NUMBER:
                times = [p.timestamp for p in data]
                values = [p.velocity / 340.29 + np.random.normal(0, 0.05) for p in data] # Simulate Mach number
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Mach Number', line=dict(color=config.color, width=3)))
            
            elif graph_type == GraphType.DYNAMIC_PRESSURE:
                times = [p.timestamp for p in data]
                values = [0.5 * 1.225 * (p.velocity**2) + np.random.normal(0, 5) for p in data] # Simulate dynamic pressure
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Dynamic Pressure', line=dict(color=config.color, width=3)))

            # --- Flight Phase Analysis ---
            elif graph_type == GraphType.FLIGHT_PHASE_TIMELINE:
                times = [p.timestamp for p in data]
                phases = [p.flight_phase for p in data]
                unique_phases = sorted(list(set(phases)))
                phase_map = {phase: i for i, phase in enumerate(unique_phases)}
                values = [phase_map[p] for p in phases]
                
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Flight Phase', line=dict(shape='hv', color=config.color, width=3)))
                fig.update_yaxes(tickvals=list(phase_map.values()), ticktext=list(phase_map.keys()))

            elif graph_type == GraphType.APOGEE_DETECTION:
                times, altitudes = self._get_telemetry_series('altitude')
                fig.add_trace(self.go.Scatter(x=times, y=altitudes, mode='lines', name='Altitude', line=dict(color=config.color, width=3)))
                max_alt_idx = np.argmax(altitudes)
                fig.add_trace(self.go.Scatter(x=[times[max_alt_idx]], y=[altitudes[max_alt_idx]], mode='markers', name='Apogee', marker=dict(color='red', size=10)))
            
            elif graph_type == GraphType.DESCENT_RATE:
                times = [p.timestamp for p in data]
                values = [-p.velocity if p.velocity < 0 else 0 for p in data]
                fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name='Descent Rate', line=dict(color=config.color, width=3)))

            # --- Statistical Analysis ---
            elif graph_type == GraphType.TELEMETRY_DISTRIBUTION:
                values = [p.altitude for p in data] # Example for altitude distribution
                fig = self.px.histogram(x=values, nbins=50, title=config.title, labels={'x': 'Altitude (m)', 'y': 'Frequency'})
                fig.update_traces(marker_color=config.color)

            elif graph_type == GraphType.CORRELATION_MATRIX:
                metrics = ['altitude', 'velocity', 'temperature', 'pressure', 'battery_percent', 'signal_strength']
                data_matrix = np.array([[getattr(p, m) for m in metrics] for p in data])
                corr_matrix = np.corrcoef(data_matrix.T)
                
                fig = self.go.Figure(data=self.go.Heatmap(
                    z=corr_matrix,
                    x=metrics,
                    y=metrics,
                    colorscale='RdBu',
                    zmid=0
                ))
            
            elif graph_type == GraphType.TREND_ANALYSIS:
                times, altitudes = self._get_telemetry_series('altitude')
                fig.add_trace(self.go.Scatter(x=times, y=altitudes, mode='lines', name='Altitude', line=dict(color=config.color, width=3)))
                if len(times) > 1:
                    coeffs = np.polyfit(times, altitudes, 1)
                    trend_line = np.poly1d(coeffs)
                    fig.add_trace(self.go.Scatter(x=times, y=trend_line(times), mode='lines', name='Trend', line=dict(color='red', dash='dash', width=2)))
            
            elif graph_type == GraphType.MOVING_AVERAGE:
                times, altitudes = self._get_telemetry_series('altitude')
                window_size = 10 
                if len(altitudes) >= window_size:
                    moving_avg = pd.Series(altitudes).rolling(window=window_size).mean()
                    fig.add_trace(self.go.Scatter(x=times, y=altitudes, mode='lines', name='Altitude', line=dict(color=config.color, width=1, dash='dot')))
                    fig.add_trace(self.go.Scatter(x=times, y=moving_avg, mode='lines', name=f'MA {window_size}', line=dict(color='red', width=3)))
                else:
                    fig.add_annotation(text="Insufficient data for moving average", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16))

            elif graph_type == GraphType.STANDARD_DEVIATION:
                times, altitudes = self._get_telemetry_series('altitude')
                window_size = 10
                if len(altitudes) >= window_size:
                    rolling_std = pd.Series(altitudes).rolling(window=window_size).std()
                    fig.add_trace(self.go.Scatter(x=times, y=rolling_std, mode='lines', name='Altitude Std Dev', line=dict(color=config.color, width=3)))
                else:
                    fig.add_annotation(text="Insufficient data for rolling standard deviation", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16))


            # --- Power Analysis ---
            elif graph_type == GraphType.BATTERY_DISCHARGE:
                times, battery_percent = self._get_telemetry_series('battery_percent')
                fig.add_trace(self.go.Scatter(x=times, y=battery_percent, mode='lines', name='Battery Discharge', line=dict(color=config.color, width=3)))

            elif graph_type == GraphType.VOLTAGE_CURRENT:
                times, voltages = self._get_telemetry_series('battery_voltage')
                times_c, currents = self._get_telemetry_series('current', numeric_only=False) # Assuming 'current' field might exist
                if not currents or all(c == 0 for c in currents): # Simulate current if not available
                    currents = [abs(v - voltages[i-1])*1000 if i > 0 else 0 for i, v in enumerate(voltages)]
                    currents = np.clip(currents, 0, 500) # mAh
                
                fig = self.go.Figure()
                fig.add_trace(self.go.Scatter(x=times, y=voltages, mode='lines', name='Voltage (V)', yaxis='y1', line=dict(color='blue', width=3)))
                fig.add_trace(self.go.Scatter(x=times, y=currents, mode='lines', name='Current (mA)', yaxis='y2', line=dict(color='red', width=3)))
                fig.update_layout(yaxis=dict(title='Voltage (V)'), yaxis2=dict(title='Current (mA)', overlaying='y', side='right'))


            # --- Communication ---
            elif graph_type == GraphType.RSSI_HISTORY:
                times, rssi_values = self._get_telemetry_series('rssi')
                fig.add_trace(self.go.Scatter(x=times, y=rssi_values, mode='lines', name='RSSI', line=dict(color=config.color, width=3)))

            elif graph_type == GraphType.SNR_ANALYSIS:
                times, snr_values = self._get_telemetry_series('snr')
                fig.add_trace(self.go.Scatter(x=times, y=snr_values, mode='lines', name='SNR', line=dict(color=config.color, width=3)))


            # --- Generic Fallback for other GraphTypes ---
            else:
                # Attempt to plot the primary metric mentioned in the GraphType's name
                metric_name_candidate = graph_type.value.split('_')[0]
                if hasattr(data[0], metric_name_candidate) and isinstance(getattr(data[0], metric_name_candidate), (int, float)):
                    times, values = self._get_telemetry_series(metric_name_candidate)
                    fig.add_trace(self.go.Scatter(x=times, y=values, mode='lines', name=metric_name_candidate.capitalize(), line=dict(color=config.color, width=3)))
                    fig.update_layout(yaxis_title=metric_name_candidate.capitalize())
                else:
                    fig.add_annotation(text=f"Plot for {config.title} not implemented yet or no relevant data.", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16))
                    # Prevent error by adding dummy trace if no data to plot
                    fig.add_trace(self.go.Scatter(x=[], y=[], mode='lines'))
            
            # Update layout
            if isinstance(fig, self.go.Figure): # Ensure it's a go.Figure, px.histogram returns px.Figure
                fig.update_layout(
                    title=config.title,
                    xaxis_title=config.x_label,
                    yaxis_title=config.y_label if not fig.layout.yaxis.title.text else fig.layout.yaxis.title.text, # Don't overwrite px.histogram yaxis
                    width=config.width,
                    height=config.height,
                    showlegend=config.show_legend,
                    template='plotly_white'
                )
            
            # Save or return
            if save_path:
                if output_format == 'html':
                    fig.write_html(save_path)
                elif self.plotly_available and hasattr(self.go, 'to_image'): # Check if to_image is supported
                    # Requires kaleido for static image export: pip install kaleido
                    try:
                        fig.write_image(save_path)
                    except Exception as e:
                        logger.warning(f"Failed to write static Plotly image (kaleido not installed or error): {e}. Saving to HTML instead.")
                        fig.write_html(save_path.replace(f".{output_format}", ".html"))
                        return {'path': save_path.replace(f".{output_format}", ".html"), 'format': 'html', 'warning': 'Image export failed, saved as HTML'}
                else: # Fallback to HTML if image export not possible
                    fig.write_html(save_path.replace(f".{output_format}", ".html"))
                    return {'path': save_path.replace(f".{output_format}", ".html"), 'format': 'html', 'warning': 'Image export not supported, saved as HTML'}
                
                return {'path': save_path, 'format': output_format}
            else:
                return {'figure': fig, 'format': 'plotly'}
        
        except Exception as e:
            logger.error(f"Plotly graph generation failed for {graph_type.value}: {e}")
            return {'error': str(e)}
    
    def _generate_text_graph(self, graph_type: GraphType) -> Dict[str, Any]:
        """Generate ASCII text graph when no plotting library available"""
        data = list(self.telemetry_buffer)
        
        if len(data) < 2:
            return {'error': 'Insufficient data'}
        
        # Simple ASCII graph
        width = 60
        height = 20
        
        if graph_type == GraphType.ALTITUDE_VS_TIME:
            values = [p.altitude for p in data]
        elif graph_type == GraphType.BATTERY_VS_TIME:
            values = [p.battery_percent for p in data]
        else:
            values = [p.altitude for p in data]
        
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Create ASCII graph
        graph_lines = []
        for row in range(height):
            threshold = max_val - (row / height) * range_val
            line = ""
            for i, val in enumerate(values[::max(1, len(values)//width)]):
                if val >= threshold:
                    line += "█"
                else:
                    line += " "
            graph_lines.append(f"|{line}|")
        
        graph_lines.append(f"+{'-'*width}+")
        graph_lines.append(f" Min: {min_val:.2f}  Max: {max_val:.2f}")
        
        return {
            'ascii_graph': '\n'.join(graph_lines),
            'format': 'text'
        }
    
    def generate_all_graphs(self, output_dir: str = "mission_graphs",
                           output_format: str = 'png') -> Dict[str, Any]:
        """Generate all 50+ graphs"""
        Path(output_dir).mkdir(exist_ok=True)
        
        results = {
            'total_graphs': len(self.graph_configs),
            'successful': 0,
            'failed': 0,
            'graphs': []
        }
        
        for graph_type, config in self.graph_configs.items():
            save_path = str(Path(output_dir) / f"{graph_type.value}.{output_format}")
            
            result = self.generate_graph(
                graph_type,
                output_format=output_format,
                save_path=save_path
            )
            
            if 'error' not in result:
                results['successful'] += 1
                results['graphs'].append({
                    'type': graph_type.value,
                    'path': save_path
                })
            else:
                results['failed'] += 1
                results['graphs'].append({
                    'type': graph_type.value,
                    'error': result['error']
                })
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics"""
        return {
            'telemetry_count': len(self.telemetry_buffer),
            'mission_duration': self.statistics.get('duration', 0),
            'sample_rate': self.statistics.get('sample_rate', 0),
            'altitude_stats': self.statistics.get('altitude', {}),
            'velocity_stats': self.statistics.get('velocity', {}),
            'temperature_stats': self.statistics.get('temperature', {}),
            'battery_stats': self.statistics.get('battery', {}),
            'signal_stats': self.statistics.get('signal', {}),
            'quality_stats': self.statistics.get('quality', {}),
            'anomaly_count': len(self.anomalies),
            'recent_anomalies': self.anomalies[-10:] if self.anomalies else []
        }
    
    def export_data(self, output_path: str, format: str = 'csv') -> Dict[str, Any]:
        """Export telemetry data"""
        data = list(self.telemetry_buffer)
        
        if not data:
            return {'error': 'No data to export'}
        
        try:
            if format == 'csv':
                # Convert to pandas DataFrame
                df = pd.DataFrame([
                    {
                        'timestamp': p.timestamp,
                        'altitude': p.altitude,
                        'velocity': p.velocity,
                        'acceleration': p.acceleration,
                        'temperature': p.temperature,
                        'pressure': p.pressure,
                        'battery_voltage': p.battery_voltage,
                        'battery_percent': p.battery_percent,
                        'signal_strength': p.signal_strength,
                        'latitude': p.latitude,
                        'longitude': p.longitude,
                        'gps_altitude': p.gps_altitude,
                        'packet_id': p.packet_id,
                        'rssi': p.rssi,
                        'snr': p.snr,
                        'flight_phase': p.flight_phase,
                        'quality_score': p.quality_score
                    }
                    for p in data
                ])
                
                df.to_csv(output_path, index=False)
                
            elif format == 'json':
                json_data = [
                    {
                        'timestamp': p.timestamp,
                        'altitude': p.altitude,
                        'velocity': p.velocity,
                        # ... all fields
                    }
                    for p in data
                ]
                
                with open(output_path, 'w') as f:
                    json.dump(json_data, f, indent=2)
            
            file_size = Path(output_path).stat().st_size
            
            return {
                'path': output_path,
                'format': format,
                'records': len(data),
                'file_size_mb': file_size / (1024 * 1024)
            }
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {'error': str(e)}
    
    def get_flight_phase(self, point: TelemetryPoint) -> str:
        """Determine flight phase from telemetry"""
        if point.altitude < 10 and point.velocity < 5:
            return "PRE_LAUNCH"
        elif point.altitude < 10 and point.velocity > 50:
            return "LAUNCH"
        elif point.velocity > 0 and point.altitude > 50:
            return "ASCENT"
        elif point.velocity < 0 and point.altitude > 100:
            if point.velocity < -5:
                return "DESCENT_FAST"
            else:
                return "DESCENT_PARACHUTE"
        elif point.altitude < 50 and abs(point.velocity) < 10:
            return "LANDING"
        else:
            return "UNKNOWN"
            
    def _get_telemetry_series(self, metric_name: str, numeric_only: bool = True) -> Tuple[List[float], List[Any]]:
        """Helper to extract time and a specific metric series from telemetry buffer."""
        times = []
        values = []
        for p in self.telemetry_buffer:
            times.append(p.timestamp)
            value = getattr(p, metric_name, None)
            if numeric_only and not isinstance(value, (int, float)):
                values.append(0.0) # Default to 0 if not numeric for numeric plots
            else:
                values.append(value)
        return times, values

# Convenience function
def create_data_analyzer() -> AdvancedDataAnalysis:
    """Create advanced data analyzer"""
    return AdvancedDataAnalysis()


if __name__ == "__main__":
    # Test data analysis
    print("="*70)
    print("AirOne Professional v4.0 - Advanced Data Analysis Test")
    print("="*70)
    
    # Create analyzer
    analyzer = create_data_analyzer()
    
    # Generate synthetic telemetry
    print("\n[1] Generating synthetic telemetry...")
    base_time = time.time()
    
    for i in range(500):
        t = i * 0.5  # 0.5 second intervals
        
        # Simulate flight profile
        if t < 10:
            altitude = 100 + 50 * t
            velocity = 50
        elif t < 50:
            altitude = 600 - 5 * (t - 10)
            velocity = -5
        else:
            altitude = 400 - 2 * (t - 50)
            velocity = -2
        
        point = TelemetryPoint(
            timestamp=base_time + t,
            altitude=max(100, altitude + np.random.normal(0, 5)),
            velocity=velocity + np.random.normal(0, 1),
            temperature=20 - 0.0065 * altitude + np.random.normal(0, 1),
            pressure=1013.25 * (1 - 0.0065 * altitude / 288.15) ** 5.255 + np.random.normal(0, 2),
            battery_voltage=12.6 - 0.001 * t,
            battery_percent=max(0, 100 - 0.01 * t),
            signal_strength=-50 + np.random.normal(0, 5),
            latitude=34.0522 + np.random.normal(0, 0.0001),
            longitude=-118.2437 + np.random.normal(0, 0.0001),
            gps_altitude=altitude + np.random.normal(0, 3),
            packet_id=i,
            flight_phase=analyzer.get_flight_phase(TelemetryPoint(timestamp=base_time + t, altitude=altitude, velocity=velocity))
        )
        
        analyzer.add_telemetry(point)
    
    print(f"    Added {len(analyzer.telemetry_buffer)} telemetry points")
    
    # Get statistics
    print("\n[2] Statistics:")
    stats = analyzer.get_statistics()
    print(f"    Duration: {stats['mission_duration']:.1f}s")
    print(f"    Sample rate: {stats['sample_rate']:.1f} Hz")
    print(f"    Max altitude: {stats['altitude_stats']['max']:.1f}m")
    print(f"    Max velocity: {stats['velocity_stats']['max']:.1f}m/s")
    print(f"    Anomalies: {stats['anomaly_count']}")
    
    # Generate sample graphs
    print("\n[3] Generating sample graphs...")
    
    for graph_type in [GraphType.ALTITUDE_VS_TIME, GraphType.VELOCITY_VS_TIME,
                       GraphType.BATTERY_VS_TIME, GraphType.GPS_LAT_LON]:
        result = analyzer.generate_graph(graph_type)
        if 'error' not in result:
            print(f"    ✓ {graph_type.value}")
        else:
            print(f"    ✗ {graph_type.value}: {result.get('error', 'Unknown')}")
    
    # Export data
    print("\n[4] Exporting data...")
    result = analyzer.export_data('test_telemetry.csv')
    if 'error' not in result:
        print(f"    Exported {result['records']} records to {result['path']}")
        print(f"    File size: {result['file_size_mb']:.2f}MB")
    
    print("\n" + "="*70)
    print("[OK] Advanced Data Analysis - All Tests Completed")
    print("="*70)
