"""
Signal Detection and Classification Module
Advanced signal detection and classification for SDR
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging


class SignalType(Enum):
    """Signal types"""
    UNKNOWN = "unknown"
    CW = "cw"  # Continuous wave
    AM = "am"
    FM = "fm"
    SSB = "ssb"
    BPSK = "bpsk"
    QPSK = "qpsk"
    QAM = "qam"
    FSK = "fsk"
    FHSS = "fhss"  # Frequency hopping
    DSSS = "dsss"  # Direct sequence spread spectrum
    NOISE = "noise"
    INTERFERENCE = "interference"


class SignalClassifier:
    """Classify detected signals"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        
    def classify(self, iq_data: np.ndarray, 
                sample_rate: float) -> Dict[str, any]:
        """Classify signal type"""
        
        # Extract features
        features = self._extract_features(iq_data, sample_rate)
        
        # Classify based on features
        signal_type = self._determine_signal_type(features)
        
        return {
            'signal_type': signal_type,
            'confidence': features.get('confidence', 0.5),
            'features': features
        }
    
    def _extract_features(self, iq_data: np.ndarray, 
                        sample_rate: float) -> Dict[str, float]:
        """Extract signal features"""
        
        features = {}
        
        # Complex signal
        complex_signal = iq_data.real + 1j * iq_data.imag
        
        # Power
        features['power'] = np.mean(np.abs(complex_signal)**2)
        features['power_db'] = 10 * np.log10(features['power'] + 1e-10)
        
        # Amplitude statistics
        amplitude = np.abs(complex_signal)
        features['amp_mean'] = np.mean(amplitude)
        features['amp_std'] = np.std(amplitude)
        features['amp_var'] = np.var(amplitude)
        features['papr'] = np.max(amplitude**2) / (np.mean(amplitude**2) + 1e-10)
        
        # Phase statistics
        phase = np.angle(complex_signal)
        features['phase_std'] = np.std(phase)
        
        # Frequency domain
        fft = np.fft.fft(complex_signal)
        power_spectrum = np.abs(fft)**2
        
        # Spectral centroid
        freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
        features['spectral_centroid'] = np.sum(np.abs(freqs) * power_spectrum) / (np.sum(power_spectrum) + 1e-10)
        
        # Spectral width
        features['spectral_width'] = np.sqrt(
            np.sum(((freqs - features['spectral_centroid'])**2) * power_spectrum) / 
            (np.sum(power_spectrum) + 1e-10)
        )
        
        # Peak to average ratio
        features['spectral_papr'] = np.max(power_spectrum) / (np.mean(power_spectrum) + 1e-10)
        
        # Zero crossings
        features['zero_crossings'] = np.sum(np.diff(np.sign(complex_signal.real)) != 0)
        
        # Cyclostationary features
        features['cyclic_strength'] = self._compute_cyclic_strength(complex_signal)
        
        return features
    
    def _compute_cyclic_strength(self, signal: np.ndarray) -> float:
        """Compute cyclostationary feature strength"""
        
        # Simplified cyclic autocorrelation at lag 1
        n = len(signal) // 2
        cyclic = np.mean(signal[:n] * np.conj(signal[n:]))
        
        return np.abs(cyclic) / (np.mean(np.abs(signal)**2) + 1e-10)
    
    def _determine_signal_type(self, features: Dict[str, float]) -> SignalType:
        """Determine signal type from features"""
        
        # Check for noise
        if features.get('power_db', -100) < -40:
            return SignalType.NOISE
        
        # Check for CW (narrowband, stable amplitude)
        if features['amp_var'] < 0.01 and features['spectral_width'] < 1000:
            return SignalType.CW
        
        # Check for AM (high PAPR, symmetric spectrum)
        if features['papr'] > 3 and features['papr'] < 10:
            return SignalType.AM
        
        # Check for FM (wide spectrum, moderate PAPR)
        if features['spectral_width'] > 5000:
            return SignalType.FM
        
        # Check for digital modulations
        if features['cyclic_strength'] > 0.3:
            if features['spectral_papr'] > 5:
                return SignalType.QAM
            else:
                return SignalType.PSK
        
        # Check for FSK (two distinct peaks)
        if features['spectral_papr'] > 10:
            return SignalType.FSK
        
        return SignalType.UNKNOWN


