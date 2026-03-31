#!/usr/bin/env python3
"""
Advanced Data Filtering and Signal Processing Pipeline
Kalman filtering, outlier detection, noise reduction, data quality assessment
"""

import numpy as np
from typing import Tuple, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FilterState:
    """Kalman filter state"""
    x: np.ndarray  # State estimate
    P: np.ndarray  # Error covariance
    Q: np.ndarray  # Process noise covariance
    R: np.ndarray  # Measurement noise covariance


class KalmanFilter:
    """1D Kalman filter for sensor data"""
    
    def __init__(self, process_variance: float = 1e-5, measurement_variance: float = 0.1):
        """Initialize Kalman filter
        
        Args:
            process_variance: Process noise variance (Q)
            measurement_variance: Measurement noise variance (R)
        """
        self.state = FilterState(
            x=np.array([0.0]),
            P=np.array([[1.0]]),
            Q=np.array([[process_variance]]),
            R=np.array([[measurement_variance]])
        )
        
        # State transition matrix (constant velocity model)
        self.F = np.array([[1.0]])
        self.H = np.array([[1.0]])  # Measurement matrix
        
        self.initialized = False
    
    def predict(self) -> float:
        """Predict next state"""
        # x_pred = F * x
        self.state.x = self.F @ self.state.x
        
        # P_pred = F * P * F^T + Q
        self.state.P = self.F @ self.state.P @ self.F.T + self.state.Q
        
        return self.state.x[0]
    
    def update(self, measurement: float) -> float:
        """Update with measurement
        
        Args:
            measurement: New sensor reading
            
        Returns:
            Filtered estimate
        """
        if not self.initialized:
            self.state.x[0] = measurement
            self.initialized = True
            return measurement
        
        # Predict
        self.predict()
        
        # Innovation (measurement residual)
        z = np.array([measurement])
        y = z - self.H @ self.state.x
        
        # Innovation covariance
        S = self.H @ self.state.P @ self.H.T + self.state.R
        
        # Kalman gain
        K = self.state.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state estimate
        self.state.x = self.state.x + K @ y
        
        # Update error covariance
        I = np.eye(1)
        self.state.P = (I - K @ self.H) @ self.state.P
        
        return self.state.x[0]


