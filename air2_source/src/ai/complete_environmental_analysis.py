"""
Complete Environmental Analysis System for Air2 CanSat
Comprehensive sensor fusion for atmospheric, radiation, magnetic, and environmental analysis
Based on ESP32-WROVER-E hardware with all specified sensors
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import time
import threading


# ============================================================================
# SENSOR DATA CLASSES
# ============================================================================

@dataclass
class BME688Data:
    """BME688 Environmental Sensor Data"""
    timestamp: float
    temperature: float  # Celsius
    pressure: float  # hPa
    humidity: float  # %
    gas_resistance: float  # Ohm
    altitude: float = 0.0  # Computed altitude


@dataclass
class BMP388Data:
    """BMP388 Barometric Sensor Data"""
    timestamp: float
    pressure: float  # hPa
    temperature: float  # Celsius
    altitude: float = 0.0


@dataclass
class MiCS6814Data:
    """MiCS-6814 3-in-1 Gas Sensor Data"""
    timestamp: float
    nh3: float  # Ammonia ppm
    co: float  # Carbon monoxide ppm
    no2: float  # Nitrogen dioxide ppm


@dataclass
class SGP30Data:
    """SGP30 TVOC + eCO2 Sensor Data"""
    timestamp: float
    tvoc: float  # ppb
    eco2: float  # ppm


@dataclass
class UVData:
    """UV-A and UV-B Sensor Data"""
    timestamp: float
    uva: float  # mW/m²
    uvb: float  # mW/m²
    uv_index: float = 0.0


@dataclass
class LightData:
    """TSL2591 Light Sensor Data"""
    timestamp: float
    lux: float
    infrared: float
    visible: float


@dataclass
class GeigerData:
    """Geiger Counter Data (M4011 Tube)"""
    timestamp: float
    count_rate: float  # CPM (counts per minute)
    dose_rate: float  # µSv/h


@dataclass
class MagnetometerData:
    """MMC5603 Magnetometer Data"""
    timestamp: float
    mag_x: float  # µT
    mag_y: float  # µT
    mag_z: float  # µT
    heading: float = 0.0  # Degrees


@dataclass
class GNSSData:
    """GNSS Position Data"""
    timestamp: float
    latitude: float
    longitude: float
    altitude: float
    speed: float  # m/s
    satellites: int
    accuracy: float


@dataclass
class PowerSystemData:
    """Power System Health Data"""
    timestamp: float
    battery_voltage: float  # V
    battery_current: float  # mA
    battery_level: float  # %
    temperature: float  # Battery temp
    health_status: str


# ============================================================================
# ANALYSIS ENUMS
# ============================================================================

class AirQualityLevel(Enum):
    GOOD = 0
    MODERATE = 1
    UNHEALTHY_SENSITIVE = 2
    UNHEALTHY = 3
    VERY_UNHEALTHY = 4
    HAZARDOUS = 5


class AtmosphericStability(Enum):
    VERY_STABLE = 0
    STABLE = 1
    NEUTRAL = 2
    UNSTABLE = 3
    VERY_UNSTABLE = 4


# ============================================================================
# BOUNDARY LAYER & INVERSION DETECTION
# ============================================================================

class BoundaryLayerDetector:
    """
    Detects atmospheric boundary layer and temperature inversions.
    Critical for understanding pollutant trapping and air quality.
    """
    
    def __init__(self, window_size: int = 100):
        self.altitude_history = deque(maxlen=window_size)
        self.temp_history = deque(maxlen=window_size)
        self.pressure_history = deque(maxlen=window_size)
        self.humidity_history = deque(maxlen=window_size)
        self.voc_history = deque(maxlen=window_size)
        
        self.inversion_layers: List[Dict] = []
        self.boundary_layer_height = 0.0
        
        # Lapse rate thresholds (°C per 100m)
        self.normal_lapse_rate = -0.65  # Standard atmosphere
        self.inversion_threshold = 0.5  # Positive lapse rate indicates inversion
        
    def add_reading(self, altitude: float, temperature: float, pressure: float, 
                   humidity: float, voc: float):
        """Add atmospheric reading."""
        self.altitude_history.append(altitude)
        self.temp_history.append(temperature)
        self.pressure_history.append(pressure)
        self.humidity_history.append(humidity)
        self.voc_history.append(voc)
        
    def detect_inversions(self) -> List[Dict]:
        """Detect temperature inversion layers."""
        if len(self.altitude_history) < 20:
            return []
            
        altitudes = np.array(list(self.altitude_history))
        temperatures = np.array(list(self.temp_history))
        
        # Sort by altitude (descending)
        sort_idx = np.argsort(-altitudes)
        alt_sorted = altitudes[sort_idx]
        temp_sorted = temperatures[sort_idx]
        
        # Detect where temperature increases with altitude
        inversions = []
        i = 0
        while i < len(alt_sorted) - 1:
            delta_alt = alt_sorted[i] - alt_sorted[i + 1]
            delta_temp = temp_sorted[i + 1] - temp_sorted[i]
            
            if delta_alt > 0 and delta_temp > 0.5:  # Inversion detected
                lapse_rate = (delta_temp / delta_alt) * 100  # °C per 100m
                
                if lapse_rate > self.inversion_threshold:
                    inversions.append({
                        'base_altitude': alt_sorted[i + 1],
                        'top_altitude': alt_sorted[i],
                        'thickness': alt_sorted[i] - alt_sorted[i + 1],
                        'lapse_rate': lapse_rate,
                        'temperature_rise': delta_temp,
                        'confidence': min(1.0, lapse_rate / 3)
                    })
                    i += 5  # Skip ahead
                else:
                    i += 1
            else:
                i += 1
                
        self.inversion_layers = inversions
        return inversions
        
    def estimate_boundary_layer_height(self) -> float:
        """Estimate boundary layer height using virtual potential temperature."""
        if len(self.altitude_history) < 30:
            return 0.0
            
        altitudes = np.array(list(self.altitude_history))
        temperatures = np.array(list(self.temp_history))
        pressures = np.array(list(self.pressure_history))
        
        # Calculate virtual potential temperature
        vt = temperatures * (1.0 + 0.61 * (self.humidity_history[-1] / 100))
        
        # Find height where vt gradient changes sign
        grad = np.gradient(vt, altitudes)
        
        # Boundary layer is where gradient is minimum (most stable)
        min_grad_idx = np.argmin(grad)
        self.boundary_layer_height = altitudes[min_grad_idx]
        
        return self.boundary_layer_height
        
    def get_inversion_report(self) -> Dict:
        """Generate comprehensive inversion report."""
        inversions = self.detect_inversions()
        blh = self.estimate_boundary_layer_height()
        
        if not inversions:
            return {
                'status': 'No significant inversions detected',
                'boundary_layer_height': blh,
                'stability_class': 'NEUTRAL',
                'pollution_trapping': False
            }
            
        strongest = max(inversions, key=lambda x: x['lapse_rate'])
        
        return {
            'status': f'{len(inversions)} inversion layer(s) detected',
            'inversions': inversions,
            'boundary_layer_height': blh,
            'strongest_inversion': strongest,
            'stability_class': 'VERY_STABLE' if strongest['lapse_rate'] > 2 else 'STABLE',
            'pollution_trapping': True,
            'recommendation': 'Inversion layer present - pollutants may accumulate'
        }


# ============================================================================
# AIR QUALITY INDEX (AQI) ESTIMATION
# ============================================================================

class AirQualityEstimator:
    """
    Real-time Air Quality Index estimation using all gas sensors.
    Combines PM2.5 proxy, O3, NO2, CO, and VOC data.
    """
    
    # AQI breakpoints (US EPA standard)
    AQI_BREAKPOINTS = {
        'pm25': [(0, 12, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
                 (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500, 301, 500)],
        'o3': [(0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150),
               (86, 105, 151, 200), (106, 200, 201, 300)],
        'co': [(0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
               (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300)],
        'no2': [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
                (361, 649, 151, 200), (650, 1249, 201, 300)]
    }
    
    def __init__(self):
        self.history = deque(maxlen=200)
        
    def add_reading(self, timestamp: float, voc: float, co2: float, nh3: float, 
                   co: float, no2: float, temperature: float, humidity: float):
        """Add air quality sensor reading."""
        self.history.append({
            'timestamp': timestamp,
            'voc': voc,
            'co2': co2,
            'nh3': nh3,
            'co': co,
            'no2': no2,
            'temp': temperature,
            'humidity': humidity
        })
        
    def estimate_pm25_proxy(self) -> float:
        """Estimate PM2.5 from optical and gas data."""
        if len(self.history) < 10:
            return 0.0
            
        recent = list(self.history)[-10:]
        
        # PM2.5 proxy from VOC and NO2 (simplified model)
        avg_voc = np.mean([r['voc'] for r in recent])
        avg_no2 = np.mean([r['no2'] for r in recent])
        
        # Empirical relationship (would be calibrated)
        pm25_proxy = (avg_voc * 0.05) + (avg_no2 * 0.3)
        
        return min(500, pm25_proxy)
        
    def calculate_aqi(self, pollutant: str, concentration: float) -> int:
        """Calculate AQI for a specific pollutant."""
        if pollutant not in self.AQI_BREAKPOINTS:
            return 0
            
        bp = self.AQI_BREAKPOINTS[pollutant]
        
        for c_low, c_high, i_low, i_high in bp:
            if c_low <= concentration <= c_high:
                # Linear interpolation
                aqi = i_low + ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low)
                return int(aqi)
                
        return 500  # Maximum AQI
        
    def get_current_aqi(self) -> Dict:
        """Calculate overall AQI and sub-indices."""
        if not self.history:
            return {'status': 'No data', 'aqi': 0}
            
        latest = self.history[-1]
        
        # Calculate sub-indices
        pm25_aqi = self.calculate_aqi('pm25', self.estimate_pm25_proxy())
        co_aqi = self.calculate_aqi('co', latest['co'])
        no2_aqi = self.calculate_aqi('no2', latest['no2'])
        
        # Overall AQI is max of all sub-indices
        overall_aqi = max(pm25_aqi, co_aqi, no2_aqi)
        
        # Determine category
        if overall_aqi <= 50:
            category = 'Good'
            health_advice = 'Air quality is satisfactory.'
        elif overall_aqi <= 100:
            category = 'Moderate'
            health_advice = 'Sensitive individuals should consider limiting outdoor exertion.'
        elif overall_aqi <= 150:
            category = 'Unhealthy for Sensitive Groups'
            health_advice = 'Sensitive groups should reduce outdoor exertion.'
        elif overall_aqi <= 200:
            category = 'Unhealthy'
            health_advice = 'Everyone should reduce outdoor exertion.'
        elif overall_aqi <= 300:
            category = 'Very Unhealthy'
            health_advice = 'Avoid outdoor activities.'
        else:
            category = 'Hazardous'
            health_advice = 'Health emergency. Stay indoors.'
            
        return {
            'aqi': overall_aqi,
            'category': category,
            'health_advice': health_advice,
            'sub_indices': {
                'pm25_proxy': pm25_aqi,
                'co': co_aqi,
                'no2': no2_aqi
            },
            'dominant_pollutant': self._identify_dominant(pm25_aqi, co_aqi, no2_aqi)
        }
        
    def _identify_dominant(self, pm25: int, co: int, no2: int) -> str:
        """Identify the dominant pollutant."""
        values = {'PM2.5': pm25, 'CO': co, 'NO2': no2}
        return max(values, key=values.get)


# ============================================================================
# RADIATION ANALYSIS
# ============================================================================

class RadiationAnalyzer:
    """
    Comprehensive radiation analysis with altitude correlation,
    magnetic field correlation, burst detection, and geographic mapping.
    """
    
    def __init__(self):
        self.altitude_history = deque(maxlen=500)
        self.radiation_history = deque(maxlen=500)
        self.mag_field_history = deque(maxlen=500)
        self.uv_history = deque(maxlen=500)
        self.position_history = deque(maxlen=500)
        self.timestamps = deque(maxlen=500)
        
        # Background radiation baseline
        self.background_level = 0.08  # µSv/h (typical sea level)
        
        # Burst detection
        self.burst_threshold = 3.0  # 3x background
        
    def add_reading(self, timestamp: float, altitude: float, radiation: float,
                   mag_x: float, mag_y: float, mag_z: float,
                   uv_index: float, lat: float, lon: float):
        """Add sensor reading."""
        self.timestamps.append(timestamp)
        self.altitude_history.append(altitude)
        self.radiation_history.append(radiation)
        self.mag_field_history.append((mag_x, mag_y, mag_z))
        self.uv_history.append(uv_index)
        self.position_history.append((lat, lon))
        
    def calculate_altitude_correlation(self) -> Dict:
        """Calculate radiation vs altitude relationship."""
        if len(self.radiation_history) < 20:
            return {'status': 'Insufficient data'}
            
        altitudes = np.array(list(self.altitude_history))
        radiations = np.array(list(self.radiation_history))
        
        # Fit exponential model: R = R0 * exp(k * alt)
        log_r = np.log(radiations + 0.01)
        coeffs = np.polyfit(altitudes, log_r, 1)
        
        r0 = np.exp(coeffs[1])  # Sea level radiation
        k = coeffs[0]  # Altitude coefficient
        
        # Calculate expected at various altitudes
        expected_500 = r0 * np.exp(k * 500)
        expected_1000 = r0 * np.exp(k * 1000)
        
        # Check for anomalies
        anomaly_detected = False
        anomaly_alt = 0
        anomaly_ratio = 0
        
        for alt, rad in zip(altitudes, radiations):
            expected = r0 * np.exp(k * alt)
            if expected > 0 and rad > expected * 2:
                anomaly_detected = True
                if rad / expected > anomaly_ratio:
                    anomaly_ratio = rad / expected
                    anomaly_alt = alt
                    
        return {
            'sea_level_baseline': r0,
            'altitude_coefficient': k,
            'expected_500m': expected_500,
            'expected_1000m': expected_1000,
            'anomaly_detected': anomaly_detected,
            'anomaly_altitude': anomaly_alt,
            'anomaly_ratio': anomaly_ratio
        }
        
    def calculate_magnetic_correlation(self) -> Dict:
        """Calculate radiation vs magnetic field correlation."""
        if len(self.radiation_history) < 30:
            return {'status': 'Insufficient data'}
            
        radiations = np.array(list(self.radiation_history))
        mag_x = np.array([m[0] for m in self.mag_field_history])
        mag_y = np.array([m[1] for m in self.mag_field_history])
        mag_z = np.array([m[2] for m in self.mag_field_history])
        
        # Total magnetic field strength
        mag_total = np.sqrt(mag_x**2 + mag_y**2 + mag_z**2)
        
        # Correlation coefficient
        correlation = np.corrcoef(radiations, mag_total)[0, 1]
        
        return {
            'correlation_coefficient': float(correlation),
            'correlation_strength': 'Strong' if abs(correlation) > 0.7 else 
                                   'Moderate' if abs(correlation) > 0.4 else 'Weak',
            'interpretation': self._interpret_mag_correlation(correlation)
        }
        
    def _interpret_mag_correlation(self, corr: float) -> str:
        """Interpret magnetic-radiation correlation."""
        if abs(corr) < 0.2:
            return "No significant correlation between magnetic field and radiation"
        elif corr > 0:
            return "Higher radiation associated with stronger magnetic field (possible solar influence)"
        else:
            return "Higher radiation associated with weaker magnetic field (possible geographic effect)"
            
    def detect_bursts(self) -> List[Dict]:
        """Detect radiation bursts/spikes."""
        if len(self.radiation_history) < 20:
            return []
            
        radiations = np.array(list(self.radiation_history))
        timestamps = np.array(list(self.timestamps))
        
        # Calculate sliding baseline
        baseline = np.convolve(radiations, np.ones(10)/10, mode='same')
        
        # Detect bursts (3x baseline)
        bursts = []
        for i, (rad, base) in enumerate(zip(radiations, baseline)):
            if base > 0 and rad > base * self.burst_threshold:
                bursts.append({
                    'timestamp': timestamps[i],
                    'altitude': list(self.altitude_history)[i],
                    'intensity': rad,
                    'baseline': base,
                    'ratio': rad / base
                })
                
        return bursts
        
    def map_cosmic_rays(self) -> Dict:
        """Map cosmic ray intensity to geographic location."""
        if len(self.position_history) < 20:
            return {'status': 'Insufficient data for mapping'}
            
        positions = np.array(list(self.position_history))
        radiations = np.array(list(self.radiation_history))
        
        # Simple grid-based mapping
        lat_bins = np.linspace(positions[:, 0].min(), positions[:, 0].max(), 10)
        lon_bins = np.linspace(positions[:, 1].min(), positions[:, 1].max(), 10)
        
        grid = np.zeros((len(lat_bins)-1, len(lon_bins)-1))
        counts = np.zeros((len(lat_bins)-1, len(lon_bins)-1))
        
        for i, (pos, rad) in enumerate(zip(positions, radiations)):
            lat_idx = np.digitize(pos[0], lat_bins) - 1
            lon_idx = np.digitize(pos[1], lon_bins) - 1
            
            if 0 <= lat_idx < len(lat_bins) - 1 and 0 <= lon_idx < len(lon_bins) - 1:
                grid[lat_idx, lon_idx] += rad
                counts[lat_idx, lon_idx] += 1
                
        # Average
        grid = np.divide(grid, counts, where=counts > 0, out=np.zeros_like(grid))
        
        return {
            'radiation_grid': grid.tolist(),
            'lat_bins': lat_bins.tolist(),
            'lon_bins': lon_bins.tolist(),
            'max_intensity_location': self._find_max_location(grid, lat_bins, lon_bins)
        }
        
    def _find_max_location(self, grid: np.ndarray, lat_bins: np.ndarray, lon_bins: np.ndarray) -> Tuple[float, float]:
        """Find location of maximum radiation."""
        max_idx = np.unravel_index(np.argmax(grid), grid.shape)
        lat = (lat_bins[max_idx[0]] + lat_bins[max_idx[0] + 1]) / 2
        lon = (lon_bins[max_idx[1]] + lon_bins[max_idx[1] + 1]) / 2
        return (lat, lon)
        
    def get_radiation_report(self) -> Dict:
        """Generate comprehensive radiation report."""
        return {
            'altitude_correlation': self.calculate_altitude_correlation(),
            'magnetic_correlation': self.calculate_magnetic_correlation(),
            'bursts_detected': self.detect_bursts(),
            'geographic_map': self.map_cosmic_rays(),
            'current_radiation': float(list(self.radiation_history)[-1]) if self.radiation_history else 0,
            'average_radiation': float(np.mean(list(self.radiation_history))) if self.radiation_history else 0
        }


# ============================================================================
# MAGNETIC FIELD ANALYSIS
# ============================================================================

class MagneticAnalyzer:
    """
    Magnetic field vector mapping and attitude estimation.
    Includes magnetic anomaly detection and correlation with radiation.
    """
    
    def __init__(self):
        self.mag_history = deque(maxlen=500)
        self.timestamp_history = deque(maxlen=500)
        self.altitude_history = deque(maxlen=500)
        self.radiation_history = deque(maxlen=500)
        
        # Earth's field reference (varies by location)
        self.earth_field_reference = 45.0  # µT (typical mid-latitude)
        
    def add_reading(self, timestamp: float, mag_x: float, mag_y: float, mag_z: float,
                   altitude: float, radiation: float):
        """Add magnetometer reading."""
        self.mag_history.append((mag_x, mag_y, mag_z))
        self.timestamp_history.append(timestamp)
        self.altitude_history.append(altitude)
        self.radiation_history.append(radiation)
        
    def calculate_heading(self) -> float:
        """Calculate magnetic heading from magnetometer data."""
        if len(self.mag_history) < 1:
            return 0.0
            
        mag_x, mag_y, mag_z = self.mag_history[-1]
        
        # Calculate heading (assuming level)
        heading = np.degrees(np.arctan2(mag_y, mag_x))
        heading = (heading + 360) % 360
        
        return heading
        
    def calculate_field_vector(self) -> Dict:
        """Calculate magnetic field vector magnitude and direction."""
        if len(self.mag_history) < 10:
            return {'status': 'Insufficient data'}
            
        vectors = np.array(self.mag_history)
        
        total = np.sqrt(vectors[:, 0]**2 + vectors[:, 1]**2 + vectors[:, 2]**2)
        
        return {
            'mean_magnitude': float(np.mean(total)),
            'std_magnitude': float(np.std(total)),
            'mean_vector': vectors.mean(axis=0).tolist(),
            'min_magnitude': float(np.min(total)),
            'max_magnitude': float(np.max(total)),
            'anomaly_detected': np.std(total) > 5.0  # High variance indicates anomaly
        }
        
    def detect_magnetic_anomalies(self) -> List[Dict]:
        """Detect magnetic anomalies that may correlate with radiation."""
        if len(self.mag_history) < 30:
            return []
            
        vectors = np.array(self.mag_history)
        total = np.sqrt(vectors[:, 0]**2 + vectors[:, 1]**2 + vectors[:, 2]**2)
        
        anomalies = []
        mean_field = np.mean(total)
        std_field = np.std(total)
        
        for i, mag in enumerate(total):
            if abs(mag - mean_field) > 2 * std_field:
                anomalies.append({
                    'timestamp': list(self.timestamp_history)[i],
                    'altitude': list(self.altitude_history)[i],
                    'magnitude': mag,
                    'deviation': (mag - mean_field) / std_field,
                    'vector': vectors[i].tolist()
                })
                
        return anomalies
        
    def correlate_with_radiation(self) -> Dict:
        """Correlate magnetic field with radiation levels."""
        if len(self.mag_history) < 30:
            return {'status': 'Insufficient data'}
            
        vectors = np.array(self.mag_history)
        total = np.sqrt(vectors[:, 0]**2 + vectors[:, 1]**2 + vectors[:, 2]**2)
        radiations = np.array(list(self.radiation_history))
        
        correlation = np.corrcoef(total, radiations)[0, 1]
        
        return {
            'magnetization_radiation_correlation': float(correlation),
            'interpretation': self._interpret_correlation(correlation)
        }
        
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret magneto-radiative correlation."""
        if abs(corr) < 0.3:
            return "No strong correlation between magnetic field and radiation"
        elif corr > 0:
            return "Positive correlation: Higher radiation with stronger magnetic field"
        else:
            return "Negative correlation: Higher radiation with weaker magnetic field"


