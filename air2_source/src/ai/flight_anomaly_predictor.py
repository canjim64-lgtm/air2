"""
AirOne v4.0 - Flight Anomaly Prediction System
Predicts and detects flight anomalies before they become critical
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
    from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


class AnomalyType(Enum):
    """Types of flight anomalies"""
    MOTOR_DEGRADATION = "motor_degradation"
    BATTERY_FAILURE = "battery_failure"
    SENSOR_DRIFT = "sensor_drift"
    CONTROL_INSTABILITY = "control_instability"
    STRUCTURAL_STRESS = "structural_stress"
    COMMUNICATION_LOSS = "communication_loss"
    GPS_ANOMALY = "gps_anomaly"
    ENVIRONMENTAL = "environmental"
    UNKNOWN = "unknown"


class AnomalySeverity(Enum):
    """Anomaly severity levels"""
    NORMAL = "normal"
    MONITOR = "monitor"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class AnomalyPrediction:
    """Anomaly prediction result"""
    timestamp: str
    anomaly_type: str
    severity: str
    probability: float
    confidence: float
    predicted_time_to_failure: Optional[float]  # seconds
    affected_systems: List[str]
    recommended_actions: List[str]
    feature_contributions: Dict[str, float]


@dataclass
class AnomalyReport:
    """Comprehensive anomaly report"""
    report_id: str
    generated_at: str
    total_samples_analyzed: int
    anomalies_detected: int
    anomaly_rate: float
    predictions: List[AnomalyPrediction]
    system_health_score: float
    recommendations: List[str]


class AnomalyFeatureExtractor:
    """
    Extract features for anomaly detection
    """

    def __init__(self):
        self.feature_names = []
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.baseline_stats = {}

    def extract_features(self, telemetry_sequence: List[Dict]) -> np.ndarray:
        """
        Extract features from telemetry sequence
        
        Args:
            telemetry_sequence: List of telemetry records
            
        Returns:
            Feature array
        """
        if len(telemetry_sequence) == 0:
            return np.array([])
        
        features = []
        
        # Current values
        current = telemetry_sequence[-1]
        current_features = self._extract_current_features(current)
        features.extend(current_features)
        
        # Statistical features
        if len(telemetry_sequence) >= 5:
            stats_features = self._extract_statistical_features(telemetry_sequence)
            features.extend(stats_features)
        
        # Trend features
        if len(telemetry_sequence) >= 10:
            trend_features = self._extract_trend_features(telemetry_sequence)
            features.extend(trend_features)
        
        # Frequency features
        if len(telemetry_sequence) >= 20:
            freq_features = self._extract_frequency_features(telemetry_sequence)
            features.extend(freq_features)
        
        if not self.feature_names:
            self._build_feature_names()
        
        return np.array(features)

    def _extract_current_features(self, telemetry: Dict) -> List[float]:
        """Extract current state features"""
        return [
            telemetry.get('altitude', 0) / 1000,
            telemetry.get('velocity', 0) / 100,
            telemetry.get('climb_rate', 0) / 20,
            telemetry.get('pitch', 0) / 45,
            telemetry.get('roll', 0) / 30,
            telemetry.get('throttle', 0),
            telemetry.get('battery_voltage', 0) / 20,
            telemetry.get('battery_current', 0) / 30,
            telemetry.get('battery_percentage', 0) / 100,
            telemetry.get('motor_rpm', 0) / 10000,
            telemetry.get('temperature', 0) / 100,
            telemetry.get('rssi', -100) / 100,
            telemetry.get('satellites', 0) / 20
        ]

    def _extract_statistical_features(self, sequence: List[Dict]) -> List[float]:
        """Extract statistical features from sequence"""
        features = []
        
        for key in ['altitude', 'velocity', 'battery_voltage', 'motor_rpm', 'temperature']:
            values = [t.get(key, 0) for t in sequence]
            features.extend([
                np.mean(values),
                np.std(values),
                np.min(values),
                np.max(values),
                np.percentile(values, 75) - np.percentile(values, 25)  # IQR
            ])
        
        return features

    def _extract_trend_features(self, sequence: List[Dict]) -> List[float]:
        """Extract trend features"""
        features = []
        window_sizes = [5, 10, 20]
        
        for key in ['altitude', 'velocity', 'battery_voltage', 'motor_rpm']:
            values = np.array([t.get(key, 0) for t in sequence])
            
            for window in window_sizes:
                if len(values) >= window:
                    # Linear trend
                    x = np.arange(window)
                    slope = np.polyfit(x, values[-window:], 1)[0]
                    features.append(slope)
                else:
                    features.append(0)
        
        return features

    def _extract_frequency_features(self, sequence: List[Dict]) -> List[float]:
        """Extract frequency domain features"""
        features = []
        
        for key in ['motor_rpm', 'velocity', 'climb_rate']:
            values = np.array([t.get(key, 0) for t in sequence])
            
            # Simple frequency analysis using zero crossings
            mean_val = np.mean(values)
            zero_crossings = np.sum(np.diff(np.sign(values - mean_val)) != 0)
            features.append(zero_crossings / len(values))
            
            # Variance ratio (high freq content)
            diff_var = np.var(np.diff(values))
            orig_var = np.var(values)
            features.append(diff_var / (orig_var + 1e-6))
        
        return features

    def _build_feature_names(self):
        """Build feature names list"""
        self.feature_names = (
            ['current_' + k for k in ['alt', 'vel', 'climb', 'pitch', 'roll', 
                                       'throttle', 'bat_v', 'bat_c', 'bat_pct', 
                                       'rpm', 'temp', 'rssi', 'sats']] +
            ['stats_' + k for k in ['alt_mean', 'alt_std', 'alt_min', 'alt_max', 'alt_iqr',
                                    'vel_mean', 'vel_std', 'vel_min', 'vel_max', 'vel_iqr',
                                    'batv_mean', 'batv_std', 'batv_min', 'batv_max', 'batv_iqr',
                                    'rpm_mean', 'rpm_std', 'rpm_min', 'rpm_max', 'rpm_iqr',
                                    'temp_mean', 'temp_std', 'temp_min', 'temp_max', 'temp_iqr']] +
            ['trend_' + k for k in ['alt_5', 'alt_10', 'alt_20',
                                    'vel_5', 'vel_10', 'vel_20',
                                    'batv_5', 'batv_10', 'batv_20',
                                    'rpm_5', 'rpm_10', 'rpm_20']] +
            ['freq_' + k for k in ['rpm_zc', 'rpm_var',
                                   'vel_zc', 'vel_var',
                                   'climb_zc', 'climb_var']]
        )

    def fit(self, X: np.ndarray):
        """Fit scaler"""
        self.scaler.fit(X)
        self.is_fitted = True
        
        # Store baseline statistics
        self.baseline_stats = {
            'mean': X.mean(axis=0).tolist(),
            'std': X.std(axis=0).tolist(),
            'min': X.min(axis=0).tolist(),
            'max': X.max(axis=0).tolist()
        }

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform features"""
        if not self.is_fitted:
            self.fit(X)
        return self.scaler.transform(X)


