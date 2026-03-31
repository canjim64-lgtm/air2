"""
Advanced Telemetry Features Module
Enhanced telemetry processing, compression, and analysis for AirOne
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import queue
import time
import json
import zlib
import logging
from collections import deque


class TelemetryEventType(Enum):
    """Telemetry event types"""
    ASCENT = "ascent"
    DESCENT = "descent"
    APOGEE = "apogee"
    PERIGEE = "perigee"
    SEPARATION = "separation"
    DEPLOYMENT = "deployment"
    LANDING = "landing"
    ANOMALY = "anomaly"
    RECOVERY = "recovery"


@dataclass
class TelemetryEvent:
    """Telemetry event detected"""
    event_type: TelemetryEventType
    timestamp: datetime
    data: Dict[str, Any]
    confidence: float
    location: Optional[Tuple[float, float]] = None


@dataclass
class TelemetryFrame:
    """Processed telemetry frame"""
    timestamp: float
    sequence: int
    sensors: Dict[str, float]
    gps: Optional[Dict[str, float]] = None
    system: Optional[Dict[str, float]] = None
    events: List[TelemetryEventType] = field(default_factory=list)
    quality_score: float = 1.0


class TelemetryEventDetector:
    """Detect events in telemetry stream"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.EventDetector")
        self.altitude_history = deque(maxlen=100)
        self.velocity_history = deque(maxlen=100)
        self.last_event_time = None
        self.apogee_detected = False
        self.separation_detected = False
        
    def detect_events(self, telemetry: Dict[str, Any]) -> List[TelemetryEvent]:
        """
        Detect events in telemetry data
        
        Args:
            telemetry: Current telemetry data
            
        Returns:
            List of detected events
        """
        events = []
        current_time = datetime.now()
        
        # Get current values
        altitude = telemetry.get('altitude', 0)
        velocity = telemetry.get('velocity', 0)
        
        # Update histories
        self.altitude_history.append(altitude)
        self.velocity_history.append(velocity)
        
        if len(self.altitude_history) < 10:
            return events
        
        # Detect ascent/descent
        alt_array = np.array(list(self.altitude_history))
        vel_array = np.array(list(self.velocity_history))
        
        # Calculate trends
        ascent_rate = np.mean(np.diff(alt_array))
        velocity_trend = np.mean(np.diff(vel_array))
        
        # Apogee detection
        if len(alt_array) > 20:
            peak_idx = np.argmax(alt_array)
            if (peak_idx > len(alt_array) * 0.4 and 
                peak_idx < len(alt_array) * 0.6 and 
                not self.apogee_detected and
                ascent_rate < 0):
                
                self.apogee_detected = True
                events.append(TelemetryEvent(
                    event_type=TelemetryEventType.APOGEE,
                    timestamp=current_time,
                    data={'altitude': altitude, 'velocity': velocity},
                    confidence=0.9
                ))
        
        # Detect ascent vs descent
        if ascent_rate > 1 and telemetry.get('last_state') != 'ascent':
            events.append(TelemetryEvent(
                event_type=TelemetryEventType.ASCENT,
                timestamp=current_time,
                data={'ascent_rate': ascent_rate},
                confidence=0.8
            ))
        elif ascent_rate < -1 and telemetry.get('last_state') != 'descent':
            events.append(TelemetryEvent(
                event_type=TelemetryEventType.DESCENT,
                timestamp=current_time,
                data={'descent_rate': abs(ascent_rate)},
                confidence=0.8
            ))
        
        # Separation detection (sudden velocity change)
        if len(self.velocity_history) > 5:
            vel_diff = np.abs(vel_array[-1] - vel_array[-5])
            if vel_diff > 20 and not self.separation_detected:
                self.separation_detected = True
                events.append(TelemetryEvent(
                    event_type=TelemetryEventType.SEPARATION,
                    timestamp=current_time,
                    data={'velocity_change': vel_diff},
                    confidence=0.85
                ))
        
        # Landing detection
        if (altitude < 10 and len(self.altitude_history) > 30 and 
            np.mean(alt_array[-10:]) < 5):
            events.append(TelemetryEvent(
                event_type=TelemetryEventType.LANDING,
                timestamp=current_time,
                data={'final_altitude': altitude},
                confidence=0.95
            ))
        
        # Anomaly detection
        if self._detect_anomaly(telemetry):
            events.append(TelemetryEvent(
                event_type=TelemetryEventType.ANOMALY,
                timestamp=current_time,
                data=telemetry,
                confidence=0.7
            ))
        
        # Rate limit events
        if self.last_event_time:
            time_since = (current_time - self.last_event_time).total_seconds()
            if time_since < 1.0:
                return []  # Too soon
        
        self.last_event_time = current_time
        
        return events
    
    def _detect_anomaly(self, telemetry: Dict[str, Any]) -> bool:
        """Detect anomalies in telemetry"""
        # Check for unrealistic values
        if telemetry.get('altitude', 0) > 100000:  # 100km - edge of space
            return True
        if abs(telemetry.get('velocity', 0)) > 2000:  # 2km/s max
            return True
        if telemetry.get('temperature', 0) > 150 or telemetry.get('temperature', 0) < -100:
            return True
        return False


