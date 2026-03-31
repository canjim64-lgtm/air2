"""
Channel Estimation and Equalization Module
Advanced channel modeling and equalization for SDR communication
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import threading
import logging


@dataclass
class ChannelEstimate:
    """Channel frequency response estimate"""
    h: np.ndarray  # Channel impulse response
    snr: float
    timestamp: float
    method: str


class ChannelEstimator:
    """Estimate channel characteristics"""
    
    def __init__(self, num_taps: int = 32):
        self.num_taps = num_taps
        self.channel_history = []
        
    def estimate_ls(self, tx_signal: np.ndarray, 
                    rx_signal: np.ndarray,
                    pilot_positions: List[int]) -> ChannelEstimate:
        """Least squares channel estimation"""
        
        # Extract pilot symbols
        tx_pilots = tx_signal[pilot_positions]
        rx_pilots = rx_signal[pilot_positions]
        
        # LS estimate: H = Y / X
        h_ls = rx_pilots / (tx_pilots + 1e-10)
        
        # Interpolate to full channel
        channel = np.zeros(self.num_taps)
        
        # Simple linear interpolation
        for i in range(len(pilot_positions) - 1):
            start = pilot_positions[i]
            end = pilot_positions[i + 1]
            
            h_start = h_ls[i]
            h_end = h_ls[i + 1]
            
            for j in range(start, min(end, self.num_taps)):
                alpha = (j - start) / (end - start) if end > start else 0
                channel[j] = (1 - alpha) * h_start + alpha * h_end
        
        # Estimate SNR
        signal_power = np.mean(np.abs(tx_signal)**2)
        noise = rx_signal - tx_signal * np.mean(channel)
        noise_power = np.mean(np.abs(noise)**2)
        snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
        
        return ChannelEstimate(
            h=channel,
            snr=snr,
            timestamp=datetime.now().timestamp(),
            method='least_squares'
        )
    
    def estimate_mmse(self, tx_signal: np.ndarray, 
                      rx_signal: np.ndarray,
                      snr_estimate: float = 10.0) -> ChannelEstimate:
        """MMSE channel estimation"""
        
        # Simple MMSE (simplified)
        correlation = np.correlate(rx_signal, tx_signal, mode='full')
        
        # Find peak
        peak_idx = np.argmax(np.abs(correlation))
        
        # Extract channel
        half_len = self.num_taps // 2
        start = max(0, peak_idx - half_len)
        end = min(len(correlation), peak_idx + half_len)
        
        channel = np.zeros(self.num_taps)
        channel[:min(end-start, self.num_taps)] = correlation[start:end]
        
        # Normalize
        channel /= (np.linalg.norm(channel) + 1e-10)
        
        return ChannelEstimate(
            h=channel,
            snr=snr_estimate,
            timestamp=datetime.now().timestamp(),
            method='mmse'
        )
    
    def estimate_dft(self, tx_signal: np.ndarray,
                     rx_signal: np.ndarray) -> ChannelEstimate:
        """DFT-based channel estimation"""
        
        # FFT-based estimation
        N = min(len(tx_signal), len(rx_signal), 1024)
        
        tx_fft = np.fft.fft(tx_signal[:N])
        rx_fft = np.fft.fft(rx_signal[:N])
        
        # Channel in frequency domain
        H = rx_fft / (tx_fft + 1e-10)
        
        # IFFT to get impulse response
        h = np.fft.ifft(H)[:self.num_taps]
        
        # Estimate SNR
        snr = np.mean(np.abs(tx_fft)**2) / (np.mean(np.abs(rx_fft - tx_fft)**2) + 1e-10)
        snr_db = 10 * np.log10(snr)
        
        return ChannelEstimate(
            h=h,
            snr=snr_db,
            timestamp=datetime.now().timestamp(),
            method='dft'
        )


class Equalizer:
    """Channel equalizer"""
    
    def __init__(self, num_taps: int = 32):
        self.num_taps = num_taps
        self.channel = None
        
    def set_channel(self, channel: ChannelEstimate):
        """Set channel estimate"""
        self.channel = channel
        
    def equalize_zf(self, rx_signal: np.ndarray) -> np.ndarray:
        """Zero-forcing equalization"""
        
        if self.channel is None:
            return rx_signal
        
        # Frequency domain equalization
        N = min(len(rx_signal), 1024)
        rx_fft = np.fft.fft(rx_signal[:N])
        
        # Equalize: X = Y / H
        H = np.fft.fft(self.channel.h, N)
        eq_fft = rx_fft / (H + 1e-10)
        
        # IFFT
        equalized = np.fft.ifft(eq_fft)
        
        return equalized
    
    def equalize_mmse(self, rx_signal: np.ndarray, 
                      noise_variance: float = 0.01) -> np.ndarray:
        """MMSE equalization"""
        
        if self.channel is None:
            return rx_signal
        
        N = min(len(rx_signal), 1024)
        rx_fft = np.fft.fft(rx_signal[:N])
        
        # MMSE equalizer: H* / (|H|^2 + sigma^2)
        H = np.fft.fft(self.channel.h, N)
        H_conj = np.conj(H)
        
        mmse_filter = H_conj / (np.abs(H)**2 + noise_variance + 1e-10)
        
        eq_fft = rx_fft * mmse_filter
        
        equalized = np.fft.ifft(eq_fft)
        
        return equalized
    
    def equalize_decision_feedback(self, rx_signal: np.ndarray,
                                    decisions: np.ndarray) -> np.ndarray:
        """Decision feedback equalizer"""
        
        if self.channel is None:
            return rx_signal
        
        # DFE using channel estimate
        equalized = np.zeros_like(rx_signal)
        
        # Forward filter (simplified)
        for i in range(len(rx_signal)):
            if i < self.num_taps:
                equalized[i] = rx_signal[i]
            else:
                # Use decision feedback
                feedback = np.dot(self.channel.h[:min(i, len(self.channel.h))], 
                                 decisions[:min(i, len(decisions))])
                equalized[i] = rx_signal[i] - feedback
        
        return equalized


class AdaptiveEqualizer(Equalizer):
    """Adaptive equalizer with training"""
    
    def __init__(self, num_taps: int = 32, step_size: float = 0.01):
        super().__init__(num_taps)
        self.step_size = step_size
        self.weights = np.zeros(num_taps, dtype=complex)
        self.buffer = np.zeros(num_taps, dtype=complex)
        
    def train(self, rx_signal: np.ndarray, 
              training_sequence: np.ndarray) -> float:
        """Train equalizer with training sequence"""
        
        error_sum = 0
        
        for i in range(len(training_sequence) - self.num_taps):
            # Update buffer
            self.buffer = np.roll(self.buffer, 1)
            self.buffer[0] = rx_signal[i]
            
            # Equalizer output
            output = np.dot(self.weights, self.buffer)
            
            # Error
            error = training_sequence[i] - output
            error_sum += np.abs(error)
            
            # Update weights (LMS)
            self.weights += self.step_size * np.conj(error) * self.buffer
        
        return error_sum / len(training_sequence)
    
    def equalize_adaptive(self, rx_signal: np.ndarray) -> np.ndarray:
        """Adaptive equalization"""
        
        equalized = np.zeros_like(rx_signal)
        
        for i in range(len(rx_signal)):
            # Update buffer
            self.buffer = np.roll(self.buffer, 1)
            self.buffer[0] = rx_signal[i]
            
            # Output
            equalized[i] = np.dot(self.weights, self.buffer)
            
            # Update (simplified)
            self.weights += self.step_size * np.conj(0.1) * self.buffer
        
        return equalized


class ChannelSimulator:
    """Simulate various channel conditions"""
    
    def __init__(self, sample_rate: float = 2.4e6):
        self.sample_rate = sample_rate
        
    def apply_awgn(self, signal: np.ndarray, 
                   snr_db: float) -> np.ndarray:
        """Add AWGN noise"""
        
        signal_power = np.mean(np.abs(signal)**2)
        noise_power = signal_power / (10**(snr_db / 10))
        
        noise = np.sqrt(noise_power / 2) * (
            np.random.randn(len(signal)) + 1j * np.random.randn(len(signal))
        )
        
        return signal + noise
    
    def apply_rayleigh_fading(self, signal: np.ndarray,
                              doppler_hz: float = 10.0) -> np.ndarray:
        """Apply Rayleigh fading"""
        
        # Generate fading coefficient
        t = np.arange(len(signal)) / self.sample_rate
        
        # Doppler frequency
        fd = doppler_hz
        
        # Complex Gaussian process for Rayleigh
        phi = 2 * np.pi * fd * t
        
        # Envelope (Rayleigh distributed)
        sigma = 1.0
        envelope = np.sqrt(-2 * np.log(np.random.rand(len(signal)))) * sigma
        
        # Phase
        phase = np.random.rand(len(signal)) * 2 * np.pi
        
        fading = envelope * np.exp(1j * phase)
        
        return signal * fading
    
    def apply_rician_fading(self, signal: np.ndarray,
                            k_factor: float = 10.0) -> np.ndarray:
        """Apply Rician fading (LOS + scatter)"""
        
        # LOS component
        los = np.exp(1j * np.random.rand(len(signal)) * 2 * np.pi)
        
        # Scatter component (Rayleigh)
        scatter = self.apply_rayleigh_fading(np.ones(len(signal)), 10.0)
        
        # Combine
        fading = (np.sqrt(k_factor) * los + scatter) / np.sqrt(k_factor + 1)
        
        return signal * fading
    
    def apply_multipath(self, signal: np.ndarray,
                        delays: List[float],
                        powers: List[float]) -> np.ndarray:
        """Apply multipath fading"""
        
        output = np.zeros_like(signal)
        
        for delay, power in zip(delays, powers):
            delay_samples = int(delay * self.sample_rate)
            
            if delay_samples < len(signal):
                path = np.roll(signal, delay_samples) * np.sqrt(power)
                output += path
        
        return output
    
    def apply_phase_rotation(self, signal: np.ndarray,
                            phase_noise_rad: float = 0.1) -> np.ndarray:
        """Apply phase noise"""
        
        phase = np.cumsum(np.random.randn(len(signal)) * phase_noise_rad)
        
        return signal * np.exp(1j * phase)
    
    def apply_frequency_offset(self, signal: np.ndarray,
                               offset_hz: float) -> np.ndarray:
        """Apply frequency offset"""
        
        t = np.arange(len(signal)) / self.sample_rate
        
        return signal * np.exp(1j * 2 * np.pi * offset_hz * t)
    
    def apply_timing_offset(self, signal: np.ndarray,
                           offset_samples: float) -> np.ndarray:
        """Apply timing offset (fractional)"""
        
        from scipy import interpolate
        
        t_orig = np.arange(len(signal))
        t_new = t_orig + offset_samples
        
        f = interpolate.interp1d(t_orig, signal.real, kind='linear')
        f_imag = interpolate.interp1d(t_orig, signal.imag, kind='linear')
        
        return f(t_new) + 1j * f_imag(t_new)


class ChannelEstimationSystem:
    """Complete channel estimation and equalization system"""
    
    def __init__(self):
        self.estimator = ChannelEstimator()
        self.equalizer = Equalizer()
        self.adaptive_eq = AdaptiveEqualizer()
        self.simulator = ChannelSimulator()
        
    def process(self, tx_signal: np.ndarray,
                rx_signal: np.ndarray,
                use_adaptive: bool = False) -> Dict[str, Any]:
        """Process through channel estimation and equalization"""
        
        # Estimate channel
        channel_est = self.estimator.estimate_dft(tx_signal, rx_signal)
        
        # Set channel for equalizer
        self.equalizer.set_channel(channel_est)
        
        # Equalize
        if use_adaptive:
            equalized = self.equalizer.equalize_mmse(rx_signal, 0.01)
        else:
            equalized = self.equalizer.equalize_zf(rx_signal)
        
        return {
            'channel': channel_est.h,
            'snr': channel_est.snr,
            'equalized': equalized,
            'method': channel_est.method
        }
    
    def simulate_channel(self, signal: np.ndarray,
                        conditions: Dict[str, Any]) -> np.ndarray:
        """Simulate channel with given conditions"""
        
        output = signal.copy()
        
        if conditions.get('awgn', False):
            output = self.simulator.apply_awgn(output, conditions.get('snr_db', 20))
        
        if conditions.get('rayleigh', False):
            output = self.simulator.apply_rayleigh_fading(output)
        
        if conditions.get('rician', False):
            output = self.simulator.apply_rician_fading(output, conditions.get('k_factor', 10))
        
        if 'delays' in conditions:
            output = self.simulator.apply_multipath(output, 
                                                    conditions['delays'],
                                                    conditions.get('powers', [1.0]))
        
        if 'freq_offset' in conditions:
            output = self.simulator.apply_frequency_offset(output,
                                                            conditions['freq_offset'])
        
        if 'phase_noise' in conditions:
            output = self.simulator.apply_phase_rotation(output,
                                                          conditions['phase_noise'])
        
        return output


# Example usage
if __name__ == "__main__":
    print("Testing Channel Estimation and Equalization...")
    
    # Test Channel Estimator
    print("\n1. Testing Channel Estimator...")
    estimator = ChannelEstimator()
    
    # Generate test signals
    tx = np.random.randn(1024) + 1j * np.random.randn(1024)
    rx = tx + np.random.randn(1024) * 0.1 + 1j * np.random.randn(1024) * 0.1
    
    channel = estimator.estimate_dft(tx, rx)
    print(f"   Channel estimate SNR: {channel.snr:.2f} dB")
    
    # Test Equalizer
    print("\n2. Testing Equalizer...")
    equalizer = Equalizer()
    equalizer.set_channel(channel)
    equalized = equalizer.equalize_mmse(rx)
    print(f"   Equalized samples: {len(equalized)}")
    
    # Test Adaptive Equalizer
    print("\n3. Testing Adaptive Equalizer...")
    adaptive = AdaptiveEqualizer()
    training_seq = np.random.randn(100) + 1j * np.random.randn(100)
    error = adaptive.train(rx[:100], training_seq)
    print(f"   Training error: {error:.4f}")
    
    # Test Channel Simulator
    print("\n4. Testing Channel Simulator...")
    simulator = ChannelSimulator()
    signal = np.ones(1000)
    
    # AWGN
    noisy = simulator.apply_awgn(signal, 20)
    print(f"   AWGN applied")
    
    # Rayleigh
    faded = simulator.apply_rayleigh_fading(signal)
    print(f"   Rayleigh fading applied")
    
    # Complete System
    print("\n5. Testing Complete System...")
    system = ChannelEstimationSystem()
    conditions = {
        'awgn': True,
        'snr_db': 20,
        'rayleigh': True,
        'freq_offset': 100
    }
    impaired = system.simulate_channel(tx, conditions)
    result = system.process(tx, impaired)
    print(f"   Processing complete, SNR: {result['snr']:.2f} dB")
    
    print("\n✅ Channel Estimation test completed!")