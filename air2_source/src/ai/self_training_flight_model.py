"""
AirOne v4.0 - Autonomous Self-Training Flight Model
Continuously learns from flight simulation data and improves predictions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import pickle
import os
import logging
import time
from dataclasses import dataclass, asdict
from collections import deque
import threading
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import sklearn with fallbacks
try:
    from sklearn.ensemble import (
        RandomForestRegressor, GradientBoostingRegressor, 
        ExtraTreesRegressor, AdaBoostRegressor
    )
    from sklearn.neural_network import MLPRegressor
    from sklearn.linear_model import Ridge, BayesianRidge
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    from sklearn.pipeline import Pipeline
    from sklearn.multioutput import MultiOutputRegressor
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


class TrainingMode(Enum):
    """Training modes for the flight model"""
    ONLINE = "online"  # Continuous real-time training
    BATCH = "batch"    # Periodic batch training
    INCREMENTAL = "incremental"  # Incremental updates
    TRANSFER = "transfer"  # Transfer learning from pre-trained


@dataclass
class FlightModelState:
    """State of the flight model"""
    timestamp: str
    total_samples: int
    training_iterations: int
    model_version: int
    accuracy_score: float
    prediction_error: float
    last_training_time: str
    next_training_trigger: str
    performance_trend: str  # improving, stable, degrading
    active_features: List[str]


@dataclass
class TrainingMetrics:
    """Training performance metrics"""
    training_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    samples_used: int
    validation_score: float
    test_score: float
    improvement: float
    model_changed: bool


class FlightDataBuffer:
    """
    Circular buffer for flight data storage
    Maintains recent flight data for continuous training
    """

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.telemetry_buffer = deque(maxlen=max_size)
        self.label_buffer = deque(maxlen=max_size)
        self.metadata_buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def add(self, telemetry: Dict[str, Any], labels: Optional[Dict] = None,
            metadata: Optional[Dict] = None):
        """Add flight data to buffer"""
        with self.lock:
            self.telemetry_buffer.append(telemetry)
            if labels:
                self.label_buffer.append(labels)
            if metadata:
                self.metadata_buffer.append(metadata or {})

    def add_batch(self, telemetry_list: List[Dict], 
                  labels_list: Optional[List[Dict]] = None):
        """Add batch of flight data"""
        with self.lock:
            for i, telemetry in enumerate(telemetry_list):
                self.telemetry_buffer.append(telemetry)
                if labels_list and i < len(labels_list):
                    self.label_buffer.append(labels_list[i])
                else:
                    self.label_buffer.append({})

    def get_recent(self, n: int) -> Tuple[List[Dict], List[Dict]]:
        """Get recent n samples"""
        with self.lock:
            telemetry = list(self.telemetry_buffer)[-n:]
            labels = list(self.label_buffer)[-n:]
            return telemetry, labels

    def get_all(self) -> Tuple[List[Dict], List[Dict]]:
        """Get all buffered data"""
        with self.lock:
            return list(self.telemetry_buffer), list(self.label_buffer)

    def size(self) -> int:
        """Get buffer size"""
        return len(self.telemetry_buffer)

    def clear(self):
        """Clear buffer"""
        with self.lock:
            self.telemetry_buffer.clear()
            self.label_buffer.clear()
            self.metadata_buffer.clear()

    def to_dataframe(self) -> pd.DataFrame:
        """Convert buffer to DataFrame"""
        with self.lock:
            if len(self.telemetry_buffer) == 0:
                return pd.DataFrame()
            return pd.DataFrame(list(self.telemetry_buffer))


class FlightFeatureExtractor:
    """
    Extracts and engineers features from raw flight telemetry
    """

    def __init__(self):
        self.feature_names = []
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_stats = {}

    def extract_features(self, telemetry: Union[Dict, List[Dict]], 
                        include_derived: bool = True) -> np.ndarray:
        """
        Extract features from telemetry data
        
        Args:
            telemetry: Single record or list of records
            include_derived: Include engineered features
            
        Returns:
            Feature array
        """
        if isinstance(telemetry, dict):
            telemetry = [telemetry]
        
        base_features = [
            'altitude', 'velocity', 'acceleration', 'pitch', 'roll', 'yaw',
            'throttle', 'battery_voltage', 'battery_current', 'motor_rpm',
            'temperature', 'pressure', 'gps_latitude', 'gps_longitude',
            'gps_altitude', 'ground_speed', 'air_speed', 'climb_rate'
        ]
        
        features_list = []
        for record in telemetry:
            features = []
            for feat in base_features:
                val = record.get(feat, 0)
                if isinstance(val, (int, float)):
                    features.append(float(val))
                else:
                    features.append(0.0)
            
            if include_derived:
                # Add derived features
                derived = self._compute_derived_features(record, features)
                features.extend(derived)
            
            features_list.append(features)
        
        if not self.feature_names:
            self.feature_names = base_features.copy()
            if include_derived:
                self.feature_names.extend([
                    'energy', 'load_factor', 'efficiency', 'power_consumption',
                    'altitude_rate', 'velocity_normalized', 'battery_percentage'
                ])
        
        return np.array(features_list)

    def _compute_derived_features(self, record: Dict, base_features: List) -> List[float]:
        """Compute derived features from raw telemetry"""
        derived = []
        
        # Energy estimation
        altitude = record.get('altitude', 0)
        velocity = record.get('velocity', 0)
        mass = record.get('mass', 1.5)  # Default 1.5kg
        gravity = 9.81
        potential_energy = mass * gravity * altitude
        kinetic_energy = 0.5 * mass * velocity ** 2
        derived.append(potential_energy + kinetic_energy)  # Total energy
        
        # Load factor
        acceleration = record.get('acceleration', 0)
        load_factor = acceleration / gravity if gravity != 0 else 0
        derived.append(load_factor)
        
        # Efficiency
        throttle = record.get('throttle', 0)
        efficiency = velocity / throttle if throttle > 0 else 0
        derived.append(efficiency)
        
        # Power consumption
        voltage = record.get('battery_voltage', 0)
        current = record.get('battery_current', 0)
        derived.append(voltage * current)  # Power in Watts
        
        # Altitude rate
        altitude_rate = record.get('climb_rate', 0)
        derived.append(altitude_rate)
        
        # Normalized velocity
        max_velocity = record.get('max_velocity', 50)
        derived.append(velocity / max_velocity if max_velocity > 0 else 0)
        
        # Battery percentage
        battery_percentage = record.get('battery_percentage', 100)
        derived.append(battery_percentage / 100)
        
        return derived

    def fit_scaler(self, X: np.ndarray):
        """Fit feature scaler"""
        self.scaler.fit(X)
        self.is_fitted = True
        
        # Store feature statistics
        self.feature_stats = {
            'mean': self.scaler.mean_.tolist(),
            'std': self.scaler.scale_.tolist(),
            'min': X.min(axis=0).tolist(),
            'max': X.max(axis=0).tolist()
        }

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform features"""
        if not self.is_fitted:
            self.fit_scaler(X)
        return self.scaler.transform(X)

    def get_feature_importance_summary(self, importances: np.ndarray) -> Dict[str, float]:
        """Get feature importance summary"""
        if len(self.feature_names) != len(importances):
            return {}
        
        importance_dict = dict(zip(self.feature_names, importances))
        sorted_importance = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'ranked_features': sorted_importance,
            'top_5': sorted_importance[:5],
            'bottom_5': sorted_importance[-5:]
        }


