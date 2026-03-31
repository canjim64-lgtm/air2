"""
Atmospheric Inversion Layer Detection & Radiation Source Locator
Change-Point Detection (CPD) for temperature/VOC inversion layers
Bayesian Inference for radiation source localization
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
from scipy import stats


@dataclass
class InversionLayer:
    altitude_start: float
    altitude_end: float
    temperature_gradient: float  # °C per meter
    voc_trap_level: float  # How much VOCs are trapped
    confidence: float
    description: str


@dataclass
class RadiationSource:
    position: Tuple[float, float]
    confidence: float
    estimated_activity: float  # Bq
    source_type: str  # 'natural', 'technogenic', 'unknown'


class InversionLayerDetector:
    """
    Change-Point Detection for atmospheric inversion layers.
    Identifies altitudes where pollutants are trapped.
    """
    
    def __init__(
        self,
        window_size: int = 50,
        threshold_std: float = 2.0
    ):
        self.window_size = window_size
        self.threshold_std = threshold_std
        
        self.altitude_history = deque(maxlen=500)
        self.temperature_history = deque(maxlen=500)
        self.voc_history = deque(maxlen=500)
        self.pressure_history = deque(maxlen=500)
        
        self.detected_inversions: List[InversionLayer] = []
        
    def add_reading(
        self,
        altitude: float,
        temperature: float,
        voc: float,
        pressure: float
    ):
        """Add atmospheric reading."""
        self.altitude_history.append(altitude)
        self.temperature_history.append(temperature)
        self.voc_history.append(voc)
        self.pressure_history.append(pressure)
        
    def detect_inversions(self) -> List[InversionLayer]:
        """
        Detect inversion layers using change-point detection.
        
        Returns:
            List of detected inversion layers
        """
        if len(self.altitude_history) < self.window_size:
            return []
            
        # Convert to arrays
        altitudes = np.array(list(self.altitude_history))
        temperatures = np.array(list(self.temperature_history))
        vocs = np.array(list(self.voc_history))
        
        # Sort by altitude (descending - from high to low)
        sort_idx = np.argsort(-altitudes)
        altitudes_sorted = altitudes[sort_idx]
        temperatures_sorted = temperatures[sort_idx]
        vocs_sorted = vocs[sort_idx]
        
        # Remove duplicates at same altitude (average)
        unique_altitudes, unique_idx = np.unique(altitudes_sorted, return_index=True)
        temps_avg = np.array([np.mean(temperatures_sorted[altitudes_sorted == a]) for a in unique_altitudes])
        vocs_avg = np.array([np.mean(vocs_sorted[altitudes_sorted == a]) for a in unique_altitudes])
        
        # Detect temperature inversions (temperature increases with altitude)
        inversions = []
        
        for i in range(len(unique_altitudes) - 1):
            alt_diff = unique_altitudes[i] - unique_altitudes[i + 1]
            temp_diff = temps_avg[i] - temps_avg[i + 1]
            
            # Inversion: temperature INCREASES with altitude (normal is decrease)
            if temp_diff < -0.5:  # Temperature rises by more than 0.5°C over altitude decrease
                gradient = temp_diff / alt_diff  # °C per meter (should be negative for normal lapse)
                
                # Check if this is a significant inversion
                # Normal lapse rate is about -6.5°C/km, so positive values indicate inversion
                inversion_strength = -gradient  # Convert to positive for clarity
                
                if inversion_strength > 1.0:  # Significant inversion
                    # Check VOC trapping at this layer
                    voc_trap = self._estimate_voc_trapping(
                        unique_altitudes[i:i+2],
                        vocs_avg[i:i+2]
                    )
                    
                    inversions.append(InversionLayer(
                        altitude_start=unique_altitudes[i + 1],
                        altitude_end=unique_altitudes[i],
                        temperature_gradient=inversion_strength,
                        voc_trap_level=voc_trap,
                        confidence=min(1.0, inversion_strength / 5),
                        description=self._describe_inversion(inversion_strength, voc_trap)
                    ))
                    
        self.detected_inversions = inversions
        return inversions
        
    def _estimate_voc_trapping(
        self,
        altitudes: np.ndarray,
        vocs: np.ndarray
    ) -> float:
        """Estimate how much VOCs are trapped at this inversion."""
        if len(altitudes) < 2:
            return 0.0
            
        # VOC accumulation factor
        alt_range = altitudes[0] - altitudes[-1]
        voc_diff = np.max(vocs) - np.min(vocs)
        
        # Higher VOCs in narrower layer = more trapping
        if alt_range > 0:
            trap_factor = (voc_diff / alt_range) * 100
            return min(1.0, trap_factor / 50)  # Normalize
        return 0.0
        
    def _describe_inversion(self, gradient: float, voc_trap: float) -> str:
        """Generate description of inversion layer."""
        if gradient > 5:
            strength = "Strong"
        elif gradient > 2:
            strength = "Moderate"
        else:
            strength = "Weak"
            
        if voc_trap > 0.7:
            trapping = "significant VOC trapping"
        elif voc_trap > 0.4:
            trapping = "moderate VOC accumulation"
        else:
            trapping = "minimal VOC effect"
            
        return f"{strength} inversion with {trapping}"
        
    def get_meteorological_report(self) -> Dict:
        """Generate meteorological report of inversion layers."""
        inversions = self.detect_inversions()
        
        if not inversions:
            return {
                'status': 'No inversion layers detected',
                'inversions': []
            }
            
        total_inversions = len(inversions)
        strongest = max(inversions, key=lambda x: x.temperature_gradient)
        
        return {
            'status': f'{total_inversions} inversion layer(s) detected',
            'inversions': [
                {
                    'altitude_range': f"{inv.altitude_end:.0f}m to {inv.altitude_start:.0f}m",
                    'gradient': f"{inv.temperature_gradient:.2f}°C/100m",
                    'voc_trap': f"{inv.voc_trap_level:.1%}",
                    'confidence': f"{inv.confidence:.0%}",
                    'description': inv.description
                }
                for inv in inversions
            ],
            'strongest_inversion': {
                'altitude': f"{(strongest.altitude_start + strongest.altitude_end) / 2:.0f}m",
                'gradient': f"{strongest.temperature_gradient:.2f}°C/100m"
            },
            'meteorological_significance': self._get_met_significance(inversions)
        }
        
    def _get_met_significance(self, inversions: List[InversionLayer]) -> str:
        """Get meteorological significance statement."""
        if not inversions:
            return "Stable atmospheric conditions."
            
        avg_gradient = np.mean([inv.temperature_gradient for inv in inversions])
        
        if avg_gradient > 4:
            return "Significant temperature inversion. Air quality may be affected. Pollutants trapped at detected layers."
        elif avg_gradient > 2:
            return "Moderate temperature inversion. Some atmospheric stability detected."
        else:
            return "Weak inversion layer. Minimal impact on air quality."


class RadiationSourceLocator:
    """
    Bayesian inference for radiation source localization.
    Uses inverse square law to locate ground-based sources.
    """
    
    def __init__(self):
        self.readings: List[Dict] = []
        
    def add_reading(self, position: Tuple[float, float], altitude: float, radiation: float, timestamp: float):
        """Add radiation measurement."""
        self.readings.append({
            'position': position,
            'altitude': altitude,
            'radiation': radiation,
            'timestamp': timestamp
        })
        
    def estimate_source(self) -> Optional[RadiationSource]:
        """
        Estimate radiation source location using inverse square model.
        
        Returns:
            RadiationSource with estimated position
        """
        if len(self.readings) < 5:
            return None
            
        # Convert readings to arrays
        positions = np.array([r['position'] for r in self.readings])
        altitudes = np.array([r['altitude'] for r in self.readings])
        radiations = np.array([r['radiation'] for r in self.readings])
        
        # Normalize radiation (account for natural background)
        background = np.percentile(radiations, 25)  # Assume lowest readings are background
        excess = radiations - background
        
        # Find spike pattern
        spike_indices = np.where(excess > np.std(excess) * 2)[0]
        
        if len(spike_indices) < 3:
            return None
            
        # Get positions and altitudes at spikes
        spike_positions = positions[spike_indices]
        spike_altitudes = altitudes[spike_indices]
        spike_radiations = excess[spike_indices]
        
        # Use inverse square model: I = A / (d² + h²)
        # where d is horizontal distance, h is altitude
        # We need to find source position that minimizes error
        
        # Grid search for source position
        center_lon = np.mean(positions[:, 1])
        center_lat = np.mean(positions[:, 0])
        
        best_error = float('inf')
        best_pos = (center_lat, center_lon)
        best_activity = 0
        
        for lat_offset in np.linspace(-0.005, 0.005, 20):
            for lon_offset in np.linspace(-0.005, 0.005, 20):
                source_lat = center_lat + lat_offset
                source_lon = center_lon + lon_offset
                
                error = 0
                for i, (pos, alt, rad) in enumerate(zip(positions, altitudes, excess)):
                    # Calculate distance from source
                    d_lat = (pos[0] - source_lat) * 111320  # meters
                    d_lon = (pos[1] - source_lon) * 111320 * np.cos(np.radians(pos[0]))
                    horizontal_dist = np.sqrt(d_lat**2 + d_lon**2)
                    
                    # Vertical distance is altitude
                    total_dist = np.sqrt(horizontal_dist**2 + alt**2)
                    
                    if total_dist > 0:
                        predicted = 1 / (total_dist ** 2)
                        actual = rad
                        error += (predicted * 1000 - actual) ** 2  # Scale for numerical stability
                        
                if error < best_error:
                    best_error = error
                    best_pos = (source_lat, source_lon)
                    
        # Estimate activity
        avg_dist = np.mean([
            np.sqrt(((pos[0] - best_pos[0]) * 111320)**2 + 
                   ((pos[1] - best_pos[1]) * 111320 * np.cos(np.radians(pos[0])))**2 + alt**2)
            for pos, alt in zip(positions, altitudes)
        ])
        best_activity = np.mean(excess) * (avg_dist ** 2)
        
        # Determine source type based on activity
        if best_activity < 1000:
            source_type = "natural"
        elif best_activity < 10000:
            source_type = "technogenic"
        else:
            source_type = "unknown"
            
        # Calculate confidence based on fit quality
        confidence = max(0, 1 - best_error / (best_error + 10000))
        
        return RadiationSource(
            position=best_pos,
            confidence=confidence,
            estimated_activity=best_activity,
            source_type=source_type
        )
        
    def get_source_report(self) -> Dict:
        """Generate radiation source report."""
        source = self.estimate_source()
        
        if source is None:
            return {
                'status': 'No significant radiation source detected',
                'source': None
            }
            
        return {
            'status': 'Source detected',
            'source': {
                'position': f"{source.position[0]:.6f}, {source.position[1]:.6f}",
                'confidence': f"{source.confidence:.0%}",
                'estimated_activity': f"{source.estimated_activity:.0f} Bq",
                'type': source.source_type
            },
            'recommendation': self._get_recommendation(source)
        }
        
    def _get_recommendation(self, source: RadiationSource) -> str:
        """Get recommendation based on source."""
        if source.source_type == 'technogenic' and source.confidence > 0.7:
            return "Possible industrial radiation source detected. Notify authorities if activity is elevated."
        elif source.source_type == 'natural':
            return "Likely natural radiation source (granite, etc.). No action required."
        else:
            return "Uncertain source. Monitor readings during descent."


def create_inversion_detector() -> InversionLayerDetector:
    """Factory function."""
    return InversionLayerDetector()


def create_source_locator() -> RadiationSourceLocator:
    """Factory function."""
    return RadiationSourceLocator()


if __name__ == "__main__":
    print("Initializing Atmospheric Analysis Systems...")
    inversion_detector = create_inversion_detector()
    source_locator = create_source_locator()
    
    # Simulate atmospheric data
    print("Simulating atmospheric readings...")
    
    for i in range(100):
        altitude = 1000 - i * 10
        base_temp = 20 - altitude * 0.0065  # Normal lapse rate
        
        # Add inversion at 500-600m
        if 500 <= altitude <= 600:
            base_temp += 5  # Temperature inversion
            
        inversion_detector.add_reading(
            altitude=altitude,
            temperature=base_temp + np.random.normal(0, 0.5),
            voc=200 + (5 if 500 <= altitude <= 600 else 0) + np.random.normal(0, 30),
            pressure=1013 - i * 0.01
        )
        
    # Get inversion report
    report = inversion_detector.get_meteorological_report()
    print(f"\nInversion Detection: {report['status']}")
    if report.get('inversions'):
        for inv in report['inversions']:
            print(f"  - {inv['altitude_range']}: {inv['description']}")
            
    # Simulate radiation readings
    print("\nSimulating radiation readings...")
    
    # Normal background
    for i in range(20):
        source_locator.add_reading(
            position=(37.7749, -122.4194),
            altitude=800 - i * 20,
            radiation=0.5 + np.random.normal(0, 0.1),
            timestamp=i * 0.5
        )
        
    # Source detected at lower altitude
    for i in range(20, 40):
        source_locator.add_reading(
            position=(37.7752, -122.4192),
            altitude=400 - (i - 20) * 10,
            radiation=1.5 + np.random.normal(0, 0.2),  # Elevated
            timestamp=i * 0.5
        )
        
    source_report = source_locator.get_source_report()
    print(f"\nSource Locator: {source_report['status']}")
    if source_report.get('source'):
        print(f"  Position: {source_report['source']['position']}")
        print(f"  Confidence: {source_report['source']['confidence']}")
        print(f"  Type: {source_report['source']['type']}")