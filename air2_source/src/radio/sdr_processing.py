"""
Advanced SDR and Digital IF Processing for AirOne v3.0
Implements Software Defined Radio and Digital Intermediate Frequency processing
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time
from datetime import datetime
import math
from scipy import signal
from scipy.fft import fft, ifft, fftfreq
import warnings
warnings.filterwarnings('ignore')


class RadioFrequencyBand(Enum):
    """Radio frequency bands for SDR operations"""
    VHF = (30e6, 300e6)      # Very High Frequency
    UHF = (300e6, 3e9)       # Ultra High Frequency
    L_BAND = (1e9, 2e9)      # L-band (satellite comms)
    S_BAND = (2e9, 4e9)      # S-band (satellite comms)
    CANSAT_BAND = (433e6, 435e6)  # 433MHz ISM band for CanSat


class ModulationType(Enum):
    """Modulation types supported by the SDR"""
    FSK = "frequency_shift_keying"
    GFSK = "gaussian_frequency_shift_keying"
    MSK = "minimum_shift_keying"
    OOK = "on_off_keying"
    AM = "amplitude_modulation"
    FM = "frequency_modulation"
    PSK = "phase_shift_keying"
    QAM = "quadrature_amplitude_modulation"


@dataclass
class IQSample:
    """In-phase and Quadrature sample for SDR processing"""
    i: float  # In-phase component
    q: float  # Quadrature component
    timestamp: datetime
    frequency: float  # Center frequency in Hz
    gain: float = 1.0
    phase: float = 0.0  # Phase in radians


@dataclass
class DemodulatedData:
    """Demodulated data from SDR processing"""
    timestamp: datetime
    bits: List[int]
    symbols: List[complex]
    frequency_offset: float
    phase_offset: float
    snr: float
    quality: float  # 0.0 to 1.0
    modulation_type: ModulationType
    additional_info: Dict[str, Any] = None


class DigitalIFProcessor:
    """Digital Intermediate Frequency processor for SDR"""
    
    def __init__(self, sample_rate: float = 2.4e6, if_frequency: float = 433.92e6):
        """
        Initialize Digital IF Processor
        :param sample_rate: ADC sample rate in Hz
        :param if_frequency: Intermediate frequency in Hz
        """
        self.sample_rate = sample_rate
        self.if_frequency = if_frequency
        self.nyquist_frequency = sample_rate / 2.0
        
        # Local oscillator for mixing
        self.local_oscillator_phase = 0.0
        self.mixing_frequency = if_frequency
        
        # Filter parameters
        self.filter_taps = None
        self.filter_state = None
        
        # AGC parameters
        self.agc_target_level = 1.0
        self.agc_attack_rate = 0.1
        self.agc_decay_rate = 0.01
        self.current_gain = 1.0
        
        # PLL parameters for carrier recovery
        self.pll_bandwidth = 0.01
        self.pll_phase = 0.0
        self.pll_frequency = 0.0
        self.pll_integrator = 0.0
        
        # Initialize filter
        self._init_filter()
    
    def _init_filter(self):
        """Initialize anti-aliasing and reconstruction filters"""
        # Design low-pass filter for anti-aliasing
        cutoff_freq = 0.4 * self.nyquist_frequency  # 40% of Nyquist
        filter_order = 64
        
        self.filter_taps = signal.firwin(
            filter_order, 
            cutoff_freq / self.nyquist_frequency, 
            window='hamming'
        )
        
        # Initialize filter state
        self.filter_state = signal.lfilter_zi(self.filter_taps, [1.0])
    
    def mix_down(self, samples: np.ndarray, lo_frequency: float = None) -> np.ndarray:
        """
        Mix signal down from RF to IF
        :param samples: Complex RF samples
        :param lo_frequency: Local oscillator frequency (defaults to IF frequency)
        :return: Mixed down IF samples
        """
        if lo_frequency is None:
            lo_frequency = self.mixing_frequency
        
        # Generate LO signal
        t = np.arange(len(samples)) / self.sample_rate
        lo_signal = np.exp(-1j * 2 * np.pi * lo_frequency * t)
        
        # Mix down
        mixed_samples = samples * lo_signal
        
        return mixed_samples
    
    def mix_up(self, samples: np.ndarray, lo_frequency: float = None) -> np.ndarray:
        """
        Mix signal up from IF to RF
        :param samples: Complex IF samples
        :param lo_frequency: Local oscillator frequency (defaults to IF frequency)
        :return: Mixed up RF samples
        """
        if lo_frequency is None:
            lo_frequency = self.mixing_frequency
        
        # Generate LO signal
        t = np.arange(len(samples)) / self.sample_rate
        lo_signal = np.exp(1j * 2 * np.pi * lo_frequency * t)
        
        # Mix up
        mixed_samples = samples * lo_signal
        
        return mixed_samples
    
    def apply_filter(self, samples: np.ndarray) -> np.ndarray:
        """Apply anti-aliasing/reconstruction filter"""
        filtered_samples, self.filter_state = signal.lfilter(
            self.filter_taps, [1.0], samples, zi=self.filter_state
        )
        return filtered_samples
    
    def automatic_gain_control(self, samples: np.ndarray) -> np.ndarray:
        """Apply automatic gain control"""
        # Calculate envelope
        envelope = np.abs(samples)
        
        # Update gain based on envelope
        avg_envelope = np.mean(envelope)
        if avg_envelope > 0:
            target_gain = self.agc_target_level / avg_envelope
            gain_delta = target_gain - self.current_gain
            
            # Apply attack/decay rates
            if abs(gain_delta) > 0.001:  # Small threshold to avoid oscillation
                if target_gain > self.current_gain:
                    # Attack (fast adjustment)
                    self.current_gain += self.agc_attack_rate * gain_delta
                else:
                    # Decay (slow adjustment)
                    self.current_gain += self.agc_decay_rate * gain_delta
        
        return samples * self.current_gain
    
    def carrier_recovery_pll(self, samples: np.ndarray) -> Tuple[np.ndarray, float, float]:
        """
        Recover carrier using PLL
        :param samples: Complex samples
        :return: Corrected samples, frequency offset, phase offset
        """
        corrected_samples = []
        freq_offsets = []
        phase_offsets = []
        
        for sample in samples:
            # Phase detector (Costas loop for BPSK/QPSK)
            phase_error = np.angle(sample)
            
            # Loop filter (proportional + integral)
            self.pll_integrator += self.pll_bandwidth * phase_error
            self.pll_frequency = self.pll_bandwidth * phase_error + self.pll_integrator
            
            # Update phase
            self.pll_phase += self.pll_frequency
            self.pll_phase = self.pll_phase % (2 * np.pi)  # Keep phase in bounds
            
            # Correct the sample
            correction = np.exp(-1j * self.pll_phase)
            corrected_sample = sample * correction
            
            corrected_samples.append(corrected_sample)
            freq_offsets.append(self.pll_frequency)
            phase_offsets.append(self.pll_phase)
        
        return (
            np.array(corrected_samples),
            np.mean(freq_offsets) if freq_offsets else 0.0,
            np.mean(phase_offsets) if phase_offsets else 0.0
        )
    
    def downsample(self, samples: np.ndarray, decimation_factor: int) -> np.ndarray:
        """Downsample with anti-aliasing filter"""
        # Apply anti-aliasing filter
        filtered_samples = self.apply_filter(samples)
        
        # Decimate
        downsampled = filtered_samples[::decimation_factor]
        
        return downsampled
    
    def upsample(self, samples: np.ndarray, interpolation_factor: int) -> np.ndarray:
        """Upsample with reconstruction filter"""
        # Zero stuffing
        upsampled = np.zeros(len(samples) * interpolation_factor, dtype=complex)
        upsampled[::interpolation_factor] = samples
        
        # Apply reconstruction filter
        reconstructed = self.apply_filter(upsampled)
        
        return reconstructed


class SDRDemodulator:
    """SDR demodulator for various modulation schemes"""
    
    def __init__(self, sample_rate: float = 2.4e6):
        self.sample_rate = sample_rate
        self.symbol_rate = 9600  # Default symbol rate
        self.baud_rate = 9600    # Default baud rate
        self.bits_per_symbol = 1  # Default for FSK
    
    def demodulate_fsk(self, samples: np.ndarray) -> DemodulatedData:
        """Demodulate FSK (Frequency Shift Keying)"""
        # Calculate instantaneous frequency
        phase = np.unwrap(np.angle(samples))
        freq = np.diff(phase) * self.sample_rate / (2 * np.pi)
        
        # Add zero to maintain length
        freq = np.concatenate([[freq[0]], freq])
        
        # Determine bit decisions based on frequency thresholds
        # Assuming 2 frequencies: mark and space
        mark_freq = 1200  # Hz
        space_freq = 2200  # Hz
        threshold = (mark_freq + space_freq) / 2
        
        bits = (freq > threshold).astype(int).tolist()
        
        # Calculate SNR estimate
        signal_power = np.mean(np.abs(samples)**2)
        noise_power = np.var(freq - np.mean(freq))
        snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
        
        return DemodulatedData(
            timestamp=datetime.now(),
            bits=bits,
            symbols=samples.tolist(),
            frequency_offset=0.0,
            phase_offset=0.0,
            snr=snr,
            quality=min(1.0, max(0.0, snr / 20.0)),  # Normalize SNR to 0-1
            modulation_type=ModulationType.FSK,
            additional_info={'frequency_estimates': freq.tolist()}
        )
    
    def demodulate_gfsk(self, samples: np.ndarray) -> DemodulatedData:
        """Demodulate GFSK (Gaussian Frequency Shift Keying)"""
        # Apply Gaussian filter to smooth transitions
        gaussian_taps = signal.gaussian(11, 2.0)
        gaussian_taps /= np.sum(gaussian_taps)
        
        filtered_samples = signal.lfilter(gaussian_taps, [1.0], samples)
        
        # Demodulate as FSK
        return self.demodulate_fsk(filtered_samples)
    
    def demodulate_psk(self, samples: np.ndarray, constellation_size: int = 4) -> DemodulatedData:
        """Demodulate PSK (Phase Shift Keying)"""
        # Calculate phase
        phases = np.angle(samples)
        
        # Map to constellation points
        constellation_phases = np.linspace(0, 2*np.pi, constellation_size, endpoint=False)
        
        # Find closest constellation point for each sample
        symbols = []
        bits = []
        
        for phase in phases:
            # Find closest constellation point
            distances = np.abs(constellation_phases - phase)
            closest_idx = np.argmin(distances)
            symbols.append(np.exp(1j * constellation_phases[closest_idx]))
            
            # Convert to bits (gray-coded for QPSK)
            if constellation_size == 4:  # QPSK
                bit1 = 1 if closest_idx in [0, 3] else 0
                bit2 = 1 if closest_idx in [1, 2] else 0
                bits.extend([bit1, bit2])
            else:  # BPSK or other
                for bit in format(closest_idx, f'0{int(np.log2(constellation_size))}b'):
                    bits.append(int(bit))
        
        # Calculate SNR
        signal_power = np.mean(np.abs(samples)**2)
        noise_power = np.mean(np.abs(samples - np.array(symbols))**2)
        snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
        
        return DemodulatedData(
            timestamp=datetime.now(),
            bits=bits,
            symbols=symbols,
            frequency_offset=0.0,
            phase_offset=0.0,
            snr=snr,
            quality=min(1.0, max(0.0, snr / 20.0)),
            modulation_type=ModulationType.PSK,
            additional_info={'constellation_size': constellation_size}
        )
    
    def demodulate_ook(self, samples: np.ndarray) -> DemodulatedData:
        """Demodulate OOK (On-Off Keying)"""
        # Calculate envelope
        envelope = np.abs(samples)
        
        # Apply threshold detection
        threshold = np.mean(envelope) * 0.7  # 70% of mean as threshold
        bits = (envelope > threshold).astype(int).tolist()
        
        # Calculate SNR
        signal_power = np.mean(envelope[envelope > threshold]**2)
        noise_power = np.mean(envelope[envelope <= threshold]**2)
        snr = 10 * np.log10(signal_power / (noise_power + 1e-10)) if noise_power > 0 else float('inf')
        
        return DemodulatedData(
            timestamp=datetime.now(),
            bits=bits,
            symbols=samples.tolist(),
            frequency_offset=0.0,
            phase_offset=0.0,
            snr=snr,
            quality=min(1.0, max(0.0, snr / 20.0)) if snr != float('inf') else 1.0,
            modulation_type=ModulationType.OOK,
            additional_info={'threshold': threshold}
        )
    
    def set_symbol_rate(self, rate: float):
        """Set symbol rate for demodulation"""
        self.symbol_rate = rate
        self.baud_rate = rate  # For now, assume baud rate equals symbol rate


class AdvancedDataFilterBank:
    """Advanced filter bank with multiple filter types for SDR applications"""
    
    def __init__(self, sample_rate: float = 2.4e6):
        self.sample_rate = sample_rate
        self.nyquist_freq = sample_rate / 2.0
        
        # Pre-designed filters
        self.filters = {}
        self._design_default_filters()
    
    def _design_default_filters(self):
        """Design default filters for common applications"""
        # Low-pass filter for anti-aliasing
        self.filters['anti_alias'] = self._design_low_pass(0.4 * self.nyquist_freq, 64)

        # Band-pass filter for channel selection (relative to baseband)
        # For a 2.4MHz sample rate, we can create a bandpass around DC
        self.filters['channel_select'] = self._design_band_pass(10e3, 50e3, 128)  # 10kHz to 50kHz bandpass

        # Matched filter for pulse shaping
        self.filters['matched'] = self._design_matched_filter()

        # Hilbert transform for envelope detection
        self.filters['hilbert'] = self._design_hilbert_transform()
    
    def _design_low_pass(self, cutoff_freq: float, filter_order: int) -> np.ndarray:
        """Design FIR low-pass filter"""
        normalized_cutoff = cutoff_freq / self.nyquist_freq
        taps = signal.firwin(filter_order, normalized_cutoff, window='hamming')
        return taps
    
    def _design_band_pass(self, low_freq: float, high_freq: float, filter_order: int) -> np.ndarray:
        """Design FIR band-pass filter"""
        low_norm = low_freq / self.nyquist_freq
        high_norm = high_freq / self.nyquist_freq
        taps = signal.firwin(filter_order, [low_norm, high_norm], pass_zero=False, window='hamming')
        return taps
    
    def _design_matched_filter(self) -> np.ndarray:
        """Design matched filter (typically root-raised cosine)"""
        # Root-raised cosine filter for pulse shaping
        alpha = 0.5  # Roll-off factor
        span = 8     # Filter span in symbols
        sps = int(self.sample_rate / 9600)  # Samples per symbol (assuming 9600 baud)
        
        # Generate RRC filter taps
        n = np.arange(-span * sps // 2, span * sps // 2 + 1)
        h_rrc = np.zeros(len(n))
        
        for i, t in enumerate(n):
            if t == 0:
                h_rrc[i] = 1 - alpha + (4 * alpha / np.pi)
            elif abs(t) == sps / (4 * alpha):
                h_rrc[i] = (alpha / np.sqrt(2)) * ((1 + 2/np.pi) * np.sin(np.pi / (4 * alpha)) + 
                                                  (1 - 2/np.pi) * np.cos(np.pi / (4 * alpha)))
            else:
                num = np.cos((1 + alpha) * np.pi * t / sps) + np.sin((1 - alpha) * np.pi * t / sps) * sps / (4 * alpha * abs(t))
                den = 1 - (4 * alpha * t / sps)**2
                h_rrc[i] = num / den
        
        return h_rrc / np.sqrt(np.sum(h_rrc**2))  # Normalize
    
    def _design_hilbert_transform(self) -> np.ndarray:
        """Design Hilbert transform filter"""
        # Odd-length Hilbert transform
        N = 65  # Must be odd
        taps = np.zeros(N)
        
        for n in range(N):
            if n != (N-1)//2:
                if (n - (N-1)//2) % 2 == 0:
                    taps[n] = 0
                else:
                    taps[n] = 2 / (np.pi * (n - (N-1)//2))
        
        return taps
    
    def apply_filter(self, samples: np.ndarray, filter_type: str = 'anti_alias') -> np.ndarray:
        """Apply specified filter to samples"""
        if filter_type not in self.filters:
            raise ValueError(f"Unknown filter type: {filter_type}")
        
        filter_taps = self.filters[filter_type]
        
        # Apply filter using convolution
        filtered_samples = signal.lfilter(filter_taps, [1.0], samples)
        
        return filtered_samples
    
    def apply_adaptive_filter(self, samples: np.ndarray, reference: np.ndarray, 
                             filter_length: int = 32, step_size: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply adaptive filter (LMS algorithm)
        :param samples: Input signal to be filtered
        :param reference: Reference signal for adaptation
        :param filter_length: Length of adaptive filter
        :param step_size: Step size for LMS algorithm
        :return: Filtered output, filter coefficients
        """
        # Initialize filter coefficients
        w = np.zeros(filter_length, dtype=complex)
        output = np.zeros(len(samples), dtype=complex)
        
        for n in range(filter_length, len(samples)):
            # Extract input vector
            x = samples[n:n-filter_length:-1]  # Time-reversed
            if len(x) < filter_length:
                x = np.pad(x, (0, filter_length - len(x)), 'constant')
            
            # Filter output
            y = np.dot(w, x)
            
            # Error signal
            error = reference[n] - y
            
            # Update filter coefficients
            w += step_size * np.conj(error) * x
            
            # Store output
            output[n] = y
        
        return output, w


