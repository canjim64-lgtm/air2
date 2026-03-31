"""
Hardware-Specific Sensor Fusion and Signal Processing
Implements non-AI signal processing for CanSat sensors:
- Power rail monitoring with ESR calculation
- Differential barometry with Kalman filter
- Geiger counter dead-time compensation
- Packet integrity checksums
- Audio proximity varimeter
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import struct
import math


# ============================================================================
# 1. REAL-TIME POWER RAIL MONITORING
# ============================================================================

class PowerRailMonitor:
    """
    Monitors 3.3V power rail using ESP32 ADC.
    Calculates ESR (Equivalent Series Resistance) and detects brownouts.
    """
    
    def __init__(self):
        self.voltage_history = deque(maxlen=100)
        self.current_history = deque(maxlen=100)
        self.timestamp_history = deque(maxlen=100)
        
        # Battery parameters (2S Li-ion)
        self.nominal_voltage = 7.4
        self.max_voltage = 8.4
        self.min_voltage = 6.0
        
        # ESR thresholds
        self.esr_warning_threshold = 0.05  # 50mΩ
        self.esr_critical_threshold = 0.1   # 100mΩ
        
        # Brownout detection
        self.brownout_threshold = 3.0  # V
        self.transmission_voltage_drop = 0.15  # Expected drop during TX
        
    def add_reading(self, timestamp: float, battery_voltage: float, 
                   adc_voltage: float = None, load_current: float = 0):
        """
        Add power reading.
        
        Args:
            timestamp: Reading timestamp
            battery_voltage: 2S battery voltage
            adc_voltage: ESP32 ADC reading (if available)
            load_current: Current draw in mA
        """
        self.timestamp_history.append(timestamp)
        self.voltage_history.append(battery_voltage)
        self.current_history.append(load_current)
        
    def calculate_esr(self) -> Dict:
        """
        Calculate Equivalent Series Resistance of battery.
        
        Returns:
            ESR value and health status
        """
        if len(self.voltage_history) < 10:
            return {'status': 'Insufficient data', 'esr_ohm': 0}
            
        voltages = np.array(list(self.voltage_history))
        currents = np.array(list(self.current_history))
        
        # Detect voltage sag during high current (TX burst)
        # Find periods with high current
        high_current_indices = np.where(currents > 100)[0]
        
        if len(high_current_indices) > 5:
            # Calculate delta V and delta I
            high_voltages = voltages[high_current_indices]
            low_voltages = voltages[np.where(currents < 50)[0]]
            
            if len(low_voltages) > 0 and len(high_voltages) > 0:
                avg_high = np.mean(high_voltages[-10:])
                avg_low = np.mean(low_voltages[-10:])
                
                delta_v = avg_low - avg_high
                delta_i = np.mean(currents[high_current_indices[-10:]]) / 1000  # Convert to A
                
                if delta_i > 0:
                    esr = delta_v / delta_i
                else:
                    esr = 0
            else:
                esr = 0
        else:
            # Use voltage variance method
            voltage_std = np.std(voltages[-20:])
            current_mean = np.mean(currents[-20:])
            
            if current_mean > 0:
                esr = voltage_std / (current_mean / 1000)
            else:
                esr = 0
                
        # Determine health
        if esr > self.esr_critical_threshold:
            health = 'CRITICAL'
        elif esr > self.esr_warning_threshold:
            health = 'WARNING'
        else:
            health = 'GOOD'
            
        return {
            'status': health,
            'esr_ohm': float(esr),
            'esr_mohm': float(esr * 1000),
            'battery_voltage': float(voltages[-1]),
            'voltage_sag': float(delta_v) if 'delta_v' in dir() else 0
        }
        
    def detect_brownout(self) -> Optional[Dict]:
        """Detect brownout conditions during radio transmission."""
        if len(self.voltage_history) < 20:
            return None
            
        voltages = np.array(list(self.voltage_history))
        currents = np.array(list(self.current_history))
        timestamps = np.array(list(self.timestamp_history))
        
        # Look for voltage dips during high current (TX)
        for i in range(len(voltages) - 1):
            if currents[i] > 200:  # TX current
                if voltages[i] < self.brownout_threshold:
                    return {
                        'timestamp': float(timestamps[i]),
                        'voltage': float(voltages[i]),
                        'current': float(currents[i]),
                        'type': 'LOW_POWER_BROWNOUT',
                        'severity': 'CRITICAL'
                    }
                    
                # Check for sudden drop
                if i > 0 and voltages[i] < voltages[i-1] - 0.1:
                    return {
                        'timestamp': float(timestamps[i]),
                        'voltage_drop': float(voltages[i-1] - voltages[i]),
                        'type': 'VOLTAGE_SPIKE_DROP',
                        'severity': 'WARNING'
                    }
                    
        return None
        
    def get_power_health_report(self) -> Dict:
        """Get comprehensive power health report."""
        esr_data = self.calculate_esr()
        brownout = self.detect_brownout()
        
        if len(self.voltage_history) > 0:
            voltages = np.array(list(self.voltage_history))
            
            # Battery percentage (rough estimate)
            cell_voltage = voltages[-1] / 2
            percentage = ((cell_voltage - 3.0) / (4.2 - 3.0)) * 100
            percentage = np.clip(percentage, 0, 100)
        else:
            percentage = 0
            
        return {
            'esr_analysis': esr_data,
            'battery_percent': float(percentage),
            'brownout_detected': brownout is not None,
            'brownout_event': brownout,
            'recommendation': self._get_recommendation(esr_data, brownout)
        }
        
    def _get_recommendation(self, esr_data: Dict, brownout: Optional[Dict]) -> str:
        """Get power recommendation."""
        if brownout and brownout.get('severity') == 'CRITICAL':
            return "CRITICAL: Low power brownout detected! Reduce transmission power immediately."
        elif esr_data['status'] == 'CRITICAL':
            return "Battery ESR is critical. Consider replacing battery."
        elif esr_data['status'] == 'WARNING':
            return "Battery ESR elevated. Monitor closely during transmissions."
        else:
            return "Power system healthy."


# ============================================================================
# 2. DIFFERENTIAL BAROMETRY (KALMAN FILTER)
# ============================================================================

class DifferentialBarometer:
    """
    Kalman Filter fusion of BMP388 and BME688 for sub-10cm altitude resolution.
    BMP388 = high precision (low noise)
    BME688 = stability (DC bias correction)
    """
    
    def __init__(self):
        # Kalman state
        self.altitude = 0.0
        self.variance = 1.0  # Uncertainty
        
        # Process noise (how much we expect altitude to change)
        self.process_noise = 0.1
        
        # Measurement noise (from sensors)
        self.bmp388_noise = 0.5   # High precision
        self.bme688_noise = 1.0    # Stability
        
        # Sensor data history
        self.altitude_history = deque(maxlen=100)
        self.pressure_history = deque(maxlen=100)
        self.timestamp_history = deque(maxlen=100)
        
    def sea_level_pressure(self, pressure: float, altitude: float, temperature: float) -> float:
        """Convert pressure to sea level."""
        return pressure * math.pow(1 - (0.0065 * altitude) / (temperature + 0.0065 * altitude + 273.15), -5.257)
        
    def pressure_to_altitude(self, pressure: float, sea_level_pressure: float = 1013.25) -> float:
        """Convert pressure to altitude using barometric formula."""
        return 44330 * (1 - math.pow(pressure / sea_level_pressure, 0.1903))
        
    def kalman_update(self, measurement: float, measurement_noise: float) -> float:
        """
        Single Kalman filter update step.
        
        Args:
            measurement: Altitude measurement
            measurement_noise: Sensor noise level
            
        Returns:
            Filtered altitude
        """
        # Prediction (assume no change in state)
        predicted_altitude = self.altitude
        predicted_variance = self.variance + self.process_noise
        
        # Update
        kalman_gain = predicted_variance / (predicted_variance + measurement_noise)
        self.altitude = predicted_altitude + kalman_gain * (measurement - predicted_altitude)
        self.variance = (1 - kalman_gain) * predicted_variance
        
        return self.altitude
        
    def fuse_sensors(self, bmp388_pressure: float, bme688_pressure: float,
                    bme688_temperature: float, reference_altitude: float = None) -> Dict:
        """
        Fuse two barometer readings using Kalman filter.
        
        Args:
            bmp388_pressure: BMP388 pressure in hPa
            bme688_pressure: BME688 pressure in hPa
            bme688_temperature: BME688 temperature for sea level calculation
            reference_altitude: Known reference altitude (if available)
            
        Returns:
            Fused altitude and confidence metrics
        """
        # Calculate altitudes from pressures
        alt_bmp = self.pressure_to_altitude(bmp388_pressure)
        alt_bme = self.pressure_to_altitude(bme688_pressure, 
                                           self.sea_level_pressure(bme688_pressure, 0, bme688_temperature))
        
        # Kalman fusion with different noise levels
        # Use BMP388 for high-frequency, BME688 for DC bias
        fused_altitude = self.kalman_update(alt_bmp, self.bmp388_noise)
        
        # Also update with BME688 periodically (for drift correction)
        if len(self.altitude_history) % 5 == 0:
            fused_altitude = self.kalman_update(alt_bme, self.bme688_noise)
            
        # Apply reference correction if available
        if reference_altitude is not None:
            error = reference_altitude - fused_altitude
            self.altitude += error * 0.1  # Gentle correction
            
        # Store history
        self.altitude_history.append(fused_altitude)
        self.pressure_history.append((bmp388_pressure, bme688_pressure))
        
        # Calculate jitter (noise level)
        if len(self.altitude_history) > 10:
            jitter = np.std(list(self.altitude_history)[-10:])
        else:
            jitter = 0
            
        return {
            'fused_altitude': float(fused_altitude),
            'bmp388_altitude': float(alt_bmp),
            'bme688_altitude': float(alt_bme),
            'jitter_cm': float(jitter * 100),
            'confidence': max(0, min(1, 1 - jitter))
        }
        
    def get_altitude_resolution(self) -> str:
        """Get current altitude resolution classification."""
        if len(self.altitude_history) < 10:
            return 'Unknown'
            
        jitter = np.std(list(self.altitude_history)[-10:]) * 100  # cm
        
        if jitter < 5:
            return f'Excellent (<5cm, jitter={jitter:.1f}cm)'
        elif jitter < 10:
            return f'Good (<10cm, jitter={jitter:.1f}cm)'
        elif jitter < 20:
            return f'Acceptable (<20cm, jitter={jitter:.1f}cm)'
        else:
            return f'Poor (>20cm, jitter={jitter:.1f}cm)'


# ============================================================================
# 3. VOC BASELINE DRIFT CORRECTION (PID-Style)
# ============================================================================

class VOCBaselineCorrector:
    """
    PID-style feedback loop for VOC drift correction.
    Tracks clean air baseline and subtracts thermal drift.
    """
    
    def __init__(self):
        # PID parameters
        self.kp = 0.5  # Proportional gain
        self.ki = 0.1  # Integral gain
        self.kd = 0.2  # Derivative gain
        
        # State
        self.baseline_voc = 0.0
        self.baseline_temp = 0.0
        self.integral = 0.0
        self.last_error = 0.0
        
        # History
        self.voc_history = deque(maxlen=200)
        self.temp_history = deque(maxlen=200)
        self.timestamp_history = deque(maxlen=200)
        
        # Drift model coefficients (temperature effect on VOC)
        self.drift_coefficient = 0.02  # VOC change per °C
        
    def set_clean_air_baseline(self, voc: float, temperature: float):
        """Set initial clean air baseline."""
        self.baseline_voc = voc
        self.baseline_temp = temperature
        self.integral = 0.0
        self.last_error = 0.0
        
    def add_reading(self, timestamp: float, voc_raw: float, temperature: float):
        """Add sensor reading."""
        self.voc_history.append(voc_raw)
        self.temp_history.append(temperature)
        self.timestamp_history.append(timestamp)
        
    def correct_voc(self, voc_raw: float, temperature: float) -> float:
        """
        Apply PID correction to VOC reading.
        
        Args:
            voc_raw: Raw VOC reading
            temperature: Current temperature
            
        Returns:
            Corrected VOC reading
        """
        # Calculate expected drift based on temperature change
        temp_delta = temperature - self.baseline_temp
        expected_drift = temp_delta * self.drift_coefficient * self.baseline_voc
        
        # Calculate error (deviation from baseline + expected drift)
        error = (voc_raw - self.baseline_voc) - expected_drift
        
        # PID controller
        self.integral += error
        derivative = error - self.last_error
        
        # PID output
        correction = self.kp * error + self.ki * self.integral + self.kd * derivative
        
        self.last_error = error
        
        # Apply correction
        corrected_voc = voc_raw - correction
        
        return max(0, corrected_voc)
        
    def auto_recalibrate_if_clean(self, window_size: int = 50) -> bool:
        """
        Auto-recalibrate baseline if conditions suggest clean air.
        
        Returns:
            True if recalibration occurred
        """
        if len(self.voc_history) < window_size:
            return False
            
        recent_vocs = list(self.voc_history)[-window_size:]
        recent_temps = list(self.temp_history)[-window_size:]
        
        # Check if variance is low (stable readings = likely clean air)
        voc_std = np.std(recent_vocs)
        temp_std = np.std(recent_temps)
        
        # Clean air conditions: low variance, temperature stable
        if voc_std < 10 and temp_std < 1:
            new_baseline = np.mean(recent_vocs)
            new_temp = np.mean(recent_temps)
            
            # Update baseline only if significantly different
            if abs(new_baseline - self.baseline_voc) > 20:
                self.baseline_voc = new_baseline
                self.baseline_temp = new_temp
                self.integral = 0.0
                return True
                
        return False
        
    def get_correction_report(self) -> Dict:
        """Get VOC correction status report."""
        if len(self.voc_history) < 10:
            return {'status': 'Insufficient data'}
            
        raw_voc = list(self.voc_history)[-1]
        temp = list(self.temp_history)[-1]
        corrected_voc = self.correct_voc(raw_voc, temp)
        
        return {
            'baseline_voc': self.baseline_voc,
            'baseline_temp': self.baseline_temp,
            'raw_voc': raw_voc,
            'corrected_voc': corrected_voc,
            'correction_applied': raw_voc - corrected_voc,
            'thermal_drift_expected': (temp - self.baseline_temp) * self.drift_coefficient * self.baseline_voc
        }


# ============================================================================
# 4. GEIGER COUNTER DEAD-TIME COMPENSATION
# ============================================================================

class GeigerDeadTimeCompensator:
    """
    Paralysable Model dead-time compensation for M4011 Geiger tube.
    Prevents under-reporting at high radiation levels.
    """
    
    # M4011 tube specifications
    DEAD_TIME_US = 190  # 190 microseconds dead time
    
    def __init__(self):
        self.count_history = deque(maxlen=100)
        self.timestamp_history = deque(maxlen=100)
        
        # True count rate (calculated)
        self.true_count_rate = 0.0
        
    def add_count(self, timestamp: float):
        """Add a Geiger click."""
        self.count_history.append(timestamp)
        self.timestamp_history.append(timestamp)
        
    def calculate_cpm(self, window_seconds: float = 60) -> float:
        """
        Calculate raw Counts Per Minute.
        
        Args:
            window_seconds: Time window for CPM calculation
            
        Returns:
            Raw CPM
        """
        if len(self.count_history) < 2:
            return 0.0
            
        timestamps = np.array(list(self.count_history))
        now = timestamps[-1]
        
        # Count clicks in window
        clicks_in_window = np.sum(timestamps >= now - window_seconds)
        
        # Convert to CPM
        cpm = (clicks_in_window / window_seconds) * 60
        
        return cpm
        
    def compensate_dead_time(self, measured_cpm: float) -> Dict:
        """
        Apply Paralysable Model dead-time compensation.
        
        The Paralysable Model formula:
        n = m * exp(m * τ)
        
        Where:
        - n = true count rate
        - m = measured count rate  
        - τ = dead time
        
        Args:
            measured_cpm: Raw measured CPM
            
        Returns:
            Compensated CPM and confidence metrics
        """
        dead_time_minutes = self.DEAD_TIME_US / 1_000_000 / 60  # Convert to minutes
        tau = dead_time_minutes
        
        # Paralysable model (iterative solution)
        # n = m * exp(m * τ)
        # We solve for n using Newton-Raphson
        
        m = measured_cpm
        n = m  # Initial guess
        
        # Newton-Raphson iteration
        for _ in range(20):
            # f(n) = n - m * exp(n * τ) = 0
            # f'(n) = 1 - m * τ * exp(n * τ)
            
            exp_term = math.exp(n * tau)
            f = n - m * exp_term
            f_prime = 1 - m * tau * exp_term
            
            if abs(f_prime) < 1e-10:
                break
                
            n_new = n - f / f_prime
            n = max(0, n_new)  # Count rate can't be negative
            
        self.true_count_rate = n
        
        # Calculate correction factor
        correction_factor = n / m if m > 0 else 1
        
        # Determine confidence (high correction = less confident)
        if correction_factor > 3:
            confidence = 'LOW'
        elif correction_factor > 1.5:
            confidence = 'MEDIUM'
        else:
            confidence = 'HIGH'
            
        return {
            'measured_cpm': measured_cpm,
            'true_cpm': n,
            'correction_factor': correction_factor,
            'dead_time_us': self.DEAD_TIME_US,
            'confidence': confidence,
            'interpretation': self._interpret_compensation(measured_cpm, n)
        }
        
    def _interpret_compensation(self, measured: float, true: float) -> str:
        """Interpret compensation results."""
        if true > measured * 2:
            return f"High radiation detected! True rate {true:.0f} CPM vs measured {measured:.0f} CPM"
        elif true > measured * 1.2:
            return f"Moderate correction: True rate {true:.0f} CPM (measured {measured:.0f} CPM)"
        else:
            return f"Minimal correction needed: True rate {true:.0f} CPM"
            
    def get_dose_rate(self, cpm: float, conversion_factor: float = 0.00812) -> Dict:
        """
        Convert CPM to dose rate in µSv/h.
        
        Args:
            cpm: CPM (dead-time compensated)
            conversion_factor: CPM to µSv/h factor for M4011 tube
            
        Returns:
            Dose rate and classification
        """
        dose_rate = cpm * conversion_factor
        
        # Classification
        if dose_rate < 0.1:
            classification = 'Background'
            advice = 'Normal background radiation levels'
        elif dose_rate < 1.0:
            classification = 'Elevated'
            advice = 'Slightly elevated - likely cosmic or natural variation'
        elif dose_rate < 2.5:
            classification = 'High'
            advice = 'Significant elevation - investigate source'
        else:
            classification = 'CRITICAL'
            advice = 'High radiation - notify team and wear protection'
            
        return {
            'dose_rate_usvh': dose_rate,
            'cpm': cpm,
            'classification': classification,
            'advice': advice
        }


# ============================================================================
# 5. ATMOSPHERIC LAPSE RATE CALCULATOR
# ============================================================================

class LapseRateCalculator:
    """
    Calculates atmospheric lapse rate and detects inversion layers.
    """
    
    def __init__(self):
        self.altitude_history = deque(maxlen=500)
        self.temperature_history = deque(maxlen=500)
        self.pressure_history = deque(maxlen=500)
        self.voc_history = deque(maxlen=500)
        self.timestamp_history = deque(maxlen=500)
        
        # Standard atmosphere lapse rate
        self.standard_lapse_rate = -0.0065  # °C/m
        
    def add_reading(self, timestamp: float, altitude: float, 
                   temperature: float, pressure: float, voc: float = 0):
        """Add atmospheric reading."""
        self.timestamp_history.append(timestamp)
        self.altitude_history.append(altitude)
        self.temperature_history.append(temperature)
        self.pressure_history.append(pressure)
        self.voc_history.append(voc)
        
    def calculate_lapse_rate(self, window_size: int = 50) -> Dict:
        """
        Calculate local adiabatic lapse rate.
        
        Returns:
            Lapse rate and inversion detection
        """
        if len(self.altitude_history) < window_size:
            return {'status': 'Insufficient data'}
            
        # Get data in altitude order (descending)
        data_points = list(zip(self.altitude_history, self.temperature_history))
        data_points.sort(key=lambda x: x[0], reverse=True)
        
        altitudes = np.array([d[0] for d in data_points[:window_size]])
        temperatures = np.array([d[1] for d in data_points[:window_size]])
        
        # Calculate lapse rate (linear regression)
        if len(altitudes) > 1 and np.std(altitudes) > 10:
            coeffs = np.polyfit(altitudes, temperatures, 1)
            lapse_rate = coeffs[0]  # °C per meter
            
            # Also calculate in °C per 100m (standard unit)
            lapse_rate_per_100m = lapse_rate * 100
        else:
            lapse_rate = 0
            lapse_rate_per_100m = 0
            
        # Determine atmospheric stability
        if lapse_rate_per_100m > 0:
            stability = 'INVERSION'
            stability_desc = 'Temperature increases with altitude - pollutants trapped'
        elif lapse_rate_per_100m < -1.5:
            stability = 'VERY_UNSTABLE'
            stability_desc = 'Strong vertical mixing - pollutants disperse'
        elif lapse_rate_per_100m < -0.5:
            stability = 'UNSTABLE'
            stability_desc = 'Moderate mixing'
        elif lapse_rate_per_100m > -0.5:
            stability = 'STABLE'
            stability_desc = 'Limited vertical mixing'
        else:
            stability = 'NEUTRAL'
            stability_desc = 'Neutral conditions'
            
        # Find inversion layers
        inversions = self._find_inversion_layers(altitudes, temperatures)
        
        return {
            'lapse_rate_cpm': lapse_rate,
            'lapse_rate_per_100m': lapse_rate_per_100m,
            'stability': stability,
            'stability_description': stability_desc,
            'standard_lapse_rate': self.standard_lapse_rate * 100,
            'deviation_from_standard': lapse_rate_per_100m - (self.standard_lapse_rate * 100),
            'inversion_layers': inversions,
            'pollution_trapping_risk': stability == 'INVERSION'
        }
        
    def _find_inversion_layers(self, altitudes: np.ndarray, 
                               temperatures: np.ndarray) -> List[Dict]:
        """Find temperature inversion layers."""
        inversions = []
        
        for i in range(len(altitudes) - 1):
            delta_alt = altitudes[i] - altitudes[i + 1]
            delta_temp = temperatures[i + 1] - temperatures[i]
            
            # Inversion: temp increases with altitude
            if delta_alt > 0 and delta_temp > 0.5:
                layer_thickness = altitudes[i] - altitudes[i + 1]
                temp_rise = delta_temp
                lapse = (delta_temp / delta_alt) * 100
                
                inversions.append({
                    'base_altitude': float(altitudes[i + 1]),
                    'top_altitude': float(altitudes[i]),
                    'thickness_m': float(layer_thickness),
                    'temperature_rise_c': float(temp_rise),
                    'lapse_rate_cper100m': float(lapse)
                })
                
        return inversions
        
    def get_meteorological_report(self) -> Dict:
        """Get comprehensive meteorological report."""
        lapse_data = self.calculate_lapse_rate()
        
        return {
            'lapse_rate_analysis': lapse_data,
            'inversion_alert': lapse_data['pollution_trapping_risk'],
            'recommendation': self._get_recommendation(lapse_data)
        }
        
    def _get_recommendation(self, lapse_data: Dict) -> str:
        """Get meteorological recommendation."""
        if lapse_data['pollution_trapping_risk']:
            return "INVERSION DETECTED: Pollutants may be trapped at inversion layer. VOCs/Gas readings may be elevated."
        elif lapse_data['stability'] == 'VERY_UNSTABLE':
            return "Strong vertical mixing - good pollutant dispersion"
        else:
            return "Atmospheric conditions within normal parameters"


# ============================================================================
# 6. PACKET-LEVEL INTEGRITY CHECKSUMS
# ============================================================================

class PacketIntegrityChecker:
    """
    CRC-16 and Fletcher checksum for HC-12 packet validation.
    """
    
    # CRC-16 Lookup table (CCITT)
    CRC16_TABLE = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
        0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
        0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
        0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
        0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
        0x48D4, 0x58F5, 0x6886, 0x78A7, 0x0880, 0x18A1, 0x28C2, 0x38E3,
        0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
        0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
        0xDBF0, 0xCBD1, 0xFBB2, 0xEB93, 0x9B74, 0x8B55, 0xBB36, 0xAB17,
        0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
        0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
        0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
        0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
        0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
        0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
        0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
        0x24E2, 0x34C3, 0x04A0, 0x1481, 0x6466, 0x7447, 0x5424, 0x4405,
        0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
        0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
        0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
        0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
        0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
        0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
        0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
        0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
    ]
    
    @staticmethod
    def crc16(data: bytes) -> int:
        """Calculate CRC-16 (CCITT) checksum."""
        crc = 0xFFFF
        for byte in data:
            crc = ((crc << 8) | (crc >> 8)) ^ PacketIntegrityChecker.CRC16_TABLE[(crc ^ byte) & 0xFF]
            crc &= 0xFFFF
        return crc
        
    @staticmethod
    def fletcher16(data: bytes) -> Tuple[int, int]:
        """Calculate Fletcher-16 checksum (two 8-bit sums)."""
        sum1 = 0
        sum2 = 0
        for byte in data:
            sum1 = (sum1 + byte) % 256
            sum2 = (sum2 + sum1) % 256
        return sum1, sum2
        
    @staticmethod
    def validate_packet(packet: bytes, expected_crc: int = None) -> Dict:
        """
        Validate packet integrity.
        
        Returns:
            Validation result with checksum info
        """
        if len(packet) < 2:
            return {'valid': False, 'reason': 'Packet too short'}
            
        # Calculate CRC-16
        calculated_crc = PacketIntegrityChecker.crc16(packet[:-2])
        
        # Calculate Fletcher
        sum1, sum2 = PacketIntegrityChecker.fletcher16(packet[:-2])
        
        # Extract embedded checksums
        embedded_crc = int.from_bytes(packet[-2:], 'big') if len(packet) >= 2 else 0
        
        # Compare
        crc_match = calculated_crc == embedded_crc if expected_crc is None else calculated_crc == expected_crc
        
        return {
            'valid': crc_match,
            'calculated_crc': hex(calculated_crc),
            'embedded_crc': hex(embedded_crc),
            'crc_match': crc_match,
            'fletcher_sum1': sum1,
            'fletcher_sum2': sum2,
            'packet_length': len(packet)
        }
        
    @staticmethod
    def create_packet(data: bytes, include_checksum: bool = True) -> bytes:
        """Create packet with embedded checksum."""
        if include_checksum:
            crc = PacketIntegrityChecker.crc16(data)
            return data + crc.to_bytes(2, 'big')
        return data


# ============================================================================
# 7. AUDIO PROXIMITY VARIMETER
# ============================================================================

class AudioProximityVarimeter:
    """
    Audio beep generator for ground proximity detection.
    Increases beep frequency as CanSat approaches ground.
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.distance_history = deque(maxlen=50)
        self.last_beep_time = 0
        self.enabled = True
        
    def add_distance(self, distance: float):
        """Add ToF distance reading."""
        self.distance_history.append(distance)
        
    def get_beep_params(self, current_time: float) -> Optional[Dict]:
        """
        Get beep parameters based on proximity.
        
        Args:
            current_time: Current timestamp
            
        Returns:
            Beep parameters or None if no beep should play
        """
        if not self.enabled or len(self.distance_history) < 2:
            return None
            
        distance = self.distance_history[-1]
        
        if distance > 10:  # Too far for proximity alert
            return None
            
        # Calculate beep frequency based on distance
        # At 4m: slow beep (1Hz)
        # At 0m: rapid beep (10Hz)
        
        if distance > 4:
            beep_frequency = 1.0  # Hz
        elif distance > 2:
            beep_frequency = 2.0  # Hz
        elif distance > 1:
            beep_frequency = 4.0  # Hz
        elif distance > 0.5:
            beep_frequency = 7.0  # Hz
        else:
            beep_frequency = 10.0  # Hz
            
        # Calculate frequency for beep
        beep_period = 1.0 / beep_frequency if beep_frequency > 0 else 999
        
        # Check if it's time for a beep
        if current_time - self.last_beep_time >= beep_period:
            self.last_beep_time = current_time
            
            # Beep duration (shorter as closer)
            duration_ms = max(20, int(100 - distance * 20))
            
            # Pitch (higher as closer)
            base_freq = 880  # A5
            pitch_factor = 1 + (4 - distance) / 4  # 1 at 4m, 2 at 0m
            frequency = int(base_freq * pitch_factor)
            
            return {
                'frequency': frequency,
                'duration_ms': duration_ms,
                'distance_m': distance,
                'beep_number': len(self.distance_history)
            }
            
        return None
        
    def generate_beep_samples(self, frequency: int, duration_ms: int) -> np.ndarray:
        """Generate audio samples for a beep."""
        n_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(n_samples) / self.sample_rate
        
        # Generate sine wave with envelope
        samples = np.sin(2 * np.pi * frequency * t)
        
        # Apply envelope (attack-decay)
        envelope = np.ones(n_samples)
        attack_samples = int(n_samples * 0.1)
        decay_samples = int(n_samples * 0.3)
        
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[-decay_samples:] = np.linspace(1, 0, decay_samples)
        
        samples *= envelope
        samples *= 0.5  # Volume control
        
        return samples.astype(np.float32)
        
    def enable(self):
        """Enable proximity alerts."""
        self.enabled = True
        
    def disable(self):
        """Disable proximity alerts."""
        self.enabled = False


