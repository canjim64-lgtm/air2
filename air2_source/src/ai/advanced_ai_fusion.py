"""
Advanced AI Ensemble System for AirOne v3.0
Combines algorithms from multiple open-source AI frameworks
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Import available ML libraries (with fallbacks)
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.svm import SVR, SVC
    from sklearn.neural_network import MLPRegressor
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from xgboost import XGBRegressor, XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    from catboost import CatBoostRegressor, CatBoostClassifier
    CATBOOST_AVAILABLE = False  # Set to False initially to avoid issues
except ImportError:
    CATBOOST_AVAILABLE = False

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import pickle
import os
import random


class SklearnAlgorithm:
    """Wrapper for scikit-learn algorithms"""
    
    def __init__(self):
        self.algorithms = {}
        self.trained_models = {}
        
        if SKLEARN_AVAILABLE:
            self.algorithms = {
                'random_forest_regressor': RandomForestRegressor(n_estimators=100, random_state=42),
                'random_forest_classifier': RandomForestClassifier(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression(),
                'svm_regressor': SVR(),
                'neural_network': MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42),
                'kmeans_cluster': KMeans(n_clusters=5, random_state=42)
            }
    
    def train(self, algorithm_name: str, X: np.ndarray, y: np.ndarray, task_type: str = 'regression'):
        """Train a sklearn algorithm"""
        if not SKLEARN_AVAILABLE:
            return None
            
        if algorithm_name not in self.algorithms:
            raise ValueError(f"Algorithm {algorithm_name} not available")
        
        model = self.algorithms[algorithm_name]
        
        if task_type == 'classification' and 'classifier' not in algorithm_name and algorithm_name not in ['svm_regressor', 'neural_network']:
            # For classification tasks, ensure we use a classifier
            if algorithm_name == 'linear_regression':
                model = LogisticRegression(random_state=42)
            elif algorithm_name == 'svm_regressor':
                model = SVC(random_state=42)
            elif algorithm_name == 'gradient_boosting':
                # Use gradient boosting classifier instead
                model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        
        model.fit(X, y)
        self.trained_models[algorithm_name] = model
        return model
    
    def predict(self, algorithm_name: str, X: np.ndarray):
        """Make predictions with a trained sklearn model"""
        if algorithm_name not in self.trained_models:
            raise ValueError(f"Model {algorithm_name} not trained")
        
        model = self.trained_models[algorithm_name]
        return model.predict(X)


class TensorflowAlgorithm:
    """Wrapper for TensorFlow/Keras algorithms"""
    
    def __init__(self):
        self.models = {}
        self.compiled_models = {}
        
    def create_dense_model(self, input_dim: int, output_dim: int = 1, hidden_layers: List[int] = None):
        """Create a dense neural network model"""
        if not TENSORFLOW_AVAILABLE:
            return None
            
        if hidden_layers is None:
            hidden_layers = [128, 64, 32]
        
        model = keras.Sequential()
        model.add(layers.Dense(hidden_layers[0], activation='relu', input_shape=(input_dim,)))
        
        for units in hidden_layers[1:]:
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.Dropout(0.2))
        
        model.add(layers.Dense(output_dim, activation='linear' if output_dim == 1 else 'softmax'))
        
        return model
    
    def train(self, model_name: str, X: np.ndarray, y: np.ndarray, epochs: int = 100, validation_split: float = 0.2):
        """Train a TensorFlow model"""
        if not TENSORFLOW_AVAILABLE:
            return None
            
        if model_name not in self.models:
            # Create a default model if not specified
            self.models[model_name] = self.create_dense_model(X.shape[1], y.shape[1] if len(y.shape) > 1 else 1)
        
        model = self.models[model_name]
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        history = model.fit(
            X, y,
            epochs=epochs,
            validation_split=validation_split,
            verbose=0
        )
        
        self.compiled_models[model_name] = model
        return model, history
    
    def predict(self, model_name: str, X: np.ndarray):
        """Make predictions with a trained TensorFlow model"""
        if model_name not in self.compiled_models:
            raise ValueError(f"Model {model_name} not trained")
        
        model = self.compiled_models[model_name]
        return model.predict(X)


if TORCH_AVAILABLE:
    class TorchDenseNet(nn.Module):
        def __init__(self, input_size, output_size, hidden_sizes=None):
            super().__init__()
            if hidden_sizes is None:
                hidden_sizes = [128, 64, 32]
            
            layers = []
            prev_size = input_size
            
            for hidden_size in hidden_sizes:
                layers.append(nn.Linear(prev_size, hidden_size))
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(0.2))
                prev_size = hidden_size
            
            layers.append(nn.Linear(prev_size, output_size))
            self.network = nn.Sequential(*layers)
        
        def forward(self, x):
            return self.network(x)
else:
    # Dummy class when torch not available
    class TorchDenseNet:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch not available")


class TorchAlgorithm:
    """Wrapper for PyTorch algorithms - requires PyTorch to be installed"""
    
    def __init__(self):
        self.models = {}
        self.trained_models = {}
        if not TORCH_AVAILABLE:
            print("Warning: PyTorch not available, TorchAlgorithm will be limited")
    
    def train(self, model_name: str, X: np.ndarray, y: np.ndarray, epochs: int = 100):
        """Train a PyTorch model"""
        if not TORCH_AVAILABLE:
            return None
            
        input_size = X.shape[1]
        output_size = y.shape[1] if len(y.shape) > 1 else 1
        
        model = TorchDenseNet(input_size, output_size)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y) if output_size > 1 else torch.FloatTensor(y.reshape(-1, 1))
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
        
        self.trained_models[model_name] = model
        return model
    
    def predict(self, model_name: str, X: np.ndarray):
        """Make predictions with a trained PyTorch model"""
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} not trained")
        
        model = self.trained_models[model_name]
        X_tensor = torch.FloatTensor(X)
        with torch.no_grad():
            predictions = model(X_tensor)
        return predictions.numpy()


class XGBoostAlgorithm:
    """Wrapper for XGBoost algorithms"""
    
    def __init__(self):
        self.models = {}
    
    def train(self, model_name: str, X: np.ndarray, y: np.ndarray, task_type: str = 'regression'):
        """Train an XGBoost model"""
        if not XGBOOST_AVAILABLE:
            return None
            
        if task_type == 'regression':
            model = XGBRegressor(n_estimators=100, random_state=42)
        else:
            model = XGBClassifier(n_estimators=100, random_state=42)
        
        model.fit(X, y)
        self.models[model_name] = model
        return model
    
    def predict(self, model_name: str, X: np.ndarray):
        """Make predictions with a trained XGBoost model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not trained")
        
        model = self.models[model_name]
        return model.predict(X)


