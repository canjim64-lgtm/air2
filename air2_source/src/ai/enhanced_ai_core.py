"""
Enhanced AI System for AirOne v3.0
Integrates multiple AI frameworks and algorithms for superior performance
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import pickle
import os
from dataclasses import dataclass

# Import the fusion system
from .advanced_ai_fusion import AdvancedAIFusion, EnsembleAI

# Import available ML libraries (with fallbacks)
try:
    from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score, classification_report
    from sklearn.linear_model import LinearRegression
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    import torch
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


@dataclass
class AIPredictionResult:
    """Structure for AI prediction results"""
    predicted_values: List[float]
    confidence_scores: List[float]
    model_contributions: Dict[str, float]
    execution_time: float
    framework_used: str


class MultiFrameworkAISystem:
    """Main AI system that combines multiple frameworks and algorithms"""
    
    def __init__(self):
        self.advanced_fusion = AdvancedAIFusion()
        self.ensemble_ai = EnsembleAI()
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.feature_names = []
        self.is_trained = False
        self.model_history = []
        self.performance_metrics = {}
        
        # Initialize framework-specific models
        self._init_framework_models()
        
        # Train a default phase classification ensemble
        self._train_phase_classifier_ensemble()
    
    def _init_framework_models(self):
        """Initialize models from different frameworks"""
        self.framework_models = {
            'sklearn': {},
            'xgboost': {},
            'lightgbm': {},
            'tensorflow': {},
            'pytorch': {},
            'ensemble': {}
        }
        if SKLEARN_AVAILABLE:
            self.mission_phase_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
        else:
            self.mission_phase_classifier = None
    
    def _train_phase_classifier_ensemble(self):
        """Train a simple ensemble classifier for mission phase prediction using synthetic data."""
        if not SKLEARN_AVAILABLE or self.mission_phase_classifier is None:
            return
        
        # Generate synthetic data for mission phases
        # Features: altitude, velocity, temperature, pressure, battery_level, latitude, longitude, radio_signal_strength
        # Target: phase (0-7 as defined in _get_phase_name)
        
        num_samples = 1000
        synthetic_telemetry = []
        for _ in range(num_samples):
            altitude = np.random.uniform(0, 7000)
            velocity = np.random.uniform(-20, 150)
            temperature = np.random.uniform(-30, 80)
            pressure = np.random.uniform(50000, 101325)
            battery_level = np.random.uniform(0, 100)
            latitude = np.random.uniform(-90, 90)
            longitude = np.random.uniform(-180, 180)
            radio_signal_strength = np.random.uniform(0, 100)
            
            synthetic_telemetry.append({
                'altitude': altitude, 'velocity': velocity, 'temperature': temperature, 'pressure': pressure,
                'battery_level': battery_level, 'latitude': latitude, 'longitude': longitude, 'radio_signal_strength': radio_signal_strength
            })
        
        X_synthetic, _ = self.prepare_features(synthetic_telemetry)
        y_synthetic = []
        
        # Assign phases based on the existing _get_phase_name logic for synthetic data
        for record in synthetic_telemetry:
            altitude = record.get('altitude', 0)
            velocity = record.get('velocity', 0)
            if altitude < 500 and velocity < 10: phase = 0
            elif altitude < 1000 and velocity < 50: phase = 1
            elif altitude < 3000 and velocity < 100: phase = 2
            elif altitude < 5000 and velocity > 50: phase = 3
            elif altitude > 5000 and velocity < 0: phase = 4
            elif altitude > 1000 and velocity < 0: phase = 5
            elif altitude < 1000 and velocity < 5: phase = 6
            else: phase = 7
            y_synthetic.append(phase)
        
        y_synthetic = np.array(y_synthetic)
        
        if X_synthetic.size > 0 and y_synthetic.size > 0:
            # Fit scaler on synthetic data
            if self.scaler:
                self.scaler.fit(X_synthetic)
                X_synthetic_scaled = self.scaler.transform(X_synthetic)
            else:
                X_synthetic_scaled = X_synthetic

            # Train the classifier
            self.mission_phase_classifier.fit(X_synthetic_scaled, y_synthetic)
            print("[OK] Mission phase classifier ensemble trained with synthetic data.")
        else:
            print("[WARN] Not enough synthetic data to train mission phase classifier.")
    
    def prepare_features(self, telemetry_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """Prepare features from telemetry data for AI processing"""
        if not telemetry_data:
            return np.array([]), []
        
        # Define feature columns based on typical telemetry data
        feature_columns = [
            'altitude', 'velocity', 'temperature', 'pressure', 
            'battery_level', 'latitude', 'longitude', 'radio_signal_strength'
        ]
        
        # Extract features
        features_list = []
        for record in telemetry_data:
            features = []
            for col in feature_columns:
                val = record.get(col, 0)
                if isinstance(val, (int, float)):
                    features.append(val)
                else:
                    features.append(0)  # Default value for non-numeric data
            features_list.append(features)
        
        # Add derived features
        extended_features_list = []
        for i, record in enumerate(telemetry_data):
            base_features = features_list[i]
            
            # Add derived features
            derived_features = []
            
            # Temporal features (if we have enough data)
            if i > 0:
                prev_record = telemetry_data[i-1]
                derived_features.extend([
                    record.get('altitude', 0) - prev_record.get('altitude', 0),  # Altitude change
                    record.get('velocity', 0) - prev_record.get('velocity', 0),  # Velocity change
                    record.get('temperature', 20) - prev_record.get('temperature', 20),  # Temp change
                    record.get('pressure', 1013.25) - prev_record.get('pressure', 1013.25),  # Pressure change
                ])
            else:
                derived_features.extend([0, 0, 0, 0])  # No previous data
            
            # Ratio features
            derived_features.extend([
                record.get('altitude', 0) / (record.get('velocity', 1) + 0.001),  # Altitude/velocity ratio
                record.get('temperature', 20) / (record.get('pressure', 1013.25) / 1000),  # Temp/pressure ratio
                record.get('battery_level', 100) / 100,  # Normalized battery
                abs(record.get('latitude', 0)) + abs(record.get('longitude', 0)),  # Distance from equator
            ])
            
            # Combine base and derived features
            all_features = base_features + derived_features
            extended_features_list.append(all_features)
        
        # Define extended feature names
        extended_feature_names = feature_columns + [
            'altitude_change', 'velocity_change', 'temp_change', 'pressure_change',
            'alt_vel_ratio', 'temp_press_ratio', 'norm_battery', 'dist_from_equator'
        ]
        
        return np.array(extended_features_list), extended_feature_names
    
    def train_comprehensive_model(self, telemetry_data: List[Dict[str, Any]],
                               target_metric: str = 'altitude',
                               task_type: str = 'regression') -> Dict[str, Any]:
        """Train a comprehensive model using multiple AI frameworks"""

        print("[INFO] Training comprehensive AI model using multiple frameworks...")
        
        # Prepare features
        X, feature_names = self.prepare_features(telemetry_data)
        if X.size == 0:
            return {'error': 'No features extracted from telemetry data'}
        
        # Prepare target values
        y = []
        for record in telemetry_data:
            target_val = record.get(target_metric, 0)
            if isinstance(target_val, (int, float)):
                y.append(target_val)
            else:
                y.append(0)  # Default value if not numeric
        
        if len(y) != len(X):
            return {'error': 'Mismatch between features and targets'}
        
        y = np.array(y)
        
        # Scale features if scaler is available
        if self.scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # Train the fusion model
        fusion_result = self.advanced_fusion.train_fusion_model(
            X_scaled, y, task_type=task_type, fusion_strategy='weighted_average'
        )
        
        self.is_trained = True
        self.feature_names = feature_names
        
        # Store model in history
        model_info = {
            'timestamp': datetime.now().isoformat(),
            'target_metric': target_metric,
            'task_type': task_type,
            'training_samples': len(telemetry_data),
            'features_used': len(feature_names),
            'fusion_result': fusion_result
        }
        self.model_history.append(model_info)
        
        print(f"✅ Comprehensive AI model trained successfully!")
        print(f"📊 Features used: {len(feature_names)}")
        print(f"📈 Training samples: {len(telemetry_data)}")
        print(f"🎯 Target metric: {target_metric}")
        
        return {
            'success': True,
            'model_info': model_info,
            'framework_summary': self.advanced_fusion.get_framework_summary(),
            'ensemble_performance': fusion_result.get('ensemble_performance', 0)
        }
    
    def predict_with_multiple_frameworks(self, current_data: List[Dict[str, Any]], 
                                       steps: int = 5) -> AIPredictionResult:
        """Make predictions using multiple AI frameworks"""
        
        if not self.is_trained:
            return AIPredictionResult(
                predicted_values=[],
                confidence_scores=[],
                model_contributions={},
                execution_time=0,
                framework_used='untrained'
            )
        
        # Prepare features for prediction
        X, _ = self.prepare_features(current_data[-1:])  # Use last record for prediction
        if X.size == 0:
            return AIPredictionResult(
                predicted_values=[],
                confidence_scores=[],
                model_contributions={},
                execution_time=0,
                framework_used='no_features'
            )
        
        # Scale features if scaler is available
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # Make predictions using the fusion model
        start_time = datetime.now()
        
        # For multi-step prediction, we'll iteratively predict
        predictions = []
        confidence_scores = []
        
        current_X = X_scaled.copy()
        for step in range(steps):
            # Get prediction from fusion model
            step_prediction_raw = self.advanced_fusion.predict_fusion(current_X)
            
            # Ensure step_prediction_raw is a single float or convertible to it
            # Flatten if it's a multi-dimensional array, take the first element if it's a list/tuple
            if isinstance(step_prediction_raw, np.ndarray) and step_prediction_raw.ndim > 0:
                step_prediction = float(step_prediction_raw.flatten()[0])
            elif isinstance(step_prediction_raw, (list, tuple)) and len(step_prediction_raw) > 0:
                 step_prediction = float(step_prediction_raw[0])
            else:
                step_prediction = float(step_prediction_raw)

            if step_prediction is not None:
                predictions.append(step_prediction)
                confidence_scores.append(0.85)  # Default confidence for ensemble
            else:
                predictions.append(0.0)
                confidence_scores.append(0.0)
            
            # Update features for next prediction (auto-regressive approach)
            # This is a more sophisticated approach than a simple decay.
            # We assume the first feature in current_X corresponds to the predicted target metric.
            # In a real system, the feature mapping would need to be explicit and flexible.
            if current_X.shape[1] > 0:
                updated_features = current_X[0, :].copy() # Get the feature vector
                # Update the feature corresponding to the target metric (e.g., altitude)
                # This assumes a fixed index for the target metric in the feature vector.
                # For this example, let's update the first feature as the predicted value.
                updated_features[0] = step_prediction
                
                # Shift other features, simulating temporal progression
                # This is a placeholder for actual temporal feature updates
                for i in range(1, len(updated_features)):
                    updated_features[i] = updated_features[i] * 0.9 + step_prediction * 0.1 # Simple blending

                current_X = np.array([updated_features]) # Reshape back to (1, num_features)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Get model contributions from the fusion system
        model_contributions = self.advanced_fusion.model_performance.copy()
        
        return AIPredictionResult(
            predicted_values=predictions,
            confidence_scores=confidence_scores,
            model_contributions=model_contributions,
            execution_time=execution_time,
            framework_used='multi_framework_ensemble'
        )
    
    def detect_anomalies_with_ensemble(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies using ensemble of models from different frameworks"""
        
        if not telemetry_data:
            return []
        
        # Prepare features
        X, _ = self.prepare_features(telemetry_data)
        if X.size == 0:
            return []
        
        # Scale features if scaler is available
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        anomalies = []
        
        # Use Isolation Forest if available
        if SKLEARN_AVAILABLE:
            try:
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                anomaly_predictions = iso_forest.fit_predict(X_scaled)
                anomaly_scores = iso_forest.decision_function(X_scaled)
                
                for i, (pred, score) in enumerate(zip(anomaly_predictions, anomaly_scores)):
                    if pred == -1:  # Anomaly detected
                        anomalies.append({
                            'index': i,
                            'timestamp': telemetry_data[i].get('timestamp', 'unknown'),
                            'anomaly_score': float(score),
                            'data_point': telemetry_data[i],
                            'source': 'isolation_forest',
                            'severity': 'high' if score < -0.1 else ('medium' if score < 0 else 'low')
                        })
            except Exception as e:
                print(f"Warning: Isolation Forest anomaly detection failed: {e}")
        
        # Additional anomaly detection could be implemented with other frameworks
        # For now, we'll return the anomalies detected by Isolation Forest
        
        return anomalies
    
    def classify_mission_phase_ensemble(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify mission phases using ensemble of models"""
        
        if not telemetry_data:
            return []
        
        # Prepare features
        X, _ = self.prepare_features(telemetry_data)
        if X.size == 0:
            return []
        
        # Scale features if scaler is available
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        classifications = []
        
        if self.mission_phase_classifier and self.is_trained:
            # Predict phases using the trained classifier
            try:
                # Scale features if scaler is available
                if self.scaler:
                    X_scaled = self.scaler.transform(X)
                else:
                    X_scaled = X
                
                predicted_phases = self.mission_phase_classifier.predict(X_scaled)
                # For simplicity, confidence can be derived from prediction probabilities if classifier supports it
                # For RandomForest, can use predict_proba
                predicted_probabilities = self.mission_phase_classifier.predict_proba(X_scaled)
                
                for i, record in enumerate(telemetry_data):
                    phase_id = int(predicted_phases[i])
                    confidence = float(np.max(predicted_probabilities[i])) if predicted_probabilities.size > 0 else 0.9
                    
                    classifications.append({
                        'index': i,
                        'timestamp': record.get('timestamp', 'unknown'),
                        'phase': phase_id,
                        'phase_name': self._get_phase_name(phase_id),
                        'confidence': confidence,
                        'data_point': record,
                        'source': 'ensemble_classifier'
                    })
                return classifications
            except Exception as e:
                print(f"⚠️  Error using mission phase classifier ensemble: {e}. Falling back to rule-based classification.")

        # Fallback to rule-based classification if classifier is not available or fails
        for i, record in enumerate(telemetry_data):
            altitude = record.get('altitude', 0)
            velocity = record.get('velocity', 0)
            battery = record.get('battery_level', 100)
            
            # More granular mission phase classification
            if altitude < 500 and velocity < 10:
                phase = 0  # Pre-launch / ground
            elif altitude < 1000 and velocity < 50:
                phase = 1  # Early ascent
            elif altitude < 3000 and velocity < 100:
                phase = 2  # Mid ascent
            elif altitude < 5000 and velocity > 50:
                phase = 3  # High ascent
            elif altitude > 5000 and velocity < 0:  # Descending
                phase = 4  # Apogee/descent start
            elif altitude > 1000 and velocity < 0:  # Still descending
                phase = 5  # Descent
            elif altitude < 1000 and velocity < 5:  # Low altitude, slow
                phase = 6  # Landing/recovery
            else:
                phase = 7  # Other/transition
            
            classifications.append({
                'index': i,
                'timestamp': record.get('timestamp', 'unknown'),
                'phase': phase,
                'phase_name': self._get_phase_name(phase),
                'confidence': 0.7, # Lower confidence for rule-based
                'data_point': record,
                'source': 'rule_based_heuristic'
            })
        
        return classifications
    
    def _get_phase_name(self, phase_id: int) -> str:
        """Get name for mission phase ID"""
        phase_names = {
            0: "Pre-launch/Ground",
            1: "Early Ascent",
            2: "Mid Ascent", 
            3: "High Ascent",
            4: "Apogee/Descent Start",
            5: "Descent",
            6: "Landing/Recovery",
            7: "Other/Transition"
        }
        return phase_names.get(phase_id, f"Phase {phase_id}")
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for all trained models"""
        return {
            'is_trained': self.is_trained,
            'model_count': len(self.model_history),
            'latest_model': self.model_history[-1] if self.model_history else None,
            'framework_availability': self.advanced_fusion.ensemble_ai.get_available_algorithms(),
            'feature_count': len(self.feature_names),
            'performance_metrics': self.performance_metrics
        }
    
    def save_model(self, filepath: str):
        """Save the trained model to disk"""
        if not self.is_trained:
            print("Warning: No trained model to save")
            return False
        
        model_data = {
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'model_history': self.model_history,
            'performance_metrics': self.performance_metrics
        }
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"✅ Model saved to {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            return False
    
    def load_model(self, filepath: str):
        """Load a trained model from disk"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.scaler = model_data.get('scaler')
            self.feature_names = model_data.get('feature_names', [])
            self.is_trained = model_data.get('is_trained', False)
            self.model_history = model_data.get('model_history', [])
            self.performance_metrics = model_data.get('performance_metrics', {})
            
            print(f"✅ Model loaded from {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False


class EnhancedAICore:
    """Enhanced AI core that integrates all AI capabilities"""
    
    def __init__(self):
        self.multi_framework_system = MultiFrameworkAISystem()
        self.analysis_history = []
        self.insight_cache = {}

        # Import and initialize advanced neural networks
        try:
            from ai.advanced_neural_networks import (
                AdvancedNeuralArchitectures,
                NeuralNetworkOptimizer,
                AdvancedNeuralProcessor,
                TelemetryNeuralAnalyzer
            )
            self.advanced_neural_architectures = AdvancedNeuralArchitectures()
            self.neural_optimizer = NeuralNetworkOptimizer()
            self.advanced_neural_processor = AdvancedNeuralProcessor()
            self.telemetry_neural_analyzer = TelemetryNeuralAnalyzer()
            print("[OK] Advanced Neural Networks integrated successfully")
        except ImportError:
            print("[WARN] Advanced Neural Networks not available, using basic functionality")
            self.advanced_neural_architectures = None
            self.neural_optimizer = None
            self.advanced_neural_processor = None
            self.telemetry_neural_analyzer = None
    
    def run_comprehensive_analysis(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive analysis using multiple AI frameworks and advanced neural networks"""

        print("🔬 Running comprehensive AI analysis with advanced neural networks...")

        start_time = datetime.now()

        # Train a model for the primary metric (altitude)
        training_result = self.multi_framework_system.train_comprehensive_model(
            telemetry_data,
            target_metric='altitude',
            task_type='regression'
        )

        # Make predictions
        prediction_result = self.multi_framework_system.predict_with_multiple_frameworks(
            telemetry_data,
            steps=5
        )

        # Detect anomalies
        anomalies = self.multi_framework_system.detect_anomalies_with_ensemble(telemetry_data)

        # Classify mission phases
        phase_classifications = self.multi_framework_system.classify_mission_phase_ensemble(telemetry_data)

        # Use advanced neural networks for enhanced analysis if available
        neural_analysis_results = {}
        if self.advanced_neural_architectures and self.advanced_neural_processor:
            print("   🧠 Running advanced neural network analysis...")

            try:
                # Prepare features for neural networks
                X, feature_names = self.multi_framework_system.prepare_features(telemetry_data)

                if len(X) > 10:  # Need sufficient data
                    # Create ensemble of neural architectures
                    X_train, X_val, y_train, y_val = train_test_split(
                        X, [d.get('altitude', 0) for d in telemetry_data],
                        test_size=0.2, random_state=42
                    )

                    # Create neural ensemble
                    neural_ensemble = self.advanced_neural_processor.create_ensemble(
                        X_train, y_train, X_val, y_val, num_models=3
                    )

                    # Make neural predictions
                    if neural_ensemble:
                        neural_predictions, neural_weights = self.advanced_neural_processor.predict_ensemble(X[-5:])  # Last 5 records

                        neural_analysis_results = {
                            'neural_ensemble_active': True,
                            'neural_predictions': neural_predictions.tolist() if hasattr(neural_predictions, 'tolist') else [],
                            'neural_model_weights': neural_weights,
                            'neural_architectures_used': len(neural_ensemble)
                        }

                        # Enhance overall predictions with neural insights
                        if len(neural_analysis_results['neural_predictions']) > 0:
                            # Add neural predictions to the main results
                            prediction_result.predicted_values.extend(neural_analysis_results['neural_predictions'][:len(prediction_result.predicted_values)])

            except Exception as e:
                print(f"   ⚠️  Neural network analysis failed: {e}")
                neural_analysis_results['neural_error'] = str(e)

        # Use telemetry neural analyzer for specialized analysis if available
        telemetry_neural_results = {}
        if self.telemetry_neural_analyzer:
            print("   📡 Running specialized telemetry neural analysis...")
            try:
                telemetry_analysis = self.telemetry_neural_analyzer.analyze_telemetry_patterns(telemetry_data)
                telemetry_neural_results = {
                    'telemetry_neural_analysis': telemetry_analysis,
                    'neural_confidence': telemetry_analysis.get('neural_confidence', 0.0)
                }

                # Enhance anomalies with neural insights
                if 'anomalies_detected' in telemetry_analysis:
                    anomalies.extend(telemetry_analysis['anomalies_detected'])

                # Enhance predictions with neural insights
                if 'predictions' in telemetry_analysis and prediction_result.predicted_values:
                    for pred in telemetry_analysis['predictions']:
                        if 'predicted_values' in pred:
                            # Add neural predictions to main results
                            for key, value in pred['predicted_values'].items():
                                if key in ['altitude', 'velocity', 'temperature']:  # Relevant metrics
                                    prediction_result.predicted_values.append(value)
                                    prediction_result.confidence_scores.append(pred.get('confidence', 0.7))

            except Exception as e:
                print(f"   ⚠️  Telemetry neural analysis failed: {e}")
                telemetry_neural_results['telemetry_neural_error'] = str(e)

        end_time = datetime.now()
        analysis_duration = (end_time - start_time).total_seconds()

        # Compile results
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'analysis_duration': analysis_duration,
            'training_result': training_result,
            'predictions': {
                'values': prediction_result.predicted_values,
                'confidences': prediction_result.confidence_scores,
                'model_contributions': prediction_result.model_contributions,
                'framework_used': prediction_result.framework_used
            },
            'anomalies': {
                'count': len(anomalies),
                'details': anomalies
            },
            'phase_classifications': {
                'count': len(phase_classifications),
                'details': phase_classifications
            },
            'model_performance': self.multi_framework_system.get_model_performance(),
            'framework_summary': self.multi_framework_system.advanced_fusion.get_framework_summary(),
            'neural_analysis': neural_analysis_results,
            'telemetry_neural_analysis': telemetry_neural_results
        }

        # Add to analysis history
        self.analysis_history.append(analysis_result)

        print(f"✅ Comprehensive analysis completed in {analysis_duration:.2f}s")
        print(f"📊 Predictions made: {len(prediction_result.predicted_values)}")
        print(f"🔍 Anomalies detected: {len(anomalies)}")
        print(f"🏷️  Phase classifications: {len(phase_classifications)}")
        print(f"🧠 Neural networks utilized: {bool(neural_analysis_results)}")
        print(f"📡 Telemetry neural analysis: {bool(telemetry_neural_results)}")

        return analysis_result
    
    def generate_insights(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from analysis results"""
        
        insights = []
        
        # Add insights based on anomalies
        anomaly_count = analysis_result['anomalies']['count']
        if anomaly_count > 0:
            insights.append(f"⚠️  {anomaly_count} anomalies detected that may require attention")
        
        # Add insights based on predictions
        predictions = analysis_result['predictions']['values']
        if len(predictions) > 0:
            avg_prediction = sum(predictions) / len(predictions)
            insights.append(f"📈 Average predicted altitude: {avg_prediction:.2f}m over next {len(predictions)} steps")
        
        # Add insights based on phase classifications
        phase_details = analysis_result['phase_classifications']['details']
        if phase_details:
            current_phase = phase_details[-1]['phase_name'] if phase_details else 'unknown'
            insights.append(f"📍 Current mission phase: {current_phase}")
        
        # Add insights about model performance
        framework_summary = analysis_result['framework_summary']
        available_frameworks = sum(1 for available in analysis_result['model_performance']['framework_availability'].values() if available)
        insights.append(f"🧠 AI frameworks utilized: {available_frameworks}/6 available")
        
        return insights
    
    def get_latest_insights(self) -> List[str]:
        """Get insights from the most recent analysis"""
        if not self.analysis_history:
            return ["No analysis performed yet"]
        
        latest_analysis = self.analysis_history[-1]
        return self.generate_insights(latest_analysis)


# Global instance
enhanced_ai_core = EnhancedAICore()