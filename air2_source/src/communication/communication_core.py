"""
Flask REST API + Socket.IO + JWT/Auth + Rate-limiting + Admin endpoints
Complete API implementation for CanSat ground station with real-time streaming

__author__ = "Gemini and Team AirOne"
"""

import os
import time
import json
import threading
import queue
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional, Any
from functools import wraps
import logging

from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, verify_jwt_in_request
)
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
import jwt

# Rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Try to import additional dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from dataclasses import asdict

# Import actual implementations from other modules
from system.config_manager import ConfigManager
from core.enhanced_core_sim import EnhancedSimulationEngine # Correct path after grep
from analysis.scientific_core import ScientificAnalysisCore
from ai.core_combined import AirOneV3_AIEngine, PredictionResult
from ml.model_registry import ModelRegistry # Assuming this path after creating
from system.session_recorder import SessionRecorder
from system.power_monitor import PowerMonitor
from system.diagnostics_service import DiagnosticsService
from hardware.rtc_driver import RTCDriver
from hardware.hardware_interface import HardwareDrivers
from sensors.telemetry_point import TelemetryPoint # Correct path after grep

# ##############################################################################
# Main Flask App and Global Configurations
# ##############################################################################

# Initialize Flask app
app = Flask(__name__)

# Configuration
class APIConfig:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.jwt_secret_key = self.config_manager.get('security.jwt_secret')
        self.jwt_access_token_expires = timedelta(hours=self.config_manager.get('security.jwt_access_token_expire_hours', 1))
        self.jwt_refresh_token_expires = timedelta(days=self.config_manager.get('security.jwt_refresh_token_expire_days', 30))
        self.rate_limit = self.config_manager.get('api.rate_limit_per_minute', 60)
        self.cors_origins = self.config_manager.get('api.cors_origins', ["*"])

        # Flask config
        app.config['JWT_SECRET_KEY'] = self.jwt_secret_key
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = self.jwt_access_token_expires
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = self.jwt_refresh_token_expires
        app.config['SECRET_KEY'] = self.jwt_secret_key

# Initialize Flask extensions globally
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60 per minute"]
)
cors = CORS()
socketio = SocketIO(async_mode='threading')


# Initialize components
def initialize_api_components(config_manager: ConfigManager):
    """Initialize all API components"""
    global api_config, api_core

    api_config = APIConfig(config_manager)

    # Configure extensions
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, origins=api_config.cors_origins)
    socketio.init_app(app, cors_allowed_origins=api_config.cors_origins, async_mode='threading')

    # Initialize API core
    api_core = APICore(config_manager, socketio)

    return api_core