# ============================================================================
# UNIFIED HARDWARE PROCESSOR
# ============================================================================

class HardwareSignalProcessor:
    """
    Complete hardware signal processing system.
    """
    
    def __init__(self):
        self.power_monitor = PowerRailMonitor()
        self.barometer = DifferentialBarometer()
        self.voc_corrector = VOCBaselineCorrector()
        self.geiger_compensator = GeigerDeadTimeCompensator()
        self.lapse_rate = LapseRateCalculator()
        self.packet_checker = PacketIntegrityChecker()
        self.proximity_vario = AudioProximityVarimeter()
        
    def process_all(self, data: Dict) -> Dict:
        """Process all sensor data through signal processing pipeline."""
        
        timestamp = data.get('timestamp', 0)
        
        # Power monitoring
        if 'battery_voltage' in data:
            self.power_monitor.add_reading(
                timestamp, data['battery_voltage'],
                data.get('load_current', 0)
            )
            
        # Barometer fusion
        if 'bmp388_pressure' in data and 'bme688_pressure' in data:
            baro_result = self.barometer.fuse_sensors(
                data['bmp388_pressure'],
                data['bme688_pressure'],
                data.get('bme688_temperature', 20),
                data.get('gps_altitude')
            )
        else:
            baro_result = {'status': 'No barometer data'}
            
        # VOC correction
        if 'voc_raw' in data and 'temperature' in data:
            self.voc_corrector.add_reading(timestamp, data['voc_raw'], data['temperature'])
            corrected_voc = self.voc_corrector.correct_voc(data['voc_raw'], data['temperature'])
        else:
            corrected_voc = data.get('voc', 0)
            
        # Geiger dead-time compensation
        if 'geiger_cpm' in data:
            geiger_result = self.geiger_compensator.compensate_dead_time(data['geiger_cpm'])
        else:
            geiger_result = {'status': 'No geiger data'}
            
        # Lapse rate
        if 'altitude' in data and 'temperature' in data:
            self.lapse_rate.add_reading(
                timestamp, data['altitude'], data['temperature'],
                data.get('pressure', 1013), data.get('voc', 0)
            )
            lapse_result = self.lapse_rate.get_meteorological_report()
        else:
            lapse_result = {'status': 'No atmospheric data'}
            
        # Proximity vario
        if 'tof_distance' in data:
            self.proximity_vario.add_distance(data['tof_distance'])
            vario_result = self.proximity_vario.get_beep_params(timestamp)
        else:
            vario_result = None
            
        return {
            'timestamp': timestamp,
            'power_health': self.power_monitor.get_power_health_report(),
            'altitude_fusion': baro_result,
            'corrected_voc': corrected_voc,
            'voc_correction_report': self.voc_corrector.get_correction_report(),
            'geiger_compensated': geiger_result,
            'lapse_rate_analysis': lapse_result,
            'proximity_beep': vario_result
        }


