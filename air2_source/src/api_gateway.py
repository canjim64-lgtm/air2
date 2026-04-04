"""
AirOne Professional v4.0 - API Gateway Server
RESTful API with authentication and rate limiting
"""
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import hashlib
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'airone-professional-v4-secret-key-2026'

# Rate limiting storage
rate_limit_store: Dict[str, list] = {}
rate_limit_lock = threading.Lock()


class APIGateway:
    """API Gateway management"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8080):
        self.host = host
        self.port = port
        self.app = app
        self.users = self._load_users()
        self.request_log = []
        self.running = False
        
    def _load_users(self) -> Dict[str, Any]:
        """Load API users from config"""
        return {
            'admin': {
                'key': hashlib.sha256('admin_api_key_2026'.encode()).hexdigest(),
                'role': 'admin',
                'rate_limit': 1000,
                'permissions': ['read', 'write', 'admin', 'delete']
            },
            'operator': {
                'key': hashlib.sha256('operator_api_key_2026'.encode()).hexdigest(),
                'role': 'operator',
                'rate_limit': 100,
                'permissions': ['read', 'write']
            },
            'viewer': {
                'key': hashlib.sha256('viewer_api_key_2026'.encode()).hexdigest(),
                'role': 'viewer',
                'rate_limit': 50,
                'permissions': ['read']
            }
        }
    
    def authenticate(self, f: Callable) -> Callable:
        """Authentication decorator"""
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            # Find user by API key
            user = None
            for username, data in self.users.items():
                if data['key'] == api_key:
                    user = {'username': username, **data}
                    break
            
            if not user:
                return jsonify({'error': 'Invalid API key'}), 401
            
            g.user = user
            return f(*args, **kwargs)
        return decorated
    
    def rate_limit(self, max_requests: int = 100, window_seconds: int = 60):
        """Rate limiting decorator"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated(*args, **kwargs):
                client_ip = request.remote_addr
                current_time = time.time()
                
                with rate_limit_lock:
                    if client_ip not in rate_limit_store:
                        rate_limit_store[client_ip] = []
                    
                    # Remove old requests
                    rate_limit_store[client_ip] = [
                        t for t in rate_limit_store[client_ip]
                        if current_time - t < window_seconds
                    ]
                    
                    # Check rate limit
                    if len(rate_limit_store[client_ip]) >= max_requests:
                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'retry_after': window_seconds
                        }), 429
                    
                    # Add current request
                    rate_limit_store[client_ip].append(current_time)
                
                return f(*args, **kwargs)
            return decorated
        return decorator
    
    def log_request(self, endpoint: str, method: str, user: str, status: int):
        """Log API request"""
        self.request_log.append({
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'user': user,
            'status': status
        })
        
        # Keep only last 10000 requests
        if len(self.request_log) > 10000:
            self.request_log = self.request_log[-10000:]
    
    def start(self):
        """Start API server"""
        self.running = True
        logger.info(f"Starting API Gateway on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
    
    def stop(self):
        """Stop API server"""
        self.running = False
        logger.info("API Gateway stopped")


# Initialize gateway
gateway = APIGateway()


# ============ API ENDPOINTS ============

@app.route('/api/health', methods=['GET'])
@gateway.rate_limit(max_requests=1000, window_seconds=60)
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '4.0'
    })


