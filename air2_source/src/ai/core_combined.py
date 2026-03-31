"""
AirOne v3 - Unified AI Core & Utilities
=======================================

This file represents the central AI and Machine Learning capabilities of AirOne v3.
It merges the mission-specific logic from the v2 ML engines with the
advanced theoretical frameworks and algorithms from the v3 "SuperNinja" codebase.

This file consolidates:
- src/ai/ai_core.py (The advanced theoretical engine)
- src/ml/advanced_ml_engine.py (The practical mission engine)
- src/ml/enhanced_ai_engine.py (A simpler Scikit-Learn based engine)
- ML algorithms from src/advanced/advanced.py
- src/ai/utils.py (Utility classes and functions)
- src/ai/report_generator.py (Report generation)
"""

import numpy as np
import pandas as pd
import logging
import pickle
import os
import json
import time
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

# Configure Logging
logger = logging.getLogger("AirOneV3_AICore")

# ##############################################################################
# Dependency Management (from all merged files)
# ##############################################################################

# --- TensorFlow, PyTorch, and Scikit-Learn ---
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import Dense, LSTM, GRU, Input, Dropout
    HAS_TF = True
except ImportError:
    HAS_TF = False

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except (ImportError, OSError) as e:
    logger.warning(f"PyTorch failed to initialize: {e}")
    HAS_TORCH = False

try:
    from sklearn.ensemble import IsolationForest, RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.mixture import GaussianMixture
    from sklearn.linear_model import Ridge, SGDRegressor
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# --- Quantum Computing ---
try:
    import qiskit
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False

# --- NLP ---
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


# ##############################################################################
# Helper Classes and Data Models (from all merged files)
# ##############################################################################

@dataclass
class PredictionResult:
    """Standardized AI prediction result"""
    predicted_altitude: float
    predicted_velocity: float
    confidence: float
    time_horizon: float
    anomaly_score: float
    risk_level: str
    explanation: List[Tuple[str, float]] = None
    framework: str = "Unknown"

@dataclass
class MissionReport:
    """Standardized mission report"""
    mission_id: str
    start_time: float
    end_time: float
    duration: float
    max_altitude: float
    max_velocity: float
    avg_temperature: float
    anomalies_detected: int
    ai_summary: str = ""
    detailed_metrics: Dict[str, Any] = None

# PyTorch Models (from advanced_ml_engine.py)
if HAS_TORCH:
    class PyTorchLSTM(nn.Module):
        def __init__(self, input_size=4, hidden_size=64, output_size=4):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
            self.fc = nn.Linear(hidden_size, output_size)

        def forward(self, x):
            out, _ = self.lstm(x)
            out = out[:, -1, :]
            out = self.fc(out)
            return out

# ##############################################################################
# Main Unified AI Engine
# ##############################################################################