class SDRBackend:
    """Backend for SDR operations with digital IF processing"""
    
    def __init__(self, center_frequency: float = 433.92e6, sample_rate: float = 2.4e6):
        self.center_frequency = center_frequency
        self.sample_rate = sample_rate
        self.is_running = False
        
        # Initialize components
        self.digital_if = DigitalIFProcessor(sample_rate=sample_rate, if_frequency=center_frequency)
        self.demodulator = SDRDemodulator(sample_rate=sample_rate)
        self.filter_bank = AdvancedDataFilterBank(sample_rate=sample_rate)
        
        # Processing buffers
        self.rf_buffer = queue.Queue(maxsize=1000)
        self.if_buffer = queue.Queue(maxsize=1000)
        self.demod_buffer = queue.Queue(maxsize=1000)
        
        # Processing statistics
        self.stats = {
            'samples_processed': 0,
            'demodulations_performed': 0,
            'errors': 0,
            'last_update': datetime.now()
        }
        
        # Threading
        self.processing_thread = None
        self.running = False
        self.processing_lock = threading.Lock()
    
    def configure_radio(self, center_frequency: float = None, sample_rate: float = None,
                       gain: float = None, modulation: ModulationType = None):
        """Configure radio parameters"""
        if center_frequency is not None:
            self.center_frequency = center_frequency
            self.digital_if.mixing_frequency = center_frequency
        
        if sample_rate is not None:
            self.sample_rate = sample_rate
            self.digital_if.sample_rate = sample_rate
            self.demodulator.sample_rate = sample_rate
            self.filter_bank.sample_rate = sample_rate
            self.filter_bank.nyquist_freq = sample_rate / 2.0
            self.filter_bank._design_default_filters()
    
    def add_rf_samples(self, samples: np.ndarray) -> bool:
        """Add RF samples to processing queue"""
        try:
            self.rf_buffer.put(samples, timeout=1.0)
            return True
        except queue.Full:
            return False
    
    def start_processing(self):
        """Start SDR processing thread"""
        if self.processing_thread and self.processing_thread.is_alive():
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
    
    def stop_processing(self):
        """Stop SDR processing"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
    
    def _processing_loop(self):
        """Main SDR processing loop"""
        while self.running:
            try:
                # Get RF samples from queue
                rf_samples = self.rf_buffer.get(timeout=1.0)
                
                # Process the samples
                processed_data = self._process_rf_samples(rf_samples)
                
                if processed_data:
                    try:
                        self.demod_buffer.put(processed_data, timeout=1.0)
                        self.stats['demodulations_performed'] += 1
                    except queue.Full:
                        pass  # Skip if buffer full
                
                self.stats['samples_processed'] += len(rf_samples)
                self.stats['last_update'] = datetime.now()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.stats['errors'] += 1
                print(f"SDR processing error: {e}")
    
    def _process_rf_samples(self, rf_samples: np.ndarray) -> Optional[DemodulatedData]:
        """Process RF samples through the entire chain"""
        try:
            # Ensure complex samples
            if rf_samples.dtype != complex:
                rf_samples = rf_samples.astype(complex)
            
            # Apply anti-aliasing filter
            filtered_rf = self.filter_bank.apply_filter(rf_samples, 'anti_alias')
            
            # Mix down to IF
            if_samples = self.digital_if.mix_down(filtered_rf)
            
            # Apply AGC
            agc_samples = self.digital_if.automatic_gain_control(if_samples)
            
            # Carrier recovery
            recovered_samples, freq_offset, phase_offset = self.digital_if.carrier_recovery_pll(agc_samples)
            
            # Apply channel selection filter
            channel_filtered = self.filter_bank.apply_filter(recovered_samples, 'channel_select')
            
            # Demodulate based on expected modulation
            demod_result = self.demodulator.demodulate_fsk(channel_filtered)
            
            # Update demodulation with recovered parameters
            demod_result.frequency_offset = freq_offset
            demod_result.phase_offset = phase_offset
            
            return demod_result
            
        except Exception as e:
            print(f"Error in RF processing: {e}")
            return None
    
    def transmit(self, data_bits: List[int], modulation_type: ModulationType = ModulationType.FSK) -> np.ndarray:
        """Transmit data by modulating it"""
        # Convert bits to symbols
        symbols = self._bits_to_symbols(data_bits, modulation_type)
        
        # Apply pulse shaping
        shaped_symbols = self._pulse_shaping(symbols)
        
        # Upconvert to RF
        rf_signal = self.digital_if.mix_up(shaped_symbols)
        
        return rf_signal
    
    def _bits_to_symbols(self, bits: List[int], modulation_type: ModulationType) -> np.ndarray:
        """Convert bits to modulation symbols"""
        if modulation_type == ModulationType.FSK:
            # Simple FSK: 0 -> mark frequency, 1 -> space frequency
            mark_freq = 1200  # Hz
            space_freq = 2200  # Hz
            
            # Generate symbols based on bits
            symbols = []
            for bit in bits:
                freq = mark_freq if bit == 0 else space_freq
                # Generate a short segment at this frequency
                t = np.linspace(0, 1/self.demodulator.symbol_rate, int(self.sample_rate/self.demodulator.symbol_rate))
                symbol_segment = np.exp(1j * 2 * np.pi * freq * t)
                symbols.extend(symbol_segment)
            
            return np.array(symbols)
        
        elif modulation_type == ModulationType.PSK:
            # BPSK: 0 -> 0°, 1 -> 180°
            symbols = []
            for bit in bits:
                phase = 0 if bit == 0 else np.pi
                symbols.append(np.exp(1j * phase))
            
            return np.array(symbols)
        
        else:
            # Default to simple BPSK
            symbols = []
            for bit in bits:
                phase = 0 if bit == 0 else np.pi
                symbols.append(np.exp(1j * phase))
            
            return np.array(symbols)
    
    def _pulse_shaping(self, symbols: np.ndarray) -> np.ndarray:
        """Apply pulse shaping to symbols"""
        # Upsample symbols
        upsample_factor = int(self.sample_rate / self.demodulator.symbol_rate)
        upsampled = np.zeros(len(symbols) * upsample_factor, dtype=complex)
        upsampled[::upsample_factor] = symbols
        
        # Apply matched filter (root-raised cosine)
        shaped = signal.lfilter(self.filter_bank.filters['matched'], [1.0], upsampled)
        
        return shaped
    
    def get_spectrum(self, samples: np.ndarray, nfft: int = 1024) -> Tuple[np.ndarray, np.ndarray]:
        """Get power spectrum of samples"""
        # Apply window to reduce spectral leakage
        windowed = samples * np.hanning(len(samples))
        
        # Zero-pad if necessary
        if len(windowed) < nfft:
            windowed = np.pad(windowed, (0, nfft - len(windowed)), 'constant')
        else:
            windowed = windowed[:nfft]  # Truncate if too long
        
        # Compute FFT
        fft_result = fft(windowed)
        frequencies = fftfreq(nfft, 1/self.sample_rate)
        power_spectrum = 20 * np.log10(np.abs(fft_result) + 1e-10)  # Convert to dB
        
        return frequencies, power_spectrum
    
    def detect_signal(self, samples: np.ndarray, threshold_db: float = -20.0) -> bool:
        """Detect presence of signal above threshold"""
        power_db = 10 * np.log10(np.mean(np.abs(samples)**2) + 1e-10)
        return power_db > threshold_db
    
    def estimate_frequency_offset(self, samples: np.ndarray) -> float:
        """Estimate frequency offset in samples"""
        # Calculate phase difference between consecutive samples
        phase_diff = np.diff(np.angle(samples))
        
        # Unwrap phase to handle 2π jumps
        unwrapped_phase = np.unwrap(np.angle(samples))
        inst_freq = np.diff(unwrapped_phase) * self.sample_rate / (2 * np.pi)
        
        # Return average frequency offset
        return np.mean(inst_freq) if len(inst_freq) > 0 else 0.0
    
    def get_signal_quality_metrics(self, samples: np.ndarray) -> Dict[str, float]:
        """Get various signal quality metrics"""
        metrics = {}
        
        # Power
        power = np.mean(np.abs(samples)**2)
        metrics['power_db'] = 10 * np.log10(power + 1e-10)
        
        # Phase noise (deviation from ideal phase)
        ideal_phase = np.angle(samples)
        unwrapped_phase = np.unwrap(ideal_phase)
        phase_deviation = np.diff(unwrapped_phase)
        metrics['phase_noise_rms'] = np.sqrt(np.mean(phase_deviation**2))
        
        # Constellation quality (if applicable)
        if len(samples) > 1:
            # Calculate magnitude variance (for amplitude constancy)
            magnitude = np.abs(samples)
            metrics['magnitude_variance'] = np.var(magnitude)
            
            # Calculate phase variance
            phase = np.angle(samples)
            metrics['phase_variance'] = np.var(phase)
        
        # SNR estimate (simple method)
        signal_power = np.mean(np.abs(samples)**2)
        # Estimate noise as high-frequency components
        if len(samples) > 100:
            # Use high-pass filtered version as noise estimate
            b, a = signal.butter(4, 0.8, 'high', fs=self.sample_rate)
            noise_estimate = signal.filtfilt(b, a, samples)
            noise_power = np.mean(np.abs(noise_estimate)**2)
            metrics['snr_db'] = 10 * np.log10(signal_power / (noise_power + 1e-10))
        else:
            metrics['snr_db'] = float('inf')
        
        return metrics


class SDRInterface:
    """Interface for interacting with the SDR backend"""
    
    def __init__(self, center_frequency: float = 433.92e6, sample_rate: float = 2.4e6):
        self.backend = SDRBackend(center_frequency, sample_rate)
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """Initialize the SDR interface"""
        try:
            self.backend.start_processing()
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"SDR initialization error: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the SDR interface"""
        self.backend.stop_processing()
        self.is_initialized = False
    
    def receive_samples(self, num_samples: int = 1024) -> np.ndarray:
        """Receive samples from the SDR (simulated for this implementation)"""
        # In a real implementation, this would interface with actual SDR hardware
        # For simulation, we'll generate some test data
        t = np.arange(num_samples) / self.backend.sample_rate
        # Simulate a modulated signal
        signal_freq = 1000  # 1 kHz tone
        data_signal = np.sin(2 * np.pi * signal_freq * t)
        # Add some noise
        noise = np.random.normal(0, 0.1, num_samples) + 1j * np.random.normal(0, 0.1, num_samples)
        return data_signal + noise
    
    def transmit_data(self, data_bits: List[int], modulation: ModulationType = ModulationType.FSK) -> bool:
        """Transmit data using the SDR"""
        try:
            rf_signal = self.backend.transmit(data_bits, modulation)
            # In a real implementation, this would send the signal to the RF hardware
            # For simulation, we just return True to indicate success
            return True
        except Exception as e:
            print(f"Transmission error: {e}")
            return False
    
    def get_spectrum_data(self, num_samples: int = 1024) -> Tuple[np.ndarray, np.ndarray]:
        """Get spectrum data for visualization"""
        samples = self.receive_samples(num_samples)
        return self.backend.get_spectrum(samples)
    
    def get_signal_quality(self, num_samples: int = 1024) -> Dict[str, float]:
        """Get current signal quality metrics"""
        samples = self.receive_samples(num_samples)
        return self.backend.get_signal_quality_metrics(samples)
    
    def set_frequency(self, frequency_hz: float):
        """Set the center frequency"""
        self.backend.configure_radio(center_frequency=frequency_hz)
    
    def set_modulation(self, modulation_type: ModulationType):
        """Set the modulation type"""
        self.current_modulation = modulation_type
        
        # Configure demodulator based on modulation type
        if modulation_type == ModulationType.AM:
            self.backend.digital_if.demod_type = 'am'
        elif modulation_type == ModulationType.FM:
            self.backend.digital_if.demod_type = 'fm'
        elif modulation_type == ModulationType.SSB:
            self.backend.digital_if.demod_type = 'ssb'
        elif modulation_type == ModulationType.DSB:
            self.backend.digital_if.demod_type = 'dsb'
        elif modulation_type == ModulationType.CW:
            self.backend.digital_if.demod_type = 'cw'
        
        self.logger.info(f"Modulation set to: {modulation_type.name}")
    
    def set_gain(self, gain_db: float):
        """Set the RF gain"""
        # This would affect the AGC settings
        self.backend.digital_if.agc_target_level = 10**(gain_db/20.0)


