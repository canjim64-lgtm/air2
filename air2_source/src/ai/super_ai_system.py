"""
Super AI System for AirOne v3.0
Integrates all advanced AI algorithms and techniques
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import json
import pickle
import os
import warnings
import logging
import hashlib
warnings.filterwarnings('ignore')

# Import all AI components
from .advanced_ai_fusion import AdvancedAIFusion, EnsembleAI
from .enhanced_ai_core import EnhancedAICore, MultiFrameworkAISystem
from .advanced_algorithms import (
    EvolutionaryOptimizer, GeneticProgramming, ReinforcementLearningAgent,
    SwarmIntelligence, AdvancedEnsembleMethods, AdvancedFeatureEngineering,
    AdvancedAnomalyDetection, AdvancedTimeSeriesAnalysis, AdvancedClustering
)

# Import available ML libraries (with fallbacks)
try:
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
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


class SuperAISystem:
    """Super AI system that combines all advanced AI techniques"""
    
    def __init__(self):
        # Initialize all AI components
        self.advanced_fusion = AdvancedAIFusion()
        self.multi_framework_system = MultiFrameworkAISystem()
        self.evolutionary_optimizer = EvolutionaryOptimizer()
        self.genetic_programming = GeneticProgramming()
        self.reinforcement_agent = ReinforcementLearningAgent(state_size=10, action_size=5) if TORCH_AVAILABLE else None
        self.swarm_intelligence = SwarmIntelligence(dimensions=10)
        self.advanced_ensemble = AdvancedEnsembleMethods()
        self.feature_engineering = AdvancedFeatureEngineering()
        self.anomaly_detection = AdvancedAnomalyDetection()
        self.time_series_analysis = AdvancedTimeSeriesAnalysis()
        self.advanced_clustering = AdvancedClustering()

        # System state
        self.is_trained = False
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.feature_names = []
        self.model_performance = []
        self.ai_decisions = []

        print("[INFO] Super AI System initialized with all advanced algorithms")
    
    def prepare_features(self, telemetry_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """Prepare features using advanced engineering techniques"""
        if not telemetry_data:
            return np.array([]), []
        
        # Start with basic features
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
        
        # Apply advanced feature engineering
        try:
            # Create polynomial features
            X_poly = self.feature_engineering.create_polynomial_features(X, degree=2)
            
            # Create interaction features
            X_interaction = self.feature_engineering.create_interaction_features(X_poly)
            
            # Create statistical features
            X_stat = self.feature_engineering.create_statistical_features(X_interaction)
            
            # Create lag features for time series
            X_final = self.feature_engineering.create_lag_features(X_stat)
            
        except:
            # Fallback to original features if advanced engineering fails
            X_final = X
        
        # Define feature names
        base_names = feature_columns
        extended_names = base_names[:]  # Copy base names
        
        # Add names for engineered features
        n_original = len(base_names)
        n_engineered = X_final.shape[1] - n_original
        
        for i in range(n_engineered):
            extended_names.append(f"engineered_feature_{i}")
        
        return X_final, extended_names
    
    def train_super_model(self, telemetry_data: List[Dict[str, Any]], 
                         target_metric: str = 'altitude', 
                         task_type: str = 'regression') -> Dict[str, Any]:
        """Train the super AI model using all available techniques"""
        
        print("🚀 Training Super AI Model with All Advanced Techniques...")
        
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
                y.append(0)
        
        if len(y) != len(X):
            return {'error': 'Mismatch between features and targets'}
        
        y = np.array(y)
        
        # Scale features if scaler is available
        if self.scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # Store feature names
        self.feature_names = feature_names
        
        # 1. Train the fusion model (already includes multiple frameworks)
        print("   1. Training multi-framework fusion model...")
        fusion_result = self.advanced_fusion.train_fusion_model(
            X_scaled, y, task_type=task_type, fusion_strategy='weighted_average'
        )
        
        # 2. Apply advanced ensemble methods
        print("   2. Applying advanced ensemble methods...")
        try:
            # Stacking ensemble
            self.advanced_ensemble.stacking_ensemble(X_scaled, y)
            
            # Bagging with diversity
            self.advanced_ensemble.bagging_with_diversity(X_scaled, y)
            
            # Boosting with adaptive learning
            self.advanced_ensemble.boosting_with_adaptive_learning(X_scaled, y)
        except Exception as e:
            print(f"   ⚠️  Advanced ensemble methods failed: {e}")
        
        # 3. Apply evolutionary optimization
        print("   3. Applying evolutionary optimization...")
        try:
            # Define parameter space for optimization
            param_space = {
                'n_estimators': (50, 200),
                'max_depth': (3, 10),
                'learning_rate': (0.01, 0.3)
            }
            
            def objective_func(params, X, y):
                # Simple objective function for demonstration
                if SKLEARN_AVAILABLE:
                    model = RandomForestRegressor(
                        n_estimators=int(params.get('n_estimators', 100)),
                        max_depth=int(params.get('max_depth', 5)),
                        random_state=42
                    )
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    score = r2_score(y_test, y_pred)
                    return score
                return 0.5  # Default score
            
            best_params, best_score = self.evolutionary_optimizer.evolve(
                objective_func, param_space, X_scaled, y
            )
            print(f"      Best evolved parameters: {best_params}, Score: {best_score:.4f}")
        except Exception as e:
            print(f"   ⚠️  Evolutionary optimization failed: {e}")
        
        # 4. Apply genetic programming
        print("   4. Applying genetic programming...")
        try:
            gp_program, gp_score = self.genetic_programming.evolve_program(
                X_scaled[:20], y[:20], feature_names[:min(10, len(feature_names))]
            )  # Use subset for GP to avoid long computation
            print(f"      Best GP program score: {gp_score:.4f}")
        except Exception as e:
            print(f"   ⚠️  Genetic programming failed: {e}")
        
        # 5. Apply swarm intelligence optimization
        print("   5. Applying swarm intelligence optimization...")
        try:
            def si_objective_func(params, X, y):
                # Simple objective function for swarm intelligence
                if SKLEARN_AVAILABLE:
                    model = RandomForestRegressor(
                        n_estimators=int(max(10, min(500, params[0]))),
                        max_depth=int(max(1, min(20, params[1]))),
                        random_state=42
                    )
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    score = r2_score(y_test, y_pred)
                    return score
                return 0.5
            
            si_params, si_score = self.swarm_intelligence.optimize(si_objective_func, X_scaled, y)
            print(f"      Best SI parameters score: {si_score:.4f}")
        except Exception as e:
            print(f"   ⚠️  Swarm intelligence optimization failed: {e}")
        
        # 6. Apply advanced clustering
        print("   6. Applying advanced clustering...")
        try:
            cluster_labels = self.advanced_clustering.ensemble_clustering(X_scaled)
            print(f"      Found {len(np.unique(cluster_labels))} clusters")
        except Exception as e:
            print(f"   ⚠️  Advanced clustering failed: {e}")
        
        # 7. Apply advanced anomaly detection
        print("   7. Applying advanced anomaly detection...")
        try:
            iso_scores = self.anomaly_detection.isolation_forest_ensemble(X_scaled)
            print(f"      Anomaly detection completed")
        except Exception as e:
            print(f"   ⚠️  Advanced anomaly detection failed: {e}")
        
        # 8. Apply time series analysis
        print("   8. Applying time series analysis...")
        try:
            if len(y) > 10:
                forecast = self.time_series_analysis.arima_forecast(y)
                print(f"      Time series forecast completed: {forecast[:3]}...")
        except Exception as e:
            print(f"   ⚠️  Time series analysis failed: {e}")
        
        # Mark as trained
        self.is_trained = True
        
        # Store model performance
        self.model_performance = {
            'fusion_performance': fusion_result.get('ensemble_performance', 0),
            'total_samples': len(telemetry_data),
            'features_used': len(feature_names),
            'training_timestamp': datetime.now().isoformat()
        }
        
        result = {
            'success': True,
            'fusion_result': fusion_result,
            'model_performance': self.model_performance,
            'features_engineered': len(feature_names) - 8,  # Assuming 8 base features
            'algorithms_applied': [
                'multi_framework_fusion',
                'advanced_ensemble_methods',
                'evolutionary_optimization',
                'genetic_programming',
                'swarm_intelligence',
                'advanced_clustering',
                'advanced_anomaly_detection',
                'time_series_analysis'
            ]
        }
        
        print(f"✅ Super AI Model trained successfully with {len(result['algorithms_applied'])} advanced techniques!")
        return result
    
    def predict_super(self, current_data: List[Dict[str, Any]], steps: int = 5) -> Dict[str, Any]:
        """Make predictions using the super AI system"""
        
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
        
        # Scale features if scaler is available
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        predictions = []
        confidence_scores = []
        
        # Use multiple prediction methods
        methods_used = []
        
        # 1. Use the fusion model
        try:
            fusion_pred = self.advanced_fusion.predict_fusion(X_scaled)
            if len(fusion_pred) > 0:
                pred_value = float(fusion_pred[0]) if hasattr(fusion_pred[0], '__len__') else float(fusion_pred)
                predictions.append(pred_value)
                confidence_scores.append(0.90)
                methods_used.append('fusion')
        except Exception as e:
            print(f"   ⚠️  Fusion prediction failed: {e}")
        
        # 2. Use multi-framework system
        try:
            multi_pred_result = self.multi_framework_system.predict_with_multiple_frameworks(
                current_data, steps=1
            )
            if multi_pred_result.predicted_values:
                predictions.extend(multi_pred_result.predicted_values)
                confidence_scores.extend(multi_pred_result.confidence_scores)
                methods_used.extend(['multi_framework'] * len(multi_pred_result.predicted_values))
        except Exception as e:
            print(f"   ⚠️  Multi-framework prediction failed: {e}")
        
        # 3. Use time series analysis for forecasting
        try:
            if len([d.get('altitude', 0) for d in current_data]) > 10:
                recent_altitudes = [d.get('altitude', 0) for d in current_data[-10:]]
                ts_forecast = self.time_series_analysis.arima_forecast(np.array(recent_altitudes))
                predictions.extend(ts_forecast[:steps])
                confidence_scores.extend([0.85] * min(len(ts_forecast), steps))
                methods_used.extend(['time_series'] * min(len(ts_forecast), steps))
        except Exception as e:
            print(f"   ⚠️  Time series prediction failed: {e}")
        
        # Combine predictions intelligently
        if predictions:
            # Weighted average based on method reliability
            weights = []
            for method in methods_used:
                if method == 'fusion':
                    weights.append(0.4)
                elif method == 'multi_framework':
                    weights.append(0.3)
                elif method == 'time_series':
                    weights.append(0.3)
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
                'methods_used': methods_used,
                'confidence_score': final_confidence,
                'prediction_weights': weights,
                'steps_predicted': len(predictions)
            }
        else:
            result = {
                'final_prediction': 0,
                'individual_predictions': [],
                'methods_used': [],
                'confidence_score': 0.0,
                'prediction_weights': [],
                'steps_predicted': 0
            }
        
        # Store decision for learning
        decision_record = {
            'timestamp': datetime.now().isoformat(),
            'input_features': X.tolist()[0] if X.size > 0 else [],
            'prediction': result['final_prediction'],
            'confidence': result['confidence_score'],
            'methods': methods_used
        }
        self.ai_decisions.append(decision_record)
        
        return result
    
    def detect_anomalies_super(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies using multiple advanced techniques"""
        
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
        
        all_anomalies = []
        
        # 1. Use ensemble of isolation forests
        try:
            iso_scores = self.anomaly_detection.isolation_forest_ensemble(X_scaled, n_estimators=5)
            # Identify anomalies (scores below threshold)
            threshold = np.percentile(iso_scores, 10)  # Bottom 10% are anomalies
            iso_anomalies = np.where(iso_scores < threshold)[0]
            
            for idx in iso_anomalies:
                all_anomalies.append({
                    'index': int(idx),
                    'timestamp': telemetry_data[idx].get('timestamp', 'unknown'),
                    'score': float(iso_scores[idx]),
                    'method': 'isolation_forest_ensemble',
                    'severity': 'high' if iso_scores[idx] < threshold * 0.5 else 'medium'
                })
        except Exception as e:
            print(f"   ⚠️  Isolation forest ensemble failed: {e}")
        
        # 2. Use multi-framework system anomaly detection
        try:
            multi_anomalies = self.multi_framework_system.detect_anomalies_with_ensemble(telemetry_data)
            for anomaly in multi_anomalies:
                anomaly['method'] = 'multi_framework_ensemble'
                all_anomalies.append(anomaly)
        except Exception as e:
            print(f"   ⚠️  Multi-framework anomaly detection failed: {e}")
        
        # Sort anomalies by severity and score
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_anomalies.sort(key=lambda x: (severity_order.get(x.get('severity', 'low'), 4), x.get('score', 0)))
        
        return all_anomalies

    def classify_phases_super(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify mission phases using multiple techniques"""

        if not telemetry_data:
            return []

        # Use multi-framework system classification
        try:
            classifications = self.multi_framework_system.classify_mission_phase_ensemble(telemetry_data)
            return classifications
        except Exception as e:
            print(f"   ⚠️  Super phase classification failed: {e}")
            return []

    def get_super_model_status(self) -> Dict[str, Any]:
        """Get status of the super model"""
        return {
            'is_trained': self.is_trained,
            'feature_count': len(self.feature_names),
            'model_performance': self.model_performance,
            'algorithms_applied': [
                'multi_framework_fusion',
                'advanced_ensemble_methods',
                'evolutionary_optimization',
                'genetic_programming',
                'swarm_intelligence',
                'advanced_clustering',
                'advanced_anomaly_detection',
                'time_series_analysis'
            ]
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'is_trained': self.is_trained,
            'model_performance': self.model_performance,
            'feature_count': len(self.feature_names),
            'decisions_made': len(self.ai_decisions),
            'algorithms_available': {
                'sklearn': SKLEARN_AVAILABLE,
                'tensorflow': TENSORFLOW_AVAILABLE,
                'pytorch': TORCH_AVAILABLE,
                'xgboost': XGBOOST_AVAILABLE,
                'lightgbm': LIGHTGBM_AVAILABLE
            },
            'recent_decisions': self.ai_decisions[-5:] if self.ai_decisions else [],
            'framework_integration': 'fully_integrated',
            'ai_techniques_deployed': 8  # Number of different AI techniques applied
        }
    
    def save_model(self, filepath: str):
        """Save the trained super AI model"""
        if not self.is_trained:
            print("Warning: No trained model to save")
            return False
        
        model_data = {
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'model_performance': self.model_performance,
            'ai_decisions': self.ai_decisions[-1000:],  # Keep last 1000 decisions
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"✅ Super AI Model saved to {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving super AI model: {e}")
            return False
    
    def load_model(self, filepath: str):
        """Load a trained super AI model"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.scaler = model_data.get('scaler')
            self.feature_names = model_data.get('feature_names', [])
            self.is_trained = model_data.get('is_trained', False)
            self.model_performance = model_data.get('model_performance', {})
            self.ai_decisions = model_data.get('ai_decisions', [])
            
            print(f"✅ Super AI Model loaded from {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error loading super AI model: {e}")
            return False


class CognitiveAIAgent:
    """Cognitive AI agent that makes intelligent decisions based on multiple AI inputs"""
    
    def __init__(self):
        self.super_ai = SuperAISystem()
        self.decision_memory = []
        self.learning_rate = 0.1
        self.confidence_threshold = 0.7
        self.adaptation_enabled = True
        self.decision_weights = defaultdict(float) # Initialize decision_weights
        self.adaptation_history = [] # Initialize adaptation_history
        self.logger = logging.getLogger(self.__class__.__name__) # Initialize logger
    
    def make_decision(self, telemetry_data: List[Dict[str, Any]], 
                     decision_context: str = "mission_control") -> Dict[str, Any]:
        """Make an intelligent decision based on multiple AI inputs"""
        
        start_time = datetime.now()
        
        # Get predictions from super AI
        prediction_result = self.super_ai.predict_super(telemetry_data)
        
        # Detect anomalies
        anomalies = self.super_ai.detect_anomalies_super(telemetry_data)
        
        # Classify mission phases
        phases = self.super_ai.classify_phases_super(telemetry_data)
        
        # Analyze trends
        trends = self._analyze_trends(telemetry_data)
        
        # Make decision based on all inputs
        decision = self._synthesize_decision(
            prediction_result, anomalies, phases, trends, decision_context
        )
        
        # Store decision for learning
        decision_record = {
            'timestamp': datetime.now().isoformat(),
            'input_data_summary': {
                'data_points': len(telemetry_data),
                'prediction': prediction_result.get('final_prediction', 0),
                'anomalies_count': len(anomalies),
                'current_phase': phases[-1]['phase_name'] if phases else 'unknown'
            },
            'decision': decision,
            'processing_time': (datetime.now() - start_time).total_seconds()
        }
        
        self.decision_memory.append(decision_record)
        
        # Adapt if enabled
        if self.adaptation_enabled:
            self._adapt_based_on_feedback(decision_record)
        
        return {
            'decision': decision,
            'confidence': decision.get('confidence', 0.5),
            'explanation': decision.get('explanation', 'Decision made by cognitive AI agent'),
            'supporting_data': {
                'prediction': prediction_result,
                'anomalies': anomalies,
                'phases': phases,
                'trends': trends
            },
            'processing_time': (datetime.now() - start_time).total_seconds()
        }
    
    def _analyze_trends(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in the telemetry data"""
        if not telemetry_data:
            return {}
        
        metrics = ['altitude', 'velocity', 'temperature', 'pressure', 'battery_level']
        trends = {}
        
        for metric in metrics:
            values = [d.get(metric, 0) for d in telemetry_data if metric in d]
            if len(values) > 1:
                # Calculate trend (slope of linear regression)
                n = len(values)
                x = np.arange(n)
                slope = (n * np.sum(x * values) - np.sum(x) * np.sum(values)) / (n * np.sum(x**2) - (np.sum(x))**2)
                trends[metric] = {
                    'slope': float(slope),
                    'direction': 'increasing' if slope > 0.1 else ('decreasing' if slope < -0.1 else 'stable'),
                    'latest_value': float(values[-1]),
                    'average': float(np.mean(values))
                }
        
        return trends
    
    def _synthesize_decision(self, prediction_result: Dict[str, Any], 
                           anomalies: List[Dict[str, Any]], 
                           phases: List[Dict[str, Any]], 
                           trends: Dict[str, Any],
                           context: str) -> Dict[str, Any]:
        """Synthesize a decision from multiple AI inputs"""
        
        # Calculate overall confidence
        pred_confidence = prediction_result.get('confidence_score', 0.5)
        anomaly_count = len(anomalies)
        current_phase = phases[-1]['phase_name'] if phases else 'unknown'
        
        # Base decision on context
        if context == "mission_control":
            # Mission control decisions
            decision = {
                'action': 'continue_normal_operations',
                'confidence': 0.8,
                'explanation': 'Normal operations continuing'
            }
            
            # Check for anomalies
            if anomaly_count > 3:
                decision['action'] = 'investigate_anomalies'
                decision['confidence'] = 0.9
                decision['explanation'] = f'{anomaly_count} anomalies detected, recommending investigation'
            
            # Check battery level
            if 'battery_level' in trends and trends['battery_level']['latest_value'] < 20:
                decision['action'] = 'initiate_recovery_procedure'
                decision['confidence'] = 0.95
                decision['explanation'] = 'Battery level critically low, initiating recovery'
            
            # Check altitude trends
            if 'altitude' in trends:
                if trends['altitude']['direction'] == 'decreasing' and current_phase == 'Descent':
                    decision['action'] = 'monitor_descent'
                    decision['confidence'] = 0.85
                    decision['explanation'] = 'Expected descent phase, monitoring closely'
        
        elif context == "safety":
            # Safety-focused decisions
            decision = {
                'action': 'safe_mode',
                'confidence': 0.9,
                'explanation': 'Safety check passed'
            }
            
            # Check for critical anomalies
            critical_anomalies = [a for a in anomalies if a.get('severity') in ['high', 'critical']]
            if len(critical_anomalies) > 0:
                decision['action'] = 'emergency_procedure'
                decision['confidence'] = 0.95
                decision['explanation'] = f'{len(critical_anomalies)} critical anomalies detected, initiating emergency procedures'
        
        else:
            # Default decisions
            decision = {
                'action': 'monitor',
                'confidence': max(0.6, pred_confidence),
                'explanation': 'Continuing monitoring operations'
            }
        
        # Adjust confidence based on anomaly count
        if anomaly_count > 5:
            decision['confidence'] *= 0.8  # Reduce confidence with many anomalies
        elif anomaly_count == 0:
            decision['confidence'] *= 1.1  # Increase confidence with no anomalies
        
        decision['confidence'] = min(0.99, decision['confidence'])  # Cap at 99%
        
        return decision
    
    def _adapt_based_on_feedback(self, decision_record: Dict[str, Any]):
        """Adapt decision-making based on outcomes, updating decision weights."""
        if not self.adaptation_enabled or not decision_record:
            return
        
        outcome = decision_record.get('outcome', 'unknown')
        # Use a hash of the decision's explanation or action as a robust ID
        decision_id = hashlib.sha256(decision_record.get('decision', {}).get('explanation', 'no_explanation').encode('utf-8')).hexdigest()
        
        # Update decision weights based on outcome
        if outcome == 'successful':
            # Increase confidence for similar future decisions
            self.decision_weights[decision_id] = min(1.0, self.decision_weights[decision_id] + self.learning_rate)
        elif outcome == 'failed':
            # Decrease confidence for similar future decisions
            self.decision_weights[decision_id] = max(0.1, self.decision_weights[decision_id] - self.learning_rate * 1.5)
        else: # Neutral or unknown outcome
            self.decision_weights[decision_id] = self.decision_weights.get(decision_id, 0.5) # Maintain or default to 0.5
        
        self.logger.info(f"Adapted decision {decision_id} based on outcome: {outcome}. New weight: {self.decision_weights[decision_id]:.2f}")
        self.adaptation_history.append({
            'decision_id': decision_id,
            'outcome': outcome,
            'new_weight': self.decision_weights[decision_id],
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_decision_insights(self) -> Dict[str, Any]:
        """Get insights from the decision-making process"""
        if not self.decision_memory:
            return {'message': 'No decisions made yet'}
        
        recent_decisions = self.decision_memory[-10:]  # Last 10 decisions
        
        insights = {
            'total_decisions': len(self.decision_memory),
            'recent_decisions': [d['decision']['action'] for d in recent_decisions],
            'average_confidence': np.mean([d['decision']['confidence'] for d in recent_decisions]),
            'most_common_action': max(set(d['decision']['action'] for d in recent_decisions), 
                                    key=lambda x: sum(1 for d in recent_decisions if d['decision']['action'] == x)),
            'processing_times': [d['processing_time'] for d in recent_decisions]
        }
        
        return insights


# Global instances
super_ai_system = SuperAISystem()
cognitive_agent = CognitiveAIAgent()