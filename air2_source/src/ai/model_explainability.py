"""
AirOne v4.0 - Model Explainability Module
SHAP-style feature importance and model interpretation
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import logging
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports with fallbacks
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.inspection import permutation_importance
    from sklearn.metrics import r2_score, accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


@dataclass
class FeatureImportance:
    """Feature importance result"""
    feature_name: str
    importance_score: float
    std_dev: Optional[float] = None
    rank: int = 0
    direction: str = "positive"  # positive, negative, mixed
    impact_description: str = ""


@dataclass
class ModelExplanation:
    """Complete model explanation"""
    model_name: str
    model_type: str
    overall_performance: Dict[str, float]
    feature_importances: List[FeatureImportance]
    global_interpretation: str
    local_explanations: Optional[List[Dict]] = None
    recommendations: List[str] = None
    generated_at: str = ""


class ModelExplainer:
    """
    Model explainability using SHAP-style analysis
    
    Provides feature importance, partial dependence, and
    local explanations for model predictions
    """

    def __init__(self, model: Any = None, feature_names: Optional[List[str]] = None):
        self.model = model
        self.feature_names = feature_names or []
        self.training_data = None
        self.training_targets = None
        self.background_data = None
        self.explainer = None
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None,
            background_samples: int = 100):
        """
        Fit explainer with training data
        
        Args:
            X: Training features
            y: Training targets (optional)
            background_samples: Number of background samples
        """
        self.training_data = X
        self.training_targets = y
        
        # Select background data for expectation
        if len(X) > background_samples:
            indices = np.random.choice(len(X), background_samples, replace=False)
            self.background_data = X[indices]
        else:
            self.background_data = X
        
        self.is_fitted = True
        logger.info(f"Explainer fitted with {len(X)} samples")

    def compute_feature_importance(self, X: np.ndarray, y: np.ndarray,
                                   method: str = "permutation",
                                   n_repeats: int = 10) -> List[FeatureImportance]:
        """
        Compute feature importance
        
        Args:
            X: Test features
            y: Test targets
            method: Importance method (permutation, impurity, coefficient)
            n_repeats: Number of permutation repeats
            
        Returns:
            List of FeatureImportance objects
        """
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn required for feature importance")
            return []
        
        if not self.feature_names:
            self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        importances = []
        
        if method == "permutation" and hasattr(self.model, 'score'):
            # Permutation importance
            result = permutation_importance(
                self.model, X, y,
                n_repeats=n_repeats,
                random_state=42,
                n_jobs=-1
            )
            
            for i, (name, imp, std) in enumerate(zip(
                self.feature_names,
                result.importances_mean,
                result.importances_std
            )):
                direction = self._determine_direction(X[:, i], self.model, i)
                importances.append(FeatureImportance(
                    feature_name=name,
                    importance_score=abs(imp),
                    std_dev=std,
                    rank=0,
                    direction=direction,
                    impact_description=self._generate_impact_description(name, abs(imp), direction)
                ))
        
        elif method == "impurity" and hasattr(self.model, 'feature_importances_'):
            # Tree-based impurity
            for i, (name, imp) in enumerate(zip(
                self.feature_names,
                self.model.feature_importances_
            )):
                direction = self._determine_direction(X[:, i], self.model, i)
                importances.append(FeatureImportance(
                    feature_name=name,
                    importance_score=imp,
                    rank=0,
                    direction=direction,
                    impact_description=self._generate_impact_description(name, imp, direction)
                ))
        
        elif method == "coefficient" and hasattr(self.model, 'coef_'):
            # Linear model coefficients
            coefs = self.model.coef_
            if len(coefs.shape) == 1:
                coefs = coefs.reshape(1, -1)
            
            for i, (name, coef) in enumerate(zip(self.feature_names, coefs[0])):
                direction = "positive" if coef > 0 else "negative"
                importances.append(FeatureImportance(
                    feature_name=name,
                    importance_score=abs(coef),
                    rank=0,
                    direction=direction,
                    impact_description=self._generate_impact_description(name, abs(coef), direction)
                ))
        
        # Rank features
        importances.sort(key=lambda x: x.importance_score, reverse=True)
        for i, imp in enumerate(importances):
            imp.rank = i + 1
        
        return importances

    def _determine_direction(self, feature_values: np.ndarray, 
                            model: Any, feature_idx: int) -> str:
        """Determine the direction of feature impact"""
        try:
            # Sample predictions at different feature values
            low_val = np.percentile(feature_values, 25)
            high_val = np.percentile(feature_values, 75)
            
            # Create test samples
            if self.background_data is not None:
                sample = self.background_data[0:1].copy()
            else:
                sample = np.zeros((1, len(self.feature_names)))
            
            sample[0, feature_idx] = low_val
            pred_low = model.predict(sample)[0]
            
            sample[0, feature_idx] = high_val
            pred_high = model.predict(sample)[0]
            
            diff = pred_high - pred_low
            if diff > 0.01:
                return "positive"
            elif diff < -0.01:
                return "negative"
            else:
                return "mixed"
        except:
            return "mixed"

    def _generate_impact_description(self, feature_name: str, 
                                     importance: float, direction: str) -> str:
        """Generate human-readable impact description"""
        if importance < 0.01:
            impact = "minimal"
        elif importance < 0.05:
            impact = "small"
        elif importance < 0.1:
            impact = "moderate"
        elif importance < 0.2:
            impact = "significant"
        else:
            impact = "major"
        
        direction_text = {
            "positive": "increases the prediction",
            "negative": "decreases the prediction",
            "mixed": "has complex effects on the prediction"
        }
        
        return f"{feature_name} has {impact} impact and {direction_text.get(direction, 'affects')} the model output"

    def explain_prediction(self, X: np.ndarray, prediction_idx: int = 0,
                          n_top_features: int = 5) -> Dict[str, Any]:
        """
        Explain a single prediction
        
        Args:
            X: Input features
            prediction_idx: Index of prediction to explain
            
        Returns:
            Explanation dictionary
        """
        if not self.is_fitted:
            raise ValueError("Explainer not fitted")
        
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        
        # Get prediction
        prediction = self.model.predict(X)[prediction_idx]
        
        # Get base value (expected value)
        if self.background_data is not None:
            base_value = np.mean(self.model.predict(self.background_data))
        else:
            base_value = prediction
        
        # Compute SHAP-style values using simplified approach
        shap_values = self._compute_shap_values(X[prediction_idx:prediction_idx+1])
        
        # Get top features
        if not self.feature_names:
            self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        feature_explanations = []
        for i, (name, shap_val) in enumerate(zip(self.feature_names, shap_values[0])):
            feature_explanations.append({
                'feature': name,
                'value': float(X[prediction_idx, i]),
                'shap_value': float(shap_val),
                'impact': 'positive' if shap_val > 0 else 'negative',
                'contribution': float(shap_val)
            })
        
        # Sort by absolute SHAP value
        feature_explanations.sort(key=lambda x: abs(x['shap_value']), reverse=True)
        
        return {
            'prediction': float(prediction),
            'base_value': float(base_value),
            'prediction_explanation': f"Prediction is {prediction - base_value:+.2f} above baseline",
            'top_features': feature_explanations[:n_top_features],
            'all_features': feature_explanations
        }

    def _compute_shap_values(self, X: np.ndarray) -> np.ndarray:
        """
        Compute SHAP-style values using sampling approach
        
        This is a simplified implementation that approximates SHAP values
        """
        n_samples, n_features = X.shape
        shap_values = np.zeros((n_samples, n_features))
        
        if self.background_data is None:
            return shap_values
        
        # Get baseline prediction
        baseline_pred = np.mean(self.model.predict(self.background_data))
        
        # For each feature, estimate its contribution
        for i in range(n_features):
            # Create perturbed samples
            perturbed = X.copy()
            
            # Replace feature with background values
            background_indices = np.random.choice(
                len(self.background_data), 
                n_samples,
                replace=True
            )
            perturbed[:, i] = self.background_data[background_indices, i]
            
            # Get predictions with perturbed feature
            perturbed_preds = self.model.predict(perturbed)
            
            # SHAP value is the difference
            original_preds = self.model.predict(X)
            shap_values[:, i] = original_preds - perturbed_preds
        
        # Normalize to sum to prediction - baseline
        for i in range(n_samples):
            current_sum = np.sum(shap_values[i])
            target = self.model.predict(X[i:i+1])[0] - baseline_pred
            if abs(current_sum) > 1e-10:
                shap_values[i] *= target / current_sum
        
        return shap_values

    def generate_partial_dependence(self, X: np.ndarray, 
                                    features: Optional[List[int]] = None,
                                    n_points: int = 50) -> Dict[str, List]:
        """
        Generate partial dependence plots data
        
        Args:
            X: Input data
            features: Features to analyze (all if None)
            n_points: Number of points for grid
            
        Returns:
            Dictionary with partial dependence data
        """
        if features is None:
            features = list(range(X.shape[1]))
        
        results = {}
        
        for feat_idx in features:
            feat_name = self.feature_names[feat_idx] if self.feature_names else f"feature_{feat_idx}"
            
            # Get feature range
            feat_min, feat_max = np.percentile(X[:, feat_idx], [5, 95])
            feat_values = np.linspace(feat_min, feat_max, n_points)
            
            pd_values = []
            for val in feat_values:
                # Create samples with fixed feature value
                samples = X.copy()
                samples[:, feat_idx] = val
                
                # Average prediction
                preds = self.model.predict(samples)
                pd_values.append(np.mean(preds))
            
            results[feat_name] = {
                'values': feat_values.tolist(),
                'partial_dependence': pd_values
            }
        
        return results

    def generate_full_explanation(self, X_test: np.ndarray, y_test: np.ndarray,
                                  model_name: str = "Model",
                                  model_type: str = "unknown") -> ModelExplanation:
        """
        Generate comprehensive model explanation
        
        Args:
            X_test: Test features
            y_test: Test targets
            model_name: Name of the model
            model_type: Type of model
            
        Returns:
            Complete ModelExplanation object
        """
        # Compute performance metrics
        y_pred = self.model.predict(X_test)
        
        if hasattr(self.model, 'predict_proba'):
            y_proba = self.model.predict_proba(X_test)
            performance = {
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'r2_score': float(r2_score(y_test, y_pred)) if len(np.unique(y_test)) > 2 else None
            }
        else:
            performance = {
                'mse': float(np.mean((y_test - y_pred) ** 2)),
                'rmse': float(np.sqrt(np.mean((y_test - y_pred) ** 2))),
                'r2_score': float(r2_score(y_test, y_pred))
            }
        
        # Compute feature importances
        feature_importances = self.compute_feature_importance(X_test, y_test)
        
        # Generate global interpretation
        if feature_importances:
            top_feature = feature_importances[0]
            global_interp = (
                f"The model is primarily driven by '{top_feature.feature_name}' "
                f"with importance score of {top_feature.importance_score:.4f}. "
                f"Top 3 features account for majority of predictive power."
            )
        else:
            global_interp = "Feature importance analysis not available."
        
        # Generate recommendations
        recommendations = self._generate_recommendations(feature_importances, performance)
        
        return ModelExplanation(
            model_name=model_name,
            model_type=model_type,
            overall_performance=performance,
            feature_importances=feature_importances,
            global_interpretation=global_interp,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )

    def _generate_recommendations(self, importances: List[FeatureImportance],
                                  performance: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Feature-based recommendations
        if importances:
            low_importance = [f for f in importances if f.importance_score < 0.01]
            if len(low_importance) > len(importances) * 0.3:
                recommendations.append(
                    "Consider removing low-importance features to reduce model complexity"
                )
            
            high_importance = [f for f in importances if f.importance_score > 0.2]
            if high_importance:
                recommendations.append(
                    f"Focus on improving '{high_importance[0].feature_name}' data quality for better predictions"
                )
        
        # Performance-based recommendations
        r2 = performance.get('r2_score')
        if r2 is not None:
            if r2 < 0.5:
                recommendations.append(
                    "Model performance is low. Consider adding more features or trying different algorithms"
                )
            elif r2 > 0.9:
                recommendations.append(
                    "Excellent performance. Validate on held-out data to check for overfitting"
                )
        
        return recommendations


class AirOneModelInterpreter:
    """
    High-level interpreter for AirOne AI/ML models
    
    Provides user-friendly explanations and visualizations
    """

    def __init__(self):
        self.explainers: Dict[str, ModelExplainer] = {}
        self.explanation_history: List[ModelExplanation] = []

    def register_model(self, model_id: str, model: Any,
                      feature_names: List[str],
                      X_train: np.ndarray, y_train: Optional[np.ndarray] = None):
        """
        Register a model for interpretation
        
        Args:
            model_id: Unique model identifier
            model: Trained model
            feature_names: Names of features
            X_train: Training data
            y_train: Training targets
        """
        explainer = ModelExplainer(model, feature_names)
        explainer.fit(X_train, y_train)
        self.explainers[model_id] = explainer
        
        logger.info(f"Model '{model_id}' registered for interpretation")

    def explain_model(self, model_id: str, X_test: np.ndarray, 
                     y_test: np.ndarray) -> Optional[ModelExplanation]:
        """
        Generate explanation for registered model
        
        Args:
            model_id: Model identifier
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Model explanation
        """
        if model_id not in self.explainers:
            logger.error(f"Model '{model_id}' not registered")
            return None
        
        explainer = self.explainers[model_id]
        explanation = explainer.generate_full_explanation(X_test, y_test, model_id, "registered")
        
        self.explanation_history.append(explanation)
        return explanation

    def explain_prediction(self, model_id: str, X: np.ndarray) -> Optional[Dict]:
        """Explain a single prediction"""
        if model_id not in self.explainers:
            return None
        
        return self.explainers[model_id].explain_prediction(X)

    def get_feature_ranking(self, model_id: str) -> Optional[List[FeatureImportance]]:
        """Get feature importance ranking for a model"""
        if model_id not in self.explainers:
            return None
        
        explainer = self.explainers[model_id]
        if explainer.training_data is not None and explainer.training_targets is not None:
            return explainer.compute_feature_importance(
                explainer.training_data,
                explainer.training_targets
            )
        return None


__all__ = [
    'ModelExplainer',
    'AirOneModelInterpreter',
    'FeatureImportance',
    'ModelExplanation'
]