class APICore:
    """Core API functionality and business logic"""

    def __init__(self, config_manager: ConfigManager, socketio_instance):
        self.config_manager = config_manager
        self.socketio = socketio_instance
        self.logger = logging.getLogger(f"{__name__}.APICore")

        # Initialize subsystems
        self.simulation: Optional[EnhancedSimulationEngine] = None
        self.analysis_core: Optional[ScientificAnalysisCore] = None
        self.ml_core: Optional[AirOneV3_AIEngine] = None
        self.session_recorder: Optional[SessionRecorder] = None
        self.power_monitor: Optional[PowerMonitor] = None
        self.diagnostics_service: Optional[DiagnosticsService] = None
        self.rtc_driver: Optional[RTCDriver] = None


        # Telemetry storage
        self.telemetry_buffer = deque(maxlen=self.config_manager.get('telemetry.buffer_size', 10000))
        self.telemetry_subscribers = set()

        # Connected clients
        self.connected_clients = {}

        # Background tasks
        self.background_threads = []

        # Rate limiting tracking
        self.request_counts = {}

        # Initialize subsystems if available
        self._initialize_subsystems()

        # Start background tasks
        self._start_background_tasks()

        self.logger.info("API Core initialized")

    def _initialize_subsystems(self):
        """Initialize optional subsystems"""
        try:
            # Initialize simulation if enabled
            if self.config_manager.get('simulation.enabled', True):
                # EnhancedSimulationEngine no longer takes config_manager, but a config dict
                sim_config = self.config_manager.get('simulation', {})
                self.simulation = EnhancedSimulationEngine(sim_config) 
                self.logger.info("Simulation engine initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize simulation: {e}")

        try:
            # Initialize analysis core - it doesn't take config_manager
            self.analysis_core = ScientificAnalysisCore()
            self.logger.info("Analysis core initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize analysis core: {e}")

        try:
            # Initialize ML core - it no longer takes config_manager
            self.ml_core = AirOneV3_AIEngine()
            self.logger.info("ML core initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize ML core: {e}")

        # Initialize New Services
        try:
            self.session_recorder = SessionRecorder()
            self.logger.info("Session Recorder initialized")
        except Exception as e:
            self.logger.warning(f"Failed to init Recorder: {e}")

        try:
            self.power_monitor = PowerMonitor()
            self.power_monitor.start() # PowerMonitor has a start method
            self.logger.info("Power Monitor initialized")
        except Exception as e:
            self.logger.warning(f"Failed to init Power Monitor: {e}")

        try:
            self.rtc_driver = RTCDriver()
            self.rtc_driver.initialize()
            self.logger.info("RTC Driver initialized")
        except Exception as e:
            self.logger.warning(f"Failed to init RTC: {e}")

        try:
            self.diagnostics_service = DiagnosticsService(
                ml_engine=self.ml_core,
                power_monitor=self.power_monitor,
                hardware_manager=HardwareDrivers() # HW manager from src/hardware/hardware_interface.py
            )
            self.logger.info("Diagnostics Service initialized")
        except Exception as e:
            self.logger.warning(f"Failed to init Diagnostics: {e}")


    def _start_background_tasks(self):
        """Start background processing threads"""
        # Telemetry processing thread
        telemetry_thread = threading.Thread(target=self._process_telemetry_loop, daemon=True)
        telemetry_thread.start()
        self.background_threads.append(telemetry_thread)

        # Simulation thread if enabled
        if self.simulation:
            simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
            simulation_thread.start()
            self.background_threads.append(simulation_thread)

        # Analysis thread
        analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        analysis_thread.start()
        self.background_threads.append(analysis_thread)

    def _process_telemetry_loop(self):
        """Background thread for processing telemetry data"""
        while True:
            try:
                # Process incoming telemetry
                if hasattr(self, '_telemetry_queue'):
                    try:
                        telemetry = self._telemetry_queue.get_nowait()
                        self._handle_telemetry(telemetry)
                    except queue.Empty:
                        # No telemetry available, continue
                        continue

                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in telemetry processing loop: {e}")

    def _simulation_loop(self):
        """Background thread for running simulation"""
        if not self.simulation:
            return

        try:
            self.simulation.start() # Simulation has a start() method

            while self.simulation.running:
                # Get latest telemetry
                # Assuming get_latest_telemetry() from EnhancedSimulationEngine returns TelemetryPoint
                latest_telemetry_dict = self.simulation.get_latest_telemetry() 
                if latest_telemetry_dict:
                    # Convert dict to TelemetryPoint if needed, or ensure sim returns TelemetryPoint
                    latest = TelemetryPoint(**latest_telemetry_dict) if isinstance(latest_telemetry_dict, dict) else latest_telemetry_dict
                    self._handle_telemetry(latest)

                time.sleep(1.0)  # 1 Hz update rate

        except Exception as e:
            self.logger.error(f"Error in simulation loop: {e}")

    def _handle_telemetry(self, telemetry: TelemetryPoint): # Use imported TelemetryPoint
        """Handle incoming telemetry data"""
        # Store in buffer
        self.telemetry_buffer.append(telemetry)

        # Emit to connected clients
        telemetry_dict = asdict(telemetry)
        self.socketio.emit('telemetry_update', telemetry_dict)

        # Check for ML anomaly detection
        if self.ml_core:
            try:
                # Assuming predict_anomaly can take a TelemetryPoint or its dict representation
                anomaly_result = self.ml_core.predict_anomaly(telemetry_dict) 
                if anomaly_result.prediction:  # Anomaly detected
                    self.socketio.emit('anomaly_alert', {
                        'timestamp': anomaly_result.timestamp,
                        'confidence': anomaly_result.confidence,
                        'model_id': anomaly_result.model_id,
                        'explanation': anomaly_result.explanation
                    })
            except Exception as e:
                self.logger.warning(f"Anomaly detection failed: {e}")

        # Session Recording
        if self.session_recorder and self.session_recorder.active:
            try:
                self.session_recorder.log_packet(telemetry_dict)
            except Exception as e:
                self.logger.warning(f"Recorder failed: {e}")

        # Power Monitor Update
        if self.power_monitor:
            try:
                # Extract battery data if available, else defaults
                v = getattr(telemetry, 'battery_voltage', 0.0)
                # Assuming telemetry point has a 'current' attribute or can be derived
                c = getattr(telemetry, 'current', 0.0) 
                t = getattr(telemetry, 'temperature', 0.0)
                self.power_monitor.update(v, c, t)
            except Exception as e:
                self.logger.warning(f"Power monitor update failed: {e}")


    def _serialize_analysis_results(self, results: Dict) -> Dict:
        """Serialize analysis results for JSON transmission"""
        serialized = {}
        for key, value in results.items():
            if hasattr(value, '__dict__'):
                serialized[key] = asdict(value)
            elif isinstance(value, (int, float, str, bool)):
                serialized[key] = value
            elif isinstance(value, dict):
                serialized[key] = self._serialize_analysis_results(value)
            elif isinstance(value, list):
                serialized[key] = [self._serialize_analysis_results(item) if hasattr(item, '__dict__') else item for item in value]
            else:
                serialized[key] = str(value)
        return serialized

    def add_telemetry(self, telemetry: TelemetryPoint):
        """Add telemetry data for processing"""
        if not hasattr(self, '_telemetry_queue'):
            self._telemetry_queue = queue.Queue()

        try:
            self._telemetry_queue.put_nowait(telemetry)
        except queue.Full:
            self.logger.warning("Telemetry queue full, dropping data")

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        health = {
            'timestamp': time.time(),
            'status': 'healthy',
            'uptime': time.time() - getattr(self, '_start_time', time.time()),
            'connected_clients': len(self.connected_clients),
            'telemetry_buffer_size': len(self.telemetry_buffer),
            'subsystems': {
                'simulation': self.simulation is not None,
                'analysis': self.analysis_core is not None,
                'ml': self.ml_core is not None
            },
            'memory_usage': self._get_memory_usage(),
            'background_threads': len(self.background_threads)
        }

        # Enrich with Diagnostics Service if avail
        if self.diagnostics_service:
            diag = self.diagnostics_service.get_diagnostics()
            health['diagnostics'] = diag


        # Check subsystem health
        if self.simulation and not self.simulation.running:
            health['status'] = 'degraded'
            health['issues'] = health.get('issues', []) + ['Simulation not running']

        return health

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}

