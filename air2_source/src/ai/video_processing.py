"""
Video Stabilization Module - Full Implementation
Unsupervised video stabilization using IMU guidance
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple
from collections import deque


class IMUGyroStabilizer:
    """Stabilize video using IMU gyro data"""
    
    def __init__(self):
        self.gyro_history = deque(maxlen=30)
        self.cumulative_angle = {'x': 0, 'y': 0, 'z': 0}
        self.smooth_factor = 0.9
    
    def update_gyro(self, gx: float, gy: float, gz: float):
        """Update with gyro readings"""
        self.gyro_history.append({'gx': gx, 'gy': gy, 'gz': gz})
        
        # Apply low-pass filter
        self.cumulative_angle['x'] = (self.smooth_factor * self.cumulative_angle['x'] + 
                                       (1 - self.smooth_factor) * gx * 0.2)
        self.cumulative_angle['y'] = (self.smooth_factor * self.cumulative_angle['y'] + 
                                       (1 - self.smooth_factor) * gy * 0.2)
        self.cumulative_angle['z'] = (self.smooth_factor * self.cumulative_angle['z'] + 
                                       (1 - self.smooth_factor) * gz * 0.2)
    
    def get_rotation_matrix(self) -> np.ndarray:
        """Get rotation matrix for stabilization"""
        
        rx = np.radians(self.cumulative_angle['x'])
        ry = np.radians(self.cumulative_angle['y'])
        rz = np.radians(self.cumulative_angle['z'])
        
        # Rotation matrices
        Rx = np.array([[1, 0, 0],
                       [0, np.cos(rx), -np.sin(rx)],
                       [0, np.sin(rx), np.cos(rx)]])
        
        Ry = np.array([[np.cos(ry), 0, np.sin(ry)],
                       [0, 1, 0],
                       [-np.sin(ry), 0, np.cos(ry)]])
        
        Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                       [np.sin(rz), np.cos(rz), 0],
                       [0, 0, 1]])
        
        return Rz @ Ry @ Rx


class VideoStabilizer:
    """Full video stabilization using motion estimation"""
    
    def __init__(self):
        self.prev_gray = None
        self.prev_transform = np.eye(3)
        self.transform_history = deque(maxlen=30)
        self.smoothing_window = 15
    
    def stabilize_frame(self, frame: np.ndarray, 
                       imu_rotation: np.ndarray = None) -> Tuple[np.ndarray, Dict]:
        """Stabilize a single frame"""
        
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        stabilized = frame.copy()
        motion_info = {'translation': [0, 0], 'rotation': 0}
        
        if self.prev_gray is not None:
            # Compute optical flow for motion estimation
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2
            )
            
            # Extract motion
            dx = np.mean(flow[..., 0])
            dy = np.mean(flow[..., 1])
            
            # Build transformation matrix
            transform = np.eye(3)
            transform[0, 2] = -dx * 0.5  # Smooth translation
            transform[1, 2] = -dy * 0.5
            
            # Apply IMU rotation if available
            if imu_rotation is not None:
                transform[:2, :2] = imu_rotation[:2, :2]
            
            # Smooth transform
            self.prev_transform = 0.9 * self.prev_transform + 0.1 * transform
            
            # Apply stabilization
            h, w = frame.shape[:2]
            M = self.prev_transform
            stabilized = cv2.warpAffine(frame, M[:2, :], (w, h))
            
            motion_info = {
                'translation': [dx, dy],
                'rotation': np.arctan2(M[1, 0], M[0, 0])
            }
        
        self.prev_gray = gray
        self.transform_history.append(self.prev_transform.copy())
        
        return stabilized, motion_info
    
    def get_horizon_angle(self) -> float:
        """Get estimated horizon angle"""
        
        if len(self.transform_history) < 2:
            return 0
        
        angles = []
        for t in list(self.transform_history)[-5:]:
            angle = np.arctan2(t[1, 0], t[0, 0])
            angles.append(angle)
        
        return np.median(angles)


class SuperResolution:
    """Real-ESRGAN style super-resolution (simplified)"""
    
    def __init__(self, scale: int = 2):
        self.scale = scale
        # Create simple upsampling kernel
        self.kernel = np.array([[1, 2, 1],
                                [2, 4, 2],
                                [1, 2, 1]]) / 16.0
    
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """Upscale image using bicubic interpolation + enhancement"""
        
        h, w = image.shape[:2]
        
        # Bicubic upscale
        upscaled = cv2.resize(image, (w * self.scale, h * self.scale),
                            interpolation=cv2.INTER_CUBIC)
        
        # Sharpen
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) / 5.0
        sharpened = cv2.filter2D(upscaled, -1, kernel)
        
        # Blend
        return cv2.addWeighted(upscaled, 0.7, sharpened, 0.3, 0)
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Apply denoising"""
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)


