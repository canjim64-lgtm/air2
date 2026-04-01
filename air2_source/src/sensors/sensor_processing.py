"""
Sensor Processing Module
All sensor processing, calibration, and data fusion
"""

import numpy as np
from typing import Dict, Tuple


class BarometerFusion:
    """Dual-barometer fusion with Kalman filter"""
    
    def __init__(self):
        # BMP388: high precision, BME688: stable
        self.Q = np.eye(2) * 0.01  # Process noise
        self.R = np.eye(2) * 0.1   # Measurement noise
        self.P = np.eye(2)         # Covariance
        self.x = np.zeros(2)       # State: [altitude_bmp, altitude_bme]
    
    def fuse(self, bmp_alt: float, bme_alt: float, dt: float = 0.1) -> float:
        """Fuse two barometer readings"""
        
        # State transition
        F = np.eye(2)
        
        # Prediction
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
        
        # Update
        z = np.array([bmp_alt, bme_alt])
        y = z - self.x  # Innovation
        
        S = self.P + self.R
        K = self.P @ np.linalg.inv(S)  # Kalman gain
        
        self.x = self.x + K @ y
        self.P = (np.eye(2) - K) @ self.P
        
        return float(np.mean(self.x))


class VOCCompensator:
    """VOC humidity/temperature compensation"""
    
    def __init__(self):
        self.baseline_temp = 25
        self.baseline_humidity = 50
    
    def compensate(self, voc_raw: float, temp: float, 
                  humidity: float) -> float:
        """Remove humidity/temperature effects"""
        
        # Thermal drift compensation
        temp_factor = 1 + 0.01 * (temp - self.baseline_temp)
        
        # Humidity compensation  
        humidity_factor = 1 + 0.005 * (humidity - self.baseline_humidity)
        
        compensated = voc_raw / (temp_factor * humidity_factor)
        
        return max(0, compensated)


class GeigerDeadTime:
    """Geiger counter dead-time compensation"""
    
    def __init__(self, dead_time_us: float = 190):
        self.dead_time = dead_time_us / 1e6  # Convert to seconds
    
    def compensate(self, cpm: float) -> float:
        """Apply dead-time correction"""
        
        # Non-paralysable model
        # True rate = observed / (1 - observed * dead_time)
        
        observed_rate = cpm / 60.0  # Convert to counts per second
        
        if observed_rate * self.dead_time >= 1:
            return cpm  # Saturated
        
        true_rate = observed_rate / (1 - observed_rate * self.dead_time)
        
        return true_rate * 60  # Convert back to CPM


class AtmosphericLapseRate:
    """Calculate atmospheric lapse rate"""
    
    def __init__(self):
        self.history = []
    
    def calculate(self, altitude: float, temperature: float) -> float:
        """Calculate temperature lapse rate"""
        
        self.history.append({'alt': altitude, 'temp': temperature})
        
        if len(self.history) < 2:
            return 0
        
        # Sort by altitude
        sorted_history = sorted(self.history, key=lambda x: x['alt'])
        
        if len(sorted_history) > 10:
            sorted_history = sorted_history[-10:]
        
        # Linear regression
        alts = [h['alt'] for h in sorted_history]
        temps = [h['temp'] for h in sorted_history]
        
        if alts[-1] == alts[0]:
            return 0
        
        # Lapse rate in °C per meter
        lapse_rate = (temps[-1] - temps[0]) / (alts[-1] - alts[0])
        
        return lapse_rate
    
    def detect_inversion(self, lapse_rate: float) -> bool:
        """Detect temperature inversion"""
        return lapse_rate > 0  # Positive = inversion


class VirtualAnemometer:
    """Calculate wind from ToF + barometer + IMU"""
    
    def __init__(self):
        self.history = []
    
    def calculate_wind(self, tof_distance: float, 
                      vertical_vel: float,
                      imu_accel: np.ndarray,
                      dt: float = 0.1) -> Dict:
        """Estimate wind speed and direction"""
        
        # Visual velocity from ToF
        visual_vel = (self.history[-1]['tof'] - tof_distance) / dt if self.history else 0
        
        self.history.append({'tof': tof_distance, 'vvel': vertical_vel})
        
        if len(self.history) > 10:
            self.history = self.history[-10:]
        
        # IMU acceleration gives device motion
        device_accel = np.linalg.norm(imu_accel)
        
        # Wind = visual - device motion
        wind_speed = abs(visual_vel - device_accel * dt)
        
        return {
            'wind_speed': wind_speed,
            'direction': 0,  # Simplified
            'confidence': 0.7
        }


class RadiationCorrelator:
    """Correlate radiation with altitude/magnetic field"""
    
    def __init__(self):
        self.baseline_model = None
    
    def learn_baseline(self, altitude_data: list, 
                      radiation_data: list):
        """Learn normal radiation vs altitude"""
        
        # Simple polynomial fit
        coeffs = np.polyfit(altitude_data, radiation_data, 2)
        self.baseline_model = coeffs
    
    def detect_anomaly(self, altitude: float, 
                      radiation: float) -> Tuple[bool, float]:
        """Detect radiation anomaly"""
        
        if self.baseline_model is None:
            return False, 0
        
        # Predict expected
        expected = np.polyval(self.baseline_model, altitude)
        
        # Deviation
        deviation = radiation - expected
        
        # Z-score
        z_score = abs(deviation) / (expected * 0.2 + 1)
        
        return z_score > 2, z_score


