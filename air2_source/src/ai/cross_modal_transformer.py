"""
Cross-Modal Transformer for GPS/IMU/Optical Flow Validation
Detects GPS Jamming, Sensor Freeze, and Sensor Discrepancies
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import torch
import torch.nn as nn


@dataclass
class SensorReading:
    timestamp: float
    gps_lat: float
    gps_lon: float
    gps_alt: float
    gps_velocity: float
    imu_gyro_x: float
    imu_gyro_y: float
    imu_gyro_z: float
    imu_accel_x: float
    imu_accel_y: float
    imu_accel_z: float
    optical_flow_x: float
    optical_flow_y: float
    barometer_alt: float


class CrossModalTransformer(nn.Module):
    """
    Cross-Modal Transformer comparing visual optical flow against IMU/Barometer data.
    Detects GPS Jamming or Sensor Freeze events when camera shows movement but GPS says stationary.
    """
    
    def __init__(
        self,
        input_dim: int = 14,
        hidden_dim: int = 256,
        num_heads: int = 8,
        num_layers: int = 4,
        dropout: float = 0.1
    ):
        super().__init__()
        
        # Input embedding layers for each sensor modality
        self.gps_embedding = nn.Sequential(
            nn.Linear(4, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        self.imu_embedding = nn.Sequential(
            nn.Linear(6, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        self.optical_embedding = nn.Sequential(
            nn.Linear(3, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Cross-modal attention layers
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # Transformer encoder layers
        self.transformer_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=hidden_dim,
                nhead=num_heads,
                dim_feedforward=hidden_dim * 4,
                dropout=dropout,
                activation='gelu',
                batch_first=True
            ),
            num_layers=num_layers
        )
        
        # Output heads
        self.anomaly_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 3),  # GPS_JAM, SENSOR_FREEZE, NOMINAL
            nn.Softmax(dim=-1)
        )
        
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
        
        self.fusion_weights = nn.Linear(hidden_dim * 3, 3)
        
    def forward(
        self,
        gps: torch.Tensor,      # [batch, seq, 4]
        imu: torch.Tensor,       # [batch, seq, 6]
        optical: torch.Tensor,   # [batch, seq, 3]
        baro: torch.Tensor       # [batch, seq, 1]
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            gps: GPS coordinates [lat, lon, alt, velocity]
            imu: IMU readings [gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z]
            optical: Optical flow [dx, dy, magnitude]
            baro: Barometer altitude
            
        Returns:
            anomaly_probs: [GPS_JAM, SENSOR_FREEZE, NOMINAL] probabilities
            confidence: Detection confidence
            fusion_weights: Cross-modal attention weights
        """
        batch_size = gps.size(0)
        seq_len = gps.size(1)
        
        # Embed each modality
        gps_emb = self.gps_embedding(gps)
        imu_emb = self.imu_embedding(imu)
        opt_emb = self.optical_embedding(optical)
        
        # Concatenate for cross-modal processing
        combined = torch.cat([gps_emb, imu_emb, opt_emb], dim=-1)
        
        # Cross-modal attention
        attn_output, attn_weights = self.cross_attention(
            combined, combined, combined
        )
        
        # Transformer encoding
        transformer_out = self.transformer_encoder(attn_output)
        
        # Use final sequence position for decision
        final_state = transformer_out[:, -1, :]
        
        # Compute anomaly classification
        anomaly_probs = self.anomaly_head(final_state)
        confidence = self.confidence_head(final_state)
        
        # Compute fusion weights for interpretability
        fusion = self.fusion_weights(
            torch.cat([gps_emb[:, -1], imu_emb[:, -1], opt_emb[:, -1]], dim=-1).unsqueeze(1)
        )
        fusion_weights = torch.softmax(fusion.squeeze(1), dim=-1)
        
        return anomaly_probs, confidence.squeeze(-1), fusion_weights


