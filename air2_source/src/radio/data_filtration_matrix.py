"""
Data Filtration Matrix Calculation Module
Advanced matrix-based signal filtering and correlation for AirOne SDR/Telemetry
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import threading
import math


@dataclass
class FiltrationMatrix:
    """Matrix for data filtration operations"""
    matrix: np.ndarray
    filter_type: str
    center_frequency: float
    bandwidth: float
    created_at: datetime


@dataclass
class CorrelationResult:
    """Correlation analysis result"""
    lag: int
    correlation: float
    significance: float


class DataFiltrationMatrix:
    """Advanced data filtration matrix calculator for SDR and telemetry"""
    
    def __init__(self, matrix_size: int = 64):
        """
        Initialize Data Filtration Matrix
        
        Args:
            matrix_size: Size of the filtration matrix (default 64x64)
        """
        self.matrix_size = matrix_size
        self.matrices: Dict[str, FiltrationMatrix] = {}
        self._lock = threading.Lock()
        
    def create_bandpass_matrix(self, center_freq: float, bandwidth: float, 
                               sample_rate: float) -> FiltrationMatrix:
        """
        Create a bandpass filtration matrix
        
        Args:
            center_freq: Center frequency in Hz
            bandwidth: Bandwidth in Hz
            sample_rate: Sample rate in Hz
            
        Returns:
            FiltrationMatrix object
        """
        with self._lock:
            # Create frequency grid
            freq = np.fft.fftfreq(self.matrix_size, 1/sample_rate)
            
            # Create bandpass response
            filter_response = np.zeros(self.matrix_size)
            low_freq = center_freq - bandwidth / 2
            high_freq = center_freq + bandwidth / 2
            
            for i, f in enumerate(freq):
                if low_freq <= abs(f) <= high_freq:
                    filter_response[i] = 1.0
                    
            # Create 2D matrix from 1D response
            matrix = np.outer(filter_response, filter_response)
            
            # Normalize
            matrix = matrix / np.max(np.abs(matrix)) if np.max(np.abs(matrix)) > 0 else matrix
            
            filt_matrix = FiltrationMatrix(
                matrix=matrix,
                filter_type="bandpass",
                center_frequency=center_freq,
                bandwidth=bandwidth,
                created_at=datetime.now()
            )
            
            key = f"bp_{center_freq/1e6:.2f}MHz_{bandwidth/1e3:.1f}kHz"
            self.matrices[key] = filt_matrix
            
            return filt_matrix
    
    def create_adaptive_matrix(self, signal_data: np.ndarray, 
                                noise_estimate: float) -> FiltrationMatrix:
        """
        Create adaptive filtration matrix based on signal characteristics
        
        Args:
            signal_data: Input signal samples
            noise_estimate: Estimated noise level
            
        Returns:
            FiltrationMatrix object
        """
        with self._lock:
            # Compute signal statistics
            signal_power = np.mean(np.abs(signal_data)**2)
            snr = signal_power / (noise_estimate**2 + 1e-10)
            
            # Compute autocorrelation matrix
            n = min(len(signal_data), self.matrix_size)
            autocorr = np.correlate(signal_data[:n], signal_data[:n], mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Create Toeplitz matrix
            matrix = np.zeros((self.matrix_size, self.matrix_size))
            for i in range(min(len(autocorr), self.matrix_size)):
                for j in range(min(len(autocorr), self.matrix_size)):
                    if i < len(autocorr) and j < len(autocorr):
                        matrix[i, j] = autocorr[abs(i-j)] if abs(i-j) < len(autocorr) else 0
            
            # Apply SNR-based weighting
            weight = min(snr / 100.0, 1.0)  # Cap at 1.0
            matrix = matrix * weight + np.eye(self.matrix_size) * (1 - weight) * 0.1
            
            # Normalize
            matrix = matrix / np.linalg.norm(matrix)
            
            filt_matrix = FiltrationMatrix(
                matrix=matrix,
                filter_type="adaptive",
                center_frequency=snr,
                bandwidth=noise_estimate,
                created_at=datetime.now()
            )
            
            key = f"adaptive_{datetime.now().timestamp()}"
            self.matrices[key] = filt_matrix
            
            return filt_matrix
    
    def apply_matrix_filter(self, data: np.ndarray, 
                            matrix: FiltrationMatrix) -> np.ndarray:
        """
        Apply filtration matrix to signal data
        
        Args:
            data: Input signal data
            matrix: FiltrationMatrix to apply
            
        Returns:
            Filtered signal
        """
        # Flatten if multidimensional
        if data.ndim > 1:
            original_shape = data.shape
            data = data.flatten()
        else:
            original_shape = None
            
        # Pad to matrix size
        if len(data) < self.matrix_size:
            data = np.pad(data, (0, self.matrix_size - len(data)), mode='constant')
        elif len(data) > self.matrix_size:
            data = data[:self.matrix_size]
            
        # Apply matrix multiplication
        filtered = np.dot(matrix.matrix, data)
        
        # Reshape if needed
        if original_shape and len(original_shape) > 1:
            # Try to restore approximate shape
            side = int(np.sqrt(len(filtered)))
            if side * side == len(filtered):
                filtered = filtered.reshape((side, side))
                
        return filtered[:len(data) if original_shape is None else len(data)]
    
    def compute_correlation_matrix(self, signals: List[np.ndarray]) -> np.ndarray:
        """
        Compute correlation matrix between multiple signals
        
        Args:
            signals: List of signal arrays
            
        Returns:
            Correlation matrix (N x N)
        """
        n = len(signals)
        corr_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    # Normalize signals
                    si = (signals[i] - np.mean(signals[i])) / (np.std(signals[i]) + 1e-10)
                    sj = (signals[j] - np.mean(signals[j])) / (np.std(signals[j]) + 1e-10)
                    
                    # Compute correlation
                    min_len = min(len(si), len(sj))
                    corr = np.dot(si[:min_len], sj[:min_len]) / min_len
                    corr_matrix[i, j] = corr
                    
        return corr_matrix
    
    def perform_time_frequency_analysis(self, signal: np.ndarray, 
                                         sample_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform time-frequency analysis using STFT
        
        Args:
            signal: Input signal
            sample_rate: Sample rate
            
        Returns:
            Tuple of (frequencies, time, spectrogram)
        """
        # Compute STFT
        window_size = min(256, len(signal) // 4)
        hop_size = window_size // 4
        
        frequencies, times, spec = [], [], []
        
        for i in range(0, len(signal) - window_size, hop_size):
            segment = signal[i:i+window_size]
            
            # Apply window
            windowed = segment * np.hanning(window_size)
            
            # Compute FFT
            fft_result = np.fft.fft(windowed)
            freqs = np.fft.fftfreq(window_size, 1/sample_rate)
            
            frequencies.append(freqs[:window_size//2])
            times.append(i / sample_rate)
            spec.append(np.abs(fft_result[:window_size//2]))
            
        return (np.array(frequencies) if frequencies else np.array([]), 
                np.array(times) if times else np.array([]),
                np.array(spec) if spec else np.array([]))
    
    def detect_anomalies(self, data: np.ndarray, threshold: float = 3.0) -> List[int]:
        """
        Detect anomalies in signal data using statistical methods
        
        Args:
            data: Input signal data
            threshold: Standard deviation threshold for anomaly detection
            
        Returns:
            List of indices where anomalies were detected
        """
        mean = np.mean(data)
        std = np.std(data)
        
        anomalies = []
        for i, val in enumerate(data):
            z_score = abs((val - mean) / (std + 1e-10))
            if z_score > threshold:
                anomalies.append(i)
                
        return anomalies
    
    def compute_spectral_coherence(self, signal1: np.ndarray, 
                                   signal2: np.ndarray,
                                   fs: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute spectral coherence between two signals
        
        Args:
            signal1: First signal
            signal2: Second signal
            fs: Sampling frequency
            
        Returns:
            Tuple of (frequencies, coherence)
        """
        # Compute cross-spectral density
        n = min(len(signal1), len(signal2))
        
        # Window the signals
        window = np.hanning(n)
        s1 = signal1[:n] * window
        s2 = signal2[:n] * window
        
        # Compute FFTs
        fft1 = np.fft.fft(s1)
        fft2 = np.fft.fft(s2)
        
        # Compute cross-spectral density
        csd = fft1 * np.conj(fft2)
        
        # Compute power spectral densities
        psd1 = np.abs(fft1)**2
        psd2 = np.abs(fft2)**2
        
        # Compute coherence
        coherence = np.abs(csd)**2 / (psd1 * psd2 + 1e-10)
        
        frequencies = np.fft.fftfreq(n, 1/fs)
        
        return frequencies[:n//2], coherence[:n//2]


class CorrelationAnalyzer:
    """DeepSeek AI-powered correlation analyzer for telemetry data"""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.correlation_models: Dict[str, Any] = {}
        
    def analyze_telemetry_correlations(self, telemetry_packets: List[Dict]) -> Dict[str, Any]:
        """
        Analyze correlations between different telemetry parameters
        
        Args:
            telemetry_packets: List of telemetry packet dictionaries
            
        Returns:
            Correlation analysis results
        """
        if not telemetry_packets:
            return {}
            
        # Extract parameter arrays
        parameters = {}
        for packet in telemetry_packets:
            for key, value in packet.items():
                if isinstance(value, (int, float)) and key not in parameters:
                    parameters[key] = []
                if key in parameters:
                    parameters[key].append(value)
        
        # Compute correlation matrix
        corr_matrix = np.zeros((len(parameters), len(parameters)))
        param_names = list(parameters.keys())
        
        for i, pi in enumerate(param_names):
            for j, pj in enumerate(param_names):
                if len(parameters[pi]) > 1 and len(parameters[pj]) > 1:
                    min_len = min(len(parameters[pi]), len(parameters[pj]))
                    corr = np.corrcoef(
                        np.array(parameters[pi][:min_len]),
                        np.array(parameters[pj][:min_len])
                    )[0, 1]
                    corr_matrix[i, j] = corr if not np.isnan(corr) else 0.0
                    
        # Find strongest correlations
        correlations = []
        for i in range(len(param_names)):
            for j in range(i+1, len(param_names)):
                if abs(corr_matrix[i, j]) > 0.7:  # Strong correlation threshold
                    correlations.append({
                        'parameter1': param_names[i],
                        'parameter2': param_names[j],
                        'correlation': corr_matrix[i, j],
                        'strength': 'strong' if abs(corr_matrix[i, j]) > 0.9 else 'moderate'
                    })
        
        return {
            'correlation_matrix': corr_matrix.tolist(),
            'parameter_names': param_names,
            'strong_correlations': sorted(correlations, 
                                          key=lambda x: abs(x['correlation']), 
                                          reverse=True),
            'num_parameters': len(param_names),
            'num_packets': len(telemetry_packets)
        }
    
    def predict_parameter(self, telemetry_history: List[Dict], 
                         target_param: str, 
                         look_ahead: int = 10) -> Tuple[List[float], float]:
        """
        Predict future values of a parameter using linear regression
        
        Args:
            telemetry_history: Historical telemetry data
            target_param: Parameter to predict
            look_ahead: Number of steps to predict
            
        Returns:
            Tuple of (predicted values, confidence)
        """
        if not telemetry_history:
            return [], 0.0
            
        # Extract target parameter values
        values = []
        for packet in telemetry_history:
            if target_param in packet:
                values.append(packet[target_param])
        
        if len(values) < 10:
            return [], 0.0
            
        # Use simple linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Fit polynomial
        coeffs = np.polyfit(x, y, 1)
        
        # Predict future values
        future_x = np.arange(len(values), len(values) + look_ahead)
        predictions = np.polyval(coeffs, future_x)
        
        # Calculate confidence (R-squared)
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))
        
        return predictions.tolist(), max(0.0, min(1.0, r_squared))
    
    def detect_parameter_drifts(self, telemetry_history: List[Dict], 
                                window_size: int = 50,
                                drift_threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect parameter value drifts over time
        
        Args:
            telemetry_history: Historical telemetry data
            window_size: Window size for comparison
            drift_threshold: Standard deviation threshold for drift
            
        Returns:
            List of detected drifts
        """
        drifts = []
        
        if len(telemetry_history) < window_size * 2:
            return drifts
            
        for param in telemetry_history[0].keys():
            if not isinstance(telemetry_history[0][param], (int, float)):
                continue
                
            values = [p[param] for p in telemetry_history if param in p]
            
            if len(values) < window_size * 2:
                continue
            
            # Compute rolling statistics
            for i in range(window_size, len(values) - window_size):
                window1 = values[i-window_size:i]
                window2 = values[i:i+window_size]
                
                mean1, std1 = np.mean(window1), np.std(window1)
                mean2, std2 = np.mean(window2), np.std(window2)
                
                # Check for significant drift
                pooled_std = np.sqrt((std1**2 + std2**2) / 2)
                if pooled_std > 0:
                    z_score = abs(mean2 - mean1) / pooled_std
                    
                    if z_score > drift_threshold:
                        drifts.append({
                            'parameter': param,
                            'drift_start_index': i,
                            'mean_before': mean1,
                            'mean_after': mean2,
                            'z_score': z_score,
                            'direction': 'increase' if mean2 > mean1 else 'decrease'
                        })
                        
        return drifts
    
    def compute_cross_correlation(self, signal1: np.ndarray, 
                                   signal2: np.ndarray,
                                   max_lag: int = 100) -> List[CorrelationResult]:
        """
        Compute cross-correlation between two signals
        
        Args:
            signal1: First signal
            signal2: Second signal
            max_lag: Maximum lag to compute
            
        Returns:
            List of correlation results
        """
        results = []
        
        # Normalize signals
        s1 = (signal1 - np.mean(signal1)) / (np.std(signal1) + 1e-10)
        s2 = (signal2 - np.mean(signal2)) / (np.std(signal2) + 1e-10)
        
        min_len = min(len(s1), len(s2), max_lag * 2)
        
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                corr = np.dot(s1[:min_len], s2[-min_len:])
            elif lag > 0:
                corr = np.dot(s1[-min_len:], s2[:min_len])
            else:
                corr = np.dot(s1[:min_len], s2[:min_len])
                
            corr /= min_len
            
            # Calculate simple significance
            significance = 1.0 - abs(corr)  # Higher correlation = lower significance for being random
            
            results.append(CorrelationResult(
                lag=lag,
                correlation=corr,
                significance=significance
            ))
            
        return results
    
    def generate_correlation_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generate human-readable correlation report
        
        Args:
            analysis: Analysis results from analyze_telemetry_correlations
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("TELEMETRY CORRELATION ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"\nAnalyzed {analysis.get('num_packets', 0)} packets")
        report.append(f"Found {analysis.get('num_parameters', 0)} parameters")
        
        strong_corr = analysis.get('strong_correlations', [])
        if strong_corr:
            report.append(f"\n{len(strong_corr)} STRONG CORRELATIONS DETECTED:")
            report.append("-" * 40)
            for corr in strong_corr[:10]:  # Top 10
                report.append(f"  {corr['parameter1']} <-> {corr['parameter2']}")
                report.append(f"    Correlation: {corr['correlation']:.4f}")
                report.append(f"    Strength: {corr['strength']}")
        else:
            report.append("\nNo strong correlations found.")
            
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    # Test Data Filtration Matrix
    print("Testing Data Filtration Matrix...")
    
    # Create matrix calculator
    dfm = DataFiltrationMatrix(matrix_size=64)
    
    # Create bandpass matrix
    bp_matrix = dfm.create_bandpass_matrix(433.92e6, 100e3, 2.4e6)
    print(f"Created bandpass matrix: {bp_matrix.filter_type}")
    
    # Test with sample data
    test_signal = np.random.randn(1024) + 1j * np.random.randn(1024)
    filtered = dfm.apply_matrix_filter(test_signal, bp_matrix)
    print(f"Filtered signal length: {len(filtered)}")
    
    # Test correlation analyzer
    print("\nTesting Correlation Analyzer...")
    
    ca = CorrelationAnalyzer()
    
    # Create sample telemetry data
    telemetry = []
    for i in range(100):
        telemetry.append({
            'altitude': 1000 + i * 0.5 + np.random.randn() * 10,
            'velocity': 50 + i * 0.1 + np.random.randn() * 2,
            'temperature': 25 + np.sin(i * 0.1) * 5 + np.random.randn() * 0.5,
            'pressure': 101325 - i * 10 + np.random.randn() * 100
        })
    
    # Analyze correlations
    analysis = ca.analyze_telemetry_correlations(telemetry)
    print(f"\nAnalysis result keys: {list(analysis.keys())}")
    print(f"Strong correlations found: {len(analysis.get('strong_correlations', []))}")
    
    # Generate report
    report = ca.generate_correlation_report(analysis)
    print(f"\n{report}")
    
    # Test prediction
    predictions, confidence = ca.predict_parameter(telemetry, 'altitude', look_ahead=10)
    print(f"\nAltitude prediction confidence: {confidence:.4f}")
    print(f"Predicted values: {predictions[:3]}...")
    
    print("\n✅ Data Filtration Matrix Module test completed!")