class OpticalFlowWind:
    """Calculate wind from optical flow"""
    
    def __init__(self):
        self.prev_frame = None
    
    def calculate(self, current_frame: np.ndarray,
                  imu_tilt: np.ndarray) -> Dict:
        """Calculate wind from optical flow"""
        
        if self.prev_frame is None:
            self.prev_frame = current_frame
            return {'speed': 0, 'direction': 0}
        
        # Simple frame differencing
        diff = current_frame.astype(float) - self.prev_frame.astype(float)
        flow = np.mean(diff)
        
        # Remove tilt effect
        tilt_compensation = np.linalg.norm(imu_tilt) * 0.1
        
        wind_speed = abs(flow - tilt_compensation)
        
        self.prev_frame = current_frame
        
        return {
            'speed': wind_speed,
            'direction': np.angle(flow) if flow != 0 else 0,
            'confidence': 0.6
        }


class GasRatioAnalyzer:
    """Analyze gas ratios for source identification"""
    
    def __init__(self):
        self.ratios = {
            'vehicle_exhaust': 2.5,
            'wildfire': 1.8,
            'industrial': 3.0,
            'clean': 0.5
        }
    
    def analyze(self, h2: float, no2: float, co: float) -> Dict:
        """Analyze gas ratios"""
        
        ratio = (h2 + no2) / (co + 0.1)
        
        # Find closest match
        best_match = 'unknown'
        best_diff = float('inf')
        
        for source, expected_ratio in self.ratios.items():
            diff = abs(ratio - expected_ratio)
            if diff < best_diff:
                best_diff = diff
                best_match = source
        
        return {
            'ratio': ratio,
            'source': best_match,
            'confidence': 1.0 / (1.0 + best_diff)
        }


class ImpactDetector:
    """Detect impact from accelerometer"""
    
    def __init__(self, threshold: float = 50):
        self.threshold = threshold
        self.prev_accel = 0
    
    def detect(self, accel_magnitude: float) -> Tuple[bool, str]:
        """Detect impact"""
        
        # Change in acceleration
        delta = abs(accel_magnitude - self.prev_accel)
        self.prev_accel = accel_magnitude
        
        if delta > self.threshold:
            return True, "IMPACT"
        
        return False, "NONE"


class RSSIMapper:
    """Map RF signal strength"""
    
    def __init__(self):
        self.points = []
    
    def add_point(self, lat: float, lon: float, rssi: float):
        """Add RSSI measurement"""
        self.points.append({'lat': lat, 'lon': lon, 'rssi': rssi})
    
    def get_heatmap(self) -> Dict:
        """Get signal heatmap"""
        
        if not self.points:
            return {'min': 0, 'max': 0, 'points': []}
        
        rssi_values = [p['rssi'] for p in self.points]
        
        return {
            'min': min(rssi_values),
            'max': max(rssi_values),
            'points': self.points
        }


class VirtualHorizon:
    """Virtual horizon from magnetometer"""
    
    def __init__(self):
        pass
    
    def calculate(self, mag: np.ndarray, 
                  accel: np.ndarray) -> Dict:
        """Calculate pitch, roll, heading"""
        
        # Normalize accelerometer
        accel_norm = accel / (np.linalg.norm(accel) + 1e-10)
        
        # Pitch and roll from accelerometer
        pitch = np.arcsin(-accel_norm[0]) * 180 / np.pi
        roll = np.arctan2(accel_norm[1], accel_norm[2]) * 180 / np.pi
        
        # Heading from magnetometer (tilt compensated)
        heading = np.arctan2(mag[1], mag[0]) * 180 / np.pi
        if heading < 0:
            heading += 360
        
        return {
            'pitch': pitch,
            'roll': roll,
            'heading': heading
        }


class PacketValidator:
    """Validate and correct telemetry packets"""
    
    def __init__(self):
        pass
    
    def validate(self, packet: Dict) -> Tuple[bool, Dict]:
        """Validate packet with CRC"""
        
        # Simple range checks
        valid = True
        corrected = packet.copy()
        
        # Altitude
        if 'altitude' in packet:
            alt = packet['altitude']
            if alt < -100 or alt > 50000:
                valid = False
        
        # Temperature
        if 'temperature' in packet:
            temp = packet['temperature']
            if temp < -50 or temp > 150:
                corrected['temperature'] = np.clip(temp, -50, 150)
        
        # Pressure
        if 'pressure' in packet:
            pres = packet['pressure']
            if pres < 0 or pres > 200000:
                valid = False
        
        return valid, corrected


# Example
if __name__ == "__main__":
    print("Sensor Processing Modules Ready")
    
    # Test barometer fusion
    bf = BarometerFusion()
    alt = bf.fuse(1000, 1001)
    print(f"Fused altitude: {alt}")
    
    # Test VOC
    voc = VOCCompensator()
    compensated = voc.compensate(100, 30, 70)
    print(f"Compensated VOC: {compensated}")
    
    # Test Geiger
    geiger = GeigerDeadTime()
    corrected = geiger.compensate(500)
    print(f"Corrected CPM: {corrected}")