class TelemetryCompressor:
    """Compress telemetry data for efficient transmission"""
    
    def __init__(self, compression_level: int = 6):
        self.logger = logging.getLogger(f"{__name__}.Compressor")
        self.compression_level = compression_level
        self.compression_stats = {
            'original_size': 0,
            'compressed_size': 0,
            'packets_compressed': 0
        }
    
    def compress(self, telemetry_data: Dict[str, Any]) -> bytes:
        """
        Compress telemetry data
        
        Args:
            telemetry_data: Telemetry dictionary
            
        Returns:
            Compressed bytes
        """
        # Convert to JSON
        json_data = json.dumps(telemetry_data, default=str)
        json_bytes = json_data.encode('utf-8')
        
        # Update stats
        self.compression_stats['original_size'] += len(json_bytes)
        
        # Compress
        compressed = zlib.compress(json_bytes, level=self.compression_level)
        
        self.compression_stats['compressed_size'] += len(compressed)
        self.compression_stats['packets_compressed'] += 1
        
        return compressed
    
    def decompress(self, compressed_data: bytes) -> Dict[str, Any]:
        """
        Decompress telemetry data
        
        Args:
            compressed_data: Compressed bytes
            
        Returns:
            Telemetry dictionary
        """
        decompressed = zlib.decompress(compressed_data)
        return json.loads(decompressed.decode('utf-8'))
    
    def get_compression_ratio(self) -> float:
        """Get current compression ratio"""
        if self.compression_stats['original_size'] > 0:
            return (self.compression_stats['compressed_size'] / 
                    self.compression_stats['original_size'])
        return 1.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get compression statistics"""
        return {
            **self.compression_stats,
            'compression_ratio': self.get_compression_ratio()
        }


class TelemetryPredictor:
    """Predict future telemetry values"""
    
    def __init__(self, prediction_horizon: int = 10):
        self.logger = logging.getLogger(f"{__name__}.Predictor")
        self.prediction_horizon = prediction_horizon
        self.histories: Dict[str, deque] = {}
        
    def add_observation(self, parameter: str, value: float):
        """Add observation for prediction"""
        if parameter not in self.histories:
            self.histories[parameter] = deque(maxlen=1000)
        self.histories[parameter].append(value)
    
    def predict(self, parameter: str) -> Tuple[List[float], float]:
        """
        Predict future values
        
        Args:
            parameter: Parameter name
            
        Returns:
            Tuple of (predictions, confidence)
        """
        if (parameter not in self.histories or 
            len(self.histories[parameter]) < 20):
            return [], 0.0
        
        values = np.array(list(self.histories[parameter]))
        
        # Use exponential moving average for simple prediction
        alpha = 0.3
        ema = values[0]
        for v in values[1:]:
            ema = alpha * v + (1 - alpha) * ema
        
        # Calculate trend
        slope = (values[-1] - values[0]) / len(values)
        
        # Generate predictions
        predictions = []
        last_val = values[-1]
        for i in range(1, self.prediction_horizon + 1):
            pred = last_val + slope * i + ema * 0.1
            predictions.append(pred)
        
        # Confidence based on data consistency
        residuals = values[1:] - values[:-1]
        variance = np.var(residuals)
        confidence = 1.0 / (1.0 + variance / 100)
        
        return predictions, min(1.0, confidence)
    
    def predict_trajectory(self, current_altitude: float, 
                          current_velocity: float) -> Dict[str, Any]:
        """
        Predict full trajectory
        
        Args:
            current_altitude: Current altitude
            current_velocity: Current velocity
            
        Returns:
            Trajectory prediction
        """
        # Simple physics-based prediction
        g = 9.81  # m/s^2
        
        if current_velocity > 0:
            # Still ascending
            time_to_peak = current_velocity / g
            peak_altitude = current_altitude + current_velocity**2 / (2 * g)
            
            return {
                'type': 'ascent',
                'time_to_apogee': time_to_peak,
                'predicted_apogee': peak_altitude,
                'time_to_ground': time_to_peak + np.sqrt(2 * peak_altitude / g),
                'confidence': 0.8
            }
        else:
            # Descending
            time_to_ground = np.sqrt(2 * current_altitude / g)
            
            return {
                'type': 'descent',
                'time_to_ground': time_to_ground,
                'impact_velocity': abs(current_velocity),
                'confidence': 0.75
            }


class TelemetryFilter:
    """Filter and smooth telemetry data"""
    
    def __init__(self, filter_type: str = 'kalman'):
        self.logger = logging.getLogger(f"{__name__}.Filter")
        self.filter_type = filter_type
        self.filters: Dict[str, Any] = {}
        
    def filter(self, parameter: str, value: float, 
               noise_estimate: float = 1.0) -> float:
        """
        Filter a telemetry value
        
        Args:
            parameter: Parameter name
            value: New value
            noise_estimate: Noise estimate
            
        Returns:
            Filtered value
        """
        if parameter not in self.filters:
            # Initialize filter state
            self.filters[parameter] = {
                'state': value,
                'error_estimate': 1.0,
                'kalman_gain': 0.0
            }
        
        filter_state = self.filters[parameter]
        
        if self.filter_type == 'kalman':
            # Kalman filter
            q = noise_estimate**2  # Process noise
            r = noise_estimate**2  # Measurement noise
            
            # Prediction
            predicted_state = filter_state['state']
            predicted_error = filter_state['error_estimate'] + q
            
            # Update
            kalman_gain = predicted_error / (predicted_error + r)
            new_state = predicted_state + kalman_gain * (value - predicted_state)
            new_error = (1 - kalman_gain) * predicted_error
            
            filter_state['state'] = new_state
            filter_state['error_estimate'] = new_error
            filter_state['kalman_gain'] = kalman_gain
            
            return new_state
            
        elif self.filter_type == 'moving_average':
            # Simple moving average
            if 'ma_window' not in filter_state:
                filter_state['ma_window'] = deque(maxlen=10)
            
            filter_state['ma_window'].append(value)
            return np.mean(filter_state['ma_window'])
        
        else:
            # No filtering
            return value
    
    def reset_filter(self, parameter: str):
        """Reset filter state for a parameter"""
        if parameter in self.filters:
            del self.filters[parameter]


class TelemetryAnalyzer:
    """Analyze telemetry data for patterns and insights"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.Analyzer")
        self.analysis_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 1000
        
    def analyze_packet(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a telemetry packet
        
        Args:
            telemetry: Telemetry data
            
        Returns:
            Analysis results
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'data_quality': self._assess_quality(telemetry),
            'sensors': {}
        }
        
        # Analyze each sensor
        sensor_ranges = {
            'altitude': (0, 100000),
            'velocity': (-2000, 2000),
            'temperature': (-50, 100),
            'pressure': (0, 110000),
            'humidity': (0, 100),
            'battery_voltage': (0, 15)
        }
        
        for sensor, (min_val, max_val) in sensor_ranges.items():
            if sensor in telemetry:
                value = telemetry[sensor]
                in_range = min_val <= value <= max_val
                
                analysis['sensors'][sensor] = {
                    'value': value,
                    'in_range': in_range,
                    'percentage': ((value - min_val) / (max_val - min_val) * 100 
                                   if in_range else 0)
                }
        
        # Store for batch analysis
        self.analysis_buffer.append(analysis)
        if len(self.analysis_buffer) > self.max_buffer_size:
            self.analysis_buffer.pop(0)
        
        return analysis
    
    def _assess_quality(self, telemetry: Dict[str, Any]) -> float:
        """Assess overall data quality"""
        if not telemetry:
            return 0.0
        
        # Count valid fields
        valid_count = sum(
            1 for v in telemetry.values() 
            if isinstance(v, (int, float)) and v != 0
        )
        
        return valid_count / max(len(telemetry), 1)
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get statistics from analysis buffer"""
        if not self.analysis_buffer:
            return {}
        
        quality_scores = [a['data_quality'] for a in self.analysis_buffer]
        
        return {
            'packets_analyzed': len(self.analysis_buffer),
            'average_quality': np.mean(quality_scores),
            'min_quality': np.min(quality_scores),
            'max_quality': np.max(quality_scores)
        }


class AdvancedTelemetryProcessor:
    """Complete advanced telemetry processing system"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AdvancedTelemetry")
        
        # Initialize components
        self.event_detector = TelemetryEventDetector()
        self.compressor = TelemetryCompressor()
        self.predictor = TelemetryPredictor()
        self.filter = TelemetryFilter(filter_type='kalman')
        self.analyzer = TelemetryAnalyzer()
        
        # Sequence number
        self.sequence = 0
        
        self.logger.info("Advanced Telemetry Processor initialized")
    
    def process(self, raw_packet: Dict[str, Any]) -> TelemetryFrame:
        """
        Process raw telemetry packet through all stages
        
        Args:
            raw_packet: Raw telemetry data
            
        Returns:
            Processed telemetry frame
        """
        self.sequence += 1
        frame = TelemetryFrame(
            timestamp=time.time(),
            sequence=self.sequence,
            sensors={},
            quality_score=1.0
        )
        
        # Apply filtering
        for key, value in raw_packet.items():
            if isinstance(value, (int, float)):
                filtered_value = self.filter.filter(key, value)
                frame.sensors[key] = filtered_value
                
                # Add to predictor
                self.predictor.add_observation(key, filtered_value)
        
        # Detect events
        events = self.event_detector.detect_events(raw_packet)
        frame.events = [e.event_type for e in events]
        
        # Extract GPS and system data
        if 'latitude' in raw_packet:
            frame.gps = {
                'latitude': raw_packet.get('latitude'),
                'longitude': raw_packet.get('longitude'),
                'altitude': raw_packet.get('gps_altitude'),
                'satellites': raw_packet.get('satellites')
            }
        
        if 'battery_voltage' in raw_packet:
            frame.system = {
                'battery_voltage': raw_packet.get('battery_voltage'),
                'battery_current': raw_packet.get('battery_current'),
                'cpu_temperature': raw_packet.get('cpu_temperature'),
                'rssi': raw_packet.get('rssi')
            }
        
        # Analyze quality
        analysis = self.analyzer.analyze_packet(frame.sensors)
        frame.quality_score = analysis['data_quality']
        
        return frame
    
    def compress_frame(self, frame: TelemetryFrame) -> bytes:
        """Compress telemetry frame"""
        data = {
            'ts': frame.timestamp,
            'seq': frame.sequence,
            'sensors': frame.sensors,
            'gps': frame.gps,
            'system': frame.system,
            'events': [e.value for e in frame.events],
            'quality': frame.quality_score
        }
        return self.compressor.compress(data)
    
    def predict_future(self, parameter: str) -> Tuple[List[float], float]:
        """Predict future values"""
        return self.predictor.predict(parameter)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            'sequence': self.sequence,
            'compression': self.compressor.get_statistics(),
            'analysis': self.analyzer.get_batch_statistics()
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Advanced Telemetry Features...")
    
    # Test Advanced Telemetry Processor
    print("\n1. Testing Advanced Telemetry Processor...")
    processor = AdvancedTelemetryProcessor()
    
    # Simulate telemetry packets
    for i in range(50):
        packet = {
            'altitude': 1000 + i * 5 + np.random.randn() * 10,
            'velocity': 50 - i * 0.5 + np.random.randn() * 2,
            'temperature': 25 + np.random.randn() * 2,
            'pressure': 101325 - i * 50 + np.random.randn() * 100,
            'battery_voltage': 12.5 + np.random.randn() * 0.1,
            'latitude': 34.0 + i * 0.001,
            'longitude': -118.0 + i * 0.001
        }
        frame = processor.process(packet)
        
        if frame.events:
            print(f"   Event detected: {frame.events}")
    
    print(f"   Processed {processor.sequence} frames")
    
    # Test compression
    print("\n2. Testing Compression...")
    packet = {
        'altitude': 1500,
        'velocity': 25,
        'temperature': 22,
        'pressure': 100000
    }
    frame = processor.process(packet)
    compressed = processor.compress_frame(frame)
    print(f"   Compression ratio: {processor.compressor.get_compression_ratio():.2%}")
    
    # Test prediction
    print("\n3. Testing Prediction...")
    preds, conf = processor.predict_future('altitude')
    print(f"   Prediction confidence: {conf:.2%}")
    if preds:
        print(f"   Next values: {preds[:3]}...")
    
    # Get statistics
    print("\n4. Getting Statistics...")
    stats = processor.get_statistics()
    print(f"   Frames processed: {stats['sequence']}")
    
    print("\n✅ Advanced Telemetry Features test completed!")