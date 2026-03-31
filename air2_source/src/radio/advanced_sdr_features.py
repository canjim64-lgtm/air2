"""
Advanced SDR Features Module
Enhanced spectrum monitoring, signal classification, and cognitive radio for AirOne
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import queue
import time
import logging


class SignalClassification(Enum):
    """Signal classification types"""
    UNKNOWN = "unknown"
    FHSS = "frequency_hopping"
    DSSS = "direct_sequence"
    CW = "continuous_wave"
    PULSED = "pulsed"
    NOISE = "noise"
    MODULATED = "modulated"
    INTERFERENCE = "interference"


class SpectrumEvent(Enum):
    """Spectrum monitoring events"""
    SIGNAL_DETECTED = "signal_detected"
    SIGNAL_LOST = "signal_lost"
    INTERFERENCE_DETECTED = "interference_detected"
    FREQUENCY_HOP = "frequency_hop"
    BANDWIDTH_CHANGE = "bandwidth_change"


@dataclass
class SignalDetection:
    """Detected signal information"""
    center_frequency: float
    bandwidth: float
    power: float
    classification: SignalClassification
    timestamp: datetime
    duration: float = 0.0
    hop_pattern: Optional[List[float]] = None


@dataclass
class SpectrumMonitorConfig:
    """Spectrum monitor configuration"""
    center_frequency: float = 433.92e6
    span: float = 10e6  # 10 MHz span
    resolution_bandwidth: float = 100e3  # 100 kHz RBW
    detection_threshold: float = -60.0  # dBm
    min_signal_duration: float = 0.1  # seconds


class SpectrumMonitor:
    """Real-time spectrum monitoring and signal detection"""
    
    def __init__(self, config: Optional[SpectrumMonitorConfig] = None):
        """
        Initialize spectrum monitor
        
        Args:
            config: Spectrum monitor configuration
        """
        self.logger = logging.getLogger(f"{__name__}.SpectrumMonitor")
        self.config = config or SpectrumMonitorConfig()
        
        # Detection state
        self.detected_signals: List[SignalDetection] = []
        self.signal_history: Dict[float, List[SignalDetection]] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.event_callbacks: Dict[SpectrumEvent, List[Callable]] = {
            event: [] for event in SpectrumEvent
        }
        
        # Statistics
        self.total_detections = 0
        self.false_alarms = 0
        
        self.logger.info("Spectrum Monitor initialized")
    
    def start_monitoring(self):
        """Start spectrum monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Spectrum monitoring started")
    
    def stop_monitoring(self):
        """Stop spectrum monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("Spectrum monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            # In a real implementation, this would scan the spectrum
            # For simulation, we'll generate test data
            self._simulate_detection()
            time.sleep(0.1)
    
    def _simulate_detection(self):
        """Simulate signal detection for testing"""
        if np.random.random() < 0.05:  # 5% chance of detection
            center_freq = self.config.center_frequency + np.random.uniform(-self.config.span/2, self.config.span/2)
            power = self.config.detection_threshold + np.random.uniform(0, 20)
            
            detection = SignalDetection(
                center_frequency=center_freq,
                bandwidth=np.random.uniform(10e3, 1e6),
                power=power,
                classification=SignalClassification.MODULATED,
                timestamp=datetime.now()
            )
            
            self._add_detection(detection)
    
    def _add_detection(self, detection: SignalDetection):
        """Add a signal detection"""
        self.detected_signals.append(detection)
        self.total_detections += 1
        
        # Store in history
        freq_key = round(detection.center_frequency / 1e6, 2)
        if freq_key not in self.signal_history:
            self.signal_history[freq_key] = []
        self.signal_history[freq_key].append(detection)
        
        # Trigger callbacks
        self._trigger_event(SpectrumEvent.SIGNAL_DETECTED, detection)
    
    def _trigger_event(self, event: SpectrumEvent, data: Any):
        """Trigger event callbacks"""
        for callback in self.event_callbacks[event]:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    def register_callback(self, event: SpectrumEvent, callback: Callable):
        """Register event callback"""
        self.event_callbacks[event].append(callback)
    
    def scan_spectrum(self, samples: np.ndarray, 
                      sample_rate: float) -> List[SignalDetection]:
        """
        Scan spectrum for signals
        
        Args:
            samples: IQ samples
            sample_rate: Sample rate
            
        Returns:
            List of detected signals
        """
        detections = []
        
        # Compute FFT
        nfft = min(2048, len(samples))
        fft_result = np.fft.fft(samples[:nfft])
        fft_result = np.fft.fftshift(fft_result)
        
        # Compute power spectrum
        power_db = 10 * np.log10(np.abs(fft_result)**2 + 1e-10)
        freqs = np.fft.fftshift(np.fft.fftfreq(nfft, 1/sample_rate))
        
        # Find peaks
        threshold = self.config.detection_threshold
        peak_indices = []
        
        for i in range(1, len(power_db) - 1):
            if (power_db[i] > threshold and 
                power_db[i] > power_db[i-1] and 
                power_db[i] > power_db[i+1]):
                peak_indices.append(i)
        
        # Group nearby peaks
        for idx in peak_indices:
            detection = SignalDetection(
                center_frequency=freqs[idx] + self.config.center_frequency,
                bandwidth=self.config.resolution_bandwidth,
                power=power_db[idx],
                classification=self._classify_signal(power_db, idx),
                timestamp=datetime.now()
            )
            detections.append(detection)
        
        return detections
    
    def _classify_signal(self, power_db: np.ndarray, idx: int) -> SignalClassification:
        """Classify signal based on spectral characteristics"""
        # Simple classification based on bandwidth and power
        power = power_db[idx]
        
        if power < self.config.detection_threshold:
            return SignalClassification.NOISE
        
        # Check for CW (narrowband)
        bandwidth_estimate = np.sum(power_db > (power - 3)) / len(power_db)
        
        if bandwidth_estimate < 0.01:
            return SignalClassification.CW
        elif bandwidth_estimate < 0.05:
            return SignalClassification.PULSED
        else:
            return SignalClassification.MODULATED
    
    def get_spectrum_waterfall(self, num_samples: int = 100) -> np.ndarray:
        """
        Get spectrum waterfall data for visualization
        
        Args:
            num_samples: Number of samples to collect
            
        Returns:
            Spectrum waterfall matrix
        """
        # In real implementation, this would collect real-time spectrum data
        # For simulation, generate test data
        waterfall = np.random.randn(num_samples, 512) * -40
        return waterfall
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {
            'total_detections': self.total_detections,
            'active_signals': len(self.detected_signals),
            'monitoring': self.is_monitoring,
            'frequency_bands': len(self.signal_history)
        }


class CognitiveRadioEngine:
    """Cognitive radio engine for dynamic spectrum access"""
    
    def __init__(self, center_frequency: float = 433.92e6):
        """
        Initialize cognitive radio engine
        
        Args:
            center_frequency: Center frequency for operations
        """
        self.logger = logging.getLogger(f"{__name__}.CognitiveRadio")
        self.center_frequency = center_frequency
        
        # Spectrum awareness
        self.spectrum_monitor = SpectrumMonitor()
        self.available_bands: List[Tuple[float, float]] = []
        self.occupied_bands: List[Tuple[float, float]] = []
        
        # Decision engine
        self.decision_policy = "best_available"  # Options: best_available, lowest_interference, etc.
        
        # Learning (simplified)
        self.channel_history: Dict[str, List[float]] = {}
        
        self.logger.info("Cognitive Radio Engine initialized")
    
    def scan_available_spectrum(self) -> List[Tuple[float, float]]:
        """
        Scan and identify available spectrum bands
        
        Returns:
            List of (start_freq, end_freq) tuples
        """
        # Get current spectrum occupancy
        detections = self.spectrum_monitor.detected_signals
        
        # Mark occupied bands
        self.occupied_bands = []
        for det in detections:
            bw = det.bandwidth
            start = det.center_frequency - bw/2
            end = det.center_frequency + bw/2
            self.occupied_bands.append((start, end))
        
        # Find available bands (simplified - just return some default bands)
        # In real implementation, this would analyze actual spectrum data
        default_bands = [
            (self.center_frequency - 5e6, self.center_frequency - 1e6),
            (self.center_frequency + 1e6, self.center_frequency + 5e6)
        ]
        
        self.available_bands = [b for b in default_bands if not self._is_occupied(b)]
        
        return self.available_bands
    
    def _is_occupied(self, band: Tuple[float, float]) -> bool:
        """Check if band is occupied"""
        for occ in self.occupied_bands:
            if (band[0] < occ[1] and band[1] > occ[0]):
                return True
        return False
    
    def select_best_channel(self) -> Optional[float]:
        """
        Select best available channel
        
        Returns:
            Center frequency of selected channel or None
        """
        if not self.available_bands:
            self.scan_available_spectrum()
        
        if not self.available_bands:
            return None
        
        # Simple selection: choose middle of first available band
        band = self.available_bands[0]
        center = (band[0] + band[1]) / 2
        
        # Record selection
        freq_key = f"{center/1e6:.2f}MHz"
        if freq_key not in self.channel_history:
            self.channel_history[freq_key] = []
        self.channel_history[freq_key].append(datetime.now().timestamp())
        
        return center
    
    def adapt_parameters(self, channel_quality: float):
        """
        Adapt radio parameters based on channel quality
        
        Args:
            channel_quality: Channel quality metric (0-1)
        """
        if channel_quality < 0.3:
            # Poor quality - reduce bandwidth, increase coding
            self.logger.warning("Poor channel quality - adapting parameters")
        elif channel_quality > 0.7:
            # Good quality - can increase data rate
            self.logger.info("Good channel quality - optimizing parameters")
    
    def predict_spectrum_availability(self, horizon: int = 10) -> Dict[str, float]:
        """
        Predict spectrum availability based on history
        
        Args:
            horizon: Prediction horizon
            
        Returns:
            Dictionary of frequency band availability probabilities
        """
        predictions = {}
        
        for freq, history in self.channel_history.items():
            if len(history) < 5:
                predictions[freq] = 0.5
                continue
            
            # Simple prediction based on usage patterns
            recent_usage = sum(1 for t in history if t > time.time() - 3600)
            predictions[freq] = 1.0 - (recent_usage / len(history))
        
        return predictions


class SignalClassifier:
    """Machine learning-based signal classifier"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SignalClassifier")
        self.classifier_model = None
        self.feature_cache = []
        
    def extract_features(self, samples: np.ndarray, 
                        sample_rate: float) -> Dict[str, float]:
        """
        Extract features from signal for classification
        
        Args:
            samples: IQ samples
            sample_rate: Sample rate
            
        Returns:
            Feature dictionary
        """
        features = {}
        
        # Time domain features
        features['mean_amplitude'] = np.mean(np.abs(samples))
        features['std_amplitude'] = np.std(np.abs(samples))
        features['peak_to_average'] = np.max(np.abs(samples)) / (np.mean(np.abs(samples)) + 1e-10)
        
        # Frequency domain features
        nfft = min(1024, len(samples))
        fft_result = np.fft.fft(samples[:nfft])
        power_spectrum = np.abs(fft_result)**2
        
        features['spectral_centroid'] = np.sum(np.arange(len(power_spectrum)) * power_spectrum) / (np.sum(power_spectrum) + 1e-10)
        features['spectral_spread'] = np.sqrt(
            np.sum(((np.arange(len(power_spectrum)) - features['spectral_centroid'])**2) * power_spectrum) / 
            (np.sum(power_spectrum) + 1e-10)
        )
        
        # Peak to average power ratio
        features['papr'] = 10 * np.log10(np.max(power_spectrum) / (np.mean(power_spectrum) + 1e-10))
        
        # Cyclostationary features (simplified)
        features['cyclic_freq_peaks'] = len(self._find_cyclic_peaks(samples))
        
        return features
    
    def _find_cyclic_peaks(self, samples: np.ndarray) -> List[float]:
        """Find cyclic frequency peaks (simplified)"""
        # Simplified - in real implementation would compute cyclic autocorrelation
        peaks = []
        n = len(samples) // 4
        for lag in range(1, n):
            cyclic_autocorr = np.abs(np.mean(samples[:-lag] * np.conj(samples[lag:])))
            if cyclic_autocorr > np.std(np.abs(samples)) * 0.5:
                peaks.append(lag)
        return peaks
    
    def classify(self, features: Dict[str, float]) -> SignalClassification:
        """
        Classify signal based on features
        
        Args:
            features: Extracted features
            
        Returns:
            Signal classification
        """
        # Simplified rule-based classification
        # In real implementation, would use trained ML model
        
        papr = features.get('papr', 10)
        cyclic_peaks = features.get('cyclic_freq_peaks', 0)
        
        if cyclic_peaks > 10:
            return SignalClassification.FHSS
        elif papr > 12:
            return SignalClassification.MODULATED
        elif papr < 3:
            return SignalClassification.CW
        else:
            return SignalClassification.UNKNOWN
    
    def train(self, training_data: List[Tuple[np.ndarray, SignalClassification]]):
        """
        Train classifier (placeholder for ML training)
        
        Args:
            training_data: List of (samples, label) tuples
        """
        self.logger.info(f"Training classifier with {len(training_data)} samples")
        # In real implementation, would train ML model
        self.classifier_model = "trained_mock"


