"""Web Dashboard Module - Professional Ground Station Dashboard"""

import sys
import os
import json
import threading
import time
from datetime import datetime

try:
    from flask import Flask, jsonify, render_template, send_from_directory
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("WARNING: Flask not installed. Install with: pip install flask")

# Flask app setup
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Global state for telemetry
TELEMETRY_DATA = {
    'altitude': 12450,
    'speed': 245,
    'heading': 127,
    'pressure': 1013.25,
    'humidity': 65,
    'gps_lat': 40.7128,
    'gps_lon': -74.0060,
    'satellites': 12,
    'temperature': 22.5,
    'battery': 84,
    'timestamp': datetime.now().isoformat()
}

SYSTEM_STATUS = {
    'cansat_id': 'CanSat-001',
    'status': 'online',
    'mission_phase': 'descent',
    'signal_strength': 98.7,
    'latency_ms': 12
}

SENSOR_DATA = [
    {'name': 'BME280 - Pressure', 'value': '1013.25', 'unit': 'hPa', 'status': 'online'},
    {'name': 'BME280 - Temperature', 'value': '22.5', 'unit': '°C', 'status': 'online'},
    {'name': 'BME280 - Humidity', 'value': '65.3', 'unit': '%', 'status': 'online'},
    {'name': 'GPS Module', 'value': '12 Sats', 'unit': 'lock', 'status': 'online'},
    {'name': 'IMU - Accel', 'value': '[0.1, 9.8, 0.2]', 'unit': 'm/s²', 'status': 'online'},
    {'name': 'IMU - Gyro', 'value': '[0.01, 0.02, 0.01]', 'unit': 'rad/s', 'status': 'online'},
    {'name': 'Radiation Sensor', 'value': '0.12', 'unit': 'μSv/h', 'status': 'standby'},
    {'name': 'LIDAR', 'value': '--', 'unit': 'm', 'status': 'offline'},
]

MISSION_TIMELINE = [
    {'phase': 'Launch', 'time': '08:00:00 UTC', 'completed': True},
    {'phase': 'Ascent', 'time': '08:15:32 UTC', 'completed': True},
    {'phase': 'Data Collection', 'time': '08:20:00 UTC', 'completed': True},
    {'phase': 'Descent', 'time': 'In Progress', 'completed': False},
    {'phase': 'Landing', 'time': 'Pending', 'completed': False},
]

ALERTS = [
    {'type': 'info', 'title': 'All Systems Nominal', 'message': 'CanSat-001 operating within normal parameters', 'time': '2 min ago'},
    {'type': 'warning', 'title': 'Temperature Advisory', 'message': 'Internal temperature approaching upper threshold', 'time': '15 min ago'},
]


@app.route('/')
def home():
    """Render main dashboard"""
    return render_template('dashboard.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)


@app.route('/api/status')
def status():
    """Get system status"""
    return jsonify({
        'status': SYSTEM_STATUS['status'],
        'mode': 'ground_station',
        'version': '4.0',
        'cansat_id': SYSTEM_STATUS['cansat_id'],
        'signal_strength': SYSTEM_STATUS['signal_strength'],
        'latency_ms': SYSTEM_STATUS['latency_ms']
    })


@app.route('/api/health')
def health():
    """Get health status"""
    return jsonify({
        'health': 'good',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/telemetry')
def telemetry():
    """Get live telemetry data"""
    return jsonify(TELEMETRY_DATA)


@app.route('/api/sensors')
def sensors():
    """Get sensor data"""
    return jsonify(SENSOR_DATA)


@app.route('/api/mission')
def mission():
    """Get mission timeline"""
    return jsonify(MISSION_TIMELINE)


@app.route('/api/alerts')
def alerts():
    """Get system alerts"""
    return jsonify(ALERTS)


# Telemetry update simulation (in production, this would come from actual hardware)
def update_telemetry():
    """Background thread to simulate telemetry updates"""
    import random
    while True:
        try:
            TELEMETRY_DATA['altitude'] += random.randint(-50, 50)
            TELEMETRY_DATA['speed'] += random.randint(-10, 10)
            TELEMETRY_DATA['heading'] = (TELEMETRY_DATA['heading'] + random.randint(-5, 5)) % 360
            TELEMETRY_DATA['pressure'] += random.uniform(-1, 1)
            TELEMETRY_DATA['humidity'] = max(0, min(100, TELEMETRY_DATA['humidity'] + random.randint(-5, 5)))
            TELEMETRY_DATA['gps_lat'] += random.uniform(-0.0005, 0.0005)
            TELEMETRY_DATA['gps_lon'] += random.uniform(-0.0005, 0.0005)
            TELEMETRY_DATA['temperature'] += random.uniform(-0.5, 0.5)
            TELEMETRY_DATA['battery'] = max(0, TELEMETRY_DATA['battery'] - 0.01)
            TELEMETRY_DATA['timestamp'] = datetime.now().isoformat()
            time.sleep(2)
        except Exception:
            pass


def main():
    """Start the web server"""
    if not FLASK_AVAILABLE:
        print("ERROR: Flask not installed. Run: pip install flask")
        return
    
    # Start telemetry simulation thread
    telemetry_thread = threading.Thread(target=update_telemetry, daemon=True)
    telemetry_thread.start()
    
    print("\n" + "="*60)
    print("     AirOne Professional - Ground Station Dashboard")
    print("="*60)
    print("\n🌐 Starting web server...")
    print("   Dashboard: http://localhost:8080")
    print("   API Endpoints:")
    print("     - /api/status     - System status")
    print("     - /api/telemetry  - Live telemetry data")
    print("     - /api/sensors    - Sensor readings")
    print("     - /api/mission    - Mission timeline")
    print("     - /api/alerts     - System alerts")
    print("\n⌨️  Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)


if __name__ == "__main__":
    main()