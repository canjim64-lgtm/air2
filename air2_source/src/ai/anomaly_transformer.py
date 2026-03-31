"""
Transformer-Based Anomaly Detection (TFT)
GPU-accelerated temporal anomaly detection for sensor data
Detects slow failures before threshold alarms trigger
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class AnomalyResult:
    timestamp: float
    is_anomaly: bool
    anomaly_type: str
    confidence: float
    score: float
    affected_sensors: List[str]
    description: str


class TimeSeriesTransformer(nn.Module):
    """
    Transformer for time series anomaly detection.
    Feeds last 10 seconds of sensor data for pattern recognition.
    """
    
    def __init__(
        self,
        input_dim: int = 8,  # Sensors: alt, pressure, battery, vibration, temp, humidity, signal, cpu
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 4,
        dropout: float = 0.1,
        sequence_length: int = 100  # 10 seconds at 10Hz
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        
        # Input embedding with temporal encoding
        self.input_proj = nn.Linear(input_dim + 2, d_model)  # +2 for time encoding
        
        # Positional encoding
        self.pos_embedding = nn.Parameter(torch.randn(1, sequence_length, d_model))
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # Multi-scale convolution for local patterns
        self.conv_layers = nn.ModuleList([
            nn.Conv1d(d_model, d_model // 2, kernel_size=k, padding=k // 2)
            for k in [3, 7, 15]
        ])
        
        # Anomaly scoring head
        self.anomaly_head = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, 1),
            nn.Sigmoid()
        )
        
        # Type classification head
        self.type_head = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Linear(d_model, 6),  # 6 anomaly types
            nn.Softmax(dim=-1)
        )
        
        # Reconstruction decoder for autoencoder component
        self.decoder = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Linear(d_model, input_dim)
        )
        
    def forward(
        self,
        x: torch.Tensor,  # [batch, seq_len, input_dim]
        time_encoding: Optional[torch.Tensor] = None  # [batch, seq_len, 2]
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            x: Sensor data [batch, seq_len, input_dim]
            time_encoding: Time features [batch, seq_len, 2]
            
        Returns:
            anomaly_score: [batch, 1] - probability of anomaly
            anomaly_type: [batch, 6] - type distribution
            reconstruction: [batch, seq_len, input_dim] - for reconstruction error
        """
        batch_size = x.size(0)
        
        # Add time encoding if provided
        if time_encoding is not None:
            x = torch.cat([x, time_encoding], dim=-1)
            
        # Input projection
        x = self.input_proj(x)
        
        # Add positional encoding
        x = x + self.pos_embedding[:, :x.size(1), :]
        
        # Transformer encoding
        transformer_out = self.transformer(x)
        
        # Multi-scale convolutions
        conv_out = transformer_out.transpose(1, 2)  # [batch, d_model, seq]
        multi_scale_features = []
        for conv in self.conv_layers:
            feat = F.relu(conv(conv_out))
            multi_scale_features.append(feat)
            
        # Concatenate multi-scale features
        multi_scale = torch.cat(multi_scale_features, dim=1).transpose(1, 2)
        
        # Global and local features
        global_feat = transformer_out[:, -1, :]  # Last timestep
        local_feat = multi_scale.mean(dim=1)  # Average across time
        
        combined = torch.cat([global_feat, local_feat], dim=-1)
        
        # Score predictions
        anomaly_score = self.anomaly_head(combined)
        anomaly_type = self.type_head(combined)
        
        # Reconstruction
        reconstruction = self.decoder(transformer_out)
        
        return anomaly_score.squeeze(-1), anomaly_type, reconstruction