class SemanticSegmenter:
    """SegFormer-style semantic segmentation (simplified)"""
    
    def __init__(self):
        self.classes = ['sky', 'ground', 'building', 'vegetation', 'water', 'road']
        
    def segment(self, frame: np.ndarray) -> Dict:
        """Segment frame into semantic classes"""
        
        h, w = frame.shape[:2]
        
        # Convert to different color spaces
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
        # Simple rule-based segmentation
        masks = {}
        
        # Sky (high value, low saturation)
        sky_mask = ((hsv[..., 1] < 50) & (hsv[..., 2] > 150)).astype(np.uint8) * 255
        masks['sky'] = sky_mask
        
        # Vegetation (green hues)
        green_mask = cv2.inRange(hsv, (25, 40, 40), (85, 255, 255))
        masks['vegetation'] = green_mask
        
        # Water (blue hues)
        water_mask = cv2.inRange(hsv, (90, 40, 40), (130, 255, 255))
        masks['water'] = water_mask
        
        # Buildings (gray, high brightness)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        building_mask = ((gray > 80) & (gray < 180)).astype(np.uint8) * 255
        masks['building'] = building_mask
        
        # Ground/road (brown/gray)
        road_mask = ((gray > 40) & (gray < 100)).astype(np.uint8) * 255
        masks['ground'] = road_mask
        
        # Calculate class percentages
        total_pixels = h * w
        percentages = {}
        
        for cls, mask in masks.items():
            percentages[cls] = np.count_nonzero(mask) / total_pixels
        
        # Find dominant class
        dominant = max(percentages.items(), key=lambda x: x[1])
        
        return {
            'dominant_class': dominant[0],
            'dominant_ratio': dominant[1],
            'percentages': percentages,
            'masks': masks
        }


class AutoencoderAnomaly:
    """Autoencoder-based anomaly detection for radiation"""
    
    def __init__(self, input_dim: int = 50):
        self.input_dim = input_dim
        # Simple placeholder - real would use trained autoencoder
        self.threshold = 0.5
        self.history = deque(maxlen=100)
    
    def train(self, normal_data: np.ndarray):
        """Train on normal data"""
        self.mean = np.mean(normal_data, axis=0)
        self.std = np.std(normal_data, axis=0) + 1e-10
    
    def detect_anomaly(self, data: np.ndarray) -> Tuple[bool, float]:
        """Detect anomaly"""
        
        if not hasattr(self, 'mean'):
            return False, 0.0
        
        # Reconstruction error (simplified)
        z_score = np.max(np.abs((data - self.mean) / self.std))
        
        is_anomaly = z_score > 3.0
        
        self.history.append(z_score)
        
        return is_anomaly, z_score