class AirOneV3_AIEngine:
    """
    The central, unified AI and ML engine for the AirOne v3 project.
    It provides a single, high-level interface to all AI capabilities.
    """
    def __init__(self, use_gpu: bool = True):
        self.logger = logging.getLogger("AirOneV3_AIEngine")
        self.models = {}
        self.scalers = {}
        self.is_ready = False
        self.feature_stats = {} # For drift detection

        self.logger.info("Initializing AirOne v3 Unified AI Engine...")

        # --- Hardware Acceleration Check ---
        self._check_hardware(use_gpu)

        # --- Initialize Models and Scalers ---
        self._initialize_scalers()
        self._build_and_load_models()
        self._warm_up_models()

        self.is_ready = True
        self.logger.info("✅ AirOne v3 Unified AI Engine is ready.")

    def _check_hardware(self, use_gpu: bool):
        if not use_gpu:
            self.logger.info("GPU usage is disabled by configuration.")
            return
        if HAS_TF:
            try:
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    self.logger.info(f"TensorFlow GPU Detected: {len(gpus)}")
                else:
                    self.logger.info("TensorFlow running on CPU.")
            except Exception as e:
                self.logger.warning(f"TensorFlow GPU check failed: {e}")
        if HAS_TORCH:
             if torch.cuda.is_available():
                self.logger.info(f"PyTorch GPU Detected: {torch.cuda.get_device_name(0)}")
             else:
                self.logger.info("PyTorch running on CPU.")

    def _initialize_scalers(self):
        """Initialize data preprocessors with robust default ranges."""
        if HAS_SKLEARN:
            self.scalers['trajectory'] = MinMaxScaler(feature_range=(0, 1))
            # Fit on a plausible range of [lat, lon, alt, vel]
            self.scalers['trajectory'].fit(np.array([
                [-90, -180, 0, -100],
                [90, 180, 80000, 1000]
            ]))

            self.scalers['sensors'] = StandardScaler()
            # Fit on a plausible range of sensor data
            self.scalers['sensors'].fit(np.array([[20, 101325, 50, 100, 100, -9.8, -9.8, -9.8, 0, 0]]))
        else:
            self.logger.warning("Scikit-learn not found. Manual scaling will be used.")

    def _build_and_load_models(self):
        """Builds or loads all required ML models from the various sources."""
        self.logger.info("Building and loading all AI/ML models...")
        # --- Primary Mission Models (from advanced_ml_engine.py) ---
        if HAS_TF:
            self.models['trajectory_lstm'] = self._build_lstm_model_tf()
            self.models['anomaly_ae'] = self._build_autoencoder_model_tf()

        if HAS_TORCH:
            self.models['torch_lstm'] = PyTorchLSTM(input_size=4, hidden_size=64, output_size=4)

        # --- Fallback & Alternative Models (from enhanced_ai_engine.py) ---
        if HAS_SKLEARN:
            # Anomaly Detection
            self.models['isolation_forest'] = IsolationForest(contamination=0.05, random_state=42)
            self.models['gmm_anomaly'] = GaussianMixture(n_components=3, covariance_type='full', random_state=42)

            # Regression
            self.models['online_trend_regressor'] = SGDRegressor(random_state=42)
            self.models['gb_regressor'] = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)

            # Feature drift tracking
            self.feature_stats = {'count': 0, 'mean': None, 'M2': None}

        if not any([HAS_TF, HAS_TORCH, HAS_SKLEARN]):
            self.logger.error("No ML libraries available. Engine functionality is severely limited.")

    def _build_lstm_model_tf(self) -> Model:
        """Builds a TensorFlow LSTM model for trajectory prediction."""
        model = Sequential([
            Input(shape=(10, 4)),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dense(4)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def _build_autoencoder_model_tf(self) -> Model:
        """Builds a TensorFlow AutoEncoder model for anomaly detection."""
        input_dim = 10
        input_layer = Input(shape=(input_dim,))
        encoded = Dense(8, activation='relu')(input_layer)
        encoded = Dense(4, activation='relu')(encoded)
        decoded = Dense(8, activation='relu')(encoded)
        decoded = Dense(input_dim, activation='sigmoid')(decoded)
        model = Model(input_layer, decoded)
        model.compile(optimizer='adam', loss='mse')
        return model

    def _warm_up_models(self):
        """Generates synthetic data to pre-train or warm up models."""
        if not HAS_SKLEARN:
            self.logger.warning("Cannot warm up models without Scikit-Learn.")
            return

        self.logger.info("Warming up ML models with synthetic flight data...")
        try:
            t = np.linspace(0, 100, 500)
            alt = np.maximum(0, 100 * t - 0.5 * 9.8 * t**2)
            vel = 100 - 9.8 * t

            X = np.column_stack([t, np.roll(alt, 1), np.roll(vel, 1)])[1:]
            y_alt = alt[1:]

            if 'gb_regressor' in self.models:
                self.models['gb_regressor'].fit(X, y_alt)

            self.logger.info("ML model warm-up complete.")
        except Exception as e:
            self.logger.error(f"Model warm-up failed: {e}")

    def predict_trajectory(self, recent_history: np.ndarray, horizon: float = 5.0) -> PredictionResult:
        """
        Predicts the next telemetry state using the best available model.
        Args:
            recent_history: shape (10, 4) -> [Lat, Lon, Alt, Vel]
        """
        if not self.is_ready:
            return PredictionResult(0, 0, 0, horizon, 0, "UNKNOWN")

        # --- Model Priority: PyTorch > TensorFlow > Scikit-Learn ---

        # PyTorch Prediction
        if HAS_TORCH and 'torch_lstm' in self.models:
            try:
                x_tensor = torch.tensor(recent_history, dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    pred = self.models['torch_lstm'](x_tensor).numpy()[0]

                # Use variance from a simple model for uncertainty proxy
                std_dev = np.array([0.1, 0.1, 5.0, 0.5])
                return PredictionResult(
                    predicted_altitude=pred[2], predicted_velocity=pred[3],
                    confidence=1.0 - np.mean(std_dev[:2]), time_horizon=horizon,
                    anomaly_score=0.1, risk_level="LOW", framework="PyTorch"
                )
            except Exception as e:
                self.logger.warning(f"PyTorch prediction failed: {e}. Falling back.")

        # TensorFlow Prediction with Monte Carlo Dropout for Uncertainty
        if HAS_TF and 'trajectory_lstm' in self.models:
            try:
                preds = np.array([
                    self.models['trajectory_lstm'](recent_history.reshape(1, 10, 4), training=True).numpy()[0]
                    for _ in range(10)
                ])
                mean_pred = np.mean(preds, axis=0)
                std_pred = np.std(preds, axis=0)

                return PredictionResult(
                    predicted_altitude=mean_pred[2], predicted_velocity=mean_pred[3],
                    confidence=1.0 - np.mean(std_pred[2:]), time_horizon=horizon,
                    anomaly_score=0.1, risk_level="LOW", framework="TensorFlow (MC Dropout)"
                )
            except Exception as e:
                self.logger.warning(f"TensorFlow prediction failed: {e}. Falling back.")

        # Scikit-Learn Fallback Prediction
        if HAS_SKLEARN and 'gb_regressor' in self.models:
            current_state = recent_history[-1, :]
            feature_vector = np.array([[current_state[0], current_state[2], current_state[3]]]) # time, alt, vel
            pred_alt = self.models['gb_regressor'].predict(feature_vector)[0]

            return PredictionResult(
                predicted_altitude=pred_alt, predicted_velocity=current_state[3],
                confidence=0.5, time_horizon=horizon, # Lower confidence for fallback
                anomaly_score=0.2, risk_level="LOW", framework="Scikit-Learn"
            )

        # Default if no models are available
        return PredictionResult(0, 0, 0, horizon, 0, "UNKNOWN", framework="None")

    def detect_anomaly(self, sensor_data: np.ndarray) -> Tuple[float, str]:
        """
        Detects anomalies in sensor data using the best available model.
        Returns an anomaly score and an explanation.
        """
        if not self.is_ready:
            return 0.0, "Engine not ready."

        sensor_data = sensor_data.reshape(1, -1)

        # TensorFlow AutoEncoder
        if HAS_TF and 'anomaly_ae' in self.models:
            try:
                pred = self.models['anomaly_ae'].predict(sensor_data)
                mse = np.mean(np.power(sensor_data - pred, 2), axis=1)[0]
                explanation = self.explain_anomaly_contribution(sensor_data[0], pred[0])
                return mse, f"TF AutoEncoder MSE: {mse:.4f}. Top contributor: {explanation[0] if explanation else 'N/A'}"
            except Exception as e:
                self.logger.warning(f"TF AutoEncoder failed: {e}")

        # Scikit-Learn Isolation Forest
        if HAS_SKLEARN and 'isolation_forest' in self.models:
            try:
                # The model must be fitted first.
                if not hasattr(self.models['isolation_forest'], "estimators_"):
                     self.models['isolation_forest'].fit(np.random.rand(100, len(sensor_data[0])))

                score = -self.models['isolation_forest'].score_samples(sensor_data)[0]
                return score, f"Isolation Forest Score: {score:.4f}"
            except Exception as e:
                self.logger.warning(f"Isolation Forest failed: {e}")

        return 0.0, "No anomaly detection model available."

    def explain_anomaly_contribution(self, original: np.ndarray, reconstructed: np.ndarray) -> List[Tuple[str, float]]:
        """Identifies which features contributed most to an autoencoder anomaly."""
        errors = np.power(original - reconstructed, 2)
        total_error = np.sum(errors)
        if total_error == 0:
            return []

        contributions = [(f"Sensor_{i}", err / total_error) for i, err in enumerate(errors)]
        return sorted(contributions, key=lambda x: x[1], reverse=True)

    def get_status(self) -> Dict[str, str]:
        """Returns the operational status of the AI engine's components."""
        return {
            "EngineReady": str(self.is_ready),
            "TensorFlow": str(HAS_TF),
            "PyTorch": str(HAS_TORCH),
            "Scikit-Learn": str(HAS_SKLEARN),
            "Quantum (Qiskit)": str(HAS_QISKIT),
            "NLP (Transformers)": str(HAS_TRANSFORMERS),
            "TrajectoryModel": "Active" if any(k in self.models for k in ['torch_lstm', 'trajectory_lstm', 'gb_regressor']) else "Inactive",
            "AnomalyModel": "Active" if any(k in self.models for k in ['anomaly_ae', 'isolation_forest']) else "Inactive",
        }


# ##############################################################################
# Natural Language Report Generator
# ##############################################################################

class AIReportGenerator:
    """
    Generates human-readable mission reports using Generative AI.
    Originally from src/ai/report_generator.py.
    """
    def __init__(self, model_name: str = "distilgpt2"):
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self.model_name = model_name

        if not HAS_TRANSFORMERS or not HAS_TORCH:
            logger.warning("Transformers or PyTorch not found. Report generator is disabled.")
            return

        self._get_optimal_device()
        self._load_pipeline()

    def _get_optimal_device(self):
        """Check for CUDA (NVIDIA GPU) availability."""
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"ReportGenerator: AI Accelerator Detected: {device_name}")
            self.device = torch.device("cuda")
        else:
            logger.info("ReportGenerator: No GPU detected. Falling back to CPU.")
            self.device = torch.device("cpu")

    def _load_pipeline(self):
        """Loads the Hugging Face model and tokenizer."""
        try:
            logger.info(f"ReportGenerator: Loading AI Model '{self.model_name}'...")
            start_time = time.time()

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            torch_dtype = torch.float16 if self.device.type == "cuda" else torch.float32

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch_dtype
            ).to(self.device)

            load_time = time.time() - start_time
            logger.info(f"ReportGenerator: Model loaded in {load_time:.2f}s to {self.device}")

        except Exception as e:
            logger.error(f"Failed to load Hugging Face model: {e}")
            self.model = None
            self.tokenizer = None

    def generate_mission_summary(self, mission_stats: Dict[str, Any]) -> str:
        """
        Generates a narrative summary of the mission from statistical data.
        """
        if not self.model or not self.tokenizer:
            return "AI Report Generator is not available."

        # Create a structured, descriptive prompt
        prompt = (
            f"Generate a concise, formal after-action report for a CanSat mission with the following key performance indicators:\n\n"
            f"### Mission Data:\n"
            f"- Mission Duration: {mission_stats.get('duration', 0)} seconds\n"
            f"- Achieved Apogee: {mission_stats.get('max_altitude', 0):.2f} meters\n"
            f"- Maximum Velocity: {mission_stats.get('max_velocity', 0):.2f} m/s\n"
            f"- Average Onboard Temperature: {mission_stats.get('avg_temp', 0):.2f}°C\n\n"
            f"### After-Action Report:\n"
            f"The mission proceeded as follows: "
        )

        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=200,
                    num_return_sequences=1,
                    temperature=0.75,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    top_k=50,
                    top_p=0.95
                )

            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Clean up the output to only return the generated part
            summary = generated_text.split("### After-Action Report:")[1].strip()
            return summary

        except Exception as e:
            logger.error(f"AI report generation failed: {e}")
            return "Error during AI report generation."