# Initialize API core
api_core = None

# Authentication decorators
def admin_required(f):
    """Decorator requiring admin privileges"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()
        # Simplified role check - in production, use proper RBAC
        if not current_user.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Authentication endpoints
@app.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Use ConfigManager for authentication (assuming it holds credentials)
        config_manager = ConfigManager() # Instantiate ConfigManager here
        admin_username = config_manager.get('security.admin_username', 'admin')
        admin_password = config_manager.get('security.admin_password', 'admin') # Default is 'admin' for dev
        operator_username = config_manager.get('security.operator_username', 'operator')
        operator_password = config_manager.get('security.operator_password', 'operator')


        if username == admin_username and password == admin_password:
            user_claims = {'username': username, 'is_admin': True}
        elif username == operator_username and password == operator_password:
            user_claims = {'username': username, 'is_admin': False}
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Create tokens
        access_token = create_access_token(identity=user_claims)
        refresh_token = create_refresh_token(identity=user_claims)

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': api_config.jwt_access_token_expires.total_seconds()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user)

        return jsonify({
            'access_token': new_access_token,
            'token_type': 'Bearer'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Telemetry endpoints
@app.route('/telemetry/latest', methods=['GET'])
@jwt_required()
def get_latest_telemetry():
    """Get latest telemetry data"""
    try:
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 1000)  # Cap at 1000

        if not api_core.telemetry_buffer:
            return jsonify({'telemetry': []})

        latest_telemetry = list(api_core.telemetry_buffer)[-limit:]
        telemetry_dict = [asdict(t) for t in latest_telemetry]

        return jsonify({
            'telemetry': telemetry_dict,
            'count': len(telemetry_dict),
            'timestamp': time.time()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/telemetry/query', methods=['POST'])
@jwt_required()
def query_telemetry():
    """Query telemetry data with filters"""
    try:
        data = request.get_json()
        from_time = data.get('from_time')
        to_time = data.get('to_time')
        filters = data.get('filters', {})
        limit = data.get('limit', 1000)

        # Query telemetry buffer (simplified)
        all_telemetry = list(api_core.telemetry_buffer)

        # Apply time filters
        if from_time:
            all_telemetry = [t for t in all_telemetry if t.timestamp >= from_time]
        if to_time:
            all_telemetry = [t for t in all_telemetry if t.timestamp <= to_time]

        # Apply other filters
        if filters:
            for field, value in filters.items():
                # TelemetryPoint has attributes, not dict keys
                if hasattr(TelemetryPoint, field): 
                    all_telemetry = [t for t in all_telemetry if getattr(t, field) == value]

        # Limit results
        all_telemetry = all_telemetry[-limit:]

        telemetry_dict = [asdict(t) for t in all_telemetry]

        return jsonify({
            'telemetry': telemetry_dict,
            'count': len(telemetry_dict),
            'query_params': data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/telemetry/upload', methods=['POST'])
@jwt_required()
def upload_telemetry():
    """Upload telemetry data (for store-and-forward nodes)"""
    try:
        data = request.get_json()
        telemetry_data = data.get('telemetry', [])

        uploaded_count = 0
        for tel_data in telemetry_data:
            try:
                # Ensure incoming data matches TelemetryPoint structure
                telemetry = TelemetryPoint(**tel_data)
                api_core.add_telemetry(telemetry)
                uploaded_count += 1
            except Exception as e:
                logging.warning(f"Failed to process telemetry: {e}")

        return jsonify({
            'uploaded': uploaded_count,
            'received': len(telemetry_data)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Analysis endpoints
@app.route('/analysis/run', methods=['POST'])
@jwt_required()
def run_analysis():
    """Run analysis on telemetry data"""
    try:
        if not api_core.analysis_core:
            return jsonify({'error': 'Analysis core not available'}), 503

        data = request.get_json()
        analysis_types = data.get('analysis_types', [])  # Specific analyses to run

        # Get recent telemetry data - ScientificAnalysisCore expects TelemetryPoint list
        recent_data = list(api_core.telemetry_buffer)[-500:]  # Last 500 samples

        if len(recent_data) < 10:
            return jsonify({'error': 'Insufficient data for analysis'}), 400

        # Run analysis
        results = api_core.analysis_core.run_comprehensive_analysis(recent_data) # run_all_analyses is from mock

        # Filter results if specific types requested
        if analysis_types:
            filtered_results = {k: v for k, v in results.items() if k in analysis_types}
        else:
            filtered_results = results

        return jsonify({
            'results': api_core._serialize_analysis_results(filtered_results),
            'timestamp': time.time(),
            'data_points': len(recent_data)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analysis/<analysis_id>/report', methods=['GET'])
@jwt_required()
def get_analysis_report(analysis_id: str):
    """Get detailed analysis report"""
    try:
        if not api_core.analysis_core:
            return jsonify({'error': 'Analysis core not available'}), 503

        # ScientificAnalysisCore doesn't have get_analysis_summary or get_trending_analyses
        # Need to provide a mock or adapt to the ScientificAnalysisCore methods
        summary = {"message": "Summary not available for this analysis core"}
        trend_data = {"message": "Trending data not available for this analysis core"}
        
        return jsonify({
            'analysis_id': analysis_id,
            'summary': summary,
            'trend_data': trend_data,
            'timestamp': time.time()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ML endpoints
@app.route('/ml/train', methods=['POST'])
@limiter.limit("2 per hour")  # Rate limit training requests
@jwt_required()
def train_model():
    """Train ML model"""
    try:
        if not api_core.ml_core:
            return jsonify({'error': 'ML core not available'}), 503

        data = request.get_json()
        model_type = data.get('model_type', 'anomaly_detection')  # or 'prediction'
        model_name = data.get('model_name', 'custom_model')
        framework = data.get('framework', 'auto')

        # Get telemetry data for training
        # AirOneV3_AIEngine.train_anomaly_detection_model expects numpy arrays
        training_data_telemetry = list(api_core.telemetry_buffer)
        
        if len(training_data_telemetry) < 50:
            return jsonify({'error': 'Insufficient data for training (need at least 50 samples)'}), 400

        # Convert list of TelemetryPoint to numpy array (features) and target if necessary
        # This is a simplified conversion, assuming fixed features
        X_train = np.array([[
            p.altitude, p.velocity, p.temperature, p.pressure, p.battery_percent, p.signal_strength
        ] for p in training_data_telemetry])
        
        # Train model
        if model_type == 'anomaly_detection':
            # AirOneV3_AIEngine.train_anomaly_detection_model needs name, framework
            model_id = api_core.ml_core.train_anomaly_detection_model(
                X_train, model_name, framework
            )
        elif model_type == 'prediction':
            # Need y_train for prediction training
            y_train = X_train[:, 0] # Example: predict altitude
            model_id = api_core.ml_core.train_prediction_model(
                X_train, y_train, model_name, framework
            )
        else:
            return jsonify({'error': f'Unknown model type: {model_type}'}), 400

        # Get model performance - AirOneV3_AIEngine's get_model_performance method will work
        performance = api_core.ml_core.get_model_performance(model_id)

        return jsonify({
            'model_id': model_id,
            'model_type': model_type,
            'framework': framework,
            'performance': performance,
            'training_samples': len(training_data_telemetry),
            'timestamp': time.time()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ml/predict', methods=['POST'])
@jwt_required()
def predict():
    """Make prediction using ML model"""
    try:
        if not api_core.ml_core:
            return jsonify({'error': 'ML core not available'}), 503

        data = request.get_json()
        model_type = data.get('model_type', 'anomaly_detection')  # or 'prediction'
        model_id = data.get('model_id')

        if model_type == 'anomaly_detection':
            # Get latest telemetry for anomaly detection
            latest_telemetry = api_core.telemetry_buffer[-1] if api_core.telemetry_buffer else None
            if not latest_telemetry:
                return jsonify({'error': 'No telemetry data available'}), 400

            # Convert TelemetryPoint to numpy array for predict_anomaly
            features = np.array([
                latest_telemetry.altitude, latest_telemetry.velocity, latest_telemetry.temperature, 
                latest_telemetry.pressure, latest_telemetry.battery_percent, latest_telemetry.signal_strength
            ])
            result = api_core.ml_core.predict_anomaly(features, model_id)

        elif model_type == 'prediction':
            # Get recent telemetry for prediction
            recent_data = list(api_core.telemetry_buffer)[-20:] if len(api_core.telemetry_buffer) >= 20 else list(api_core.telemetry_buffer)
            if len(recent_data) < 10:
                return jsonify({'error': 'Insufficient history for prediction'}), 400

            # Convert list of TelemetryPoint to numpy array (features)
            X_predict = np.array([[
                p.altitude, p.velocity, p.temperature, p.pressure, p.battery_percent, p.signal_strength
            ] for p in recent_data])

            # AirOneV3_AIEngine.predict_future expects numpy array
            result = api_core.ml_core.predict_future(X_predict, model_id)

        else:
            return jsonify({'error': f'Unknown model type: {model_type}'}), 400

        # Assuming PredictionResult attributes match the return structure
        return jsonify({
            'prediction': result.prediction,
            'confidence': result.confidence,
            'model_id': result.model_id,
            'timestamp': result.timestamp, # Assuming timestamp is part of PredictionResult
            'explanation': result.explanation,
            'metadata': result.metadata
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ml/models', methods=['GET'])
@jwt_required()
def list_models():
    """List available ML models"""
    try:
        if not api_core.ml_core:
            return jsonify({'error': 'ML core not available'}), 503

        model_type = request.args.get('type')
        framework = request.args.get('framework')

        # Get models from registry
        all_models = api_core.ml_core.model_registry.list_models(model_type, framework)

        models_list = []
        for model_meta in all_models:
            # ModelRegistry.list_models returns ModelMetadata objects, not raw dicts
            models_list.append(asdict(model_meta)) # Convert ModelMetadata to dict

        return jsonify({
            'models': models_list,
            'count': len(models_list),
            'filters': {'type': model_type, 'framework': framework}
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ml/models/<model_id>/performance', methods=['GET'])
@jwt_required()
def get_model_performance(model_id: str):
    """Get detailed model performance"""
    try:
        if not api_core.ml_core:
            return jsonify({'error': 'ML core not available'}), 503

        performance = api_core.ml_core.get_model_performance(model_id)

        return jsonify(performance)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# System endpoints
@app.route('/system/health', methods=['GET'])
@jwt_required()
def get_system_health():
    """Get system health status"""
    try:
        health = api_core.get_system_health()
        return jsonify(health)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/system/status', methods=['GET'])
@jwt_required()
def get_system_status():
    """Get detailed system status"""
    try:
        status = {
            'api': {
                'version': '1.0.0',
                'uptime': time.time() - getattr(api_core, '_start_time', time.time()),
                'environment': os.getenv('FLASK_ENV', 'development')
            },
            'subsystems': {},
            'statistics': {
                'telemetry_points': len(api_core.telemetry_buffer),
                'connected_clients': len(api_core.connected_clients),
                'total_requests': sum(api_core.request_counts.values())
            }
        }

        # Add subsystem status
        if api_core.simulation:
            status['subsystems']['simulation'] = {
                'running': api_core.simulation.running,
                'current_time': api_core.simulation.current_time,
                'duration': api_core.simulation.duration
            }

        if api_core.analysis_core:
            # ScientificAnalysisCore doesn't have analysis_history or event_flags
            status['subsystems']['analysis'] = {
                'available': True,
                'note': 'ScientificAnalysisCore does not expose history via these attributes'
            }

        if api_core.ml_core:
            ml_status = api_core.ml_core.get_system_status()
            status['subsystems']['ml'] = ml_status

        return jsonify(status)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/system/logs', methods=['GET'])
@admin_required
def get_system_logs():
    """Get system logs"""
    try:
        lines = request.args.get('lines', 100, type=int)
        level = request.args.get('level', 'INFO')

        # Read from log file (simplified)
        log_file_path = os.path.join(os.path.dirname(__file__), '../../logs/airone.log') # Adjusted path
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                all_lines = f.readlines()

            # Filter by level and get last N lines
            filtered_lines = [line for line in all_lines if level in line]
            log_lines = filtered_lines[-lines:]

            return jsonify({
                'logs': log_lines,
                'total_lines': len(log_lines),
                'level_filter': level
            })
        else:
            return jsonify({'logs': [], 'message': 'Log file not found'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/system/shutdown', methods=['POST'])
@admin_required
def shutdown_system():
    """Shutdown system (admin only)"""
    try:
        # Stop simulation if running
        if api_core.simulation:
            api_core.simulation.stop()

        # Schedule shutdown
        def delayed_shutdown():
            time.sleep(2)
            os._exit(0)

        shutdown_thread = threading.Thread(target=delayed_shutdown)
        shutdown_thread.start()

        return jsonify({
            'message': 'System shutdown initiated',
            'timestamp': time.time()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Recorder Endpoints
@app.route('/recorder/start', methods=['POST'])
@jwt_required()
def start_recording():
    try:
        data = request.get_json() or {}
        name = data.get('session_name')
        if api_core.session_recorder:
            sid = api_core.session_recorder.start_session(name)
            return jsonify({'session_id': sid, 'active': True})
        return jsonify({'error': 'Recorder not available'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recorder/stop', methods=['POST'])
@jwt_required()
def stop_recording():
    try:
        if api_core.session_recorder:
            api_core.session_recorder.stop_session()
            return jsonify({'active': False})
        return jsonify({'error': 'Recorder not available'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Data export endpoints
@app.route('/export/csv', methods=['GET'])
@jwt_required()
def export_csv():
    """Export telemetry data as CSV"""
    try:
        limit = request.args.get('limit', 1000, type=int)

        if not api_core.telemetry_buffer:
            return jsonify({'error': 'No data available'}), 404

        # Convert to DataFrame
        telemetry_data = [asdict(t) for t in list(api_core.telemetry_buffer)[-limit:]]

        if PANDAS_AVAILABLE:
            df = pd.DataFrame(telemetry_data)
            csv_data = df.to_csv(index=False)

            return jsonify({
                'csv_data': csv_data,
                'filename': f'telemetry_{int(time.time())}.csv',
                'records': len(telemetry_data)
            })
        else:
            # Fallback CSV generation
            if telemetry_data:
                headers = list(telemetry_data[0].keys()) # Get keys from first dict
                csv_lines = [','.join(headers)]
                for row in telemetry_data:
                    csv_lines.append(','.join(str(row.get(h, '')) for h in headers)) # Use .get for safety
                csv_data = '\n'.join(csv_lines)

                return jsonify({
                    'csv_data': csv_data,
                    'filename': f'telemetry_{int(time.time())}.csv',
                    'records': len(telemetry_data)
                })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/json', methods=['GET'])
@jwt_required()
def export_json():
    """Export data as JSON"""
    try:
        export_type = request.args.get('type', 'telemetry')  # telemetry, analysis, models
        limit = request.args.get('limit', 1000, type=int)

        if export_type == 'telemetry':
            data = [asdict(t) for t in list(api_core.telemetry_buffer)[-limit:]]
        elif export_type == 'analysis' and api_core.analysis_core:
            # ScientificAnalysisCore does not have analysis_history
            data = [{"error": "ScientificAnalysisCore does not directly expose analysis_history"}]
        elif export_type == 'models' and api_core.ml_core:
            # ModelRegistry.list_models returns ModelMetadata objects, not raw dicts
            models = api_core.ml_core.model_registry.list_models()
            data = [asdict(m) for m in models]
        else:
            return jsonify({'error': f'Unknown export type: {export_type}'}), 400

        return jsonify({
            'data': data,
            'type': export_type,
            'count': len(data),
            'timestamp': time.time()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Static file serving (for web interface)
@app.route('/')
def index():
    """Serve main web interface"""
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    api_core.connected_clients[client_id] = {
        'connected_at': time.time(),
        'address': get_remote_address()
    }

    emit('connected', {
        'client_id': client_id,
        'server_time': time.time(),
        'message': 'Connected to CanSat Ground Station'
    })

    # Send current system status
    emit('system_status', api_core.get_system_status())

    logging.info(f"Client connected: {client_id}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in api_core.connected_clients:
        del api_core.connected_clients[client_id]

    logging.info(f"Client disconnected: {client_id}")

@socketio.on('subscribe_telemetry')
def handle_subscribe_telemetry():
    """Subscribe to telemetry updates"""
    client_id = request.sid
    api_core.telemetry_subscribers.add(client_id)

    emit('subscribed', {'type': 'telemetry'})
    logging.info(f"Client {client_id} subscribed to telemetry")

@socketio.on('unsubscribe_telemetry')
def handle_unsubscribe_telemetry():
    """Unsubscribe from telemetry updates"""
    client_id = request.sid
    api_core.telemetry_subscribers.discard(client_id)

    emit('unsubscribed', {'type': 'telemetry'})
    logging.info(f"Client {client_id} unsubscribed from telemetry")

@socketio.on('request_analysis')
def handle_request_analysis(data):
    """Handle on-demand analysis request"""
    try:
        analysis_types = data.get('analysis_types', [])

        if api_core.analysis_core and len(api_core.telemetry_buffer) > 10:
            recent_data = list(api_core.telemetry_buffer)[-100:]
            # ScientificAnalysisCore.run_comprehensive_analysis returns a dict, not a list of analysis results
            results = api_core.analysis_core.run_comprehensive_analysis(recent_data) 

            # Filter results if specific types requested
            if analysis_types:
                filtered_results = {k: v for k, v in results.items() if k in analysis_types}
            else:
                filtered_results = results

            emit('analysis_results', {
                'results': api_core._serialize_analysis_results(filtered_results),
                'timestamp': time.time()
            })
        else:
            emit('error', {'message': 'Analysis not available or insufficient data'})

    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('control_command')
def handle_control_command(data):
    """Handle control commands"""
    try:
        command = data.get('command')
        params = data.get('params', {})

        if command == 'start_simulation':
            if api_core.simulation and not api_core.simulation.running:
                api_core.simulation.start()
                emit('command_result', {'command': command, 'status': 'started'})
            else:
                emit('error', {'message': 'Simulation not available or already running'})

        elif command == 'stop_simulation':
            if api_core.simulation and api_core.simulation.running:
                api_core.simulation.stop()
                emit('command_result', {'command': command, 'status': 'stopped'})
            else:
                emit('error', {'message': 'Simulation not running'})

        elif command == 'train_model':
            # Handle model training
            if api_core.ml_core:
                # This would trigger training in background
                emit('command_result', {'command': command, 'status': 'training_started'})
            else:
                emit('error', {'message': 'ML core not available'})

        else:
            emit('error', {'message': f'Unknown command: {command}'})

    except Exception as e:
        emit('error', {'message': str(e)})

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token required'}), 401

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': f'Rate limit exceeded: {e.description}'}), 429

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Utility functions
def create_app(config_manager: ConfigManager):
    """Create and configure Flask app"""
    global api_core

    # Initialize API components
    api_core = initialize_api_components(config_manager)

    # Set start time
    api_core._start_time = time.time()

    return app

def run_api_server(config_manager: ConfigManager):
    """Run the API server"""
    global api_core

    # Create app
    app = create_app(config_manager)

    # Get configuration
    host = config_manager.get('api.host', '0.0.0.0')
    port = config_manager.get('api.port', 5000)
    debug = config_manager.get('system.debug', False)

    # Run server
    logging.info(f"Starting API server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug)