class SignalDetector:
    """Detect signals in spectrum"""
    
    def __init__(self, threshold_db: float = -20.0):
        self.threshold_db = threshold_db
        
    def detect(self, spectrum: np.ndarray, 
              frequencies: np.ndarray) -> List[Dict]:
        """Detect signals in spectrum"""
        
        # Convert to dB
        spectrum_db = 10 * np.log10(spectrum + 1e-10)
        
        # Find peaks above threshold
        peaks = []
        
        for i in range(1, len(spectrum_db) - 1):
            if (spectrum_db[i] > self.threshold_db and
                spectrum_db[i] >= spectrum_db[i-1] and
                spectrum_db[i] >= spectrum_db[i+1]):
                
                peaks.append({
                    'frequency': frequencies[i],
                    'power_db': spectrum_db[i],
                    'index': i
                })
        
        # Merge nearby peaks
        merged = self._merge_peaks(peaks, frequencies)
        
        return merged
    
    def _merge_peaks(self, peaks: List[Dict], 
                    frequencies: np.ndarray) -> List[Dict]:
        """Merge nearby peaks"""
        if not peaks:
            return []
        
        merged = [peaks[0]]
        
        for peak in peaks[1:]:
            last = merged[-1]
            
            # If within 1% frequency, merge
            freq_diff = abs(peak['frequency'] - last['frequency'])
            if freq_diff < abs(last['frequency']) * 0.01:
                # Keep stronger
                if peak['power_db'] > last['power_db']:
                    merged[-1] = peak
            else:
                merged.append(peak)
        
        return merged


class SpectrumAnalyzer:
    """Real-time spectrum analysis"""
    
    def __init__(self, sample_rate: float = 2.4e6):
        self.sample_rate = sample_rate
        self.history = []
        self.max_history = 100
        
    def analyze(self, iq_data: np.ndarray) -> Dict:
        """Analyze spectrum"""
        
        # FFT
        nfft = min(2048, len(iq_data))
        fft_result = np.fft.fft(iq_data[:nfft])
        fft_result = np.fft.fftshift(fft_result)
        
        # Power spectrum
        power = np.abs(fft_result)**2
        frequencies = np.fft.fftshift(np.fft.fftfreq(nfft, 1/self.sample_rate))
        
        # Statistics
        stats = {
            'frequencies': frequencies,
            'power': power,
            'max_power_db': 10 * np.log10(np.max(power) + 1e-10),
            'mean_power_db': 10 * np.log10(np.mean(power) + 1e-10),
            'noise_floor_db': 10 * np.log10(np.percentile(power, 10) + 1e-10),
            'dynamic_range': 10 * np.log10(np.max(power) / (np.percentile(power, 10) + 1e-10))
        }
        
        # Add to history
        self.history.append(stats)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        return stats
    
    def get_waterfall_data(self, num_points: int = 100) -> np.ndarray:
        """Get waterfall data for visualization"""
        
        if not self.history:
            return np.zeros((num_points, 512))
        
        waterfall = np.zeros((num_points, 512))
        
        for i, stat in enumerate(self.history[-num_points:]):
            power_db = 10 * np.log10(stat['power'][:512] + 1e-10)
            waterfall[i] = power_db
        
        return waterfall


