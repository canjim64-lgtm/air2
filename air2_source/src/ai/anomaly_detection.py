"""
AirOne v4.0 - Advanced Anomaly Detection
Autoencoder, Isolation Forest, and ensemble-based anomaly detection
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import logging
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.svm import OneClassSVM
    from sklearn.covariance import EllipticEnvelope
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.cluster import DBSCAN
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available")


class AnomalyMethod(Enum):
    """Anomaly detection methods"""
    ISOLATION_FOREST = "isolation_forest"
    AUTOENCODER = "autoencoder"
    LOCAL_OUTLIER_FACTOR = "lof"
    ONE_CLASS_SVM = "ocsvm"
    ELLIPTIC_ENVELOPE = "elliptic"
    PCA_BASED = "pca"
    DBSCAN = "dbscan"
    ENSEMBLE = "ensemble"
    STATISTICAL = "statistical"


class AnomalySeverity(Enum):
    """Anomaly severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyResult:
    """Anomaly detection result"""
    is_anomaly: bool
    anomaly_score: float
    severity: str
    method: str
    confidence: float
    feature_contributions: Optional[Dict[str, float]] = None
    timestamp: str = ""


@dataclass
class AnomalyReport:
    """Comprehensive anomaly report"""
    total_samples: int
    anomalies_detected: int
    anomaly_rate: float
    method: str
    threshold: float
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    anomalies: List[AnomalyResult]
    statistics: Dict[str, Any]


