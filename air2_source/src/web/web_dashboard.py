"""
AirOne Professional v4.0 - Web Dashboard
Modern web-based real-time monitoring dashboard
"""
# -*- coding: utf-8 -*-

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import threading
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'airone-secret-key-2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
dashboard_state = {
    'telemetry': {
        'altitude': 0.0,
        'velocity': 0.0,
        'temperature': 25.0,
        'pressure': 1013.25,
        'battery': 100.0,
        'signal': -50,
        'latitude': 0.0,
        'longitude': 0.0,
        'flight_phase': 'STANDBY'
    },
    'system_status': {
        'cpu_usage': 0.0,
        'memory_usage': 0.0,
        'disk_usage': 0.0,
        'network_status': 'connected',
        'uptime_seconds': 0
    },
    'mission_status': {
        'state': 'IDLE',
        'progress': 0,
        'events': [],
        'start_time': None
    },
    'alerts': [],
    'connected_clients': 0
}


# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AirOne Professional v4.0 - Web Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            color: #cdd6f4;
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(137, 180, 250, 0.1);
            border-radius: 12px;
            border: 1px solid rgba(137, 180, 250, 0.2);
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #89b4fa, #f38ba8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .header .status {
            display: inline-block;
            padding: 6px 16px;
            background: #a6e3a1;
            color: #1e1e2e;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .status.disconnected {
            background: #f38ba8;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .card {
            background: rgba(49, 50, 68, 0.6);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(137, 180, 250, 0.2);
            backdrop-filter: blur(10px);
        }
        
        .card h3 {
            color: #89b4fa;
            margin-bottom: 15px;
            font-size: 1.2em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card h3 .icon {
            font-size: 1.5em;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(137, 180, 250, 0.1);
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #a6adc8;
            font-size: 0.95em;
        }
        
        .metric-value {
            font-size: 1.3em;
            font-weight: 700;
            color: #89b4fa;
        }
        
        .metric-value.warning {
            color: #fab387;
        }
        
        .metric-value.danger {
            color: #f38ba8;
        }
        
        .metric-value.success {
            color: #a6e3a1;
        }
        
        .chart-container {
            position: relative;
            height: 250px;
            margin-top: 15px;
        }
        
        .alert-box {
            background: rgba(243, 139, 168, 0.1);
            border-left: 4px solid #f38ba8;
            padding: 12px 16px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        
        .alert-box.info {
            background: rgba(137, 180, 250, 0.1);
            border-left-color: #89b4fa;
        }
        
        .alert-box.success {
            background: rgba(166, 227, 161, 0.1);
            border-left-color: #a6e3a1;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(137, 180, 250, 0.2);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #89b4fa, #a6e3a1);
            transition: width 0.3s ease;
        }
        
        .event-log {
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        
        .event-item {
            padding: 6px 0;
            border-bottom: 1px solid rgba(137, 180, 250, 0.1);
        }
        
        .event-time {
            color: #6c7086;
            margin-right: 10px;
        }
        
        .connection-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(49, 50, 68, 0.9);
            border-radius: 20px;
            border: 1px solid rgba(137, 180, 250, 0.2);
        }
        
        .connection-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #a6e3a1;
            animation: pulse 2s infinite;
        }
        
        .connection-dot.disconnected {
            background: #f38ba8;
            animation: none;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #6c7086;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="connection-indicator">
        <div class="connection-dot" id="connectionDot"></div>
        <span id="connectionStatus">Connected</span>
    </div>
    
    <div class="header">
        <h1>🚀 AirOne Professional v4.0</h1>
        <p>Web Dashboard - Real-time Monitoring</p>
        <div style="margin-top: 10px;">
            <span class="status" id="systemStatus">SYSTEM ONLINE</span>
        </div>
    </div>
    
    <div class="dashboard-grid">
        <!-- Telemetry Card -->
        <div class="card">
            <h3><span class="icon">📊</span> Real-time Telemetry</h3>
            <div class="metric">
                <span class="metric-label">Altitude</span>
                <span class="metric-value" id="altitude">0.00 m</span>
            </div>
            <div class="metric">
                <span class="metric-label">Velocity</span>
                <span class="metric-value" id="velocity">0.00 m/s</span>
            </div>
            <div class="metric">
                <span class="metric-label">Temperature</span>
                <span class="metric-value" id="temperature">25.0 °C</span>
            </div>
            <div class="metric">
                <span class="metric-label">Pressure</span>
                <span class="metric-value" id="pressure">1013.25 hPa</span>
            </div>
            <div class="metric">
                <span class="metric-label">Battery</span>
                <span class="metric-value success" id="battery">100%</span>
            </div>
            <div class="metric">
                <span class="metric-label">Signal Strength</span>
                <span class="metric-value" id="signal">-50 dBm</span>
            </div>
        </div>
        
        <!-- System Resources Card -->
        <div class="card">
            <h3><span class="icon">💻</span> System Resources</h3>
            <div class="metric">
                <span class="metric-label">CPU Usage</span>
                <span class="metric-value" id="cpuUsage">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="cpuProgress" style="width: 0%"></div>
            </div>
            <div class="metric" style="margin-top: 15px;">
                <span class="metric-label">Memory Usage</span>
                <span class="metric-value" id="memoryUsage">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="memoryProgress" style="width: 0%"></div>
            </div>
            <div class="metric" style="margin-top: 15px;">
                <span class="metric-label">Disk Usage</span>
                <span class="metric-value" id="diskUsage">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="diskProgress" style="width: 0%"></div>
            </div>
            <div class="metric" style="margin-top: 15px;">
                <span class="metric-label">Network</span>
                <span class="metric-value success" id="networkStatus">Connected</span>
            </div>
            <div class="metric">
                <span class="metric-label">Uptime</span>
                <span class="metric-value" id="uptime">0s</span>
            </div>
        </div>
        
        <!-- Altitude Chart Card -->
        <div class="card">
            <h3><span class="icon">📈</span> Altitude Over Time</h3>
            <div class="chart-container">
                <canvas id="altitudeChart"></canvas>
            </div>
        </div>
        
        <!-- Mission Status Card -->
        <div class="card">
            <h3><span class="icon">🎯</span> Mission Status</h3>
            <div class="metric">
                <span class="metric-label">State</span>
                <span class="metric-value" id="missionState">IDLE</span>
            </div>
            <div class="metric">
                <span class="metric-label">Progress</span>
                <span class="metric-value" id="missionProgress">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="missionProgressFill" style="width: 0%"></div>
            </div>
            <div style="margin-top: 20px;">
                <h4 style="color: #89b4fa; margin-bottom: 10px; font-size: 1em;">Recent Events</h4>
                <div class="event-log" id="eventLog">
                    <div class="event-item">
                        <span class="event-time">--:--:--</span>
                        <span>Waiting for mission data...</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alerts Card -->
        <div class="card">
            <h3><span class="icon">🔔</span> Alerts & Notifications</h3>
            <div id="alertsContainer">
                <div class="alert-box info">
                    <strong>System Ready</strong><br>
                    Dashboard initialized and ready for monitoring.
                </div>
            </div>
        </div>
        
        <!-- GPS Card -->
        <div class="card">
            <h3><span class="icon">📍</span> GPS Position</h3>
            <div class="metric">
                <span class="metric-label">Latitude</span>
                <span class="metric-value" id="latitude">0.000000</span>
            </div>
            <div class="metric">
                <span class="metric-label">Longitude</span>
                <span class="metric-value" id="longitude">0.000000</span>
            </div>
            <div class="metric">
                <span class="metric-label">Flight Phase</span>
                <span class="metric-value" id="flightPhase">STANDBY</span>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>AirOne Professional v4.0 - Ultimate Unified Edition</p>
        <p>Web Dashboard © 2026 AirOne Development Team</p>
    </div>
    
    <script>
        // Initialize Socket.IO
        const socket = io();
        
        // Connection status
        socket.on('connect', () => {
            document.getElementById('connectionDot').classList.remove('disconnected');
            document.getElementById('connectionStatus').textContent = 'Connected';
        });
        
        socket.on('disconnect', () => {
            document.getElementById('connectionDot').classList.add('disconnected');
            document.getElementById('connectionStatus').textContent = 'Disconnected';
        });
        
        // Receive telemetry data
        socket.on('telemetry_update', (data) => {
            updateTelemetry(data);
        });
        
        socket.on('system_update', (data) => {
            updateSystemStatus(data);
        });
        
        socket.on('mission_update', (data) => {
            updateMissionStatus(data);
        });
        
        socket.on('alert', (data) => {
            addAlert(data);
        });
        
        function updateTelemetry(data) {
            document.getElementById('altitude').textContent = data.altitude.toFixed(2) + ' m';
            document.getElementById('velocity').textContent = data.velocity.toFixed(2) + ' m/s';
            document.getElementById('temperature').textContent = data.temperature.toFixed(1) + ' °C';
            document.getElementById('pressure').textContent = data.pressure.toFixed(2) + ' hPa';
            
            const batteryElem = document.getElementById('battery');
            batteryElem.textContent = data.battery.toFixed(1) + '%';
            batteryElem.className = 'metric-value ' + (data.battery > 50 ? 'success' : data.battery > 20 ? 'warning' : 'danger');
            
            document.getElementById('signal').textContent = data.signal + ' dBm';
            document.getElementById('latitude').textContent = data.latitude.toFixed(6);
            document.getElementById('longitude').textContent = data.longitude.toFixed(6);
            document.getElementById('flightPhase').textContent = data.flight_phase;
            
            // Update chart
            updateChart(data.altitude);
        }
        
        function updateSystemStatus(data) {
            document.getElementById('cpuUsage').textContent = data.cpu_usage.toFixed(1) + '%';
            document.getElementById('cpuProgress').style.width = data.cpu_usage + '%';
            
            document.getElementById('memoryUsage').textContent = data.memory_usage.toFixed(1) + '%';
            document.getElementById('memoryProgress').style.width = data.memory_usage + '%';
            
            document.getElementById('diskUsage').textContent = data.disk_usage.toFixed(1) + '%';
            document.getElementById('diskProgress').style.width = data.disk_usage + '%';
            
            const networkElem = document.getElementById('networkStatus');
            networkElem.textContent = data.network_status === 'connected' ? 'Connected' : 'Disconnected';
            networkElem.className = 'metric-value ' + (data.network_status === 'connected' ? 'success' : 'danger');
            
            document.getElementById('uptime').textContent = formatUptime(data.uptime_seconds);
        }
        
        function updateMissionStatus(data) {
            document.getElementById('missionState').textContent = data.state;
            document.getElementById('missionProgress').textContent = data.progress.toFixed(1) + '%';
            document.getElementById('missionProgressFill').style.width = data.progress + '%';
            
            // Update event log
            if (data.events && data.events.length > 0) {
                const eventLog = document.getElementById('eventLog');
                eventLog.innerHTML = data.events.slice(-10).map(event => 
                    '<div class="event-item">' +
                    '<span class="event-time">' + event.time + '</span>' +
                    '<span>' + event.message + '</span>' +
                    '</div>'
                ).join('');
            }
        }
        
        function addAlert(data) {
            const container = document.getElementById('alertsContainer');
            const alertBox = document.createElement('div');
            alertBox.className = 'alert-box ' + (data.type || 'info');
            alertBox.innerHTML = '<strong>' + data.title + '</strong><br>' + data.message;
            
            container.insertBefore(alertBox, container.firstChild);
            
            // Keep only last 5 alerts
            while (container.children.length > 5) {
                container.removeChild(container.lastChild);
            }
        }
        
        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            return h + 'h ' + m + 'm ' + s + 's';
        }
        
        // Chart.js setup
        const ctx = document.getElementById('altitudeChart').getContext('2d');
        const altitudeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Altitude (m)',
                    data: [],
                    borderColor: '#89b4fa',
                    backgroundColor: 'rgba(137, 180, 250, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: 'rgba(137, 180, 250, 0.1)'
                        },
                        ticks: {
                            color: '#a6adc8',
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(137, 180, 250, 0.1)'
                        },
                        ticks: {
                            color: '#a6adc8'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        function updateChart(altitude) {
            const now = new Date();
            const timeLabel = now.getHours().toString().padStart(2, '0') + ':' + 
                             now.getMinutes().toString().padStart(2, '0') + ':' + 
                             now.getSeconds().toString().padStart(2, '0');
            
            altitudeChart.data.labels.push(timeLabel);
            altitudeChart.data.datasets[0].data.push(altitude);
            
            // Keep last 50 points
            if (altitudeChart.data.labels.length > 50) {
                altitudeChart.data.labels.shift();
                altitudeChart.data.datasets[0].data.shift();
            }
            
            altitudeChart.update();
        }
        
        // Request initial data
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                updateTelemetry(data.telemetry);
                updateSystemStatus(data.system_status);
                updateMissionStatus(data.mission_status);
            })
            .catch(error => console.error('Error fetching status:', error));
    </script>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Serve the dashboard HTML"""
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify(dashboard_state)


@app.route('/api/telemetry')
def get_telemetry():
    """Get current telemetry"""
    return jsonify(dashboard_state['telemetry'])


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    dashboard_state['connected_clients'] += 1
    logger.info(f"Client connected. Total clients: {dashboard_state['connected_clients']}")
    emit('connected', {'clients': dashboard_state['connected_clients']})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    dashboard_state['connected_clients'] = max(0, dashboard_state['connected_clients'] - 1)
    logger.info(f"Client disconnected. Total clients: {dashboard_state['connected_clients']}")


def simulate_telemetry():
    """Simulate telemetry data for demo purposes"""
    import math
    
    while True:
        try:
            now = datetime.now()
            timestamp = now.timestamp()
            
            # Simulate flight profile
            flight_time = timestamp % 300  # 5 minute cycle
            
            # Altitude simulation (parabolic flight)
            if flight_time < 150:
                altitude = 500 * math.sin(math.pi * flight_time / 150)
            else:
                altitude = 500 * math.sin(math.pi * (300 - flight_time) / 150)
            
            # Add some noise
            altitude += random.uniform(-10, 10)
            
            # Velocity
            velocity = random.uniform(5, 25) + altitude / 100
            
            # Temperature (decreases with altitude)
            temperature = 25 - (altitude / 100) + random.uniform(-2, 2)
            
            # Pressure (decreases with altitude)
            pressure = 1013.25 - (altitude / 10) + random.uniform(-5, 5)
            
            # Battery (slowly decreasing)
            dashboard_state['telemetry']['battery'] = max(0, 100 - (timestamp % 3600) / 36)
            
            # Update telemetry
            dashboard_state['telemetry'].update({
                'altitude': max(0, altitude),
                'velocity': max(0, velocity),
                'temperature': max(-50, temperature),
                'pressure': max(900, pressure),
                'signal': random.randint(-80, -40),
                'latitude': 40.7128 + random.uniform(-0.01, 0.01),
                'longitude': -74.0060 + random.uniform(-0.01, 0.01),
                'flight_phase': 'ASCENT' if altitude > 0 and flight_time < 150 else 'DESCENT'
            })
            
            # Update system status
            dashboard_state['system_status'].update({
                'cpu_usage': random.uniform(20, 60),
                'memory_usage': random.uniform(40, 70),
                'disk_usage': 45.5,
                'uptime_seconds': (now - datetime(2026, 1, 1)).total_seconds()
            })
            
            # Update mission status
            dashboard_state['mission_status']['progress'] = (flight_time / 300) * 100
            dashboard_state['mission_status']['state'] = 'ACTIVE' if altitude > 100 else 'STANDBY'
            
            # Emit updates
            socketio.emit('telemetry_update', dashboard_state['telemetry'])
            socketio.emit('system_update', dashboard_state['system_status'])
            socketio.emit('mission_update', dashboard_state['mission_status'])
            
            # Random alerts
            if random.random() < 0.05:
                alerts = [
                    {'type': 'info', 'title': 'Telemetry Update', 'message': 'Data received successfully'},
                    {'type': 'success', 'title': 'Milestone', 'message': 'Altitude milestone reached!'},
                    {'type': 'warning', 'title': 'Battery Warning', 'message': 'Battery level below 50%'}
                ]
                alert = random.choice(alerts)
                socketio.emit('alert', alert)
            
            import time
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in telemetry simulation: {e}")
            import time
            time.sleep(1)


def start_dashboard(host='127.0.0.1', port=5000, debug=False, simulation=True):
    """Start the web dashboard"""
    
    # Start telemetry simulation in background
    if simulation:
        sim_thread = threading.Thread(target=simulate_telemetry, daemon=True)
        sim_thread.start()
        logger.info("Telemetry simulation started")
    
    # Start the web server
    logger.info(f"Starting AirOne Web Dashboard on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AirOne Web Dashboard')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-sim', action='store_true', help='Disable telemetry simulation')
    
    args = parser.parse_args()
    
    start_dashboard(
        host=args.host,
        port=args.port,
        debug=args.debug,
        simulation=not args.no_sim
    )
