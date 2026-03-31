"""
React/Flask Web Dashboard Server for AirOne Professional v4.0
Integrated with real-time telemetry from the Unified Feature Manager.
"""
import logging
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import threading
import time
from typing import Optional, Any

logger = logging.getLogger(__name__)

# React Dashboard Source (External CDN for speed, but fully functional)
REACT_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>AirOne Professional v4.0</title>
    <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
    <style>
        body { font-family: 'Segoe UI'; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #007acc; }
        .metric { font-size: 2.5em; font-weight: bold; color: #4CAF50; }
        .warning { color: #ff9800; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        function Dashboard() {
            const [data, setData] = React.useState({ altitude: 0, velocity: 0, status: "OFFLINE", battery: 0 });
            
            React.useEffect(() => {
                const interval = setInterval(() => {
                    fetch('/api/telemetry/latest').then(res => res.json()).then(setData).catch(() => {});
                }, 500);
                return () => clearInterval(interval);
            }, []);

            return (
                <div>
                    <h1 style={{color: '#007acc'}}>AirOne Mission Control (v4.0 Unified)</h1>
                    <div className="card">
                        <h3>System Integrity</h3>
                        <div className="metric" style={{color: data.status === "NOMINAL" ? "#4CAF50" : "#ff5722"}}>{data.status}</div>
                    </div>
                    <div style={{display: 'flex', gap: '20px'}}>
                        <div className="card" style={{flex: 1}}><h3>Altitude (m)</h3><div className="metric">{data.altitude.toFixed(2)}</div></div>
                        <div className="card" style={{flex: 1}}><h3>Velocity (m/s)</h3><div className="metric">{data.velocity.toFixed(2)}</div></div>
                        <div className="card" style={{flex: 1}}><h3>Battery (V)</h3><div className="metric">{data.battery.toFixed(2)}</div></div>
                    </div>
                </div>
            );
        }
        ReactDOM.render(<Dashboard />, document.getElementById('root'));
    </script>
</body>
</html>
"""

class ReactDashboardServer:
    def __init__(self, feature_manager: Optional[Any] = None, port: int = 8080):
        self.logger = logging.getLogger(f"{__name__}.ReactDashboardServer")
        self.port = port
        self.feature_manager = feature_manager
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string(REACT_DASHBOARD_HTML)
            
        @self.app.route('/api/telemetry/latest')
        def get_telemetry():
            # Real integration: Pulling from TelemetryProcessor and Thermal systems
            alt, vel, batt, status = 0.0, 0.0, 0.0, "NOMINAL"
            
            if self.feature_manager:
                # Try to get latest from Telemetry Processor
                tp = self.feature_manager.get_feature('telemetry_processor')
                if tp:
                    latest = tp.get_latest_data()
                    alt = latest.get('altitude', 0.0)
                    vel = latest.get('velocity', 0.0)
                    batt = latest.get('battery_voltage', 0.0)
                
                # Check health from thermal system
                ts = self.feature_manager.get_feature('thermal_management')
                if ts and ts.throttled: status = "THROTTLED"

            return jsonify({
                "status": status,
                "altitude": alt,
                "velocity": vel,
                "battery": batt,
                "timestamp": time.time()
            })

    def start(self):
        server_thread = threading.Thread(
            target=lambda: self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
        )
        server_thread.daemon = True
        server_thread.start()
        self.logger.info(f"React Dashboard Live on port {self.port}.")
