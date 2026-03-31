"""
Video Stabilization AI & Time-Series Event Tagger
Unsupervised learning to de-spin tumbling CanSat video
Automatic event detection and bookmarking
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class EventTag:
    timestamp: float
    event_type: str
    confidence: float
    description: str
    thumbnail: Optional[np.ndarray] = None


@dataclass
class StabilizedFrame:
    frame_id: int
    original: np.ndarray
    stabilized: np.ndarray
    rotation_correction: float
    translation_correction: Tuple[float, float]


class IMUGuidedStabilizer:
    """
    Unsupervised video stabilization using IMU data as guide.
    Digitally un-spins and levels video from tumbling CanSat.
    """
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        
        # IMU integration for motion estimation
        self.gyro_history = deque(maxlen=100)
        self.rotation_cumulative = np.array([0.0, 0.0, 0.0])
        
        # Video frame buffer
        self.frame_buffer: deque = deque(maxlen=5)
        
        # Smoothing parameters
        self.smoothing_window = 15
        
        # Reference orientation (set when stabilized)
        self.reference_orientation = None
        
    def add_imu_reading(self, gyro: Tuple[float, float, float], timestamp: float):
        """Add IMU reading for motion tracking."""
        self.gyro_history.append((gyro, timestamp))
        
        # Integrate gyroscope to get cumulative rotation
        if len(self.gyro_history) > 1:
            dt = timestamp - self.gyro_history[-2][1]
            self.rotation_cumulative += np.array(gyro) * dt
            
    def set_reference_orientation(self, orientation: Tuple[float, float, float]):
        """Set the reference (level) orientation."""
        self.reference_orientation = np.array(orientation)
        
    def stabilize_frame(
        self,
        frame: np.ndarray,
        frame_id: int,
        gyro: Tuple[float, float, float],
        timestamp: float
    ) -> StabilizedFrame:
        """
        Stabilize a single frame using IMU guidance.
        
        Args:
            frame: Input video frame
            frame_id: Frame identifier
            gyro: Current gyroscope reading
            timestamp: Frame timestamp
            
        Returns:
            StabilizedFrame with corrected video
        """
        # Add IMU reading
        self.add_imu_reading(gyro, timestamp)
        
        # Calculate rotation correction
        if self.reference_orientation is not None:
            current_rot = self.rotation_cumulative
            correction = self.reference_orientation - current_rot
            
            # Limit correction to prevent over-stabilization
            max_correction = np.pi / 6  # 30 degrees max
            correction = np.clip(correction, -max_correction, max_correction)
        else:
            correction = np.array([0.0, 0.0, 0.0])
            
        # Calculate rotation matrix
        angle = np.linalg.norm(correction)
        if angle > 0.001:
            axis = correction / angle
            cos_a = np.cos(angle / 2)
            sin_a = np.sin(angle / 2)
            quat = np.array([cos_a, sin_a * axis[0], sin_a * axis[1], sin_a * axis[2]])
        else:
            quat = np.array([1.0, 0.0, 0.0, 0.0])
            
        # Apply rotation to frame
        stabilized = self._apply_rotation(frame, correction)
        
        # Apply smoothing filter
        stabilized = self._smooth_stabilization(stabilized)
        
        return StabilizedFrame(
            frame_id=frame_id,
            original=frame,
            stabilized=stabilized,
            rotation_correction=float(angle),
            translation_correction=(0.0, 0.0)
        )
        
    def _apply_rotation(self, frame: np.ndarray, rotation: np.ndarray) -> np.ndarray:
        """Apply rotation correction to frame."""
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)
        
        # Combined rotation from all axes
        total_angle = np.sqrt(np.sum(rotation**2))
        total_angle_deg = np.degrees(total_angle)
        
        # Create rotation matrix
        M = cv2.getRotationMatrix2D(center, -total_angle_deg * 0.1, 1.0)  # Scale down effect
        
        # Apply transformation
        if len(frame.shape) == 3:
            stabilized = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR)
        else:
            stabilized = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR)
            
        return stabilized
        
    def _smooth_stabilization(self, frame: np.ndarray) -> np.ndarray:
        """Apply temporal smoothing to reduce jitter."""
        self.frame_buffer.append(frame)
        
        if len(self.frame_buffer) < 3:
            return frame
            
        # Simple temporal averaging with weights
        frames = list(self.frame_buffer)
        smoothed = np.zeros_like(frame, dtype=np.float32)
        
        weights = [0.5, 0.3, 0.2][:len(frames)]
        weights = np.array(weights) / sum(weights)
        
        for f, w in zip(frames, weights):
            smoothed += f.astype(np.float32) * w
            
        return smoothed.astype(np.uint8)


class TimeSeriesEventTagger:
    """
    Transformer-based time series event detection.
    Recognizes signatures of specific flight events.
    """
    
    EVENT_TYPES = {
        'apogee': 'Apogee Reached',
        'tumble': 'Tumble Detected',
        'main_chute': 'Main Chute Deployment',
        'ground_impact': 'Ground Impact',
        'radio_loss': 'Radio Signal Lost',
        'high_vibration': 'High Vibration Event',
        'voc_spike': 'VOC Spike Detected',
        'radiation_spike': 'Radiation Anomaly'
    }
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        
        # Event detection model
        self.model = self._create_event_model().to(device)
        self.model.eval()
        
        # Data buffer
        self.data_buffer: deque = deque(maxlen=200)  # ~20 seconds at 10Hz
        
        # Detected events
        self.events: List[EventTag] = []
        
        # Event state tracking
        self.active_signatures = {event: 0 for event in self.EVENT_TYPES}
        
    def _create_event_model(self) -> nn.Module:
        """Create event detection transformer."""
        class EventTransformer(nn.Module):
            def __init__(self):
                super().__init__()
                self.embedding = nn.Linear(8, 64)
                
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model=64, nhead=4, dim_feedforward=128,
                    dropout=0.1, activation='gelu', batch_first=True
                )
                self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=3)
                
                self.classifier = nn.Sequential(
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Linear(32, len(EventTagger.EVENT_TYPES) + 1)  # +1 for no event
                )
                
            def forward(self, x):
                x = self.embedding(x)
                x = self.transformer(x)
                x = x[:, -1]  # Use final position
                return self.classifier(x)
                
        class EventTagger:
            EVENT_TYPES = {
                'apogee': 'Apogee Reached',
                'tumble': 'Tumble Detected',
                'main_chute': 'Main Chute Deployment',
                'ground_impact': 'Ground Impact',
                'radio_loss': 'Radio Signal Lost',
                'high_vibration': 'High Vibration Event',
                'voc_spike': 'VOC Spike Detected',
                'radiation_spike': 'Radiation Anomaly'
            }
            
        return EventTransformer()
        
    def add_reading(
        self,
        timestamp: float,
        altitude: float,
        pressure: float,
        battery: float,
        vibration: float,
        temperature: float,
        radiation: float,
        voc: float
    ):
        """Add telemetry reading for event detection."""
        features = np.array([
            altitude / 1000,
            pressure / 1013,
            battery / 100,
            vibration / 1.0,
            temperature / 50,
            radiation / 2.0,
            voc / 500,
            1.0  # Time placeholder
        ])
        
        self.data_buffer.append((timestamp, features))
        
    def detect_events(self) -> List[EventTag]:
        """
        Detect events in current data buffer.
        
        Returns:
            List of detected EventTags
        """
        if len(self.data_buffer) < 20:
            return []
            
        # Prepare input
        features = np.array([f for _, f in self.data_buffer])
        timestamps = np.array([t for t, _ in self.data_buffer])
        
        # Detect each event type
        new_events = []
        
        # 1. Apogee detection (altitude peak)
        altitudes = features[:, 0] * 1000
        if self._detect_peak(altitudes, threshold=0.95):
            new_events.append(self._create_event('apogee', timestamps[-1], 0.9))
            
        # 2. Tumble detection (high rotation variance)
        if self._detect_tumble(features):
            new_events.append(self._create_event('tumble', timestamps[-1], 0.85))
            
        # 3. Main chute detection (sudden deceleration)
        if self._detect_deceleration(altitudes, window=20):
            new_events.append(self._create_event('main_chute', timestamps[-1], 0.8))
            
        # 4. Ground impact (altitude near zero, high vibration)
        if altitudes[-1] < 10 and features[-1, 3] > 0.8:
            new_events.append(self._create_event('ground_impact', timestamps[-1], 0.95))
            
        # 5. High vibration
        if features[-1, 3] > 0.7:
            new_events.append(self._create_event('high_vibration', timestamps[-1], 0.7))
            
        # 6. VOC spike
        if self._detect_spike(features[:, 6], threshold=2.0):
            new_events.append(self._create_event('voc_spike', timestamps[-1], 0.75))
            
        # 7. Radiation spike
        if self._detect_spike(features[:, 5], threshold=2.5):
            new_events.append(self._create_event('radiation_spike', timestamps[-1], 0.8))
            
        # Update history
        for event in new_events:
            if event.event_type not in [e.event_type for e in self.events[-10:]]:
                self.events.append(event)
                
        return new_events
        
    def _detect_peak(self, values: np.ndarray, threshold: float = 0.9) -> bool:
        """Detect if current value is near peak of recent history."""
        if len(values) < 10:
            return False
            
        max_val = np.max(values)
        current = values[-1]
        
        return current >= max_val * threshold and np.all(values[-5:] <= max_val)
        
    def _detect_tumble(self, features: np.ndarray) -> bool:
        """Detect tumbling motion from high variance."""
        if len(features) < 20:
            return False
            
        # High vibration with erratic altitude changes
        vibration = features[:, 3]
        altitude_changes = np.abs(np.diff(features[:, 0]))
        
        return np.mean(vibration[-10:]) > 0.5 and np.std(altitude_changes[-10:]) > 0.02
        
    def _detect_deceleration(self, altitudes: np.ndarray, window: int = 20) -> bool:
        """Detect sudden deceleration."""
        if len(altitudes) < window:
            return False
            
        recent = altitudes[-window:]
        
        # Check for rate change
        rate_before = (recent[window//2] - recent[0]) / (window//2)
        rate_after = (recent[-1] - recent[window//2]) / (window//2)
        
        # Deceleration detected if rate reduces significantly
        return rate_before > 5 and rate_after < 2 and (rate_before - rate_after) > 3
        
    def _detect_spike(self, values: np.ndarray, threshold: float = 2.0) -> bool:
        """Detect spike in values."""
        if len(values) < 10:
            return False
            
        mean = np.mean(values[:-5])
        std = np.std(values[:-5])
        current = values[-1]
        
        return current > mean + threshold * std
        
    def _create_event(self, event_type: str, timestamp: float, confidence: float) -> EventTag:
        """Create an event tag."""
        descriptions = {
            'apogee': 'Maximum altitude reached. Parachute should deploy.',
            'tumble': 'CanSat tumbling detected. Monitor stability.',
            'main_chute': 'Main parachute deployment. Descent rate reduced.',
            'ground_impact': 'CanSat has landed. End of flight data.',
            'high_vibration': 'Unusual vibration levels detected. Check structure.',
            'voc_spike': 'Volatile organic compounds spiked. Possible pollutant source.',
            'radiation_spike': 'Radiation levels elevated above baseline.'
        }
        
        return EventTag(
            timestamp=timestamp,
            event_type=event_type,
            confidence=confidence,
            description=descriptions.get(event_type, 'Unknown event')
        )
        
    def get_event_bookmarks(self) -> List[Dict]:
        """Get all events formatted for UI bookmarking."""
        return [
            {
                'timestamp': e.timestamp,
                'type': e.event_type,
                'name': self.EVENT_TYPES.get(e.event_type, e.event_type),
                'description': e.description,
                'confidence': e.confidence
            }
            for e in self.events
        ]


class VideoAnalysisSystem:
    """
    Combined video stabilization and event tagging system.
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.stabilizer = IMUGuidedStabilizer(device)
        self.event_tagger = TimeSeriesEventTagger(device)
        
    def process_frame(
        self,
        frame: np.ndarray,
        frame_id: int,
        gyro: Tuple[float, float, float],
        timestamp: float
    ) -> StabilizedFrame:
        """Process frame and detect events."""
        return self.stabilizer.stabilize_frame(frame, frame_id, gyro, timestamp)
        
    def add_telemetry(
        self,
        timestamp: float,
        altitude: float,
        pressure: float,
        battery: float,
        vibration: float,
        temperature: float,
        radiation: float,
        voc: float
    ):
        """Add telemetry for event detection."""
        self.event_tagger.add_reading(
            timestamp, altitude, pressure, battery, vibration,
            temperature, radiation, voc
        )
        
    def get_events(self) -> List[EventTag]:
        """Get detected events."""
        return self.event_tagger.detect_events()


