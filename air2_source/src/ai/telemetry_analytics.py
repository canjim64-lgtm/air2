"""
AirOne v4.0 - Real-Time Telemetry Analytics
Stream processing and analytics for flight telemetry data
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from enum import Enum
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    GAUGE = "gauge"
    COUNTER = "counter"
    RATE = "rate"
    HISTOGRAM = "histogram"
    PERCENTILE = "percentile"


@dataclass
class TelemetryMetric:
    """Telemetry metric"""
    name: str
    value: float
    timestamp: str
    metric_type: str
    unit: str
    tags: Dict[str, str]


@dataclass
class AnalyticsWindow:
    """Analytics time window"""
    window_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    sample_count: int
    metrics: Dict[str, Any]


@dataclass
class TelemetryAlert:
    """Telemetry alert"""
    alert_id: str
    timestamp: str
    metric: str
    value: float
    threshold: float
    severity: str
    message: str


class StreamProcessor:
    """
    Real-time stream processing for telemetry
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.data_buffer: deque = deque(maxlen=window_size)
        self.lock = threading.Lock()

    def add(self, data: Dict[str, Any]):
        """Add data point to stream"""
        with self.lock:
            data['processed_at'] = datetime.now().isoformat()
            self.data_buffer.append(data)

    def add_batch(self, data_list: List[Dict[str, Any]]):
        """Add batch of data points"""
        with self.lock:
            for data in data_list:
                data['processed_at'] = datetime.now().isoformat()
                self.data_buffer.append(data)

    def get_window(self, size: Optional[int] = None) -> List[Dict]:
        """Get recent window of data"""
        with self.lock:
            n = size or self.window_size
            return list(self.data_buffer)[-n:]

    def get_all(self) -> List[Dict]:
        """Get all buffered data"""
        with self.lock:
            return list(self.data_buffer)

    def clear(self):
        """Clear buffer"""
        with self.lock:
            self.data_buffer.clear()


