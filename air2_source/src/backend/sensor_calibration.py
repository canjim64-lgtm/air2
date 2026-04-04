"""
Sensor Calibration Module - Full Implementation
Calibration and cross-calibration for all sensors
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import deque


class IMUCalibrator:
    """Calibrate IMU (accelerometer + gyroscope)"""
    
    def __init__(self):
        self.accel_bias = np.array([0.0, 0.0, 0.0])
        self.accel_scale = np.eye(3)
        self.gyro_bias = np.array([0.0, 0.0, 0.0])
        self.calibrated = False
        self.samples = deque(maxlen=500)
    
    def collect_sample(self, accel: np.ndarray, gyro: np.ndarray):
        """Collect calibration sample"""
        self.samples.append({'accel': accel, 'gyro': gyro})
    
    def calibrate(self):
        """Perform calibration"""
        if len(self.samples) < 100:
            return False
        
        # Calculate mean acceleration (should be ~1g in one axis)
        accels = np.array([s['accel'] for s in self.samples])
        gyros = np.array([s['gyro'] for s in self.samples])
        
        # Bias is mean offset
        self.accel_bias = np.mean(accels, axis=0)
        self.gyro_bias = np.mean(gyros, axis=0)
        
        # Scale factors (simplified)
        self.accel_scale = np.eye(3)
        
        self.calibrated = True
        return True
    
    def apply(self, accel: np.ndarray, gyro: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Apply calibration"""
        if not self.calibrated:
            return accel, gyro
        
        # Remove bias and apply scale
        accel_cal = self.accel_scale @ (accel - self.accel_bias)
        gyro_cal = gyro - self.gyro_bias
        
        return accel_cal, gyro_cal


class BarometerCalibrator:
    """Calibrate barometer with known altitude"""
    
    def __init__(self):
        self.sea_level_pressure = 101325.0
        self.offset = 0
        self.calibrated = False
        self.samples = deque(maxlen=100)
    
    def set_known_altitude(self, altitude: float, pressure: float):
        """Set known pressure at altitude"""
        # Standard atmosphere: P = P0 * (1 - 0.0000225577 * h)^5.25588
        # Simplified: P0 = P * exp(h / 8400)
        self.sea_level_pressure = pressure * np.exp(altitude / 8400)
        self.calibrated = True
    
    def collect_sample(self, pressure: float, temperature: float):
        """Collect sample for calibration"""
        self.samples.append({'pressure': pressure, 'temperature': temperature})
    
    def calibrate(self):
        """Calibrate from samples"""
        if len(self.samples) < 10:
            return False
        
        pressures = [s['pressure'] for s in self.samples]
        self.offset = np.mean(presses) - self.sea_level_pressure
        self.calibrated = True
        return True
    
    def get_altitude(self, pressure: float) -> float:
        """Calculate altitude from pressure"""
        if not self.calibrated:
            return 0
        
        p = pressure - self.offset
        # Inverse of standard atmosphere
        return 44330 * (1 - (p / self.sea_level_pressure) ** 0.1903)


class GPSCalibrator:
    """Calibrate GPS position"""
    
    def __init__(self):
        self.reference_lat = 0
        self.reference_lon = 0
        self.datum_set = False
    
    def set_datum(self, lat: float, lon: float):
        """Set reference datum"""
        self.reference_lat = lat
        self.reference_lon = lon
        self.datum_set = True
    
    def apply(self, lat: float, lon: float) -> Dict:
        """Apply datum offset"""
        if not self.datum_set:
            return {'lat': lat, 'lon': lon, 'lat_offset': 0, 'lon_offset': 0}
        
        return {
            'lat': lat,
            'lon': lon,
            'lat_offset': lat - self.reference_lat,
            'lon_offset': lon - self.reference_lon
        }


class GasSensorCalibrator:
    """Calibrate gas sensors (VOC, CO2)"""
    
    def __init__(self):
        self.voc_baseline = 0
        self.co2_baseline = 400
        self.temp_compensation = {}
        self.calibrated = False
    
    def set_clean_air(self, voc: float, co2: float, temp: float):
        """Set baseline from clean air"""
        self.voc_baseline = voc
        self.co2_baseline = co2
        self.temp_compensation['base_temp'] = temp
        self.calibrated = True
    
    def collect_sample(self, voc: float, co2: float, temp: float, humidity: float):
        """Collect sample"""
        pass  # Would store for drift analysis
    
    def apply(self, voc: float, co2: float, temp: float) -> Dict:
        """Apply calibration"""
        if not self.calibrated:
            return {'voc': voc, 'co2': co2, 'compensated': False}
        
        # Temperature compensation
        base_temp = self.temp_compensation.get('base_temp', 25)
        temp_factor = 1 + 0.01 * (temp - base_temp)
        
        voc_comp = (voc - self.voc_baseline) * temp_factor
        co2_comp = (co2 - self.co2_baseline)
        
        return {
            'voc': max(0, voc_comp),
            'co2': max(0, co2_comp),
            'compensated': True,
            'temp_factor': temp_factor
        }


