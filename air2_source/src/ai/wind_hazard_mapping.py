"""
Optical Flow Wind Vector Sensing & Predictive Landing Zone Contamination
Visual drift calculation for wind estimation
Hazard perimeter generation for recovery team
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import cv2


@dataclass
class WindEstimate:
    timestamp: float
    altitude: float
    speed: float  # m/s
    direction: float  # degrees (0 = North, clockwise)
    confidence: float
    source: str  # 'visual_flow', 'imu_fusion', 'barometric'


@dataclass
class ContaminationZone:
    center: Tuple[float, float]
    radius: float  # meters
    voc_level: float
    radiation_level: float
    hazard_score: float  # 0-10 scale
    color: Tuple[int, int, int]


class OpticalFlowWindSensor:
    """
    Wind estimation using ESP32-CAM optical flow and IMU.
    Calculates visual drift to estimate wind speed and direction.
    """
    
    def __init__(
        self,
        ground_resolution: float = 0.1,  # meters per pixel
        camera_height: float = 480  # pixels
    ):
        self.ground_resolution = ground_resolution
        self.camera_height = camera_height
        
        # Tracking
        self.prev_image = None
        self.prev_timestamp = None
        self.velocity_history: deque = deque(maxlen=50)
        
        # IMU integration
        self.imu_angles = deque(maxlen=50)
        
        # Wind estimation
        self.wind_estimate = WindEstimate(0, 0, 0, 0, 0, 'none')
        
    def process_frame(
        self,
        image: np.ndarray,
        timestamp: float,
        imu_gyro: Tuple[float, float, float],
        altitude: float,
        descent_rate: float
    ) -> WindEstimate:
        """
        Process frame and estimate wind vector.
        
        Args:
            image: Grayscale image from ESP32-CAM
            timestamp: Frame timestamp
            imu_gyro: Gyroscope readings (x, y, z)
            altitude: Current altitude
            descent_rate: Current descent rate (m/s)
            
        Returns:
            WindEstimate with speed and direction
        """
        current_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        if self.prev_image is not None and self.prev_timestamp is not None:
            dt = timestamp - self.prev_timestamp
            
            if dt > 0:
                # Compute optical flow
                flow = cv2.calcOpticalFlowFarneback(
                    self.prev_image, current_image, None,
                    0.5, 3, 15, 3, 7, 1.5, 0
                )
                
                # Get average flow in center region (avoid edge artifacts)
                h, w = flow.shape[:2]
                center_region = flow[h//4:3*h//4, w//4:3*w//4]
                
                avg_flow_x = np.median(center_region[..., 0])
                avg_flow_y = np.median(center_region[..., 1])
                
                # Calculate pixel velocity
                pixel_velocity_x = avg_flow_x / dt  # pixels per second
                pixel_velocity_y = avg_flow_y / dt
                
                # Convert to ground velocity using altitude
                # Pixels moved / focal_length * altitude
                focal_length = 525  # Approximate focal length
                ground_velocity_x = (pixel_velocity_x / focal_length) * altitude
                ground_velocity_y = (pixel_velocity_y / focal_length) * altitude
                
                # Subtract camera motion (from IMU and descent)
                # The camera motion tells us how the CanSat is moving
                camera_motion_x = imu_gyro[1] * altitude * 0.1  # roll effect
                camera_motion_y = imu_gyro[0] * altitude * 0.1  # pitch effect
                
                # Apparent ground motion = wind + camera motion
                apparent_vx = ground_velocity_x
                apparent_vy = ground_velocity_y
                
                # Wind is what's left after removing known camera motion
                wind_vx = apparent_vx - camera_motion_x
                wind_vy = apparent_vy - camera_motion_y
                
                # Calculate wind speed and direction
                wind_speed = np.sqrt(wind_vx**2 + wind_vy**2)
                
                # Direction: 0 = North, clockwise
                wind_direction = np.degrees(np.arctan2(wind_vy, wind_vx)) % 360
                
                # Confidence based on flow magnitude and consistency
                flow_magnitude = np.sqrt(avg_flow_x**2 + avg_flow_y**2)
                confidence = min(1.0, flow_magnitude / 10)  # Higher flow = higher confidence
                
                # Store in history
                self.velocity_history.append((wind_speed, wind_direction, timestamp))
                
                # Smooth estimate with rolling average
                if len(self.velocity_history) > 5:
                    recent = list(self.velocity_history)[-10:]
                    avg_speed = np.mean([v[0] for v in recent])
                    # Circular average for direction
                    directions = [np.radians(v[1]) for v in recent]
                    avg_dir = np.degrees(np.argmin([  # Simple circular mean
                        sum([np.cos(d) for d in directions])**2 + sum([np.sin(d) for d in directions])**2
                        for _ in [1]
                    ]))
                    
                    self.wind_estimate = WindEstimate(
                        timestamp=timestamp,
                        altitude=altitude,
                        speed=avg_speed,
                        direction=avg_dir,
                        confidence=confidence,
                        source='visual_flow'
                    )
                else:
                    self.wind_estimate = WindEstimate(
                        timestamp=timestamp,
                        altitude=altitude,
                        speed=wind_speed,
                        direction=wind_direction,
                        confidence=confidence,
                        source='visual_flow'
                    )
                    
        self.prev_image = current_image.copy()
        self.prev_timestamp = timestamp
        
        return self.wind_estimate
        
    def get_wind_profile(self) -> List[Dict]:
        """Get wind measurements at different altitudes."""
        measurements = []
        for speed, direction, timestamp in self.velocity_history:
            measurements.append({
                'speed': speed,
                'direction': direction,
                'timestamp': timestamp
            })
        return measurements[-50:]


class HazardContaminationMapper:
    """
    Predictive landing zone contamination mapping.
    Combines landing prediction with VOC/radiation for hazard perimeters.
    """
    
    HAZARD_THRESHOLDS = {
        'voc_moderate': 300,      # ppm
        'voc_high': 600,          # ppm
        'radiation_moderate': 1.0,  # µSv/h
        'radiation_high': 2.5      # µSv/h
    }
    
    def __init__(self):
        self.contamination_zones: List[ContaminationZone] = []
        self.landing_prediction = None
        
    def add_measurement(
        self,
        position: Tuple[float, float],
        altitude: float,
        voc_level: float,
        radiation_level: float,
        timestamp: float
    ):
        """Add contamination measurement."""
        # Calculate hazard score (0-10)
        voc_score = min(5, voc_level / self.HAZARD_THRESHOLDS['voc_high'] * 5)
        rad_score = min(5, radiation_level / self.HAZARD_THRESHOLDS['radiation_high'] * 5)
        hazard_score = (voc_score + rad_score) / 2 * 2  # Scale to 0-10
        
        # Determine color based on hazard
        if hazard_score < 3:
            color = (0, 255, 0)  # Green
        elif hazard_score < 6:
            color = (255, 255, 0)  # Yellow
        elif hazard_score < 8:
            color = (255, 128, 0)  # Orange
        else:
            color = (255, 0, 0)  # Red
            
        # Calculate zone radius based on altitude (higher = larger spread)
        radius = max(10, min(100, 200 - altitude / 5))
        
        zone = ContaminationZone(
            center=position,
            radius=radius,
            voc_level=voc_level,
            radiation_level=radiation_level,
            hazard_score=hazard_score,
            color=color
        )
        
        self.contamination_zones.append(zone)
        
        # Keep only recent zones (cleanup old ones)
        if len(self.contamination_zones) > 200:
            self.contamination_zones = self.contamination_zones[-200:]
            
    def set_landing_prediction(self, position: Tuple[float, float], uncertainty: float):
        """Set predicted landing position."""
        self.landing_prediction = {
            'position': position,
            'uncertainty': uncertainty,
            'radius': uncertainty * 2  # Ellipse radius based on uncertainty
        }
        
    def generate_hazard_perimeter(self) -> Dict:
        """
        Generate hazard perimeter data for map visualization.
        
        Returns:
            Dict with perimeter circles and warnings
        """
        if not self.contamination_zones:
            return {'status': 'No data'}
            
        # Find highest hazard zone near landing
        landing_pos = self.landing_prediction['position'] if self.landing_prediction else None
        
        hazards_near_landing = []
        all_hazards = []
        
        for zone in self.contamination_zones[-50:]:
            zone_data = {
                'center': zone.center,
                'radius': zone.radius,
                'hazard_score': zone.hazard_score,
                'color': list(zone.color),
                'voc_level': zone.voc_level,
                'radiation_level': zone.radiation_level
            }
            
            all_hazards.append(zone_data)
            
            if landing_pos:
                dist = self._haversine_distance(zone.center, landing_pos)
                if dist < 50:  # Within 50m of landing
                    hazards_near_landing.append(zone_data)
                    
        # Generate warning messages
        warnings = []
        
        if hazards_near_landing:
            avg_hazard = np.mean([z['hazard_score'] for z in hazards_near_landing])
            if avg_hazard > 7:
                warnings.append("CRITICAL: High contamination hazard near landing zone!")
                warnings.append("Recovery team should wear protective equipment.")
            elif avg_hazard > 4:
                warnings.append("WARNING: Moderate contamination detected at landing zone.")
                warnings.append("Advise caution during recovery.")
                
        return {
            'landing_prediction': self.landing_prediction,
            'hazard_zones': all_hazards,
            'hazards_near_landing': hazards_near_landing,
            'warnings': warnings,
            'recovery_priority': 'HIGH' if len(hazards_near_landing) > 3 else 'NORMAL'
        }
        
    def _haversine_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate distance between two GPS positions in meters."""
        lat1, lon1 = pos1
        lat2, lon2 = pos2
        
        R = 6371000  # Earth radius in meters
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        
        a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
        
    def get_safety_recommendation(self) -> str:
        """Get safety recommendation for recovery team."""
        if not self.contamination_zones:
            return "No contamination data available. Proceed with standard protocols."
            
        recent_zones = self.contamination_zones[-20:]
        max_hazard = max(z.hazard_score for z in recent_zones)
        
        if max_hazard > 8:
            return "DANGER: High contamination zone. Full hazmat suit required."
        elif max_hazard > 6:
            return "CAUTION: Moderate contamination. respirator and gloves recommended."
        elif max_hazard > 4:
            return "ADVISORY: Low-level contamination. Standard PPE sufficient."
        else:
            return "CLEAR: No significant contamination detected."