class AnomalyDetector:
    """
    Real-time anomaly detection using temporal transformer.
    Detects slow failures, voltage sags, and subtle sensor patterns.
    """
    
    ANOMALY_TYPES = [
        'NOMINAL',
        'BATTERY_VOLTAGE_SAG',
        'SENSOR_FREEZE',
        'COMMUNICATION_LOSS',
        'TEMPERATURE_DRIFT',
        'VIBRATION_ANOMALY'
    ]
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        window_size: int = 100  # 10 seconds at 10Hz
    ):
        self.device = device
        self.window_size = window_size
        
        # Initialize model
        self.model = TimeSeriesTransformer(sequence_length=window_size).to(device)
        self.model.eval()
        
        # Data buffers
        self.sensor_buffer: deque = deque(maxlen=window_size)
        self.time_buffer: deque = deque(maxlen=window_size)
        
        # Detection thresholds
        self.anomaly_threshold = 0.7
        self.reconstruction_threshold = 2.5  # Standard deviations
        
        # History
        self.anomaly_history: List[AnomalyResult] = []
        
        # Normal baseline (computed from initial data)
        self.baseline_mean = None
        self.baseline_std = None
        
    def add_sensor_reading(
        self,
        timestamp: float,
        altitude: float,
        pressure: float,
        battery: float,
        vibration: float,
        temperature: float,
        humidity: float,
        signal_strength: float,
        cpu_temp: float = 50.0
    ):
        """Add a new sensor reading."""
        reading = np.array([
            altitude, pressure, battery, vibration,
            temperature, humidity, signal_strength, cpu_temp
        ])
        
        self.sensor_buffer.append(reading)
        self.time_buffer.append(timestamp)
        
    def detect(self) -> AnomalyResult:
        """
        Perform anomaly detection on current buffer.
        
        Returns:
            AnomalyResult with detection details
        """
        if len(self.sensor_buffer) < self.window_size // 2:
            return AnomalyResult(
                timestamp=self.time_buffer[-1] if self.time_buffer else 0,
                is_anomaly=False,
                anomaly_type='NOMINAL',
                confidence=0.0,
                score=0.0,
                affected_sensors=[],
                description='Insufficient data'
            )
            
        # Prepare input
        sensor_data = np.array(list(self.sensor_buffer))
        timestamps = np.array(list(self.time_buffer))
        
        # Normalize timestamps
        time_encoding = self._compute_time_encoding(timestamps)
        
        # Convert to tensors
        sensor_tensor = torch.FloatTensor(sensor_data).unsqueeze(0).to(self.device)
        time_tensor = torch.FloatTensor(time_encoding).unsqueeze(0).to(self.device)
        
        # Run model
        with torch.no_grad():
            anomaly_score, anomaly_type, reconstruction = self.model(sensor_tensor, time_tensor)
            
        # Get predictions
        score = anomaly_score[0].item()
        type_probs = anomaly_type[0].cpu().numpy()
        
        # Compute reconstruction error
        recon_error = torch.mean((sensor_tensor - reconstruction) ** 2).item()
        
        # Check baseline statistics
        if self.baseline_mean is not None:
            z_scores = np.abs(sensor_data[-1] - self.baseline_mean) / (self.baseline_std + 1e-6)
            anomalous_sensors = []
            for i, z in enumerate(z_scores):
                if z > self.reconstruction_threshold:
                    sensor_names = ['altitude', 'pressure', 'battery', 'vibration',
                                   'temperature', 'humidity', 'signal', 'cpu_temp']
                    anomalous_sensors.append(sensor_names[i])
        else:
            anomalous_sensors = []
            
        # Determine anomaly type
        type_idx = np.argmax(type_probs)
        anomaly_type_name = self.ANOMALY_TYPES[type_idx]
        
        is_anomaly = score > self.anomaly_threshold
        
        result = AnomalyResult(
            timestamp=timestamps[-1],
            is_anomaly=is_anomaly,
            anomaly_type=anomaly_type_name,
            confidence=score,
            score=recon_error,
            affected_sensors=anomalous_sensors,
            description=self._generate_description(anomaly_type_name, anomalous_sensors, recon_error)
        )
        
        if is_anomaly:
            self.anomaly_history.append(result)
            
        return result
        
    def _compute_time_encoding(self, timestamps: np.ndarray) -> np.ndarray:
        """Compute time-based features for transformer."""
        if len(timestamps) < 2:
            return np.zeros((len(timestamps), 2))
            
        # Time since start
        t_start = timestamps[0]
        time_since_start = (timestamps - t_start).reshape(-1, 1)
        
        # Normalized position in window
        positions = np.linspace(0, 1, len(timestamps)).reshape(-1, 1)
        
        return np.concatenate([time_since_start, positions], axis=1)
        
    def _generate_description(
        self,
        anomaly_type: str,
        sensors: List[str],
        reconstruction_error: float
    ) -> str:
        """Generate human-readable description."""
        if anomaly_type == 'NOMINAL':
            return 'All systems operating normally'
            
        descriptions = {
            'BATTERY_VOLTAGE_SAG': 'Battery voltage drop detected - possible excessive power draw or RF transmission issue',
            'SENSOR_FREEZE': 'Sensor readings frozen - possible hardware malfunction or connection loss',
            'COMMUNICATION_LOSS': 'Signal strength anomaly detected - possible RF interference or antenna issue',
            'TEMPERATURE_DRIFT': 'Temperature reading drift - possible thermal sensor malfunction or environmental change',
            'VIBRATION_ANOMALY': 'Unusual vibration patterns detected - possible mechanical issue or structural damage'
        }
        
        base_desc = descriptions.get(anomaly_type, 'Unknown anomaly detected')
        
        if sensors:
            base_desc += f' (Affected: {", ".join(sensors)})'
            
        return base_desc
        
    def update_baseline(self, num_samples: int = 100):
        """Update the baseline statistics for anomaly detection."""
        if len(self.sensor_buffer) < num_samples:
            return
            
        samples = np.array(list(self.sensor_buffer)[-num_samples:])
        self.baseline_mean = np.mean(samples, axis=0)
        self.baseline_std = np.std(samples, axis=0) + 1e-6
        
    def get_anomaly_summary(self) -> Dict:
        """Get summary of detected anomalies."""
        if not self.anomaly_history:
            return {'status': 'No anomalies detected', 'total': 0}
            
        type_counts = {}
        for result in self.anomaly_history:
            type_counts[result.anomaly_type] = type_counts.get(result.anomaly_type, 0) + 1
            
        return {
            'total_anomalies': len(self.anomaly_history),
            'by_type': type_counts,
            'most_common': max(type_counts, key=type_counts.get) if type_counts else 'None',
            'recent_anomalies': self.anomaly_history[-10:]
        }