# ============================================================================
# ATMOSPHERIC STABILITY & PHYSICS
# ============================================================================

class AtmosphericPhysicsAnalyzer:
    """
    Comprehensive atmospheric physics study including pressure, temperature,
    radiation, UV, stability index, and sensor drift.
    """
    
    def __init__(self):
        self.data_history = {
            'altitude': deque(maxlen=500),
            'pressure': deque(maxlen=500),
            'temperature': deque(maxlen=500),
            'humidity': deque(maxlen=500),
            'radiation': deque(maxlen=500),
            'uv_index': deque(maxlen=500),
            'wind_speed': deque(maxlen=500),
            'timestamp': deque(maxlen=500)
        }
        
    def add_reading(self, **kwargs):
        """Add atmospheric reading."""
        for key, value in kwargs.items():
            if key in self.data_history and value is not None:
                self.data_history[key].append(value)
                
    def calculate_stability_index(self) -> Dict:
        """Calculate atmospheric stability index (PBL height proxy)."""
        if len(self.data_history['temperature']) < 30:
            return {'stability': 'Unknown', 'index': 0}
            
        temps = np.array(list(self.data_history['temperature']))
        alts = np.array(list(self.data_history['altitude']))
        
        # Calculate lapse rate
        if len(alts) > 1:
            lapse_rate = np.polyfit(alts, temps, 1)[0] * 100  # °C per 100m
            
            # Determine stability class
            if lapse_rate < -1.5:
                stability = AtmosphericStability.VERY_UNSTABLE
                index = 5
            elif lapse_rate < -0.5:
                stability = AtmosphericStability.UNSTABLE
                index = 4
            elif lapse_rate < 0.5:
                stability = AtmosphericStability.NEUTRAL
                index = 3
            elif lapse_rate < 2.0:
                stability = AtmosphericStability.STABLE
                index = 2
            else:
                stability = AtmosphericStability.VERY_STABLE
                index = 1
                
            return {
                'stability': stability.name,
                'index': index,
                'lapse_rate': lapse_rate,
                'interpretation': self._interpret_stability(stability, lapse_rate)
            }
            
        return {'stability': 'Unknown'}
        
    def _interpret_stability(self, stability: AtmosphericStability, lapse: float) -> str:
        """Interpret stability conditions."""
        if stability == AtmosphericStability.VERY_UNSTABLE:
            return "Strong vertical mixing, good pollutant dispersion"
        elif stability == AtmosphericStability.UNSTABLE:
            return "Moderate mixing, reasonable dispersion"
        elif stability == AtmosphericStability.NEUTRAL:
            return "Neutral conditions, average dispersion"
        elif stability == AtmosphericStability.STABLE:
            return "Limited mixing, pollutants may accumulate"
        else:
            return f"Strong inversion ({lapse:.1f}°C/100m), poor dispersion expected"
            
    def calculate_density_altitude(self, pressure: float, temperature: float, 
                                  humidity: float) -> float:
        """Calculate density altitude (pressure altitude corrected for temperature)."""
        # Standard atmosphere pressure at sea level
        p0 = 1013.25  # hPa
        
        # Pressure altitude
        alt = 145366.45 * (1 - (pressure / p0) ** 0.190284)
        
        # Temperature correction
        isa_temp = 15 - (alt / 1000) * 2  # ISA temperature
        temp_diff = temperature - isa_temp
        
        # Density altitude correction (~120ft per degree deviation)
        density_alt = alt + (temp_diff * 120)
        
        return density_alt
        
    def calculate_atmospheric_transparency(self) -> Dict:
        """Calculate atmospheric transparency from UV and solar data."""
        if len(self.data_history['uv_index']) < 10:
            return {'transparency': 'Unknown'}
            
        uv = np.array(list(self.data_history['uv_index']))
        alt = np.array(list(self.data_history['altitude']))
        
        # Higher UV at high altitude = better transparency
        avg_uv = np.mean(uv)
        avg_alt = np.mean(alt)
        
        # UV increases roughly 10% per 1000m
        expected_uv = 5 * (1 + avg_alt / 10000)  # Baseline 5 at sea level
        actual_ratio = avg_uv / expected_uv if expected_uv > 0 else 0
        
        if actual_ratio > 0.8:
            transparency = 'Good'
        elif actual_ratio > 0.5:
            transparency = 'Moderate'
        else:
            transparency = 'Poor'
            
        return {
            'transparency': transparency,
            'transparency_ratio': actual_ratio,
            'average_uv': float(avg_uv),
            'altitude_factor': float(1 + avg_alt / 10000)
        }
        
    def predict_anomalies(self) -> List[Dict]:
        """Predict environmental anomalies using trend analysis."""
        if len(self.data_history['radiation']) < 50:
            return []
            
        anomalies = []
        
        # Radiation spike prediction
        rad = np.array(list(self.data_history['radiation']))
        rad_mean = np.mean(rad)
        rad_std = np.std(rad)
        
        if len(rad) > 5:
            rad_trend = rad[-5:].mean() - rad[-10:-5].mean()
            if rad_trend > rad_std * 2:
                anomalies.append({
                    'type': 'Radiation Spike Imminent',
                    'confidence': 0.7,
                    'current_trend': rad_trend
                })
                
        # VOC spike prediction
        if 'voc' in self.data_history and len(self.data_history['voc']) > 20:
            voc = np.array(list(self.data_history['voc']))
            if len(voc) > 5:
                voc_trend = voc[-5:].mean() - voc[-10:-5].mean()
                if voc_trend > 100:
                    anomalies.append({
                        'type': 'VOC Spike Approaching',
                        'confidence': 0.6,
                        'current_trend': voc_trend
                    })
                    
        return anomalies
        
    def get_physics_report(self) -> Dict:
        """Generate comprehensive atmospheric physics report."""
        return {
            'stability': self.calculate_stability_index(),
            'transparency': self.calculate_atmospheric_transparency(),
            'predictions': self.predict_anomalies(),
            'pressure_gradient': self._calculate_pressure_gradient(),
            'thermal_gradient': self._calculate_thermal_gradient()
        }
        
    def _calculate_pressure_gradient(self) -> float:
        """Calculate pressure gradient."""
        if len(self.data_history['pressure']) < 20:
            return 0.0
        pressure = np.array(list(self.data_history['pressure']))
        altitude = np.array(list(self.data_history['altitude']))
        return float(np.polyfit(altitude, pressure, 1)[0])
        
    def _calculate_thermal_gradient(self) -> float:
        """Calculate thermal gradient."""
        if len(self.data_history['temperature']) < 20:
            return 0.0
        temp = np.array(list(self.data_history['temperature']))
        altitude = np.array(list(self.data_history['altitude']))
        return float(np.polyfit(altitude, temp, 1)[0] * 100)