class AutoencoderAnomalyDetector:
    """
    Autoencoder-based anomaly detection
    
    Uses reconstruction error to identify anomalies
    """

    def __init__(self, input_dim: int, config: Optional[Dict] = None):
        self.input_dim = input_dim
        self.config = config or {}
        
        # Architecture config
        self.encoding_dim = self.config.get('encoding_dim', max(8, input_dim // 4))
        self.hidden_layers = self.config.get('hidden_layers', [64, 32])
        self.dropout_rate = self.config.get('dropout_rate', 0.2)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = None
        self.is_trained = False
        self.normal_reconstruction_errors = []

    def build_model(self) -> Optional[keras.Model]:
        """Build autoencoder model"""
        if not TENSORFLOW_AVAILABLE:
            logger.error("TensorFlow required for autoencoder")
            return None
        
        # Encoder
        inputs = layers.Input(shape=(self.input_dim,))
        x = inputs
        
        # Encoding layers
        for units in self.hidden_layers:
            x = layers.Dense(units, activation='relu')(x)
            x = layers.Dropout(self.dropout_rate)(x)
            x = layers.BatchNormalization()(x)
        
        # Bottleneck
        x = layers.Dense(self.encoding_dim, activation='relu')(x)
        
        # Decoding layers
        for units in reversed(self.hidden_layers):
            x = layers.Dense(units, activation='relu')(x)
            x = layers.Dropout(self.dropout_rate)(x)
            x = layers.BatchNormalization()(x)
        
        # Output
        outputs = layers.Dense(self.input_dim, activation='linear')(x)
        
        model = keras.Model(inputs=inputs, outputs=outputs)
        
        # Compile
        optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
        model.compile(optimizer=optimizer, loss='mse')
        
        return model

    def fit(self, X: np.ndarray, epochs: int = 100, 
            batch_size: int = 32, validation_split: float = 0.1,
            threshold_percentile: float = 95) -> Dict[str, Any]:
        """
        Train autoencoder on normal data
        
        Args:
            X: Normal training data
            epochs: Training epochs
            batch_size: Batch size
            validation_split: Validation data ratio
            threshold_percentile: Percentile for anomaly threshold
            
        Returns:
            Training results
        """
        if not TENSORFLOW_AVAILABLE:
            return {'error': 'TensorFlow not available'}
        
        # Scale data
        X_scaled = self.scaler.fit_transform(X)
        
        # Build model
        self.model = self.build_model()
        if self.model is None:
            return {'error': 'Model build failed'}
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True
        )
        
        # Train
        history = self.model.fit(
            X_scaled, X_scaled,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=0
        )
        
        # Calculate reconstruction errors on training data
        X_pred = self.model.predict(X_scaled, verbose=0)
        reconstruction_errors = np.mean(np.square(X_scaled - X_pred), axis=1)
        self.normal_reconstruction_errors = reconstruction_errors.tolist()
        
        # Set threshold
        self.threshold = np.percentile(reconstruction_errors, threshold_percentile)
        
        self.is_trained = True
        
        return {
            'status': 'trained',
            'threshold': float(self.threshold),
            'mean_error': float(np.mean(reconstruction_errors)),
            'std_error': float(np.std(reconstruction_errors)),
            'epochs_trained': len(history.history['loss'])
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomalies
        
        Returns:
            Array of 1 (anomaly) or 0 (normal)
        """
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        X_pred = self.model.predict(X_scaled, verbose=0)
        
        reconstruction_errors = np.mean(np.square(X_scaled - X_pred), axis=1)
        predictions = (reconstruction_errors > self.threshold).astype(int)
        
        return predictions

    def get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """Get continuous anomaly scores"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        X_pred = self.model.predict(X_scaled, verbose=0)
        
        reconstruction_errors = np.mean(np.square(X_scaled - X_pred), axis=1)
        
        # Normalize scores to 0-1 range
        if self.threshold > 0:
            normalized_scores = reconstruction_errors / (self.threshold * 2)
            normalized_scores = np.clip(normalized_scores, 0, 1)
        else:
            normalized_scores = reconstruction_errors
        
        return normalized_scores

    def explain_anomaly(self, X: np.ndarray, anomaly_idx: int) -> Dict[str, Any]:
        """Explain why a sample was flagged as anomaly"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X[anomaly_idx:anomaly_idx+1])
        X_pred = self.model.predict(X_scaled, verbose=0)
        
        # Calculate per-feature reconstruction error
        feature_errors = np.square(X_scaled[0] - X_pred[0])
        
        # Rank features by contribution to anomaly
        feature_ranking = np.argsort(feature_errors)[::-1]
        
        return {
            'reconstruction_error': float(np.mean(feature_errors)),
            'threshold': float(self.threshold),
            'is_anomaly': bool(np.mean(feature_errors) > self.threshold),
            'feature_contributions': {
                f'feature_{i}': float(feature_errors[i])
                for i in feature_ranking[:5]  # Top 5 contributing features
            }
        }


class IsolationForestDetector:
    """
    Isolation Forest-based anomaly detection
    """

    def __init__(self, contamination: float = 0.1, config: Optional[Dict] = None):
        self.contamination = contamination
        self.config = config or {}
        
        self.model = IsolationForest(
            n_estimators=self.config.get('n_estimators', 100),
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False

    def fit(self, X: np.ndarray) -> Dict[str, Any]:
        """Fit isolation forest"""
        if not SKLEARN_AVAILABLE:
            return {'error': 'scikit-learn not available'}
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        
        return {'status': 'trained', 'n_estimators': self.model.n_estimators}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies (-1 for anomaly, 1 for normal)"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """Get anomaly scores (more negative = more anomalous)"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        scores = self.model.decision_function(X_scaled)
        
        # Convert to 0-1 range (higher = more anomalous)
        normalized = -scores
        normalized = (normalized - normalized.min()) / (normalized.max() - normalized.min() + 1e-10)
        
        return normalized


class LOFDetector:
    """
    Local Outlier Factor-based anomaly detection
    """

    def __init__(self, n_neighbors: int = 20, contamination: float = 0.1):
        self.n_neighbors = n_neighbors
        self.contamination = contamination
        
        self.model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            novelty=True,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False

    def fit(self, X: np.ndarray) -> Dict[str, Any]:
        """Fit LOF model"""
        if not SKLEARN_AVAILABLE:
            return {'error': 'scikit-learn not available'}
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        
        return {'status': 'trained', 'n_neighbors': self.n_neighbors}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """Get LOF scores"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X)
        scores = -self.model.score_samples(X_scaled)  # Negate so higher = more anomalous
        
        # Normalize to 0-1
        normalized = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
        
        return normalized


class EnsembleAnomalyDetector:
    """
    Ensemble of multiple anomaly detection methods
    """

    def __init__(self, methods: List[str] = None, config: Optional[Dict] = None):
        self.methods = methods or ['isolation_forest', 'autoencoder', 'lof']
        self.config = config or {}
        self.detectors = {}
        self.weights = {}
        self.is_trained = False
        self.threshold = 0.5

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Fit ensemble of detectors"""
        results = {}
        
        for method in self.methods:
            try:
                if method == 'isolation_forest':
                    detector = IsolationForestDetector(
                        contamination=self.config.get('contamination', 0.1)
                    )
                    result = detector.fit(X)
                
                elif method == 'autoencoder' and TENSORFLOW_AVAILABLE:
                    detector = AutoencoderAnomalyDetector(
                        X.shape[1],
                        self.config.get('autoencoder', {})
                    )
                    result = detector.fit(X)
                
                elif method == 'lof':
                    detector = LOFDetector(
                        contamination=self.config.get('contamination', 0.1)
                    )
                    result = detector.fit(X)
                
                else:
                    continue
                
                self.detectors[method] = detector
                results[method] = result
                
            except Exception as e:
                logger.warning(f"Failed to fit {method}: {e}")
        
        # Set equal weights
        n_detectors = len(self.detectors)
        self.weights = {m: 1.0 / n_detectors for m in self.detectors}
        self.is_trained = True
        
        # Calibrate threshold if labels available
        if y is not None:
            self._calibrate_threshold(X, y)
        
        return results

    def _calibrate_threshold(self, X: np.ndarray, y: np.ndarray):
        """Calibrate decision threshold using labeled data"""
        scores = self.get_anomaly_scores(X)
        
        best_threshold = 0.5
        best_f1 = 0
        
        for threshold in np.arange(0.1, 0.9, 0.05):
            predictions = (scores >= threshold).astype(int)
            try:
                f1 = f1_score(y, predictions)
                if f1 > best_f1:
                    best_f1 = f1
                    best_threshold = threshold
            except:
                continue
        
        self.threshold = best_threshold
        logger.info(f"Calibrated threshold: {best_threshold:.2f} (F1: {best_f1:.3f})")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies using voting"""
        if not self.is_trained:
            raise ValueError("Ensemble not trained")
        
        scores = self.get_anomaly_scores(X)
        return (scores >= self.threshold).astype(int)

    def get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """Get ensemble anomaly scores"""
        if not self.is_trained:
            raise ValueError("Ensemble not trained")
        
        all_scores = []
        for method, detector in self.detectors.items():
            scores = detector.get_anomaly_scores(X)
            all_scores.append(scores * self.weights[method])
        
        ensemble_scores = np.sum(all_scores, axis=0)
        
        return ensemble_scores

    def get_method_scores(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Get scores from each method"""
        if not self.is_trained:
            return {}
        
        return {
            method: detector.get_anomaly_scores(X)
            for method, detector in self.detectors.items()
        }


class StatisticalAnomalyDetector:
    """
    Statistical anomaly detection methods
    """

    def __init__(self, method: str = 'zscore', threshold: float = 3.0):
        self.method = method
        self.threshold = threshold
        self.stats = {}
        self.is_trained = False

    def fit(self, X: np.ndarray) -> Dict[str, Any]:
        """Fit statistical model"""
        if self.method == 'zscore':
            self.stats['mean'] = np.mean(X, axis=0)
            self.stats['std'] = np.std(X, axis=0)
        elif self.method == 'mad':
            self.stats['median'] = np.median(X, axis=0)
            self.stats['mad'] = np.median(np.abs(X - np.median(X, axis=0)), axis=0)
        elif self.method == 'iqr':
            self.stats['q1'] = np.percentile(X, 25, axis=0)
            self.stats['q3'] = np.percentile(X, 75, axis=0)
            self.stats['iqr'] = self.stats['q3'] - self.stats['q1']
        
        self.is_trained = True
        return {'status': 'trained', 'method': self.method}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict anomalies"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        if self.method == 'zscore':
            z_scores = np.abs((X - self.stats['mean']) / (self.stats['std'] + 1e-10))
            return (np.max(z_scores, axis=1) > self.threshold).astype(int)
        
        elif self.method == 'mad':
            mad_scores = np.abs((X - self.stats['median']) / (self.stats['mad'] + 1e-10))
            return (np.max(mad_scores, axis=1) > self.threshold).astype(int)
        
        elif self.method == 'iqr':
            lower = self.stats['q1'] - self.threshold * self.stats['iqr']
            upper = self.stats['q3'] + self.threshold * self.stats['iqr']
            is_anomaly = np.any((X < lower) | (X > upper), axis=1)
            return is_anomaly.astype(int)
        
        return np.zeros(len(X))

    def get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """Get anomaly scores"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        if self.method == 'zscore':
            z_scores = np.abs((X - self.stats['mean']) / (self.stats['std'] + 1e-10))
            return np.max(z_scores, axis=1) / self.threshold
        
        elif self.method == 'mad':
            mad_scores = np.abs((X - self.stats['median']) / (self.stats['mad'] + 1e-10))
            return np.max(mad_scores, axis=1) / self.threshold
        
        elif self.method == 'iqr':
            lower = self.stats['q1'] - self.threshold * self.stats['iqr']
            upper = self.stats['q3'] + self.threshold * self.stats['iqr']
            distances = np.maximum(lower - X, X - upper, 0)
            return np.max(distances, axis=1) / (self.stats['iqr'] + 1e-10)
        
        return np.zeros(len(X))


class AirOneAnomalyDetection:
    """
    High-level anomaly detection interface for AirOne
    """

    def __init__(self, method: str = 'ensemble'):
        self.method = method
        self.detector = None
        self.is_trained = False
        self.feature_names = []

    def fit(self, X: np.ndarray, feature_names: Optional[List[str]] = None,
            y: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Fit anomaly detector
        
        Args:
            X: Training data (should be normal data)
            feature_names: Optional feature names
            y: Optional labels for threshold calibration
            
        Returns:
            Fitting results
        """
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        
        if self.method == 'ensemble':
            self.detector = EnsembleAnomalyDetector()
        elif self.method == 'autoencoder':
            self.detector = AutoencoderAnomalyDetector(X.shape[1])
        elif self.method == 'isolation_forest':
            self.detector = IsolationForestDetector()
        elif self.method == 'lof':
            self.detector = LOFDetector()
        elif self.method == 'statistical':
            self.detector = StatisticalAnomalyDetector()
        else:
            self.detector = EnsembleAnomalyDetector()
        
        result = self.detector.fit(X, y)
        self.is_trained = True
        
        return result

    def detect(self, X: np.ndarray, 
               return_scores: bool = True) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Detect anomalies
        
        Args:
            X: Data to check
            return_scores: Whether to return anomaly scores
            
        Returns:
            Predictions and optionally scores
        """
        if not self.is_trained:
            raise ValueError("Detector not trained")
        
        predictions = self.detector.predict(X)
        
        if return_scores:
            scores = self.detector.get_anomaly_scores(X)
            return predictions, scores
        
        return predictions

    def generate_report(self, X: np.ndarray, 
                       y_true: Optional[np.ndarray] = None) -> AnomalyReport:
        """
        Generate comprehensive anomaly report
        
        Args:
            X: Data to analyze
            y_true: Optional true labels for evaluation
            
        Returns:
            AnomalyReport
        """
        predictions, scores = self.detect(X, return_scores=True)
        
        n_anomalies = np.sum(predictions)
        anomaly_rate = n_anomalies / len(X)
        
        # Calculate metrics if labels available
        precision, recall, f1 = None, None, None
        if y_true is not None:
            try:
                precision = precision_score(y_true, predictions, zero_division=0)
                recall = recall_score(y_true, predictions, zero_division=0)
                f1 = f1_score(y_true, predictions, zero_division=0)
            except:
                pass
        
        # Create anomaly results
        anomalies = []
        for i in range(len(X)):
            if predictions[i] == 1:
                severity = self._classify_severity(scores[i])
                anomalies.append(AnomalyResult(
                    is_anomaly=True,
                    anomaly_score=float(scores[i]),
                    severity=severity.value,
                    method=self.method,
                    confidence=float(scores[i]),
                    timestamp=datetime.now().isoformat()
                ))
        
        return AnomalyReport(
            total_samples=len(X),
            anomalies_detected=int(n_anomalies),
            anomaly_rate=float(anomaly_rate),
            method=self.method,
            threshold=getattr(self.detector, 'threshold', 0.5),
            precision=precision,
            recall=recall,
            f1_score=f1,
            anomalies=anomalies,
            statistics={
                'score_mean': float(np.mean(scores)),
                'score_std': float(np.std(scores)),
                'score_max': float(np.max(scores)),
                'score_min': float(np.min(scores))
            }
        )

    def _classify_severity(self, score: float) -> AnomalySeverity:
        """Classify anomaly severity based on score"""
        if score >= 0.8:
            return AnomalySeverity.CRITICAL
        elif score >= 0.6:
            return AnomalySeverity.HIGH
        elif score >= 0.4:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW


__all__ = [
    'AutoencoderAnomalyDetector',
    'IsolationForestDetector',
    'LOFDetector',
    'EnsembleAnomalyDetector',
    'StatisticalAnomalyDetector',
    'AirOneAnomalyDetection',
    'AnomalyResult',
    'AnomalyReport',
    'AnomalyMethod',
    'AnomalySeverity'
]