def create_anomaly_detector(device: str = "auto") -> AnomalyDetector:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return AnomalyDetector(device=device)


# Demo
if __name__ == "__main__":
    print("Initializing Anomaly Detector...")
    detector = create_anomaly_detector()
    
    # Simulate normal sensor data
    print("Simulating sensor data...")
    
    for i in range(200):
        # Normal operation with slight noise
        detector.add_sensor_reading(
            timestamp=i * 0.1,
            altitude=500 - i * 0.5,
            pressure=1013 - i * 0.01,
            battery=12.5 + np.random.normal(0, 0.1),
            vibration=0.1 + np.random.normal(0, 0.02),
            temperature=20 + np.random.normal(0, 0.5),
            humidity=50 + np.random.normal(0, 1),
            signal_strength=-65 + np.random.normal(0, 2)
        )
        
    # Update baseline
    detector.update_baseline()
    
    # Check for anomalies
    result = detector.detect()
    print(f"\nAnomaly Detection Result:")
    print(f"  Type: {result.anomaly_type}")
    print(f"  Is Anomaly: {result.is_anomaly}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Description: {result.description}")
    
    # Simulate voltage sag
    print("\nSimulating battery voltage sag...")
    for i in range(20):
        detector.add_sensor_reading(
            timestamp=20 + i * 0.1,
            altitude=490,
            pressure=1000,
            battery=11.5 - i * 0.1,  # Sagging battery
            vibration=0.15,
            temperature=22,
            humidity=52,
            signal_strength=-63
        )
        
    result = detector.detect()
    print(f"\nAnomaly Detection Result:")
    print(f"  Type: {result.anomaly_type}")
    print(f"  Is Anomaly: {result.is_anomaly}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Description: {result.description}")