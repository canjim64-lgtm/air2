"""
AirOne v4.0 - Unified AI/ML Service
Enterprise-grade AI/ML orchestration layer for AirOne Professional
Combines all AI/ML capabilities into a unified, scalable service
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import pickle
import os
import time
import hashlib
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import AI components
try:
    from .ai_core import AIFusionEngine, EnhancedAICore, AdvancedAIProcessor
    from .super_ai_system import SuperAISystem
    from .deepseek_model_integration import DeepSeekModelIntegration
    from .advanced_ai_fusion import AdvancedAIFusion
    from .enhanced_ai_core import MultiFrameworkAISystem
    AI_COMPONENTS_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"AI components could not be fully loaded due to missing dependencies: {e}")
    AI_COMPONENTS_AVAILABLE = False
    # Define stubs for necessary classes if they are missing
    class AIFusionEngine: pass
    class EnhancedAICore: pass
    class AdvancedAIProcessor: pass
    class SuperAISystem: 
        def __init__(self): pass
    class DeepSeekModelIntegration: 
        def __init__(self): self.model_loaded = False
        def analyze_data(self, data): return "DeepSeek AI unavailable."
    class AdvancedAIFusion: pass
    class MultiFrameworkAISystem: 
        def __init__(self): pass

# Import ML components
try:
    from ..ml.advanced_ml_engine import LocalAIDataAnalyzer, AdvancedReportGenerator
    from .advanced_algorithms import (
        EvolutionaryOptimizer, GeneticProgramming, ReinforcementLearningAgent,
        SwarmIntelligence, AdvancedEnsembleMethods
    )
    ML_COMPONENTS_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"ML components could not be fully loaded due to missing dependencies: {e}")
    ML_COMPONENTS_AVAILABLE = False
    # Define stubs for necessary classes if they are missing
    class LocalAIDataAnalyzer: pass
    class AdvancedReportGenerator: 
        def generate_report(self, *args, **kwargs): return "ML Report generator unavailable."
    class EvolutionaryOptimizer: 
        def __init__(self, *args, **kwargs): pass
    class GeneticProgramming: pass
    class ReinforcementLearningAgent: pass
    class SwarmIntelligence: 
        def __init__(self, *args, **kwargs): pass
    class AdvancedEnsembleMethods: pass

# Try imports with fallbacks
try:
    from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report, confusion_matrix
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.decomposition import PCA, TruncatedSVD
    from sklearn.neural_network import MLPRegressor, MLPClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Some ML features will be limited.")

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. Deep learning features will be limited.")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    # Verify functional and not corrupted (common issue on some Windows installs)
    import torch._utils
    _ = torch._utils # Force attribute access
    _test = torch.tensor([1.0])
    TORCH_AVAILABLE = True
except (ImportError, AttributeError, OSError, Exception):
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available or corrupted. Some AI features will be limited.")


class TaskType(Enum):
    """ML task types"""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES_FORECAST = "time_series_forecast"
    OPTIMIZATION = "optimization"


class ModelStatus(Enum):
    """Model training status"""
    NOT_TRAINED = "not_trained"
    TRAINING = "training"
    TRAINED = "trained"
    EVALUATING = "evaluating"
    DEPLOYED = "deployed"
    FAILED = "failed"


@dataclass
class ModelMetadata:
    """Metadata for trained models"""
    model_id: str
    model_type: str
    task_type: str
    created_at: str
    training_samples: int
    features_count: int
    accuracy: Optional[float] = None
    mse: Optional[float] = None
    r2_score: Optional[float] = None
    status: str = "not_trained"
    framework: str = "sklearn"
    hyperparameters: Optional[Dict] = None


@dataclass
class PredictionResult:
    """Structure for prediction results"""
    predictions: List[Any]
    confidence_scores: List[float]
    model_id: str
    inference_time_ms: float
    metadata: Dict[str, Any]


class UnifiedAIService:
    """
    Unified AI/ML Service for AirOne Professional v4.0
    
    Provides a single interface for all AI/ML operations including:
    - Multi-framework model training
    - Deep learning analysis
    - Anomaly detection
    - Time series forecasting
    - Optimization algorithms
    - Natural language processing (via DeepSeek)
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, ModelMetadata] = {}
        self.training_history: List[Dict] = []
        self.prediction_cache: Dict[str, Any] = {}
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.max_cache_size = self.config.get('max_cache_size', 1000)
        
        # Feature configuration
        self.feature_columns = [
            'altitude', 'velocity', 'temperature', 'pressure',
            'battery_level', 'latitude', 'longitude', 'radio_signal_strength'
        ]
        
        # Initialize core AI systems
        logger.info("Initializing Unified AI Service...")
        self.super_ai = SuperAISystem()
        self.multi_framework_ai = MultiFrameworkAISystem()
        self.deepseek_ai = DeepSeekModelIntegration()
        self.advanced_fusion = AdvancedAIFusion()
        
        # Initialize ML components
        if SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.regressor = RandomForestRegressor(n_estimators=100, random_state=42)
            self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            self.scaler = None
            self.anomaly_detector = None
            self.regressor = None
            self.classifier = None
            
        self.performance_mode = "PERFORMANCE" # Options: PERFORMANCE, ECO, THROTTLED
        
    def set_performance_mode(self, mode: str):
        """Sets the performance mode of the AI service"""
        mode = mode.upper()
        if mode in ["PERFORMANCE", "ECO", "THROTTLED"]:
            self.performance_mode = mode
            logger.info(f"AI Service performance mode set to {mode}")
            return True
        return False
        
        # Initialize optimization algorithms
        self.evolutionary_optimizer = EvolutionaryOptimizer()
        self.swarm_intelligence = SwarmIntelligence(dimensions=10)
        
        # Model registry
        self.model_registry: Dict[str, Dict] = {}
        
        logger.info("✅ Unified AI Service initialized successfully")

    def _generate_model_id(self, model_type: str, task_type: str) -> str:
        """Generate unique model ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{model_type}_{task_type}_{timestamp}_{time.time()}"
        model_hash = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:8]
        return f"{model_type}_{task_type}_{model_hash}"

    def _compute_hash(self, data: Any) -> str:
        """Compute hash for caching"""
        return hashlib.md5(str(data).encode('utf-8')).hexdigest()

    # ==================== DATA PREPROCESSING ====================

    def prepare_features(self, telemetry_data: List[Dict[str, Any]], 
                        include_derived: bool = True) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features from telemetry data
        
        Args:
            telemetry_data: List of telemetry records
            include_derived: Whether to create derived features
            
        Returns:
            Tuple of (feature_array, feature_names)
        """
        if not telemetry_data:
            return np.array([]), []

        features_list = []
        for record in telemetry_data:
            features = []
            for col in self.feature_columns:
                val = record.get(col, 0)
                if isinstance(val, (int, float)):
                    features.append(float(val))
                else:
                    features.append(0.0)
            features_list.append(features)

        X = np.array(features_list)
        feature_names = self.feature_columns.copy()

        if include_derived and len(telemetry_data) > 1:
            # Add temporal features
            for i in range(1, len(telemetry_data)):
                for j, col in enumerate(self.feature_columns):
                    diff_col = f"{col}_diff"
                    if i == 1:
                        feature_names.append(diff_col)
                    diff_val = float(telemetry_data[i].get(col, 0)) - float(telemetry_data[i-1].get(col, 0))
                    if len(features_list) > i:
                        if len(features_list[i]) < len(feature_names):
                            features_list[i].append(diff_val)
            
            # Pad first record
            while len(features_list[0]) < len(feature_names):
                features_list[0].append(0.0)
            
            X = np.array([f[:len(feature_names)] for f in features_list])

        return X, feature_names

    def normalize_features(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        """Normalize features using StandardScaler"""
        if self.scaler is None or X.size == 0:
            return X
        
        if fit:
            return self.scaler.fit_transform(X)
        else:
            try:
                return self.scaler.transform(X)
            except Exception:
                # If not fitted, fit and transform
                return self.scaler.fit_transform(X)

    # ==================== MODEL TRAINING ====================

    def train_model(self, telemetry_data: List[Dict[str, Any]], 
                   task_type: TaskType,
                   target_column: Optional[str] = None,
                   model_type: str = "random_forest",
                   hyperparameters: Optional[Dict] = None) -> ModelMetadata:
        """
        Train a model on telemetry data
        
        Args:
            telemetry_data: Training data
            task_type: Type of ML task
            target_column: Target variable for supervised learning
            model_type: Model algorithm to use
            hyperparameters: Model hyperparameters
            
        Returns:
            ModelMetadata with training results
        """
        if not telemetry_data:
            raise ValueError("No telemetry data provided")

        model_id = self._generate_model_id(model_type, task_type.value)
        start_time = time.time()
        
        # Ensure hyperparameters is a dict
        hyperparameters = hyperparameters or {}
        
        logger.info(f"Training {model_type} model for {task_type.value}...")
        
        try:
            # Prepare features
            X, feature_names = self.prepare_features(telemetry_data, include_derived=True)
            
            if X.size == 0:
                raise ValueError("Feature extraction failed")
            
            # Prepare target
            if task_type in [TaskType.REGRESSION, TaskType.CLASSIFICATION]:
                if not target_column:
                    target_column = 'altitude'  # Default target
                
                y = np.array([record.get(target_column, 0) for record in telemetry_data])
                
                # Normalize features
                X_scaled = self.normalize_features(X, fit=True)
                
                # Split data
                if len(X_scaled) > 10:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X_scaled, y, test_size=0.2, random_state=42
                    )
                else:
                    X_train, X_test = X_scaled, X_scaled
                    y_train, y_test = y, y
                
                # Train model based on type
                if model_type == "random_forest":
                    if task_type == TaskType.REGRESSION:
                        model = RandomForestRegressor(
                            n_estimators=hyperparameters.get('n_estimators', 100),
                            random_state=42,
                            **(hyperparameters or {})
                        )
                    else:
                        model = RandomForestClassifier(
                            n_estimators=hyperparameters.get('n_estimators', 100),
                            random_state=42,
                            **(hyperparameters or {})
                        )
                elif model_type == "gradient_boosting":
                    model = GradientBoostingRegressor(
                        n_estimators=hyperparameters.get('n_estimators', 100),
                        random_state=42,
                        **(hyperparameters or {})
                    )
                elif model_type == "mlp":
                    model = MLPRegressor(
                        hidden_layer_sizes=hyperparameters.get('hidden_layer_sizes', (64, 32, 16)),
                        max_iter=500,
                        random_state=42
                    )
                else:
                    model = RandomForestRegressor(n_estimators=100, random_state=42)
                
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                
                if task_type == TaskType.REGRESSION:
                    mse = mean_squared_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    accuracy = None
                else:
                    mse = None
                    r2 = None
                    accuracy = accuracy_score(y_test, y_pred)
                
                self.models[model_id] = model
                
            elif task_type == TaskType.ANOMALY_DETECTION:
                X_scaled = self.normalize_features(X, fit=True)
                model = IsolationForest(contamination=0.1, random_state=42)
                model.fit(X_scaled)
                self.models[model_id] = model
                mse, r2, accuracy = None, None, None
                
            elif task_type == TaskType.CLUSTERING:
                n_clusters = hyperparameters.get('n_clusters', 5) if hyperparameters else 5
                model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                model.fit(X)
                self.models[model_id] = model
                mse, r2, accuracy = None, None, None
                
            else:
                raise ValueError(f"Unsupported task type: {task_type.value}")
            
            training_time = time.time() - start_time
            
            # Create metadata
            metadata = ModelMetadata(
                model_id=model_id,
                model_type=model_type,
                task_type=task_type.value,
                created_at=datetime.now().isoformat(),
                training_samples=len(telemetry_data),
                features_count=X.shape[1],
                accuracy=accuracy,
                mse=mse,
                r2_score=r2,
                status="trained",
                framework="sklearn" if SKLEARN_AVAILABLE else "fallback",
                hyperparameters=hyperparameters
            )
            
            self.model_metadata[model_id] = metadata
            self.training_history.append({
                'model_id': model_id,
                'timestamp': metadata.created_at,
                'training_time': training_time,
                'metrics': {'accuracy': accuracy, 'mse': mse, 'r2': r2}
            })
            
            logger.info(f"✅ Model {model_id} trained successfully in {training_time:.2f}s")
            return metadata
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            metadata = ModelMetadata(
                model_id=model_id,
                model_type=model_type,
                task_type=task_type.value,
                created_at=datetime.now().isoformat(),
                training_samples=len(telemetry_data),
                features_count=0,
                status="failed"
            )
            self.model_metadata[model_id] = metadata
            raise

    # ==================== PREDICTIONS ====================

    def predict(self, model_id: str, input_data: Union[List[Dict], np.ndarray],
               return_confidence: bool = True) -> PredictionResult:
        """
        Make predictions using a trained model
        
        Args:
            model_id: ID of trained model
            input_data: Input data for prediction
            return_confidence: Whether to return confidence scores
            
        Returns:
            PredictionResult with predictions and metadata
        """
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        start_time = time.time()
        model = self.models[model_id]
        metadata = self.model_metadata[model_id]
        
        # Prepare input
        if isinstance(input_data, list) and isinstance(input_data[0], dict):
            # Must use the same 'include_derived' setting as training
            # Default to True if it looks like a sequence, but training used True
            X, _ = self.prepare_features(input_data, include_derived=True)
        else:
            X = np.array(input_data)
        
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Normalize if needed
        if self.scaler is not None and metadata.task_type in ['regression', 'classification']:
            X_scaled = self.normalize_features(X, fit=False)
        else:
            X_scaled = X
        
        # Make prediction
        if metadata.task_type in ['regression', 'classification']:
            predictions = model.predict(X_scaled).tolist()
        elif metadata.task_type == 'anomaly_detection':
            predictions = model.predict(X_scaled).tolist()
        elif metadata.task_type == 'clustering':
            predictions = model.predict(X_scaled).tolist()
        else:
            predictions = model.predict(X_scaled).tolist()
        
        # Calculate confidence
        confidence_scores = []
        if return_confidence:
            if hasattr(model, 'predict_proba') and metadata.task_type == 'classification':
                probas = model.predict_proba(X_scaled)
                confidence_scores = np.max(probas, axis=1).tolist()
            else:
                # Default confidence based on training metrics
                base_confidence = metadata.accuracy or metadata.r2_score or 0.8
                confidence_scores = [base_confidence] * len(predictions)
        
        inference_time = (time.time() - start_time) * 1000
        
        return PredictionResult(
            predictions=predictions,
            confidence_scores=confidence_scores,
            model_id=model_id,
            inference_time_ms=inference_time,
            metadata={
                'model_type': metadata.model_type,
                'task_type': metadata.task_type,
                'input_size': len(input_data)
            }
        )

    # ==================== ANOMALY DETECTION ====================

    def detect_anomalies(self, telemetry_data: List[Dict[str, Any]], 
                        threshold: float = -0.1) -> List[Dict[str, Any]]:
        """
        Detect anomalies in telemetry data
        
        Args:
            telemetry_data: Telemetry data to analyze
            threshold: Anomaly score threshold
            
        Returns:
            List of detected anomalies with details
        """
        if not telemetry_data:
            return []
        
        X, _ = self.prepare_features(telemetry_data)
        
        if self.anomaly_detector is None:
            # Train on the fly if not trained
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.anomaly_detector.fit(X)
        
        scaled_X = self.normalize_features(X, fit=False) if self.scaler else X
        
        try:
            predictions = self.anomaly_detector.predict(scaled_X)
            scores = self.anomaly_detector.decision_function(scaled_X)
        except Exception:
            # If not fitted, fit and predict
            self.anomaly_detector.fit(scaled_X)
            predictions = self.anomaly_detector.predict(scaled_X)
            scores = self.anomaly_detector.decision_function(scaled_X)
        
        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly
                severity = 'high' if score < -0.15 else ('medium' if score < -0.05 else 'low')
                anomalies.append({
                    'index': i,
                    'timestamp': telemetry_data[i].get('timestamp', 'unknown'),
                    'anomaly_score': float(score),
                    'severity': severity,
                    'data_point': telemetry_data[i]
                })
        
        return sorted(anomalies, key=lambda x: x['anomaly_score'])

    # ==================== DEEPSEEK INTEGRATION ====================

    def analyze_with_deepseek(self, data: Any, analysis_type: str = "summary") -> str:
        """
        Analyze data using DeepSeek AI
        
        Args:
            data: Data to analyze
            analysis_type: Type of analysis (summary, insights, prediction)
            
        Returns:
            AI-generated analysis text
        """
        if analysis_type == "summary":
            return self.deepseek_ai.analyze_data(data)
        elif analysis_type == "insights":
            return self.deepseek_ai.generate_insights(data)
        elif analysis_type == "prediction":
            return self.deepseek_ai.predict_outcomes(data)
        else:
            return self.deepseek_ai.analyze_data(data)

    # ==================== OPTIMIZATION ====================

    def optimize_hyperparameters(self, telemetry_data: List[Dict[str, Any]],
                                target_column: str,
                                param_space: Dict[str, Tuple],
                                n_iterations: int = 50) -> Dict[str, Any]:
        """
        Optimize model hyperparameters using evolutionary algorithms
        
        Args:
            telemetry_data: Training data
            target_column: Target variable
            param_space: Parameter space for optimization
            n_iterations: Number of optimization iterations
            
        Returns:
            Best parameters and performance
        """
        logger.info("Starting hyperparameter optimization...")
        
        X, _ = self.prepare_features(telemetry_data)
        y = np.array([r.get(target_column, 0) for r in telemetry_data])
        
        if len(X) < 10:
            return {'error': 'Insufficient data for optimization'}
        
        X_scaled = self.normalize_features(X, fit=True)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
        
        def fitness_function(params):
            model = RandomForestRegressor(
                n_estimators=int(params[0]),
                max_depth=int(params[1]) if len(params) > 1 else None,
                random_state=42
            )
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            return -mean_squared_error(y_test, y_pred)  # Negative for maximization
        
        best_params, best_score, history = self.evolutionary_optimizer.optimize(
            fitness_function,
            param_ranges=list(param_space.values()),
            population_size=20,
            generations=n_iterations
        )
        
        return {
            'best_parameters': best_params,
            'best_score': -best_score,  # Convert back to positive MSE
            'optimization_history': history
        }

    # ==================== MODEL MANAGEMENT ====================

    def list_models(self) -> List[ModelMetadata]:
        """List all trained models"""
        return list(self.model_metadata.values())

    def get_model(self, model_id: str) -> Optional[Any]:
        """Get a trained model by ID"""
        return self.models.get(model_id)

    def delete_model(self, model_id: str) -> bool:
        """Delete a trained model"""
        if model_id in self.models:
            del self.models[model_id]
            del self.model_metadata[model_id]
            logger.info(f"Model {model_id} deleted")
            return True
        return False

    def save_model(self, model_id: str, filepath: str) -> bool:
        """Save model to disk"""
        if model_id not in self.models:
            return False
        
        model_data = {
            'model': self.models[model_id],
            'metadata': asdict(self.model_metadata[model_id]),
            'scaler_state': self.scaler.__getstate__() if self.scaler else None
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model {model_id} saved to {filepath}")
        return True

    def load_model(self, filepath: str) -> Optional[str]:
        """Load model from disk"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            model_id = model_data['metadata']['model_id']
            self.models[model_id] = model_data['model']
            self.model_metadata[model_id] = ModelMetadata(**model_data['metadata'])
            
            if model_data['scaler_state'] and self.scaler:
                self.scaler.__setstate__(model_data['scaler_state'])
            
            logger.info(f"Model {model_id} loaded from {filepath}")
            return model_id
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None

    # ==================== REPORTING ====================

    def generate_analysis_report(self, telemetry_data: List[Dict[str, Any]],
                                include_predictions: bool = True) -> str:
        """
        Generate comprehensive analysis report
        
        Args:
            telemetry_data: Telemetry data to analyze
            include_predictions: Whether to include predictions
            
        Returns:
            Formatted report string
        """
        report_generator = AdvancedReportGenerator()
        
        # Perform analysis
        anomalies = self.detect_anomalies(telemetry_data)
        
        # Train temporary model for predictions
        predictions = []
        if include_predictions and len(telemetry_data) > 10:
            try:
                metadata = self.train_model(telemetry_data, TaskType.REGRESSION, 'altitude')
                last_records = telemetry_data[-5:]
                pred_result = self.predict(metadata.model_id, last_records)
                predictions = pred_result.predictions
            except Exception as e:
                logger.warning(f"Prediction failed: {e}")
        
        # Generate report
        report_data = {
            'telemetry_data': telemetry_data,
            'anomalies': anomalies,
            'predictions': predictions,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        report = report_generator.generate_report('mission_summary', report_data)
        
        if anomalies:
            report += "\n\n" + report_generator.generate_report('anomaly_report', {'anomalies': anomalies})
        
        return report

    # ==================== UTILITY METHODS ====================

    def clear_cache(self):
        """Clear prediction cache"""
        self.prediction_cache.clear()
        logger.info("Cache cleared")

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'status': 'operational',
            'models_count': len(self.models),
            'cache_size': len(self.prediction_cache),
            'frameworks_available': {
                'sklearn': SKLEARN_AVAILABLE,
                'tensorflow': TENSORFLOW_AVAILABLE,
                'pytorch': TORCH_AVAILABLE,
                'deepseek': self.deepseek_ai.model_loaded
            },
            'total_training_sessions': len(self.training_history)
        }

    def process_mission_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process mission data using AI capabilities.
        Specifically requested for mission orchestration.
        """
        logger.info(f"Processing mission data: {data}")
        
        # Wrap the data in a list for existing analysis methods if it's just a single record
        telemetry_list = [data]
        
        # Detect anomalies
        anomalies = self.detect_anomalies(telemetry_list)
        
        # Generate basic analysis
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "processed",
            "anomalies_found": len(anomalies),
            "anomalies": anomalies,
            "data_summary": {
                "altitude": data.get("altitude", 0),
                "mission_status": data.get("status", "unknown")
            }
        }


# Convenience function to create service instance
def create_unified_ai_service(config: Optional[Dict] = None) -> UnifiedAIService:
    """Create and return a Unified AI Service instance"""
    return UnifiedAIService(config)


# Export main classes
__all__ = [
    'UnifiedAIService',
    'create_unified_ai_service',
    'TaskType',
    'ModelStatus',
    'ModelMetadata',
    'PredictionResult'
]