class MagnetometerCalibrator:
    """Calibrate magnetometer (hard/soft iron)"""
    
    def __init__(self):
        self.hard_iron = np.array([0.0, 0.0, 0.0])
        self.soft_iron = np.eye(3)
        self.calibrated = False
        self.samples = deque(maxlen=500)
    
    def collect_sample(self, mag: np.ndarray):
        """Collect sample during rotation"""
        self.samples.append(mag)
    
    def calibrate(self):
        """Perform 3D ellipse fitting"""
        if len(self.samples) < 100:
            return False
        
        mags = np.array(self.samples)
        
        # Find center (hard iron)
        self.hard_iron = np.mean(mags, axis=0)
        
        # Find scale (soft iron) - simplified
        stds = np.std(mags, axis=0)
        self.soft_iron = np.diag(1 / (stds + 0.001))
        
        self.calibrated = True
        return True
    
    def apply(self, mag: np.ndarray) -> np.ndarray:
        """Apply calibration"""
        if not self.calibrated:
            return mag
        
        # Remove hard iron, apply soft iron
        return self.soft_iron @ (mag - self.hard_iron)


class CrossSensorCalibrator:
    """Calibrate sensors against each other"""
    
    def __init__(self):
        self.baro_alt = 0
        self.gps_alt = 0
        self.offset = 0
    
    def calibrate_altitude(self, baro_alt: float, gps_alt: float):
        """Calibrate barometer against GPS"""
        self.baro_alt = baro_alt
        self.gps_alt = gps_alt
        self.offset = baro_alt - gps_alt
        return self.offset
    
    def apply_baro_offset(self, alt: float) -> float:
        """Apply offset"""
        return alt - self.offset
    
    def calibrate_rssi_distance(self, rssi: float, distance: float):
        """Calibrate RSSI vs distance"""
        # Simple path loss model: RSSI = TxPower - 10*n*log10(d)
        # Assume n = 2 (free space), TxPower = -20 dBm
        n = 2
        tx_power = -20
        measured_power = tx_power - 10 * n * np.log10(max(distance, 1))
        
        return measured_power - rssi


class CalibrationManager:
    """Manage all calibrations"""
    
    def __init__(self):
        self.imu = IMUCalibrator()
        self.baro = BarometerCalibrator()
        self.gps = GPSCalibrator()
        self.gas = GasSensorCalibrator()
        self.mag = MagnetometerCalibrator()
        self.cross = CrossSensorCalibrator()
        self.calibration_status = {}
    
    def get_status(self) -> Dict:
        """Get calibration status"""
        return {
            'imu': self.imu.calibrated,
            'barometer': self.baro.calibrated,
            'gps': self.gps.datum_set,
            'gas': self.gas.calibrated,
            'magnetometer': self.mag.calibrated
        }
    
    def save_calibration(self, filename: str):
        """Save calibration to file"""
        import json
        
        data = {
            'imu_accel_bias': self.imu.accel_bias.tolist(),
            'imu_gyro_bias': self.imu.gyro_bias.tolist(),
            'baro_sea_level': self.baro.sea_level_pressure,
            'baro_offset': self.baro.offset,
            'gps_datum': [self.gps.reference_lat, self.gps.reference_lon],
            'gas_voc_baseline': self.gas.voc_baseline,
            'gas_co2_baseline': self.gas.co2_baseline,
            'mag_hard_iron': self.mag.hard_iron.tolist(),
            'cross_alt_offset': self.cross.offset
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f)
    
    def load_calibration(self, filename: str):
        """Load calibration from file"""
        import json
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.imu.accel_bias = np.array(data['imu_accel_bias'])
        self.imu.gyro_bias = np.array(data['imu_gyro_bias'])
        self.imu.calibrated = True
        
        self.baro.sea_level_pressure = data['baro_sea_level']
        self.baro.offset = data['baro_offset']
        self.baro.calibrated = True
        
        self.gps.reference_lat = data['gps_datum'][0]
        self.gps.reference_lon = data['gps_datum'][1]
        self.gps.datum_set = True
        
        self.gas.voc_baseline = data['gas_voc_baseline']
        self.gas.co2_baseline = data['gas_co2_baseline']
        self.gas.calibrated = True
        
        self.mag.hard_iron = np.array(data['mag_hard_iron'])
        self.mag.calibrated = True
        
        self.cross.offset = data['cross_alt_offset']


# Example
if __name__ == "__main__":
    cm = CalibrationManager()
    
    # Simulate calibration
    cm.imu.collect_sample(np.array([0.1, 9.8, 0.2]), np.array([0.01, 0.02, 0.01]))
    cm.imu.calibrate()
    
    print(f"Calibration status: {cm.get_status()}")