# ============================================================================
# COMMUNICATIONS & LOCALIZATION
# ============================================================================

class CommunicationsAnalyzer:
    """
    Beacon & RSSI-based localization, frequency-agile telemetry analysis,
    and store-and-forward data relay monitoring.
    """
    
    def __init__(self):
        self.rssi_history = deque(maxlen=100)
        self.snr_history = deque(maxlen=100)
        self.packet_loss_history = deque(maxlen=100)
        self.timestamp_history = deque(maxlen=100)
        self.frequency_history = deque(maxlen=100)
        
    def add_reading(self, timestamp: float, rssi: float, snr: float,
                   packet_loss: float, frequency: float):
        """Add communication metrics."""
        self.rssi_history.append(rssi)
        self.snr_history.append(snr)
        self.packet_loss_history.append(packet_loss)
        self.timestamp_history.append(timestamp)
        self.frequency_history.append(frequency)
        
    def estimate_position_from_rssi(self, known_beacons: Dict[str, Tuple[float, float, int]]) -> Optional[Tuple[float, float]]:
        """
        Estimate position from RSSI and known beacon locations.
        
        Args:
            known_beacons: Dict of beacon_id -> (lat, lon, tx_power_dBm)
        """
        if len(self.rssi_history) < 3:
            return None
            
        avg_rssi = np.mean(list(self.rssi_history))
        
        # Simple centroid-based estimation
        # In real implementation, use trilateration
        lat_center = np.mean([b[0] for b in known_beacons.values()])
        lon_center = np.mean([b[1] for b in known_beacons.values()])
        
        # Adjust based on RSSI (higher RSSI = closer)
        if avg_rssi > -50:
            confidence = 'High'
        elif avg_rssi > -70:
            confidence = 'Medium'
        else:
            confidence = 'Low'
            
        return (lat_center, lon_center, confidence)
        
    def analyze_frequency_agility(self) -> Dict:
        """Analyze frequency hopping effectiveness."""
        if len(self.frequency_history) < 20:
            return {'status': 'Insufficient data'}
            
        frequencies = np.array(list(self.frequency_history))
        rssi = np.array(list(self.rssi_history))
        
        # Check for optimal frequency selection
        freq_rssi_corr = {}
        for freq in np.unique(frequencies):
            mask = frequencies == freq
            avg_rssi = np.mean(rssi[mask])
            freq_rssi_corr[float(freq)] = float(avg_rssi)
            
        best_freq = max(freq_rssi_corr, key=freq_rssi_corr.get)
        
        return {
            'optimal_frequency': best_freq,
            'frequency_rssi_map': freq_rssi_corr,
            'hop_success_rate': 1.0 - np.mean(list(self.packet_loss_history)),
            'average_snr': float(np.mean(list(self.snr_history)))
        }
        
    def detect_link_degradation(self) -> Dict:
        """Detect communication link degradation."""
        if len(self.rssi_history) < 20:
            return {'status': 'OK', 'degraded': False}
            
        rssi = np.array(list(self.rssi_history))
        
        # Check for trends
        recent_mean = np.mean(rssi[-10:])
        older_mean = np.mean(rssi[-20:-10])
        trend = recent_mean - older_mean
        
        degraded = trend < -5 or recent_mean < -80
        
        return {
            'current_rssi': float(rssi[-1]),
            'average_rssi': float(recent_mean),
            'trend_dbm_per_minute': float(trend * 6),  # Extrapolate
            'degraded': degraded,
            'status': 'DEGRADED' if degraded else 'OK',
            'recommendation': self._get_link_recommendation(degraded, recent_mean)
        }
        
    def _get_link_recommendation(self, degraded: bool, rssi: float) -> str:
        """Get link maintenance recommendation."""
        if degraded:
            if rssi < -90:
                return "Critical: Consider changing position or using backup link"
            return "Warning: Monitor closely, prepare for frequency change"
        return "Link healthy"


