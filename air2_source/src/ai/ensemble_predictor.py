"""
AirOne v4.0 - Multi-Model Ensemble Predictor
Combines multiple ML models for robust flight predictions
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports
try:
    from sklearn.ensemble import (
        RandomForestRegressor, GradientBoostingRegressor,
        ExtraTreesRegressor, AdaBoostRegressor,
        VotingRegressor, StackingRegressor
    )
    from sklearn.linear_model import Ridge, Lasso, ElasticNet, BayesianRidge
    from sklearn.neural_network import MLPRegressor
    from sklearn.svm import SVR
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


@dataclass
class ModelPrediction:
    """Prediction from a single model"""
    model_name: str
    prediction: float
    confidence: float
    model_weight: float


@dataclass
class EnsemblePrediction:
    """Combined ensemble prediction"""
    timestamp: str
    target: str
    predicted_value: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    ensemble_confidence: float
    model_predictions: List[ModelPrediction]
    model_agreement: float
    best_single_model: str
    prediction_method: str


class EnsembleModel:
    """
    Individual model wrapper for ensemble
    """

    def __init__(self, name: str, model: Any, scaler: Optional[StandardScaler] = None):
        self.name = name
        self.model = model
        self.scaler = scaler
        self.is_trained = False
        self.validation_score = 0.0
        self.prediction_history: List[float] = []
        self.error_history: List[float] = []

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train the model"""
        if self.scaler:
            X = self.scaler.fit_transform(X)
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make prediction"""
        if self.scaler:
            X = self.scaler.transform(X)
        return self.model.predict(X)

    def update_score(self, y_true: np.ndarray, y_pred: np.ndarray):
        """Update validation score"""
        self.validation_score = r2_score(y_true, y_pred)
        
        # Track errors
        errors = np.abs(y_true - y_pred)
        self.error_history.extend(errors.tolist())
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

    def get_confidence(self, X: np.ndarray) -> np.ndarray:
        """Estimate prediction confidence"""
        if not self.error_history:
            return np.ones(len(X)) * 0.5
        
        # Use historical error to estimate confidence
        avg_error = np.mean(self.error_history[-100:])
        std_error = np.std(self.error_history[-100:])
        
        # Confidence based on error distribution
        confidence = 1 / (1 + std_error / (avg_error + 1e-6))
        return np.ones(len(X)) * confidence


class MultiModelEnsemble:
    """
    Multi-model ensemble predictor
    
    Combines predictions from multiple models using:
    - Weighted averaging
    - Stacking
    - Bayesian model averaging
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Model registry
        self.models: Dict[str, EnsembleModel] = {}
        self.model_weights: Dict[str, float] = {}
        
        # Ensemble configuration
        self.ensemble_method = self.config.get('ensemble_method', 'weighted')
        self.min_models_for_ensemble = self.config.get('min_models', 3)
        self.adaptive_weighting = self.config.get('adaptive_weighting', True)
        
        # Feature configuration
        self.feature_names = []
        self.scaler = StandardScaler()
        
        # Prediction tracking
        self.prediction_history: Dict[str, List[EnsemblePrediction]] = defaultdict(list)
        
        # Target models
        self.targets = ['altitude', 'velocity', 'battery_percentage', 'climb_rate']

    def initialize_models(self):
        """Initialize all models in the ensemble"""
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available")
            return
        
        logger.info("Initializing ensemble models...")
        
        # Define model configurations
        model_configs = {
            'random_forest': RandomForestRegressor(
                n_estimators=100, max_depth=20, min_samples_split=5,
                n_jobs=-1, random_state=42
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100, max_depth=5, learning_rate=0.1,
                random_state=42
            ),
            'extra_trees': ExtraTreesRegressor(
                n_estimators=100, max_depth=20, min_samples_split=5,
                n_jobs=-1, random_state=42
            ),
            'ada_boost': AdaBoostRegressor(
                n_estimators=50, learning_rate=0.5,
                random_state=42
            ),
            'bayesian_ridge': BayesianRidge(),
            'mlp': MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                max_iter=500, early_stopping=True,
                random_state=42
            ),
            'knn': KNeighborsRegressor(n_neighbors=5, n_jobs=-1),
            'ridge': Ridge(alpha=1.0)
        }
        
        # Create models for each target
        for target in self.targets:
            for name, model in model_configs.items():
                model_name = f"{target}_{name}"
                self.models[model_name] = EnsembleModel(
                    name=model_name,
                    model=model,
                    scaler=StandardScaler()
                )
                self.model_weights[model_name] = 1.0
        
        logger.info(f"Initialized {len(self.models)} models")

    def train(self, X: np.ndarray, y_dict: Dict[str, np.ndarray],
              validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train all models
        
        Args:
            X: Feature matrix
            y_dict: Dictionary of target arrays
            validation_split: Validation data ratio
            
        Returns:
            Training results
        """
        if not SKLEARN_AVAILABLE:
            return {'error': 'scikit-learn not available'}
        
        results = {}
        
        # Split data
        if len(X) > 10:
            X_train, X_val, indices = self._split_data(X, validation_split)
        else:
            X_train, X_val = X, X
        
        # Train each model
        for target, y in y_dict.items():
            if len(y) != len(X):
                continue
            
            y_train = y[:len(X_train)]
            y_val = y[-len(X_val):] if len(X_val) > 0 else y_train
            
            for model_name, model in self.models.items():
                if not model_name.startswith(f"{target}_"):
                    continue
                
                try:
                    model.fit(X_train, y_train)
                    
                    # Validate
                    if len(X_val) > 0:
                        y_pred = model.predict(X_val)
                        model.update_score(y_val, y_pred)
                        r2 = model.validation_score
                    else:
                        r2 = 0.0
                    
                    # Update weight based on performance
                    if self.adaptive_weighting:
                        self.model_weights[model_name] = max(0.1, r2)
                    
                    results[model_name] = {
                        'status': 'trained',
                        'r2_score': r2,
                        'weight': self.model_weights[model_name]
                    }
                    
                except Exception as e:
                    results[model_name] = {
                        'status': 'failed',
                        'error': str(e)
                    }
        
        logger.info(f"Training complete. {sum(1 for r in results.values() if r.get('status') == 'trained')} models trained")
        return results

    def _split_data(self, X: np.ndarray, val_split: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Split data into train and validation"""
        n = len(X)
        split_idx = int(n * (1 - val_split))
        
        indices = np.random.permutation(n)
        train_idx = indices[:split_idx]
        val_idx = indices[split_idx:]
        
        return X[train_idx], X[val_idx], indices

    def predict(self, X: np.ndarray, target: str) -> EnsemblePrediction:
        """
        Make ensemble prediction for a target
        
        Args:
            X: Feature matrix
            target: Target variable name
            
        Returns:
            EnsemblePrediction
        """
        # Get models for this target
        target_models = {
            name: model for name, model in self.models.items()
            if name.startswith(f"{target}_") and model.is_trained
        }
        
        if not target_models:
            return self._fallback_prediction(target)
        
        # Get individual predictions
        model_predictions = []
        all_predictions = []
        weights = []
        
        for name, model in target_models.items():
            try:
                pred = model.predict(X)[0]
                confidence = model.get_confidence(X)[0]
                weight = self.model_weights.get(name, 0.5)
                
                model_predictions.append(ModelPrediction(
                    model_name=name,
                    prediction=float(pred),
                    confidence=float(confidence),
                    model_weight=float(weight)
                ))
                
                all_predictions.append(pred)
                weights.append(weight)
                
            except Exception as e:
                logger.warning(f"Prediction failed for {name}: {e}")
        
        if not all_predictions:
            return self._fallback_prediction(target)
        
        # Combine predictions
        if self.ensemble_method == 'weighted':
            combined = self._weighted_average(all_predictions, weights)
        elif self.ensemble_method == 'stacking':
            combined = self._stacking_predict(all_predictions, X)
        elif self.ensemble_method == 'bayesian':
            combined = self._bayesian_average(all_predictions, weights)
        else:
            combined = self._weighted_average(all_predictions, weights)
        
        # Calculate confidence interval
        pred_std = np.std(all_predictions)
        ci_lower = combined - 1.96 * pred_std
        ci_upper = combined + 1.96 * pred_std
        
        # Model agreement
        agreement = 1 - (pred_std / (np.mean(np.abs(all_predictions)) + 1e-6))
        
        # Best single model
        best_idx = np.argmax(weights)
        best_model = list(target_models.keys())[best_idx]
        
        prediction = EnsemblePrediction(
            timestamp=datetime.now().isoformat(),
            target=target,
            predicted_value=float(combined),
            confidence_interval_lower=float(ci_lower),
            confidence_interval_upper=float(ci_upper),
            ensemble_confidence=float(np.mean([p.confidence for p in model_predictions])),
            model_predictions=model_predictions,
            model_agreement=float(agreement),
            best_single_model=best_model,
            prediction_method=self.ensemble_method
        )
        
        # Track history
        self.prediction_history[target].append(prediction)
        if len(self.prediction_history[target]) > 1000:
            self.prediction_history[target] = self.prediction_history[target][-1000:]
        
        return prediction

    def predict_all_targets(self, X: np.ndarray) -> Dict[str, EnsemblePrediction]:
        """Make predictions for all targets"""
        predictions = {}
        for target in self.targets:
            predictions[target] = self.predict(X, target)
        return predictions

    def _weighted_average(self, predictions: List[float], 
                         weights: List[float]) -> float:
        """Weighted average of predictions"""
        weights = np.array(weights)
        weights = weights / (weights.sum() + 1e-6)
        return np.average(predictions, weights=weights)

    def _bayesian_average(self, predictions: List[float],
                         weights: List[float]) -> float:
        """Bayesian model averaging"""
        # Convert weights to probabilities
        weights = np.array(weights)
        weights = np.exp(weights) / (np.sum(np.exp(weights)) + 1e-6)
        return np.average(predictions, weights=weights)

    def _stacking_predict(self, predictions: List[float], 
                         X: np.ndarray) -> float:
        """Stacking-based combination"""
        # Simple linear combination as meta-learner
        weights = np.array([self.model_weights.get(name, 0.5) 
                          for name in self.models.keys()
                          if name.startswith(predictions[0])])
        return self._weighted_average(predictions, weights.tolist())

    def _fallback_prediction(self, target: str) -> EnsemblePrediction:
        """Fallback prediction when models not available"""
        return EnsemblePrediction(
            timestamp=datetime.now().isoformat(),
            target=target,
            predicted_value=0.0,
            confidence_interval_lower=0.0,
            confidence_interval_upper=0.0,
            ensemble_confidence=0.0,
            model_predictions=[],
            model_agreement=0.0,
            best_single_model="none",
            prediction_method="fallback"
        )

    def update_weights(self, X: np.ndarray, y_dict: Dict[str, np.ndarray]):
        """Update model weights based on recent performance"""
        for target, y_true in y_dict.items():
            target_models = {
                name: model for name, model in self.models.items()
                if name.startswith(f"{target}_") and model.is_trained
            }
            
            for name, model in target_models.items():
                try:
                    y_pred = model.predict(X)
                    model.update_score(y_true, y_pred)
                    
                    # Update weight
                    if self.adaptive_weighting:
                        self.model_weights[name] = max(0.1, model.validation_score)
                        
                except Exception as e:
                    logger.warning(f"Weight update failed for {name}: {e}")

    def get_model_rankings(self, target: str) -> List[Dict[str, Any]]:
        """Get model rankings for a target"""
        target_models = [
            (name, model) for name, model in self.models.items()
            if name.startswith(f"{target}_") and model.is_trained
        ]
        
        rankings = []
        for name, model in sorted(target_models, 
                                  key=lambda x: self.model_weights.get(x[0], 0),
                                  reverse=True):
            rankings.append({
                'name': name,
                'weight': self.model_weights.get(name, 0),
                'r2_score': model.validation_score,
                'predictions_made': len(model.prediction_history)
            })
        
        return rankings

    def get_ensemble_summary(self) -> Dict[str, Any]:
        """Get ensemble summary"""
        summary = {
            'total_models': len(self.models),
            'trained_models': sum(1 for m in self.models.values() if m.is_trained),
            'targets': self.targets,
            'ensemble_method': self.ensemble_method,
            'adaptive_weighting': self.adaptive_weighting,
            'model_rankings': {}
        }
        
        for target in self.targets:
            summary['model_rankings'][target] = self.get_model_rankings(target)
        
        return summary

    def export_ensemble(self, filepath: str) -> bool:
        """Export ensemble configuration"""
        try:
            import pickle
            
            ensemble_data = {
                'models': {
                    name: {
                        'model': model.model,
                        'scaler': model.scaler,
                        'is_trained': model.is_trained,
                        'validation_score': model.validation_score
                    }
                    for name, model in self.models.items()
                    if model.is_trained
                },
                'weights': self.model_weights,
                'config': self.config,
                'targets': self.targets
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(ensemble_data, f)
            
            logger.info(f"Ensemble exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export ensemble: {e}")
            return False


# Convenience function
def create_ensemble_predictor(config: Optional[Dict] = None) -> MultiModelEnsemble:
    """Create and return a Multi-Model Ensemble instance"""
    return MultiModelEnsemble(config)


__all__ = [
    'MultiModelEnsemble',
    'create_ensemble_predictor',
    'EnsembleModel',
    'EnsemblePrediction',
    'ModelPrediction'
]
