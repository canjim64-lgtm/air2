"""
AirOne v4.0 - Concept Drift Detection
Detect changes in data distribution and model performance over time
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available")


class DriftType(Enum):
    """Types of concept drift"""
    SUDDEN = "sudden"       # Abrupt change
    GRADUAL = "gradual"     # Slow transition
    RECURRING = "recurring" # Periodic patterns
    INCREMENTAL = "incremental"  # Continuous change


class DriftSeverity(Enum):
    """Drift severity levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftDetection:
    """Drift detection result"""
    timestamp: str
    drift_detected: bool
    drift_type: str
    severity: str
    confidence: float
    affected_features: List[str]
    statistical_tests: Dict[str, float]
    recommended_action: str


@dataclass
class DriftReport:
    """Comprehensive drift report"""
    report_id: str
    generated_at: str
    analysis_window_hours: float
    total_samples: int
    drift_events: List[DriftDetection]
    overall_drift_score: float
    model_performance_trend: str
    recommendations: List[str]


class StatisticalDriftDetector:
    """
    Statistical tests for drift detection
    """

    def __init__(self, window_size: int = 100, alpha: float = 0.05):
        self.window_size = window_size
        self.alpha = alpha
        self.reference_data: deque = deque(maxlen=window_size)
        self.current_data: deque = deque(maxlen=window_size)
        self.is_reference_set = False

    def set_reference(self, data: np.ndarray):
        """Set reference distribution"""
        self.reference_data = deque(list(data[-self.window_size:]), maxlen=self.window_size)
        self.is_reference_set = True

    def add_sample(self, value: float):
        """Add sample to current distribution"""
        self.current_data.append(value)

    def reset_current(self):
        """Reset current distribution"""
        self.current_data.clear()

    def ks_test(self) -> Tuple[float, bool]:
        """Kolmogorov-Smirnov test"""
        if not self.is_reference_set or len(self.current_data) < 10:
            return 1.0, False
        
        if not SCIPY_AVAILABLE:
            # Simple mean comparison fallback
            ref_mean = np.mean(self.reference_data)
            cur_mean = np.mean(self.current_data)
            ref_std = np.std(self.reference_data) + 1e-6
            z_score = abs(cur_mean - ref_mean) / ref_std
            return z_score, z_score > 2
        
        stat, p_value = stats.ks_2samp(self.reference_data, self.current_data)
        return p_value, p_value < self.alpha

    def psi_test(self, n_buckets: int = 10) -> Tuple[float, bool]:
        """Population Stability Index"""
        if not self.is_reference_set or len(self.current_data) < 10:
            return 0.0, False
        
        ref_data = np.array(self.reference_data)
        cur_data = np.array(self.current_data)
        
        # Create buckets
        breakpoints = np.percentile(ref_data, np.linspace(0, 100, n_buckets + 1))
        breakpoints = np.unique(breakpoints)
        
        if len(breakpoints) < 2:
            return 0.0, False
        
        # Calculate distributions
        ref_dist = np.histogram(ref_data, bins=breakpoints)[0] / len(ref_data) + 1e-6
        cur_dist = np.histogram(cur_data, bins=breakpoints)[0] / len(cur_data) + 1e-6
        
        # Normalize
        ref_dist = ref_dist / np.sum(ref_dist)
        cur_dist = cur_dist / np.sum(cur_dist)
        
        # Calculate PSI
        psi = np.sum((cur_dist - ref_dist) * np.log(cur_dist / ref_dist))
        
        # Interpret PSI
        drift = psi > 0.25  # Significant drift threshold
        return psi, drift

    def adwin_test(self, delta: float = 0.01) -> Tuple[float, bool]:
        """ADWIN-style drift detection (simplified)"""
        if len(self.current_data) < 20:
            return 0.0, False
        
        data = np.array(self.current_data)
        n = len(data)
        
        # Find optimal split point
        max_stat = 0
        best_split = 0
        
        for split in range(n // 4, 3 * n // 4):
            left = data[:split]
            right = data[split:]
            
            n0, n1 = len(left), len(right)
            m0, m1 = np.mean(left), np.mean(right)
            
            # Hoeffding bound
            m = (n0 * m0 + n1 * m1) / (n0 + n1)
            eps = np.sqrt(np.log(4 / delta) / (2 * (1/n0 + 1/n1)))
            
            stat = abs(m0 - m1)
            if stat > max_stat:
                max_stat = stat
                best_split = split
        
        drift = max_stat > eps if 'eps' in locals() else False
        return max_stat, drift

    def detect(self) -> Dict[str, Any]:
        """Run all drift detection tests"""
        results = {}
        
        ks_p, ks_drift = self.ks_test()
        results['ks_test'] = {
            'p_value': float(ks_p),
            'drift_detected': bool(ks_drift)
        }
        
        psi, psi_drift = self.psi_test()
        results['psi_test'] = {
            'psi_value': float(psi),
            'drift_detected': bool(psi_drift)
        }
        
        adwin_stat, adwin_drift = self.adwin_test()
        results['adwin_test'] = {
            'statistic': float(adwin_stat),
            'drift_detected': bool(adwin_drift)
        }
        
        # Overall drift (majority vote)
        drifts = [ks_drift, psi_drift, adwin_drift]
        results['overall_drift'] = sum(drifts) >= 2
        
        return results


class PerformanceDriftDetector:
    """
    Detect drift through model performance degradation
    """

    def __init__(self, window_size: int = 200):
        self.window_size = window_size
        self.predictions: deque = deque(maxlen=window_size)
        self.actuals: deque = deque(maxlen=window_size)
        self.performance_history: deque = deque(maxlen=window_size)
        self.timestamps: deque = deque(maxlen=window_size)

    def add_prediction(self, prediction: float, actual: float, 
                       timestamp: Optional[datetime] = None):
        """Record prediction and actual value"""
        self.predictions.append(prediction)
        self.actuals.append(actual)
        self.timestamps.append(timestamp or datetime.now())
        
        # Calculate instantaneous performance
        error = abs(prediction - actual)
        self.performance_history.append(1 / (1 + error))  # Convert to accuracy-like metric

    def get_performance_trend(self) -> Dict[str, Any]:
        """Analyze performance trend"""
        if len(self.performance_history) < 20:
            return {'trend': 'insufficient_data'}
        
        perf = np.array(self.performance_history)
        
        # Calculate trend
        x = np.arange(len(perf))
        slope, _ = np.polyfit(x, perf, 1)
        
        # Recent vs older performance
        recent = perf[-50:] if len(perf) >= 50 else perf
        older = perf[:-50] if len(perf) >= 50 else perf[:len(perf)//2]
        
        recent_mean = np.mean(recent)
        older_mean = np.mean(older)
        
        # Determine trend
        if slope < -0.001:
            trend = 'degrading'
        elif slope > 0.001:
            trend = 'improving'
        else:
            trend = 'stable'
        
        # Calculate degradation rate
        degradation_rate = (older_mean - recent_mean) / (older_mean + 1e-6)
        
        return {
            'trend': trend,
            'slope': float(slope),
            'recent_performance': float(recent_mean),
            'older_performance': float(older_mean),
            'degradation_rate': float(degradation_rate),
            'samples_analyzed': len(perf)
        }

    def detect_performance_drift(self, threshold: float = 0.1) -> Tuple[bool, float]:
        """Detect significant performance degradation"""
        trend = self.get_performance_trend()
        
        if trend['trend'] == 'insufficient_data':
            return False, 0.0
        
        degradation = trend['degradation_rate']
        drift_detected = degradation > threshold
        
        return drift_detected, degradation


class FeatureDriftMonitor:
    """
    Monitor drift across multiple features
    """

    def __init__(self, feature_names: List[str], window_size: int = 500):
        self.feature_names = feature_names
        self.window_size = window_size
        
        # Per-feature detectors
        self.detectors: Dict[str, StatisticalDriftDetector] = {
            name: StatisticalDriftDetector(window_size)
            for name in feature_names
        }
        
        self.feature_stats: Dict[str, Dict] = {}

    def set_reference(self, data: Dict[str, np.ndarray]):
        """Set reference distributions for all features"""
        for name, values in data.items():
            if name in self.detectors:
                self.detectors[name].set_reference(values)
                self.feature_stats[name] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values))
                }

    def add_sample(self, features: Dict[str, float]):
        """Add sample to all feature monitors"""
        for name, value in features.items():
            if name in self.detectors:
                self.detectors[name].add_sample(value)

    def detect_all(self) -> Dict[str, Any]:
        """Detect drift across all features"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'features': {},
            'drifted_features': [],
            'total_features': len(self.feature_names),
            'drift_ratio': 0.0
        }
        
        for name, detector in self.detectors.items():
            detection = detector.detect()
            results['features'][name] = detection
            
            if detection['overall_drift']:
                results['drifted_features'].append({
                    'name': name,
                    'reference_mean': self.feature_stats.get(name, {}).get('mean', 0),
                    'tests': detection
                })
        
        results['drift_ratio'] = len(results['drifted_features']) / len(self.feature_names)
        
        return results


class ConceptDriftDetector:
    """
    Comprehensive concept drift detection system
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Feature drift monitor
        self.feature_monitor: Optional[FeatureDriftMonitor] = None
        
        # Performance drift detector
        self.performance_detector = PerformanceDriftDetector(
            window_size=self.config.get('performance_window', 200)
        )
        
        # Drift history
        self.drift_history: List[DriftDetection] = []
        
        # Configuration
        self.drift_threshold = self.config.get('drift_threshold', 0.1)
        self.alert_cooldown = self.config.get('alert_cooldown', 300)  # seconds
        self.last_alert_time: Optional[datetime] = None

    def initialize(self, reference_data: Dict[str, np.ndarray],
                  feature_names: Optional[List[str]] = None):
        """Initialize with reference data"""
        if feature_names is None:
            feature_names = list(reference_data.keys())
        
        self.feature_monitor = FeatureDriftMonitor(feature_names)
        self.feature_monitor.set_reference(reference_data)
        
        logger.info(f"Drift detector initialized with {len(feature_names)} features")

    def add_sample(self, features: Dict[str, float],
                  prediction: Optional[float] = None,
                  actual: Optional[float] = None):
        """
        Add sample for drift monitoring
        
        Args:
            features: Feature values
            prediction: Model prediction
            actual: Actual value (when available)
        """
        if self.feature_monitor:
            self.feature_monitor.add_sample(features)
        
        if prediction is not None and actual is not None:
            self.performance_detector.add_prediction(prediction, actual)

    def detect(self) -> DriftDetection:
        """Perform drift detection"""
        timestamp = datetime.now()
        
        # Feature drift
        feature_drift = {}
        drifted_features = []
        
        if self.feature_monitor:
            feature_drift = self.feature_monitor.detect_all()
            drifted_features = [f['name'] for f in feature_drift.get('drifted_features', [])]
        
        # Performance drift
        perf_drift, perf_degradation = self.performance_detector.detect_performance_drift(
            self.drift_threshold
        )
        
        # Determine overall drift
        drift_detected = len(drifted_features) > 0 or perf_drift
        
        # Calculate severity
        drift_ratio = feature_drift.get('drift_ratio', 0)
        if drift_ratio > 0.5 or perf_degradation > 0.2:
            severity = DriftSeverity.CRITICAL
        elif drift_ratio > 0.3 or perf_degradation > 0.15:
            severity = DriftSeverity.HIGH
        elif drift_ratio > 0.2 or perf_degradation > 0.1:
            severity = DriftSeverity.MEDIUM
        elif drift_ratio > 0.1 or perf_degradation > 0.05:
            severity = DriftSeverity.LOW
        else:
            severity = DriftSeverity.NONE
        
        # Determine drift type
        drift_type = self._classify_drift_type(feature_drift, perf_degradation)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(severity, drifted_features, perf_drift)
        
        # Statistical tests summary
        stat_tests = {}
        if feature_drift.get('features'):
            for feat, data in feature_drift['features'].items():
                if 'ks_test' in data:
                    stat_tests[f'{feat}_ks_pvalue'] = data['ks_test']['p_value']
        
        detection = DriftDetection(
            timestamp=timestamp.isoformat(),
            drift_detected=drift_detected,
            drift_type=drift_type.value if drift_detected else DriftType.SUDDEN.value,
            severity=severity.value,
            confidence=1.0 - (drift_ratio if drift_detected else 0),
            affected_features=drifted_features,
            statistical_tests=stat_tests,
            recommended_action=recommendation
        )
        
        # Record in history
        if drift_detected:
            self.drift_history.append(detection)
        
        return detection

    def _classify_drift_type(self, feature_drift: Dict, 
                            perf_degradation: float) -> DriftType:
        """Classify the type of drift"""
        if not feature_drift:
            return DriftType.SUDDEN
        
        # Check for gradual drift (many features with small drift)
        drift_ratio = feature_drift.get('drift_ratio', 0)
        n_drifted = len(feature_drift.get('drifted_features', []))
        
        if drift_ratio > 0.3 and n_drifted > 3:
            return DriftType.GRADUAL
        
        # Check for recurring patterns (would need historical analysis)
        if len(self.drift_history) >= 5:
            recent_drifts = self.drift_history[-5:]
            if all(d.severity in ['low', 'medium'] for d in recent_drifts):
                return DriftType.RECURRING
        
        # Check for incremental drift (performance degradation)
        if perf_degradation > 0.1:
            return DriftType.INCREMENTAL
        
        return DriftType.SUDDEN

    def _generate_recommendation(self, severity: DriftSeverity,
                                drifted_features: List[str],
                                perf_drift: bool) -> str:
        """Generate recommended action"""
        if severity == DriftSeverity.NONE:
            return "No action required - continue monitoring"
        
        recommendations = []
        
        if severity in [DriftSeverity.CRITICAL, DriftSeverity.HIGH]:
            recommendations.append("Immediate model retraining recommended")
        
        if perf_drift:
            recommendations.append("Model performance degraded - consider retraining")
        
        if len(drifted_features) > 0:
            recommendations.append(f"Monitor features: {', '.join(drifted_features)}")
        
        if severity == DriftSeverity.MEDIUM:
            recommendations.append("Schedule model evaluation within 24 hours")
        
        if severity == DriftSeverity.LOW:
            recommendations.append("Continue monitoring - no immediate action needed")
        
        return "; ".join(recommendations)

    def get_drift_report(self, window_hours: float = 24) -> DriftReport:
        """Generate comprehensive drift report"""
        now = datetime.now()
        window_start = now - timedelta(hours=window_hours)
        
        # Filter recent drift events
        recent_drifts = [
            d for d in self.drift_history
            if datetime.fromisoformat(d.timestamp) >= window_start
        ]
        
        # Calculate overall drift score
        if recent_drifts:
            severity_scores = {
                'none': 0, 'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0
            }
            overall_score = np.mean([
                severity_scores.get(d.severity, 0) for d in recent_drifts
            ])
        else:
            overall_score = 0.0
        
        # Get performance trend
        perf_trend = self.performance_detector.get_performance_trend()
        
        # Generate recommendations
        recommendations = []
        
        if overall_score > 0.5:
            recommendations.append("High drift detected - prioritize model retraining")
        
        if perf_trend.get('trend') == 'degrading':
            recommendations.append("Performance degrading - investigate root cause")
        
        if not recommendations:
            recommendations.append("System operating normally - continue monitoring")
        
        report = DriftReport(
            report_id=f"drift_report_{now.strftime('%Y%m%d_%H%M%S')}",
            generated_at=now.isoformat(),
            analysis_window_hours=window_hours,
            total_samples=len(self.performance_detector.performance_history),
            drift_events=recent_drifts[-20:],  # Last 20 events
            overall_drift_score=overall_score,
            model_performance_trend=perf_trend.get('trend', 'unknown'),
            recommendations=recommendations
        )
        
        return report

    def export_report(self, filepath: str) -> bool:
        """Export drift report to file"""
        try:
            report = self.get_drift_report()
            
            report_dict = {
                'report_id': report.report_id,
                'generated_at': report.generated_at,
                'analysis_window_hours': report.analysis_window_hours,
                'total_samples': report.total_samples,
                'overall_drift_score': report.overall_drift_score,
                'model_performance_trend': report.model_performance_trend,
                'drift_events': [asdict(d) for d in report.drift_events],
                'recommendations': report.recommendations
            }
            
            with open(filepath, 'w') as f:
                json.dump(report_dict, f, indent=2)
            
            logger.info(f"Drift report exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False


# Convenience function
def create_drift_detector(config: Optional[Dict] = None) -> ConceptDriftDetector:
    """Create and return a Concept Drift Detector instance"""
    return ConceptDriftDetector(config)


__all__ = [
    'ConceptDriftDetector',
    'create_drift_detector',
    'StatisticalDriftDetector',
    'PerformanceDriftDetector',
    'FeatureDriftMonitor',
    'DriftDetection',
    'DriftReport',
    'DriftType',
    'DriftSeverity'
]
