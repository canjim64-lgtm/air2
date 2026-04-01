"""
Real-Time Processing Module - Full Implementation
High-rate telemetry processing and streaming
"""

import time
import threading
import queue
import numpy as np
from typing import Dict, List, Callable, Any
from collections import deque
import socket
import struct


class TimeSeriesBuffer:
    """Ring buffer for time series data"""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self.data = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)
    
    def append(self, value: float, timestamp: float = None):
        if timestamp is None:
            timestamp = time.time()
        self.data.append(value)
        self.timestamps.append(timestamp)
    
    def get_range(self, start_time: float, end_time: float) -> List[float]:
        result = []
        for i, ts in enumerate(self.timestamps):
            if start_time <= ts <= end_time:
                result.append(self.data[i])
        return result
    
    def get_latest(self, n: int) -> List[float]:
        return list(self.data)[-n:]
    
    def get_statistics(self) -> Dict:
        if not self.data:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0}
        arr = np.array(self.data)
        return {
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'count': len(arr)
        }


class MovingAverageFilter:
    """Moving average filter for smoothing"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.buffer = deque(maxlen=window_size)
    
    def filter(self, value: float) -> float:
        self.buffer.append(value)
        return sum(self.buffer) / len(self.buffer)


class ExponentialSmoother:
    """Exponential smoothing filter"""
    
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.last_value = None
    
    def filter(self, value: float) -> float:
        if self.last_value is None:
            self.last_value = value
            return value
        smoothed = self.alpha * value + (1 - self.alpha) * self.last_value
        self.last_value = smoothed
        return smoothed


class KalmanFilter:
    """1D Kalman filter for noise reduction"""
    
    def __init__(self, process_variance: float = 1.0, measurement_variance: float = 1.0):
        self.q = process_variance  # Process noise
        self.r = measurement_variance  # Measurement noise
        self.x = 0  # Estimate
        self.p = 1  # Estimate covariance
        self.k = 0  # Kalman gain
    
    def update(self, measurement: float) -> float:
        # Prediction
        self.p = self.p + self.q
        
        # Update
        self.k = self.p / (self.p + self.r)
        self.x = self.x + self.k * (measurement - self.x)
        self.p = (1 - self.k) * self.p
        
        return self.x


class PIDController:
    """PID controller for control loops"""
    
    def __init__(self, kp: float = 1.0, ki: float = 0.1, kd: float = 0.01):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0
        self.last_error = 0
        self.last_time = None
    
    def compute(self, setpoint: float, measurement: float) -> float:
        current_time = time.time()
        
        if self.last_time is not None:
            dt = current_time - self.last_time
            if dt > 0:
                error = setpoint - measurement
                
                # Proportional
                p = self.kp * error
                
                # Integral
                self.integral += error * dt
                i = self.ki * self.integral
                
                # Derivative
                d = self.kd * (error - self.last_error) / dt
                
                self.last_error = error
                self.last_time = current_time
                
                return p + i + d
        
        self.last_time = current_time
        return 0


class RateLimiter:
    """Rate limiter for control signals"""
    
    def __init__(self, max_rate: float):
        self.max_rate = max_rate
        self.last_value = 0
        self.last_time = None
    
    def limit(self, value: float) -> float:
        current_time = time.time()
        
        if self.last_time is not None:
            dt = current_time - self.last_time
            if dt > 0:
                max_change = self.max_rate * dt
                delta = value - self.last_value
                
                if abs(delta) > max_change:
                    value = self.last_value + np.sign(delta) * max_change
        
        self.last_value = value
        self.last_time = current_time
        return value


class PacketProcessor:
    """Process incoming packets"""
    
    def __init__(self):
        self.parser = None
        self.handlers = []
        self.stats = {'processed': 0, 'errors': 0, 'rate': 0}
    
    def register_handler(self, handler: Callable):
        self.handlers.append(handler)
    
    def process(self, packet: bytes) -> Dict:
        try:
            # Simple parsing (would be more sophisticated in real use)
            data = eval(packet.decode('utf-8'))
            
            for handler in self.handlers:
                handler(data)
            
            self.stats['processed'] += 1
            return data
        except Exception as e:
            self.stats['errors'] += 1
            return {}
    
    def get_stats(self) -> Dict:
        return self.stats


class StreamBuffer:
    """Buffer for streaming data"""
    
    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size
        self.buffer = queue.Queue(maxsize=buffer_size)
        self.overflow_count = 0
    
    def put(self, data: Any) -> bool:
        try:
            self.buffer.put_nowait(data)
            return True
        except queue.Full:
            self.overflow_count += 1
            return False
    
    def get(self, timeout: float = None) -> Any:
        return self.buffer.get(timeout=timeout)
    
    def is_empty(self) -> bool:
        return self.buffer.empty()
    
    def size(self) -> int:
        return self.buffer.qsize()


class TelemetryAggregator:
    """Aggregate telemetry at different rates"""
    
    def __init__(self):
        self.sensors = {}  # sensor_name -> TimeSeriesBuffer
        self.aggregators = {}  # name -> aggregated value
    
    def add_sensor(self, name: str, max_points: int = 1000):
        self.sensors[name] = TimeSeriesBuffer(max_points)
    
    def add_measurement(self, sensor: str, value: float, timestamp: float = None):
        if sensor not in self.sensors:
            self.add_sensor(sensor)
        self.sensors[sensor].append(value, timestamp)
    
    def aggregate(self, sensor: str, window: int = 10) -> Dict:
        if sensor not in self.sensors:
            return {}
        
        values = self.sensors[sensor].get_latest(window)
        if not values:
            return {}
        
        arr = np.array(values)
        return {
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'last': values[-1],
            'count': len(values)
        }
    
    def get_all_aggregates(self) -> Dict:
        result = {}
        for sensor in self.sensors:
            result[sensor] = self.aggregate(sensor)
        return result


class EventDetector:
    """Detect events from telemetry"""
    
    def __init__(self):
        self.thresholds = {
            'high_altitude': 400,
            'low_altitude': 50,
            'high_vibration': 50,
            'high_temperature': 60
        }
        self.events = []
    
    def set_threshold(self, event_type: str, value: float):
        self.thresholds[event_type] = value
    
    def check(self, telemetry: Dict) -> List[Dict]:
        new_events = []
        timestamp = telemetry.get('timestamp', time.time())
        
        # Check altitude
        alt = telemetry.get('altitude', 0)
        if alt > self.thresholds.get('high_altitude', 400):
            new_events.append({'type': 'HIGH_ALTITUDE', 'value': alt, 'time': timestamp})
        elif alt < self.thresholds.get('low_altitude', 50):
            new_events.append({'type': 'LOW_ALTITUDE', 'value': alt, 'time': timestamp})
        
        # Check temperature
        temp = telemetry.get('temperature', 0)
        if temp > self.thresholds.get('high_temperature', 60):
            new_events.append({'type': 'HIGH_TEMP', 'value': temp, 'time': timestamp})
        
        # Check vibration
        vib = telemetry.get('vibration', 0)
        if vib > self.thresholds.get('high_vibration', 50):
            new_events.append({'type': 'HIGH_VIBRATION', 'value': vib, 'time': timestamp})
        
        self.events.extend(new_events)
        return new_events
    
    def get_events(self, event_type: str = None) -> List[Dict]:
        if event_type:
            return [e for e in self.events if e['type'] == event_type]
        return self.events


class WatchdogTimer:
    """Watchdog timer for system health"""
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.last_ping = time.time()
        self.expired = False
    
    def ping(self):
        self.last_ping = time.time()
        self.expired = False
    
    def check(self) -> bool:
        if time.time() - self.last_ping > self.timeout:
            self.expired = True
            return False
        return True
    
    def is_expired(self) -> bool:
        return self.expired


class HealthMonitor:
    """Monitor system health"""
    
    def __init__(self):
        self.watchdogs = {}
        self.status = 'HEALTHY'
        self.alerts = []
    
    def add_watchdog(self, name: str, timeout: float):
        self.watchdogs[name] = WatchdogTimer(timeout)
    
    def ping(self, name: str):
        if name in self.watchdogs:
            self.watchdogs[name].ping()
    
    def check_health(self) -> Dict:
        all_healthy = True
        
        for name, wd in self.watchdogs.items():
            if not wd.check():
                all_healthy = False
                self.alerts.append({
                    'time': time.time(),
                    'type': 'WATCHDOG_TIMEOUT',
                    'component': name
                })
        
        self.status = 'HEALTHY' if all_healthy else 'UNHEALTHY'
        
        return {
            'status': self.status,
            'watchdogs': {name: not wd.is_expired() for name, wd in self.watchdogs.items()},
            'alerts': len(self.alerts)
        }


# Example
if __name__ == "__main__":
    # Test filters
    maf = MovingAverageFilter(5)
    for i in range(10):
        print(f"MAF: {maf.filter(float(i))}")
    
    # Test aggregator
    agg = TelemetryAggregator()
    for i in range(20):
        agg.add_measurement('altitude', 100 + i * 0.5)
    
    print(f"Aggregate: {agg.aggregate('altitude', 10)}")