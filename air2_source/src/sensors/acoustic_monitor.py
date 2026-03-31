"""
Acoustic Structural Health Monitor (ASHM) for AirOne Professional v4.0
Performs FFT-based peak detection on vibration buffers to identify structural stress.
"""
import logging
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AcousticHealthMonitor:
    def __init__(self, sampling_rate: int = 44100):
        self.logger = logging.getLogger(f"{__name__}.AcousticHealthMonitor")
        self.sampling_rate = sampling_rate
        self.anomaly_threshold = 0.35
        self.logger.info("Acoustic Monitor Initialized.")

    def analyze_audio_buffer(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Analyzes real vibration data for anomalies using power spectral density peaks."""
        if audio_data is None or len(audio_data) < 128:
            return {"status": "INSUFFICIENT_DATA"}

        # Apply Hanning window to prevent spectral leakage
        window = np.hanning(len(audio_data))
        windowed_data = audio_data * window
        
        # FFT and Power Spectral Density
        fft_values = np.fft.rfft(windowed_data)
        psd = np.abs(fft_values)**2
        freqs = np.fft.rfftfreq(len(audio_data), 1.0/self.sampling_rate)
        
        dominant_idx = np.argmax(psd)
        dominant_freq = freqs[dominant_idx]
        peak_pwr = psd[dominant_idx]
        
        # Detection logic
        status = "NOMINAL"
        stress_score = 0.0
        
        # Characteristic high-frequency harmonic spike (> 10kHz) indicates structural failure
        if dominant_freq > 10000 and peak_pwr > 1000:
            status = "STRUCTURAL_FAILURE_DETECTED"
            stress_score = 1.0
        elif 2000 < dominant_freq < 5000:
            status = "VIBRATION_WARNING"
            stress_score = 0.4

        return {
            "status": status,
            "dom_freq_hz": round(float(dominant_freq), 1),
            "peak_power": round(float(peak_pwr), 2),
            "stress_score": stress_score
        }
