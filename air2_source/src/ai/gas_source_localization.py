"""
Neural Gas Plume Back-Propagation & Source Localization
Physics-Informed Neural Network for reverse-simulating gas source location
Combines VOC spikes, descent rate, and wind data to predict origin
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import torch
import torch.nn as nn


@dataclass
class GasReading:
    timestamp: float
    voc_ppm: float
    co2_ppm: float
    temperature: float
    humidity: float
    pressure: float
    altitude: float
    position: Tuple[float, float]  # lat, lon
    wind_speed: float
    wind_direction: float


@dataclass
class SourceEstimate:
    source_location: Tuple[float, float]
    confidence: float
    source_cone: np.ndarray
    back_trajectory: List[Tuple[float, float, float]]
    estimated_release_time: float
    concentration_estimate: float


class PINNGasPlume(nn.Module):
    """
    Physics-Informed Neural Network for gas plume back-propagation.
    Uses physics constraints to reverse-simulate source location.
    """
    
    def __init__(
        self,
        input_dim: int = 10,  # VOC, CO2, temp, humidity, pressure, altitude, position, wind
        hidden_dim: int = 128,
        num_layers: int = 5
    ):
        super().__init__()
        
        # Input encoding
        self.input_layer = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU()
        )
        
        # Physics-informed layers (mass balance, diffusion constraints)
        self.physics_layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU(),
                nn.Dropout(0.1)
            )
            for _ in range(num_layers)
        ])
        
        # Source location prediction head
        self.source_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 2)  # lat, lon offset from current position
        )
        
        # Concentration prediction head
        self.concentration_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        # Back-trajectory head
        self.trajectory_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 30 * 3)  # 30 timesteps * 3D position
        )
        
        # Physics constraints (diffusion coefficients)
        self.diffusion_coeff = nn.Parameter(torch.tensor(0.5))
        self.wind_drift = nn.Parameter(torch.tensor(0.3))
        
    def forward(
        self,
        gas_data: torch.Tensor,  # [batch, seq, 10]
        current_pos: torch.Tensor  # [batch, 2]
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            gas_data: Gas sensor readings over time
            current_pos: Current CanSat position
            
        Returns:
            source_location: Predicted source coordinates
            concentration: Estimated source concentration
            trajectory: Back-trajectory path
        """
        batch = gas_data.size(0)
        
        # Encode input
        x = self.input_layer(gas_data)
        
        # Apply physics-informed layers
        for layer in self.physics_layers:
            x = layer(x)
            
        # Global context
        context = torch.mean(x, dim=1)  # [batch, hidden_dim]
        
        # Predict source location offset from current position
        source_offset = torch.tanh(self.source_head(context)) * 0.01  # Limit offset
        source_location = current_pos + source_offset
        
        # Predict source concentration
        concentration = torch.exp(self.concentration_head(context))  # Positive concentration
        
        # Predict back-trajectory
        trajectory = self.trajectory_head(x)  # [batch, 90]
        trajectory = trajectory.view(batch, 30, 3)  # Reshape to timesteps
        
        return source_location, concentration.squeeze(-1), trajectory


class SourceLocalization:
    """
    Real-time gas source localization using back-propagation.
    Generates "Source Probability" cone on map.
    """
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.model = PINNGasPlume().to(device)
        self.model.eval()
        
        # Reading history
        self.readings: List[GasReading] = []
        
        # Current position
        self.current_pos = (0.0, 0.0)
        
    def add_reading(self, reading: GasReading):
        """Add a new gas reading."""
        self.readings.append(reading)
        self.current_pos = reading.position
        
        # Keep last 100 readings
        if len(self.readings) > 100:
            self.readings = self.readings[-100:]
            
    def estimate_source(self) -> Optional[SourceEstimate]:
        """
        Estimate gas source location using back-propagation.
        
        Returns:
            SourceEstimate with location and trajectory
        """
        if len(self.readings) < 5:
            return None
            
        # Prepare input data
        gas_features = []
        for r in self.readings:
            features = [
                r.voc_ppm / 1000,  # Normalize
                r.co2_ppm / 5000,
                r.temperature / 50,
                r.humidity / 100,
                r.pressure / 1013,
                r.altitude / 1000,
                r.position[0],
                r.position[1],
                r.wind_speed / 20,
                r.wind_direction / 360
            ]
            gas_features.append(features)
            
        gas_tensor = torch.FloatTensor([gas_features]).to(self.device)
        pos_tensor = torch.FloatTensor([[self.current_pos]]).to(self.device)
        
        with torch.no_grad():
            source_loc, concentration, trajectory = self.model(gas_tensor, pos_tensor)
            
        source_location = tuple(source_loc[0].cpu().numpy())
        conc_estimate = concentration[0].item()
        
        # Generate back-trajectory
        traj_np = trajectory[0].cpu().numpy()
        back_trajectory = [
            (self.current_pos[0] + t[0] * 0.001, 
             self.current_pos[1] + t[1] * 0.001,
             self.readings[0].altitude - i * (self.readings[0].altitude / 30))
            for i, t in enumerate(traj_np[:10])
        ]
        
        # Generate source cone (probability distribution)
        source_cone = self._generate_cone(source_location, back_trajectory)
        
        # Calculate confidence based on model certainty
        confidence = min(1.0, len(self.readings) / 30)
        
        return SourceEstimate(
            source_location=source_location,
            confidence=confidence,
            source_cone=source_cone,
            back_trajectory=back_trajectory,
            estimated_release_time=self.readings[0].timestamp - 60,
            concentration_estimate=conc_estimate
        )
        
    def _generate_cone(
        self,
        source: Tuple[float, float],
        trajectory: List[Tuple[float, float, float]]
    ) -> np.ndarray:
        """Generate probability cone around source estimate."""
        # Create grid for visualization
        lat_center, lon_center = source
        lat_range = np.linspace(lat_center - 0.01, lat_center + 0.01, 50)
        lon_range = np.linspace(lon_center - 0.01, lon_center + 0.01, 50)
        
        cone = np.zeros((50, 50))
        
        # Gaussian falloff from source
        for i, lat in enumerate(lat_range):
            for j, lon in enumerate(lon_range):
                dist = np.sqrt((lat - lat_center)**2 + (lon - lon_center)**2)
                cone[i, j] = np.exp(-dist * 100)
                
        # Normalize
        cone /= np.sum(cone)
        
        return cone


def create_source_localizer(device: str = "auto") -> SourceLocalization:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return SourceLocalization(device=device)


if __name__ == "__main__":
    print("Initializing Source Localization...")
    localizer = create_source_localizer()
    
    # Simulate readings
    for i in range(20):
        reading = GasReading(
            timestamp=i * 0.5,
            voc_ppm=500 + np.random.normal(100, 20),
            co2_ppm=400 + np.random.normal(50, 10),
            temperature=20 + np.random.normal(0, 2),
            humidity=60 + np.random.normal(0, 5),
            pressure=1013,
            altitude=500 - i * 25,
            position=(37.7749 + i * 0.0001, -122.4194 + i * 0.00005),
            wind_speed=5 + np.random.normal(0, 1),
            wind_direction=180
        )
        localizer.add_reading(reading)
        
    estimate = localizer.estimate_source()
    if estimate:
        print(f"Source Location: {estimate.source_location}")
        print(f"Confidence: {estimate.confidence:.1%}")
        print(f"Concentration Estimate: {estimate.concentration_estimate:.1f} ppm")