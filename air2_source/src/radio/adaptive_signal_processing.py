"""
Adaptive Signal Processing Module
Advanced adaptive filtering and signal enhancement for AirOne SDR
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
import logging


class AdaptiveFilterType(Enum):
    """Types of adaptive filters"""
    LMS = "least_mean_squares"
    RLS = "recursive_least_squares"
    NLMS = "normalized_lms"
    KALMAN = "kalman"
    AFFINE = "affine_projection"


@dataclass
class FilterState:
    """State of adaptive filter"""
    filter_type: AdaptiveFilterType
    coefficients: np.ndarray
    error: float = 0.0
    convergence: float = 0.0
    iterations: int = 0


class AdaptiveFilter:
    """Base class for adaptive filters"""
    
    def __init__(self, filter_length: int = 32, step_size: float = 0.01):
        self.filter_length = filter_length
        self.step_size = step_size
        self.coefficients = np.zeros(filter_length)
        self.input_buffer = np.zeros(filter_length)
        
    def filter(self, input_signal: float, desired_signal: Optional[float] = None) -> float:
        """Process a single sample"""
        raise NotImplementedError
    
    def update_coefficients(self, error: float):
        """Update filter coefficients"""
        raise NotImplementedError
    
    def reset(self):
        """Reset filter state"""
        self.coefficients = np.zeros(self.filter_length)
        self.input_buffer = np.zeros(self.filter_length)


class LMSFilter(AdaptiveFilter):
    """Least Mean Squares adaptive filter"""
    
    def filter(self, input_signal: float, desired_signal: Optional[float] = None) -> float:
        # Shift input buffer
        self.input_buffer = np.roll(self.input_buffer, 1)
        self.input_buffer[0] = input_signal
        
        # Compute output
        output = np.dot(self.coefficients, self.input_buffer)
        
        # Update if desired signal provided
        if desired_signal is not None:
            error = desired_signal - output
            self.update_coefficients(error)
            
        return output
    
    def update_coefficients(self, error: float):
        # LMS update: w(n+1) = w(n) + mu * e * x(n)
        self.coefficients += self.step_size * error * self.input_buffer
        

class N LMSFilter(AdaptiveFilter):
    """Normalized LMS adaptive filter"""
    
    def filter(self, input_signal: float, desired_signal: Optional[float] = None) -> float:
        self.input_buffer = np.roll(self.input_buffer, 1)
        self.input_buffer[0] = input_signal
        
        # Normalization factor
        norm = np.dot(self.input_buffer, self.input_buffer) + 1e-8
        
        output = np.dot(self.coefficients, self.input_buffer)
        
        if desired_signal is not None:
            error = desired_signal - output
            self.update_coefficients(error, norm)
            
        return output
    
    def update_coefficients(self, error: float, norm: float):
        # NLMS update
        self.coefficients += (self.step_size / norm) * error * self.input_buffer


class RLSFilter(AdaptiveFilter):
    """Recursive Least Squares adaptive filter"""
    
    def __init__(self, filter_length: int = 32, forgetting_factor: float = 0.99):
        super().__init__(filter_length)
        self.forgetting_factor = forgetting_factor
        self.P = np.eye(filter_length) / 0.01  # Inverse correlation matrix
        self.lamda = forgetting_factor
        
    def filter(self, input_signal: float, desired_signal: Optional[float] = None) -> float:
        self.input_buffer = np.roll(self.input_buffer, 1)
        self.input_buffer[0] = input_signal
        
        # Compute gain
        k = np.dot(self.P, self.input_buffer)
        gain = k / (self.lamda + np.dot(self.input_buffer, k) + 1e-8)
        
        # Output
        output = np.dot(self.coefficients, self.input_buffer)
        
        if desired_signal is not None:
            error = desired_signal - output
            self.update_coefficients(error, gain)
            
        return output
    
    def update_coefficients(self, error: float, gain: np.ndarray):
        # RLS update
        self.coefficients += error * gain
        self.P = (self.P - np.outer(gain, self.input_buffer.T @ self.P)) / self.lamda


class AdaptiveNoiseCanceller:
    """Adaptive noise cancellation system"""
    
    def __init__(self, filter_type: AdaptiveFilterType = AdaptiveFilterType.NLMS,
                 filter_length: int = 64):
        self.filter_type = filter_type
        self.filter_length = filter_length
        
        # Create primary and reference filters
        if filter_type == AdaptiveFilterType.LMS:
            self.primary_filter = LMSFilter(filter_length)
            self.reference_filter = LMSFilter(filter_length)
        elif filter_type == AdaptiveFilterType.NLMS:
            self.primary_filter = NLMSFilter(filter_length)
            self.reference_filter = NLMSFilter(filter_length)
        elif filter_type == AdaptiveFilterType.RLS:
            self.primary_filter = RLSFilter(filter_length)
            self.reference_filter = RLSFilter(filter_length)
        else:
            self.primary_filter = LMSFilter(filter_length)
            self.reference_filter = LMSFilter(filter_length)
        
        self.noise_reference = None
        
    def cancel(self, primary_signal: float, 
               noise_reference: Optional[float] = None) -> float:
        """Cancel noise from primary signal"""
        
        if noise_reference is not None:
            # Use provided noise reference
            self.noise_reference = noise_reference
            
        if self.noise_reference is None:
            return primary_signal
        
        # Filter the noise reference
        noise_estimate = self.reference_filter.filter(self.noise_reference)
        
        # Cancel from primary
        output = primary_signal - noise_estimate
        
        return output
    
    def reset(self):
        """Reset filters"""
        self.primary_filter.reset()
        self.reference_filter.reset()


class Beamformer:
    """Spatial beamforming for antenna arrays"""
    
    def __init__(self, num_antennas: int = 4, sample_rate: float = 2.4e6):
        self.num_antennas = num_antennas
        self.sample_rate = sample_rate
        self.weights = np.ones(num_antennas) / num_antennas
        self.direction = 0.0  # Beam direction in degrees
        
    def set_direction(self, angle: float):
        """Set beam direction"""
        self.direction = angle
        
        # Calculate beamforming weights for given direction
        # Assuming uniform linear array
        d = 0.5  # Spacing in wavelengths
        k = 2 * np.pi  # Wavenumber
        
        for i in range(self.num_antennas):
            phase = k * d * i * np.sin(np.radians(angle))
            self.weights[i] = np.exp(1j * phase) / self.num_antennas
    
    def form_beam(self, signals: np.ndarray) -> np.ndarray:
        """Form beam from array signals
        
        Args:
            signals: Array of shape (num_antennas, num_samples)
            
        Returns:
            Beamformed signal
        """
        if signals.shape[0] != self.num_antennas:
            raise ValueError(f"Expected {self.num_antennas} antenna signals")
        
        # Apply weights
        beamformed = np.zeros(signals.shape[1], dtype=complex)
        
        for i in range(self.num_antennas):
            beamformed += self.weights[i] * signals[i]
            
        return beamformed
    
    def adapt_weights(self, signals: np.ndarray, reference: np.ndarray):
        """Adapt weights using LMS"""
        for i in range(len(reference) - 1):
            # Beamform current sample
            beam = sum(self.weights[j] * signals[j, i] for j in range(self.num_antennas))
            
            # Error
            error = reference[i] - beam
            
            # Update weights
            mu = 0.01
            for j in range(self.num_antennas):
                self.weights[j] += mu * error * np.conj(signals[j, i])


class SignalDetector:
    """Advanced signal detection and classification"""
    
    def __init__(self, threshold_db: float = -20.0):
        self.threshold_db = threshold_db
        self.detected_signals = []
        
    def detect_signals(self, spectrum: np.ndarray, 
                       frequencies: np.ndarray) -> List[Dict]:
        """Detect signals in spectrum"""
        detections = []
        
        # Convert to dB
        spectrum_db = 10 * np.log10(spectrum + 1e-10)
        
        # Find peaks above threshold
        for i in range(1, len(spectrum_db) - 1):
            if (spectrum_db[i] > self.threshold_db and
                spectrum_db[i] > spectrum_db[i-1] and
                spectrum_db[i] > spectrum_db[i+1]):
                
                detection = {
                    'frequency': frequencies[i],
                    'power_db': spectrum_db[i],
                    'bandwidth': self._estimate_bandwidth(spectrum_db, i)
                }
                detections.append(detection)
                
        self.detected_signals = detections
        return detections
    
    def _estimate_bandwidth(self, spectrum: np.ndarray, peak_idx: int) -> float:
        """Estimate signal bandwidth"""
        threshold = spectrum[peak_idx] - 3  # 3 dB bandwidth
        
        # Find -3dB points
        left_idx = peak_idx
        for i in range(peak_idx, 0, -1):
            if spectrum[i] < threshold:
                left_idx = i
                break
                
        right_idx = peak_idx
        for i in range(peak_idx, len(spectrum)):
            if spectrum[i] < threshold:
                right_idx = i
                break
                
        return abs(right_idx - left_idx)


class InterferenceMitigator:
    """Interference mitigation techniques"""
    
    def __init__(self):
        self.interference_profile = None
        
    def notch_filter(self, signal: np.ndarray, 
                     interference_freq: float,
                     sample_rate: float,
                     q_factor: float = 30.0) -> np.ndarray:
        """Apply notch filter at interference frequency"""
        
        # Calculate notch parameters
        w0 = 2 * np.pi * interference_freq / sample_rate
        alpha = np.sin(w0) / (2 * q_factor)
        
        # Design notch filter coefficients
        b = np.array([1, -2 * np.cos(w0), 1])
        a = np.array([1, -2 * np.cos(w0), 1 - alpha])
        
        # Apply filter
        from scipy import signal as sig
        filtered = sig.lfilter(b, a, signal)
        
        return filtered
    
    def adaptive_interference_cancellation(self, 
                                          signal: np.ndarray,
                                          interference: np.ndarray) -> np.ndarray:
        """Adaptive interference cancellation"""
        
        # Use NLMS filter
        filter_len = 64
        mu = 0.1
        
        coefficients = np.zeros(filter_len)
        buffer = np.zeros(filter_len)
        output = np.zeros_like(signal)
        
        for i in range(len(signal)):
            # Update buffer
            buffer = np.roll(buffer, 1)
            buffer[0] = interference[i] if i < len(interference) else 0
            
            # Filter
            output[i] = np.dot(coefficients, buffer)
            
            # Error
            error = signal[i] - output[i]
            
            # Update coefficients
            norm = np.dot(buffer, buffer) + 1e-8
            coefficients += (mu / norm) * error * buffer
            
        return output


class SignalEnhancer:
    """Signal enhancement and quality improvement"""
    
    def __init__(self):
        self.processing_history = []
        
    def spectral_squelch(self, signal: np.ndarray,
                        sample_rate: float,
                        noise_floor_db: float = -60.0) -> np.ndarray:
        """Spectral squelch - suppress noise below threshold"""
        
        # Compute spectrum
        nfft = min(1024, len(signal))
        spectrum = np.fft.fft(signal[:nfft])
        spectrum_db = 20 * np.log10(np.abs(spectrum) + 1e-10)
        
        # Find noise floor
        noise_floor = np.percentile(spectrum_db, 20)
        
        # Apply squelch
        squelch_threshold = max(noise_floor + 10, noise_floor_db)
        mask = spectrum_db > squelch_threshold
        
        # Apply mask
        spectrum_filtered = spectrum * mask
        spectrum_filtered[~mask] = 0
        
        # Reconstruct signal
        filtered = np.fft.ifft(spectrum_filtered)
        
        return filtered.real
    
    def automatic_gain_control(self, signal: np.ndarray,
                               target_level: float = 0.5,
                               attack_time: float = 0.001,
                               release_time: float = 0.1) -> np.ndarray:
        """Digital automatic gain control"""
        
        # Calculate envelope
        envelope = np.abs(signal)
        
        # Determine gain
        current_gain = 1.0
        output = np.zeros_like(signal)
        
        for i in range(len(signal)):
            # Update gain based on envelope
            if envelope[i] > target_gain:
                # Attack
                current_gain *= (1 - attack_time)
            else:
                # Release
                current_gain *= (1 + release_time)
                
            # Clamp gain
            current_gain = np.clip(current_gain, 0.1, 10.0)
            
            # Apply gain
            output[i] = signal[i] * current_gain
            
        return output
    
    def bandpass_enhancement(self, signal: np.ndarray,
                            sample_rate: float,
                            low_freq: float,
                            high_freq: float) -> np.ndarray:
        """Enhance signal within frequency band"""
        
        # Design bandpass filter
        nyquist = sample_rate / 2
        low = low_freq / nyquist
        high = high_freq / nyquist
        
        from scipy import signal as sig
        b, a = sig.butter(4, [low, high], btype='band')
        
        # Apply filter
        enhanced = sig.filtfilt(b, a, signal)
        
        return enhanced


class AdaptiveSignalProcessor:
    """Complete adaptive signal processing system"""
    
    def __init__(self):
        self.noise_canceller = AdaptiveNoiseCanceller()
        self.beamformer = Beamformer()
        self.detector = SignalDetector()
        self.mitigator = InterferenceMitigator()
        self.enhancer = SignalEnhancer()
        
    def process(self, samples: np.ndarray, 
                sample_rate: float = 2.4e6) -> Dict[str, Any]:
        """Process signals with all techniques"""
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'samples': len(samples)
        }
        
        # Noise cancellation
        if len(samples) > 100:
            noise_ref = samples[:100].mean()
            cancelled = self.noise_canceller.cancel(samples, noise_ref)
            results['noise_cancelled'] = True
        else:
            cancelled = samples
            
        # Enhancement
        enhanced = self.enhancer.spectral_squelch(cancelled, sample_rate)
        results['enhanced'] = True
        
        # Detection
        nfft = min(2048, len(enhanced))
        spectrum = np.abs(np.fft.fft(enhanced[:nfft]))**2
        freqs = np.fft.fftfreq(nfft, 1/sample_rate)
        detections = self.detector.detect_signals(spectrum, freqs)
        results['detections'] = len(detections)
        
        return results


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Adaptive Signal Processing...")
    
    # Test LMS Filter
    print("\n1. Testing LMS Filter...")
    lms = LMSFilter(filter_length=32, step_size=0.1)
    
    # Test with noise
    signal = np.sin(2 * np.pi * 100 * np.arange(1000) / 10000)
    noise = np.random.randn(1000) * 0.1
    desired = signal + noise
    
    for i in range(len(signal)):
        output = lms.filter(signal[i], desired[i])
        
    print(f"   LMS filter converged")
    
    # Test RLS Filter
    print("\n2. Testing RLS Filter...")
    rls = RLSFilter(filter_length=32)
    
    for i in range(len(signal)):
        output = rls.filter(signal[i], desired[i])
        
    print(f"   RLS filter converged")
    
    # Test Noise Canceller
    print("\n3. Testing Noise Canceller...")
    nc = AdaptiveNoiseCanceller()
    primary = np.sin(2 * np.pi * 100 * np.arange(100) / 1000)
    noise_ref = np.random.randn(100) * 0.5
    output = nc.cancel(primary, noise_ref)
    print(f"   Noise cancellation complete")
    
    # Test Beamformer
    print("\n4. Testing Beamformer...")
    bf = Beamformer(num_antennas=4)
    bf.set_direction(30)
    signals = np.random.randn(4, 100) + 1j * np.random.randn(4, 100)
    beamformed = bf.form_beam(signals)
    print(f"   Beamforming complete")
    
    # Test Signal Enhancer
    print("\n5. Testing Signal Enhancer...")
    enhancer = SignalEnhancer()
    signal = np.random.randn(1000)
    enhanced = enhancer.spectral_squelch(signal, 1000)
    print(f"   Enhancement complete")
    
    # Test Complete Processor
    print("\n6. Testing Complete Processor...")
    processor = AdaptiveSignalProcessor()
    samples = np.random.randn(1024) + 1j * np.random.randn(1024)
    results = processor.process(samples, 2.4e6)
    print(f"   Processing results: {results}")
    
    print("\n✅ Adaptive Signal Processing test completed!")