class SelfTrainingFlightModel:
    """
    Autonomous self-training flight prediction model
    
    Continuously learns from flight simulation data and improves
    predictions for altitude, velocity, battery, and trajectory
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Model configuration
        self.model_type = self.config.get('model_type', 'ensemble')
        self.training_mode = TrainingMode(self.config.get('training_mode', 'online'))
        self.prediction_targets = self.config.get('prediction_targets', 
                                                   ['altitude', 'velocity', 'battery_percentage'])
        
        # Training configuration
        self.min_samples_for_training = self.config.get('min_samples', 100)
        self.training_interval_seconds = self.config.get('training_interval', 60)
        self.validation_split = self.config.get('validation_split', 0.2)
        self.retrain_threshold = self.config.get('retrain_threshold', 0.05)  # 5% degradation
        
        # Data buffer
        self.buffer = FlightDataBuffer(max_size=self.config.get('buffer_size', 10000))
        
        # Feature extractor
        self.feature_extractor = FlightFeatureExtractor()
        
        # Models
        self.models: Dict[str, Any] = {}
        self.model_version = 0
        self.training_history: List[TrainingMetrics] = []
        
        # Performance tracking
        self.performance_window = deque(maxlen=100)
        self.last_training_time = None
        self.training_lock = threading.Lock()
        
        # State
        self.is_initialized = False
        self.is_training = False
        self.state = None
        
        logger.info("Self-Training Flight Model initialized")

    def initialize(self, initial_data: Optional[List[Dict]] = None):
        """
        Initialize the model with optional initial data
        
        Args:
            initial_data: Initial flight data for warm start
        """
        logger.info("Initializing Self-Training Flight Model...")
        
        if initial_data:
            logger.info(f"Loading {len(initial_data)} initial samples...")
            self.buffer.add_batch(initial_data)
            
            # Initial training if enough data
            if len(initial_data) >= self.min_samples_for_training:
                self._train_initial_model()
        
        self.is_initialized = True
        self._update_state()
        
        logger.info("✅ Self-Training Flight Model ready")

    def _train_initial_model(self):
        """Train initial model from buffered data"""
        logger.info("Training initial model...")
        
        telemetry, labels = self.buffer.get_all()
        
        if len(telemetry) < self.min_samples_for_training:
            logger.warning("Insufficient data for initial training")
            return
        
        # Extract features
        X = self.feature_extractor.extract_features(telemetry)
        
        # Create labels from telemetry if not provided
        y_data = {}
        for target in self.prediction_targets:
            y_data[target] = np.array([t.get(target, 0) for t in telemetry])
        
        # Train models for each target
        for target in self.prediction_targets:
            self._train_target_model(target, X, y_data[target])
        
        self.model_version = 1
        self.last_training_time = datetime.now()
        
        logger.info(f"✅ Initial model trained (version {self.model_version})")

    def _train_target_model(self, target: str, X: np.ndarray, y: np.ndarray):
        """Train model for a specific prediction target"""
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn required for training")
            return
        
        # Scale features
        X_scaled = self.feature_extractor.transform(X)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=self.validation_split, random_state=42
        )
        
        # Create model based on type
        if self.model_type == 'ensemble':
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
            n_jobs=-1,
                random_state=42
            )
        elif self.model_type == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'neural_network':
            model = MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                max_iter=500,
                early_stopping=True,
                random_state=42
            )
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Train
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_val)
        val_score = r2_score(y_val, y_pred)
        
        self.models[target] = {
            'model': model,
            'r2_score': val_score,
            'trained_at': datetime.now().isoformat()
        }
        
        logger.info(f"  {target}: R² = {val_score:.4f}")

    def ingest_flight_data(self, telemetry: Dict[str, Any], 
                          generate_labels: bool = True):
        """
        Ingest new flight data for training
        
        Args:
            telemetry: Flight telemetry record
            generate_labels: Auto-generate training labels
        """
        if not self.is_initialized:
            self.initialize()
        
        # Add to buffer
        if generate_labels:
            # Use current telemetry as labels for next prediction
            self.buffer.add(telemetry, labels=telemetry.copy())
        else:
            self.buffer.add(telemetry)
        
        # Check if training should be triggered
        if self._should_train():
            self.trigger_training()

    def _should_train(self) -> bool:
        """Check if training should be triggered"""
        # Check sample count
        if self.buffer.size() < self.min_samples_for_training:
            return False
        
        # Check time interval
        if self.last_training_time:
            elapsed = (datetime.now() - self.last_training_time).total_seconds()
            if elapsed < self.training_interval_seconds:
                return False
        
        # Check performance degradation
        if len(self.performance_window) >= 10:
            recent_perf = list(self.performance_window)[-5:]
            older_perf = list(self.performance_window)[:5]
            
            if np.mean(recent_perf) < np.mean(older_perf) - self.retrain_threshold:
                logger.info("Performance degradation detected, triggering training")
                return True
        
        return True

    def trigger_training(self) -> Optional[TrainingMetrics]:
        """
        Trigger model training
        
        Returns:
            Training metrics if training completed
        """
        if self.is_training:
            logger.info("Training already in progress")
            return None
        
        with self.training_lock:
            self.is_training = True
            start_time = time.time()
            
            try:
                metrics = self._perform_training()
                
                duration = time.time() - start_time
                metrics.end_time = datetime.now().isoformat()
                metrics.duration_seconds = duration
                
                self.training_history.append(metrics)
                self.last_training_time = datetime.now()
                
                logger.info(f"✅ Training completed in {duration:.2f}s")
                
                return metrics
                
            except Exception as e:
                logger.error(f"Training failed: {e}")
                return None
            finally:
                self.is_training = False

    def _perform_training(self) -> TrainingMetrics:
        """Perform model training"""
        training_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now().isoformat()
        
        # Get training data
        telemetry, labels = self.buffer.get_recent(
            min(self.buffer.size(), 5000)  # Use up to 5000 recent samples
        )
        
        if len(telemetry) < self.min_samples_for_training:
            return TrainingMetrics(
                training_id=training_id,
                start_time=start_time,
                end_time="",
                duration_seconds=0,
                samples_used=len(telemetry),
                validation_score=0,
                test_score=0,
                improvement=0,
                model_changed=False
            )
        
        # Extract features
        X = self.feature_extractor.extract_features(telemetry)
        X_scaled = self.feature_extractor.transform(X)
        
        # Store previous scores for comparison
        prev_scores = {
            target: self.models.get(target, {}).get('r2_score', 0)
            for target in self.prediction_targets
        }
        
        # Train models for each target
        new_scores = {}
        for target in self.prediction_targets:
            y = np.array([t.get(target, 0) for t in telemetry])
            self._train_target_model(target, X_scaled, y)
            new_scores[target] = self.models[target]['r2_score']
        
        # Calculate improvement
        improvements = [
            new_scores[t] - prev_scores.get(t, 0)
            for t in self.prediction_targets
        ]
        avg_improvement = np.mean(improvements)
        
        self.model_version += 1
        
        # Update state
        self._update_state()
        
        return TrainingMetrics(
            training_id=training_id,
            start_time=start_time,
            end_time="",
            duration_seconds=0,
            samples_used=len(telemetry),
            validation_score=np.mean(list(new_scores.values())),
            test_score=np.mean(list(new_scores.values())),
            improvement=avg_improvement,
            model_changed=avg_improvement > 0.01
        )

    def predict(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make predictions from current telemetry
        
        Args:
            telemetry: Current flight telemetry
            
        Returns:
            Dictionary with predictions
        """
        if not self.models:
            return self._fallback_prediction(telemetry)
        
        # Extract features
        X = self.feature_extractor.extract_features([telemetry])
        X_scaled = self.feature_extractor.transform(X)
        
        predictions = {'timestamp': datetime.now().isoformat()}
        
        for target, target_data in self.models.items():
            try:
                pred = target_data['model'].predict(X_scaled)[0]
                predictions[f'predicted_{target}'] = float(pred)
                predictions[f'{target}_confidence'] = float(target_data['r2_score'])
            except Exception as e:
                logger.warning(f"Prediction failed for {target}: {e}")
                predictions[f'predicted_{target}'] = telemetry.get(target, 0)
        
        # Track prediction performance
        self._track_prediction(telemetry, predictions)
        
        return predictions

    def _track_prediction(self, telemetry: Dict, predictions: Dict):
        """Track prediction accuracy for performance monitoring"""
        for target in self.prediction_targets:
            actual = telemetry.get(target)
            predicted = predictions.get(f'predicted_{target}')
            
            if actual is not None and predicted is not None:
                error = abs(actual - predicted)
                normalized_error = error / (abs(actual) + 1e-6)
                accuracy = 1 - min(normalized_error, 1.0)
                self.performance_window.append(accuracy)

    def _fallback_prediction(self, telemetry: Dict) -> Dict[str, Any]:
        """Fallback predictions when model not trained"""
        predictions = {'timestamp': datetime.now().isoformat(), 'status': 'fallback'}
        
        for target in self.prediction_targets:
            predictions[f'predicted_{target}'] = telemetry.get(target, 0)
            predictions[f'{target}_confidence'] = 0.0
        
        return predictions

    def _update_state(self):
        """Update model state"""
        avg_score = np.mean([
            self.models.get(t, {}).get('r2_score', 0)
            for t in self.prediction_targets
        ])
        
        avg_error = np.mean([
            1 - self.models.get(t, {}).get('r2_score', 0)
            for t in self.prediction_targets
        ])
        
        # Determine performance trend
        if len(self.performance_window) >= 10:
            recent = list(self.performance_window)[-10:]
            if np.mean(recent[-5:]) > np.mean(recent[:5]) + 0.02:
                trend = "improving"
            elif np.mean(recent[-5:]) < np.mean(recent[:5]) - 0.02:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        next_training = None
        if self.last_training_time:
            next_training = (
                self.last_training_time + timedelta(seconds=self.training_interval_seconds)
            ).isoformat()
        
        self.state = FlightModelState(
            timestamp=datetime.now().isoformat(),
            total_samples=self.buffer.size(),
            training_iterations=len(self.training_history),
            model_version=self.model_version,
            accuracy_score=avg_score,
            prediction_error=avg_error,
            last_training_time=self.last_training_time.isoformat() if self.last_training_time else None,
            next_training_trigger=next_training,
            performance_trend=trend,
            active_features=self.feature_extractor.feature_names
        )

    def get_state(self) -> Optional[FlightModelState]:
        """Get current model state"""
        if self.state is None:
            self._update_state()
        return self.state

    def get_training_history(self, limit: int = 10) -> List[TrainingMetrics]:
        """Get recent training history"""
        return self.training_history[-limit:]

    def save_model(self, filepath: str) -> bool:
        """Save model to file"""
        try:
            model_data = {
                'models': {
                    name: {
                        'model': data['model'],
                        'r2_score': data['r2_score']
                    }
                    for name, data in self.models.items()
                },
                'model_version': self.model_version,
                'feature_extractor': self.feature_extractor,
                'feature_stats': self.feature_extractor.feature_stats,
                'training_history': [asdict(m) for m in self.training_history[-100:]],
                'config': self.config
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load_model(self, filepath: str) -> bool:
        """Load model from file"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data.get('models', {})
            self.model_version = model_data.get('model_version', 0)
            self.feature_extractor = model_data.get('feature_extractor', FlightFeatureExtractor())
            self.training_history = [
                TrainingMetrics(**m) for m in model_data.get('training_history', [])
            ]
            
            logger.info(f"Model loaded from {filepath} (version {self.model_version})")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        if not self.state:
            self._update_state()
        
        report = {
            'model_state': asdict(self.state) if self.state else {},
            'training_summary': {
                'total_sessions': len(self.training_history),
                'avg_improvement': np.mean([m.improvement for m in self.training_history]) if self.training_history else 0,
                'successful_sessions': sum(1 for m in self.training_history if m.model_changed)
            },
            'target_performance': {
                target: {
                    'r2_score': self.models.get(target, {}).get('r2_score', 0),
                    'trained_at': self.models.get(target, {}).get('trained_at', 'never')
                }
                for target in self.prediction_targets
            },
            'buffer_status': {
                'current_size': self.buffer.size(),
                'max_size': self.buffer.max_size,
                'utilization': self.buffer.size() / self.buffer.max_size
            }
        }
        
        return report


# Convenience function
def create_self_training_flight_model(config: Optional[Dict] = None) -> SelfTrainingFlightModel:
    """Create and return a Self-Training Flight Model instance"""
    return SelfTrainingFlightModel(config)


__all__ = [
    'SelfTrainingFlightModel',
    'create_self_training_flight_model',
    'FlightDataBuffer',
    'FlightFeatureExtractor',
    'FlightModelState',
    'TrainingMetrics',
    'TrainingMode'
]