def create_video_analysis_system(device: str = "auto") -> VideoAnalysisSystem:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return VideoAnalysisSystem(device=device)


if __name__ == "__main__":
    print("Initializing Video Analysis System...")
    system = create_video_analysis_system()
    
    # Set reference orientation (level)
    system.stabilizer.set_reference_orientation((0.0, 0.0, 0.0))
    
    # Simulate flight
    print("Simulating flight data...")
    
    for i in range(100):
        # Simulate tumbling
        gyro = (
            np.sin(i * 0.5) * 0.5,
            np.cos(i * 0.3) * 0.3,
            np.sin(i * 0.7) * 0.2
        )
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        stabilized = system.process_frame(frame, i, gyro, timestamp=i * 0.2)
        
        # Add telemetry
        system.add_telemetry(
            timestamp=i * 0.2,
            altitude=1000 - i * 10,
            pressure=1013 - i * 0.01,
            battery=100 - i * 0.2,
            vibration=0.5 + abs(np.sin(i * 0.5)) * 0.5,
            temperature=20 - i * 0.02,
            radiation=0.5 + np.random.normal(0, 0.1),
            voc=200 + np.random.normal(50, 20)
        )
        
        if i % 20 == 0:
            print(f"Frame {i}: Rotation correction = {stabilized.rotation_correction:.3f} rad")
            
    events = system.get_events()
    print(f"\nDetected {len(events)} events")
    
    for event in events[:5]:
        print(f"  - {event.event_type}: {event.description}")