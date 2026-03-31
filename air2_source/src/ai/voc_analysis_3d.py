"""
VOC Sensor Fusion De-noising & 3D Volumetric Voxel Mapping
MLP for cleaning VOC data based on temperature and humidity
GPU-accelerated 3D voxel map rendering for atmospheric layers
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import torch
import torch.nn as nn
from collections import deque


@dataclass
class VOCReading:
    timestamp: float
    voc_raw: float
    temperature: float
    humidity: float
    pressure: float
    altitude: float
    position: Tuple[float, float]
    voc_purified: float = 0.0


@dataclass
class VoxelCell:
    x: int
    y: int
    z: int
    voc_level: float
    color: Tuple[int, int, int]


class VOCDeNoisingMLP(nn.Module):
    """
    Multi-Layer Perceptron for VOC sensor de-noising.
    Takes (VOC + Temp + Humidity) and outputs purified VOC index.
    """
    
    def __init__(
        self,
        input_dim: int = 3,
        hidden_dims: List[int] = [64, 128, 64],
        output_dim: int = 1
    ):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            prev_dim = hidden_dim
            
        layers.append(nn.Linear(prev_dim, output_dim))
        
        self.model = nn.Sequential(*layers)
        
    def forward(self, voc: torch.Tensor, temp: torch.Tensor, humidity: torch.Tensor) -> torch.Tensor:
        """
        Args:
            voc: Raw VOC reading [batch, 1]
            temp: Temperature [batch, 1]
            humidity: Humidity [batch, 1]
            
        Returns:
            Purified VOC index [batch, 1]
        """
        x = torch.cat([voc, temp, humidity], dim=-1)
        return self.model(x)


class VOCALPurifier:
    """
    VOC purification using neural network.
    Removes noise caused by weather changes during descent.
    """
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.model = VOCDeNoisingMLP().to(device)
        self.model.eval()
        
        # Training state
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.loss_fn = nn.MSELoss()
        
        # Calibration data
        self.calibration_pairs: List[Tuple[np.ndarray, float]] = []
        
    def purify(
        self,
        voc_raw: float,
        temperature: float,
        humidity: float
    ) -> float:
        """
        Purify VOC reading.
        
        Args:
            voc_raw: Raw VOC value
            temperature: Temperature in Celsius
            humidity: Humidity percentage
            
        Returns:
            Purified VOC index
        """
        voc_t = torch.FloatTensor([[voc_raw / 1000]]).to(self.device)
        temp_t = torch.FloatTensor([[temperature / 50]]).to(self.device)
        hum_t = torch.FloatTensor([[humidity / 100]]).to(self.device)
        
        with torch.no_grad():
            purified = self.model(voc_t, temp_t, hum_t)[0, 0].item()
            
        return purified * 1000
        
    def add_calibration_pair(self, raw: float, true_clean: float, temp: float, humidity: float):
        """Add calibration data pair."""
        self.calibration_pairs.append((np.array([raw, temp, humidity]), true_clean))
        
    def train(self, epochs: int = 50):
        """Train the de-noising model."""
        if len(self.calibration_pairs) < 10:
            print("Warning: Insufficient calibration data")
            return
            
        inputs = np.array([p[0] for p in self.calibration_pairs])
        targets = np.array([p[1] for p in self.calibration_pairs]) / 1000
        
        dataset = torch.FloatTensor(inputs)
        targetset = torch.FloatTensor(targets).unsqueeze(1)
        
        for epoch in range(epochs):
            self.model.train()
            
            # Shuffle
            idx = torch.randperm(len(dataset))
            inputs_batch = dataset[idx]
            targets_batch = targetset[idx]
            
            # Train
            voc = inputs_batch[:, 0:1].to(self.device)
            temp = inputs_batch[:, 1:2].to(self.device)
            hum = inputs_batch[:, 2:3].to(self.device)
            targets_p = targets_batch.to(self.device)
            
            self.optimizer.zero_grad()
            outputs = self.model(voc, temp, hum)
            loss = self.loss_fn(outputs, targets_p)
            loss.backward()
            self.optimizer.step()
            
        self.model.eval()


class Voxel3DMapper:
    """
    3D Volumetric Voxel Mapper for atmospheric visualization.
    Renders voxel grid colored by VOC concentration.
    """
    
    def __init__(
        self,
        grid_size: Tuple[int, int, int] = (20, 20, 50),
        resolution: float = 10.0  # meters per voxel
    ):
        self.grid_size = grid_size
        self.resolution = resolution
        
        # Voxel storage
        self.voxels: Dict[Tuple[int, int, int], VoxelCell] = {}
        
        # Origin point (starting position)
        self.origin = None
        
        # Reading history
        self.readings: List[VOCReading] = []
        
        # Color scale for VOC levels
        self.voc_color_scale = self._create_color_scale()
        
    def _create_color_scale(self) -> Dict[float, Tuple[int, int, int]]:
        """Create color scale for VOC levels (green=good, red=dangerous)."""
        return {
            0.0: (0, 255, 0),      # Green - clean
            0.3: (255, 255, 0),   # Yellow - moderate
            0.6: (255, 128, 0),   # Orange - high
            1.0: (255, 0, 0)      # Red - dangerous
        }
        
    def _interpolate_color(self, voc_level: float) -> Tuple[int, int, int]:
        """Interpolate color based on VOC level."""
        levels = sorted(self.voc_color_scale.keys())
        
        if voc_level <= levels[0]:
            return self.voc_color_scale[levels[0]]
        if voc_level >= levels[-1]:
            return self.voc_color_scale[levels[-1]]
            
        for i in range(len(levels) - 1):
            if levels[i] <= voc_level < levels[i + 1]:
                t = (voc_level - levels[i]) / (levels[i + 1] - levels[i])
                c1 = self.voc_color_scale[levels[i]]
                c2 = self.voc_color_scale[levels[i + 1]]
                return (
                    int(c1[0] + (c2[0] - c1[0]) * t),
                    int(c1[1] + (c2[1] - c1[1]) * t),
                    int(c1[2] + (c2[2] - c1[2]) * t)
                )
                
        return (128, 128, 128)
        
    def add_reading(self, reading: VOCReading):
        """Add a VOC reading to the voxel map."""
        if self.origin is None:
            self.origin = reading.position
            
        self.readings.append(reading)
        
        # Calculate voxel indices
        dx = (reading.position[0] - self.origin[0]) * 111320  # rough meters
        dy = (reading.position[1] - self.origin[1]) * 111320
        dz = reading.altitude
        
        vx = int(dx / self.resolution)
        vy = int(dy / self.resolution)
        vz = int(dz / self.resolution)
        
        # Clamp to grid
        vx = max(0, min(self.grid_size[0] - 1, vx + self.grid_size[0] // 2))
        vy = max(0, min(self.grid_size[1] - 1, vy + self.grid_size[1] // 2))
        vz = max(0, min(self.grid_size[2] - 1, vz))
        
        # Create or update voxel
        key = (vx, vy, vz)
        if key in self.voxels:
            # Average with existing
            existing = self.voxels[key]
            avg_voc = (existing.voc_level + reading.voc_purified) / 2
            self.voxels[key] = VoxelCell(
                x=vx, y=vy, z=vz,
                voc_level=avg_voc,
                color=self._interpolate_color(avg_voc)
            )
        else:
            self.voxels[key] = VoxelCell(
                x=vx, y=vy, z=vz,
                voc_level=reading.voc_purified,
                color=self._interpolate_color(reading.voc_purified)
            )
            
    def get_voxel_grid(self) -> np.ndarray:
        """
        Get the 3D voxel grid as numpy array.
        
        Returns:
            3D array with VOC levels [z, y, x]
        """
        grid = np.zeros(self.grid_size)
        
        for (vx, vy, vz), voxel in self.voxels.items():
            grid[vz, vy, vx] = voxel.voc_level
            
        return grid
        
    def get_cross_section(self, axis: str = 'z', level: int = None) -> np.ndarray:
        """
        Get a 2D cross-section of the voxel map.
        
        Args:
            axis: 'x', 'y', or 'z'
            level: Slice level (default: middle)
            
        Returns:
            2D array of VOC levels
        """
        grid = self.get_voxel_grid()
        
        if axis == 'z':
            if level is None:
                level = grid.shape[0] // 2
            return grid[level, :, :]
        elif axis == 'y':
            if level is None:
                level = grid.shape[1] // 2
            return grid[:, level, :]
        else:
            if level is None:
                level = grid.shape[2] // 2
            return grid[:, :, level]
            
    def generate_visualization_data(self) -> Dict:
        """
        Generate data for 3D visualization (Three.js compatible).
        
        Returns:
            Dictionary with vertices, colors, and indices
        """
        vertices = []
        colors = []
        indices = []
        
        voxel_size = self.resolution
        idx = 0
        
        for (vx, vy, vz), voxel in self.voxels.items():
            # 8 corners of the cube
            x, y, z = vx * voxel_size, vy * voxel_size, vz * voxel_size
            
            corners = [
                [x, y, z],
                [x + voxel_size, y, z],
                [x + voxel_size, y + voxel_size, z],
                [x, y + voxel_size, z],
                [x, y, z + voxel_size],
                [x + voxel_size, y, z + voxel_size],
                [x + voxel_size, y + voxel_size, z + voxel_size],
                [x, y + voxel_size, z + voxel_size]
            ]
            
            # Add vertices
            for corner in corners:
                vertices.extend(corner)
                
            # Add colors (RGB for each vertex)
            color = voxel.color
            for _ in corners:
                colors.extend([color[0] / 255, color[1] / 255, color[2] / 255])
                
            # Add indices for a cube (two triangles per face, 6 faces)
            faces = [
                [0, 1, 2, 0, 2, 3],  # bottom
                [4, 6, 5, 4, 7, 6],  # top
                [0, 4, 5, 0, 5, 1],  # front
                [2, 6, 7, 2, 7, 3],  # back
                [0, 3, 7, 0, 7, 4],  # left
                [1, 5, 6, 1, 6, 2]   # right
            ]
            
            base = idx * 8
            for face in faces:
                for i in face:
                    indices.append(base + i)
                    
            idx += 1
            
        return {
            'vertices': np.array(vertices).tolist(),
            'colors': np.array(colors).tolist(),
            'indices': indices
        }


class VOCAnalysisSystem:
    """
    Complete VOC analysis system combining de-noising and 3D mapping.
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.purifier = VOCALPurifier(device)
        self.voxel_mapper = Voxel3DMapper()
        
        self.readings: List[VOCReading] = []
        
    def add_reading(
        self,
        timestamp: float,
        voc_raw: float,
        temperature: float,
        humidity: float,
        pressure: float,
        altitude: float,
        position: Tuple[float, float]
    ):
        """Add a new VOC reading."""
        # Purify the VOC value
        voc_purified = self.purifier.purify(voc_raw, temperature, humidity)
        
        reading = VOCReading(
            timestamp=timestamp,
            voc_raw=voc_raw,
            voc_purified=voc_purified,
            temperature=temperature,
            humidity=humidity,
            pressure=pressure,
            altitude=altitude,
            position=position
        )
        
        self.readings.append(reading)
        self.voxel_mapper.add_reading(reading)
        
    def get_current_voc_index(self) -> float:
        """Get the current purified VOC index."""
        if self.readings:
            return self.readings[-1].voc_purified
        return 0.0
        
    def get_voxel_grid(self) -> np.ndarray:
        """Get the 3D VOC voxel grid."""
        return self.voxel_mapper.get_voxel_grid()
        
    def get_visualization_data(self) -> Dict:
        """Get data for 3D visualization."""
        return self.voxel_mapper.generate_visualization_data()


def create_voc_analysis_system(device: str = "auto") -> VOCAnalysisSystem:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return VOCAnalysisSystem(device=device)


if __name__ == "__main__":
    print("Initializing VOC Analysis System...")
    voc_system = create_voc_analysis_system()
    
    # Simulate readings
    for i in range(100):
        voc_system.add_reading(
            timestamp=i * 0.2,
            voc_raw=200 + np.random.normal(50, 20),
            temperature=20 + i * 0.1,
            humidity=60 + np.sin(i * 0.1) * 10,
            pressure=1013,
            altitude=500 - i * 5,
            position=(37.7749, -122.4194)
        )
        
    print(f"Processed {len(voc_system.readings)} readings")
    print(f"Current VOC Index: {voc_system.get_current_voc_index():.1f}")
    
    # Get visualization data
    viz_data = voc_system.get_visualization_data()
    print(f"Voxel count: {len(viz_data['vertices']) // 24}")
    print(f"3D visualization data generated")