class SignalDemodulator:
    """Demodulate various signal types"""
    
    def __init__(self):
        self.sample_rate = 2.4e6
        
    def demodulate(self, iq_data: np.ndarray, 
                 signal_type: SignalType) -> Dict:
        """Demodulate signal"""
        
        if signal_type == SignalType.AM:
            return self._demod_am(iq_data)
        elif signal_type == SignalType.FM:
            return self._demod_fm(iq_data)
        elif signal_type == SignalType.CW:
            return self._demod_cw(iq_data)
        elif signal_type in [SignalType.BPSK, SignalType.QPSK]:
            return self._demod_psk(iq_data)
        elif signal_type == SignalType.FSK:
            return self._demod_fsk(iq_data)
        else:
            return {'data': iq_data.real, 'bits': [], 'success': False}
    
    def _demod_am(self, iq_data: np.ndarray) -> Dict:
        """AM demodulation"""
        
        # Envelope detection
        envelope = np.abs(iq_data)
        
        # DC removal
        envelope = envelope - np.mean(envelope)
        
        return {
            'data': envelope,
            'bits': [],
            'success': True
        }
    
    def _demod_fm(self, iq_data: np.ndarray) -> Dict:
        """FM demodulation"""
        
        # Phase difference (instantaneous frequency)
        phase = np.angle(iq_data)
        inst_freq = np.diff(phase)
        
        # Unwrap
        inst_freq = np.unwrap(inst_freq)
        
        return {
            'data': inst_freq,
            'bits': [],
            'success': True
        }
    
    def _demod_cw(self, iq_data: np.ndarray) -> Dict:
        """CW (continuous wave) demodulation"""
        
        # Simply return magnitude
        return {
            'data': np.abs(iq_data),
            'bits': [],
            'success': True
        }
    
    def _demod_psk(self, iq_data: np.ndarray) -> Dict:
        """PSK demodulation"""
        
        # Phase demodulation
        phase = np.angle(iq_data)
        
        # Differential decode
        diff_phase = np.diff(phase)
        
        # Map to bits
        bits = (diff_phase > 0).astype(int)
        
        return {
            'data': phase,
            'bits': bits.tolist(),
            'success': True
        }
    
    def _demod_fsk(self, iq_data: np.ndarray) -> Dict:
        """FSK demodulation"""
        
        # Instantaneous frequency
        phase = np.angle(iq_data)
        inst_freq = np.diff(np.unwrap(phase))
        
        # Simple threshold demodulation
        threshold = 0
        bits = (inst_freq > threshold).astype(int)
        
        return {
            'data': inst_freq,
            'bits': bits.tolist(),
            'success': True
        }


class SpectrumMonitor:
    """Complete spectrum monitoring system"""
    
    def __init__(self):
        self.detector = SignalDetector()
        self.classifier = SignalClassifier()
        self.analyzer = SpectrumAnalyzer()
        self.demodulator = SignalDemodulator()
        
    def process(self, iq_data: np.ndarray, 
               sample_rate: float = 2.4e6) -> Dict:
        """Process IQ data through complete pipeline"""
        
        # Analyze spectrum
        spectrum_stats = self.analyzer.analyze(iq_data)
        
        # Detect signals
        signals = self.detector.detect(spectrum_stats['power'], 
                                      spectrum_stats['frequencies'])
        
        # Classify each detected signal
        classified = []
        for signal in signals:
            # Extract signal segment
            freq = signal['frequency']
            bw = 100e3  # Assume 100kHz bandwidth
            
            # Simple classification
            classification = self.classifier.classify(iq_data, sample_rate)
            
            classified.append({
                **signal,
                'classification': classification['signal_type'].value,
                'confidence': classification['confidence']
            })
        
        return {
            'spectrum': spectrum_stats,
            'signals': classified,
            'num_signals': len(classified)
        }


# Example usage
if __name__ == "__main__":
    print("Testing Signal Detection and Classification...")
    
    # Generate test signal
    sample_rate = 2.4e6
    t = np.arange(1024) / sample_rate
    signal = np.sin(2 * np.pi * 433.92e6 * t) + 0.1 * np.random.randn(1024)
    
    # Test classifier
    print("\n1. Testing Signal Classifier...")
    classifier = SignalClassifier()
    result = classifier.classify(signal, sample_rate)
    print(f"   Signal type: {result['signal_type'].value}")
    
    # Test detector
    print("\n2. Testing Signal Detector...")
    detector = SignalDetector()
    fft = np.fft.fft(signal[:512])
    freqs = np.fft.fftfreq(512, 1/sample_rate)
    signals = detector.detect(np.abs(fft)**2, freqs)
    print(f"   Detected {len(signals)} signals")
    
    # Test analyzer
    print("\n3. Testing Spectrum Analyzer...")
    analyzer = SpectrumAnalyzer()
    stats = analyzer.analyze(signal)
    print(f"   Max power: {stats['max_power_db']:.2f} dB")
    
    # Test complete monitor
    print("\n4. Testing Complete Monitor...")
    monitor = SpectrumMonitor()
    result = monitor.process(signal, sample_rate)
    print(f"   Signals found: {result['num_signals']}")
    
    print("\n✅ Signal Detection test completed!")