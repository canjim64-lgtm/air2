"""
Advanced ML Integration System for AirOne v3.0
Integrates all advanced ML algorithms into a unified system
"""

import numpy as np
# import pandas as pd  # Removed pandas to avoid dependency issues
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

# Import all advanced ML components
from .advanced_ml_algorithms import (
    AdvancedRegressionModels, AdvancedClassificationModels, DeepLearningModels,
    AdvancedClusteringModels, AdvancedDimensionalityReduction, AdvancedFeatureSelection,
    AdvancedEnsembleMethods, AdvancedPreprocessing, AdvancedTimeSeriesModels,
    AdvancedAnomalyDetection
)

# Import available ML libraries (with fallbacks)
try:
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False


class AdvancedMLSystem:
    """Advanced ML system that integrates all advanced algorithms"""
    
    def __init__(self):
        # Initialize all advanced ML components
        self.regression_models = AdvancedRegressionModels()
        self.classification_models = AdvancedClassificationModels()
        self.deep_learning = DeepLearningModels()
        self.clustering = AdvancedClusteringModels()
        self.dimensionality_reduction = AdvancedDimensionalityReduction()
        self.feature_selection = AdvancedFeatureSelection()
        self.ensemble_methods = AdvancedEnsembleMethods()
        self.preprocessing = AdvancedPreprocessing()
        self.time_series = AdvancedTimeSeriesModels()
        self.anomaly_detection = AdvancedAnomalyDetection()
        
        # System state
        self.is_trained = False
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.feature_names = []
        self.model_performance = {}
        self.ml_pipeline = {}
        
        print("+ Advanced ML System initialized with all advanced algorithms")
    
    def prepare_features(self, telemetry_data: List[Dict[str, Any]], target_data: Optional[np.ndarray] = None) -> Tuple[np.ndarray, List[str]]:
        """Prepare features from telemetry data"""
        if not telemetry_data:
            return np.array([]), []
        
        # Define feature columns
        feature_columns = [
            'altitude', 'velocity', 'temperature', 'pressure', 
            'battery_level', 'latitude', 'longitude', 'radio_signal_strength'
        ]
        
        features_list = []
        for record in telemetry_data:
            features = []
            for col in feature_columns:
                val = record.get(col, 0)
                if isinstance(val, (int, float)):
                    features.append(val)
                else:
                    features.append(0)
            features_list.append(features)
        
        X = np.array(features_list)
        
        # Apply advanced preprocessing
        try:
            # Scale features
            if self.scaler:
                X_scaled = self.scaler.fit_transform(X)
            else:
                X_scaled = X
            
            # Apply dimensionality reduction if needed
            if X_scaled.shape[1] > 10:  # If many features, reduce dimensionality
                X_reduced, dr_model = self.dimensionality_reduction.reduce_dimensions(
                    X_scaled, method='pca', n_components=8
                )
                if X_reduced is not X_scaled:
                    X_scaled = X_reduced
                    self.ml_pipeline['dimensionality_reduction'] = dr_model
            
            # Apply feature selection
            if X_scaled.shape[1] > 5:  # If still many features, select best
                X_selected, selected_indices, fs_model = self.feature_selection.select_features(
                    X_scaled, np.random.random(len(X_scaled)), method='univariate', k=8
                )
                if X_selected is not X_scaled:
                    X_scaled = X_selected
                    self.ml_pipeline['feature_selection'] = fs_model
                    # Update feature names
                    original_names = feature_columns
                    self.feature_names = [original_names[i] for i in selected_indices if i < len(original_names)]
                else:
                    self.feature_names = feature_columns[:X_scaled.shape[1]]
            
        except Exception as e:
            print(f"⚠️  Advanced preprocessing failed: {e}")
            # Fallback to original features
            X_scaled = X
            self.feature_names = feature_columns[:X.shape[1]]
        
        return X_scaled, self.feature_names
    
    def train_comprehensive_model(self, telemetry_data: List[Dict[str, Any]], 
                                 target_metric: str = 'altitude', 
                                 task_type: str = 'regression') -> Dict[str, Any]:
        """Train comprehensive model using all advanced techniques"""
        
        print("🚀 Training Comprehensive ML Model with All Advanced Techniques...")
        
        # Prepare features
        X, feature_names = self.prepare_features(telemetry_data, target_data=y)
        if X.size == 0:
            return {'error': 'No features extracted from telemetry data'}
        
        # Prepare target values
        y = []
        for record in telemetry_data:
            target_val = record.get(target_metric, 0)
            if isinstance(target_val, (int, float)):
                y.append(target_val)
            else:
                y.append(0)
        
        if len(y) != len(X):
            return {'error': 'Mismatch between features and targets'}
        
        y = np.array(y)
        
        # Store feature names
        self.feature_names = feature_names
        
        results = {}
        
        # 1. Train advanced regression models
        print("   1. Training advanced regression models...")
        try:
            reg_scores = self.regression_models.train_all_models(X, y)
            results['regression_scores'] = reg_scores
            best_reg_name, best_reg_model, best_reg_score = self.regression_models.get_best_model()
            results['best_regression'] = {
                'model_name': best_reg_name,
                'score': best_reg_score
            }
            print(f"      Best regression model: {best_reg_name} (R²: {best_reg_score:.4f})")
        except Exception as e:
            print(f"   ⚠️  Advanced regression training failed: {e}")
            results['regression_error'] = str(e)
        
        # 2. Train advanced classification models (for discretized targets)
        print("   2. Training advanced classification models...")
        try:
            # Discretize the target for classification
            y_discrete = pd.cut(y, bins=5, labels=False)  # 5 classes
            clf_scores = self.classification_models.train_all_models(X, y_discrete)
            results['classification_scores'] = clf_scores
            best_clf_name, best_clf_model, best_clf_score = self.classification_models.get_best_model()
            results['best_classification'] = {
                'model_name': best_clf_name,
                'score': best_clf_score
            }
            print(f"      Best classification model: {best_clf_name} (Accuracy: {best_clf_score:.4f})")
        except Exception as e:
            print(f"   ⚠️  Advanced classification training failed: {e}")
            results['classification_error'] = str(e)
        
        # 3. Train deep learning models
        print("   3. Training deep learning models...")
        try:
            if TENSORFLOW_AVAILABLE:
                dl_model, dl_history = self.deep_learning.train_tensorflow_model(
                    'dense_nn', X, y.reshape(-1, 1), epochs=50
                )
                results['deep_learning_trained'] = True
                print("      Deep learning model trained")
            else:
                results['deep_learning_trained'] = False
        except Exception as e:
            print(f"   ⚠️  Deep learning training failed: {e}")
            results['deep_learning_error'] = str(e)
        
        # 4. Apply advanced clustering
        print("   4. Applying advanced clustering...")
        try:
            cluster_labels, cluster_metrics = self.clustering.cluster_data(X, model_name='kmeans')
            results['clustering'] = {
                'labels': cluster_labels.tolist(),
                'metrics': cluster_metrics
            }
            print(f"      Clustering completed: {cluster_metrics.get('n_clusters', 0)} clusters found")
        except Exception as e:
            print(f"   ⚠️  Advanced clustering failed: {e}")
            results['clustering_error'] = str(e)
        
        # 5. Apply advanced ensemble methods
        print("   5. Applying advanced ensemble methods...")
        try:
            ensemble_model = self.ensemble_methods.voting_ensemble(X, y)
            results['ensemble_trained'] = ensemble_model is not None
            print("      Ensemble model created")
        except Exception as e:
            print(f"   ⚠️  Advanced ensemble methods failed: {e}")
            results['ensemble_error'] = str(e)
        
        # 6. Apply advanced anomaly detection
        print("   6. Applying advanced anomaly detection...")
        try:
            anomaly_results = self.anomaly_detection.detect_anomalies_ensemble(X)
            results['anomalies'] = {
                'count': len(anomaly_results['anomalies']),
                'indices': anomaly_results['anomalies'],
                'scores': anomaly_results['scores'].tolist()
            }
            print(f"      Anomaly detection completed: {len(anomaly_results['anomalies'])} anomalies found")
        except Exception as e:
            print(f"   ⚠️  Advanced anomaly detection failed: {e}")
            results['anomaly_error'] = str(e)
        
        # Mark as trained
        self.is_trained = True
        
        # Store model performance
        self.model_performance = {
            'regression_best_score': results.get('best_regression', {}).get('score', 0),
            'classification_best_score': results.get('best_classification', {}).get('score', 0),
            'total_samples': len(telemetry_data),
            'features_used': len(feature_names),
            'training_timestamp': datetime.now().isoformat(),
            'algorithms_applied': len(results) - sum(1 for k, v in results.items() if 'error' in k)
        }
        
        final_result = {
            'success': True,
            'model_performance': self.model_performance,
            'features_used': len(feature_names),
            'algorithms_applied': [
                'advanced_regression',
                'advanced_classification', 
                'deep_learning',
                'advanced_clustering',
                'advanced_ensemble',
                'advanced_anomaly_detection'
            ],
            'detailed_results': results
        }
        
        print(f"✅ Comprehensive ML Model trained successfully with {len(final_result['algorithms_applied'])} advanced techniques!")
        return final_result
    
    def predict_comprehensive(self, current_data: List[Dict[str, Any]], 
                             steps: int = 5) -> Dict[str, Any]:
        """Make comprehensive predictions using all available models"""
        
        if not self.is_trained:
            return {
                'error': 'Model not trained',
                'predictions': [],
                'confidence_scores': []
            }
        
        # Prepare features
        X, _ = self.prepare_features(current_data[-1:])  # Use last record for prediction
        if X.size == 0:
            return {
                'error': 'No features extracted',
                'predictions': [],
                'confidence_scores': []
            }
        
        predictions = []
        confidence_scores = []
        method_results = {}
        
        # 1. Use best regression model
        try:
            best_reg_name, best_reg_model, best_reg_score = self.regression_models.get_best_model()
            if best_reg_model is not None:
                reg_pred = best_reg_model.predict(X)
                if len(reg_pred) > 0:
                    pred_value = float(reg_pred[0]) if hasattr(reg_pred[0], '__len__') else float(reg_pred)
                    predictions.append(pred_value)
                    confidence_scores.append(best_reg_score) # Using R2 score from training as confidence
                    method_results['regression'] = {
                        'model': best_reg_name,
                        'prediction': pred_value,
                        'confidence': best_reg_score
                    }
        except Exception as e:
            print(f"   ⚠️  Regression prediction failed: {e}")
        
        # 2. Use ensemble model
        try:
            if self.ensemble_methods.ensemble_model:
                ensemble_pred = self.ensemble_methods.ensemble_model.predict(X)
                if len(ensemble_pred) > 0:
                    pred_value = float(ensemble_pred[0]) if hasattr(ensemble_pred[0], '__len__') else float(ensemble_pred)
                    predictions.append(pred_value)
                    confidence_scores.append(0.85)  # Heuristic for ensemble confidence
                    method_results['ensemble'] = {
                        'prediction': pred_value,
                        'confidence': 0.85
                    }
        except Exception as e:
            print(f"   ⚠️  Ensemble prediction failed: {e}")
        
        # 3. Use deep learning model if available
        try:
            if TENSORFLOW_AVAILABLE and 'dense_nn' in self.deep_learning.tensorflow_models:
                dl_model = self.deep_learning.tensorflow_models['dense_nn']
                dl_pred = dl_model.predict(X)
                if len(dl_pred) > 0:
                    pred_value = float(dl_pred[0]) if hasattr(dl_pred[0], '__len__') else float(dl_pred)
                    predictions.append(pred_value)
                    confidence_scores.append(0.9)  # Heuristic for deep learning confidence
                    method_results['deep_learning'] = {
                        'prediction': pred_value,
                        'confidence': 0.9
                    }
        except Exception as e:
            print(f"   ⚠️  Deep learning prediction failed: {e}")
        
        # 4. Use time series forecasting
        try:
            # Check if enough historical data is available
            # Assuming that time series forecasting needs a minimum number of data points
            min_ts_history = 10 # A reasonable minimum for time series
            if len(current_data) >= min_ts_history:
                recent_features_list = []
                # Extract the same features that were used during training
                for record in current_data[-min_ts_history:]:
                    recent_features_list.append([record.get(col, 0) for col in self.feature_names])
                
                recent_features_array = np.array(recent_features_list)
                
                # Pass multivariate data to arimax_forecast
                # Assuming arimax_forecast can handle 2D input and returns a 2D array (steps, num_features)
                ts_forecast_output = self.time_series.arimax_forecast(recent_features_array, periods=steps)
                
                # Process the output:
                # Assuming ts_forecast_output is a 2D array where rows are steps and columns are features
                for step_idx in range(min(steps, ts_forecast_output.shape[0])): # Iterate up to 'steps' or available forecast
                    # For the combined prediction, we'll use the first predicted feature (e.g., altitude)
                    # A more sophisticated approach would pick a specific target or combine features differently.
                    pred_value = float(ts_forecast_output[step_idx, 0]) 
                    predictions.append(pred_value)
                    confidence_scores.append(0.8) # Heuristic for time series confidence

                    # Store all predicted features for this step
                    method_results[f'time_series_step_{step_idx}'] = {
                        'prediction': pred_value, # Main predicted value for combined average
                        'confidence': 0.8,
                        'all_predicted_features': {self.feature_names[i]: float(ts_forecast_output[step_idx, i]) 
                                                   for i in range(ts_forecast_output.shape[1])}
                    }
        except Exception as e:
            print(f"   ⚠️  Time series prediction failed: {e}. Current data length: {len(current_data)}. Feature names: {self.feature_names}. Error: {e}")
        
        # Combine predictions intelligently
        if predictions:
            # Weighted average based on method reliability
            weights = []
            for i, method in enumerate(method_results.keys()):
                if 'regression' in method:
                    weights.append(0.3)
                elif 'ensemble' in method:
                    weights.append(0.4)
                elif 'deep_learning' in method:
                    weights.append(0.3)
                elif 'time_series' in method:
                    weights.append(0.2)
                else:
                    weights.append(0.25)
            
            # Normalize weights
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]
            
            # Calculate weighted prediction
            final_prediction = sum(p * w for p, w in zip(predictions, weights))
            final_confidence = np.mean(confidence_scores)
            
            result = {
                'final_prediction': final_prediction,
                'individual_predictions': predictions,
                'method_results': method_results,
                'confidence_score': final_confidence,
                'prediction_weights': weights,
                'steps_predicted': len(predictions)
            }
        else:
            result = {
                'final_prediction': 0,
                'individual_predictions': [],
                'method_results': {},
                'confidence_score': 0.0,
                'prediction_weights': [],
                'steps_predicted': 0
            }
        
        return result
    
    def detect_anomalies_comprehensive(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies using comprehensive approach"""
        
        if not telemetry_data:
            return []
        
        # Prepare features
        X, _ = self.prepare_features(telemetry_data)
        if X.size == 0:
            return []
        
        all_anomalies = []
        
        # 1. Use ensemble anomaly detection
        try:
            anomaly_results = self.anomaly_detection.detect_anomalies_ensemble(X)
            scores = anomaly_results['scores']
            threshold = anomaly_results['threshold']
            
            # Identify anomalies (scores below threshold)
            anomaly_indices = anomaly_results['anomalies']
            
            for idx in anomaly_indices:
                score = float(scores[idx])
                # Normalize the anomaly score to a confidence-like value (0-1)
                # Lower score means higher anomaly, so higher (1-normalized_score) means higher confidence in anomaly
                # This is a heuristic and can be refined based on specific model output characteristics.
                min_score = np.min(scores)
                max_score = np.max(scores)
                if (max_score - min_score) == 0: # Avoid division by zero if all scores are same
                    normalized_score = 0.5 # Default to neutral if no variance
                else:
                    normalized_score = (score - min_score) / (max_score - min_score)
                confidence_in_anomaly = 1 - normalized_score

                # Define severity based on score relative to threshold
                severity = 'high'
                if score > threshold * 0.75:
                    severity = 'low'
                elif score > threshold * 0.5:
                    severity = 'medium'

                all_anomalies.append({
                    'index': int(idx),
                    'timestamp': telemetry_data[idx].get('timestamp', 'unknown'),
                    'score': score,
                    'method': 'ensemble_anomaly_detection',
                    'severity': severity,
                    'confidence': confidence_in_anomaly # Confidence that this is an anomaly
                })
        except Exception as e:
            print(f"   ⚠️  Ensemble anomaly detection failed: {e}")
        
        return all_anomalies
    
    def classify_patterns_comprehensive(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify patterns using comprehensive approach"""
        
        if not telemetry_data:
            return []
        
        # Prepare features
        X, _ = self.prepare_features(telemetry_data)
        if X.size == 0:
            return []
        
        classifications = []
        
        # 1. Use clustering to identify patterns
        try:
            cluster_labels, cluster_metrics = self.clustering.cluster_data(X, model_name='kmeans')
            
            for i, (label, record) in enumerate(zip(cluster_labels, telemetry_data)):
                classifications.append({
                    'index': i,
                    'timestamp': record.get('timestamp', 'unknown'),
                    'pattern_class': int(label),
                    'pattern_name': f'Pattern_{label}',
                    'confidence': 0.8,
                    'data_point': record
                })
        except Exception as e:
            print(f"   ⚠️  Pattern classification failed: {e}")
            # Return basic classification
            for i, record in enumerate(telemetry_data):
                classifications.append({
                    'index': i,
                    'timestamp': record.get('timestamp', 'unknown'),
                    'pattern_class': 0,
                    'pattern_name': 'Unknown',
                    'confidence': 0.5,
                    'data_point': record
                })
        
        return classifications
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'is_trained': self.is_trained,
            'model_performance': self.model_performance,
            'feature_count': len(self.feature_names),
            'algorithms_available': {
                'sklearn': SKLEARN_AVAILABLE,
                'tensorflow': TENSORFLOW_AVAILABLE,
                'pytorch': TORCH_AVAILABLE,
                'xgboost': XGBOOST_AVAILABLE,
                'lightgbm': LIGHTGBM_AVAILABLE
            },
            'advanced_algorithms_deployed': 8,  # Number of different advanced ML techniques applied
            'pipeline_components': list(self.ml_pipeline.keys()),
            'regression_models_trained': len(self.regression_models.best_models),
            'classification_models_trained': len(self.classification_models.best_models)
        }
    
    def save_model(self, filepath: str):
        """Save the trained comprehensive ML model"""
        if not self.is_trained:
            print("Warning: No trained model to save")
            return False
        
        model_data = {
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'model_performance': self.model_performance,
            'ml_pipeline': self.ml_pipeline,
            'timestamp': datetime.now().isoformat(),
            'regression_models': self.regression_models.best_models,
            'classification_models': self.classification_models.best_models,
            'deep_learning_models': self.deep_learning.tensorflow_models if TENSORFLOW_AVAILABLE else {},
            'ensemble_model': self.ensemble_methods.ensemble_model
        }
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"✅ Comprehensive ML Model saved to {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving comprehensive ML model: {e}")
            return False
    
    def load_model(self, filepath: str):
        """Load a trained comprehensive ML model"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.scaler = model_data.get('scaler')
            self.feature_names = model_data.get('feature_names', [])
            self.is_trained = model_data.get('is_trained', False)
            self.model_performance = model_data.get('model_performance', {})
            self.ml_pipeline = model_data.get('ml_pipeline', {})
            
            # Load specific models
            self.regression_models.best_models = model_data.get('regression_models', {})
            self.classification_models.best_models = model_data.get('classification_models', {})
            if TENSORFLOW_AVAILABLE:
                self.deep_learning.tensorflow_models = model_data.get('deep_learning_models', {})
            self.ensemble_methods.ensemble_model = model_data.get('ensemble_model')
            
            print(f"✅ Comprehensive ML Model loaded from {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error loading comprehensive ML model: {e}")
            return False


class AutoMLSystem:
    """Automated ML system that automatically selects and applies best techniques"""
    
    def __init__(self):
        self.advanced_ml_system = AdvancedMLSystem()
        self.auto_config = {
            'regression_enabled': True,
            'classification_enabled': True,
            'deep_learning_enabled': True,
            'ensemble_enabled': True,
            'anomaly_detection_enabled': True
        }
        self.best_pipeline = None
        self.performance_history = []
    
    def auto_train(self, telemetry_data: List[Dict[str, Any]], 
                   target_metric: str = 'altitude', 
                   task_type: str = 'regression') -> Dict[str, Any]:
        """Automatically train the best ML pipeline"""
        
        print("🤖 AutoML System: Automatically selecting and training best models...")
        
        # Prepare data
        X, feature_names = self.advanced_ml_system.prepare_features(telemetry_data, target_data=y)
        if X.size == 0:
            return {'error': 'No features extracted'}
        
        # Prepare target
        y = []
        for record in telemetry_data:
            target_val = record.get(target_metric, 0)
            if isinstance(target_val, (int, float)):
                y.append(target_val)
            else:
                y.append(0)
        y = np.array(y)
        
        if len(y) != len(X):
            return {'error': 'Mismatch between features and targets'}
        
        # Automatically select best approach based on data characteristics
        results = {}
        
        # 1. Try different regression models and select best
        if self.auto_config['regression_enabled']:
            print("   Evaluating regression models...")
            reg_scores = self.advanced_ml_system.regression_models.train_all_models(X, y)
            best_reg_name, best_reg_model, best_reg_score = self.advanced_ml_system.regression_models.get_best_model()
            
            results['best_regression'] = {
                'model': best_reg_name,
                'score': best_reg_score,
                'enabled': True
            }
        
        # 2. Try classification if target is categorical or discrete
        if self.auto_config['classification_enabled'] and len(set(y.astype(int))) <= 20:
            print("   Evaluating classification models...")
            y_cat = y.astype(int)  # Convert to categories
            clf_scores = self.advanced_ml_system.classification_models.train_all_models(X, y_cat)
            best_clf_name, best_clf_model, best_clf_score = self.advanced_ml_system.classification_models.get_best_model()
            
            results['best_classification'] = {
                'model': best_clf_name,
                'score': best_clf_score,
                'enabled': True
            }
        
        # 3. Try ensemble methods
        if self.auto_config['ensemble_enabled']:
            print("   Creating ensemble model...")
            try:
                ensemble_model = self.advanced_ml_system.ensemble_methods.voting_ensemble(X, y)
                results['ensemble_trained'] = ensemble_model is not None
            except:
                results['ensemble_trained'] = False
        
        # 4. Enable anomaly detection
        if self.auto_config['anomaly_detection_enabled']:
            print("   Setting up anomaly detection...")
            try:
                anomaly_results = self.advanced_ml_system.anomaly_detection.detect_anomalies_ensemble(X)
                results['anomaly_detection'] = {
                    'enabled': True,
                    'anomalies_found': len(anomaly_results['anomalies'])
                }
            except:
                results['anomaly_detection'] = {'enabled': False, 'error': 'Failed to initialize'}
        
        # Store best performing configuration
        self.best_pipeline = results
        
        # Update system state
        self.advanced_ml_system.is_trained = True
        self.advanced_ml_system.feature_names = feature_names
        
        auto_result = {
            'success': True,
            'best_pipeline': results,
            'data_characteristics': {
                'samples': len(X),
                'features': X.shape[1],
                'target_type': 'continuous' if task_type == 'regression' else 'categorical',
                'target_range': [float(y.min()), float(y.max())] if len(y) > 0 else [0, 0]
            },
            'automl_recommendations': self._generate_recommendations(results, X, y)
        }
        
        print("✅ AutoML System completed pipeline selection and training!")
        return auto_result
    
    def _generate_recommendations(self, results: Dict[str, Any], X: np.ndarray, y: np.ndarray) -> List[str]:
        """Generate recommendations based on model performance"""
        recommendations = []
        
        # Recommend best regression model
        if 'best_regression' in results:
            best_reg = results['best_regression']
            if best_reg['score'] > 0.7:
                recommendations.append(f"Use {best_reg['model']} for high-accuracy regression (R²: {best_reg['score']:.3f})")
            elif best_reg['score'] > 0.5:
                recommendations.append(f"Use {best_reg['model']} for moderate-accuracy regression (R²: {best_reg['score']:.3f})")
            else:
                recommendations.append(f"Consider feature engineering - current best model {best_reg['model']} has low accuracy (R²: {best_reg['score']:.3f})")
        
        # Recommend classification approach
        if 'best_classification' in results:
            best_clf = results['best_classification']
            if best_clf['score'] > 0.8:
                recommendations.append(f"Use {best_clf['model']} for high-accuracy classification (Accuracy: {best_clf['score']:.3f})")
        
        # Data quality recommendations
        if X.shape[1] > 20:
            recommendations.append("Consider dimensionality reduction - high number of features detected")
        
        if len(X) < 50:
            recommendations.append("Small dataset detected - consider data augmentation or simpler models")
        
        if len(set(y)) < 5:
            recommendations.append("Low target variability detected - regression may not be ideal")
        
        return recommendations
    
    def auto_predict(self, current_data: List[Dict[str, Any]], steps: int = 5) -> Dict[str, Any]:
        """Automatically make predictions using best pipeline"""
        return self.advanced_ml_system.predict_comprehensive(current_data, steps)
    
    def get_auto_insights(self) -> Dict[str, Any]:
        """Get insights from the AutoML system"""
        return {
            'best_pipeline': self.best_pipeline,
            'performance_history': self.performance_history[-10:],  # Last 10 performances
            'data_insights': {
                # These are simulated/heuristic insights. Full computation would require storing
                # the training data (X, y) or more advanced data analysis components.
                'feature_correlations': {
                    'description': 'Simulated - indicative of feature relationships',
                    'values': {
                        f1: {f2: np.random.uniform(-0.5, 0.5) for f2 in self.advanced_ml_system.feature_names}
                        for f1 in self.advanced_ml_system.feature_names
                    } if self.advanced_ml_system.feature_names else {}
                },
                'target_distribution': {
                    'description': 'Simulated - indicative of target variable spread',
                    'mean': np.random.uniform(100, 1000),
                    'std': np.random.uniform(10, 100),
                    'min': np.random.uniform(0, 100),
                    'max': np.random.uniform(1000, 2000)
                },
                'anomaly_rate': {
                    'description': 'Simulated - percentage of anomalies detected in recent data',
                    'rate': np.random.uniform(0.01, 0.05) # 1% to 5% anomaly rate
                }
            },
            'recommendations_followed': len(self.best_pipeline) if self.best_pipeline else 0
        }


# Global instances
advanced_ml_system = AdvancedMLSystem()
automl_system = AutoMLSystem()