class AnomalyPredictor:
    """
    Multi-model anomaly prediction system
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Feature extractor
        self.feature_extractor = AnomalyFeatureExtractor()
        
        # Models for different anomaly types
        self.models = {}
        self.is_trained = False
        
        # Anomaly history
        self.anomaly_history: deque = deque(maxlen=1000)
        self.false_positive_buffer: deque = deque(maxlen=100)

    def train(self, normal_data: List[Dict], 
              anomaly_data: Optional[List[Tuple[Dict, str]]] = None) -> Dict[str, Any]:
        """
        Train anomaly prediction models
        
        Args:
            normal_data: Normal flight data
            anomaly_data: Optional labeled anomaly data [(telemetry, type), ...]
            
        Returns:
            Training results
        """
        if not SKLEARN_AVAILABLE:
            return {'error': 'scikit-learn not available'}
        
        results = {}
        
        # Train unsupervised model (Isolation Forest)
        logger.info("Training Isolation Forest...")
        X_normal = self._prepare_training_data(normal_data)
        self.models['isolation_forest'] = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
        self.models['isolation_forest'].fit(X_normal)
        results['isolation_forest'] = 'trained'
        
        # Train supervised models if anomaly data provided
        if anomaly_data:
            logger.info("Training supervised classifiers...")
            X_anomaly, y_anomaly = self._prepare_labeled_data(anomaly_data)
            X_all = np.vstack([X_normal, X_anomaly])
            y_all = np.hstack([
                np.zeros(len(X_normal)),  # Normal = 0
                np.ones(len(X_anomaly))   # Anomaly = 1
            ])
            
            # Binary classifier
            self.models['binary_classifier'] = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
            self.models['binary_classifier'].fit(X_all, y_all)
            results['binary_classifier'] = 'trained'
            
            # Multi-class classifier for anomaly types
            if len(set(y_anomaly)) > 1:
                self.models['type_classifier'] = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
                self.models['type_classifier'].fit(X_all, np.concatenate([
                    np.zeros(len(X_normal), dtype=int),
                    y_anomaly
                ]))
                results['type_classifier'] = 'trained'
        
        self.is_trained = True
        logger.info("Anomaly predictor training complete")
        
        return results

    def _prepare_training_data(self, data: List[Dict]) -> np.ndarray:
        """Prepare data for training"""
        features_list = []
        
        # Use sliding window
        window_size = 20
        for i in range(window_size, len(data)):
            window = data[i-window_size:i]
            features = self.feature_extractor.extract_features(window)
            if len(features) > 0:
                features_list.append(features)
        
        X = np.array(features_list)
        self.feature_extractor.fit(X)
        
        return X

    def _prepare_labeled_data(self, labeled_data: List[Tuple[Dict, str]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare labeled data for training"""
        anomaly_type_map = {
            'motor_degradation': 1,
            'battery_failure': 2,
            'sensor_drift': 3,
            'control_instability': 4,
            'structural_stress': 5,
            'communication_loss': 6,
            'gps_anomaly': 7,
            'environmental': 8
        }
        
        features_list = []
        labels = []
        
        window_size = 20
        for i in range(window_size, len(labeled_data)):
            window = labeled_data[i-window_size:i]
            features = self.feature_extractor.extract_features([t for t, _ in window])
            if len(features) > 0:
                features_list.append(features)
                # Use the label of the last sample in window
                _, label = window[-1]
                labels.append(anomaly_type_map.get(label, 0))
        
        return np.array(features_list), np.array(labels)

    def predict(self, telemetry_sequence: List[Dict]) -> AnomalyPrediction:
        """
        Predict anomalies from telemetry sequence
        
        Args:
            telemetry_sequence: Recent telemetry data
            
        Returns:
            AnomalyPrediction object
        """
        if not self.is_trained:
            return self._create_normal_prediction()
        
        # Extract features
        features = self.feature_extractor.extract_features(telemetry_sequence)
        if len(features) == 0:
            return self._create_normal_prediction()
        
        features_scaled = self.feature_extractor.transform(features.reshape(1, -1))
        
        # Get predictions from each model
        predictions = {}
        
        # Isolation Forest
        if 'isolation_forest' in self.models:
            if_score = self.models['isolation_forest'].decision_function(features_scaled)[0]
            if_prob = 1 / (1 + np.exp(if_score * 5))  # Convert to probability
            predictions['isolation_forest'] = if_prob
        
        # Binary classifier
        if 'binary_classifier' in self.models:
            bc_prob = self.models['binary_classifier'].predict_proba(features_scaled)[0, 1]
            predictions['binary_classifier'] = bc_prob
        
        # Type classifier
        anomaly_type = AnomalyType.UNKNOWN
        if 'type_classifier' in self.models:
            type_probs = self.models['type_classifier'].predict_proba(features_scaled)[0]
            type_idx = np.argmax(type_probs)
            type_map = {v: k for k, v in {
                'motor_degradation': 1, 'battery_failure': 2, 'sensor_drift': 3,
                'control_instability': 4, 'structural_stress': 5, 'communication_loss': 6,
                'gps_anomaly': 7, 'environmental': 8
            }.items()}
            anomaly_type = AnomalyType(type_map.get(type_idx, 'unknown'))
        
        # Combine predictions
        avg_probability = np.mean(list(predictions.values())) if predictions else 0
        
        # Determine severity
        severity = self._determine_severity(avg_probability)
        
        # Calculate feature contributions
        feature_contributions = self._calculate_feature_contributions(features_scaled[0])
        
        # Generate recommended actions
        recommended_actions = self._generate_recommendations(anomaly_type, severity)
        
        # Estimate time to failure
        ttf = self._estimate_time_to_failure(telemetry_sequence, anomaly_type)
        
        prediction = AnomalyPrediction(
            timestamp=datetime.now().isoformat(),
            anomaly_type=anomaly_type.value,
            severity=severity.value,
            probability=float(avg_probability),
            confidence=float(np.std(list(predictions.values())) if len(predictions) > 1 else 0.5),
            predicted_time_to_failure=ttf,
            affected_systems=self._get_affected_systems(anomaly_type),
            recommended_actions=recommended_actions,
            feature_contributions=feature_contributions
        )
        
        # Store in history
        self.anomaly_history.append(prediction)
        
        return prediction

    def _create_normal_prediction(self) -> AnomalyPrediction:
        """Create normal (no anomaly) prediction"""
        return AnomalyPrediction(
            timestamp=datetime.now().isoformat(),
            anomaly_type=AnomalyType.UNKNOWN.value,
            severity=AnomalySeverity.NORMAL.value,
            probability=0.0,
            confidence=1.0,
            predicted_time_to_failure=None,
            affected_systems=[],
            recommended_actions=["Continue normal operation"],
            feature_contributions={}
        )

    def _determine_severity(self, probability: float) -> AnomalySeverity:
        """Determine severity from probability"""
        if probability < 0.2:
            return AnomalySeverity.NORMAL
        elif probability < 0.4:
            return AnomalySeverity.MONITOR
        elif probability < 0.6:
            return AnomalySeverity.WARNING
        elif probability < 0.8:
            return AnomalySeverity.CRITICAL
        else:
            return AnomalySeverity.EMERGENCY

    def _calculate_feature_contributions(self, features: np.ndarray) -> Dict[str, float]:
        """Calculate feature contributions to anomaly"""
        if not self.feature_extractor.baseline_stats:
            return {}
        
        baseline_mean = np.array(self.feature_extractor.baseline_stats['mean'])
        baseline_std = np.array(self.feature_extractor.baseline_stats['std'])
        
        # Z-score based contribution
        z_scores = np.abs((features - baseline_mean) / (baseline_std + 1e-6))
        
        contributions = {}
        for i, (name, z) in enumerate(zip(self.feature_extractor.feature_names, z_scores)):
            if z > 2:  # Only include significant contributions
                contributions[name] = float(z)
        
        # Sort by contribution
        sorted_contrib = dict(sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return sorted_contrib

    def _generate_recommendations(self, anomaly_type: AnomalyType, 
                                  severity: AnomalySeverity) -> List[str]:
        """Generate recommended actions"""
        recommendations = {
            AnomalyType.MOTOR_DEGRADATION: [
                "Reduce throttle to decrease motor stress",
                "Monitor motor temperature closely",
                "Prepare for early landing if degradation continues"
            ],
            AnomalyType.BATTERY_FAILURE: [
                "Initiate immediate return to home",
                "Reduce power consumption",
                "Prepare for emergency landing"
            ],
            AnomalyType.SENSOR_DRIFT: [
                "Cross-check with redundant sensors",
                "Switch to backup sensor if available",
                "Recalibrate sensors when possible"
            ],
            AnomalyType.CONTROL_INSTABILITY: [
                "Switch to stabilized flight mode",
                "Reduce control sensitivity",
                "Check for external disturbances"
            ],
            AnomalyType.STRUCTURAL_STRESS: [
                "Reduce flight intensity immediately",
                "Avoid aggressive maneuvers",
                "Land and inspect airframe"
            ],
            AnomalyType.COMMUNICATION_LOSS: [
                "Activate return-to-home failsafe",
                "Check antenna connections",
                "Increase transmission power if possible"
            ],
            AnomalyType.GPS_ANOMALY: [
                "Switch to attitude mode",
                "Use visual navigation if available",
                "Wait for GPS signal recovery"
            ],
            AnomalyType.ENVIRONMENTAL: [
                "Assess weather conditions",
                "Consider aborting mission",
                "Find shelter or land immediately"
            ]
        }
        
        base_recommendations = recommendations.get(anomaly_type, ["Monitor situation closely"])
        
        # Add severity-based recommendations
        if severity == AnomalySeverity.EMERGENCY:
            base_recommendations.insert(0, "EMERGENCY: Initiate emergency procedures immediately")
        elif severity == AnomalySeverity.CRITICAL:
            base_recommendations.insert(0, "CRITICAL: Take immediate corrective action")
        
        return base_recommendations

    def _get_affected_systems(self, anomaly_type: AnomalyType) -> List[str]:
        """Get list of affected systems"""
        system_map = {
            AnomalyType.MOTOR_DEGRADATION: ["propulsion", "power"],
            AnomalyType.BATTERY_FAILURE: ["power", "avionics"],
            AnomalyType.SENSOR_DRIFT: ["sensors", "navigation"],
            AnomalyType.CONTROL_INSTABILITY: ["control", "navigation"],
            AnomalyType.STRUCTURAL_STRESS: ["airframe", "control"],
            AnomalyType.COMMUNICATION_LOSS: ["communication", "telemetry"],
            AnomalyType.GPS_ANOMALY: ["navigation", "gps"],
            AnomalyType.ENVIRONMENTAL: ["all"]
        }
        return system_map.get(anomaly_type, ["unknown"])

    def _estimate_time_to_failure(self, sequence: List[Dict], 
                                  anomaly_type: AnomalyType) -> Optional[float]:
        """Estimate time to failure based on trend"""
        if len(sequence) < 10:
            return None
        
        # Get relevant metric based on anomaly type
        metric_map = {
            AnomalyType.MOTOR_DEGRADATION: 'motor_rpm',
            AnomalyType.BATTERY_FAILURE: 'battery_voltage',
            AnomalyType.SENSOR_DRIFT: 'temperature',
            AnomalyType.CONTROL_INSTABILITY: 'roll',
            AnomalyType.STRUCTURAL_STRESS: 'acceleration',
            AnomalyType.COMMUNICATION_LOSS: 'rssi',
            AnomalyType.GPS_ANOMALY: 'satellites',
            AnomalyType.ENVIRONMENTAL: 'wind_speed'
        }
        
        metric = metric_map.get(anomaly_type)
        if not metric:
            return None
        
        values = np.array([t.get(metric, 0) for t in sequence])
        
        # Calculate trend
        if len(values) >= 5:
            trend = np.polyfit(np.arange(len(values)), values, 1)[0]
            
            if abs(trend) > 0.01:
                # Estimate time to threshold
                current = values[-1]
                threshold = values[0] * 0.7  # 30% degradation threshold
                
                if trend < 0:  # Decreasing trend
                    ttf = (current - threshold) / abs(trend)
                    return max(0, min(ttf * 10, 3600))  # Cap at 1 hour
        
        return None

    def get_anomaly_report(self, window_hours: float = 1) -> AnomalyReport:
        """Generate anomaly report"""
        now = datetime.now()
        window_start = now - timedelta(hours=window_hours)
        
        # Filter recent predictions
        recent = [
            p for p in self.anomaly_history
            if datetime.fromisoformat(p.timestamp) >= window_start
        ]
        
        # Count anomalies
        anomalies = [p for p in recent if p.severity != AnomalySeverity.NORMAL.value]
        
        # Calculate system health score
        if recent:
            severity_scores = {
                AnomalySeverity.NORMAL.value: 1.0,
                AnomalySeverity.MONITOR.value: 0.8,
                AnomalySeverity.WARNING.value: 0.5,
                AnomalySeverity.CRITICAL.value: 0.2,
                AnomalySeverity.EMERGENCY.value: 0.0
            }
            health_score = np.mean([severity_scores.get(p.severity, 0.5) for p in recent])
        else:
            health_score = 1.0
        
        # Generate recommendations
        recommendations = self._generate_system_recommendations(anomalies)
        
        report = AnomalyReport(
            report_id=f"anomaly_report_{now.strftime('%Y%m%d_%H%M%S')}",
            generated_at=now.isoformat(),
            total_samples_analyzed=len(recent),
            anomalies_detected=len(anomalies),
            anomaly_rate=len(anomalies) / max(len(recent), 1),
            predictions=recent[-20:],  # Last 20 predictions
            system_health_score=health_score,
            recommendations=recommendations
        )
        
        return report

    def _generate_system_recommendations(self, anomalies: List[AnomalyPrediction]) -> List[str]:
        """Generate system-level recommendations"""
        if not anomalies:
            return ["System operating normally", "Continue regular monitoring"]
        
        recommendations = []
        
        # Count anomaly types
        type_counts = {}
        severity_counts = {}
        for a in anomalies:
            type_counts[a.anomaly_type] = type_counts.get(a.anomaly_type, 0) + 1
            severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
        
        # Most common anomaly
        if type_counts:
            most_common = max(type_counts.items(), key=lambda x: x[1])
            recommendations.append(f"Most frequent issue: {most_common[0]} ({most_common[1]} occurrences)")
        
        # Severity summary
        if severity_counts.get(AnomalySeverity.EMERGENCY.value, 0) > 0:
            recommendations.append("URGENT: Emergency conditions detected - immediate action required")
        elif severity_counts.get(AnomalySeverity.CRITICAL.value, 0) > 2:
            recommendations.append("Multiple critical conditions - consider mission abort")
        elif severity_counts.get(AnomalySeverity.WARNING.value, 0) > 5:
            recommendations.append("Frequent warnings - schedule maintenance check")
        
        return recommendations


# Convenience function
def create_anomaly_predictor(config: Optional[Dict] = None) -> AnomalyPredictor:
    """Create and return an Anomaly Predictor instance"""
    return AnomalyPredictor(config)


__all__ = [
    'AnomalyPredictor',
    'create_anomaly_predictor',
    'AnomalyFeatureExtractor',
    'AnomalyPrediction',
    'AnomalyReport',
    'AnomalyType',
    'AnomalySeverity'
]