# ============================================================================
# POWER SYSTEM HEALTH MONITORING
# ============================================================================

class PowerHealthMonitor:
    """
    Comprehensive power system health monitoring including battery,
    power consumption, and thermal management.
    """
    
    def __init__(self):
        self.voltage_history = deque(maxlen=200)
        self.current_history = deque(maxlen=200)
        self.temperature_history = deque(maxlen=200)
        self.timestamp_history = deque(maxlen=200)
        
        # Battery parameters (2S Li-ion)
        self.nominal_voltage = 7.4  # V
        self.max_voltage = 8.4  # V (fully charged)
        self.min_voltage = 6.0  # V (protection threshold)
        self.capacity_mah = 1000  # mAh
        
    def add_reading(self, timestamp: float, voltage: float, current: float, temperature: float):
        """Add power system reading."""
        self.voltage_history.append(voltage)
        self.current_history.append(current)
        self.temperature_history.append(temperature)
        self.timestamp_history.append(timestamp)
        
    def estimate_remaining_capacity(self) -> float:
        """Estimate remaining battery capacity."""
        if len(self.current_history) < 10:
            return 0.0
            
        current = np.array(list(self.current_history))
        timestamps = np.array(list(self.timestamp_history))
        
        # Calculate average current draw
        avg_current = np.mean(current[-50:])
        
        # Integrate over time to estimate usage
        if len(timestamps) > 1:
            dt = timestamps[-1] - timestamps[0]  # seconds
            if dt > 0:
                usage_mah = (avg_current * dt) / 3600  # mAh
                remaining = self.capacity_mah - usage_mah
                return max(0, remaining)
                
        return 50.0  # Default estimate
        
    def calculate_health_status(self) -> Dict:
        """Calculate comprehensive power health status."""
        if not self.voltage_history:
            return {'status': 'No data'}
            
        voltage = np.array(list(self.voltage_history))
        current = np.array(list(self.current_history))
        temp = np.array(list(self.temperature_history))
        
        # Voltage-based estimate
        cell_voltage = voltage[-1] / 2  # 2S pack
        voltage_percent = (cell_voltage - self.min_voltage / 2) / ((self.max_voltage - self.min_voltage) / 2) * 100
        voltage_percent = np.clip(voltage_percent, 0, 100)
        
        # Health flags
        low_voltage = voltage[-1] < self.min_voltage + 0.5
        high_temp = np.mean(temp[-10:]) > 45  # >45°C
        high_current = np.mean(current[-10:]) > 800  # >800mA average
        
        # Status determination
        if low_voltage or high_temp:
            status = 'CRITICAL'
        elif high_current:
            status = 'WARNING'
        else:
            status = 'OK'
            
        return {
            'status': status,
            'battery_percent': float(voltage_percent),
            'current_draw_ma': float(np.mean(current[-10:])),
            'temperature_c': float(np.mean(temp[-10:])),
            'estimated_runtime_min': self._estimate_runtime(),
            'flags': {
                'low_voltage': low_voltage,
                'high_temperature': high_temp,
                'high_current': high_current
            }
        }
        
    def _estimate_runtime(self) -> float:
        """Estimate remaining runtime in minutes."""
        avg_current = np.mean(list(self.current_history)[-20:])
        if avg_current > 0:
            remaining_ah = self.estimate_remaining_capacity() / 1000
            return (remaining_ah / (avg_current / 1000)) * 60
        return 0.0
        
    def detect_power_anomalies(self) -> List[Dict]:
        """Detect power system anomalies."""
        if len(self.voltage_history) < 30:
            return []
            
        voltage = np.array(list(self.voltage_history))
        
        anomalies = []
        
        # Sudden voltage drop
        diff = np.diff(voltage)
        for i, d in enumerate(diff):
            if d < -0.2:  # >0.2V drop
                anomalies.append({
                    'type': 'Sudden Voltage Drop',
                    'timestamp': list(self.timestamp_history)[i + 1],
                    'drop_v': d
                })
                
        return anomalies


