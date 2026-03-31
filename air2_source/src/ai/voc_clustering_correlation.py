"""
VOC Fingerprint Clustering & Thermal-Chemical Correlation
t-SNE/UMAP dimensionality reduction for chemical map visualization
Real-time Pearson correlation heatmap for cause identification
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import torch
import torch.nn as nn
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ClusterResult:
    timestamp: float
    cluster_id: int
    cluster_name: str
    proximity_scores: Dict[str, float]
    dominant_gas: str


class ChemicalClusterMapper:
    """
    VOC fingerprint clustering using t-SNE/UMAP.
    Maps sensor readings to chemical clusters in real-time.
    """
    
    CLUSTER_NAMES = {
        0: 'Clean Air',
        1: 'Vehicle Exhaust',
        2: 'Industrial Solvent',
        3: 'Wildfire Smoke',
        4: 'Cooking Vapors',
        5: 'Background'
    }
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        history_size: int = 500
    ):
        self.device = device
        self.history_size = history_size
        
        # Data history
        self.feature_history: deque = deque(maxlen=history_size)
        self.timestamp_history: deque = deque(maxlen=history_size)
        
        # Cluster centers (initialized with default profiles)
        self.cluster_profiles = self._initialize_profiles()
        
        # Dimensionality reduction
        self.scaler = StandardScaler()
        self.tsne = None
        
        # GPU-accelerated embedding
        self.embedding_model = self._create_embedding_model().to(device)
        
    def _initialize_profiles(self) -> np.ndarray:
        """Initialize known chemical fingerprint profiles."""
        # VOC sensor resistance patterns for different chemicals
        return np.array([
            [0.1, 0.1, 0.1, 0.1],   # Clean Air
            [0.8, 0.6, 0.3, 0.7],   # Vehicle Exhaust (CO, HC, NO2, CO2)
            [0.9, 0.3, 0.8, 0.2],   # Industrial Solvent
            [0.7, 0.9, 0.5, 0.4],   # Wildfire Smoke
            [0.2, 0.7, 0.1, 0.8],   # Cooking Vapors
            [0.3, 0.2, 0.2, 0.2]    # Background
        ])
        
    def _create_embedding_model(self) -> nn.Module:
        """Create neural network for feature embedding."""
        class EmbeddingNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(8, 64),
                    nn.ReLU(),
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Linear(32, 16)
                )
            def forward(self, x):
                return self.net(x)
        return EmbeddingNet()
        
    def add_reading(
        self,
        timestamp: float,
        voc_total: float,
        co2: float,
        temperature: float,
        humidity: float,
        pressure: float,
        altitude: float,
        no2: float = 0,
        so2: float = 0
    ):
        """Add a new sensor reading."""
        # Create feature vector
        features = np.array([
            voc_total / 1000,
            co2 / 5000,
            temperature / 50,
            humidity / 100,
            pressure / 1013,
            altitude / 1000,
            no2 / 100,
            so2 / 50
        ])
        
        self.feature_history.append(features)
        self.timestamp_history.append(timestamp)
        
    def compute_clusters(self) -> List[ClusterResult]:
        """
        Compute t-SNE embedding and cluster assignments.
        
        Returns:
            List of cluster assignments for recent readings
        """
        if len(self.feature_history) < 20:
            return []
            
        # Convert to numpy
        features = np.array(list(self.feature_history))
        
        # Normalize
        features_scaled = self.scaler.fit_transform(features)
        
        # GPU-accelerated t-SNE
        features_tensor = torch.FloatTensor(features_scaled).to(self.device)
        with torch.no_grad():
            embedded = self.embedding_model(features_tensor).cpu().numpy()
            
        # Compute t-SNE for visualization
        if len(features) > 30:
            tsne = TSNE(n_components=2, perplexity=min(30, len(features) // 2), random_state=42)
            tsne_result = tsne.fit_transform(embedded)
        else:
            tsne_result = embedded[:, :2]
            
        # Assign clusters based on distance to known profiles
        results = []
        for i, (feature, tsne_point) in enumerate(zip(features, tsne_result)):
            cluster_id, proximity_scores = self._assign_cluster(feature)
            cluster_name = self.CLUSTER_NAMES.get(cluster_id, 'Unknown')
            
            results.append(ClusterResult(
                timestamp=self.timestamp_history[i],
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                proximity_scores=proximity_scores,
                dominant_gas=self._identify_dominant_gas(proximity_scores)
            ))
            
        return results
        
    def _assign_cluster(self, features: np.ndarray) -> Tuple[int, Dict[str, float]]:
        """Assign reading to nearest cluster based on profile."""
        # Normalize features for comparison
        feature_normalized = features[:4] / (features[:4].max() + 1e-6)
        
        proximities = {}
        for cluster_id, profile in enumerate(self.cluster_profiles):
            # Cosine similarity
            similarity = np.dot(feature_normalized, profile) / (
                np.linalg.norm(feature_normalized) * np.linalg.norm(profile) + 1e-6
            )
            proximities[self.CLUSTER_NAMES[cluster_id]] = float(similarity)
            
        # Find closest cluster
        cluster_id = max(proximities, key=proximities.get)
        return cluster_id, proximities
        
    def _identify_dominant_gas(self, proximity_scores: Dict[str, float]) -> str:
        """Identify the dominant gas based on proximity scores."""
        if not proximity_scores:
            return "Unknown"
            
        max_score = max(proximity_scores.values())
        
        gas_mapping = {
            'Clean Air': 'None (Clean)',
            'Vehicle Exhaust': 'CO, HC',
            'Industrial Solvent': 'VOC (Organic)',
            'Wildfire Smoke': 'Particulates, CO',
            'Cooking Vapors': 'Hydrocarbons',
            'Background': 'Trace Elements'
        }
        
        for cluster_name, score in proximity_scores.items():
            if score == max_score:
                return gas_mapping.get(cluster_name, 'Unknown')
                
        return "Mixed Sources"


class ThermalChemicalCorrelation:
    """
    Real-time thermal-chemical correlation analysis.
    Identifies if VOC spikes are thermally driven or independent.
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        
        self.voc_history = deque(maxlen=window_size)
        self.temp_history = deque(maxlen=window_size)
        self.humidity_history = deque(maxlen=window_size)
        self.pressure_history = deque(maxlen=window_size)
        self.timestamp_history = deque(maxlen=window_size)
        
    def add_reading(self, timestamp: float, voc: float, temp: float, humidity: float, pressure: float):
        """Add sensor reading."""
        self.voc_history.append(voc)
        self.temp_history.append(temp)
        self.humidity_history.append(humidity)
        self.pressure_history.append(pressure)
        self.timestamp_history.append(timestamp)
        
    def compute_correlation(self) -> Dict:
        """
        Compute Pearson correlation between VOC and environmental factors.
        
        Returns:
            Dict with correlation coefficients and interpretation
        """
        if len(self.voc_history) < 20:
            return {'status': 'Insufficient data'}
            
        voc = np.array(self.voc_history)
        temp = np.array(self.temp_history)
        humidity = np.array(self.humidity_history)
        pressure = np.array(self.pressure_history)
        
        # Compute correlations
        voc_temp_corr = self._pearson_correlation(voc, temp)
        voc_hum_corr = self._pearson_correlation(voc, humidity)
        voc_pres_corr = self._pearson_correlation(voc, pressure)
        
        # Correlation heatmap matrix
        correlation_matrix = np.array([
            [1.0, voc_temp_corr, voc_hum_corr, voc_pres_corr],
            [voc_temp_corr, 1.0, self._pearson_correlation(temp, humidity), self._pearson_correlation(temp, pressure)],
            [voc_hum_corr, self._pearson_correlation(humidity, temp), 1.0, self._pearson_correlation(humidity, pressure)],
            [voc_pres_corr, self._pearson_correlation(pressure, temp), self._pearson_correlation(pressure, humidity), 1.0]
        ])
        
        # Interpretation
        if abs(voc_temp_corr) > 0.7:
            thermal_driver = 'Strong'
        elif abs(voc_temp_corr) > 0.4:
            thermal_driver = 'Moderate'
        else:
            thermal_driver = 'Weak'
            
        cause = 'Point-source leak detected' if abs(voc_temp_corr) < 0.3 else 'Temperature-dependent emission'
        
        return {
            'correlation_matrix': correlation_matrix.tolist(),
            'factors': ['VOC', 'Temperature', 'Humidity', 'Pressure'],
            'voc_temp_correlation': float(voc_temp_corr),
            'voc_humidity_correlation': float(voc_hum_corr),
            'voc_pressure_correlation': float(voc_pres_corr),
            'thermal_driver': thermal_driver,
            'cause_interpretation': cause
        }
        
    def _pearson_correlation(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
            
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sqrt(np.sum((x - x_mean)**2) * np.sum((y - y_mean)**2))
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator
        
    def generate_correlation_plot_data(self) -> Dict:
        """Generate data for GUI correlation heatmap."""
        result = self.compute_correlation()
        
        if 'status' in result:
            return result
            
        # Create heatmap data
        matrix = np.array(result['correlation_matrix'])
        
        # Convert to color values (red = negative, white = 0, blue = positive)
        colors = []
        for row in matrix:
            row_colors = []
            for val in row:
                if val > 0:
                    row_colors.append([1.0, 1.0 - val, 1.0 - val])  # Blue tint
                else:
                    row_colors.append([1.0 + val, 1.0, 1.0 + val])  # Red tint
            colors.append(row_colors)
            
        return {
            'matrix': matrix.tolist(),
            'colors': colors,
            'labels': result['factors'],
            'interpretation': result['cause_interpretation']
        }


class VOCAnalysisEngine:
    """
    Complete VOC analysis engine combining clustering and correlation.
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.cluster_mapper = ChemicalClusterMapper(device)
        self.correlation_analyzer = ThermalChemicalCorrelation()
        
    def add_reading(
        self,
        timestamp: float,
        voc_total: float,
        co2: float,
        temperature: float,
        humidity: float,
        pressure: float,
        altitude: float,
        no2: float = 0,
        so2: float = 0
    ):
        """Add sensor reading to both analyzers."""
        self.cluster_mapper.add_reading(
            timestamp, voc_total, co2, temperature, humidity, pressure, altitude, no2, so2
        )
        self.correlation_analyzer.add_reading(timestamp, voc_total, temperature, humidity, pressure)
        
    def get_analysis(self) -> Dict:
        """Get comprehensive VOC analysis."""
        clusters = self.cluster_mapper.compute_clusters()
        correlation = self.correlation_analyzer.generate_correlation_plot_data()
        
        latest_cluster = clusters[-1] if clusters else None
        
        return {
            'latest_cluster': {
                'name': latest_cluster.cluster_name if latest_cluster else 'Unknown',
                'dominant_gas': latest_cluster.dominant_gas if latest_cluster else 'Unknown',
                'proximity_scores': latest_cluster.proximity_scores if latest_cluster else {}
            },
            'correlation': correlation,
            'chemical_map_points': self._get_chemical_map_points(clusters),
            'total_readings': len(self.cluster_mapper.feature_history)
        }
        
    def _get_chemical_map_points(self, clusters: List[ClusterResult]) -> List[Dict]:
        """Get points for chemical map visualization."""
        return [
            {
                'timestamp': c.timestamp,
                'cluster': c.cluster_id,
                'name': c.cluster_name,
                'dominant_gas': c.dominant_gas
            }
            for c in clusters[-50:]  # Last 50 points
        ]


def create_voc_analysis_engine(device: str = "auto") -> VOCAnalysisEngine:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return VOCAnalysisEngine(device=device)


if __name__ == "__main__":
    print("Initializing VOC Analysis Engine...")
    engine = create_voc_analysis_engine()
    
    # Simulate readings from different scenarios
    print("Simulating sensor readings...")
    
    # Clean air phase
    for i in range(30):
        engine.add_reading(
            timestamp=i * 0.2,
            voc_total=100 + np.random.normal(20, 10),
            co2=400,
            temperature=20 + i * 0.1,
            humidity=50,
            pressure=1013,
            altitude=500 - i * 10
        )
        
    # Vehicle exhaust phase
    for i in range(30, 60):
        engine.add_reading(
            timestamp=i * 0.2,
            voc_total=600 + np.random.normal(100, 30),
            co2=1200 + np.random.normal(100, 20),
            temperature=22 + (i - 30) * 0.1,
            humidity=55,
            pressure=1013,
            altitude=300 - (i - 30) * 10
        )
        
    # Wildfire smoke phase
    for i in range(60, 100):
        engine.add_reading(
            timestamp=i * 0.2,
            voc_total=800 + np.random.normal(150, 50),
            co2=900,
            temperature=28 + np.random.normal(0, 2),
            humidity=35,
            pressure=1010,
            altitude=100 - (i - 60) * 10
        )
        
    # Get analysis
    analysis = engine.get_analysis()
    
    print(f"\nLatest Cluster: {analysis['latest_cluster']['name']}")
    print(f"Dominant Gas: {analysis['latest_cluster']['dominant_gas']}")
    print(f"VOC-Temperature Correlation: {analysis['correlation'].get('voc_temp_correlation', 'N/A'):.3f}")
    print(f"Cause: {analysis['correlation'].get('cause_interpretation', 'N/A')}")