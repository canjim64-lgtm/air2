"""
AI Module - Data Analysis and Prediction
- Machine learning for sensor data
- Anomaly detection
- Flight phase prediction
- Path planning suggestions
"""
import random
import time
from typing import Dict, Any, List, Optional
from collections import deque


class AnomalyDetector:
    """Detect anomalies in sensor data"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.data_windows: Dict[str, deque] = {}
        
        # Thresholds
        self.thresholds = {
            'temperature_change': 5.0,  # °C per minute
            'pressure_change': 5.0,     # hPa per minute
            'altitude_change': 50.0,     # m per second
            'battery_drop': 5.0         # % per minute
        }
    
    def update(self, sensor: str, value: float) -> Dict[str, Any]:
        """Update and check for anomalies"""
        if sensor not in self.data_windows:
            self.data_windows[sensor] = deque(maxlen=self.window_size)
        
        self.data_windows[sensor].append({
            'value': value,
            'timestamp': time.time()
        })
        
        # Check for anomalies
        return self._check_anomaly(sensor)
    
    def _check_anomaly(self, sensor: str) -> Dict[str, Any]:
        """Check recent values for anomalies"""
        window = self.data_windows[sensor]
        
        if len(window) < 2:
            return {'anomaly': False}
        
        # Calculate rate of change
        recent = list(window)[-10:]
        if len(recent) < 2:
            return {'anomaly': False}
        
        values = [r['value'] for r in recent]
        times = [r['timestamp'] for r in recent]
        
        # Rate of change
        dt = times[-1] - times[0]
        if dt > 0:
            rate = (values[-1] - values[0]) / dt * 60  # per minute
            
            anomaly = False
            anomaly_type = None
            
            if sensor == 'temperature' and abs(rate) > self.thresholds['temperature_change']:
                anomaly = True
                anomaly_type = 'temp_spike'
            elif sensor == 'pressure' and abs(rate) > self.thresholds['pressure_change']:
                anomaly = True
                anomaly_type = 'pressure_change'
            elif sensor == 'altitude' and abs(rate) > self.thresholds['altitude_change']:
                anomaly = True
                anomaly_type = 'altitude_change'
            
            return {
                'anomaly': anomaly,
                'type': anomaly_type,
                'rate': rate,
                'value': values[-1]
            }
        
        return {'anomaly': False}


class FlightPhaseClassifier:
    """Classify current flight phase"""
    
    def __init__(self):
        self.phases = ['ground', 'ascent', 'descent', 'landing', 'stationary']
        self.thresholds = {
            'ascent_speed': 2.0,     # m/s upward
            'descent_speed': -2.0,   # m/s downward
            'ground_altitude': 100   # m
        }
    
    def classify(self, altitude: float, vertical_speed: float) -> str:
        """Classify flight phase"""
        
        if altitude < self.thresholds['ground_altitude']:
            return 'ground'
        
        if vertical_speed > self.thresholds['ascent_speed']:
            return 'ascent'
        elif vertical_speed < self.thresholds['descent_speed']:
            return 'descent'
        elif altitude > 500 and abs(vertical_speed) < 1:
            return 'stationary'
        else:
            return 'landing'


class Predictor:
    """Predict future states"""
    
    def __init__(self):
        self.history: Dict[str, List] = {}
    
    def predict_landing(self, altitude: float, descent_rate: float) -> float:
        """Predict time to landing (seconds)"""
        if descent_rate <= 0:
            return float('inf')
        return altitude / descent_rate
    
    def predict_max_altitude(self, ascent_rate: float, burnout_time: int = 60) -> float:
        """Predict max altitude (meters)"""
        # Simple ballistic model
        return 1000 + (ascent_rate * burnout_time) - (0.5 * 9.81 * (burnout_time ** 2) / ascent_rate)
    
    def predict_battery_runtime(self, current_battery: float, consumption_rate: float) -> float:
        """Predict remaining battery runtime (minutes)"""
        if consumption_rate <= 0:
            return float('inf')
        return (current_battery / consumption_rate) * 60


class DataAnalyzer:
    """Analyze sensor data patterns"""
    
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.flight_classifier = FlightPhaseClassifier()
        self.predictor = Predictor()
        
        self.current_phase = 'ground'
        self.alerts: List[Dict] = []
    
    def analyze(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Full analysis of sensor data"""
        results = {}
        
        # Check each sensor for anomalies
        for key in ['temperature', 'pressure', 'altitude', 'battery']:
            if key in sensor_data:
                result = self.anomaly_detector.update(key, sensor_data[key])
                if result.get('anomaly'):
                    self.alerts.append({
                        'time': time.time(),
                        'type': result.get('type'),
                        'sensor': key,
                        'value': result.get('value')
                    })
        
        # Classify flight phase
        altitude = sensor_data.get('altitude', 0)
        speed = sensor_data.get('speed', 0)
        self.current_phase = self.flight_classifier.classify(altitude, speed)
        
        results['phase'] = self.current_phase
        results['anomalies'] = len([a for a in self.alerts if time.time() - a['time'] < 60])
        
        # Predictions
        results['landing_time'] = self.predictor.predict_landing(
            altitude,
            sensor_data.get('vertical_speed', -5)
        )
        
        results['battery_runtime'] = self.predictor.predict_battery_runtime(
            sensor_data.get('battery', 100),
            sensor_data.get('battery_rate', 1)
        )
        
        return results
    
    def get_recommendations(self, sensor_data: Dict[str, Any]) -> List[str]:
        """Get AI recommendations"""
        recs = []
        
        # Battery check
        if sensor_data.get('battery', 100) < 20:
            recs.append("⚠️ LOW BATTERY - Consider mission abort")
        
        # Temperature check
        if sensor_data.get('temperature', 25) < -10:
            recs.append("❄️ LOW TEMPERATURE - Heater may be needed")
        elif sensor_data.get('temperature', 25) > 40:
            recs.append("🔥 HIGH TEMPERATURE - Check cooling")
        
        # Altitude check
        if sensor_data.get('altitude', 0) > 10000:
            recs.append("🛫 HIGH ALTITUDE - Check parachute deployment")
        
        # Pressure check
        if sensor_data.get('pressure', 1013) < 900:
            recs.append("🌊 LOW PRESSURE - High altitude operation")
        
        return recs
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary"""
        return {
            'current_phase': self.current_phase,
            'recent_alerts': len(self.alerts),
            'alerts': self.alerts[-10:]
        }


class AIModule:
    """Main AI Module combining all features"""
    
    def __init__(self):
        self.analyzer = DataAnalyzer()
        self.model_loaded = False
    
    def process(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data through AI pipeline"""
        # Add timestamp
        sensor_data['ai_timestamp'] = time.time()
        
        # Analyze
        analysis = self.analyzer.analyze(sensor_data)
        
        # Get recommendations
        recommendations = self.analyzer.get_recommendations(sensor_data)
        
        return {
            'analysis': analysis,
            'recommendations': recommendations,
            'timestamp': time.time()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get AI status"""
        return self.analyzer.get_summary()


def main():
    """Test AI module"""
    ai = AIModule()
    
    # Test data
    test_data = {
        'temperature': 25.0,
        'humidity': 50.0,
        'pressure': 1013.0,
        'altitude': 1000.0,
        'speed': 10.0,
        'vertical_speed': 5.0,
        'battery': 80.0,
        'battery_rate': 2.0
    }
    
    result = ai.process(test_data)
    
    print("Analysis:", result['analysis'])
    print("Recommendations:", result['recommendations'])


if __name__ == "__main__":
    main()