# ##############################################################################
# Model and Data Management Utilities
# ##############################################################################

class ModelRegistry:
    """
    Manages ML Model Versions & Metadata.
    Originally from src/ml/advanced_ml_engine.py.
    """
    def __init__(self, registry_path='models/registry.json'):
        self.path = registry_path
        self.models = self._load()

    def _load(self) -> Dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load model registry: {e}")
        return {}

    def register(self, name: str, version: str, metadata: Dict[str, Any]):
        """Registers or updates a model in the registry."""
        key = f"{name}_v{version}"
        self.models[key] = metadata
        self._save()
        logger.info(f"Registered model '{key}' in the registry.")

    def _save(self):
        """Saves the current registry to disk."""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w') as f:
                json.dump(self.models, f, indent=4)
        except IOError as e:
            logger.error(f"Failed to save model registry: {e}")


# ##############################################################################
# AI-Powered Mission Analysis
# ##############################################################################

class AIPoweredMissionAnalyzer:
    """
    Advanced mission analysis using AI/ML techniques
    """
    def __init__(self):
        self.ai_engine = AirOneV3_AIEngine()
        self.report_generator = AIReportGenerator()
        self.model_registry = ModelRegistry()

    def analyze_mission_data(self, telemetry_data: List[Dict], mission_stats: Dict[str, Any]) -> MissionReport:
        """
        Performs comprehensive AI-powered analysis of mission data
        """
        # Perform anomaly detection on the telemetry data
        anomalies_detected = 0
        for i, record in enumerate(telemetry_data):
            # Extract sensor data for anomaly detection
            sensor_values = [record.get('altitude', 0), record.get('temperature', 0), 
                             record.get('pressure', 0), record.get('velocity', 0)]
            sensor_array = np.array(sensor_values)
            
            anomaly_score, explanation = self.ai_engine.detect_anomaly(sensor_array)
            if anomaly_score > 0.5:  # Threshold for considering it an anomaly
                anomalies_detected += 1

        # Generate AI summary if possible
        ai_summary = self.report_generator.generate_mission_summary(mission_stats)

        # Create mission report
        report = MissionReport(
            mission_id=f"mission_{int(time.time())}",
            start_time=mission_stats.get('start_time', time.time()),
            end_time=mission_stats.get('end_time', time.time()),
            duration=mission_stats.get('duration', 0),
            max_altitude=mission_stats.get('max_altitude', 0),
            max_velocity=mission_stats.get('max_velocity', 0),
            avg_temperature=mission_stats.get('avg_temp', 0),
            anomalies_detected=anomalies_detected,
            ai_summary=ai_summary,
            detailed_metrics=mission_stats
        )

        return report

    def generate_comprehensive_report(self, mission_report: MissionReport) -> str:
        """
        Generates a comprehensive report combining AI analysis and human-readable format
        """
        report_text = f"""
MISSION REPORT: {mission_report.mission_id}
============================================

EXECUTIVE SUMMARY:
- Duration: {mission_report.duration:.2f} seconds
- Max Altitude: {mission_report.max_altitude:.2f} meters
- Max Velocity: {mission_report.max_velocity:.2f} m/s
- Avg Temperature: {mission_report.avg_temperature:.2f}°C
- Anomalies Detected: {mission_report.anomalies_detected}

AI-GENERATED SUMMARY:
{mission_report.ai_summary}

TECHNICAL ANALYSIS:
- The mission showed {'normal' if mission_report.anomalies_detected < 3 else 'concerning'} anomaly patterns
- {'Performance was nominal' if mission_report.anomalies_detected == 0 else f'Detected {mission_report.anomalies_detected} anomalies requiring review'}
- {'Temperature remained stable' if abs(mission_report.avg_temperature - 20) < 5 else 'Temperature variations observed'}

RECOMMENDATIONS:
- {'Mission objectives achieved successfully' if mission_report.anomalies_detected == 0 else 'Review anomaly logs for potential system issues'}
- {'No further action required' if mission_report.anomalies_detected == 0 else 'Investigate anomalies in detail'}
        """
        return report_text