@app.route('/api/status', methods=['GET'])
@gateway.authenticate
@gateway.rate_limit(max_requests=500, window_seconds=60)
def get_status():
    """Get system status"""
    import psutil
    
    return jsonify({
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/telemetry', methods=['GET'])
@gateway.authenticate
@gateway.rate_limit(max_requests=200, window_seconds=60)
def get_telemetry():
    """Get telemetry data"""
    # Simulated telemetry data
    return jsonify({
        'altitude': 523.5,
        'velocity': 25.3,
        'temperature': 22.5,
        'pressure': 1013.25,
        'battery': 95.2,
        'signal': -65,
        'latitude': 40.7128,
        'longitude': -74.0060,
        'flight_phase': 'ASCENT',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/telemetry', methods=['POST'])
@gateway.authenticate
@gateway.rate_limit(max_requests=100, window_seconds=60)
def post_telemetry():
    """Post telemetry data"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Log telemetry
    logger.info(f"Telemetry received: {data}")
    
    return jsonify({
        'status': 'success',
        'message': 'Telemetry data received',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/users', methods=['GET'])
@gateway.authenticate
@gateway.rate_limit(max_requests=50, window_seconds=60)
def get_users():
    """Get user list (admin only)"""
    if 'admin' not in g.user.get('permissions', []):
        return jsonify({'error': 'Admin permission required'}), 403
    
    users_list = [
        {
            'username': username,
            'role': data['role'],
            'rate_limit': data['rate_limit']
        }
        for username, data in gateway.users.items()
    ]
    
    return jsonify({'users': users_list})


@app.route('/api/logs', methods=['GET'])
@gateway.authenticate
@gateway.rate_limit(max_requests=30, window_seconds=60)
def get_logs():
    """Get API request logs (admin only)"""
    if 'admin' not in g.user.get('permissions', []):
        return jsonify({'error': 'Admin permission required'}), 403
    
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        'logs': gateway.request_log[-limit:]
    })


@app.route('/api/config', methods=['GET'])
@gateway.authenticate
@gateway.rate_limit(max_requests=50, window_seconds=60)
def get_config():
    """Get system configuration"""
    return jsonify({
        'config': {
            'version': '4.0',
            'api_version': '1.0',
            'features': {
                'telemetry': True,
                'ai': True,
                'security': True,
                'web_dashboard': True
            }
        }
    })


@app.route('/api/commands', methods=['POST'])
@gateway.authenticate
@gateway.rate_limit(max_requests=20, window_seconds=60)
def post_command():
    """Execute system command"""
    if 'write' not in g.user.get('permissions', []):
        return jsonify({'error': 'Write permission required'}), 403
    
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({'error': 'Command required'}), 400
    
    logger.info(f"Command received: {command}")
    
    # Simulate command execution
    return jsonify({
        'status': 'success',
        'message': f'Command "{command}" executed',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/export', methods=['POST'])
@gateway.authenticate
@gateway.rate_limit(max_requests=10, window_seconds=60)
def export_data():
    """Export system data"""
    if 'read' not in g.user.get('permissions', []):
        return jsonify({'error': 'Read permission required'}), 403
    
    data = request.json
    export_type = data.get('type', 'json')
    
    return jsonify({
        'status': 'success',
        'export_type': export_type,
        'message': f'Data exported as {export_type}',
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


def run_api_server(host: str = '127.0.0.1', port: int = 8080):
    """Run API server"""
    gateway.host = host
    gateway.port = port
    gateway.start()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AirOne API Gateway')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    args = parser.parse_args()
    
    print("="*70)
    print("  AirOne Professional v4.0 - API Gateway Server")
    print("="*70)
    print()
    print(f"Starting API Gateway on http://{args.host}:{args.port}")
    print()
    print("Available Endpoints:")
    print("  GET  /api/health          - Health check")
    print("  GET  /api/status          - System status")
    print("  GET  /api/telemetry       - Get telemetry")
    print("  POST /api/telemetry       - Post telemetry")
    print("  GET  /api/users           - Get users (admin)")
    print("  GET  /api/logs            - Get logs (admin)")
    print("  GET  /api/config          - Get configuration")
    print("  POST /api/commands        - Execute command")
    print("  POST /api/export          - Export data")
    print()
    print("Authentication:")
    print("  Header: X-API-Key: <your-api-key>")
    print()
    print("Default API Keys:")
    print("  Admin:   admin_api_key_2026")
    print("  Operator: operator_api_key_2026")
    print("  Viewer:  viewer_api_key_2026")
    print()
    
    run_api_server(args.host, args.port)