class MetricCalculator:
    """
    Calculate various metrics from telemetry stream
    """

    @staticmethod
    def calculate_stats(values: List[float]) -> Dict[str, float]:
        """Calculate statistical metrics"""
        if not values:
            return {}
        
        arr = np.array(values)
        return {
            'count': len(values),
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'median': float(np.median(arr)),
            'variance': float(np.var(arr)),
            'skewness': float(_safe_call(lambda: np.mean(((arr - np.mean(arr)) / np.std(arr)) ** 3), 0)),
            'kurtosis': float(_safe_call(lambda: np.mean(((arr - np.mean(arr)) / np.std(arr)) ** 4) - 3, 0))
        }

    @staticmethod
    def calculate_percentiles(values: List[float], 
                             percentiles: List[float] = None) -> Dict[str, float]:
        """Calculate percentiles"""
        if not values:
            return {}
        
        if percentiles is None:
            percentiles = [25, 50, 75, 90, 95, 99]
        
        arr = np.array(values)
        return {
            f'p{int(p)}': float(np.percentile(arr, p))
            for p in percentiles
        }

    @staticmethod
    def calculate_rate(values: List[float], 
                      timestamps: List[datetime]) -> float:
        """Calculate rate of change"""
        if len(values) < 2 or len(timestamps) < 2:
            return 0.0
        
        time_diff = (timestamps[-1] - timestamps[0]).total_seconds()
        if time_diff == 0:
            return 0.0
        
        value_diff = values[-1] - values[0]
        return value_diff / time_diff

    @staticmethod
    def calculate_trend(values: List[float]) -> Dict[str, float]:
        """Calculate trend using linear regression"""
        if len(values) < 3:
            return {'slope': 0.0, 'direction': 'stable'}
        
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        # Normalize slope
        mean_val = np.mean(values)
        normalized_slope = slope / (abs(mean_val) + 1e-6)
        
        if normalized_slope > 0.01:
            direction = 'increasing'
        elif normalized_slope < -0.01:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'direction': direction,
            'normalized_slope': float(normalized_slope)
        }

    @staticmethod
    def calculate_frequency(values: List[float], sample_rate: float) -> Dict[str, float]:
        """Simple frequency analysis"""
        if len(values) < 10:
            return {}
        
        arr = np.array(values)
        
        # Zero crossing rate
        mean_val = np.mean(arr)
        zero_crossings = np.sum(np.diff(np.sign(arr - mean_val)) != 0)
        zcr = zero_crossings / (2 * len(arr)) * sample_rate
        
        # Dominant frequency (simplified)
        fft_vals = np.fft.fft(arr - mean_val)
        freqs = np.fft.fftfreq(len(arr), 1/sample_rate)
        
        # Get positive frequencies only
        positive_mask = freqs > 0
        if np.any(positive_mask):
            dominant_idx = np.argmax(np.abs(fft_vals[positive_mask]))
            dominant_freq = freqs[positive_mask][dominant_idx]
        else:
            dominant_freq = 0
        
        return {
            'zero_crossing_rate': float(zcr),
            'dominant_frequency': float(dominant_freq),
            'spectral_energy': float(np.sum(np.abs(fft_vals) ** 2))
        }

    @staticmethod
    def calculate_correlation(x_values: List[float], 
                             y_values: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(x_values) < 3 or len(y_values) < 3:
            return 0.0
        
        return float(np.corrcoef(x_values, y_values)[0, 1])


def _safe_call(func: Callable, default: Any) -> Any:
    """Safely call function with fallback"""
    try:
        return func()
    except:
        return default


class TelemetryAnalytics:
    """
    Real-time telemetry analytics engine
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Stream processors for different metrics
        self.processors: Dict[str, StreamProcessor] = {}
        
        # Metric calculators
        self.calculator = MetricCalculator()
        
        # Alert rules
        self.alert_rules: List[Dict] = []
        self.active_alerts: Dict[str, TelemetryAlert] = {}
        self.alert_history: List[TelemetryAlert] = []
        
        # Analytics windows
        self.windows: Dict[str, AnalyticsWindow] = {}
        self.window_duration = self.config.get('window_duration', 60)  # seconds
        
        # Callbacks
        self.on_metric_callback: Optional[Callable] = None
        self.on_alert_callback: Optional[Callable] = None
        
        # Threading
        self.lock = threading.Lock()
        self.running = False
        self.analytics_thread = None
        
        # Metrics tracking
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        logger.info("Telemetry Analytics initialized")

    def start(self):
        """Start analytics processing"""
        self.running = True
        self.analytics_thread = threading.Thread(target=self._analytics_loop, daemon=True)
        self.analytics_thread.start()
        logger.info("Telemetry Analytics started")

    def stop(self):
        """Stop analytics processing"""
        self.running = False
        if self.analytics_thread:
            self.analytics_thread.join(timeout=5)
        logger.info("Telemetry Analytics stopped")

    def ingest(self, telemetry: Dict[str, Any]):
        """
        Ingest telemetry data
        
        Args:
            telemetry: Telemetry record
        """
        timestamp = datetime.now()
        
        # Add to processors
        for key, value in telemetry.items():
            if isinstance(value, (int, float)):
                if key not in self.processors:
                    self.processors[key] = StreamProcessor(
                        window_size=self.config.get('window_size', 500)
                    )
                
                self.processors[key].add({
                    'value': value,
                    'timestamp': timestamp
                })
                
                # Track metric history
                self.metric_history[key].append({
                    'value': value,
                    'timestamp': timestamp.isoformat()
                })
        
        # Check alerts
        self._check_alerts(telemetry, timestamp)

    def ingest_batch(self, telemetry_list: List[Dict[str, Any]]):
        """Ingest batch of telemetry data"""
        for telemetry in telemetry_list:
            self.ingest(telemetry)

    def get_current_metrics(self) -> Dict[str, TelemetryMetric]:
        """Get current metrics for all tracked values"""
        metrics = {}
        
        for name, processor in self.processors.items():
            window = processor.get_window(size=10)
            if not window:
                continue
            
            latest = window[-1]
            metrics[name] = TelemetryMetric(
                name=name,
                value=latest['value'],
                timestamp=latest['timestamp'].isoformat() if isinstance(latest['timestamp'], datetime) else str(latest.get('timestamp', datetime.now())),
                metric_type=MetricType.GAUGE.value,
                unit=self._get_unit(name),
                tags={}
            )
        
        return metrics

    def get_analytics_summary(self, window_seconds: int = 60) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'window_seconds': window_seconds,
            'metrics': {},
            'alerts': {
                'active': len(self.active_alerts),
                'total': len(self.alert_history)
            },
            'trends': {},
            'correlations': {}
        }
        
        for name, processor in self.processors.items():
            window = processor.get_window()
            if len(window) < 5:
                continue
            
            values = [w['value'] for w in window]
            timestamps = [w['timestamp'] for w in window]
            
            # Basic stats
            stats = self.calculator.calculate_stats(values)
            percentiles = self.calculator.calculate_percentiles(values)
            trend = self.calculator.calculate_trend(values)
            
            summary['metrics'][name] = {
                'current': values[-1] if values else 0,
                **stats,
                **percentiles
            }
            
            summary['trends'][name] = trend
            
            # Rate
            if len(timestamps) >= 2:
                rate = self.calculator.calculate_rate(values, timestamps)
                summary['metrics'][name]['rate'] = rate
        
        # Calculate correlations
        metric_names = list(self.processors.keys())
        for i, name1 in enumerate(metric_names):
            for name2 in metric_names[i+1:]:
                values1 = [w['value'] for w in self.processors[name1].get_window()]
                values2 = [w['value'] for w in self.processors[name2].get_window()]
                
                if len(values1) >= 5 and len(values2) >= 5:
                    corr = self.calculator.calculate_correlation(values1, values2)
                    if abs(corr) > 0.5:  # Only track significant correlations
                        summary['correlations'][f"{name1}_{name2}"] = corr
        
        return summary

    def add_alert_rule(self, metric: str, condition: str, 
                       threshold: float, severity: str = 'warning'):
        """
        Add alert rule
        
        Args:
            metric: Metric name to monitor
            condition: Condition ('gt', 'lt', 'eq', 'ne', 'ge', 'le')
            threshold: Threshold value
            severity: Alert severity
        """
        self.alert_rules.append({
            'metric': metric,
            'condition': condition,
            'threshold': threshold,
            'severity': severity,
            'enabled': True
        })
        logger.info(f"Alert rule added: {metric} {condition} {threshold}")

    def remove_alert_rule(self, metric: str):
        """Remove alert rule for metric"""
        self.alert_rules = [r for r in self.alert_rules if r['metric'] != metric]

    def _check_alerts(self, telemetry: Dict, timestamp: datetime):
        """Check alert rules against telemetry"""
        for rule in self.alert_rules:
            if not rule.get('enabled', True):
                continue
            
            metric = rule['metric']
            if metric not in telemetry:
                continue
            
            value = telemetry[metric]
            threshold = rule['threshold']
            condition = rule['condition']
            
            triggered = False
            if condition == 'gt' and value > threshold:
                triggered = True
            elif condition == 'lt' and value < threshold:
                triggered = True
            elif condition == 'ge' and value >= threshold:
                triggered = True
            elif condition == 'le' and value <= threshold:
                triggered = True
            elif condition == 'eq' and value == threshold:
                triggered = True
            elif condition == 'ne' and value != threshold:
                triggered = True
            
            if triggered:
                self._trigger_alert(metric, value, threshold, rule['severity'], timestamp)

    def _trigger_alert(self, metric: str, value: float, threshold: float,
                       severity: str, timestamp: datetime):
        """Trigger an alert"""
        alert_id = f"alert_{metric}_{timestamp.strftime('%Y%m%d%H%M%S')}"
        
        # Check if alert already active (avoid duplicates)
        if metric in self.active_alerts:
            return
        
        alert = TelemetryAlert(
            alert_id=alert_id,
            timestamp=timestamp.isoformat(),
            metric=metric,
            value=value,
            threshold=threshold,
            severity=severity,
            message=f"{metric} {value:.2f} exceeded threshold {threshold:.2f}"
        )
        
        self.active_alerts[metric] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Alert triggered: {alert.message}")
        
        if self.on_alert_callback:
            self.on_alert_callback(alert)

    def clear_alert(self, metric: str):
        """Clear alert for metric"""
        if metric in self.active_alerts:
            del self.active_alerts[metric]

    def _analytics_loop(self):
        """Background analytics processing loop"""
        while self.running:
            try:
                # Generate periodic analytics
                summary = self.get_analytics_summary()
                
                # Update windows
                self._update_windows(summary)
                
                # Callback
                if self.on_metric_callback:
                    self.on_metric_callback(summary)
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Analytics loop error: {e}")
                time.sleep(1)

    def _update_windows(self, summary: Dict):
        """Update analytics windows"""
        now = datetime.now()
        window_id = now.strftime('%Y%m%d_%H%M')
        
        if window_id not in self.windows:
            self.windows[window_id] = AnalyticsWindow(
                window_id=window_id,
                start_time=now.isoformat(),
                end_time=now.isoformat(),
                duration_seconds=0,
                sample_count=0,
                metrics={}
            )
        
        window = self.windows[window_id]
        window.end_time = now.isoformat()
        window.duration_seconds = self.window_duration
        window.metrics = summary.get('metrics', {})
        
        # Count samples
        total_samples = sum(
            len(p.get_all()) for p in self.processors.values()
        )
        window.sample_count = total_samples

    def _get_unit(self, metric: str) -> str:
        """Get unit for metric"""
        units = {
            'altitude': 'm',
            'velocity': 'm/s',
            'climb_rate': 'm/s',
            'battery_voltage': 'V',
            'battery_current': 'A',
            'battery_percentage': '%',
            'temperature': '°C',
            'pressure': 'Pa',
            'motor_rpm': 'RPM',
            'throttle': '%',
            'rssi': 'dBm',
            'satellites': 'count'
        }
        return units.get(metric, '')

    def export_analytics(self, filepath: str, 
                        window_minutes: int = 60) -> bool:
        """Export analytics report"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'summary': self.get_analytics_summary(),
                'active_alerts': [asdict(a) for a in self.active_alerts.values()],
                'alert_history': [asdict(a) for a in self.alert_history[-100:]],
                'windows': {
                    wid: asdict(w) 
                    for wid, w in self.windows.items()
                },
                'metric_history': {
                    name: list(history)[-100:]
                    for name, history in self.metric_history.items()
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Analytics exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            return False

    def set_callbacks(self, on_metric: Optional[Callable] = None,
                     on_alert: Optional[Callable] = None):
        """Set analytics callbacks"""
        self.on_metric_callback = on_metric
        self.on_alert_callback = on_alert


# Convenience function
def create_telemetry_analytics(config: Optional[Dict] = None) -> TelemetryAnalytics:
    """Create and return a Telemetry Analytics instance"""
    return TelemetryAnalytics(config)


__all__ = [
    'TelemetryAnalytics',
    'create_telemetry_analytics',
    'StreamProcessor',
    'MetricCalculator',
    'TelemetryMetric',
    'AnalyticsWindow',
    'TelemetryAlert',
    'MetricType'
]