class CrossModalValidator:
    """
    Real-time cross-modal validation system for CanSat sensor fusion.
    Flags "GPS Jamming" or "Sensor Freeze" events.
    """
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        window_size: int = 50
    ):
        self.device = device
        self.window_size = window_size
        
        self.model = CrossModalTransformer().to(device)
        self.model.eval()
        
        # Sliding window buffers
        self.gps_buffer = []
        self.imu_buffer = []
        self.optical_buffer = []
        self.baro_buffer = []
        self.timestamps = []
        
        # Alert thresholds
        self.jamming_threshold = 0.85
        self.freeze_threshold = 0.75
        
        # Event history
        self.event_history: List[Dict] = []
        
    def add_reading(self, reading: SensorReading):
        """Add a new sensor reading to the buffers."""
        self.timestamps.append(reading.timestamp)
        self.gps_buffer.append([reading.gps_lat, reading.gps_lon, reading.gps_alt, reading.gps_velocity])
        self.imu_buffer.append([
            reading.imu_gyro_x, reading.imu_gyro_y, reading.imu_gyro_z,
            reading.imu_accel_x, reading.imu_accel_y, reading.imu_accel_z
        ])
        self.optical_buffer.append([reading.optical_flow_x, reading.optical_flow_y, 
                                     np.sqrt(reading.optical_flow_x**2 + reading.optical_flow_y**2)])
        self.baro_buffer.append([reading.barometer_alt])
        
        # Keep only last window_size readings
        if len(self.timestamps) > self.window_size:
            self.timestamps = self.timestamps[-self.window_size:]
            self.gps_buffer = self.gps_buffer[-self.window_size:]
            self.imu_buffer = self.imu_buffer[-self.window_size:]
            self.optical_buffer = self.optical_buffer[-self.window_size:]
            self.baro_buffer = self.baro_buffer[-self.window_size:]
            
    def validate(self) -> Dict:
        """
        Perform cross-modal validation on current buffer.
        
        Returns:
            Dict with anomaly detection results
        """
        if len(self.timestamps) < 10:
            return {"status": "INSUFFICIENT_DATA", "confidence": 0.0}
            
        # Convert to tensors
        gps_t = torch.FloatTensor([self.gps_buffer]).to(self.device)
        imu_t = torch.FloatTensor([self.imu_buffer]).to(self.device)
        opt_t = torch.FloatTensor([self.optical_buffer]).to(self.device)
        baro_t = torch.FloatTensor([self.baro_buffer]).to(self.device)
        
        with torch.no_grad():
            anomaly_probs, confidence, fusion_weights = self.model(gps_t, imu_t, opt_t, baro_t)
            
        anomaly_probs = anomaly_probs[0].cpu().numpy()
        confidence = confidence[0].cpu().item()
        fusion_weights = fusion_weights[0].cpu().numpy()
        
        # Interpret results
        gps_jam_prob = anomaly_probs[0]
        sensor_freeze_prob = anomaly_probs[1]
        nominal_prob = anomaly_probs[2]
        
        event_type = "NOMINAL"
        alert_level = "NONE"
        
        if gps_jam_prob > self.jamming_threshold:
            event_type = "GPS_JAMMING_DETECTED"
            alert_level = "CRITICAL"
        elif sensor_freeze_prob > self.freeze_threshold:
            event_type = "SENSOR_FREEZE_DETECTED"
            alert_level = "WARNING"
            
        result = {
            "status": event_type,
            "alert_level": alert_level,
            "confidence": confidence,
            "probabilities": {
                "gps_jamming": float(gps_jam_prob),
                "sensor_freeze": float(sensor_freeze_prob),
                "nominal": float(nominal_prob)
            },
            "fusion_weights": {
                "gps_modality": float(fusion_weights[0]),
                "imu_modality": float(fusion_weights[1]),
                "optical_modality": float(fusion_weights[2])
            },
            "timestamp": self.timestamps[-1]
        }
        
        # Log event
        if alert_level != "NONE":
            self.event_history.append(result)
            
        return result
    
    def get_event_summary(self) -> Dict:
        """Get summary of detected events."""
        total_events = len(self.event_history)
        gps_jams = sum(1 for e in self.event_history if e["status"] == "GPS_JAMMING_DETECTED")
        freezes = sum(1 for e in self.event_history if e["status"] == "SENSOR_FREEZE_DETECTED")
        
        return {
            "total_events": total_events,
            "gps_jamming_count": gps_jams,
            "sensor_freeze_count": freezes,
            "events": self.event_history[-100:]  # Last 100 events
        }


def create_cross_modal_validator(device: str = "auto") -> CrossModalValidator:
    """Factory function to create a cross-modal validator."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return CrossModalValidator(device=device)


# Demo usage
if __name__ == "__main__":
    validator = create_cross_modal_validator()
    
    # Simulate normal flight data
    print("Simulating CanSat flight data...")
    for i in range(100):
        reading = SensorReading(
            timestamp=i * 0.2,
            gps_lat=37.7749 + np.random.normal(0, 0.0001),
            gps_lon=-122.4194 + np.random.normal(0, 0.0001),
            gps_alt=500 - i * 5 + np.random.normal(0, 1),
            gps_velocity=np.random.uniform(5, 15),
            imu_gyro_x=np.random.normal(0, 0.1),
            imu_gyro_y=np.random.normal(0, 0.1),
            imu_gyro_z=np.random.normal(0, 0.1),
            imu_accel_x=np.random.normal(0, 0.5),
            imu_accel_y=np.random.normal(0, 0.5),
            imu_accel_z=9.8 + np.random.normal(0, 0.2),
            optical_flow_x=np.random.uniform(-2, 2),
            optical_flow_y=np.random.uniform(-2, 2),
            barometer_alt=500 - i * 5 + np.random.normal(0, 0.5)
        )
        validator.add_reading(reading)
        
    result = validator.validate()
    print(f"\nValidation Result: {result}")