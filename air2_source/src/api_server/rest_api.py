"""REST API Server Module - Actual working API server"""

try:
    from flask import Flask, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'service': 'AirOne REST API',
        'version': '4.0',
        'status': 'running'
    })

@app.route('/api/status')
def status():
    return jsonify({'status': 'online', 'mode': 'api'})

@app.route('/api/health')
def health():
    return jsonify({'health': 'ok'})

@app.route('/api/modes')
def modes():
    return jsonify({
        'modes': ['GUI','CLI','Web','API','Desktop','System','Telemetry','Ground','AI','Security','Quantum','Cosmic','Pipeline']
    })

def main():
    if not FLASK_AVAILABLE:
        print("Flask not installed. Run: pip install flask")
        return
    
    print("Starting REST API on http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()