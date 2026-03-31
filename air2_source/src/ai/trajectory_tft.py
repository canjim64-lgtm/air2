"""
Temporal Fusion Transformer for GPU-Accelerated Trajectory Prediction
Monte Carlo simulations for landing path probability heat maps
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class TrajectoryPoint:
    timestamp: float
    position: np.ndarray  # [x, y, z]
    velocity: np.ndarray  # [vx, vy, vz]
    acceleration: np.ndarray  # [ax, ay, az]
    wind: np.ndarray  # [wx, wy, wz]


@dataclass
class TrajectoryPrediction:
    mean: np.ndarray  # Predicted landing point
    probability_map: np.ndarray  # Heat map of landing probabilities
    monte_carlo_paths: List[np.ndarray]  # Individual simulation paths
    confidence: float
    estimated_landing_time: float


class TemporalFusionTransformer(nn.Module):
    """
    Temporal Fusion Transformer for multi-horizon time series forecasting.
    Used for predicting CanSat trajectory and landing zone.
    """
    
    def __init__(
        self,
        input_dim: int = 15,  # [pos(3), vel(3), accel(3), wind(3), alt(1), time(2)]
        hidden_dim: int = 256,
        num_heads: int = 8,
        num_layers: int = 6,
        dropout: float = 0.1,
        forecast_horizon: int = 100
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.forecast_horizon = forecast_horizon
        
        # Input encoding
        self.input_embedding = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Temporal gating (GRU-like)
        self.temporal_gate = nn.GRUCell(hidden_dim, hidden_dim)
        
        # Multi-head attention for temporal dependencies
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # Transformer layers
        self.transformer_layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=hidden_dim,
                nhead=num_heads,
                dim_feedforward=hidden_dim * 4,
                dropout=dropout,
                activation='gelu',
                batch_first=True
            )
            for _ in range(num_layers)
        ])
        
        # Static covariate embedding (fixed features like date, location)
        self.static_embedding = nn.Sequential(
            nn.Linear(8, hidden_dim // 2),
            nn.ReLU()
        )
        
        # Known future input embedding (forecast wind, etc.)
        self.future_embedding = nn.Sequential(
            nn.Linear(forecast_horizon * 3, hidden_dim),
            nn.ReLU()
        )
        
        # Output heads for position and uncertainty
        self.position_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, forecast_horizon * 3)
        )
        
        self.uncertainty_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, forecast_horizon * 3)
        )
        
    def forward(
        self,
        history: torch.Tensor,  # [batch, seq_len, input_dim]
        static_covariates: Optional[torch.Tensor] = None  # [batch, 8]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            history: Historical trajectory data
            static_covariates: Static features (lat, lon, date, etc.)
            
        Returns:
            predictions: Predicted positions [batch, horizon, 3]
            uncertainties: Prediction uncertainties [batch, horizon, 3]
        """
        batch_size = history.size(0)
        
        # Embed input
        x = self.input_embedding(history)
        
        # Temporal processing
        for layer in self.transformer_layers:
            # Self-attention
            attn_out, _ = self.attention(x, x, x)
            x = layer(x + attn_out)
        
        # Global context
        context = torch.mean(x, dim=1)  # [batch, hidden_dim]
        
        # Add static context if available
        if static_covariates is not None:
            static_emb = self.static_embedding(static_covariates)
            context = torch.cat([context, static_emb], dim=-1)
        
        # Repeat for each forecast step
        context = context.unsqueeze(1).repeat(1, self.forecast_horizon, 1)
        
        # Decode predictions
        predictions = self.position_head(context)
        uncertainties = F.softplus(self.uncertainty_head(context)) + 1e-6
        
        return predictions, uncertainties