def create_hardware_processor() -> HardwareSignalProcessor:
    """Factory function."""
    return HardwareSignalProcessor()


if __name__ == "__main__":
    print("=" * 60)
    print("Hardware Signal Processing System")
    print("=" * 60)
    
    processor = create_hardware_processor()
    
    # Simulate data
    for i in range(100):
        data = {
            'timestamp': i * 2,
            'altitude': 1000 - i * 10,
            'battery_voltage': 7.4 - i * 0.003,
            'load_current': 150 + (50 if i % 10 < 3 else 0),
            'bmp388_pressure': 900 + i * 0.1,
            'bme688_pressure': 901 + i * 0.1,
            'bme688_temperature': 20 - i * 0.01,
            'voc_raw': 200 + np.random.normal(50, 20),
            'temperature': 20 - i * 0.015,
            'geiger_cpm': 30 + i * 0.3,
            'tof_distance': 100 if i < 80 else (100 - (i - 80) * 10),
            'pressure': 1013 - i * 0.01
        }
        
        if i % 20 == 0:
            result = processor.process_all(data)
            print(f"\n--- t={i*2}s ---")
            print(f"Power: {result['power_health']['esr_analysis']['status']}, ESR={result['power_health']['esr_analysis']['esr_mohm']:.1f}mΩ")
            print(f"Altitude: {result['altitude_fusion'].get('fused_altitude', 0):.1f}m, jitter={result['altitude_fusion'].get('jitter_cm', 0):.1f}cm")
            print(f"Corrected VOC: {result['corrected_voc']:.1f} ppm")
            print(f"Lapse Rate: {result['lapse_rate_analysis']['lapse_rate_analysis']['lapse_rate_per_100m']:.2f}°C/100m")
            
    print("\n" + "=" * 60)
    print("Hardware Signal Processor Ready!")
    print("=" * 60)