"""
Isotope Spectral Fingerprinting & Radiation Analysis
1D-CNN for real-time radiation source classification
Altitude-Radiation Correlation Modeling with Dynamic Baseline
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import torch
import torch.nn as nn


@dataclass
class RadiationReading:
    timestamp: float
    count_rate: float  # counts per second
    energy_spectrum: np.ndarray  # Pulse height distribution
    altitude: float
    temperature: float


@dataclass
class ClassificationResult:
    source_type: str
    confidence: float
    is_anomaly: bool
    anomaly_score: float
    natural_baseline: float
    dynamic_threshold: float


class SpectrumClassifier1DCNN(nn.Module):
    """
    1D-CNN for radiation spectral fingerprinting.
    Classifies radiation sources from energy spectrum.
    """
    
    def __init__(
        self,
        input_length: int = 256,
        num_classes: int = 5
    ):
        super().__init__()
        
        self.conv_layers = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=7, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),
            
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(16)
        )
        
        self.fc_layers = nn.Sequential(
            nn.Linear(128 * 16, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes),
            nn.Softmax(dim=-1)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)
        return self.fc_layers(x)


class AltitudeCorrelationModel(nn.Module):
    """
    Regression model for altitude-radiation correlation.
    Creates dynamic baseline for anomaly detection.
    """
    
    def __init__(self):
        super().__init__()
        
        self.model = nn.Sequential(
            nn.Linear(3, 64),  # altitude, temperature, pressure
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Softmax(dim=0)
        )
        
    def forward(self, altitude: torch.Tensor, temp: torch.Tensor, pressure: torch.Tensor) -> torch.Tensor:
        x = torch.stack([altitude, temp, pressure], dim=-1)
        return self.model(x)


class RadiationAnalyzer:
    """
    Complete radiation analysis system.
    Classifies sources and detects anomalies using altitude correlation.
    """
    
    SOURCE_TYPES = [
        'Natural Background',
        'Technogenic/Industrial', 
        'Elevated Cosmic',
        'Radon Progeny',
        'Unknown/Industrial'
    ]
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        
        # Models
        self.spectrum_classifier = SpectrumClassifier1DCNN().to(device)
        self.altitude_model = AltitudeCorrelationModel().to(device)
        
        self.spectrum_classifier.eval()
        self.altitude_model.eval()
        
        # Calibration data
        self.calibration_readings: List[RadiationReading] = []
        self.baseline_params = {'a': 0.15, 'b': 0.0003, 'c': 0.0}
        
        # History
        self.classification_history: List[ClassificationResult] = []
        
    def calibrate(self, readings: List[RadiationReading]):
        """Calibrate baseline model from known altitude readings."""
        self.calibration_readings = readings
        
        if len(readings) > 10:
            altitudes = np.array([r.altitude for r in readings])
            counts = np.array([r.count_rate for r in readings])
            
            # Fit exponential model: count_rate = a * exp(b * altitude) + c
            log_counts = np.log(counts + 1)
            coeffs = np.polyfit(altitudes, log_counts, 1)
            
            self.baseline_params = {
                'a': np.exp(coeffs[1]),
                'b': coeffs[0]
            }
            
    def predict_baseline(self, altitude: float) -> float:
        """Predict expected radiation at given altitude."""
        a = self.baseline_params['a']
        b = self.baseline_params['b']
        return a * np.exp(b * altitude) + 0.1
        
    def classify(
        self,
        reading: RadiationReading
    ) -> ClassificationResult:
        """
        Classify radiation source and detect anomalies.
        
        Args:
            reading: Radiation reading with spectrum
            
        Returns:
            ClassificationResult
        """
        # Prepare spectrum
        spectrum = reading.energy_spectrum[:256] if len(reading.energy_spectrum) >= 256 else np.pad(
            reading.energy_spectrum, (0, 256 - len(reading.energy_spectrum))
        )
        spectrum_tensor = torch.FloatTensor(spectrum).unsqueeze(0).unsqueeze(0).to(self.device)
        
        # Classify source type
        with torch.no_grad():
            probs = self.spectrum_classifier(spectrum_tensor)[0].cpu().numpy()
            
        class_idx = np.argmax(probs)
        source_type = self.SOURCE_TYPES[class_idx]
        confidence = probs[class_idx]
        
        # Check against altitude baseline
        expected = self.predict_baseline(reading.altitude)
        observed = reading.count_rate
        
        # Dynamic threshold based on variance
        if len(self.classification_history) > 10:
            recent_counts = [h.count_rate for h in self.classification_history[-20:]]
            std = np.std(recent_counts)
            threshold = expected + 2 * std
        else:
            threshold = expected * 1.5
            
        anomaly_score = max(0, (observed - expected) / (expected + 1))
        is_anomaly = observed > threshold
        
        result = ClassificationResult(
            source_type=source_type,
            confidence=float(confidence),
            is_anomaly=is_anomaly,
            anomaly_score=float(anomaly_score),
            natural_baseline=expected,
            dynamic_threshold=threshold
        )
        
        self.classification_history.append(ClassificationResult(
            source_type=result.source_type,
            confidence=result.confidence,
            is_anomaly=result.is_anomaly,
            anomaly_score=result.anomaly_score,
            natural_baseline=result.natural_baseline,
            dynamic_threshold=result.dynamic_threshold
        ))
        # Store count rate for threshold computation
        self.classification_history[-1].count_rate = observed
        
        return result
        
    def get_summary(self) -> Dict:
        """Get radiation analysis summary."""
        if not self.classification_history:
            return {'status': 'No data'}
            
        recent = self.classification_history[-50:]
        
        counts = [r.count_rate for r in recent]
        
        return {
            'avg_count_rate': np.mean(counts),
            'max_count_rate': np.max(counts),
            'anomaly_count': sum(1 for r in recent if r.is_anomaly),
            'source_distribution': self._get_source_distribution(recent),
            'current_baseline': self.predict_baseline(
                self.classification_history[-1].natural_baseline if hasattr(self.classification_history[-1], 'natural_baseline') else 500
            ) if self.classification_history else 0
        }
        
    def _get_source_distribution(self, recent: List[ClassificationResult]) -> Dict[str, int]:
        dist = {}
        for r in recent:
            dist[r.source_type] = dist.get(r.source_type, 0) + 1
        return dist


def create_radiation_analyzer(device: str = "auto") -> RadiationAnalyzer:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return RadiationAnalyzer(device=device)


if __name__ == "__main__":
    print("Initializing Radiation Analyzer...")
    analyzer = create_radiation_analyzer()
    
    # Simulate readings
    for i in range(30):
        spectrum = np.random.exponential(50, 256)
        # Add some peaks
        spectrum[50:60] += np.random.uniform(100, 200)
        spectrum[150:160] += np.random.uniform(50, 100)
        
        reading = RadiationReading(
            timestamp=i * 0.5,
            count_rate=10 + 5 * np.exp(0.005 * i * 50) + np.random.normal(0, 2),
            energy_spectrum=spectrum,
            altitude=i * 50,
            temperature=20
        )
        
        result = analyzer.classify(reading)
        
        if i % 5 == 0:
            print(f"Altitude {reading.altitude:.0f}m: {result.source_type}, "
                  f"Count={reading.count_rate:.1f}, Expected={result.natural_baseline:.1f}")
                
    summary = analyzer.get_summary()
    print(f"\nSummary: {summary}")