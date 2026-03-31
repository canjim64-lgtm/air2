#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Complete REST API System
Full-featured REST API with authentication, rate limiting, and comprehensive endpoints
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Import AdvancedDataAnalysis for telemetry data
from analysis.advanced_data_analysis import AdvancedDataAnalysis, TelemetryPoint

class AirOneAPI:
    """Complete REST API for AirOne Professional"""
    
    def __init__(self, host='0.0.0.0', port=5001):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = secrets.token_hex(32)
        
        # Enable CORS
        CORS(self.app, resources={r"/api/*": {"origins": "*"}})
        
        # Rate limiting
        self.limiter = Limiter(
            self.app,
            key_func=get_remote_address,
            default_limits=["100 per minute", "1000 per hour"]
        )
        
        # API tokens storage
        self.api_tokens = {}
        self.token_dir = Path(__file__).parent.parent / 'config' / 'api'
        self.token_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data analysis component
        self.data_analyzer = AdvancedDataAnalysis()
        # Simulate some initial telemetry data for the analyzer
        self._simulate_initial_telemetry()
        
        # Register routes
        self._register_routes()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _simulate_initial_telemetry(self):
        """Simulate adding some initial telemetry data to the analyzer."""
        base_time = time.time()
        for i in range(100):
            t = i * 0.5
            point = TelemetryPoint(
                timestamp=base_time + t,
                altitude=100 + 5 * t + np.random.normal(0, 2),
                velocity=10 + 0.5 * t + np.random.normal(0, 0.5),
                temperature=25 - 0.1 * t + np.random.normal(0, 0.5),
                pressure=1010 + 0.5 * t + np.random.normal(0, 1),
                battery_percent=100 - 0.1 * t,
                signal_strength=-60 + np.random.normal(0, 3)
            )
            self.data_analyzer.add_telemetry(point)
    
    def _register_routes(self):
        """Register all API routes"""
        
        # Health and status endpoints
        @self.app.route('/api/health')
        @self.limiter.limit("10 per second")
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '4.0 Ultimate Unified Edition'
            })
        
        @self.app.route('/api/status')
        @self.limiter.limit("5 per second")
        def system_status():
            """System status endpoint"""
            return jsonify({
                'system': 'AirOne Professional',
                'version': '4.0 Ultimate Unified Edition',
                'status': 'online',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': 'running',
                'features': {
                    'modes': 13,
                    'ai_systems': 8,
                    'ml_systems': 3,
                    'security_systems': 9,
                    'quantum_systems': 2,
                    'cosmic_systems': 5,
                    'total_features': '500+'
                }
            })
        
        # Authentication endpoints
        @self.app.route('/api/auth/token', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def create_token():
            """Create API token"""
            data = request.get_json()
            
            if not data or 'username' not in data:
                return jsonify({'error': 'Username required'}), 400
            
            username = data['username']
            token = secrets.token_hex(32)
            
            self.api_tokens[token] = {
                'username': username,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'permissions': ['read', 'write']
            }
            
            # Save token
            self._save_tokens()
            
            return jsonify({
                'token': token,
                'expires_at': self.api_tokens[token]['expires_at']
            })
        
        @self.app.route('/api/auth/token/<token>', methods=['DELETE'])
        @self.limiter.limit("10 per minute")
        def revoke_token(token):
            """Revoke API token"""
            if token in self.api_tokens:
                del self.api_tokens[token]
                self._save_tokens()
                return jsonify({'message': 'Token revoked'})
            return jsonify({'error': 'Token not found'}), 404
        
        # Modes endpoints
        @self.app.route('/api/modes')
        @self.limiter.limit("30 per minute")
        def list_modes():
            """List all operational modes"""
            modes = [
                {'id': 1, 'name': 'Desktop GUI', 'status': 'available'},
                {'id': 2, 'name': 'Headless CLI', 'status': 'available'},
                {'id': 3, 'name': 'Offline/Air-Gapped', 'status': 'available'},
                {'id': 4, 'name': 'Simulation-Only', 'status': 'available'},
                {'id': 5, 'name': 'CanSat Data Receiver', 'status': 'available'},
                {'id': 6, 'name': 'Replay/Forensic', 'status': 'available'},
                {'id': 7, 'name': 'Secure SAFE', 'status': 'available'},
                {'id': 8, 'name': 'Web Server', 'status': 'available'},
                {'id': 9, 'name': 'Digital Twin', 'status': 'available'},
                {'id': 10, 'name': 'Powerful Mode Pack', 'status': 'available'},
                {'id': 11, 'name': 'Powerful Security', 'status': 'available'},
                {'id': 12, 'name': 'Ultimate Enhanced', 'status': 'available'},
                {'id': 13, 'name': 'Cosmic Fusion', 'status': 'available'}
            ]
            return jsonify({'modes': modes, 'total': len(modes)})
        
        @self.app.route('/api/modes/<int:mode_id>')
        @self.limiter.limit("30 per minute")
        def get_mode(mode_id):
            """Get mode details"""
            modes = {
                1: {'name': 'Desktop GUI', 'description': 'Full graphical interface'},
                2: {'name': 'Headless CLI', 'description': 'Command-line interface'},
                3: {'name': 'Offline/Air-Gapped', 'description': 'Isolated operation'},
                4: {'name': 'Simulation-Only', 'description': 'Pure simulation'},
                5: {'name': 'CanSat Data Receiver', 'description': 'Hardware interface'},
                6: {'name': 'Replay/Forensic', 'description': 'Historical analysis'},
                7: {'name': 'Secure SAFE', 'description': 'Emergency recovery'},
                8: {'name': 'Web Server', 'description': 'Web API and Interface'},
                9: {'name': 'Digital Twin', 'description': 'Digital twin simulation'},
                10: {'name': 'Powerful Mode Pack', 'description': 'All modes integrated'},
                11: {'name': 'Powerful Security', 'description': 'Advanced security'},
                12: {'name': 'Ultimate Enhanced', 'description': 'Most advanced mode'},
                13: {'name': 'Cosmic Fusion', 'description': 'Quantum AI fusion'}
            }
            
            if mode_id in modes:
                return jsonify({'id': mode_id, **modes[mode_id]})
            return jsonify({'error': 'Mode not found'}), 404
        
        # Features endpoints
        @self.app.route('/api/features')
        @self.limiter.limit("30 per minute")
        def list_features():
            """List all features"""
            return jsonify({
                'operational_modes': 13,
                'ai_systems': 8,
                'ml_systems': 3,
                'security_systems': 9,
                'quantum_systems': 2,
                'cosmic_systems': 5,
                'pipeline_systems': 4,
                'hardware_systems': 4,
                'total_features': '500+',
                'all_modes_have_all_features': True
            })
        
        # Telemetry endpoints
        @self.app.route('/api/telemetry/current')
        @self.limiter.limit("60 per minute")
        def get_current_telemetry():
            """Get current telemetry data"""
            if self.data_analyzer.telemetry_buffer:
                latest_point = self.data_analyzer.telemetry_buffer[-1]
                return jsonify({
                    'altitude': latest_point.altitude,
                    'velocity': latest_point.velocity,
                    'temperature': latest_point.temperature,
                    'pressure': latest_point.pressure,
                    'battery': latest_point.battery_percent,
                    'signal_strength': latest_point.signal_strength,
                    'timestamp': datetime.utcnow().isoformat(), # Use current UTC time for API response
                    'status': 'nominal' # Placeholder for actual status determination
                })
            return jsonify({
                'error': 'No telemetry data available',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'unavailable'
            }), 503
        
        @self.app.route('/api/telemetry/history')
        @self.limiter.limit("30 per minute")
        def get_telemetry_history():
            """Get historical telemetry data"""
            num_points = request.args.get('num_points', 10, type=int)
            
            if self.data_analyzer.telemetry_buffer:
                # Retrieve the last 'num_points' from the buffer
                history_data = list(self.data_analyzer.telemetry_buffer)[-num_points:]
                
                # Convert TelemetryPoint objects to dictionaries for JSON serialization
                serialized_history = []
                for point in history_data:
                    serialized_history.append({
                        'timestamp': datetime.fromtimestamp(point.timestamp).isoformat(), # Convert float timestamp to datetime string
                        'altitude': point.altitude,
                        'velocity': point.velocity,
                        'temperature': point.temperature,
                        'pressure': point.pressure,
                        'battery': point.battery_percent,
                        'signal_strength': point.signal_strength,
                        'flight_phase': point.flight_phase,
                        'quality_score': point.quality_score
                        # Add other relevant fields from TelemetryPoint as needed
                    })
                
                return jsonify({'history': serialized_history, 'count': len(serialized_history)})
            
            return jsonify({
                'history': [],
                'count': 0,
                'message': 'No telemetry data available'
            })
        
        # System endpoints
        @self.app.route('/api/system/info')
        @self.limiter.limit("10 per minute")
        def system_info():
            """Get system information"""
            import platform
            return jsonify({
                'python_version': platform.python_version(),
                'platform': platform.platform(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'airone_version': '4.0 Ultimate Unified Edition'
            })
        
        @self.app.route('/api/system/logs', methods=['GET'])
        @self.limiter.limit("10 per minute")
        def get_logs():
            """Get system logs"""
            log_file = Path(__file__).parent.parent / 'logs' / 'airone.log'
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                return jsonify({'logs': lines, 'count': len(lines)})
            return jsonify({'logs': [], 'message': 'No logs available'})
        
        # Configuration endpoints
        @self.app.route('/api/config', methods=['GET'])
        @self.limiter.limit("10 per minute")
        def get_config():
            """Get system configuration"""
            config_file = Path(__file__).parent.parent / 'config' / 'system_config.json'
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return jsonify(config)
            return jsonify({'error': 'Configuration not found'}), 404
        
        @self.app.route('/api/config', methods=['PUT'])
        @self.limiter.limit("5 per minute")
        def update_config():
            """Update system configuration"""
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            config_file = Path(__file__).parent.parent / 'config' / 'system_config.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return jsonify({'message': 'Configuration updated'})
        
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.errorhandler(429)
        def ratelimit_handler(error):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
    
    def _save_tokens(self):
        """Save API tokens to file"""
        token_file = self.token_dir / 'api_tokens.json'
        with open(token_file, 'w', encoding='utf-8') as f:
            json.dump(self.api_tokens, f, indent=2, default=str)
    
    def _load_tokens(self):
        """Load API tokens from file"""
        token_file = self.token_dir / 'api_tokens.json'
        if token_file.exists():
            with open(token_file, 'r', encoding='utf-8') as f:
                self.api_tokens = json.load(f)
    
    def run(self, debug=False):
        """Run the API server"""
        self._load_tokens()
        self.logger.info(f"Starting API server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)


def create_api_server(host='0.0.0.0', port=5001) -> AirOneAPI:
    """Create and return API server"""
    return AirOneAPI(host, port)


if __name__ == '__main__':
    # Run API server
    api = create_api_server()
    api.run(debug=True)
