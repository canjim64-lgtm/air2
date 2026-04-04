"""
Telemetry Anomaly Detection Module
Real-time anomaly detection for telemetry data streams
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
import logging
from collections import deque


class AnomalyType(Enum):
    """Types of anomalies"""
    SPIKE = "spike"
    DROPOUT = "dropout"
    DRIFT = "drift"
    STUCK = "stuck"
    RATE_CHANGE = "rate_change"
    OUT_OF_RANGE = "out_of_range"
    CORRUPTED = "corrupted"


class Severity(Enum):
    """Anomaly severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_type: AnomalyType
    parameter: str
    value: float
    expected_range: Tuple[float, float]
    severity: Severity
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)


class StatisticalAnomalyDetector:
    """Statistical-based anomaly detection"""
    
    def __init__(self, window_size: int = 100, z_threshold: float = 3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        
        self.history: Dict[str, deque] = {}
        
    def add_sample(self, parameter: str, value: float):
        """Add sample to history"""
        if parameter not in self.history:
            self.history[parameter] = deque(maxlen=self.window_size)
        self.history[parameter].append(value)
    
    def detect(self, parameter: str, value: float) -> Optional[Anomaly]:
        """Detect anomaly in parameter"""
        
        if parameter not in self.history or len(self.history[parameter]) < 10:
            return None
        
        values = np.array(list(self.history[parameter]))
        
        # Calculate statistics
        mean = np.mean(values)
        std = np.std(values)
        
        # Z-score
        z_score = abs((value - mean) / (std + 1e-10))
        
        if z_score > self.z_threshold:
            # Determine severity
            if z_score > 5:
                severity = Severity.CRITICAL
            elif z_score > 4:
                severity = Severity.HIGH
            elif z_score > 3.5:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW
            
            return Anomaly(
                anomaly_type=AnomalyType.SPIKE,
                parameter=parameter,
                value=value,
                expected_range=(mean - self.z_threshold * std, 
                               mean + self.z_threshold * std),
                severity=severity,
                timestamp=datetime.now(),
                details={'z_score': z_score, 'mean': mean, 'std': std}
            )
        
        return None


class ChangePointDetector:
    """Detect change points in time series"""
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.baseline = None
        
    def detect_change(self, values: np.ndarray) -> Tuple[bool, int]:
        """Detect if there's a change point"""
        
        if len(values) < 20:
            return False, -1
        
        # CUSUM algorithm
        mean = np.mean(values[:len(values)//2])
        
        cusum_pos = 0
        cusum_neg = 0
        change_point = -1
        
        for i in range(len(values) // 2, len(values)):
            deviation = values[i] - mean
            
            cusum_pos = max(0, cusum_pos + deviation - self.threshold)
            cusum_neg = max(0, cusum_neg - deviation - self.threshold)
            
            if cusum_pos > 5 or cusum_neg > 5:
                change_point = i
                break
        
        return change_point >= 0, change_point


class PatternAnomalyDetector:
    """Detect patterns that indicate anomalies"""
    
    def __init__(self):
        self.stuck_counts: Dict[str, int] = {}
        
    def detect_stuck(self, parameter: str, value: float,
                    tolerance: float = 0.001) -> Optional[Anomaly]:
        """Detect if value is stuck"""
        
        if parameter not in self.stuck_counts:
            self.stuck_counts[parameter] = 0
            return None
        
        # Check if value hasn't changed much
        if abs(value - self.stuck_counts.get(f'last_{parameter}', value)) < tolerance:
            self.stuck_counts[parameter] = self.stuck_counts.get(parameter, 0) + 1
            
            if self.stuck_counts[parameter] > 10:
                return Anomaly(
                    anomaly_type=AnomalyType.STUCK,
                    parameter=parameter,
                    value=value,
                    expected_range=(0, 0),
                    severity=Severity.MEDIUM,
                    timestamp=datetime.now(),
                    details={'consecutive_same': self.stuck_counts[parameter]}
                )
        else:
            self.stuck_counts[parameter] = 0
        
        self.stuck_counts[f'last_{parameter}'] = value
        return None
    
    def detect_rate_change(self, parameter: str,
                          old_rate: float, new_rate: float,
                          threshold: float = 2.0) -> Optional[Anomaly]:
        """Detect significant rate of change"""
        
        if old_rate == 0:
            return None
        
        ratio = abs(new_rate / old_rate)
        
        if ratio > threshold:
            severity = Severity.HIGH if ratio > 5 else Severity.MEDIUM
            
            return Anomaly(
                anomaly_type=AnomalyType.RATE_CHANGE,
                parameter=parameter,
                value=new_rate,
                expected_range=(-threshold * old_rate, threshold * old_rate),
                severity=severity,
                timestamp=datetime.now(),
                details={'old_rate': old_rate, 'new_rate': new_rate, 'ratio': ratio}
            )
        
        return None
    
    def detect_dropout(self, parameter: str, value: float,
                      min_value: float = -1e9) -> Optional[Anomaly]:
        """Detect data dropout"""
        
        if value <= min_value:
            return Anomaly(
                anomaly_type=AnomalyType.DROPOUT,
                parameter=parameter,
                value=value,
                expected_range=(min_value, 1e9),
                severity=Severity.HIGH,
                timestamp=datetime.now(),
                details={'value': value}
            )
        
        return None


class IsolationForestDetector:
    """Isolation forest-based anomaly detection"""
    
    def __init__(self, num_trees: int = 100, sample_size: int = 256):
        self.num_trees = num_trees
        self.sample_size = sample_size
        self.trees = []
        
    def fit(self, data: np.ndarray):
        """Fit isolation forest"""
        self.trees = []
        
        for _ in range(self.num_trees):
            # Sample data
            indices = np.random.choice(len(data), 
                                       min(self.sample_size, len(data)), 
                                       replace=False)
            sample = data[indices]
            
            # Build simple tree
            tree = self._build_tree(sample, depth=0, max_depth=10)
            self.trees.append(tree)
    
    def _build_tree(self, data: np.ndarray, depth: int, 
                    max_depth: int) -> Dict:
        """Build isolation tree"""
        if depth >= max_depth or len(data) <= 1:
            return {'leaf': True, 'size': len(data)}
        
        # Random split
        feature = np.random.randint(0, data.shape[1])
        split_value = np.median(data[:, feature])
        
        left = data[data[:, feature] < split_value]
        right = data[data[:, feature] >= split_value]
        
        return {
            'leaf': False,
            'feature': feature,
            'split': split_value,
            'left': self._build_tree(left, depth + 1, max_depth),
            'right': self._build_tree(right, depth + 1, max_depth)
        }
    
    def anomaly_score(self, sample: np.ndarray) -> float:
        """Calculate anomaly score"""
        
        if not self.trees:
            return 0.0
        
        # Average path length
        path_lengths = []
        
        for tree in self.trees:
            depth = self._path_length(sample, tree, 0)
            path_lengths.append(depth)
        
        # Anomaly score: s(x, n) = 2^(-E(h(x))/c(n))
        c_n = self._c(self.sample_size)
        avg_path = np.mean(path_lengths)
        
        score = 2 ** (-avg_path / c_n)
        
        return score
    
    def _path_length(self, sample: np.ndarray, node: Dict, 
                    depth: int) -> float:
        """Get path length in tree"""
        if node.get('leaf', False):
            return depth + self._c(node.get('size', 1))
        
        feature = node['feature']
        split = node['split']
        
        if sample[feature] < split:
            return self._path_length(sample, node['left'], depth + 1)
        else:
            return self._path_length(sample, node['right'], depth + 1)
    
    def _c(self, n: int) -> float:
        """Average path length for unsuccessful search"""
        if n <= 1:
            return 0
        return 2 * (np.log(n - 1) + 0.5772156649) - (2 * (n - 1) / n)


class TelemetryAnomalyMonitor:
    """Complete anomaly monitoring system"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AnomalyMonitor")
        
        # Detectors
        self.stat_detector = StatisticalAnomalyDetector()
        self.change_detector = ChangePointDetector()
        self.pattern_detector = PatternAnomalyDetector()
        self.isolation_forest = IsolationForestDetector()
        
        # State
        self.anomalies: List[Anomaly] = []
        self.parameter_rates: Dict[str, float] = {}
        
        # Configuration
        self.anomaly_callbacks: List[Callable] = []
        
    def add_sample(self, parameter: str, value: float) -> List[Anomaly]:
        """Add sample and check for anomalies"""
        
        detected = []
        
        # Statistical detection
        self.stat_detector.add_sample(parameter, value)
        stat_anomaly = self.stat_detector.detect(parameter, value)
        if stat_anomaly:
            detected.append(stat_anomaly)
        
        # Pattern detection
        stuck_anomaly = self.pattern_detector.detect_stuck(parameter, value)
        if stuck_anomaly:
            detected.append(stuck_anomaly)
        
        dropout_anomaly = self.pattern_detector.detect_dropout(parameter, value)
        if dropout_anomaly:
            detected.append(dropout_anomaly)
        
        # Rate change detection
        if parameter in self.parameter_rates:
            old_rate = self.parameter_rates[parameter]
            new_rate = abs(value - self.parameter_rates[parameter])
            rate_anomaly = self.pattern_detector.detect_rate_change(
                parameter, old_rate, new_rate
            )
            if rate_anomaly:
                detected.append(rate_anomaly)
        
        self.parameter_rates[parameter] = value
        
        # Store anomalies
        for anomaly in detected:
            self.anomalies.append(anomaly)
            self._trigger_callbacks(anomaly)
        
        return detected
    
    def detect_multi_variate(self, data: np.ndarray, 
                            threshold: float = 0.6) -> bool:
        """Detect multivariate anomalies"""
        
        if len(data) < 50:
            return False
        
        # Fit isolation forest
        self.isolation_forest.fit(data)
        
        # Check new data point
        score = self.isolation_forest.anomaly_score(data[-1])
        
        return score > threshold
    
    def register_callback(self, callback: Callable):
        """Register anomaly callback"""
        self.anomaly_callbacks.append(callback)
    
    def _trigger_callbacks(self, anomaly: Anomaly):
        """Trigger anomaly callbacks"""
        for callback in self.anomaly_callbacks:
            try:
                callback(anomaly)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    def get_anomalies(self, 
                      since: Optional[datetime] = None) -> List[Anomaly]:
        """Get recent anomalies"""
        
        if since is None:
            return self.anomalies
        
        return [a for a in self.anomalies if a.timestamp >= since]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get anomaly statistics"""
        
        by_type = {}
        by_severity = {}
        
        for anomaly in self.anomalies:
            t = anomaly.anomaly_type.value
            by_type[t] = by_type.get(t, 0) + 1
            
            s = anomaly.severity.value
            by_severity[s] = by_severity.get(s, 0) + 1
        
        return {
            'total_anomalies': len(self.anomalies),
            'by_type': by_type,
            'by_severity': by_severity
        }
    
    def clear_anomalies(self):
        """Clear anomaly history"""
        self.anomalies.clear()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Telemetry Anomaly Detection...")
    
    # Test Statistical Detector
    print("\n1. Testing Statistical Detector...")
    stat_detector = StatisticalAnomalyDetector()
    
    for i in range(100):
        stat_detector.add_sample('temperature', 25 + np.random.randn() * 2)
    
    anomaly = stat_detector.detect('temperature', 40)  # Spike
    if anomaly:
        print(f"   Detected: {anomaly.anomaly_type.value}, severity: {anomaly.severity.value}")
    
    # Test Pattern Detector
    print("\n2. Testing Pattern Detector...")
    pattern_detector = PatternAnomalyDetector()
    
    for i in range(20):
        anomaly = pattern_detector.detect_stuck('velocity', 50.0)
    
    anomaly = pattern_detector.detect_stuck('velocity', 50.0)
    if anomaly:
        print(f"   Detected stuck: {anomaly.anomaly_type.value}")
    
    # Test Complete Monitor
    print("\n3. Testing Complete Monitor...")
    monitor = TelemetryAnomalyMonitor()
    
    # Add samples
    for i in range(100):
        monitor.add_sample('altitude', 1000 + i * 0.5)
        monitor.add_sample('temperature', 25 + np.random.randn() * 2)
    
    # Inject anomaly
    anomalies = monitor.add_sample('temperature', 50.0)
    print(f"   Detected {len(anomalies)} anomalies")
    
    # Get statistics
    stats = monitor.get_statistics()
    print(f"   Statistics: {stats}")
    
    # Test Isolation Forest
    print("\n4. Testing Isolation Forest...")
    iforest = IsolationForestDetector()
    data = np.random.randn(100, 5)
    iforest.fit(data)
    score = iforest.anomaly_score(np.array([0, 0, 0, 0, 0]))
    print(f"   Anomaly score: {score:.4f}")
    
    print("\n✅ Telemetry Anomaly Detection test completed!")