# ============================================================================
# UNIFIED ENVIRONMENTAL ANALYSIS SYSTEM
# ============================================================================

class CompleteEnvironmentalAnalyzer:
    """
    Complete environmental analysis system integrating all analyzers.
    Provides unified interface for all sensor data and analysis.
    """
    
    def __init__(self):
        # Initialize all analyzers
        self.boundary_detector = BoundaryLayerDetector()
        self.aqi_estimator = AirQualityEstimator()
        self.radiation_analyzer = RadiationAnalyzer()
        self.magnetic_analyzer = MagneticAnalyzer()
        self.atmospheric_analyzer = AtmosphericPhysicsAnalyzer()
        self.comms_analyzer = CommunicationsAnalyzer()
        self.power_monitor = PowerHealthMonitor()
        
        # Event history
        self.events: List[Dict] = []
        self.alert_history: List[Dict] = []
        
    def process_sensor_data(self, data: Dict) -> Dict:
        """
        Process all sensor data and generate comprehensive analysis.
        
        Args:
            data: Dictionary with all sensor readings
            
        Returns:
            Comprehensive analysis results
        """
        timestamp = data.get('timestamp', time.time())
        
        # Update all analyzers
        # Atmospheric data
        if 'altitude' in data and 'temperature' in data:
            self.boundary_detector.add_reading(
                data['altitude'], data['temperature'],
                data.get('pressure', 1013), data.get('humidity', 50),
                data.get('voc', 0)
            )
            
            self.atmospheric_analyzer.add_reading(
                timestamp=timestamp,
                altitude=data['altitude'],
                pressure=data.get('pressure', 1013),
                temperature=data['temperature'],
                humidity=data.get('humidity', 50),
                radiation=data.get('radiation', 0),
                uv_index=data.get('uv_index', 0)
            )
            
        # Air quality
        if 'voc' in data or 'co2' in data:
            self.aqi_estimator.add_reading(
                timestamp, data.get('voc', 0), data.get('co2', 400),
                data.get('nh3', 0), data.get('co', 0), data.get('no2', 0),
                data.get('temperature', 20), data.get('humidity', 50)
            )
            
        # Radiation
        if 'radiation' in data:
            self.radiation_analyzer.add_reading(
                timestamp, data.get('altitude', 0), data['radiation'],
                data.get('mag_x', 0), data.get('mag_y', 0), data.get('mag_z', 0),
                data.get('uv_index', 0), data.get('lat', 0), data.get('lon', 0)
            )
            
        # Magnetic
        if 'mag_x' in data:
            self.magnetic_analyzer.add_reading(
                timestamp, data['mag_x'], data['mag_y'], data['mag_z'],
                data.get('altitude', 0), data.get('radiation', 0)
            )
            
        # Communications
        if 'rssi' in data:
            self.comms_analyzer.add_reading(
                timestamp, data['rssi'], data.get('snr', 0),
                data.get('packet_loss', 0), data.get('frequency', 433)
            )
            
        # Power
        if 'battery_voltage' in data:
            self.power_monitor.add_reading(
                timestamp, data['battery_voltage'], data.get('battery_current', 0),
                data.get('battery_temp', 25)
            )
            
        # Generate comprehensive report
        return self.generate_comprehensive_report()
        
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive environmental report."""
        return {
            'timestamp': time.time(),
            'boundary_layer': self.boundary_detector.get_inversion_report(),
            'air_quality': self.aqi_estimator.get_current_aqi(),
            'radiation': self.radiation_analyzer.get_radiation_report(),
            'magnetic': {
                'heading': self.magnetic_analyzer.calculate_heading(),
                'field_vector': self.magnetic_analyzer.calculate_field_vector(),
                'anomalies': self.magnetic_analyzer.detect_magnetic_anomalies(),
                'radiation_correlation': self.magnetic_analyzer.correlate_with_radiation()
            },
            'atmospheric_physics': self.atmospheric_analyzer.get_physics_report(),
            'communications': {
                'link_status': self.comms_analyzer.detect_link_degradation(),
                'frequency_analysis': self.comms_analyzer.analyze_frequency_agility()
            },
            'power_health': self.power_monitor.calculate_health_status(),
            'anomaly_predictions': self.atmospheric_analyzer.predict_anomalies()
        }
        
    def check_critical_alerts(self) -> List[Dict]:
        """Check for critical conditions requiring alerts."""
        alerts = []
        
        report = self.generate_comprehensive_report()
        
        # Radiation alert
        if report['radiation']['current_radiation'] > 2.5:
            alerts.append({
                'level': 'CRITICAL',
                'message': f"High radiation: {report['radiation']['current_radiation']:.2f} µSv/h",
                'action': 'Wear protective equipment'
            })
            
        # Air quality alert
        if report['air_quality']['aqi'] > 150:
            alerts.append({
                'level': 'WARNING',
                'message': f"Unhealthy AQI: {report['air_quality']['aqi']}",
                'action': report['air_quality']['health_advice']
            })
            
        # Inversion warning
        if report['boundary_layer']['pollution_trapping']:
            alerts.append({
                'level': 'INFO',
                'message': "Temperature inversion detected",
                'action': "Pollutants may accumulate"
            })
            
        # Power alert
        if report['power_health']['status'] == 'CRITICAL':
            alerts.append({
                'level': 'CRITICAL',
                'message': "Power system critical",
                'action': "Conserve power immediately"
            })
            
        self.alert_history.extend(alerts)
        return alerts


def create_complete_analyzer() -> CompleteEnvironmentalAnalyzer:
    """Factory function to create complete environmental analyzer."""
    return CompleteEnvironmentalAnalyzer()


if __name__ == "__main__":
    print("=" * 70)
    print("Air2 CanSat - Complete Environmental Analysis System")
    print("=" * 70)
    
    analyzer = create_complete_analyzer()
    
    # Simulate comprehensive sensor data
    print("\nSimulating sensor data...")
    
    for i in range(100):
        data = {
            'timestamp': i * 2,
            'altitude': 1000 - i * 10,
            'temperature': 20 - i * 0.015,
            'pressure': 1013 - i * 0.01,
            'humidity': 60 + np.sin(i * 0.1) * 10,
            'voc': 200 + np.random.normal(100, 30),
            'co2': 400 + np.random.normal(50, 10),
            'nh3': 5 + np.random.normal(0, 2),
            'co': 2 + np.random.normal(0, 1),
            'no2': 10 + np.random.normal(0, 5),
            'radiation': 0.5 + 0.002 * i + np.random.normal(0, 0.1),
            'uv_index': 5 + np.random.normal(0, 1),
            'mag_x': 25 + np.random.normal(0, 2),
            'mag_y': -10 + np.random.normal(0, 2),
            'mag_z': 35 + np.random.normal(0, 2),
            'lat': 37.7749 + i * 0.00001,
            'lon': -122.4194 + i * 0.00001,
            'rssi': -65 + np.random.normal(0, 5),
            'snr': 15 + np.random.normal(0, 3),
            'packet_loss': 0.02,
            'battery_voltage': 7.4 - i * 0.005,
            'battery_current': 150 + np.random.normal(0, 30)
        }
        
        if i % 20 == 0:
            report = analyzer.process_sensor_data(data)
            print(f"\n--- Analysis at t={i*2}s ---")
            print(f"AQI: {report['air_quality']['aqi']} ({report['air_quality']['category']})")
            print(f"Radiation: {report['radiation']['current_radiation']:.3f} µSv/h")
            print(f"Heading: {report['magnetic']['heading']:.1f}°")
            print(f"Stability: {report['atmospheric_physics']['stability']['stability']}")
            
    print("\n" + "=" * 70)
    print("Environmental Analysis System Ready")
    print("=" * 70)