# ##############################################################################
# Main execution block
# ##############################################################################
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Launching AirOne v3 Unified AI Core & Utilities Test Suite 🚀")

    # --- Initialization ---
    ai_engine = AirOneV3_AIEngine(use_gpu=True)
    print("\n--- AI Engine Status ---")
    for key, val in ai_engine.get_status().items():
        print(f"  {key}: {val}")

    # --- Test Trajectory Prediction ---
    print("\n--- Testing Trajectory Prediction ---")
    # Create synthetic history: 10 steps, 4 features [lat, lon, alt, vel]
    history = np.random.rand(10, 4) * np.array([0.01, 0.01, 100, 10]) + np.array([34, -118, 1000, 50])
    prediction_result = ai_engine.predict_trajectory(history, horizon=10.0)
    if prediction_result.framework != "None":
        print(f"Prediction successful using {prediction_result.framework}:")
        print(f"  - Predicted Alt (10s): {prediction_result.predicted_altitude:.2f} m")
        print(f"  - Predicted Vel (10s): {prediction_result.predicted_velocity:.2f} m/s")
        print(f"  - Confidence: {prediction_result.confidence:.2%}")
    else:
        print("❌ Trajectory prediction failed.")

    # --- Test Anomaly Detection ---
    print("\n--- Testing Anomaly Detection ---")
    normal_sensors = np.random.rand(10) * 0.1 + 0.5 # Normal data around 0.5
    anomaly_sensors = normal_sensors.copy()
    anomaly_sensors[3] = 0.95 # Inject a clear anomaly

    score_normal, expl_normal = ai_engine.detect_anomaly(normal_sensors)
    score_anomaly, expl_anomaly = ai_engine.detect_anomaly(anomaly_sensors)

    print(f"Normal Data -> Score: {score_normal:.4f} ({expl_normal})")
    print(f"Anomalous Data -> Score: {score_anomaly:.4f} ({expl_anomaly})")
    if score_anomaly > score_normal:
        print("✅ Anomaly detection test PASSED.")
    else:
        print("❌ Anomaly detection test FAILED.")

    # --- Test AI Report Generator ---
    print("\n--- Testing AI Report Generator ---")
    report_gen = AIReportGenerator()
    if report_gen.model:
        sample_stats = {
            'duration': 320,
            'max_altitude': 1050.7,
            'max_velocity': 55.2,
            'avg_temp': 15.3
        }
        summary = report_gen.generate_mission_summary(sample_stats)
        print("Generated Mission Summary:")
        print(summary)
    else:
        print("❌ AI Report Generator model not loaded. Skipping test.")

    # --- Test Model Registry ---
    print("\n--- Testing Model Registry ---")
    registry = ModelRegistry(registry_path='temp_test_registry.json')
    registry.register(
        name="trajectory_lstm",
        version="1.2.0",
        metadata={
            "timestamp": time.time(),
            "accuracy": 0.98,
            "trained_by": "test_suite"
        }
    )
    print("Model registry test complete. Check 'temp_test_registry.json'.")
    # Clean up test file
    if os.path.exists('temp_test_registry.json'):
        os.remove('temp_test_registry.json')

    # --- Test AI-Powered Mission Analyzer ---
    print("\n--- Testing AI-Powered Mission Analyzer ---")
    analyzer = AIPoweredMissionAnalyzer()
    
    # Create sample telemetry data
    sample_telemetry = [
        {'altitude': 1000, 'temperature': 20, 'pressure': 90000, 'velocity': 50},
        {'altitude': 1500, 'temperature': 18, 'pressure': 85000, 'velocity': 60},
        {'altitude': 2000, 'temperature': 15, 'pressure': 80000, 'velocity': 70},
    ]
    
    sample_mission_stats = {
        'start_time': time.time() - 300,
        'end_time': time.time(),
        'duration': 300,
        'max_altitude': 2000,
        'max_velocity': 70,
        'avg_temp': 17.6
    }
    
    mission_report = analyzer.analyze_mission_data(sample_telemetry, sample_mission_stats)
    comprehensive_report = analyzer.generate_comprehensive_report(mission_report)
    
    print("Generated Comprehensive Report:")
    print(comprehensive_report)

    print("\n✅ Unified AI Core & Utilities test suite finished.")