# Example usage and testing
if __name__ == "__main__":
    print("Testing Advanced SDR and Digital IF Processing...")
    
    # Create SDR interface
    sdr = SDRInterface(center_frequency=433.92e6, sample_rate=2.4e6)
    
    # Initialize
    success = sdr.initialize()
    print(f"SDR initialized: {success}")
    
    if success:
        # Test receiving samples
        samples = sdr.receive_samples(1024)
        print(f"Received {len(samples)} samples")
        
        # Test spectrum analysis
        freqs, powers = sdr.get_spectrum_data(1024)
        print(f"Spectrum data: {len(freqs)} frequency bins")
        
        # Test signal quality
        quality_metrics = sdr.get_signal_quality(1024)
        print(f"Signal quality metrics: {list(quality_metrics.keys())}")
        
        # Test transmission
        test_bits = [1, 0, 1, 1, 0, 0, 1, 0]
        tx_success = sdr.transmit_data(test_bits, ModulationType.FSK)
        print(f"Transmission successful: {tx_success}")
        
        # Test backend processing
        backend = sdr.backend
        print(f"Backend sample rate: {backend.sample_rate}")
        print(f"Center frequency: {backend.center_frequency}")
        
        # Test filter bank
        test_signal = np.random.randn(100) + 1j * np.random.randn(100)
        filtered_signal = backend.filter_bank.apply_filter(test_signal, 'anti_alias')
        print(f"Applied filter to {len(test_signal)} samples")
        
        # Test demodulation
        demod_result = backend.demodulator.demodulate_fsk(test_signal)
        print(f"Demodulated {len(demod_result.bits)} bits with SNR: {demod_result.snr:.2f} dB")
        
        # Shutdown
        sdr.shutdown()
        print("SDR interface shut down")
    
    print("Advanced SDR and Digital IF Processing test completed successfully!")