class LightGBMAlgorithm:
    """Wrapper for LightGBM algorithms"""
    
    def __init__(self):
        self.models = {}
    
    def train(self, model_name: str, X: np.ndarray, y: np.ndarray, task_type: str = 'regression'):
        """Train a LightGBM model"""
        if not LIGHTGBM_AVAILABLE:
            return None
            
        if task_type == 'regression':
            train_data = lgb.Dataset(X, label=y)
            params = {
                'objective': 'regression',
                'metric': 'rmse',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9
            }
            model = lgb.train(params, train_data, num_boost_round=100)
        else:
            train_data = lgb.Dataset(X, label=y)
            params = {
                'objective': 'multiclass',
                'num_class': len(np.unique(y)),
                'metric': 'multi_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9
            }
            model = lgb.train(params, train_data, num_boost_round=100)
        
        self.models[model_name] = model
        return model
    
    def predict(self, model_name: str, X: np.ndarray):
        """Make predictions with a trained LightGBM model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not trained")
        
        model = self.models[model_name]
        return model.predict(X)


class EnsembleAI:
    """Ensemble AI system combining multiple algorithms from different frameworks"""
    
    def __init__(self):
        self.sklearn_wrapper = SklearnAlgorithm()
        self.tensorflow_wrapper = TensorflowAlgorithm() if TENSORFLOW_AVAILABLE else None
        self.torch_wrapper = TorchAlgorithm() if TORCH_AVAILABLE else None
        self.xgboost_wrapper = XGBoostAlgorithm() if XGBOOST_AVAILABLE else None
        self.lightgbm_wrapper = LightGBMAlgorithm() if LIGHTGBM_AVAILABLE else None
        
        self.ensemble_weights = {}
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.pca = PCA(n_components=0.95) if SKLEARN_AVAILABLE else None
        
        # Initialize with default weights
        self._init_default_weights()
    
    def _init_default_weights(self):
        """Initialize default weights for ensemble"""
        self.ensemble_weights = {
            'random_forest': 0.2,
            'xgboost': 0.2,
            'lightgbm': 0.2,
            'neural_network': 0.15,
            'gradient_boosting': 0.15,
            'tensorflow': 0.05,
            'pytorch': 0.05
        }
    
    def preprocess_data(self, X: np.ndarray) -> np.ndarray:
        """Preprocess data using available tools"""
        if self.scaler:
            X = self.scaler.fit_transform(X)
        
        if self.pca and X.shape[0] > X.shape[1]:  # Only apply PCA if we have more samples than features
            X = self.pca.fit_transform(X)
        
        return X
    
    def train_ensemble(self, X: np.ndarray, y: np.ndarray, task_type: str = 'regression'):
        """Train multiple algorithms and create an ensemble"""
        X_processed = self.preprocess_data(X.copy())
        
        trained_predictions = {}
        
        # Train sklearn algorithms
        if SKLEARN_AVAILABLE:
            # Random Forest
            rf_model = self.sklearn_wrapper.train('random_forest_regressor', X_processed, y, task_type)
            if rf_model:
                rf_pred = self.sklearn_wrapper.predict('random_forest_regressor', X_processed)
                trained_predictions['random_forest'] = rf_pred
            
            # Gradient Boosting
            gb_model = self.sklearn_wrapper.train('gradient_boosting', X_processed, y, task_type)
            if gb_model:
                gb_pred = self.sklearn_wrapper.predict('gradient_boosting', X_processed)
                trained_predictions['gradient_boosting'] = gb_pred
            
            # Neural Network
            nn_model = self.sklearn_wrapper.train('neural_network', X_processed, y, task_type)
            if nn_model:
                nn_pred = self.sklearn_wrapper.predict('neural_network', X_processed)
                trained_predictions['neural_network'] = nn_pred
        
        # Train XGBoost
        if XGBOOST_AVAILABLE:
            xgb_model = self.xgboost_wrapper.train('xgboost', X_processed, y, task_type)
            if xgb_model:
                xgb_pred = self.xgboost_wrapper.predict('xgboost', X_processed)
                trained_predictions['xgboost'] = xgb_pred
        
        # Train LightGBM
        if LIGHTGBM_AVAILABLE:
            lgb_model = self.lightgbm_wrapper.train('lightgbm', X_processed, y, task_type)
            if lgb_model:
                lgb_pred = self.lightgbm_wrapper.predict('lightgbm', X_processed)
                trained_predictions['lightgbm'] = lgb_pred
        
        # Train TensorFlow model
        if TENSORFLOW_AVAILABLE:
            try:
                tf_model, history = self.tensorflow_wrapper.train('tensorflow', X_processed, y.reshape(-1, 1) if len(y.shape) == 1 else y, epochs=50)
                if tf_model:
                    tf_pred = self.tensorflow_wrapper.predict('tensorflow', X_processed)
                    trained_predictions['tensorflow'] = tf_pred.flatten() if len(tf_pred.shape) > 1 and tf_pred.shape[1] == 1 else tf_pred
            except:
                pass  # Skip if TensorFlow training fails
        
        # Train PyTorch model
        if TORCH_AVAILABLE:
            try:
                torch_model = self.torch_wrapper.train('pytorch', X_processed, y.reshape(-1, 1) if len(y.shape) == 1 else y, epochs=50)
                if torch_model:
                    torch_pred = self.torch_wrapper.predict('pytorch', X_processed)
                    trained_predictions['pytorch'] = torch_pred.flatten() if len(torch_pred.shape) > 1 and torch_pred.shape[1] == 1 else torch_pred
            except:
                pass  # Skip if PyTorch training fails
        
        # Calculate ensemble weights based on individual model performance
        if len(trained_predictions) > 1:
            self._update_weights_from_performance(trained_predictions, y)
        
        return trained_predictions
    
    def _update_weights_from_performance(self, predictions: Dict[str, np.ndarray], y_true: np.ndarray):
        """Update ensemble weights based on individual model performance"""
        performances = {}
        
        for model_name, pred in predictions.items():
            # Handle different prediction shapes
            if len(pred) != len(y_true):
                continue
                
            # Calculate performance (MSE for regression, accuracy for classification)
            if len(y_true.shape) == 1 or y_true.shape[1] == 1:
                # Regression task
                mse = mean_squared_error(y_true, pred)
                # Convert to score (lower MSE = higher score)
                performances[model_name] = 1 / (1 + mse)
            else:
                # Classification task
                # For multiclass, we'll use a simplified approach
                try:
                    acc = accuracy_score(y_true.argmax(axis=1), pred.argmax(axis=1)) if pred.ndim > 1 else accuracy_score(y_true, (pred > 0.5).astype(int))
                    performances[model_name] = acc
                except:
                    # Fallback for incompatible shapes
                    performances[model_name] = 0.5
        
        # Normalize performances to get weights
        total_perf = sum(performances.values())
        if total_perf > 0:
            for model_name in performances:
                self.ensemble_weights[model_name] = performances[model_name] / total_perf
    
    def predict_ensemble(self, X: np.ndarray) -> np.ndarray:
        """Make ensemble predictions"""
        X_processed = self.preprocess_data(X.copy())
        
        predictions = {}

        # Get predictions from all available models
        if SKLEARN_AVAILABLE:
            try:
                predictions['random_forest'] = self.sklearn_wrapper.predict('random_forest_regressor', X_processed)
            except Exception as e:
                self.logger.debug(f"Random forest prediction failed: {e}")

            try:
                predictions['gradient_boosting'] = self.sklearn_wrapper.predict('gradient_boosting', X_processed)
            except Exception as e:
                self.logger.debug(f"Gradient boosting prediction failed: {e}")

            try:
                predictions['neural_network'] = self.sklearn_wrapper.predict('neural_network', X_processed)
            except Exception as e:
                self.logger.debug(f"Neural network prediction failed: {e}")

        if XGBOOST_AVAILABLE:
            try:
                predictions['xgboost'] = self.xgboost_wrapper.predict('xgboost', X_processed)
            except Exception as e:
                self.logger.debug(f"XGBoost prediction failed: {e}")

        if LIGHTGBM_AVAILABLE:
            try:
                predictions['lightgbm'] = self.lightgbm_wrapper.predict('lightgbm', X_processed)
            except Exception as e:
                self.logger.debug(f"LightGBM prediction failed: {e}")

        if TENSORFLOW_AVAILABLE and self.tensorflow_wrapper:
            try:
                tf_pred = self.tensorflow_wrapper.predict('tensorflow', X_processed)
                predictions['tensorflow'] = tf_pred.flatten() if len(tf_pred.shape) > 1 and tf_pred.shape[1] == 1 else tf_pred
            except Exception as e:
                self.logger.debug(f"TensorFlow prediction failed: {e}")

        if TORCH_AVAILABLE and self.torch_wrapper:
            try:
                torch_pred = self.torch_wrapper.predict('pytorch', X_processed)
                predictions['pytorch'] = torch_pred.flatten() if len(torch_pred.shape) > 1 and torch_pred.shape[1] == 1 else torch_pred
            except Exception as e:
                self.logger.debug(f"PyTorch prediction failed: {e}")

        # Apply weighted ensemble
        ensemble_pred = np.zeros_like(list(predictions.values())[0]) if predictions else np.array([])
        
        total_weight = 0
        for model_name, pred in predictions.items():
            if model_name in self.ensemble_weights:
                weight = self.ensemble_weights[model_name]
                if len(ensemble_pred) == 0:
                    ensemble_pred = pred * weight
                else:
                    # Ensure predictions are the same shape
                    if ensemble_pred.shape == pred.shape:
                        ensemble_pred += pred * weight
                total_weight += weight
        
        if total_weight > 0:
            ensemble_pred /= total_weight
        
        return ensemble_pred
    
    def get_available_algorithms(self) -> Dict[str, bool]:
        """Get information about available algorithms"""
        return {
            'scikit-learn': SKLEARN_AVAILABLE,
            'tensorflow': TENSORFLOW_AVAILABLE,
            'pytorch': TORCH_AVAILABLE,
            'xgboost': XGBOOST_AVAILABLE,
            'lightgbm': LIGHTGBM_AVAILABLE
        }


class AdvancedAIFusion:
    """Advanced AI fusion system that combines multiple AI frameworks"""
    
    def __init__(self):
        self.ensemble_ai = EnsembleAI()
        self.feature_importance = {}
        self.model_performance = {}
        self.fusion_strategies = [
            'weighted_average',
            'stacking',
            'voting',
            'bayesian_blending'
        ]
    
    def train_fusion_model(self, X: np.ndarray, y: np.ndarray, task_type: str = 'regression', 
                          fusion_strategy: str = 'weighted_average') -> Dict[str, Any]:
        """Train a fusion model using multiple AI frameworks"""
        
        print(f"🚀 Training fusion model using {fusion_strategy} strategy...")
        
        # Train the ensemble
        trained_predictions = self.ensemble_ai.train_ensemble(X, y, task_type)
        
        # Evaluate individual models
        self._evaluate_individual_models(trained_predictions, y)
        
        # Make ensemble prediction on training data to evaluate
        ensemble_pred = self.ensemble_ai.predict_ensemble(X)
        
        # Calculate overall performance
        if task_type == 'regression':
            overall_mse = mean_squared_error(y, ensemble_pred)
            overall_performance = 1 / (1 + overall_mse)  # Convert to score
        else:
            overall_performance = accuracy_score(y, (ensemble_pred > 0.5).astype(int)) if ensemble_pred.ndim == 1 else accuracy_score(y.argmax(axis=1), ensemble_pred.argmax(axis=1))
        
        result = {
            'trained_models': list(trained_predictions.keys()),
            'ensemble_performance': overall_performance,
            'individual_performances': self.model_performance,
            'feature_importance': self.feature_importance,
            'fusion_strategy': fusion_strategy,
            'available_frameworks': self.ensemble_ai.get_available_algorithms()
        }
        
        print(f"✅ Fusion model trained successfully!")
        print(f"📊 Overall ensemble performance: {overall_performance:.4f}")
        
        return result
    
    def _evaluate_individual_models(self, predictions: Dict[str, np.ndarray], y_true: np.ndarray):
        """Evaluate individual model performances"""
        for model_name, pred in predictions.items():
            if len(pred) != len(y_true):
                continue
                
            if len(y_true.shape) == 1 or y_true.shape[1] == 1:
                # Regression
                mse = mean_squared_error(y_true, pred)
                self.model_performance[model_name] = 1 / (1 + mse)  # Convert to score
            else:
                # Classification
                try:
                    acc = accuracy_score(y_true.argmax(axis=1), pred.argmax(axis=1)) if pred.ndim > 1 else accuracy_score(y_true, (pred > 0.5).astype(int))
                    self.model_performance[model_name] = acc
                except:
                    self.model_performance[model_name] = 0.5
    
    def predict_fusion(self, X: np.ndarray) -> np.ndarray:
        """Make predictions using the fusion model"""
        return self.ensemble_ai.predict_ensemble(X)
    
    def get_framework_summary(self) -> str:
        """Get a summary of available AI frameworks"""
        frameworks = self.ensemble_ai.get_available_algorithms()
        
        summary = "AI Frameworks Integration Summary:\n"
        summary += "="*40 + "\n"
        
        for framework, available in frameworks.items():
            status = "✅ Available" if available else "❌ Not Available"
            summary += f"{framework.capitalize()}: {status}\n"
        
        summary += f"\nTotal Algorithms Available: {len([f for f in frameworks.values() if f])}/{len(frameworks)}"
        
        return summary


# Global instance
advanced_ai_fusion = AdvancedAIFusion()