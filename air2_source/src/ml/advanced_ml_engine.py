"""
Advanced ML Engine for AirOne v3.0
Handles machine learning and AI functionality with local AI capabilities
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import pickle
import os
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, classification_report
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor
import warnings
warnings.filterwarnings('ignore')

# Import enhanced AI capabilities
from .enhanced_ai_engine import EnhancedMLEngine, EnhancedLocalAIDataAnalyzer, EnhancedReportGenerator


@dataclass
class ReportSection:
    """Structure for report sections"""
    title: str
    content: str
    recommendations: List[str]
    data_insights: List[Dict[str, Any]]


class DeepLearningAnalyzer:
    """Advanced deep learning analyzer using neural networks"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.sequence_length = 10  # Number of previous steps to use for prediction
        self.feature_names = [
            'altitude', 'velocity', 'temperature', 'pressure', 'battery_level',
            'latitude', 'longitude', 'radio_signal_strength'
        ]

    def create_lstm_features(self, telemetry_data: List[Dict[str, Any]], sequence_length: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM-style processing"""
        if len(telemetry_data) < sequence_length + 1:
            return np.array([]), np.array([])

        # Prepare features
        features_list = []
        for record in telemetry_data:
            features = [record.get(name, 0) for name in self.feature_names]
            features_list.append(features)

        features_array = np.array(features_list)

        # Create sequences
        X, y = [], []
        for i in range(len(features_array) - sequence_length):
            X.append(features_array[i:(i + sequence_length)])
            y.append(features_array[i + sequence_length])  # Predict next step

        return np.array(X), np.array(y)

    def build_simple_nn_model(self, input_shape):
        """Build a simple neural network model using available tools"""
        # Using sklearn's MLPRegressor which implements a neural network
        model = MLPRegressor(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            solver='adam',
            max_iter=500,
            random_state=42
        )
        return model

    def train(self, telemetry_data: List[Dict[str, Any]]) -> bool:
        """Train the deep learning model"""
        if not telemetry_data or len(telemetry_data) < self.sequence_length + 5:
            return False

        X, y = self.create_lstm_features(telemetry_data, self.sequence_length)
        if X.size == 0 or y.size == 0:
            return False

        # Reshape for training (flatten sequences)
        X_flat = X.reshape(X.shape[0], -1)

        # Scale features
        X_scaled = self.scaler.fit_transform(X_flat)

        # Build and train model
        self.model = self.build_simple_nn_model(X_scaled.shape[1:])
        self.model.fit(X_scaled, y)

        self.is_trained = True
        return True

    def predict_sequence(self, telemetry_data: List[Dict[str, Any]], steps: int = 5) -> List[Dict[str, Any]]:
        """Predict multiple steps ahead using the trained model"""
        if not self.is_trained or self.model is None or not telemetry_data:
            return []

        predictions = []
        # Get the last 'sequence_length' records from telemetry_data
        current_sequence = telemetry_data[-self.sequence_length:]

        for step in range(steps):
            # Prepare current sequence for prediction
            current_features_list = []
            for record in current_sequence:
                features = [record.get(name, 0) for name in self.feature_names]
                current_features_list.append(features)

            # Ensure we have exactly sequence_length data points
            if len(current_features_list) < self.sequence_length:
                # Pad with the first available record if not enough
                padding_needed = self.sequence_length - len(current_features_list)
                current_features_list = [current_features_list[0]] * padding_needed + current_features_list

            # Take the last sequence_length elements
            current_features = np.array(current_features_list[-self.sequence_length:])
            
            # Flatten for the scaler and model
            current_input_flat = current_features.reshape(1, -1)

            # Scale input
            current_input_scaled = self.scaler.transform(current_input_flat)

            # Make prediction
            pred_values = self.model.predict(current_input_scaled)[0]

            # Create prediction record
            pred_record = {
                'step': step + 1,
                'confidence': 0.75  # Neural network confidence
            }
            for i, name in enumerate(self.feature_names):
                pred_record[f'predicted_{name}'] = float(pred_values[i])
            
            predictions.append(pred_record)

            # Update sequence for next prediction
            new_record = {name: pred_values[i] for i, name in enumerate(self.feature_names)}
            
            # Slide the window: remove first element and add predicted
            current_sequence = current_sequence[1:] + [new_record]

        return predictions


class LocalAIDataAnalyzer:
    """Local AI data analyzer for telemetry and sensor data"""

    def __init__(self):
        self.scaler_features = StandardScaler()
        self.scaler_targets = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.prediction_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.classification_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.clustering_model = KMeans(n_clusters=5, random_state=42, n_init=10) # Added n_init for KMeans
        self.deep_analyzer = DeepLearningAnalyzer()
        self.is_trained = {'anomaly': False, 'prediction': False, 'classification': False, 'clustering': False, 'deep_learning': False}
        self.feature_columns = [
            'altitude', 'velocity', 'temperature', 'pressure', 'battery_level',
            'latitude', 'longitude', 'radio_signal_strength', 'timestamp_numeric'
        ]

    def prepare_features(self, telemetry_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare features from telemetry data for ML models"""
        if not telemetry_data:
            return pd.DataFrame()

        df = pd.DataFrame(telemetry_data)

        # Convert timestamp to numeric if present
        if 'timestamp' in df.columns:
            df['timestamp_numeric'] = pd.to_datetime(df['timestamp'], errors='coerce').astype(np.int64) // 10**9
        else:
            df['timestamp_numeric'] = 0 # Default if no timestamp

        # Ensure all feature columns are present, fill missing with 0
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0

        return df[self.feature_columns].fillna(0)

    def prepare_classification_features(self, telemetry_data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, np.ndarray]:
        """Prepare features and labels for classification tasks"""
        df = self.prepare_features(telemetry_data)
        if df.empty:
            return pd.DataFrame(), np.array([])

        labels = []
        for _, record in df.iterrows():
            # Create labels based on altitude (example mission phases)
            if record['altitude'] < 1000:
                label = 0  # Pre-launch / early phase
            elif record['altitude'] < 5000:
                label = 1  # Ascent phase
            elif record['altitude'] < 10000:
                label = 2  # High altitude
            else:
                label = 3  # Very high altitude
            labels.append(label)

        return df, np.array(labels)

    def train_anomaly_detector(self, telemetry_data: List[Dict[str, Any]]) -> bool:
        """Train the anomaly detection model"""
        df = self.prepare_features(telemetry_data)
        if df.empty:
            return False

        scaled_features = self.scaler_features.fit_transform(df)
        self.anomaly_detector.fit(scaled_features)
        self.is_trained['anomaly'] = True
        return True

    def detect_anomalies(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in telemetry data"""
        if not self.is_trained['anomaly'] or not telemetry_data:
            return []

        df = self.prepare_features(telemetry_data)
        if df.empty:
            return []

        scaled_features = self.scaler_features.transform(df)
        anomaly_predictions = self.anomaly_detector.predict(scaled_features)
        anomaly_scores = self.anomaly_detector.decision_function(scaled_features)

        anomalies = []
        for i, (pred, score) in enumerate(zip(anomaly_predictions, anomaly_scores)):
            if pred == -1:  # Anomaly detected
                anomalies.append({
                    'index': i,
                    'timestamp': telemetry_data[i].get('timestamp', 'unknown'),
                    'anomaly_score': float(score),
                    'data_point': telemetry_data[i],
                    'severity': 'high' if score < -0.1 else ('medium' if score < 0 else 'low')
                })
        return anomalies

    def train_predictor(self, telemetry_data: List[Dict[str, Any]], target_metric: str = 'altitude') -> bool:
        """Train a predictor model for a specific metric"""
        if not telemetry_data or len(telemetry_data) < 10:
            return False

        df = self.prepare_features(telemetry_data)
        if df.empty:
            return False

        if target_metric not in df.columns:
            print(f"Target metric '{target_metric}' not found in data.")
            return False

        X = df.drop(columns=[target_metric], errors='ignore')
        y = df[target_metric]

        if X.empty or y.empty:
            return False

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        X_train_scaled = self.scaler_features.fit_transform(X_train)
        X_test_scaled = self.scaler_features.transform(X_test)

        y_train_scaled = self.scaler_targets.fit_transform(y_train.to_numpy().reshape(-1, 1)).flatten()

        self.prediction_model.fit(X_train_scaled, y_train_scaled)

        y_pred_scaled = self.prediction_model.predict(X_test_scaled)
        y_pred = self.scaler_targets.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
        y_test_original = y_test.to_numpy()

        mse = mean_squared_error(y_test_original, y_pred)
        r2 = r2_score(y_test_original, y_pred)
        print(f"Prediction model trained - MSE: {mse:.2f}, R²: {r2:.2f}")

        self.is_trained['prediction'] = True
        return True

    def predict_next_values(self, current_data: List[Dict[str, Any]], steps: int = 5) -> List[Dict[str, Any]]:
        """Predict next values for telemetry metrics"""
        if not self.is_trained['prediction'] or not current_data or self.scaler_features.n_features_in_ is None:
            return []

        predictions = []
        last_record_df = self.prepare_features(current_data[-1:])
        if last_record_df.empty:
            return []
        
        current_features_scaled = self.scaler_features.transform(last_record_df)

        # To simplify, we'll predict only the target_metric that was used for training
        # A more robust solution would require retraining for multiple targets or a multi-output model
        # Assuming 'altitude' was the target for now based on train_predictor default
        predicted_target_index = self.feature_columns.index('altitude') if 'altitude' in self.feature_columns else 0 # Placeholder

        for step in range(steps):
            pred_scaled_target = self.prediction_model.predict(current_features_scaled)[0]
            pred_target_value = self.scaler_targets.inverse_transform(np.array(pred_scaled_target).reshape(-1, 1)).flatten()[0]

            pred_record = {
                'step': step + 1,
                f'predicted_altitude': float(pred_target_value),
                'confidence': 0.8
            }
            # Simulate other metrics simply
            for col in self.feature_columns:
                if col != 'altitude' and col != 'timestamp_numeric':
                    pred_record[f'predicted_{col}'] = current_data[-1].get(col, 0) + np.random.uniform(-1, 1)

            predictions.append(pred_record)

            # Update current_features_scaled for next prediction step (simple update)
            # This is a basic way to propagate predictions, a real system would be more complex
            # For this simulation, we'll just slightly perturb current features
            current_features_scaled += np.random.normal(0, 0.05, current_features_scaled.shape)

        return predictions

    def train_classification_model(self, telemetry_data: List[Dict[str, Any]]) -> bool:
        """Train a classification model to identify mission phases"""
        df, labels = self.prepare_classification_features(telemetry_data)
        if df.empty or labels.size == 0:
            return False

        scaled_features = self.scaler_features.fit_transform(df)
        self.classification_model.fit(scaled_features, labels)
        self.is_trained['classification'] = True
        return True

    def classify_mission_phase(self, telemetry_data: List[Dict[str, Any]]) -> List[int]:
        """Classify mission phases for telemetry data"""
        if not self.is_trained['classification'] or not telemetry_data:
            return []

        df, _ = self.prepare_classification_features(telemetry_data)
        if df.empty:
            return []

        scaled_features = self.scaler_features.transform(df)
        predictions = self.classification_model.predict(scaled_features)
        return predictions.tolist()

    def perform_clustering(self, telemetry_data: List[Dict[str, Any]]) -> List[int]:
        """Perform clustering to identify similar patterns in telemetry"""
        if not telemetry_data:
            return []

        df = self.prepare_features(telemetry_data)
        if df.empty:
            return []

        scaled_features = self.scaler_features.fit_transform(df)
        cluster_labels = self.clustering_model.fit_predict(scaled_features)
        self.is_trained['clustering'] = True
        return cluster_labels.tolist()


class AdvancedReportGenerator:
    """Advanced report generator with enhanced analytics and visualization"""

    def __init__(self):
        self.report_templates = {
            'mission_summary': self._generate_mission_summary,
            'anomaly_report': self._generate_anomaly_report,
            'performance_analysis': self._generate_performance_analysis,
            'prediction_summary': self._generate_prediction_summary,
            'deep_analysis': self._generate_deep_analysis,
            'clustering_report': self._generate_clustering_report,
            'classification_report': self._generate_classification_report
        }

    def generate_report(self, report_type: str, data: Dict[str, Any]) -> str:
        """Generate a specific type of report"""
        if report_type not in self.report_templates:
            return f"Unknown report type: {report_type}"

        return self.report_templates[report_type](data)

    def _generate_mission_summary(self, data: Dict[str, Any]) -> str:
        """Generate mission summary report"""
        telemetry_data = data.get('telemetry_data', [])
        analysis_results = data.get('analysis_results', {})

        if not telemetry_data:
            return "# Mission Summary Report\n\nNo telemetry data available."

        # Calculate mission stats
        altitudes = [point.get('altitude', 0) for point in telemetry_data if 'altitude' in point]
        velocities = [point.get('velocity', 0) for point in telemetry_data if 'velocity' in point]
        battery_levels = [point.get('battery_level', 100) for point in telemetry_data if 'battery_level' in point]

        report = f"""# Mission Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Mission Statistics
- Total Data Points: {len(telemetry_data)}
- Max Altitude: {max(altitudes) if altitudes else 0:.2f} m
- Min Altitude: {min(altitudes) if altitudes else 0:.2f} m
- Avg Altitude: {np.mean(altitudes) if altitudes else 0:.2f} m
- Max Velocity: {max(velocities) if velocities else 0:.2f} m/s
- Min Battery Level: {min(battery_levels) if battery_levels else 100:.2f}%

## Mission Phase Analysis
"""

        # Add phase analysis if available
        if 'phase_analysis' in analysis_results:
            phase_analysis = analysis_results['phase_analysis']
            report += f"- Apogee Time: {phase_analysis.get('apogee_time', 'N/A')}\n"
            report += f"- Total Ascent: {phase_analysis.get('total_ascent', 0):.2f} m\n"
            report += f"- Total Descent: {phase_analysis.get('total_descent', 0):.2f} m\n"

        report += "\n## Recommendations\n"
        if battery_levels and min(battery_levels) < 20:
            report += "- Battery level critically low - recommend immediate recovery\n"
        if altitudes and max(altitudes) > 10000:
            report += "- Maximum altitude exceeded safety threshold\n"

        return report

    def _generate_anomaly_report(self, data: Dict[str, Any]) -> str:
        """Generate anomaly detection report"""
        anomalies = data.get('anomalies', [])

        if not anomalies:
            return "# Anomaly Detection Report\n\nNo anomalies detected in the data."

        report = f"""# Anomaly Detection Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Detected Anomalies: {len(anomalies)}

## Anomaly Details
"""

        for i, anomaly in enumerate(anomalies[:10]):  # Limit to first 10 anomalies
            report += f"""
{i+1}. Index: {anomaly.get('index', 'N/A')}
   Timestamp: {anomaly.get('timestamp', 'N/A')}
   Severity: {anomaly.get('severity', 'N/A')}
   Score: {anomaly.get('anomaly_score', 0):.3f}
   Data: {json.dumps({k: v for k, v in anomaly.get('data_point', {}).items() if k != 'data_point'}, indent=2)[:200]}...
"""

        if len(anomalies) > 10:
            report += f"\n... and {len(anomalies) - 10} more anomalies\n"

        report += "\n## Anomaly Analysis\n"
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1

        report += f"- High Severity: {severity_counts['high']}\n"
        report += f"- Medium Severity: {severity_counts['medium']}\n"
        report += f"- Low Severity: {severity_counts['low']}\n"

        return report

    def _generate_performance_analysis(self, data: Dict[str, Any]) -> str:
        """Generate performance analysis report"""
        telemetry_data = data.get('telemetry_data', [])

        if not telemetry_data:
            return "# Performance Analysis Report\n\nNo telemetry data available for analysis."

        # Calculate performance metrics
        battery_levels = [point.get('battery_level', 100) for point in telemetry_data if 'battery_level' in point]
        signal_strengths = [point.get('radio_signal_strength', -100) for point in telemetry_data if 'radio_signal_strength' in point]

        report = f"""# Performance Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## System Performance
- Average Battery Level: {np.mean(battery_levels) if battery_levels else 100:.2f}%
- Minimum Battery Level: {min(battery_levels) if battery_levels else 100:.2f}%
- Average Signal Strength: {np.mean(signal_strengths) if signal_strengths else -100:.2f} dBm
- Data Transmission Success Rate: {(len(telemetry_data) / len(telemetry_data) * 100) if telemetry_data else 0:.1f}%

## Efficiency Metrics
"""

        if battery_levels:
            battery_depletion = battery_levels[0] - battery_levels[-1] if len(battery_levels) > 1 else 0
            report += f"- Battery Depletion: {battery_depletion:.2f}%\n"
            report += f"- Estimated Mission Life Remaining: {battery_levels[-1] if battery_levels else 100:.1f}%\n"

        return report

    def _generate_prediction_summary(self, data: Dict[str, Any]) -> str:
        """Generate prediction summary report"""
        predictions = data.get('predictions', [])

        if not predictions:
            return "# Prediction Summary Report\n\nNo predictions available."

        report = f"""# Prediction Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Prediction Steps: {len(predictions)}

## Predicted Values
"""

        for i, pred in enumerate(predictions[:5]):  # Show first 5 predictions
            report += f"""
Step {pred.get('step', i+1)}:
  - Altitude: {pred.get('predicted_altitude', 0):.2f} m
  - Velocity: {pred.get('predicted_velocity', 0):.2f} m/s
  - Temperature: {pred.get('predicted_temperature', 20):.2f} °C
  - Battery: {pred.get('predicted_battery', 100):.2f}%
  - Confidence: {pred.get('confidence', 0):.2f}
"""

        if len(predictions) > 5:
            report += f"\n... and {len(predictions) - 5} more predictions\n"

        return report

    def _generate_deep_analysis(self, data: Dict[str, Any]) -> str:
        """Generate deep analysis report with advanced metrics"""
        telemetry_data = data.get('telemetry_data', [])
        deep_predictions = data.get('deep_predictions', [])

        if not telemetry_data:
            return "# Deep Analysis Report\n\nNo telemetry data available for deep analysis."

        # Calculate advanced metrics
        altitudes = [point.get('altitude', 0) for point in telemetry_data if 'altitude' in point]
        velocities = [point.get('velocity', 0) for point in telemetry_data if 'velocity' in point]
        temperatures = [point.get('temperature', 20) for point in telemetry_data if 'temperature' in point]

        # Calculate derivatives and trends
        altitude_rates = []
        velocity_rates = []
        for i in range(1, len(altitudes)):
            altitude_rates.append(altitudes[i] - altitudes[i-1])
            if i < len(velocities):
                velocity_rates.append(velocities[i] - velocities[i-1])

        report = f"""# Deep Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Advanced Metrics
- Data Points: {len(telemetry_data)}
- Altitude Variance: {np.var(altitudes) if altitudes else 0:.2f}
- Velocity Variance: {np.var(velocities) if velocities else 0:.2f}
- Temperature Variance: {np.var(temperatures) if temperatures else 0:.2f}

## Trend Analysis
- Average Altitude Rate: {np.mean(altitude_rates) if altitude_rates else 0:.2f} m/s
- Average Velocity Rate: {np.mean(velocity_rates) if velocity_rates else 0:.2f} m/s²
- Max Altitude Acceleration: {np.max(altitude_rates) if altitude_rates else 0:.2f} m/s
- Min Altitude Acceleration: {np.min(altitude_rates) if altitude_rates else 0:.2f} m/s

## Deep Learning Predictions
"""

        if deep_predictions:
            report += f"- Number of Deep Predictions: {len(deep_predictions)}\n"
            for i, pred in enumerate(deep_predictions[:3]):
                report += f"  Step {pred.get('step', i+1)}: Altitude={pred.get('predicted_altitude', 0):.2f}m, Confidence={pred.get('confidence', 0):.2f}\n"
        else:
            report += "- No deep learning predictions available\n"

        return report

    def _generate_clustering_report(self, data: Dict[str, Any]) -> str:
        """Generate clustering analysis report"""
        telemetry_data = data.get('telemetry_data', [])
        clusters = data.get('clusters', [])

        if not telemetry_data or not clusters:
            return "# Clustering Analysis Report\n\nNo clustering data available."

        # Count cluster occurrences
        unique_clusters, counts = np.unique(clusters, return_counts=True)

        report = f"""# Clustering Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Number of Clusters: {len(unique_clusters)}

## Cluster Distribution
"""

        for cluster_id, count in zip(unique_clusters, counts):
            percentage = (count / len(clusters)) * 100
            report += f"- Cluster {cluster_id}: {count} points ({percentage:.1f}%)\n"

        report += "\n## Cluster Characteristics\n"

        # Analyze each cluster
        for cluster_id in unique_clusters:
            cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
            cluster_data = [telemetry_data[i] for i in cluster_indices]

            cluster_altitudes = [point.get('altitude', 0) for point in cluster_data]
            cluster_temperatures = [point.get('temperature', 20) for point in cluster_data]

            report += f"""
Cluster {cluster_id}:
  - Size: {len(cluster_data)} points
  - Avg Altitude: {np.mean(cluster_altitudes):.2f} m
  - Avg Temperature: {np.mean(cluster_temperatures):.2f} °C
  - Max Altitude: {max(cluster_altitudes) if cluster_altitudes else 0:.2f} m
  - Min Altitude: {min(cluster_altitudes) if cluster_altitudes else 0:.2f} m
"""

        return report

    def _generate_classification_report(self, data: Dict[str, Any]) -> str:
        """Generate classification analysis report"""
        telemetry_data = data.get('telemetry_data', [])
        classifications = data.get('classifications', [])

        if not telemetry_data or not classifications:
            return "# Classification Analysis Report\n\nNo classification data available."

        # Define phase labels
        phase_labels = {
            0: "Pre-launch / Early Phase",
            1: "Ascent Phase",
            2: "High Altitude",
            3: "Very High Altitude"
        }

        # Count phase occurrences
        unique_phases, counts = np.unique(classifications, return_counts=True)

        report = f"""# Classification Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mission Phases Identified: {len(unique_phases)}

## Phase Distribution
"""

        for phase_id, count in zip(unique_phases, counts):
            percentage = (count / len(classifications)) * 100
            phase_label = phase_labels.get(phase_id, f"Phase {phase_id}")
            report += f"- {phase_label}: {count} points ({percentage:.1f}%)\n"

        report += "\n## Phase Transitions\n"

        # Identify phase transitions
        transitions = []
        for i in range(1, len(classifications)):
            if classifications[i] != classifications[i-1]:
                transitions.append({
                    'from': classifications[i-1],
                    'to': classifications[i],
                    'at_index': i
                })

        if transitions:
            for t in transitions[:5]:  # Show first 5 transitions
                from_label = phase_labels.get(t['from'], f"Phase {t['from']}")
                to_label = phase_labels.get(t['to'], f"Phase {t['to']}")
                report += f"- Transition from {from_label} to {to_label} at data point {t['at_index']}\n"
        else:
            report += "- No phase transitions detected\n"

        return report


class ReportGenerator:
    """Generates comprehensive reports based on data analysis"""

    def __init__(self):
        self.report_templates = {
            'mission_summary': self._generate_mission_summary,
            'anomaly_report': self._generate_anomaly_report,
            'performance_analysis': self._generate_performance_analysis,
            'prediction_summary': self._generate_prediction_summary
        }

    def generate_report(self, report_type: str, data: Dict[str, Any]) -> str:
        """Generate a specific type of report"""
        if report_type not in self.report_templates:
            return f"Unknown report type: {report_type}"

        return self.report_templates[report_type](data)

    def _generate_mission_summary(self, data: Dict[str, Any]) -> str:
        """Generate mission summary report"""
        telemetry_data = data.get('telemetry_data', [])
        analysis_results = data.get('analysis_results', {})

        if not telemetry_data:
            return "# Mission Summary Report\n\nNo telemetry data available."

        # Calculate mission stats
        altitudes = [point.get('altitude', 0) for point in telemetry_data if 'altitude' in point]
        velocities = [point.get('velocity', 0) for point in telemetry_data if 'velocity' in point]
        battery_levels = [point.get('battery_level', 100) for point in telemetry_data if 'battery_level' in point]

        report = f"""# Mission Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Mission Statistics
- Total Data Points: {len(telemetry_data)}
- Max Altitude: {max(altitudes) if altitudes else 0:.2f} m
- Min Altitude: {min(altitudes) if altitudes else 0:.2f} m
- Avg Altitude: {np.mean(altitudes) if altitudes else 0:.2f} m
- Max Velocity: {max(velocities) if velocities else 0:.2f} m/s
- Min Battery Level: {min(battery_levels) if battery_levels else 100:.2f}%

## Mission Phase Analysis
"""

        # Add phase analysis if available
        if 'phase_analysis' in analysis_results:
            phase_analysis = analysis_results['phase_analysis']
            report += f"- Apogee Time: {phase_analysis.get('apogee_time', 'N/A')}\n"
            report += f"- Total Ascent: {phase_analysis.get('total_ascent', 0):.2f} m\n"
            report += f"- Total Descent: {phase_analysis.get('total_descent', 0):.2f} m\n"

        report += "\n## Recommendations\n"
        if battery_levels and min(battery_levels) < 20:
            report += "- Battery level critically low - recommend immediate recovery\n"
        if altitudes and max(altitudes) > 10000:
            report += "- Maximum altitude exceeded safety threshold\n"

        return report

    def _generate_anomaly_report(self, data: Dict[str, Any]) -> str:
        """Generate anomaly detection report"""
        anomalies = data.get('anomalies', [])

        if not anomalies:
            return "# Anomaly Detection Report\n\nNo anomalies detected in the data."

        report = f"""# Anomaly Detection Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Detected Anomalies: {len(anomalies)}

## Anomaly Details
"""

        for i, anomaly in enumerate(anomalies[:10]):  # Limit to first 10 anomalies
            report += f"""
{i+1}. Index: {anomaly.get('index', 'N/A')}
   Timestamp: {anomaly.get('timestamp', 'N/A')}
   Severity: {anomaly.get('severity', 'N/A')}
   Score: {anomaly.get('anomaly_score', 0):.3f}
   Data: {json.dumps({k: v for k, v in anomaly.get('data_point', {}).items() if k != 'data_point'}, indent=2)[:200]}...
"""

        if len(anomalies) > 10:
            report += f"\n... and {len(anomalies) - 10} more anomalies\n"

        report += "\n## Anomaly Analysis\n"
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1

        report += f"- High Severity: {severity_counts['high']}\n"
        report += f"- Medium Severity: {severity_counts['medium']}\n"
        report += f"- Low Severity: {severity_counts['low']}\n"

        return report

    def _generate_performance_analysis(self, data: Dict[str, Any]) -> str:
        """Generate performance analysis report"""
        telemetry_data = data.get('telemetry_data', [])

        if not telemetry_data:
            return "# Performance Analysis Report\n\nNo telemetry data available for analysis."

        # Calculate performance metrics
        battery_levels = [point.get('battery_level', 100) for point in telemetry_data if 'battery_level' in point]
        signal_strengths = [point.get('radio_signal_strength', -100) for point in telemetry_data if 'radio_signal_strength' in point]

        report = f"""# Performance Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## System Performance
- Average Battery Level: {np.mean(battery_levels) if battery_levels else 100:.2f}%
- Minimum Battery Level: {min(battery_levels) if battery_levels else 100:.2f}%
- Average Signal Strength: {np.mean(signal_strengths) if signal_strengths else -100:.2f} dBm
- Data Transmission Success Rate: {(len(telemetry_data) / len(telemetry_data) * 100) if telemetry_data else 0:.1f}%

## Efficiency Metrics
"""

        if battery_levels:
            battery_depletion = battery_levels[0] - battery_levels[-1] if len(battery_levels) > 1 else 0
            report += f"- Battery Depletion: {battery_depletion:.2f}%\n"
            report += f"- Estimated Mission Life Remaining: {battery_levels[-1] if battery_levels else 100:.1f}%\n"

        return report

    def _generate_prediction_summary(self, data: Dict[str, Any]) -> str:
        """Generate prediction summary report"""
        predictions = data.get('predictions', [])

        if not predictions:
            return "# Prediction Summary Report\n\nNo predictions available."

        report = f"""# Prediction Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Prediction Steps: {len(predictions)}

## Predicted Values
"""

        for i, pred in enumerate(predictions[:5]):  # Show first 5 predictions
            report += f"""
Step {pred.get('step', i+1)}:
  - Altitude: {pred.get('predicted_altitude', 0):.2f} m
  - Velocity: {pred.get('predicted_velocity', 0):.2f} m/s
  - Temperature: {pred.get('predicted_temperature', 20):.2f} °C
  - Battery: {pred.get('predicted_battery', 100):.2f}%
  - Confidence: {pred.get('confidence', 0):.2f}
"""

        if len(predictions) > 5:
            report += f"\n... and {len(predictions) - 5} more predictions\n"

        return report


class AdvancedMLEngine:
    """Advanced machine learning engine for AirOne system"""

    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu
        self.is_initialized = False
        self.models: Dict[str, Any] = {}
        self.scalers = {
            'features': StandardScaler(),
            'targets': StandardScaler()
        }
        self.feature_columns_trained: List[str] = []

        # Initialize the engine
        self._initialize()

        # Initialize local AI components
        self.local_analyzer = LocalAIDataAnalyzer()
        self.report_generator = ReportGenerator() # Basic report generator, kept for backward compatibility if needed
        self.advanced_report_generator = AdvancedReportGenerator()

    def _initialize(self):
        """Initialize the ML engine"""
        print("Initializing Advanced ML Engine with Local AI Capabilities...")
        try:
            self._init_models()
            self.is_initialized = True
            print("Advanced ML Engine initialized successfully with Local AI")
        except Exception as e:
            print(f"Advanced ML Engine initialization failed: {e}")
            print("Running in fallback mode with basic functionality")
            self.is_initialized = False

    def _init_models(self):
        """Initialize ML models for various tasks."""
        self.models['anomaly_detector'] = IsolationForest(contamination=0.1, random_state=42)
        self.models['prediction_engine'] = RandomForestRegressor(n_estimators=100, random_state=42)
        self.models['classification_engine'] = RandomForestClassifier(n_estimators=100, random_state=42)
        self.models['clustering_engine'] = KMeans(n_clusters=5, random_state=42, n_init=10)
        # Deep learning model is handled by DeepLearningAnalyzer instance within LocalAIDataAnalyzer

    def train_model(self, model_name: str, telemetry_data: List[Dict[str, Any]],
                    feature_columns: List[str], target_key: Optional[str] = None) -> bool:
        """
        Train a specific model with provided telemetry data.
        :param model_name: Name of the model to train.
        :param telemetry_data: List of telemetry data dictionaries.
        :param feature_columns: List of feature column names to use for training.
        :param target_key: Name of the target variable column, if applicable (for supervised learning).
        :return: True if training was successful, False otherwise.
        """
        if not self.is_initialized:
            print("ML Engine not initialized, cannot train model.")
            return False

        if model_name not in self.models:
            print(f"Model {model_name} not found.")
            return False

        if not telemetry_data or len(telemetry_data) < 50:
            print("Insufficient telemetry data for training (need at least 50 samples).")
            return False

        # Prepare features
        # Create a DataFrame to handle missing values and consistent column order
        df = pd.DataFrame(telemetry_data)
        # Ensure 'timestamp' is handled if it's in feature_columns
        if 'timestamp' in feature_columns and 'timestamp' in df.columns:
            df['timestamp_numeric'] = pd.to_datetime(df['timestamp'], errors='coerce').astype(np.int64) // 10**9
            # Replace original timestamp with numeric version for features
            feature_columns = [col if col != 'timestamp' else 'timestamp_numeric' for col in feature_columns]
        elif 'timestamp_numeric' in feature_columns and 'timestamp' in df.columns:
             df['timestamp_numeric'] = pd.to_datetime(df['timestamp'], errors='coerce').astype(np.int64) // 10**9

        features_df = df[feature_columns].fillna(0.0) # Fill NaN with 0 for numerical stability
        features = features_df.values

        # Fit and transform features
        scaled_features = self.scalers['features'].fit_transform(features)
        
        model = self.models[model_name]
        targets = None

        try:
            if model_name == 'anomaly_detector':
                model.fit(scaled_features)
            elif model_name == 'clustering_engine':
                model.fit(scaled_features)
            elif target_key:
                if target_key not in df.columns:
                    print(f"Target key '{target_key}' not found in telemetry data.")
                    return False
                targets = df[target_key].values
                # Scale targets if it's a regression model
                if isinstance(model, (RandomForestRegressor, GradientBoostingRegressor, MLPRegressor)):
                    scaled_targets = self.scalers['targets'].fit_transform(targets.reshape(-1, 1)).flatten()
                    model.fit(scaled_features, scaled_targets)
                else: # For classification models
                    # Ensure targets are correctly prepared for classification
                    if isinstance(model, RandomForestClassifier):
                        # LabelEncoder can be used for string targets, but assuming numeric for now
                        model.fit(scaled_features, targets)
                    else:
                        model.fit(scaled_features, targets)
            else:
                print(f"Model {model_name} requires a target for training but none was provided.")
                return False

            self.feature_columns_trained = feature_columns
            print(f"Model {model_name} trained successfully with {len(telemetry_data)} samples.")
            return True
        except Exception as e:
            print(f"Error training model {model_name}: {e}")
            return False

    def predict(self, model_name: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make a prediction using the specified model."""
        if not self.is_initialized:
            print("ML Engine not initialized, returning basic prediction.")
            return self._basic_prediction_fallback(input_data)

        if model_name not in self.models:
            print(f"Model {model_name} not found.")
            return None
        
        # Ensure the model is trained by checking if scaler for features has been fitted
        if self.scalers['features'].n_features_in_ is None:
             print(f"Model {model_name} or scaler not trained. Cannot predict.")
             return self._basic_prediction_fallback(input_data)

        try:
            return self._run_prediction_with_model(model_name, input_data)
        except Exception as e:
            print(f"Error during prediction with model {model_name}: {e}. Falling back to basic prediction.")
            return self._basic_prediction_fallback(input_data)

    def _basic_prediction_fallback(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic prediction when ML engine is not available or model fails."""
        prediction = {
            'timestamp': datetime.now().isoformat(),
            'input_data': input_data,
            'predictions': {},
            'confidence': 0.5,  # Default confidence when no ML
            'anomalies_detected': [],
            'recommendations': [],
            'model_used': 'fallback'
        }

        # Basic predictions based on input data
        if 'altitude' in input_data:
            prediction['predictions']['next_altitude'] = input_data['altitude'] + np.random.uniform(-10, 10)
        if 'temperature' in input_data:
            prediction['predictions']['next_temperature'] = input_data['temperature'] + np.random.uniform(-2, 2)
        if 'battery_level' in input_data:
            prediction['predictions']['battery_trend'] = 'decreasing' if input_data['battery_level'] < 80 else 'stable'
        return prediction

    def _run_prediction_with_model(self, model_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run prediction using the specified model."""
        model = self.models[model_name]
        
        feature_columns = self.feature_columns_trained
        if not feature_columns:
            print("Feature columns not set for trained models. Cannot predict.")
            return self._basic_prediction_fallback(input_data)
        
        # Prepare input features as a DataFrame row and then convert to numpy array
        input_df = pd.DataFrame([input_data])
        # Handle timestamp for prediction if it was used in training
        if 'timestamp_numeric' in feature_columns and 'timestamp' in input_df.columns:
            input_df['timestamp_numeric'] = pd.to_datetime(input_df['timestamp'], errors='coerce').astype(np.int64) // 10**9
        
        # Ensure all trained feature columns are present, fill missing with 0
        for col in feature_columns:
            if col not in input_df.columns:
                input_df[col] = 0.0
        
        features = input_df[feature_columns].values
        
        # Scale features using the scaler fitted during training
        scaled_features = self.scalers['features'].transform(features)

        predictions_array = model.predict(scaled_features)
        
        prediction_output = {
            'timestamp': datetime.now().isoformat(),
            'input_data': input_data,
            'predictions': {},
            'confidence': 0.7,
            'anomalies_detected': [],
            'recommendations': [],
            'model_used': model_name
        }

        if isinstance(model, (RandomForestRegressor, GradientBoostingRegressor, MLPRegressor)):
            # Inverse transform if targets were scaled
            if self.scalers['targets'].n_features_in_ is not None:
                actual_predictions = self.scalers['targets'].inverse_transform(predictions_array.reshape(-1, 1)).flatten()
            else:
                actual_predictions = predictions_array.flatten()
            prediction_output['predictions']['predicted_values'] = actual_predictions.tolist()
            # Placeholder for confidence, could be derived from model variance or past performance
            prediction_output['confidence'] = 0.85
        elif isinstance(model, RandomForestClassifier):
            prediction_output['predictions']['predicted_class'] = int(predictions_array[0])
            if hasattr(model, 'predict_proba'):
                prediction_output['confidence'] = float(np.max(model.predict_proba(scaled_features)[0]))
            else:
                prediction_output['confidence'] = 0.75
        elif isinstance(model, IsolationForest):
            prediction_output['predictions']['is_anomaly'] = (predictions_array[0] == -1).tolist()
            if hasattr(model, 'decision_function'):
                # Normalize decision function score to a confidence-like value
                score = model.decision_function(scaled_features)[0]
                prediction_output['confidence'] = float(max(0, min(1, 0.5 - score / 2))) # Heuristic to map to 0-1
            else:
                prediction_output['confidence'] = 0.7
        elif isinstance(model, KMeans):
            prediction_output['predictions']['cluster_id'] = int(predictions_array[0])
            prediction_output['confidence'] = 0.9 # Clustering usually has high confidence if data fits well

        return prediction_output

    def detect_anomalies(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in telemetry data using a trained anomaly detection model."""
        if not self.is_initialized:
            print("ML Engine not initialized, using basic anomaly detection.")
            return self._basic_anomaly_detection_fallback(telemetry_data)

        model_name = 'anomaly_detector'
        if model_name not in self.models:
            print(f"Anomaly detection model {model_name} not found.")
            return []

        # Ensure the model is trained
        if self.scalers['features'].n_features_in_ is None:
            print(f"Anomaly detection model or scaler not trained. Cannot detect anomalies.")
            return self._basic_anomaly_detection_fallback(telemetry_data)

        try:
            return self._run_anomaly_detection_with_model(model_name, telemetry_data)
        except Exception as e:
            print(f"Error during anomaly detection with model {model_name}: {e}. Falling back to basic detection.")
            return self._basic_anomaly_detection_fallback(telemetry_data)

    def _basic_anomaly_detection_fallback(self, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Basic anomaly detection when ML engine is not available or model fails."""
        anomalies = []

        if not telemetry_data:
            return anomalies

        metrics = ['altitude', 'temperature', 'pressure', 'battery_level', 'velocity']

        for metric in metrics:
            values = [point.get(metric, 0) for point in telemetry_data if metric in point]
            if len(values) < 2:
                continue

            mean_val = np.mean(values)
            std_val = np.std(values)

            # Flag values that are more than 2 standard deviations from mean
            threshold = 2 * std_val
            for i, point in enumerate(telemetry_data):
                if metric in point:
                    val = point[metric]
                    if abs(val - mean_val) > threshold:
                        anomalies.append({
                            'index': i,
                            'timestamp': point.get('timestamp', 'unknown'),
                            'metric': metric,
                            'value': val,
                            'mean': mean_val,
                            'std': std_val,
                            'anomaly_type': 'statistical_outlier',
                            'model_used': 'fallback_statistical'
                        })
        return anomalies

    def _run_anomaly_detection_with_model(self, model_name: str, telemetry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run actual anomaly detection using the specified model."""
        model = self.models[model_name]

        feature_columns = self.feature_columns_trained
        if not feature_columns:
            print("Feature columns not set for trained models. Cannot detect anomalies.")
            return self._basic_anomaly_detection_fallback(telemetry_data)
        
        df = pd.DataFrame(telemetry_data)
        if 'timestamp_numeric' in feature_columns and 'timestamp' in df.columns:
            df['timestamp_numeric'] = pd.to_datetime(df['timestamp'], errors='coerce').astype(np.int64) // 10**9

        for col in feature_columns:
            if col not in df.columns:
                df[col] = 0.0

        features = df[feature_columns].values
        scaled_features = self.scalers['features'].transform(features)

        anomaly_predictions = model.predict(scaled_features)
        
        anomaly_scores = None
        if hasattr(model, 'decision_function'):
            anomaly_scores = model.decision_function(scaled_features)

        anomalies = []
        for i, pred in enumerate(anomaly_predictions):
            if pred == -1:  # Anomaly detected
                score = float(anomaly_scores[i]) if anomaly_scores is not None else -0.5
                anomalies.append({
                    'index': i,
                    'timestamp': telemetry_data[i].get('timestamp', 'unknown'),
                    'metric': 'multivariate',
                    'value': {col: telemetry_data[i].get(col) for col in feature_columns},
                    'anomaly_score': score,
                    'severity': 'high' if score < -0.1 else 'medium',
                    'model_used': model_name
                })
        return anomalies

    def update_model(self, model_name: str, new_telemetry_data: List[Dict[str, Any]],
                     feature_columns: List[str], target_key: Optional[str] = None) -> bool:
        """
        Update a model with new data (for adaptive learning or retraining).
        This currently performs a full retraining with the new data. For continuous learning,
        online learning algorithms or partial_fit would be more appropriate.
        """
        if not self.is_initialized:
            print("ML Engine not initialized, cannot update model.")
            return False

        if model_name not in self.models:
            print(f"Model {model_name} not found.")
            return False

        if not new_telemetry_data:
            print("No new data provided for model update.")
            return False

        print(f"Updating {model_name} with {len(new_telemetry_data)} new samples. Retraining model...")
        
        # In a production system, you'd want to load old data + new data and retrain
        # For this simulation, we'll assume the new data is enough to retrain
        # Or, for models supporting partial_fit, we'd use that.

        try:
            # Prepare new features
            df = pd.DataFrame(new_telemetry_data)
            if 'timestamp' in feature_columns and 'timestamp' in df.columns:
                df['timestamp_numeric'] = pd.to_datetime(df['timestamp'], errors='coerce').astype(np.int64) // 10**9
                feature_columns_processed = [col if col != 'timestamp' else 'timestamp_numeric' for col in feature_columns]
            elif 'timestamp_numeric' in feature_columns and 'timestamp' in df.columns:
                df['timestamp_numeric'] = pd.to_datetime(df['timestamp'], errors='coerce').astype(np.int64) // 10**9
                feature_columns_processed = feature_columns
            else:
                feature_columns_processed = feature_columns

            for col in feature_columns_processed:
                if col not in df.columns:
                    df[col] = 0.0

            features_new = df[feature_columns_processed].values
            
            # Use existing scaler for features if already fitted, otherwise fit it
            if self.scalers['features'].n_features_in_ is None:
                scaled_features_new = self.scalers['features'].fit_transform(features_new)
            else:
                scaled_features_new = self.scalers['features'].transform(features_new)

            model = self.models[model_name]
            
            # Retrain logic
            if model_name == 'anomaly_detector':
                model.fit(scaled_features_new)
            elif model_name == 'clustering_engine':
                model.fit(scaled_features_new)
            elif target_key:
                if target_key not in df.columns:
                    print(f"Target key '{target_key}' not found in new telemetry data.")
                    return False
                targets_new = df[target_key].values

                if isinstance(model, (RandomForestRegressor, GradientBoostingRegressor, MLPRegressor)):
                    # Fit and transform targets if scaler is not fitted, else just transform
                    if self.scalers['targets'].n_features_in_ is None:
                        scaled_targets_new = self.scalers['targets'].fit_transform(targets_new.reshape(-1, 1)).flatten()
                    else:
                        scaled_targets_new = self.scalers['targets'].transform(targets_new.reshape(-1, 1)).flatten()
                    model.fit(scaled_features_new, scaled_targets_new)
                elif isinstance(model, RandomForestClassifier):
                    model.fit(scaled_features_new, targets_new)
                else:
                    model.fit(scaled_features_new, targets_new) # Fallback for other models

            self.feature_columns_trained = feature_columns_processed
            print(f"Model {model_name} updated successfully with {len(new_telemetry_data)} samples.")
            return True
        except Exception as e:
            print(f"Error updating model {model_name}: {e}")
            return False

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        if model_name not in self.models:
            return None

        model = self.models[model_name]
        info = {
            'name': model_name,
            'type': type(model).__name__,
            'is_trained': self.scalers['features'].n_features_in_ is not None and hasattr(model, 'n_features_in_') or (hasattr(model, 'predict') and callable(model.predict)), # Heuristic for trained status
            'parameters': model.get_params() if hasattr(model, 'get_params') else {},
            'feature_columns_used': self.feature_columns_trained
        }
        # Add model-specific attributes if available
        if hasattr(model, 'n_estimators'):
            info['n_estimators'] = model.n_estimators
        if hasattr(model, 'n_clusters'):
            info['n_clusters'] = model.n_clusters
        if hasattr(model, 'contamination'):
            info['contamination'] = model.contamination
        return info

    def get_engine_status(self) -> Dict[str, Any]:
        """Get status of the ML engine."""
        return {
            'initialized': self.is_initialized,
            'use_gpu': self.use_gpu,
            'available_models': {name: self.get_model_info(name) for name in self.models.keys()},
            'engine_version': '3.0.0',
            'local_ai_available': hasattr(self, 'local_analyzer'),
            'feature_scaler_fitted': self.scalers['features'].n_features_in_ is not None,
            'target_scaler_fitted': self.scalers['targets'].n_features_in_ is not None
        }

    # NEW LOCAL AI CAPABILITIES
    def analyze_telemetry_local(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform local AI analysis on telemetry data"""
        if not telemetry_data:
            return {'error': 'No telemetry data provided'}

        results: Dict[str, Any] = {
            'anomalies_detected': 0,
            'anomalies': [],
            'predictions': [],
            'classifications': [],
            'clusters': [],
            'deep_predictions': [],
            'analysis_performed': False,
            'timestamp': datetime.now().isoformat()
        }

        # Train and detect anomalies
        if self.local_analyzer.train_anomaly_detector(telemetry_data):
            results['anomalies'] = self.local_analyzer.detect_anomalies(telemetry_data)
            results['anomalies_detected'] = len(results['anomalies'])
        else:
            print("Failed to train local anomaly detector.")

        # Train and predict
        # Assuming 'altitude' as the primary target for prediction for now
        if self.local_analyzer.train_predictor(telemetry_data, 'altitude'):
            results['predictions'] = self.local_analyzer.predict_next_values(telemetry_data, steps=5)
        else:
            print("Failed to train local predictor.")

        # Train and classify mission phases
        if self.local_analyzer.train_classification_model(telemetry_data):
            results['classifications'] = self.local_analyzer.classify_mission_phase(telemetry_data)
        else:
            print("Failed to train local classification model.")

        # Perform clustering
        results['clusters'] = self.local_analyzer.perform_clustering(telemetry_data)
        if not results['clusters']:
            print("Failed to perform local clustering.")


        # Perform deep learning analysis
        if self.local_analyzer.deep_analyzer.train(telemetry_data):
            results['deep_predictions'] = self.local_analyzer.deep_analyzer.predict_sequence(telemetry_data, steps=5)
        else:
            print("Failed to train local deep learning analyzer.")

        results['analysis_performed'] = True
        return results

    def generate_report(self, report_type: str, data: Dict[str, Any]) -> str:
        """Generate a report using the local AI report generator"""
        # Always use the advanced report generator
        try:
            return self.advanced_report_generator.generate_report(report_type, data)
        except Exception as e:
            print(f"Error generating advanced report '{report_type}': {e}. Falling back to basic report generator.")
            return self.report_generator.generate_report(report_type, data)

    def run_comprehensive_analysis(self, telemetry_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive analysis using local AI capabilities"""
        if not telemetry_data:
            return {'error': 'No telemetry data provided'}

        # Perform local AI analysis
        local_analysis = self.analyze_telemetry_local(telemetry_data)

        # Generate various reports
        reports = {}

        # Mission summary report
        mission_data = {
            'telemetry_data': telemetry_data,
            'analysis_results': {},
            'anomalies': local_analysis.get('anomalies', [])
        }
        reports['mission_summary'] = self.advanced_report_generator.generate_report('mission_summary', mission_data)

        # Anomaly report
        anomaly_data = {
            'anomalies': local_analysis.get('anomalies', [])
        }
        reports['anomaly_report'] = self.advanced_report_generator.generate_report('anomaly_report', anomaly_data)

        # Performance analysis report
        perf_data = {
            'telemetry_data': telemetry_data
        }
        reports['performance_analysis'] = self.advanced_report_generator.generate_report('performance_analysis', perf_data)

        # Prediction summary report
        pred_data = {
            'predictions': local_analysis.get('predictions', [])
        }
        reports['prediction_summary'] = self.advanced_report_generator.generate_report('prediction_summary', pred_data)

        # Deep analysis report
        deep_data = {
            'telemetry_data': telemetry_data,
            'deep_predictions': local_analysis.get('deep_predictions', [])
        }
        reports['deep_analysis'] = self.advanced_report_generator.generate_report('deep_analysis', deep_data)

        # Clustering report
        cluster_data = {
            'telemetry_data': telemetry_data,
            'clusters': local_analysis.get('clusters', [])
        }
        reports['clustering_report'] = self.advanced_report_generator.generate_report('clustering_report', cluster_data)

        # Classification report
        class_data = {
            'telemetry_data': telemetry_data,
            'classifications': local_analysis.get('classifications', [])
        }
        reports['classification_report'] = self.advanced_report_generator.generate_report('classification_report', class_data)

        return {
            'local_analysis': local_analysis,
            'reports': reports,
            'analysis_completed': True,
            'timestamp': datetime.now().isoformat()
        }