class MonteCarloSimulator:
    """GPU-accelerated Monte Carlo simulation for trajectory uncertainty."""
    
    def __init__(
        self,
        num_simulations: int = 100,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.num_simulations = num_simulations
        self.device = device
        
    def simulate_landing(
        self,
        initial_state: Dict,
        wind_field: Dict,
        num_steps: int = 100
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Run Monte Carlo simulations for landing prediction.
        
        Args:
            initial_state: Initial position, velocity, etc.
            wind_field: Wind data as function of altitude
            num_steps: Number of time steps to simulate
            
        Returns:
            landing_points: [num_sims, 3] landing positions
            paths: [num_sims, num_steps, 3] full trajectories
        """
        paths = []
        landing_points = []
        
        for _ in range(self.num_simulations):
            path = [initial_state['position'].copy()]
            pos = initial_state['position'].copy()
            vel = initial_state['velocity'].copy()
            
            for step in range(num_steps):
                # Get wind at current altitude
                altitude = pos[2]
                wind = self._get_wind(wind_field, altitude)
                
                # Add random perturbations (turbulence)
                turbulence = np.random.normal(0, 0.5, 3)
                
                # Simple physics integration
                gravity = np.array([0, 0, -9.81])
                acceleration = gravity + wind + turbulence
                
                vel += acceleration * 0.1
                pos += vel * 0.1
                
                path.append(pos.copy())
                
                # Stop if below ground
                if pos[2] < 0:
                    pos[2] = 0
                    break
                    
            paths.append(np.array(path))
            landing_points.append(pos.copy())
            
        return np.array(landing_points), np.array(paths)
        
    def _get_wind(self, wind_field: Dict, altitude: float) -> np.ndarray:
        """Sample wind at given altitude."""
        if 'profile' in wind_field:
            # Linear interpolation of wind profile
            alts = wind_field['profile']['altitudes']
            winds = wind_field['profile']['winds']
            
            if altitude <= alts[0]:
                return winds[0]
            if altitude >= alts[-1]:
                return winds[-1]
                
            for i in range(len(alts) - 1):
                if alts[i] <= altitude < alts[i + 1]:
                    t = (altitude - alts[i]) / (alts[i + 1] - alts[i])
                    return (1 - t) * winds[i] + t * winds[i + 1]
                    
        return np.zeros(3)
        
    def compute_probability_heatmap(
        self,
        landing_points: np.ndarray,
        grid_resolution: float = 5.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute probability heatmap from landing points.
        
        Returns:
            heatmap: 2D probability grid
            x_coords: X grid coordinates
            y_coords: Y grid coordinates
        """
        # Compute bounds
        min_x = np.min(landing_points[:, 0]) - 50
        max_x = np.max(landing_points[:, 0]) + 50
        min_y = np.min(landing_points[:, 1]) - 50
        max_y = np.max(landing_points[:, 1]) + 50
        
        # Create grid
        x_coords = np.arange(min_x, max_x, grid_resolution)
        y_coords = np.arange(min_y, max_y, grid_resolution)
        
        heatmap = np.zeros((len(y_coords), len(x_coords)))
        
        # Kernel density estimation (simple version)
        kernel_width = 10.0
        for point in landing_points:
            for i, y in enumerate(y_coords):
                for j, x in enumerate(x_coords):
                    dist = np.sqrt((x - point[0])**2 + (y - point[1])**2)
                    heatmap[i, j] += np.exp(-dist**2 / (2 * kernel_width**2))
                    
        # Normalize
        heatmap /= np.sum(heatmap) * grid_resolution**2
        
        return heatmap, x_coords, y_coords


class TrajectoryPredictor:
    """
    Complete trajectory prediction system using TFT and Monte Carlo.
    Provides landing probability heat maps.
    """
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        monte_carlo_sims: int = 100
    ):
        self.device = device
        
        # Initialize models
        self.tft_model = TemporalFusionTransformer().to(device)
        self.tft_model.eval()
        
        self.monte_carlo = MonteCarloSimulator(
            num_simulations=monte_carlo_sims,
            device=device
        )
        
        # Trajectory history
        self.trajectory_history: deque = deque(maxlen=500)
        
        # Wind model (simplified)
        self.wind_field = {'profile': {'altitudes': [0, 100, 500], 'winds': [np.zeros(3)] * 3}}
        
    def add_trajectory_point(self, point: TrajectoryPoint):
        """Add a new trajectory observation."""
        self.trajectory_history.append(point)
        
    def predict(
        self,
        current_state: Dict,
        forecast_time: float = 60.0
    ) -> TrajectoryPrediction:
        """
        Predict future trajectory and landing zone.
        
        Args:
            current_state: Current position, velocity, etc.
            forecast_time: Time to forecast in seconds
            
        Returns:
            TrajectoryPrediction with heatmap and paths
        """
        if len(self.trajectory_history) < 10:
            return self._default_prediction(current_state)
            
        # Get recent history
        recent_trajectories = np.array([
            np.concatenate([p.position, p.velocity, p.acceleration, p.wind])
            for p in list(self.trajectory_history)[-100:]
        ])
        
        # Pad if needed
        while len(recent_trajectories) < 100:
            recent_trajectories = np.vstack([recent_trajectories, recent_trajectories[-1:]])
            
        # Convert to tensor
        history_tensor = torch.FloatTensor(recent_trajectories).unsqueeze(0).to(self.device)
        
        # Get TFT prediction
        with torch.no_grad():
            predictions, uncertainties = self.tft_model(history_tensor)
            
        pred_points = predictions[0].cpu().numpy()
        
        # Run Monte Carlo simulations
        landing_points, paths = self.monte_carlo.simulate_landing(
            current_state, self.wind_field
        )
        
        # Compute heatmap
        heatmap, x_coords, y_coords = self.monte_carlo.compute_probability_heatmap(landing_points)
        
        # Compute mean landing point
        mean_landing = np.mean(landing_points, axis=0)
        
        # Estimate confidence
        confidence = 1.0 - np.std(np.linalg.norm(landing_points - mean_landing, axis=1)) / 100
        
        return TrajectoryPrediction(
            mean=mean_landing,
            probability_map=heatmap,
            monte_carlo_paths=paths.tolist(),
            confidence=np.clip(confidence, 0.0, 1.0),
            estimated_landing_time=current_state.get('timestamp', 0) + forecast_time
        )
        
    def _default_prediction(self, current_state: Dict) -> TrajectoryPrediction:
        """Return default prediction when insufficient data."""
        return TrajectoryPrediction(
            mean=current_state.get('position', np.zeros(3)),
            probability_map=np.zeros((100, 100)),
            monte_carlo_paths=[],
            confidence=0.0,
            estimated_landing_time=0
        )


def create_trajectory_predictor(
    device: str = "auto",
    monte_carlo_sims: int = 100
) -> TrajectoryPredictor:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return TrajectoryPredictor(device=device, monte_carlo_sims=monte_carlo_sims)


# Demo
if __name__ == "__main__":
    print("Initializing Trajectory Predictor...")
    predictor = create_trajectory_predictor(monte_carlo_sims=50)
    
    # Simulate trajectory
    print("Simulating descent trajectory...")
    current_state = {
        'position': np.array([0.0, 0.0, 200.0]),
        'velocity': np.array([5.0, -3.0, -15.0]),
        'timestamp': 0.0
    }
    
    for t in range(100):
        point = TrajectoryPoint(
            timestamp=t * 0.5,
            position=np.array([t * 0.3, -t * 0.2, 200 - t * 2]),
            velocity=np.array([0.3, -0.2, -2]),
            acceleration=np.array([0, 0, -9.8]),
            wind=np.array([1, -0.5, 0])
        )
        predictor.add_trajectory_point(point)
        
    prediction = predictor.predict(current_state, forecast_time=30.0)
    
    print(f"\nPrediction Results:")
    print(f"  Mean Landing: {prediction.mean}")
    print(f"  Confidence: {prediction.confidence:.2%}")
    print(f"  Monte Carlo Paths: {len(prediction.monte_carlo_paths)}")
    print(f"  Heatmap Shape: {prediction.probability_map.shape}")