class OutlierDetector:
    """Statistical outlier detection"""
    
    def __init__(self, window_size: int = 20, threshold: float = 3.0):
        """Initialize outlier detector
        
        Args:
            window_size: Size of sliding window
            threshold: Number of standard deviations for outlier
        """
        self.window_size = window_size
        self.threshold = threshold
        self.buffer = []
    
    def is_outlier(self, value: float) -> Tuple[bool, float]:
        """Check if value is an outlier
        
        Args:
            value: New data point
            
        Returns:
            (is_outlier, z_score)
        """
        self.buffer.append(value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        
        if len(self.buffer) < 3:
            return False, 0.0
        
        mean = np.mean(self.buffer)
        std = np.std(self.buffer)
        
        if std < 1e-6:
            return False, 0.0
        
        z_score = abs((value - mean) / std)
        is_outlier = z_score > self.threshold
        
        return is_outlier, z_score


class MovingAverageFilter:
    """Simple moving average filter"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.buffer = []
    
    def filter(self, value: float) -> float:
        """Apply moving average filter"""
        self.buffer.append(value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        
        return np.mean(self.buffer)


class ExponentialFilter:
    """Exponential moving average filter"""
    
    def __init__(self, alpha: float = 0.3):
        """Initialize exponential filter
        
        Args:
            alpha: Smoothing factor (0-1), higher = less smoothing
        """
        self.alpha = alpha
        self.value = None
    
    def filter(self, measurement: float) -> float:
        """Apply exponential filter"""
        if self.value is None:
            self.value = measurement
        else:
            self.value = self.alpha * measurement + (1 - self.alpha) * self.value
        
        return self.value


class MedianFilter:
    """Median filter for spike removal"""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.buffer = []
    
    def filter(self, value: float) -> float:
        """Apply median filter"""
        self.buffer.append(value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        
        return np.median(self.buffer)


class DataQualityAssessor:
    """Assess data quality and health"""
    
    def __init__(self):
        self.last_value = None
        self.last_update_time = None
        self.frozen_count = 0
        self.missing_count = 0
        self.total_count = 0
    
    def assess(self, value: Optional[float], timestamp: float) -> dict:
        """Assess data quality
        
        Returns:
            Dictionary with quality metrics
        """
        self.total_count += 1
        
        # Check for missing data
        if value is None:
            self.missing_count += 1
            return {
                'status': 'MISSING',
                'frozen': False,
                'missing_rate': self.missing_count / self.total_count,
                'quality_score': 0.0
            }
        
        # Check for frozen data
        frozen = False
        if self.last_value is not None and abs(value - self.last_value) < 1e-6:
            self.frozen_count += 1
            if self.frozen_count > 10:
                frozen = True
        else:
            self.frozen_count = 0
        
        self.last_value = value
        self.last_update_time = timestamp
        
        # Calculate quality score
        missing_rate = self.missing_count / self.total_count
        quality_score = 1.0 - missing_rate
        
        if frozen:
            quality_score *= 0.5
        
        status = 'HEALTHY' if quality_score > 0.9 else 'DEGRADED' if quality_score > 0.7 else 'CRITICAL'
        
        return {
            'status': status,
            'frozen': frozen,
            'missing_rate': missing_rate,
            'quality_score': quality_score
        }


class ComprehensiveDataPipeline:
    """Complete data processing pipeline"""
    
    def __init__(self):
        """Initialize all filters and processors"""
        # Filters for different sensor types
        self.altitude_filter = KalmanFilter(process_variance=1e-4, measurement_variance=0.5)
        self.velocity_filter = KalmanFilter(process_variance=1e-3, measurement_variance=1.0)
        self.temperature_filter = ExponentialFilter(alpha=0.2)
        self.pressure_filter = KalmanFilter(process_variance=1e-5, measurement_variance=10.0)
        self.radiation_filter = MedianFilter(window_size=5)
        self.voc_filter = MovingAverageFilter(window_size=10)
        
        # Outlier detectors
        self.altitude_outlier = OutlierDetector(window_size=20, threshold=3.0)
        self.radiation_outlier = OutlierDetector(window_size=15, threshold=2.5)
        
        # Quality assessors
        self.altitude_quality = DataQualityAssessor()
        self.radiation_quality = DataQualityAssessor()
        
        logger.info("Data processing pipeline initialized")
    
    def process_altitude(self, raw_value: float, timestamp: float) -> dict:
        """Process altitude measurement"""
        # Quality assessment
        quality = self.altitude_quality.assess(raw_value, timestamp)
        
        # Outlier detection
        is_outlier, z_score = self.altitude_outlier.is_outlier(raw_value)
        
        # Apply Kalman filter
        filtered_value = self.altitude_filter.update(raw_value)
        
        return {
            'raw': raw_value,
            'filtered': filtered_value,
            'is_outlier': is_outlier,
            'z_score': z_score,
            'quality': quality
        }
    
    def process_radiation(self, raw_value: float, timestamp: float) -> dict:
        """Process radiation measurement"""
        # Quality assessment
        quality = self.radiation_quality.assess(raw_value, timestamp)
        
        # Outlier detection
        is_outlier, z_score = self.radiation_outlier.is_outlier(raw_value)
        
        # Apply median filter (good for spike removal)
        filtered_value = self.radiation_filter.filter(raw_value)
        
        return {
            'raw': raw_value,
            'filtered': filtered_value,
            'is_outlier': is_outlier,
            'z_score': z_score,
            'quality': quality
        }
    
    def process_temperature(self, raw_value: float) -> float:
        """Process temperature measurement"""
        return self.temperature_filter.filter(raw_value)
    
    def process_pressure(self, raw_value: float) -> float:
        """Process pressure measurement"""
        return self.pressure_filter.update(raw_value)
    
    def process_voc(self, raw_value: float) -> float:
        """Process VOC measurement"""
        return self.voc_filter.filter(raw_value)


# ============================================================================
# ADVANCED FILTERING ALGORITHMS (NEW - PRESERVING ALL EXISTING FEATURES)
# ============================================================================

class SavitzkyGolayFilter:
    """Savitzky-Golay filter for polynomial smoothing
    
    Preserves signal features better than moving average.
    Excellent for scientific data with peaks and valleys.
    """
    
    def __init__(self, window_size: int = 11, poly_order: int = 3):
        """Initialize Savitzky-Golay filter
        
        Args:
            window_size: Window size (must be odd)
            poly_order: Polynomial order (must be < window_size)
        """
        if window_size % 2 == 0:
            window_size += 1  # Ensure odd
        
        self.window_size = window_size
        self.poly_order = min(poly_order, window_size - 1)
        self.buffer = []
    
    def filter(self, value: float) -> float:
        """Apply Savitzky-Golay filter"""
        self.buffer.append(value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        
        if len(self.buffer) < self.window_size:
            return value
        
        try:
            from scipy.signal import savgol_filter
            filtered = savgol_filter(self.buffer, self.window_size, self.poly_order)
            return filtered[-1]
        except ImportError:
            # Fallback to simple moving average
            return np.mean(self.buffer)


class ButterworthFilter:
    """Butterworth low-pass digital filter
    
    Removes high-frequency noise with smooth frequency response.
    """
    
    def __init__(self, cutoff_freq: float = 0.1, order: int = 4, sampling_rate: float = 10.0):
        """Initialize Butterworth filter
        
        Args:
            cutoff_freq: Cutoff frequency (Hz)
            order: Filter order (higher = sharper cutoff)
            sampling_rate: Sampling rate (Hz)
        """
        self.cutoff_freq = cutoff_freq
        self.order = order
        self.sampling_rate = sampling_rate
        self.buffer = []
        self.max_buffer = 100
    
    def filter(self, value: float) -> float:
        """Apply Butterworth filter"""
        self.buffer.append(value)
        if len(self.buffer) > self.max_buffer:
            self.buffer.pop(0)
        
        if len(self.buffer) < 25: # filtfilt needs enough padding
            return value
        
        try:
            from scipy.signal import butter, filtfilt
            nyquist = self.sampling_rate / 2.0
            normal_cutoff = self.cutoff_freq / nyquist
            b, a = butter(self.order, normal_cutoff, btype='low', analog=False)
            filtered = filtfilt(b, a, self.buffer)
            return filtered[-1]
        except (ImportError, ValueError):
            # Fallback to exponential filter
            alpha = 0.3
            result = self.buffer[0]
            for val in self.buffer[1:]:
                result = alpha * val + (1 - alpha) * result
            return result


class WaveletDenoiser:
    """Wavelet-based denoising filter
    
    Multi-resolution analysis for noise removal while preserving edges.
    Excellent for non-stationary signals.
    """
    
    def __init__(self, wavelet: str = 'db4', level: int = 3, threshold_type: str = 'soft'):
        """Initialize wavelet denoiser
        
        Args:
            wavelet: Wavelet type ('db4', 'sym4', 'coif1', etc.)
            level: Decomposition level
            threshold_type: 'soft' or 'hard' thresholding
        """
        self.wavelet = wavelet
        self.level = level
        self.threshold_type = threshold_type
        self.buffer = []
        self.max_buffer = 64  # Power of 2 for efficiency
    
    def filter(self, value: float) -> float:
        """Apply wavelet denoising"""
        self.buffer.append(value)
        if len(self.buffer) > self.max_buffer:
            self.buffer.pop(0)
        
        if len(self.buffer) < 32:
            return value
        
        try:
            import pywt
            # Wavelet decomposition
            coeffs = pywt.wavedec(self.buffer, self.wavelet, level=self.level)
            
            # Threshold estimation (universal threshold)
            sigma = np.median(np.abs(coeffs[-1])) / 0.6745
            threshold = sigma * np.sqrt(2 * np.log(len(self.buffer)))
            
            # Apply thresholding
            coeffs_thresh = [coeffs[0]]  # Keep approximation coefficients
            for coeff in coeffs[1:]:
                if self.threshold_type == 'soft':
                    coeffs_thresh.append(pywt.threshold(coeff, threshold, mode='soft'))
                else:
                    coeffs_thresh.append(pywt.threshold(coeff, threshold, mode='hard'))
            
            # Reconstruction
            denoised = pywt.waverec(coeffs_thresh, self.wavelet)
            return denoised[len(self.buffer) // 2]
        except ImportError:
            # Fallback to median filter
            return np.median(self.buffer[-5:] if len(self.buffer) >= 5 else self.buffer)


class AdaptiveLMSFilter:
    """Adaptive Least Mean Squares (LMS) filter
    
    Learns optimal filter coefficients adaptively.
    Adapts to changing signal characteristics.
    """
    
    def __init__(self, filter_order: int = 10, step_size: float = 0.01):
        """Initialize adaptive LMS filter
        
        Args:
            filter_order: Number of filter coefficients
            step_size: Learning rate (smaller = more stable, slower adaptation)
        """
        self.filter_order = filter_order
        self.step_size = step_size
        self.weights = np.zeros(filter_order)
        self.buffer = []
    
    def filter(self, value: float, desired: Optional[float] = None) -> float:
        """Apply adaptive LMS filter
        
        Args:
            value: Input signal
            desired: Desired signal (if None, uses delayed input)
        """
        self.buffer.append(value)
        if len(self.buffer) > self.filter_order + 10:
            self.buffer.pop(0)
        
        if len(self.buffer) < self.filter_order:
            return value
        
        # Input vector
        x = np.array(self.buffer[-self.filter_order:])
        
        # Filter output
        y = np.dot(self.weights, x)
        
        # Desired signal (use delayed input if not provided)
        if desired is None:
            desired = self.buffer[-self.filter_order - 5] if len(self.buffer) > self.filter_order + 5 else value
        
        # Error
        error = desired - y
        
        # Update weights (LMS algorithm)
        self.weights += self.step_size * error * x
        
        return y


class HampelFilter:
    """Hampel filter for robust outlier replacement
    
    Replaces outliers with median of neighboring values.
    More robust than simple outlier detection.
    """
    
    def __init__(self, window_size: int = 7, n_sigma: float = 3.0):
        """Initialize Hampel filter
        
        Args:
            window_size: Window size for median calculation
            n_sigma: Number of standard deviations for outlier threshold
        """
        self.window_size = window_size
        self.n_sigma = n_sigma
        self.buffer = []
    
    def filter(self, value: float) -> float:
        """Apply Hampel filter"""
        self.buffer.append(value)
        if len(self.buffer) > self.window_size * 2:
            self.buffer.pop(0)
        
        if len(self.buffer) < self.window_size:
            return value
        
        # Get window around current value
        window = self.buffer[-self.window_size:]
        
        # Calculate median and MAD (Median Absolute Deviation)
        median = np.median(window)
        mad = np.median(np.abs(window - median))
        
        # Threshold
        threshold = self.n_sigma * 1.4826 * mad  # 1.4826 is consistency constant
        
        # Replace outlier with median
        if abs(value - median) > threshold:
            return median
        else:
            return value


class TrimmedMeanFilter:
    """Trimmed mean filter
    
    Removes extreme values before averaging.
    More robust than simple mean.
    """
    
    def __init__(self, window_size: int = 10, trim_percent: float = 0.2):
        """Initialize trimmed mean filter
        
        Args:
            window_size: Window size
            trim_percent: Percentage to trim from each end (0.0-0.5)
        """
        self.window_size = window_size
        self.trim_percent = min(0.5, max(0.0, trim_percent))
        self.buffer = []
    
    def filter(self, value: float) -> float:
        """Apply trimmed mean filter"""
        self.buffer.append(value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        
        if len(self.buffer) < 3:
            return value
        
        # Sort values
        sorted_values = np.sort(self.buffer)
        
        # Calculate trim indices
        n_trim = int(len(sorted_values) * self.trim_percent)
        
        if n_trim > 0:
            trimmed = sorted_values[n_trim:-n_trim]
        else:
            trimmed = sorted_values
        
        return np.mean(trimmed)


class WinsorizedMeanFilter:
    """Winsorized mean filter
    
    Caps extreme values instead of removing them.
    Preserves sample size while reducing outlier impact.
    """
    
    def __init__(self, window_size: int = 10, limits: Tuple[float, float] = (0.1, 0.1)):
        """Initialize Winsorized mean filter
        
        Args:
            window_size: Window size
            limits: (lower_limit, upper_limit) as fractions (0.0-0.5 each)
        """
        self.window_size = window_size
        self.limits = limits
        self.buffer = []
    
    def filter(self, value: float) -> float:
        """Apply Winsorized mean filter"""
        self.buffer.append(value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        
        if len(self.buffer) < 3:
            return value
        
        # Sort values
        sorted_values = np.sort(self.buffer)
        
        # Calculate Winsorization bounds
        n = len(sorted_values)
        lower_idx = int(n * self.limits[0])
        upper_idx = int(n * (1 - self.limits[1]))
        
        # Winsorize
        winsorized = sorted_values.copy()
        if lower_idx > 0:
            winsorized[:lower_idx] = sorted_values[lower_idx]
        if upper_idx < n:
            winsorized[upper_idx:] = sorted_values[upper_idx - 1]
        
        return np.mean(winsorized)


# ============================================================================
# ENHANCED DATA PROCESSING PIPELINE
# ============================================================================

@dataclass
class FilterPerformanceMetrics:
    """Performance metrics for filter evaluation"""
    filter_name: str
    rmse: float  # Root Mean Square Error
    snr: float  # Signal-to-Noise Ratio
    latency: float  # Processing latency (ms)
    smoothness: float  # Signal smoothness metric


class EnhancedDataProcessingPipeline:
    """Enhanced pipeline with advanced filters and performance tracking"""
    
    def __init__(self, enable_advanced: bool = True):
        """Initialize enhanced pipeline
        
        Args:
            enable_advanced: Enable advanced filters (requires scipy, pywt)
        """
        # Keep ALL existing filters
        self.kalman = KalmanFilter()
        self.outlier = OutlierDetector()
        self.moving_avg = MovingAverageFilter()
        self.exponential = ExponentialFilter()
        self.median = MedianFilter()
        self.quality = DataQualityAssessor()
        
        # Add advanced filters
        self.enable_advanced = enable_advanced
        if enable_advanced:
            self.savgol = SavitzkyGolayFilter(window_size=11, poly_order=3)
            self.butterworth = ButterworthFilter(cutoff_freq=0.1, order=4)
            self.wavelet = WaveletDenoiser(wavelet='db4', level=3)
            self.adaptive_lms = AdaptiveLMSFilter(filter_order=10, step_size=0.01)
            self.hampel = HampelFilter(window_size=7, n_sigma=3.0)
            self.trimmed_mean = TrimmedMeanFilter(window_size=10, trim_percent=0.2)
            self.winsorized = WinsorizedMeanFilter(window_size=10, limits=(0.1, 0.1))
        
        # Performance tracking and adaptive recommendation
        self.performance_metrics = {} # Stores historical performance of filters
        self.filter_recommendation_history = [] # Tracks past recommendations and simulated outcomes
        
        logger.info(f"Enhanced data processing pipeline initialized (advanced={enable_advanced})")
    
    def process(self, value: float, timestamp: float, filter_type: str = 'kalman') -> float:
        """Process value with specified filter
        
        Args:
            value: Raw measurement
            timestamp: Timestamp
            filter_type: Filter to use ('kalman', 'savgol', 'butterworth', 'wavelet', 
                        'adaptive', 'hampel', 'trimmed', 'winsorized', 'median', 
                        'moving_avg', 'exponential')
        
        Returns:
            Filtered value
        """
        import time
        start_time = time.time()
        
        # Apply selected filter
        if filter_type == 'kalman':
            result = self.kalman.update(value)
        elif filter_type == 'median':
            result = self.median.filter(value)
        elif filter_type == 'moving_avg':
            result = self.moving_avg.filter(value)
        elif filter_type == 'exponential':
            result = self.exponential.filter(value)
        elif self.enable_advanced:
            if filter_type == 'savgol':
                result = self.savgol.filter(value)
            elif filter_type == 'butterworth':
                result = self.butterworth.filter(value)
            elif filter_type == 'wavelet':
                result = self.wavelet.filter(value)
            elif filter_type == 'adaptive':
                result = self.adaptive_lms.filter(value)
            elif filter_type == 'hampel':
                result = self.hampel.filter(value)
            elif filter_type == 'trimmed':
                result = self.trimmed_mean.filter(value)
            elif filter_type == 'winsorized':
                result = self.winsorized.filter(value)
            else:
                result = value
        else:
            result = value
        
        # Track latency
        latency = (time.time() - start_time) * 1000  # ms
        
        # Simulate filter performance (e.g., higher value means better)
        # In a real system, this would come from actual signal analysis (RMSE, SNR, etc.)
        simulated_performance = 1.0 - (abs(value - result) / max(1, abs(value))) # Closer filtered to raw, higher 'smoothness'

        # Update historical performance for this filter type
        if filter_type not in self.performance_metrics:
            self.performance_metrics[filter_type] = {'total_performance': 0.0, 'count': 0}
        
        self.performance_metrics[filter_type]['total_performance'] += simulated_performance
        self.performance_metrics[filter_type]['count'] += 1
        
        return result
    
    def recommend_filter(self, signal_characteristics: dict) -> str:
        """Recommend best filter based on signal characteristics and adaptive learning.
        
        Args:
            signal_characteristics: Dict with 'noise_level', 'has_spikes', 
                                   'is_smooth', 'is_stationary'
        
        Returns:
            Recommended filter name
        """
        noise = signal_characteristics.get('noise_level', 'medium')
        has_spikes = signal_characteristics.get('has_spikes', False)
        is_smooth = signal_characteristics.get('is_smooth', True)
        is_stationary = signal_characteristics.get('is_stationary', True)

        # Initial rule-based recommendation (baseline)
        if has_spikes:
            initial_recommendation = 'hampel' if self.enable_advanced else 'median'
        elif noise == 'high':
            if is_stationary:
                initial_recommendation = 'savgol' if self.enable_advanced else 'kalman'
            else:
                initial_recommendation = 'wavelet' if self.enable_advanced else 'adaptive'
        elif noise == 'low':
            initial_recommendation = 'exponential'
        else:  # medium noise
            if is_smooth:
                initial_recommendation = 'butterworth' if self.enable_advanced else 'kalman'
            else:
                initial_recommendation = 'savgol' if self.enable_advanced else 'moving_avg'
        
        # Adaptive adjustment based on historical performance
        # This is a rudimentary form of adaptive learning:
        # If a filter has performed well historically for similar characteristics,
        # it gets a boost. Otherwise, stick to the rule-based.
        
        best_adaptive_filter = initial_recommendation
        highest_avg_performance = self.performance_metrics.get(initial_recommendation, {}).get('total_performance', 0.0) / max(1, self.performance_metrics.get(initial_recommendation, {}).get('count', 0))
        
        for filter_name, metrics in self.performance_metrics.items():
            if metrics['count'] > 10: # Only consider filters with sufficient history
                avg_performance = metrics['total_performance'] / metrics['count']
                
                # Simple adaptive logic: if another filter has significantly better average performance
                # for similar characteristics (simulated here by a random boost for simplicity),
                # recommend it instead.
                # In a real system, 'similar characteristics' would involve a more complex matching
                # based on past 'signal_characteristics' for which the filter was used.
                if avg_performance > highest_avg_performance + 0.1: # 0.1 is an arbitrary threshold
                    highest_avg_performance = avg_performance
                    best_adaptive_filter = filter_name

        self.filter_recommendation_history.append({
            'timestamp': datetime.now().isoformat(),
            'signal_characteristics': signal_characteristics,
            'initial_recommendation': initial_recommendation,
            'final_recommendation': best_adaptive_filter,
            'confidence': highest_avg_performance # Confidence is based on historical performance
        })
        
        return best_adaptive_filter


# Alias for backward compatibility
DataProcessingPipeline = ComprehensiveDataPipeline


def main():
    """Test data processing pipeline"""
    import matplotlib.pyplot as plt
    
    pipeline = ComprehensiveDataPipeline()
    
    print("Testing Data Processing Pipeline")
    print("="*60)
    
    # Generate noisy data with outliers
    t = np.linspace(0, 10, 100)
    true_signal = 100 * np.sin(t)
    noise = np.random.normal(0, 5, 100)
    measurements = true_signal + noise
    
    # Add some outliers
    measurements[20] += 50
    measurements[50] -= 40
    measurements[80] += 60
    
    # Process data
    filtered = []
    outliers = []
    
    for i, (time, meas) in enumerate(zip(t, measurements)):
        result = pipeline.process_altitude(meas, time)
        filtered.append(result['filtered'])
        if result['is_outlier']:
            outliers.append(i)
    
    print(f"\nProcessed {len(measurements)} measurements")
    print(f"Detected {len(outliers)} outliers at indices: {outliers}")
    
    # Plot results
    plt.figure(figsize=(12, 6))
    plt.plot(t, true_signal, 'g-', label='True Signal', linewidth=2)
    plt.plot(t, measurements, 'r.', label='Noisy Measurements', alpha=0.5)
    plt.plot(t, filtered, 'b-', label='Kalman Filtered', linewidth=2)
    plt.scatter(t[outliers], measurements[outliers], c='orange', s=100, marker='x', label='Outliers', zorder=5)
    plt.xlabel('Time (s)')
    plt.ylabel('Altitude (m)')
    plt.title('Data Processing Pipeline - Kalman Filter + Outlier Detection')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('data_pipeline_test.png')
    print("\n✅ Plot saved: data_pipeline_test.png")


if __name__ == "__main__":
    main()