class ChangePointDetector:
    """CPD for atmospheric inversion layer detection"""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.data_history = {'temperature': deque(maxlen=100),
                            'pressure': deque(maxlen=100),
                            'altitude': deque(maxlen=100)}
    
    def update(self, temperature: float, pressure: float, altitude: float):
        """Update with sensor data"""
        self.data_history['temperature'].append(temperature)
        self.data_history['pressure'].append(pressure)
        self.data_history['altitude'].append(altitude)
    
    def detect_inversion(self) -> Tuple[bool, Dict]:
        """Detect temperature inversion layer"""
        
        temps = list(self.data_history['temperature'])
        alts = list(self.data_history['altitude'])
        
        if len(temps) < self.window_size:
            return False, {}
        
        # Split into two windows
        window1_temps = temps[-self.window_size:-self.window_size//2]
        window2_temps = temps[-self.window_size//2:]
        
        window1_alts = alts[-self.window_size:-self.window_size//2]
        window2_alts = alts[-self.window_size//2:]
        
        # Calculate average temps and alts
        avg_temp1 = np.mean(window1_temps)
        avg_temp2 = np.mean(window2_temps)
        avg_alt1 = np.mean(window1_alts)
        avg_alt2 = np.mean(window2_alts)
        
        # Lapse rate for each window
        if avg_alt2 != avg_alt1:
            lr1 = (avg_temp1 - np.mean(temps[-self.window_size:-self.window_size*3//4])) / (avg_alt1 - np.mean(alts[-self.window_size:-self.window_size*3//4]))
            lr2 = (np.mean(temps[-self.window_size*3//4:]) - avg_temp2) / (np.mean(alts[-self.window_size*3//4:]) - avg_alt2)
        else:
            lr1 = lr2 = 0
        
        # Inversion: temp increases with altitude
        is_inversion = lr2 > 0 and lr1 < 0
        
        return is_inversion, {
            'lower_lapse_rate': lr1,
            'upper_lapse_rate': lr2,
            'inversion_altitude': avg_alt2,
            'confidence': abs(lr2) if is_inversion else 0
        }


class BayesianSourceLocator:
    """Bayesian inference for radiation/VOC source localization"""
    
    def __init__(self):
        self.measurements = []
        self.wind_measurements = []
    
    def add_measurement(self, lat: float, lon: float, alt: float,
                       concentration: float, wind_speed: float, wind_dir: float):
        """Add environmental measurement"""
        self.measurements.append({
            'lat': lat, 'lon': lon, 'alt': alt,
            'concentration': concentration
        })
        self.wind_measurements.append({
            'speed': wind_speed, 'direction': wind_dir
        })
    
    def estimate_source(self) -> Dict:
        """Estimate most likely source location"""
        
        if len(self.measurements) < 3:
            return {'lat': 0, 'lon': 0, 'confidence': 0}
        
        # Back-propagation using wind
        # For each measurement, trace back along wind vector
        source_candidates = []
        
        for i, m in enumerate(self.measurements):
            if i >= len(self.wind_measurements):
                continue
            
            wind = self.wind_measurements[i]
            
            # Distance traveled (assume concentration decreases with distance)
            distance = 1000 / (m['concentration'] + 1)  # Simplified
            
            # Back-propagate
            angle = np.radians(wind['direction'])
            dx = distance * np.cos(angle)
            dy = distance * np.sin(angle)
            
            # Convert to degrees (approximate)
            source_lat = m['lat'] - dy / 111000
            source_lon = m['lon'] - dx / (111000 * np.cos(np.radians(m['lat'])))
            
            source_candidates.append({
                'lat': source_lat,
                'lon': source_lon,
                'weight': m['concentration']
            })
        
        if not source_candidates:
            return {'lat': 0, 'lon': 0, 'confidence': 0}
        
        # Weighted average
        total_weight = sum(c['weight'] for c in source_candidates)
        est_lat = sum(c['lat'] * c['weight'] for c in source_candidates) / total_weight
        est_lon = sum(c['lon'] * c['weight'] for c in source_candidates) / total_weight
        
        return {
            'lat': est_lat,
            'lon': est_lon,
            'confidence': min(0.9, total_weight / 100),
            'num_candidates': len(source_candidates)
        }


# Example
if __name__ == "__main__":
    vs = VideoStabilizer()
    stabilized, info = vs.stabilize_frame(np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8))
    print(f"Stabilization: {info}")
    
    ss = SuperResolution()
    upscaled = ss.upscale(np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8))
    print(f"Upscaled shape: {upscaled.shape}")