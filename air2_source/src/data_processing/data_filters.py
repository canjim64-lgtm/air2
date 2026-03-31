"""
Advanced Data Filters for AirOne v3.0
Implements comprehensive filtering techniques for sensor data processing
"""

import numpy as np
from typing import List, Tuple, Optional, Union, Dict, Any
from datetime import datetime
import math
from scipy import signal
from scipy.ndimage import median_filter
from scipy.interpolate import interp1d
import warnings
warnings.filterwarnings('ignore')


class ButterworthFilter:
    """Butterworth low-pass/high-pass/band-pass filter implementation"""
    
    def __init__(self, cutoff_freq: float, sampling_rate: float, filter_order: int = 4, 
                 filter_type: str = 'low'):
        """
        Initialize Butterworth filter
        :param cutoff_freq: Cutoff frequency (Hz)
        :param sampling_rate: Sampling rate (Hz)
        :param filter_order: Filter order (default 4)
        :param filter_type: 'low', 'high', 'band', 'bandstop'
        """
        nyquist = 0.5 * sampling_rate
        normal_cutoff = cutoff_freq / nyquist
        
        # Design filter
        self.b, self.a = signal.butter(filter_order, normal_cutoff, 
                                       btype=filter_type, analog=False)
        
        # Initialize filter state
        self.zi = signal.lfilter_zi(self.b, self.a)
        self.initialized = False
    
    def filter(self, data: np.ndarray) -> np.ndarray:
        """Apply filter to data"""
        if not self.initialized:
            # Initialize with first sample
            filtered_data, self.zi = signal.lfilter(self.b, self.a, data, zi=self.zi * data[0])
            self.initialized = True
        else:
            filtered_data, self.zi = signal.lfilter(self.b, self.a, data, zi=self.zi)
        
        return filtered_data


class KalmanFilter1D:
    """1D Kalman Filter for real-time data filtering"""
    
    def __init__(self, process_noise: float = 0.1, measurement_noise: float = 0.1, 
                 initial_estimate: float = 0.0, initial_error: float = 1.0):
        """
        Initialize 1D Kalman Filter
        :param process_noise: Process noise (Q)
        :param measurement_noise: Measurement noise (R)
        :param initial_estimate: Initial state estimate
        :param initial_error: Initial error estimate
        """
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.estimate = initial_estimate
        self.error = initial_error
        
        # State transition model (constant)
        self.A = 1.0  # State transition
        self.H = 1.0  # Observation model
    
    def update(self, measurement: float) -> float:
        """Update filter with new measurement"""
        # Prediction step
        prediction = self.A * self.estimate
        prediction_error = self.A * self.error * self.A + self.process_noise
        
        # Update step
        kalman_gain = prediction_error * self.H / (self.H * prediction_error * self.H + self.measurement_noise)
        self.estimate = prediction + kalman_gain * (measurement - self.H * prediction)
        self.error = (1 - kalman_gain * self.H) * prediction_error
        
        return self.estimate


class SavitzkyGolayFilter:
    """Savitzky-Golay filter for smoothing and derivative estimation"""
    
    def __init__(self, window_length: int = 5, polyorder: int = 2, deriv: int = 0):
        """
        Initialize Savitzky-Golay filter
        :param window_length: Length of the filter window (odd number)
        :param polyorder: Order of polynomial to fit
        :param deriv: Order of derivative to compute
        """
        if window_length % 2 == 0:
            window_length += 1  # Ensure odd window length
        if window_length < polyorder + 2:
            window_length = polyorder + 2
            if window_length % 2 == 0:
                window_length += 1
        
        self.window_length = window_length
        self.polyorder = polyorder
        self.deriv = deriv
    
    def filter(self, data: np.ndarray) -> np.ndarray:
        """Apply Savitzky-Golay filter to data"""
        if len(data) < self.window_length:
            # If data is too short, return original data
            return data
        
        return signal.savgol_filter(data, self.window_length, self.polyorder, 
                                   deriv=self.deriv)


class MedianFilter:
    """Median filter for removing impulse noise"""
    
    def __init__(self, window_size: int = 3):
        """
        Initialize Median filter
        :param window_size: Size of the median window
        """
        self.window_size = window_size if window_size % 2 == 1 else window_size + 1  # Ensure odd
    
    def filter(self, data: np.ndarray) -> np.ndarray:
        """Apply median filter to data"""
        return median_filter(data, size=self.window_size)


