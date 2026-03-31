"""
AirOne v4.0 - Enhanced ML Algorithms
Next-generation machine learning algorithms with AutoML capabilities
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import time
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import sklearn with fallbacks
try:
    from sklearn.ensemble import (
        RandomForestRegressor, RandomForestClassifier, 
        GradientBoostingRegressor, GradientBoostingClassifier,
        ExtraTreesRegressor, ExtraTreesClassifier,
        AdaBoostRegressor, AdaBoostClassifier,
        HistGradientBoostingRegressor, HistGradientBoostingClassifier,
        VotingRegressor, VotingClassifier,
        StackingRegressor, StackingClassifier,
        IsolationForest
    )
    from sklearn.linear_model import (
        LinearRegression, Ridge, Lasso, ElasticNet, 
        BayesianRidge, ARDRegression, SGDRegressor,
        LogisticRegression, RidgeClassifier, PassiveAggressiveClassifier
    )
    from sklearn.svm import SVR, SVC, NuSVR, OneClassSVM
    from sklearn.neighbors import (
        KNeighborsRegressor, KNeighborsClassifier, 
        RadiusNeighborsRegressor, RadiusNeighborsClassifier,
        LocalOutlierFactor, NearestNeighbors
    )
    from sklearn.neural_network import MLPRegressor, MLPClassifier
    from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier, ExtraTreeRegressor
    from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, Birch, MeanShift
    from sklearn.decomposition import PCA, KernelPCA, FastICA, NMF
    from sklearn.preprocessing import (
        StandardScaler, MinMaxScaler, RobustScaler, 
        QuantileTransformer, PowerTransformer, PolynomialFeatures
    )
    from sklearn.model_selection import (
        train_test_split, cross_val_score, GridSearchCV, 
        RandomizedSearchCV, learning_curve, validation_curve
    )
    from sklearn.metrics import (
        mean_squared_error, r2_score, accuracy_score, 
        precision_score, recall_score, f1_score, roc_auc_score,
        silhouette_score, calinski_harabasz_score, davies_bouldin_score
    )
    from sklearn.pipeline import Pipeline, make_pipeline
    from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
    from sklearn.gaussian_process import GaussianProcessRegressor, GaussianProcessClassifier
    SKLEARN_AVAILABLE = True
except ImportError as e:
    SKLEARN_AVAILABLE = False
    logger.warning(f"scikit-learn import warning: {e}")

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, regularizers
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available")


class ModelCategory(Enum):
    """Model categories"""
    LINEAR = "linear"
    TREE_BASED = "tree_based"
    NEURAL_NETWORK = "neural_network"
    SVM = "svm"
    NEIGHBOR_BASED = "neighbor_based"
    ENSEMBLE = "ensemble"
    PROBABILISTIC = "probabilistic"
    CLUSTERING = "clustering"
    DECOMPOSITION = "decomposition"


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_name: str
    model_category: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    roc_auc: Optional[float] = None
    training_time: float = 0.0
    inference_time: float = 0.0
    model_size_kb: float = 0.0
    feature_count: int = 0
    sample_count: int = 0


class AutoMLSelector:
    """
    Automated model selection and hyperparameter tuning
    
    Automatically evaluates multiple models and selects the best performer
    """

    def __init__(self, task_type: str = "regression", cv_folds: int = 5):
        self.task_type = task_type
        self.cv_folds = cv_folds
        self.model_results: Dict[str, ModelPerformance] = {}
        self.best_model = None
        self.best_model_name = None
        self.best_score = None
        
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn required for AutoMLSelector")

    def _get_model_candidates(self) -> Dict[str, Any]:
        """Get candidate models for evaluation"""
        if self.task_type == "regression":
            return {
                'linear_regression': LinearRegression(),
                'ridge': Ridge(alpha=1.0),
                'lasso': Lasso(alpha=1.0),
                'elastic_net': ElasticNet(alpha=1.0, l1_ratio=0.5),
                'bayesian_ridge': BayesianRidge(),
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'extra_trees': ExtraTreesRegressor(n_estimators=100, random_state=42),
                'ada_boost': AdaBoostRegressor(n_estimators=50, random_state=42),
                'mlp': MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42),
                'svr': SVR(kernel='rbf', C=1.0, epsilon=0.1),
                'knn': KNeighborsRegressor(n_neighbors=5),
                'gaussian_process': GaussianProcessRegressor(random_state=42),
                'hist_gradient_boosting': HistGradientBoostingRegressor(random_state=42)
            }
        elif self.task_type == "classification":
            return {
                'logistic_regression': LogisticRegression(max_iter=1000, random_state=42),
                'ridge_classifier': RidgeClassifier(alpha=1.0),
                'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'extra_trees': ExtraTreesClassifier(n_estimators=100, random_state=42),
                'ada_boost': AdaBoostClassifier(n_estimators=50, random_state=42),
                'mlp': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42),
                'svc': SVC(kernel='rbf', C=1.0, probability=True, random_state=42),
                'knn': KNeighborsClassifier(n_neighbors=5),
                'gaussian_nb': GaussianNB(),
                'gaussian_process': GaussianProcessClassifier(random_state=42),
                'hist_gradient_boosting': HistGradientBoostingClassifier(random_state=42)
            }
        else:
            raise ValueError(f"Unsupported task type: {self.task_type}")

    def evaluate_models(self, X: np.ndarray, y: np.ndarray, 
                       n_top_models: int = 3,
                       scoring_metric: Optional[str] = None) -> Dict[str, ModelPerformance]:
        """
        Evaluate all candidate models
        
        Args:
            X: Feature matrix
            y: Target values
            n_top_models: Number of top models to return
            scoring_metric: Scoring metric (default: r2 for regression, accuracy for classification)
            
        Returns:
            Dictionary of model performances
        """
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available")
            return {}
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determine scoring metric
        if scoring_metric is None:
            scoring_metric = 'r2' if self.task_type == "regression" else 'accuracy'
        
        candidates = self._get_model_candidates()
        logger.info(f"Evaluating {len(candidates)} {self.task_type} models...")
        
        for name, model in candidates.items():
            try:
                start_time = time.time()
                
                # Cross-validation
                scores = cross_val_score(
                    model, X_scaled, y, 
                    cv=self.cv_folds, 
                    scoring=scoring_metric,
                    n_jobs=-1
                )
                
                # Train on full data for timing
                model.fit(X_scaled, y)
                training_time = time.time() - start_time
                
                # Predictions for additional metrics
                y_pred = model.predict(X_scaled)
                
                # Calculate metrics
                if self.task_type == "regression":
                    mse = mean_squared_error(y, y_pred)
                    mae = np.mean(np.abs(y - y_pred))
                    rmse = np.sqrt(mse)
                    r2 = np.mean(scores)
                    
                    perf = ModelPerformance(
                        model_name=name,
                        model_category=self._get_model_category(name),
                        mse=mse,
                        rmse=rmse,
                        mae=mae,
                        r2_score=r2,
                        training_time=training_time,
                        feature_count=X.shape[1],
                        sample_count=len(y)
                    )
                else:
                    accuracy = np.mean(scores)
                    
                    # Additional classification metrics
                    if len(np.unique(y)) == 2:  # Binary classification
                        precision = precision_score(y, y_pred, average='binary', zero_division=0)
                        recall = recall_score(y, y_pred, average='binary', zero_division=0)
                        f1 = f1_score(y, y_pred, average='binary', zero_division=0)
                        try:
                            if hasattr(model, 'predict_proba'):
                                roc_auc = roc_auc_score(y, model.predict_proba(X_scaled)[:, 1])
                            else:
                                roc_auc = None
                        except:
                            roc_auc = None
                    else:
                        precision = precision_score(y, y_pred, average='macro', zero_division=0)
                        recall = recall_score(y, y_pred, average='macro', zero_division=0)
                        f1 = f1_score(y, y_pred, average='macro', zero_division=0)
                        roc_auc = None
                    
                    perf = ModelPerformance(
                        model_name=name,
                        model_category=self._get_model_category(name),
                        accuracy=accuracy,
                        precision=precision,
                        recall=recall,
                        f1_score=f1,
                        roc_auc=roc_auc,
                        training_time=training_time,
                        feature_count=X.shape[1],
                        sample_count=len(y)
                    )
                
                self.model_results[name] = perf
                
                # Track best model
                if self.best_score is None or self._is_better(perf, scoring_metric):
                    self.best_score = self._get_score(perf, scoring_metric)
                    self.best_model = model
                    self.best_model_name = name
                    
            except Exception as e:
                logger.warning(f"Model {name} failed: {e}")
                continue
        
        logger.info(f"Best model: {self.best_model_name} with score: {self.best_score:.4f}")
        return self.model_results

    def _get_model_category(self, model_name: str) -> str:
        """Get model category from name"""
        if any(x in model_name for x in ['linear', 'ridge', 'lasso', 'elastic', 'bayesian', 'logistic']):
            return ModelCategory.LINEAR.value
        elif any(x in model_name for x in ['random_forest', 'gradient_boost', 'extra_trees', 'ada_boost', 'hist_gradient']):
            return ModelCategory.ENSEMBLE.value
        elif 'mlp' in model_name or 'neural' in model_name:
            return ModelCategory.NEURAL_NETWORK.value
        elif 'sv' in model_name:
            return ModelCategory.SVM.value
        elif 'knn' in model_name or 'neighbor' in model_name:
            return ModelCategory.NEIGHBOR_BASED.value
        elif 'gaussian' in model_name or 'nb' in model_name:
            return ModelCategory.PROBABILISTIC.value
        else:
            return "other"

    def _is_better(self, perf: ModelPerformance, metric: str) -> bool:
        """Check if performance is better than current best"""
        score = self._get_score(perf, metric)
        if score is None:
            return False
        if self.best_score is None:
            return True
        return score > self.best_score

    def _get_score(self, perf: ModelPerformance, metric: str) -> Optional[float]:
        """Get score from performance based on metric"""
        metric_map = {
            'r2': perf.r2_score,
            'accuracy': perf.accuracy,
            'f1': perf.f1_score,
            'precision': perf.precision,
            'recall': perf.recall,
            'roc_auc': perf.roc_auc,
            'neg_mse': -perf.mse if perf.mse else None
        }
        return metric_map.get(metric)

    def get_best_model(self):
        """Get the best performing model"""
        return self.best_model

    def get_results_summary(self) -> pd.DataFrame:
        """Get results summary as DataFrame"""
        if not self.model_results:
            return pd.DataFrame()
        
        data = []
        for name, perf in self.model_results.items():
            data.append(asdict(perf) if hasattr(perf, '__dataclass_fields__') else perf.__dict__)
        
        df = pd.DataFrame(data)
        if 'r2_score' in df.columns:
            df = df.sort_values('r2_score', ascending=False)
        elif 'accuracy' in df.columns:
            df = df.sort_values('accuracy', ascending=False)
        
        return df


class HyperparameterOptimizer:
    """
    Advanced hyperparameter optimization with multiple strategies
    """

    def __init__(self, optimization_strategy: str = "bayesian"):
        """
        Initialize optimizer
        
        Args:
            optimization_strategy: Strategy to use (grid, random, bayesian)
        """
        self.strategy = optimization_strategy
        self.best_params = None
        self.best_score = None
        self.optimization_history = []

    def optimize(self, model, X: np.ndarray, y: np.ndarray,
                param_grid: Dict[str, List],
                cv_folds: int = 5,
                scoring: str = 'r2',
                n_iter: int = 50) -> Dict[str, Any]:
        """
        Optimize hyperparameters
        
        Args:
            model: Base model to optimize
            X: Feature matrix
            y: Target values
            param_grid: Parameter grid to search
            cv_folds: Number of CV folds
            scoring: Scoring metric
            n_iter: Number of iterations (for random/bayesian search)
            
        Returns:
            Optimization results
        """
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available")
            return {}
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        if self.strategy == "grid":
            search = GridSearchCV(
                model, param_grid,
                cv=cv_folds,
                scoring=scoring,
                n_jobs=-1,
                verbose=1
            )
        elif self.strategy == "random":
            search = RandomizedSearchCV(
                model, param_grid,
                n_iter=n_iter,
                cv=cv_folds,
                scoring=scoring,
                n_jobs=-1,
                verbose=1
            )
        else:  # bayesian - use randomized as fallback if optuna not available
            try:
                import optuna
                return self._optuna_optimize(model, X_scaled, y, param_grid, scoring, n_iter)
            except ImportError:
                logger.warning("Optuna not available, using random search")
                search = RandomizedSearchCV(
                    model, param_grid,
                    n_iter=n_iter,
                    cv=cv_folds,
                    scoring=scoring,
                    n_jobs=-1,
                    verbose=1
                )
        
        search.fit(X_scaled, y)
        
        self.best_params = search.best_params_
        self.best_score = search.best_score_
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'best_estimator': search.best_estimator_
        }

    def _optuna_optimize(self, model, X, y, param_grid, scoring, n_iter):
        """Optuna-based optimization"""
        import optuna
        
        def objective(trial):
            # Create trial-specific params
            trial_params = {}
            for param_name, param_values in param_grid.items():
                if isinstance(param_values[0], int):
                    trial_params[param_name] = trial.suggest_int(param_name, min(param_values), max(param_values))
                elif isinstance(param_values[0], float):
                    trial_params[param_name] = trial.suggest_float(param_name, min(param_values), max(param_values))
                else:
                    trial_params[param_name] = trial.suggest_categorical(param_name, param_values)
            
            # Create model with trial params
            trial_model = type(model)(**trial_params)
            
            # Cross-validation
            scores = cross_val_score(trial_model, X, y, cv=5, scoring=scoring)
            return np.mean(scores)
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_iter)
        
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        return {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'optimization_history': study.trials_dataframe().to_dict() if hasattr(study, 'trials_dataframe') else []
        }


class EnsembleModelBuilder:
    """
    Advanced ensemble model builder with stacking and voting
    """

    def __init__(self):
        self.ensemble_model = None
        self.base_models = []
        self.meta_model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None

    def create_stacking_ensemble(self, X: np.ndarray, y: np.ndarray,
                                  task_type: str = "regression",
                                  cv_folds: int = 5) -> Any:
        """
        Create stacking ensemble
        
        Args:
            X: Feature matrix
            y: Target values
            task_type: Task type (regression/classification)
            cv_folds: Number of CV folds
            
        Returns:
            Trained stacking ensemble
        """
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available")
            return None
        
        X_scaled = self.scaler.fit_transform(X)
        
        if task_type == "regression":
            self.base_models = [
                ('rf', RandomForestRegressor(n_estimators=100, random_state=42)),
                ('gb', GradientBoostingRegressor(n_estimators=100, random_state=42)),
                ('et', ExtraTreesRegressor(n_estimators=100, random_state=42)),
                ('mlp', MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42))
            ]
            self.meta_model = LinearRegression()
        else:
            self.base_models = [
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42)),
                ('et', ExtraTreesClassifier(n_estimators=100, random_state=42)),
                ('svc', SVC(kernel='rbf', C=1.0, probability=True, random_state=42))
            ]
            self.meta_model = LogisticRegression(max_iter=1000, random_state=42)
        
        self.ensemble_model = StackingRegressor(estimators=self.base_models, final_estimator=self.meta_model, cv=cv_folds) \
            if task_type == "regression" else \
            StackingClassifier(estimators=self.base_models, final_estimator=self.meta_model, cv=cv_folds)
        
        self.ensemble_model.fit(X_scaled, y)
        
        logger.info("Stacking ensemble created successfully")
        return self.ensemble_model

    def create_voting_ensemble(self, X: np.ndarray, y: np.ndarray,
                                task_type: str = "regression",
                                voting: str = 'soft') -> Any:
        """
        Create voting ensemble
        
        Args:
            X: Feature matrix
            y: Target values
            task_type: Task type
            voting: Voting type (soft/hard for classification, average for regression)
            
        Returns:
            Trained voting ensemble
        """
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available")
            return None
        
        X_scaled = self.scaler.fit_transform(X)
        
        if task_type == "regression":
            estimators = [
                ('rf', RandomForestRegressor(n_estimators=100, random_state=42)),
                ('gb', GradientBoostingRegressor(n_estimators=100, random_state=42)),
                ('et', ExtraTreesRegressor(n_estimators=100, random_state=42))
            ]
            self.ensemble_model = VotingRegressor(estimators=estimators)
        else:
            estimators = [
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42)),
                ('svc', SVC(kernel='rbf', C=1.0, probability=True, random_state=42))
            ]
            self.ensemble_model = VotingClassifier(estimators=estimators, voting=voting)
        
        self.ensemble_model.fit(X_scaled, y)
        
        logger.info(f"Voting ensemble created successfully with {voting} voting")
        return self.ensemble_model


# Export classes
__all__ = [
    'AutoMLSelector',
    'HyperparameterOptimizer',
    'EnsembleModelBuilder',
    'ModelPerformance',
    'ModelCategory'
]
