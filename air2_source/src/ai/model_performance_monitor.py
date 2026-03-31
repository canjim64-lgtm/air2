"""
AirOne v4.0 - Model Performance Monitor
Monitors and evaluates self-training model performance in real-time
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PerformanceStatus(Enum):
    """Model performance status"""
    EXCELLENT = "excellent"  # > 95%
    GOOD = "good"            # > 85%
    ACCEPTABLE = "acceptable" # > 70%
    POOR = "poor"            # > 50%
    CRITICAL = "critical"    # <= 50%


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    timestamp: str
    level: str
    metric: str
    current_value: float
    threshold: float
    message: str
    recommended_action: str


@dataclass
class ModelEvaluation:
    """Model evaluation result"""
    evaluation_id: str
    timestamp: str
    samples_evaluated: int
    metrics: Dict[str, float]
    status: str
    alerts: List[PerformanceAlert]
    recommendations: List[str]


class PerformanceMonitor:
    """
    Real-time model performance monitoring
    
    Tracks prediction accuracy, drift detection, and generates alerts
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Monitoring windows
        self.short_window = self.config.get('short_window', 50)
        self.medium_window = self.config.get('medium_window', 200)
        self.long_window = self.config.get('long_window', 1000)
        
        # Thresholds
        self.accuracy_thresholds = {
            'excellent': 0.95,
            'good': 0.85,
            'acceptable': 0.70,
            'poor': 0.50
        }
        
        self.drift_threshold = self.config.get('drift_threshold', 0.1)
        self.alert_cooldown_seconds = self.config.get('alert_cooldown', 60)
        
        # Data storage
        self.prediction_history: deque = deque(maxlen=self.long_window)
        self.actual_history: deque = deque(maxlen=self.long_window)
        self.error_history: deque = deque(maxlen=self.long_window)
        self.latency_history: deque = deque(maxlen=self.short_window * 2)
        
        # Alerts
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []
        self.last_alert_time: Dict[str, datetime] = {}
        
        # Baseline metrics
        self.baseline_metrics: Dict[str, float] = {}
        self.baseline_set = False
        
        # Callbacks
        self.on_alert_callback: Optional[Callable] = None
        
        # Threading
        self.lock = threading.Lock()
        
        logger.info("Performance Monitor initialized")

    def record_prediction(self, prediction: Dict[str, Any], 
                         actual: Optional[Dict[str, Any]] = None,
                         latency_ms: float = 0):
        """
        Record a prediction for monitoring
        
        Args:
            prediction: Model prediction
            actual: Actual values (when available)
            latency_ms: Prediction latency in milliseconds
        """
        with self.lock:
            self.prediction_history.append(prediction)
            self.latency_history.append(latency_ms)
            
            if actual:
                self.actual_history.append(actual)
                
                # Calculate errors
                errors = self._calculate_errors(prediction, actual)
                self.error_history.append(errors)
                
                # Check for drift and generate alerts
                self._check_drift()
                self._check_accuracy()
                self._check_latency()

    def _calculate_errors(self, prediction: Dict, actual: Dict) -> Dict[str, float]:
        """Calculate prediction errors"""
        errors = {}
        
        for key, pred_val in prediction.items():
            if key.startswith('predicted_') and isinstance(pred_val, (int, float)):
                actual_key = key.replace('predicted_', '')
                actual_val = actual.get(actual_key)
                
                if actual_val is not None:
                    abs_error = abs(pred_val - actual_val)
                    rel_error = abs_error / (abs(actual_val) + 1e-6)
                    errors[actual_key] = {
                        'absolute': abs_error,
                        'relative': rel_error,
                        'accuracy': 1 - min(rel_error, 1.0)
                    }
        
        return errors

    def _check_drift(self):
        """Check for prediction drift"""
        if len(self.error_history) < self.medium_window:
            return
        
        recent_errors = list(self.error_history)[-self.short_window:]
        older_errors = list(self.error_history)[-self.medium_window:-self.short_window]
        
        for metric in ['altitude', 'velocity', 'battery_percentage']:
            recent_avg = np.mean([e.get(metric, {}).get('relative', 0) for e in recent_errors])
            older_avg = np.mean([e.get(metric, {}).get('relative', 0) for e in older_errors])
            
            drift = recent_avg - older_avg
            
            if drift > self.drift_threshold:
                self._generate_alert(
                    level=AlertLevel.WARNING,
                    metric=f"{metric}_drift",
                    current_value=drift,
                    threshold=self.drift_threshold,
                    message=f"Prediction drift detected for {metric}",
                    recommended_action=f"Consider retraining the model with recent {metric} data"
                )

    def _check_accuracy(self):
        """Check prediction accuracy"""
        if len(self.error_history) < self.short_window:
            return
        
        recent_errors = list(self.error_history)[-self.short_window:]
        
        for metric in ['altitude', 'velocity', 'battery_percentage']:
            accuracies = [e.get(metric, {}).get('accuracy', 0) for e in recent_errors]
            avg_accuracy = np.mean(accuracies)
            
            if avg_accuracy < self.accuracy_thresholds['poor']:
                self._generate_alert(
                    level=AlertLevel.CRITICAL,
                    metric=f"{metric}_accuracy",
                    current_value=avg_accuracy,
                    threshold=self.accuracy_thresholds['acceptable'],
                    message=f"Critical accuracy drop for {metric}: {avg_accuracy:.1%}",
                    recommended_action="Immediate model retraining required"
                )
            elif avg_accuracy < self.accuracy_thresholds['acceptable']:
                self._generate_alert(
                    level=AlertLevel.WARNING,
                    metric=f"{metric}_accuracy",
                    current_value=avg_accuracy,
                    threshold=self.accuracy_thresholds['good'],
                    message=f"Low accuracy for {metric}: {avg_accuracy:.1%}",
                    recommended_action="Schedule model retraining"
                )

    def _check_latency(self):
        """Check prediction latency"""
        if len(self.latency_history) < self.short_window:
            return
        
        avg_latency = np.mean(self.latency_history[-self.short_window:])
        
        if avg_latency > 100:  # 100ms threshold
            self._generate_alert(
                level=AlertLevel.WARNING,
                metric="prediction_latency",
                current_value=avg_latency,
                threshold=100,
                message=f"High prediction latency: {avg_latency:.1f}ms",
                recommended_action="Consider model optimization or hardware upgrade"
            )

    def _generate_alert(self, level: AlertLevel, metric: str,
                       current_value: float, threshold: float,
                       message: str, recommended_action: str):
        """Generate performance alert"""
        # Check cooldown
        now = datetime.now()
        if metric in self.last_alert_time:
            cooldown = timedelta(seconds=self.alert_cooldown_seconds)
            if now - self.last_alert_time[metric] < cooldown:
                return
        
        alert_id = f"alert_{metric}_{now.strftime('%Y%m%d%H%M%S')}"
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            timestamp=now.isoformat(),
            level=level.value,
            metric=metric,
            current_value=current_value,
            threshold=threshold,
            message=message,
            recommended_action=recommended_action
        )
        
        self.active_alerts[metric] = alert
        self.alert_history.append(alert)
        self.last_alert_time[metric] = now
        
        logger.warning(f"Alert [{level.value}]: {message}")
        
        if self.on_alert_callback:
            self.on_alert_callback(alert)

    def set_baseline(self, evaluation: ModelEvaluation):
        """Set baseline metrics for comparison"""
        self.baseline_metrics = evaluation.metrics.copy()
        self.baseline_set = True
        logger.info("Baseline metrics set")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self.lock:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'samples_recorded': len(self.prediction_history),
                'errors_recorded': len(self.error_history)
            }
            
            # Accuracy metrics
            if self.error_history:
                recent_errors = list(self.error_history)[-self.short_window:]
                
                for metric in ['altitude', 'velocity', 'battery_percentage']:
                    accuracies = [e.get(metric, {}).get('accuracy', 0) for e in recent_errors]
                    if accuracies:
                        metrics[f'{metric}_accuracy_mean'] = float(np.mean(accuracies))
                        metrics[f'{metric}_accuracy_std'] = float(np.std(accuracies))
                        metrics[f'{metric}_accuracy_min'] = float(np.min(accuracies))
                        metrics[f'{metric}_accuracy_max'] = float(np.max(accuracies))
            
            # Latency metrics
            if self.latency_history:
                metrics['latency_mean_ms'] = float(np.mean(self.latency_history))
                metrics['latency_std_ms'] = float(np.std(self.latency_history))
                metrics['latency_max_ms'] = float(np.max(self.latency_history))
                metrics['latency_p95_ms'] = float(np.percentile(self.latency_history, 95))
            
            # Status
            metrics['status'] = self._get_performance_status().value
            metrics['active_alerts'] = len(self.active_alerts)
            
            return metrics

    def _get_performance_status(self) -> PerformanceStatus:
        """Determine overall performance status"""
        if not self.error_history:
            return PerformanceStatus.ACCEPTABLE
        
        recent_errors = list(self.error_history)[-self.short_window:]
        
        all_accuracies = []
        for e in recent_errors:
            for metric_data in e.values():
                if isinstance(metric_data, dict) and 'accuracy' in metric_data:
                    all_accuracies.append(metric_data['accuracy'])
        
        if not all_accuracies:
            return PerformanceStatus.ACCEPTABLE
        
        avg_accuracy = np.mean(all_accuracies)
        
        if avg_accuracy >= self.accuracy_thresholds['excellent']:
            return PerformanceStatus.EXCELLENT
        elif avg_accuracy >= self.accuracy_thresholds['good']:
            return PerformanceStatus.GOOD
        elif avg_accuracy >= self.accuracy_thresholds['acceptable']:
            return PerformanceStatus.ACCEPTABLE
        elif avg_accuracy >= self.accuracy_thresholds['poor']:
            return PerformanceStatus.POOR
        else:
            return PerformanceStatus.CRITICAL

    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def clear_alert(self, metric: str) -> bool:
        """Clear an alert"""
        if metric in self.active_alerts:
            del self.active_alerts[metric]
            return True
        return False

    def clear_all_alerts(self):
        """Clear all alerts"""
        self.active_alerts.clear()

    def evaluate_model(self, test_data: List[Dict], 
                      actual_data: List[Dict]) -> ModelEvaluation:
        """
        Evaluate model on test data
        
        Args:
            test_data: Predictions to evaluate
            actual_data: Actual values
            
        Returns:
            ModelEvaluation object
        """
        evaluation_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()
        
        # Calculate metrics
        metrics = {}
        errors_by_metric = {}
        
        for pred, actual in zip(test_data, actual_data):
            errors = self._calculate_errors(pred, actual)
            
            for metric, error_data in errors.items():
                if metric not in errors_by_metric:
                    errors_by_metric[metric] = []
                errors_by_metric[metric].append(error_data)
        
        # Aggregate metrics
        for metric, error_list in errors_by_metric.items():
            accuracies = [e['accuracy'] for e in error_list]
            metrics[f'{metric}_accuracy'] = float(np.mean(accuracies))
            metrics[f'{metric}_mae'] = float(np.mean([e['absolute'] for e in error_list]))
            metrics[f'{metric}_rmse'] = float(np.sqrt(np.mean([e['absolute']**2 for e in error_list])))
        
        # Determine status
        overall_accuracy = np.mean([v for k, v in metrics.items() if 'accuracy' in k])
        
        if overall_accuracy >= self.accuracy_thresholds['excellent']:
            status = PerformanceStatus.EXCELLENT.value
        elif overall_accuracy >= self.accuracy_thresholds['good']:
            status = PerformanceStatus.GOOD.value
        elif overall_accuracy >= self.accuracy_thresholds['acceptable']:
            status = PerformanceStatus.ACCEPTABLE.value
        else:
            status = PerformanceStatus.POOR.value
        
        # Generate recommendations
        recommendations = []
        
        if overall_accuracy < self.accuracy_thresholds['good']:
            recommendations.append("Consider retraining with more diverse data")
        
        for metric, acc in [(k.replace('_accuracy', ''), v) for k, v in metrics.items() if 'accuracy' in k]:
            if acc < self.accuracy_thresholds['acceptable']:
                recommendations.append(f"Focus on improving {metric} prediction accuracy")
        
        if metrics.get('latency_mean_ms', 0) > 50:
            recommendations.append("Optimize model for faster inference")
        
        evaluation = ModelEvaluation(
            evaluation_id=evaluation_id,
            timestamp=timestamp,
            samples_evaluated=len(test_data),
            metrics=metrics,
            status=status,
            alerts=self.get_active_alerts(),
            recommendations=recommendations
        )
        
        return evaluation

    def get_performance_trend(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance trend over time"""
        if len(self.alert_history) < 2:
            return {'trend': 'insufficient_data'}
        
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        recent_alerts = [
            a for a in self.alert_history
            if datetime.fromisoformat(a.timestamp) >= window_start
        ]
        
        critical_count = sum(1 for a in recent_alerts if a.level == AlertLevel.CRITICAL.value)
        warning_count = sum(1 for a in recent_alerts if a.level == AlertLevel.WARNING.value)
        
        if critical_count > 5 or warning_count > 10:
            trend = 'degrading'
        elif critical_count == 0 and warning_count < 3:
            trend = 'improving'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'window_minutes': window_minutes,
            'critical_alerts': critical_count,
            'warning_alerts': warning_count,
            'total_alerts': len(recent_alerts)
        }

    def export_report(self, filepath: str) -> bool:
        """Export performance report to file"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'current_metrics': self.get_current_metrics(),
                'performance_status': self._get_performance_status().value,
                'active_alerts': [asdict(a) for a in self.get_active_alerts()],
                'alert_history': [asdict(a) for a in self.alert_history[-100:]],
                'performance_trend': self.get_performance_trend(),
                'baseline_metrics': self.baseline_metrics,
                'baseline_set': self.baseline_set
            }
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Performance report exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False

    def set_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Set alert callback"""
        self.on_alert_callback = callback


class ModelEvaluator:
    """
    Comprehensive model evaluation system
    """

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.evaluation_history: List[ModelEvaluation] = []

    def run_evaluation(self, model: Any, test_data: List[Dict],
                      actual_data: List[Dict]) -> ModelEvaluation:
        """Run comprehensive model evaluation"""
        evaluation = self.monitor.evaluate_model(test_data, actual_data)
        self.evaluation_history.append(evaluation)
        return evaluation

    def compare_models(self, models: Dict[str, Any], 
                      test_data: List[Dict],
                      actual_data: List[Dict]) -> Dict[str, Any]:
        """Compare multiple models"""
        results = {}
        
        for name, model in models.items():
            # For now, just use the monitor's evaluation
            # In a full implementation, would run each model
            evaluation = self.monitor.evaluate_model(test_data, actual_data)
            results[name] = {
                'status': evaluation.status,
                'metrics': evaluation.metrics,
                'samples': evaluation.samples_evaluated
            }
        
        # Rank models
        ranked = sorted(
            results.items(),
            key=lambda x: np.mean([v for k, v in x[1]['metrics'].items() if 'accuracy' in k]),
            reverse=True
        )
        
        return {
            'results': results,
            'ranking': [name for name, _ in ranked],
            'best_model': ranked[0][0] if ranked else None
        }

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary of all evaluations"""
        if not self.evaluation_history:
            return {'evaluations': 0}
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'latest_status': self.evaluation_history[-1].status,
            'latest_accuracy': np.mean([
                v for k, v in self.evaluation_history[-1].metrics.items()
                if 'accuracy' in k
            ]),
            'status_history': [e.status for e in self.evaluation_history[-10:]]
        }


__all__ = [
    'PerformanceMonitor',
    'ModelEvaluator',
    'PerformanceAlert',
    'ModelEvaluation',
    'AlertLevel',
    'PerformanceStatus'
]