def create_wind_sensor() -> OpticalFlowWindSensor:
    """Factory function."""
    return OpticalFlowWindSensor()
    
def create_hazard_mapper() -> HazardContaminationMapper:
    """Factory function."""
    return HazardContaminationMapper()


if __name__ == "__main__":
    print("Initializing Wind and Hazard Systems...")
    wind_sensor = create_wind_sensor()
    hazard_mapper = create_hazard_mapper()
    
    # Simulate frames
    print("Simulating optical flow wind sensing...")
    
    for i in range(50):
        frame = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        gyro = (np.random.normal(0, 0.1), np.random.normal(0, 0.1), np.random.normal(0, 0.05))
        
        wind = wind_sensor.process_frame(
            frame,
            timestamp=i * 0.2,
            imu_gyro=gyro,
            altitude=500 - i * 10,
            descent_rate=10
        )
        
        if i % 10 == 0:
            print(f"Frame {i}: Wind Speed={wind.speed:.2f}m/s, Direction={wind.direction:.1f}°")
            
    # Simulate hazard mapping
    print("\nSimulating hazard contamination mapping...")
    
    for i in range(30):
        hazard_mapper.add_measurement(
            position=(37.7749 + i * 0.0001, -122.4194),
            altitude=500 - i * 15,
            voc_level=200 + np.random.normal(100, 50),
            radiation_level=0.5 + np.random.normal(0, 0.2),
            timestamp=i * 0.5
        )
        
    hazard_mapper.set_landing_prediction((37.7770, -122.4194), 15)
    
    perimeter = hazard_mapper.generate_hazard_perimeter()
    print(f"\nHazard Perimeter: {len(perimeter.get('hazard_zones', []))} zones")
    print(f"Recovery Priority: {perimeter.get('recovery_priority', 'NORMAL')}")
    print(f"Safety: {hazard_mapper.get_safety_recommendation()}")