class MovingAverageFilter:
    """Moving average filter for smoothing data"""
    
    def __init__(self, window_size: int = 5):
        """
        Initialize Moving Average filter
        :param window_size: Size of the averaging window
        """
        self.window_size = window_size
        self.buffer = np.zeros(window_size)
        self.index = 0
        self.filled = False
    
    def filter(self, data: np.ndarray) -> np.ndarray:
        """Apply moving average filter to data"""
        if len(data) == 1:
            # Single value - update internal buffer
            self.buffer[self.index] = data[0]
            self.index = (self.index + 1) % self.window_size
            
            if self.index == 0:
                self.filled = True
            
            current_buffer = self.buffer if self.filled else self.buffer[:self.index]
            return np.mean(current_buffer)
        else:
            # Array of values - apply moving average
            if len(data) < self.window_size:
                # Use simple average if data is too short
                return np.full_like(data, np.mean(data))
            
            # Use convolution for efficiency
            window = np.ones(self.window_size) / self.window_size
            return np.convolve(data, window, mode='same')


class AlphaBetaFilter:
    """Alpha-Beta filter for tracking with position and velocity"""
    
    def __init__(self, alpha: float = 0.8, beta: float = 0.2, dt: float = 1.0):
        """
        Initialize Alpha-Beta filter
        :param alpha: Position correction gain
        :param beta: Velocity correction gain
        :param dt: Time step
        """
        self.alpha = alpha
        self.beta = beta
        self.dt = dt
        self.reset()
    
    def reset(self):
        """Reset filter state"""
        self.position = 0.0
        self.velocity = 0.0
        self.initialized = False
    
    def update(self, measurement: float) -> Tuple[float, float]:
        """Update filter with new measurement"""
        if not self.initialized:
            self.position = measurement
            self.initialized = True
            return self.position, self.velocity
        
        # Predict
        predicted_position = self.position + self.dt * self.velocity
        predicted_velocity = self.velocity
        
        # Update
        residual = measurement - predicted_position
        self.position = predicted_position + self.alpha * residual
        self.velocity = predicted_velocity + self.beta * residual / self.dt
        
        return self.position, self.velocity


class ParticleFilter1D:
    """1D Particle Filter for non-linear/non-Gaussian systems"""
    
    def __init__(self, num_particles: int = 100, process_noise: float = 0.1, 
                 measurement_noise: float = 0.1):
        """
        Initialize 1D Particle Filter
        :param num_particles: Number of particles
        :param process_noise: Process noise standard deviation
        :param measurement_noise: Measurement noise standard deviation
        """
        self.num_particles = num_particles
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        
        # Initialize particles
        self.particles = np.random.randn(num_particles) * 10
        self.weights = np.ones(num_particles) / num_particles
    
    def update(self, measurement: float) -> float:
        """Update filter with new measurement"""
        # Predict step - add process noise
        self.particles += np.random.normal(0, self.process_noise, self.num_particles)
        
        # Update weights based on measurement likelihood
        likelihood = np.exp(-0.5 * ((measurement - self.particles) / self.measurement_noise) ** 2)
        self.weights *= likelihood
        self.weights += 1e-300  # Avoid zero weights
        self.weights /= np.sum(self.weights)  # Normalize
        
        # Resample if effective sample size is too low
        effective_samples = 1.0 / np.sum(self.weights ** 2)
        if effective_samples < self.num_particles / 2:
            self._resample()
        
        # Return estimate (weighted average)
        estimate = np.average(self.particles, weights=self.weights)
        return estimate
    
    def _resample(self):
        """Systematic resampling"""
        cumulative_sum = np.cumsum(self.weights)
        cumulative_sum[-1] = 1.0  # Ensure last value is 1.0
        
        new_particles = np.zeros_like(self.particles)
        u = np.random.uniform(0, 1/self.num_particles)
        
        i, j = 0, 0
        while i < self.num_particles:
            while cumulative_sum[j] < u:
                j += 1
            new_particles[i] = self.particles[j]
            u += 1/self.num_particles
            i += 1
        
        self.particles = new_particles
        self.weights.fill(1.0 / self.num_particles)


