"""Web Dashboard Module - Actual working web server"""

import sys

try:
    from flask import Flask, jsonify, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("WARNING: Flask not installed. Install with: pip install flask")

if FLASK_AVAILABLE:
    HTML_TEMPLATE = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AirOne Dashboard</title>
        <style>
            body { font-family: Arial; margin: 40px; background: #1a1a2e; color: #eee; }
            h1 { color: #00d4ff; }
            .card { background: #16213e; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .status { color: #00ff88; }
        </style>
    </head>
    <body>
        <h1>AirOne Professional v4.0 - Web Dashboard</h1>
        <div class="card">
            <h2>System Status</h2>
            <p class="status">Online</p>
            <p>Mode: Web Dashboard</p>
            <p>Port: 8080</p>
        </div>
        <div class="card">
            <h2>API Endpoints</h2>
            <p><a href="/api/status" style="color:#00d4ff">/api/status</a></p>
            <p><a href="/api/health" style="color:#00d4ff">/api/health</a></p>
        </div>
    </body>
    </html>
    '''

    app = Flask(__name__)

    @app.route('/')
    def home():
        return render_template_string(HTML_TEMPLATE)

    @app.route('/api/status')
    def status():
        return jsonify({'status': 'online', 'mode': 'web', 'version': '4.0'})

    @app.route('/api/health')
    def health():
        return jsonify({'health': 'good'})

def main():
    if not FLASK_AVAILABLE:
        print("ERROR: Flask not installed. Run: pip install flask")
        return
    
    print("Starting web server on http://localhost:8080")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == "__main__":
    main()