class AdvancedSDRProcessor:
    """Advanced SDR processor with all enhanced features"""
    
    def __init__(self, center_frequency: float = 433.92e6, sample_rate: float = 2.4e6):
        self.center_frequency = center_frequency
        self.sample_rate = sample_rate
        
        # Initialize components
        self.spectrum_monitor = SpectrumMonitor()
        self.cognitive_radio = CognitiveRadioEngine(center_frequency)
        self.signal_classifier = SignalClassifier()
        
        # Processing state
        self.current_channel = center_frequency
        self.is_adaptive = False
        
        self.logger = logging.getLogger(f"{__name__}.AdvancedSDR")
    
    def process_samples(self, samples: np.ndarray) -> Dict[str, Any]:
        """
        Process samples with full feature extraction
        
        Args:
            samples: IQ samples
            
        Returns:
            Processing results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'samples_analyzed': len(samples)
        }
        
        # Extract features for classification
        features = self.signal_classifier.extract_features(samples, self.sample_rate)
        results['features'] = features
        
        # Classify signal
        classification = self.signal_classifier.classify(features)
        results['classification'] = classification.value
        
        # Spectrum monitoring
        detections = self.spectrum_monitor.scan_spectrum(samples, self.sample_rate)
        results['detected_signals'] = len(detections)
        
        # Cognitive radio decisions
        if self.is_adaptive:
            channel_quality = self._estimate_channel_quality(samples, features)
            if channel_quality < 0.5:
                self._adapt_to_interference()
        
        return results
    
    def _estimate_channel_quality(self, samples: np.ndarray, 
                                  features: Dict[str, float]) -> float:
        """Estimate channel quality"""
        # Simple quality metric based on signal features
        snr_estimate = features.get('papr', 10) / 10  # Normalize
        return min(1.0, snr_estimate)
    
    def _adapt_to_interference(self):
        """Adapt to interference conditions"""
        new_channel = self.cognitive_radio.select_best_channel()
        if new_channel:
            self.logger.info(f"Adapting to new channel: {new_channel/1e6:.2f} MHz")
            self.current_channel = new_channel


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Advanced SDR Features...")
    
    # Test Spectrum Monitor
    print("\n1. Testing Spectrum Monitor...")
    monitor = SpectrumMonitor()
    monitor.start_monitoring()
    time.sleep(0.5)
    stats = monitor.get_statistics()
    print(f"   Monitoring stats: {stats}")
    monitor.stop_monitoring()
    
    # Test Cognitive Radio
    print("\n2. Testing Cognitive Radio...")
    cr = CognitiveRadioEngine()
    available = cr.scan_available_spectrum()
    print(f"   Available bands: {len(available)}")
    best = cr.select_best_channel()
    print(f"   Selected channel: {best/1e6:.2f} MHz" if best else "   No channel available")
    
    # Test Signal Classifier
    print("\n3. Testing Signal Classifier...")
    classifier = SignalClassifier()
    
    # Generate test signals
    test_signal = np.random.randn(1024) + 1j * np.random.randn(1024)
    features = classifier.extract_features(test_signal, 2.4e6)
    print(f"   Extracted features: {list(features.keys())[:5]}...")
    
    classification = classifier.classify(features)
    print(f"   Classification: {classification.value}")
    
    # Test Advanced SDR Processor
    print("\n4. Testing Advanced SDR Processor...")
    processor = AdvancedSDRProcessor()
    results = processor.process_samples(test_signal)
    print(f"   Processed: {results['samples_analyzed']} samples")
    print(f"   Classification: {results['classification']}")
    
    print("\n✅ Advanced SDR Features test completed!")