"""
AI Model Training Pipeline Module
End-to-end ML model training and optimization for telemetry
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


class ModelType(Enum):
    """ML model types"""
    LINEAR_REGRESSION = "linear_regression"
    POLYNOMIAL_REGRESSION = "polynomial_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    LSTM = "lstm"
    TRANSFORMER = "transformer"


class TrainingStage(Enum):
    """Training pipeline stages"""
    DATA_PREP = "data_preparation"
    FEATURE_ENG = "feature_engineering"
    MODEL_TRAIN = "model_training"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"
    DEPLOYMENT = "deployment"


@dataclass
class TrainingConfig:
    """Training configuration"""
    model_type: ModelType
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    hyperparameter_search: bool = False


@dataclass
class TrainingResult:
    """Training result"""
    model: Any
    metrics: Dict[str, float]
    training_time: float
    history: Dict[str, List[float]]
    feature_importance: Optional[Dict[str, float]] = None


class FeatureEngineer:
    """Feature engineering for ML"""
    
    def __init__(self):
        self.feature_functions: Dict[str, Callable] = {}
        
    def add_feature(self, name: str, func: Callable):
        """Add feature function"""
        self.feature_functions[name] = func
    
    def engineer_features(self, data: Dict[str, np.ndarray]) -> Tuple[np.ndarray, List[str]]:
        """Generate all features"""
        
        features = []
        feature_names = []
        
        # Original features
        for name, values in data.items():
            features.append(values)
            feature_names.append(name)
            
            # Add derived features
            if name in self.feature_functions:
                derived = self.feature_functions[name](values)
                if isinstance(derived, np.ndarray):
                    features.append(derived)
                    feature_names.append(f"{name}_derived")
        
        # Statistical features
        for name, values in data.items():
            # Rolling statistics
            for window in [5, 10, 20]:
                rolling_mean = self._rolling_mean(values, window)
                rolling_std = self._rolling_std(values, window)
                
                features.append(rolling_mean)
                features.append(rolling_std)
                feature_names.extend([f"{name}_mean_w{window}", f"{name}_std_w{window}"])
            
            # Differences
            diff = np.diff(values, prepend=values[0])
            features.append(diff)
            feature_names.append(f"{name}_diff")
            
            # Lag features
            for lag in [1, 2, 3]:
                lagged = np.roll(values, lag)
                lagged[0:lag] = values[0]
                features.append(lagged)
                feature_names.append(f"{name}_lag{lag}")
        
        return np.column_stack(features), feature_names
    
    def _rolling_mean(self, arr: np.ndarray, window: int) -> np.ndarray:
        """Rolling mean"""
        return np.convolve(arr, np.ones(window)/window, mode='same')
    
    def _rolling_std(self, arr: np.ndarray, window: int) -> np.ndarray:
        """Rolling standard deviation"""
        result = np.zeros_like(arr)
        for i in range(len(arr)):
            start = max(0, i - window // 2)
            end = min(len(arr), i + window // 2)
            result[i] = np.std(arr[start:end])
        return result


class DataPreprocessor:
    """Data preprocessing for ML"""
    
    def __init__(self):
        self.scaler_params: Dict[str, Dict] = {}
        
    def normalize(self, data: np.ndarray, method: str = 'standard') -> np.ndarray:
        """Normalize data"""
        
        if method == 'standard':
            mean = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            
            self.scaler_params['mean'] = mean
            self.scaler_params['std'] = std
            
            return (data - mean) / (std + 1e-10)
        
        elif method == 'minmax':
            min_val = np.min(data, axis=0)
            max_val = np.max(data, axis=0)
            
            self.scaler_params['min'] = min_val
            self.scaler_params['max'] = max_val
            
            return (data - min_val) / (max_val - min_val + 1e-10)
        
        return data
    
    def handle_missing(self, data: np.ndarray, 
                     method: str = 'interpolate') -> np.ndarray:
        """Handle missing values"""
        
        if method == 'interpolate':
            mask = ~np.isnan(data)
            indices = np.arange(len(data))
            
            for col in range(data.shape[1]):
                valid = mask[:, col]
                if valid.any():
                    data[~valid, col] = np.interp(
                        indices[~valid],
                        indices[valid],
                        data[valid, col]
                    )
        
        elif method == 'mean':
            for col in range(data.shape[1]):
                mask = ~np.isnan(data[:, col])
                if mask.any():
                    mean_val = np.mean(data[mask, col])
                    data[~mask, col] = mean_val
        
        return data
    
    def split_data(self, data: np.ndarray, labels: np.ndarray,
                   test_size: float = 0.2) -> Tuple:
        """Split data into train/test"""
        
        n = len(data)
        n_test = int(n * test_size)
        
        indices = np.random.permutation(n)
        test_indices = indices[:n_test]
        train_indices = indices[n_test:]
        
        return (data[train_indices], data[test_indices],
                labels[train_indices], labels[test_indices])


class ModelTrainer:
    """ML model training"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model = None
        self.history = {'loss': [], 'val_loss': []}
        
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> TrainingResult:
        """Train model"""
        
        start_time = time.time()
        
        if self.config.model_type == ModelType.LINEAR_REGRESSION:
            result = self._train_linear(X_train, y_train, X_val, y_val)
        elif self.config.model_type == ModelType.POLYNOMIAL_REGRESSION:
            result = self._train_polynomial(X_train, y_train, X_val, y_val)
        elif self.config.model_type == ModelType.RANDOM_FOREST:
            result = self._train_random_forest(X_train, y_train, X_val, y_val)
        elif self.config.model_type == ModelType.NEURAL_NETWORK:
            result = self._train_neural_network(X_train, y_train, X_val, y_val)
        else:
            result = self._train_linear(X_train, y_train, X_val, y_val)
        
        result.training_time = time.time() - start_time
        
        return result
    
    def _train_linear(self, X_train, y_train, X_val, y_val):
        """Linear regression"""
        # Simple linear regression using normal equations
        X_with_bias = np.column_stack([np.ones(len(X_train)), X_train])
        
        # Calculate weights
        weights = np.linalg.lstsq(X_with_bias, y_train, rcond=None)[0]
        
        # Predict
        y_pred_train = X_with_bias @ weights
        
        # Metrics
        train_mse = np.mean((y_train - y_pred_train)**2)
        
        metrics = {
            'train_mse': train_mse,
            'train_rmse': np.sqrt(train_mse),
            'train_r2': self._r2_score(y_train, y_pred_train)
        }
        
        return TrainingResult(
            model=weights,
            metrics=metrics,
            training_time=0,
            history=self.history
        )
    
    def _train_polynomial(self, X_train, y_train, X_val, y_val):
        """Polynomial regression"""
        degree = 3
        
        # Create polynomial features
        X_poly = self._poly_features(X_train, degree)
        
        # Train
        weights = np.linalg.lstsq(X_poly, y_train, rcond=None)[0]
        
        # Predict
        y_pred = X_poly @ weights
        
        metrics = {
            'train_mse': np.mean((y_train - y_pred)**2),
            'train_r2': self._r2_score(y_train, y_pred)
        }
        
        return TrainingResult(
            model={'weights': weights, 'degree': degree},
            metrics=metrics,
            training_time=0,
            history=self.history
        )
    
    def _train_random_forest(self, X_train, y_train, X_val, y_val):
        """Random forest (simplified)"""
        n_trees = 10
        
        trees = []
        for _ in range(n_trees):
            # Bootstrap sample
            indices = np.random.choice(len(X_train), len(X_train), replace=True)
            X_boot = X_train[indices]
            y_boot = y_train[indices]
            
            # Simple decision tree
            tree = self._build_tree(X_boot, y_boot, depth=5)
            trees.append(tree)
        
        # Predict (average)
        predictions = np.zeros(len(X_train))
        for tree in trees:
            predictions += self._predict_tree(X_train, tree)
        predictions /= n_trees
        
        metrics = {
            'train_mse': np.mean((y_train - predictions)**2),
            'train_r2': self._r2_score(y_train, predictions)
        }
        
        return TrainingResult(
            model=trees,
            metrics=metrics,
            training_time=0,
            history=self.history
        )
    
    def _train_neural_network(self, X_train, y_train, X_val, y_val):
        """Simple neural network"""
        
        # Architecture
        input_size = X_train.shape[1]
        hidden_size = 32
        output_size = 1
        
        # Initialize weights
        W1 = np.random.randn(input_size, hidden_size) * 0.1
        b1 = np.zeros(hidden_size)
        W2 = np.random.randn(hidden_size, output_size) * 0.1
        b2 = np.zeros(output_size)
        
        # Training
        for epoch in range(self.config.epochs):
            # Forward pass
            hidden = np.maximum(0, X_train @ W1 + b1)  # ReLU
            output = hidden @ W2 + b2
            
            # Backward pass
            lr = self.config.learning_rate
            
            error = output - y_train.reshape(-1, 1)
            
            dW2 = hidden.T @ error / len(X_train)
            db2 = np.mean(error, axis=0)
            
            d_hidden = error @ W2.T
            d_hidden[hidden <= 0] = 0
            
            dW1 = X_train.T @ d_hidden / len(X_train)
            db1 = np.mean(d_hidden, axis=0)
            
            # Update
            W2 -= lr * dW2
            b2 -= lr * db2
            W1 -= lr * dW1
            b1 -= lr * db1
            
            # Store loss
            self.history['loss'].append(np.mean(error**2))
        
        # Final predictions
        hidden = np.maximum(0, X_train @ W1 + b1)
        output = hidden @ W2 + b2
        
        metrics = {
            'train_mse': np.mean((y_train - output.flatten())**2),
            'train_r2': self._r2_score(y_train, output.flatten())
        }
        
        return TrainingResult(
            model={'W1': W1, 'b1': b1, 'W2': W2, 'b2': b2},
            metrics=metrics,
            training_time=0,
            history=self.history
        )
    
    def _poly_features(self, X: np.ndarray, degree: int) -> np.ndarray:
        """Create polynomial features"""
        poly = [np.ones(len(X))]
        
        for d in range(1, degree + 1):
            for i in range(X.shape[1]):
                poly.append(X[:, i]**d)
        
        return np.column_stack(poly)
    
    def _build_tree(self, X, y, depth, max_depth=5):
        """Build decision tree"""
        if depth >= max_depth or len(np.unique(y)) == 1:
            return {'leaf': True, 'value': np.mean(y)}
        
        # Best split
        best_gain = -np.inf
        best_split = None
        
        for i in range(X.shape[1]):
            for threshold in [np.median(X[:, i])]:
                left = y[X[:, i] < threshold]
                right = y[X[:, i] >= threshold]
                
                if len(left) > 0 and len(right) > 0:
                    gain = np.var(y) - (len(left) * np.var(left) + len(right) * np.var(right)) / len(y)
                    
                    if gain > best_gain:
                        best_gain = gain
                        best_split = (i, threshold)
        
        if best_split is None:
            return {'leaf': True, 'value': np.mean(y)}
        
        feature_idx, threshold = best_split
        left_idx = X[:, feature_idx] < threshold
        right_idx = ~left_idx
        
        return {
            'leaf': False,
            'feature': feature_idx,
            'threshold': threshold,
            'left': self._build_tree(X[left_idx], y[left_idx], depth + 1, max_depth),
            'right': self._build_tree(X[right_idx], y[right_idx], depth + 1, max_depth)
        }
    
    def _predict_tree(self, X, tree):
        """Predict using tree"""
        if tree.get('leaf', False):
            return np.full(len(X), tree['value'])
        
        predictions = np.zeros(len(X))
        
        left_idx = X[:, tree['feature']] < tree['threshold']
        right_idx = ~left_idx
        
        predictions[left_idx] = self._predict_tree(X[left_idx], tree['left'])
        predictions[right_idx] = self._predict_tree(X[right_idx], tree['right'])
        
        return predictions
    
    def _r2_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate R2 score"""
        ss_res = np.sum((y_true - y_pred)**2)
        ss_tot = np.sum((y_true - np.mean(y_true))**2)
        
        return 1 - ss_res / (ss_tot + 1e-10)


class HyperparameterOptimizer:
    """Hyperparameter optimization"""
    
    def __init__(self, model_type: ModelType):
        self.model_type = model_type
        
    def grid_search(self, X_train, y_train, X_val, y_val,
                   param_grid: Dict) -> Tuple[Dict, float]:
        """Grid search for best hyperparameters"""
        
        best_params = {}
        best_score = -np.inf
        
        # Generate parameter combinations
        import itertools
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        for combo in itertools.product(*values):
            params = dict(zip(keys, combo))
            
            # Train with params
            config = TrainingConfig(
                model_type=self.model_type,
                **params
            )
            
            trainer = ModelTrainer(config)
            result = trainer.train(X_train, y_train, X_val, y_val)
            
            score = result.metrics.get('train_r2', 0)
            
            if score > best_score:
                best_score = score
                best_params = params
        
        return best_params, best_score
    
    def random_search(self, X_train, y_train, X_val, y_val,
                     param_distributions: Dict,
                     n_iter: int = 10) -> Tuple[Dict, float]:
        """Random search for best hyperparameters"""
        
        best_params = {}
        best_score = -np.inf
        
        for _ in range(n_iter):
            # Sample random params
            params = {}
            for key, dist in param_distributions.items():
                if isinstance(dist, tuple) and isinstance(dist[0], float):
                    params[key] = np.random.uniform(dist[0], dist[1])
                elif isinstance(dist, tuple):
                    params[key] = np.random.choice(dist)
            
            # Train
            config = TrainingConfig(
                model_type=self.model_type,
                **params
            )
            
            trainer = ModelTrainer(config)
            result = trainer.train(X_train, y_train, X_val, y_val)
            
            score = result.metrics.get('train_r2', 0)
            
            if score > best_score:
                best_score = score
                best_params = params
        
        return best_params, best_score


class MLTrainingPipeline:
    """Complete ML training pipeline"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()
        self.trainer = ModelTrainer(config)
        self.optimizer = HyperparameterOptimizer(config.model_type)
        
        self.stage_results: Dict[TrainingStage, Any] = {}
        
    def run(self, data: Dict[str, np.ndarray], 
            target: str) -> TrainingResult:
        """Run complete training pipeline"""
        
        # Stage 1: Data Preparation
        X = data[target]
        y = data.get('label', X)  # Simplified
        
        X = self.preprocessor.handle_missing(X)
        X = self.preprocessor.normalize(X)
        
        self.stage_results[TrainingStage.DATA_PREP] = X
        
        # Stage 2: Feature Engineering
        X_features, feature_names = self.feature_engineer.engineage_features(data)
        
        self.stage_results[TrainingStage.FEATURE_ENG] = (X_features, feature_names)
        
        # Stage 3: Split data
        X_train, X_val, y_train, y_val = self.preprocessor.split_data(
            X_features, y, self.config.validation_split
        )
        
        # Stage 4: Model Training
        result = self.trainer.train(X_train, y_train, X_val, y_val)
        
        self.stage_results[TrainingStage.MODEL_TRAIN] = result
        
        # Stage 5: Optimization (optional)
        if self.config.hyperparameter_search:
            best_params, best_score = self.optimizer.random_search(
                X_train, y_train, X_val, y_val,
                {'learning_rate': (0.0001, 0.1), 'batch_size': [16, 32, 64]}
            )
            result.metrics['optimization_score'] = best_score
        
        return result
    
    def predict(self, model: Any, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        
        if isinstance(model, dict) and 'weights' in model:
            # Polynomial
            X_poly = self.trainer._poly_features(X, model['degree'])
            return X_poly @ model['weights']
        
        return X


# Example usage
if __name__ == "__main__":
    print("Testing AI Model Training Pipeline...")
    
    # Generate sample data
    print("\n1. Generating sample data...")
    np.random.seed(42)
    
    data = {
        'altitude': np.cumsum(np.random.randn(1000) * 0.5 + 0.5),
        'velocity': np.random.randn(1000) * 10 + 50,
        'temperature': np.random.randn(1000) * 2 + 25,
        'pressure': np.random.randn(1000) * 100 + 101325,
        'label': np.random.randn(1000)
    }
    
    # Create config
    print("\n2. Creating training config...")
    config = TrainingConfig(
        model_type=ModelType.NEURAL_NETWORK,
        learning_rate=0.01,
        batch_size=32,
        epochs=50
    )
    
    # Run pipeline
    print("\n3. Running training pipeline...")
    pipeline = MLTrainingPipeline(config)
    result = pipeline.run(data, 'altitude')
    
    print(f"   Training MSE: {result.metrics['train_mse']:.4f}")
    print(f"   Training R2: {result.metrics['train_r2']:.4f}")
    print(f"   Training time: {result.training_time:.2f}s")
    
    # Test prediction
    print("\n4. Testing prediction...")
    test_data = np.random.randn(10, 10)
    predictions = pipeline.predict(result.model, test_data)
    print(f"   Predictions shape: {predictions.shape}")
    
    print("\n✅ AI Model Training Pipeline test completed!")