class AdaptiveFilter:
    """Adaptive filter that adjusts parameters based on signal characteristics"""
    
    def __init__(self, initial_filter_type: str = 'kalman', window_size: int = 10):
        """
        Initialize Adaptive Filter
        :param initial_filter_type: Initial filter type ('kalman', 'moving_avg', 'median')
        :param window_size: Window size for adaptation
        """
        self.filter_type = initial_filter_type
        self.window_size = window_size
        self.data_window = []
        self.filter = self._create_filter(initial_filter_type)
    
    def _create_filter(self, filter_type: str):
        """Create filter instance based on type"""
        if filter_type == 'kalman':
            return KalmanFilter1D()
        elif filter_type == 'moving_avg':
            return MovingAverageFilter(window_size=5)
        elif filter_type == 'median':
            return MedianFilter(window_size=3)
        else:
            return KalmanFilter1D()
    
    def update_characteristics(self, data: List[float]) -> str:
        """Update filter based on signal characteristics"""
        if len(data) < 5:
            return self.filter_type
        
        # Calculate signal characteristics
        variance = np.var(data)
        mean_abs_change = np.mean(np.abs(np.diff(data)))
        max_change = np.max(np.abs(np.diff(data)))
        
        # Decide on best filter type based on characteristics
        if max_change > 3 * mean_abs_change:
            # Large outliers detected - use median filter
            new_type = 'median'
        elif variance > 10:
            # High variance - use Kalman filter
            new_type = 'kalman'
        else:
            # Smooth signal - use moving average
            new_type = 'moving_avg'
        
        if new_type != self.filter_type:
            self.filter_type = new_type
            self.filter = self._create_filter(new_type)
        
        return self.filter_type
    
    def filter(self, data: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Apply adaptive filter to data"""
        if isinstance(data, (list, np.ndarray)):
            result = []
            for val in data:
                # Update window
                self.data_window.append(val)
                if len(self.data_window) > self.window_size:
                    self.data_window.pop(0)
                
                # Update filter type if needed
                self.update_characteristics(self.data_window)
                
                # Apply filter
                if self.filter_type == 'kalman':
                    result.append(self.filter.update(val))
                else:
                    result.append(self.filter.filter(np.array([val]))[0])
            return np.array(result)
        else:
            # Single value
            self.data_window.append(data)
            if len(self.data_window) > self.window_size:
                self.data_window.pop(0)
            
            self.update_characteristics(self.data_window)
            
            if self.filter_type == 'kalman':
                return self.filter.update(data)
            else:
                return self.filter.filter(np.array([data]))[0]


class OutlierDetector:
    """Statistical outlier detection and removal"""
    
    def __init__(self, method: str = 'mad', threshold: float = 2.0):
        """
        Initialize Outlier Detector
        :param method: 'mad' (Median Absolute Deviation) or 'iqr' (Interquartile Range)
        :param threshold: Threshold multiplier for outlier detection
        """
        self.method = method
        self.threshold = threshold
        self.buffer = []
        self.buffer_size = 50  # Size of historical data for statistics
    
    def detect_and_clean(self, data: np.ndarray) -> Tuple[np.ndarray, List[bool]]:
        """
        Detect and clean outliers in data
        :param data: Input data array
        :return: Cleaned data array, outlier mask
        """
        if self.method == 'mad':
            return self._detect_mad(data)
        elif self.method == 'iqr':
            return self._detect_iqr(data)
        else:
            return data, [False] * len(data)
    
    def _detect_mad(self, data: np.ndarray) -> Tuple[np.ndarray, List[bool]]:
        """Detect outliers using Median Absolute Deviation"""
        # Update buffer with new data
        for val in data:
            self.buffer.append(val)
            if len(self.buffer) > self.buffer_size:
                self.buffer.pop(0)
        
        if len(self.buffer) < 3:
            return data, [False] * len(data)
        
        # Calculate MAD statistics
        median_val = np.median(self.buffer)
        mad = np.median(np.abs(np.array(self.buffer) - median_val))
        
        if mad == 0:
            mad = np.std(self.buffer)
        
        # Detect outliers
        cleaned_data = data.copy()
        outlier_mask = []
        
        for i, val in enumerate(data):
            # Calculate deviation from historical median
            deviation = abs(val - median_val)
            is_outlier = deviation > (self.threshold * mad)
            outlier_mask.append(is_outlier)
            
            if is_outlier:
                # Replace outlier with interpolated value or median
                if i > 0 and i < len(data) - 1:
                    # Use linear interpolation between neighbors
                    cleaned_data[i] = (data[i-1] + data[i+1]) / 2
                else:
                    # Use historical median
                    cleaned_data[i] = median_val
        
        return cleaned_data, outlier_mask
    
    def _detect_iqr(self, data: np.ndarray) -> Tuple[np.ndarray, List[bool]]:
        """Detect outliers using Interquartile Range"""
        # Update buffer with new data
        for val in data:
            self.buffer.append(val)
            if len(self.buffer) > self.buffer_size:
                self.buffer.pop(0)
        
        if len(self.buffer) < 4:
            return data, [False] * len(data)
        
        # Calculate IQR statistics
        q25, q75 = np.percentile(self.buffer, [25, 75])
        iqr = q75 - q25
        lower_bound = q25 - self.threshold * iqr
        upper_bound = q75 + self.threshold * iqr
        
        # Detect outliers
        cleaned_data = data.copy()
        outlier_mask = []
        
        for i, val in enumerate(data):
            is_outlier = val < lower_bound or val > upper_bound
            outlier_mask.append(is_outlier)
            
            if is_outlier:
                # Replace outlier with boundary value or median
                if val < lower_bound:
                    cleaned_data[i] = lower_bound
                elif val > upper_bound:
                    cleaned_data[i] = upper_bound
                else:
                    cleaned_data[i] = np.median(self.buffer)
        
        return cleaned_data, outlier_mask


class DataFilterPipeline:
    """Pipeline for chaining multiple filters together"""
    
    def __init__(self):
        self.filters = []
        self.filter_names = []
    
    def add_filter(self, filter_obj, name: str = ""):
        """Add a filter to the pipeline"""
        self.filters.append(filter_obj)
        self.filter_names.append(name if name else f"Filter_{len(self.filters)}")
    
    def add_outlier_detector(self):
        """Add outlier detector to pipeline"""
        self.add_filter(OutlierDetector(), "OutlierDetector")
    
    def add_kalman_filter(self, process_noise: float = 0.1, measurement_noise: float = 0.1):
        """Add Kalman filter to pipeline"""
        self.add_filter(KalmanFilter1D(process_noise, measurement_noise), "KalmanFilter")
    
    def add_moving_average(self, window_size: int = 5):
        """Add moving average filter to pipeline"""
        self.add_filter(MovingAverageFilter(window_size), "MovingAverage")
    
    def add_median_filter(self, window_size: int = 3):
        """Add median filter to pipeline"""
        self.add_filter(MedianFilter(window_size), "MedianFilter")
    
    def add_butterworth_filter(self, cutoff_freq: float, sampling_rate: float, 
                              filter_order: int = 4, filter_type: str = 'low'):
        """Add Butterworth filter to pipeline"""
        self.add_filter(ButterworthFilter(cutoff_freq, sampling_rate, filter_order, filter_type), 
                       "ButterworthFilter")
    
    def process(self, data: np.ndarray) -> np.ndarray:
        """Process data through the entire pipeline"""
        result = data.copy()
        
        for i, filter_obj in enumerate(self.filters):
            try:
                if hasattr(filter_obj, 'filter'):
                    result = filter_obj.filter(result)
                elif callable(filter_obj):
                    result = filter_obj(result)
            except Exception as e:
                print(f"Error in filter {self.filter_names[i]}: {e}")
                # Continue with original data if filter fails
        
        return result
    
    def reset(self):
        """Reset all filters in the pipeline"""
        for filter_obj in self.filters:
            if hasattr(filter_obj, 'reset'):
                filter_obj.reset()


class AdvancedDataFilterEngine:
    """Main engine for managing all data filtering operations"""
    
    def __init__(self):
        self.filters = {
            'kalman': KalmanFilter1D(),
            'alpha_beta': AlphaBetaFilter(),
            'particle': ParticleFilter1D(),
            'adaptive': AdaptiveFilter(),
            'outlier_detector': OutlierDetector(),
            'butterworth': ButterworthFilter(cutoff_freq=10, sampling_rate=100),
            'savitzky_golay': SavitzkyGolayFilter(),
            'median': MedianFilter(),
            'moving_average': MovingAverageFilter()
        }
        
        # Pipeline configurations for different sensor types
        self.pipeline_configs = {
            'altitude': self._create_altitude_pipeline(),
            'temperature': self._create_temperature_pipeline(),
            'pressure': self._create_pressure_pipeline(),
            'radiation': self._create_radiation_pipeline(),
            'gas': self._create_gas_pipeline(),
            'uv': self._create_uv_pipeline(),
            'magnetic': self._create_magnetic_pipeline()
        }
    
    def _create_altitude_pipeline(self) -> DataFilterPipeline:
        """Create pipeline optimized for altitude data"""
        pipeline = DataFilterPipeline()
        pipeline.add_outlier_detector()
        pipeline.add_filter(AlphaBetaFilter(alpha=0.8, beta=0.2), "AlphaBeta")
        pipeline.add_filter(MovingAverageFilter(window_size=3), "Smooth")
        return pipeline
    
    def _create_temperature_pipeline(self) -> DataFilterPipeline:
        """Create pipeline optimized for temperature data"""
        pipeline = DataFilterPipeline()
        pipeline.add_outlier_detector()
        pipeline.add_filter(KalmanFilter1D(process_noise=0.01, measurement_noise=0.1), "Kalman")
        pipeline.add_filter(SavitzkyGolayFilter(window_length=5, polyorder=2), "SavitzkyGolay")
        return pipeline
    
    def _create_pressure_pipeline(self) -> DataFilterPipeline:
        """Create pipeline optimized for pressure data"""
        pipeline = DataFilterPipeline()
        pipeline.add_outlier_detector()
        pipeline.add_filter(KalmanFilter1D(process_noise=0.001, measurement_noise=0.01), "Kalman")
        pipeline.add_filter(MovingAverageFilter(window_size=5), "Smooth")
        return pipeline
    
    def _create_radiation_pipeline(self) -> DataFilterPipeline:
        """Create pipeline optimized for radiation data"""
        pipeline = DataFilterPipeline()
        pipeline.add_outlier_detector()
        pipeline.add_filter(MedianFilter(window_size=3), "Median")
        pipeline.add_filter(AdaptiveFilter(initial_filter_type='kalman'), "Adaptive")
        return pipeline
    
    def _create_gas_pipeline(self) -> DataFilterPipeline:
        """Create pipeline optimized for gas sensor data"""
        pipeline = DataFilterPipeline()
        pipeline.add_outlier_detector()
        pipeline.add_filter(KalmanFilter1D(process_noise=0.05, measurement_noise=0.2), "Kalman")
        pipeline.add_filter(MovingAverageFilter(window_size=7), "Smooth")
        return pipeline
    
    def _create_uv_pipeline(self) -> DataFilterPipeline:
        """Create pipeline optimized for UV data"""
        pipeline = DataFilterPipeline()
        pipeline.add_outlier_detector()
        pipeline.add_filter(MedianFilter(window_size=3), "Median")
        pipeline.add_filter(SavitzkyGolayFilter(window_length=5, polyorder=2), "SavitzkyGolay")
        return pipeline
    
    def _create_magnetic_pipeline(self) -> DataFilterPipeline:
        """Create pipeline optimized for magnetic field data"""
        pipeline = DataFilterPipeline()
        pipeline.add_outlier_detector()
        pipeline.add_filter(KalmanFilter1D(process_noise=0.001, measurement_noise=0.01), "Kalman")
        pipeline.add_filter(MovingAverageFilter(window_size=5), "Smooth")
        return pipeline
    
    def filter_data(self, data: np.ndarray, sensor_type: str = 'generic') -> Dict[str, Any]:
        """
        Filter data based on sensor type
        :param data: Input data array
        :param sensor_type: Type of sensor ('altitude', 'temperature', 'pressure', etc.)
        :return: Dictionary with filtered data and metadata
        """
        original_data = data.copy()
        
        # Select appropriate pipeline
        if sensor_type in self.pipeline_configs:
            pipeline = self.pipeline_configs[sensor_type]
            filtered_data = pipeline.process(data)
        else:
            # Use generic pipeline
            pipeline = DataFilterPipeline()
            pipeline.add_outlier_detector()
            pipeline.add_filter(KalmanFilter1D(), "Kalman")
            filtered_data = pipeline.process(data)
        
        # Calculate quality metrics
        noise_reduction = self._calculate_noise_reduction(original_data, filtered_data)
        smoothness = self._calculate_smoothness(filtered_data)
        
        return {
            'filtered_data': filtered_data,
            'original_data': original_data,
            'sensor_type': sensor_type,
            'pipeline_used': sensor_type if sensor_type in self.pipeline_configs else 'generic',
            'noise_reduction_db': noise_reduction,
            'smoothness': smoothness,
            'timestamp': datetime.now()
        }
    
    def _calculate_noise_reduction(self, original: np.ndarray, filtered: np.ndarray) -> float:
        """Calculate noise reduction in decibels"""
        original_power = np.mean(original ** 2)
        filtered_power = np.mean(filtered ** 2)
        
        if filtered_power == 0:
            return float('inf')
        
        if original_power == 0:
            return 0
        
        return 10 * np.log10(original_power / filtered_power)
    
    def _calculate_smoothness(self, data: np.ndarray) -> float:
        """Calculate smoothness metric based on second derivative"""
        if len(data) < 3:
            return 0.0
        
        # Calculate second derivative approximation
        second_deriv = np.diff(data, n=2)
        smoothness = 1.0 / (1.0 + np.mean(second_deriv ** 2))
        return smoothness
    
    def get_filter_status(self) -> Dict[str, Any]:
        """Get status of all filters"""
        status = {}
        for name, filter_obj in self.filters.items():
            status[name] = {
                'type': type(filter_obj).__name__,
                'initialized': True
            }
        
        return status


# Example usage and testing
if __name__ == "__main__":
    # Create test data with noise and outliers
    t = np.linspace(0, 10, 100)
    clean_signal = 10 * np.sin(0.5 * t) + 5 * np.cos(0.2 * t)
    noise = np.random.normal(0, 0.5, len(t))
    outliers = np.zeros_like(t)
    outliers[10:12] = 5  # Add some outliers
    outliers[50:51] = -4
    noisy_signal = clean_signal + noise + outliers
    
    # Test individual filters
    print("Testing individual filters...")
    
    # Kalman filter
    kf = KalmanFilter1D(process_noise=0.1, measurement_noise=0.5)
    kf_result = np.array([kf.update(x) for x in noisy_signal])
    print(f"Kalman filter applied, final estimate: {kf_result[-1]:.2f}")
    
    # Moving average
    ma = MovingAverageFilter(window_size=5)
    ma_result = ma.filter(noisy_signal)
    print(f"Moving average applied")
    
    # Median filter
    med = MedianFilter(window_size=3)
    med_result = med.filter(noisy_signal)
    print(f"Median filter applied")
    
    # Outlier detector
    od = OutlierDetector(method='mad', threshold=2.0)
    cleaned_signal, outlier_mask = od.detect_and_clean(noisy_signal)
    print(f"Outlier detection applied, {sum(outlier_mask)} outliers detected")
    
    # Test pipeline
    print("\nTesting filter pipeline...")
    pipeline = DataFilterPipeline()
    pipeline.add_outlier_detector()
    pipeline.add_filter(KalmanFilter1D(process_noise=0.05, measurement_noise=0.3), "Kalman")
    pipeline.add_filter(MovingAverageFilter(window_size=3), "MovingAvg")
    
    pipeline_result = pipeline.process(noisy_signal)
    print(f"Pipeline applied successfully")
    
    # Test main engine
    print("\nTesting main filter engine...")
    engine = AdvancedDataFilterEngine()
    result = engine.filter_data(noisy_signal, sensor_type='temperature')
    print(f"Engine applied, noise reduction: {result['noise_reduction_db']:.2f} dB")
    print(f"Smoothness: {result['smoothness']:.3f}")
    
    print("All filter tests completed successfully!")