#!/usr/bin/env python3
"""
AirOne v4.0 - REST API Server
================================

Complete REST API for all AirOne features.
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Simulated data
class AirOneAPI:
    """AirOne API Backend"""
    
    def __init__(self):
        self.telemetry_data = self._generate_telemetry()
        self.missions = []
        self.alerts = []
        self._init_sample_data()
        
    def _generate_telemetry(self):
        """Generate sample telemetry"""
        return {
            "altitude": 500 + random.uniform(-50, 50),
            "velocity": 25 + random.uniform(-5, 5),
            "temperature": 22 + random.uniform(-3, 3),
            "battery": 87,
            "pressure": 1013 + random.uniform(-10, 10),
            "signal": -65 + random.uniform(-5, 5),
            "latitude": 42.0 + random.uniform(-0.01, 0.01),
            "longitude": -75.0 + random.uniform(-0.01, 0.01),
            "heading": random.uniform(0, 360),
            "phase": random.choice(["ASCENT", "CRUISE", "DESCENT"]),
            "timestamp": datetime.now().isoformat()
        }
        
    def _init_sample_data(self):
        """Initialize sample data"""
        # Sample missions
        self.missions = [
            {"id": "m1", "name": "Test Flight 1", "status": "completed", "waypoints": 5},
            {"id": "m2", "name": "Survey Mission", "status": "planned", "waypoints": 10},
            {"id": "m3", "name": "Emergency", "status": "active", "waypoints": 3}
        ]
        
        # Sample alerts
        self.alerts = [
            {"id": "a1", "type": "warning", "message": "Low battery", "time": datetime.now().isoformat()},
            {"id": "a2", "type": "info", "message": "GPS locked", "time": datetime.now().isoformat()}
        ]
        
    def get_telemetry(self):
        """Get current telemetry"""
        self.telemetry_data = self._generate_telemetry()
        return self.telemetry_data
        
    def get_status(self):
        """Get system status"""
        return {
            "system": "ONLINE",
            "mode": "FLIGHT",
            "battery": self.telemetry_data["battery"],
            "signal": self.telemetry_data["signal"],
            "gps": "LOCKED",
            "uptime": "2:15:30"
        }
        
    def get_missions(self):
        """Get all missions"""
        return self.missions
        
    def create_mission(self, data):
        """Create new mission"""
        mission = {
            "id": f"m{len(self.missions) + 1}",
            "name": data.get("name", "New Mission"),
            "status": "planned",
            "waypoints": data.get("waypoints", 0),
            "created": datetime.now().isoformat()
        }
        self.missions.append(mission)
        return mission
        
    def get_alerts(self):
        """Get alerts"""
        return self.alerts
        
    def clear_alert(self, alert_id):
        """Clear alert"""
        self.alerts = [a for a in self.alerts if a["id"] != alert_id]
        return {"success": True}


# Create API instance
api = AirOneAPI()


# API Routes
@app.route('/')
def index():
    """API index"""
    return jsonify({
        "name": "AirOne v4.0 REST API",
        "version": "4.0.0",
        "endpoints": {
            "/api/telemetry": "Get current telemetry",
            "/api/status": "Get system status",
            "/api/missions": "List missions",
            "/api/missions/create": "Create mission",
            "/api/alerts": "Get alerts",
            "/api/flight/start": "Start flight",
            "/api/flight/stop": "Stop flight",
            "/api/config": "Get/set configuration"
        }
    })


@app.route('/api/telemetry')
def get_telemetry():
    """Get telemetry data"""
    return jsonify(api.get_telemetry())


@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify(api.get_status())


@app.route('/api/missions', methods=['GET'])
def get_missions():
    """Get all missions"""
    return jsonify(api.get_missions())


@app.route('/api/missions/create', methods=['POST'])
def create_mission():
    """Create new mission"""
    data = request.json or {}
    mission = api.create_mission(data)
    return jsonify(mission)


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get alerts"""
    return jsonify(api.get_alerts())


@app.route('/api/alerts/<alert_id>', methods=['DELETE'])
def clear_alert(alert_id):
    """Clear alert"""
    return jsonify(api.clear_alert(alert_id))


@app.route('/api/flight/start', methods=['POST'])
def start_flight():
    """Start flight"""
    return jsonify({"success": True, "message": "Flight started", "status": "AIRBORNE"})


@app.route('/api/flight/stop', methods=['POST'])
def stop_flight():
    """Stop flight"""
    return jsonify({"success": True, "message": "Flight stopped", "status": "GROUND"})


@app.route('/api/flight/emergency', methods=['POST'])
def emergency_stop():
    """Emergency stop"""
    return jsonify({"success": True, "message": "Emergency stop activated", "status": "EMERGENCY"})


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get configuration"""
    return jsonify({
        "update_interval": 1000,
        "max_altitude": 1500,
        "max_speed": 50,
        "battery_threshold": 20,
        "telemetry_enabled": True,
        "logging_enabled": True
    })


@app.route('/api/config', methods=['POST'])
def set_config():
    """Set configuration"""
    data = request.json or {}
    return jsonify({"success": True, "config": data})


@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


def run_api_server(host='0.0.0.0', port=5001, debug=False):
    """Run the API server"""
    print(f"Starting AirOne API Server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5001)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    run_api_server(args.host, args.port, args.debug)
