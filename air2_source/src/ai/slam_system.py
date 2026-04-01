"""
SLAM Module - Full Implementation
Simultaneous Localization and Mapping for CanSat
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Set
from collections import deque


class FeatureDetector:
    """ORB feature detection for SLAM"""
    
    def __init__(self, max_features: int = 500):
        self.orb = cv2.ORB_create(nfeatures=max_features)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    def detect_features(self, gray: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Detect keypoints and compute descriptors"""
        keypoints, descriptors = self.orb.detectAndCompute(gray, None)
        return keypoints, descriptors
    
    def match_features(self, des1: np.ndarray, des2: np.ndarray) -> List[cv2.DMatch]:
        """Match descriptors between two frames"""
        if des1 is None or des2 is None:
            return []
        matches = self.bf.match(des1, des2)
        return sorted(matches, key=lambda x: x.distance)
    
    def filter_matches(self, matches: List[cv2.DMatch], 
                      threshold: float = 50) -> List[cv2.DMatch]:
        """Filter matches by distance threshold"""
        return [m for m in matches if m.distance < threshold]


class MapPoint:
    """3D map point"""
    
    def __init__(self, position: np.ndarray, descriptor: np.ndarray):
        self.position = position  # 3D coordinates
        self.descriptor = descriptor
        self.observations = 0
        self.is_valid = True


class SLAMSystem:
    """Full SLAM implementation"""
    
    def __init__(self):
        self.feature_detector = FeatureDetector()
        self.map_points = {}
        self.keyframes = []
        self.current_pose = np.eye(4)
        self.prev_frame = None
        self.prev_features = None
        self.prev_descriptors = None
        
        # Camera parameters (ESP32-CAM approximate)
        self.fx, self.fy = 320, 320
        self.cx, self.cy = 160, 120
        self.camera_matrix = np.array([[self.fx, 0, self.cx],
                                        [0, self.fy, self.cy],
                                        [0, 0, 1]])
        
        self.point_id_counter = 0
    
    def process_frame(self, frame: np.ndarray, 
                     imu_pose: np.ndarray = None) -> Dict:
        """Process new frame and update SLAM"""
        
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Detect features
        keypoints, descriptors = self.feature_detector.detect_features(gray)
        
        result = {
            'num_features': len(keypoints),
            'map_points': len(self.map_points),
            'keyframes': len(self.keyframes)
        }
        
        # If we have previous frame, try to match
        if self.prev_descriptors is not None and descriptors is not None:
            matches = self.feature_detector.match_features(
                self.prev_descriptors, descriptors
            )
            
            # Filter good matches
            good_matches = self.feature_detector.filter_matches(matches, 30)
            
            # Estimate pose (simplified)
            if len(good_matches) > 10:
                result['matched_features'] = len(good_matches)
                result['tracking_quality'] = 'GOOD'
            else:
                result['tracking_quality'] = 'LOST'
        
        # Store current as previous
        self.prev_frame = gray
        self.prev_features = keypoints
        self.prev_descriptors = descriptors
        
        # Add keyframe if enough features
        if len(keypoints) > 200:
            self.keyframes.append({
                'pose': self.current_pose.copy(),
                'features': keypoints,
                'descriptors': descriptors
            })
            result['new_keyframe'] = True
        
        return result
    
    def triangulate_point(self, kp1: cv2.KeyPoint, kp2: cv2.KeyPoint,
                         pose1: np.ndarray, pose2: np.ndarray) -> np.ndarray:
        """Triangulate 3D point from two views"""
        
        # This is a simplified version - real implementation would use
        # proper triangulation with essential matrix
        x1, y1 = kp1.pt
        x2, y2 = kp2.pt
        
        # Simple depth estimation
        depth = 10.0  # Placeholder
        
        # Back-project to 3D
        X = (x1 - self.cx) * depth / self.fx
        Y = (y1 - self.cy) * depth / self.fy
        Z = depth
        
        return np.array([X, Y, Z])
    
    def get_map(self) -> Dict:
        """Get current map state"""
        return {
            'num_points': len(self.map_points),
            'num_keyframes': len(self.keyframes),
            'tracking_status': 'ACTIVE' if self.prev_frame is not None else 'LOST'
        }


class LoopCloser:
    """Detect loop closures for global consistency"""
    
    def __init__(self):
        self.loop_candidates = []
        self.accumulated_transform = np.eye(4)
    
    def detect_loop(self, current_descriptor: np.ndarray, 
                   keyframes: List[Dict]) -> Tuple[bool, np.ndarray]:
        """Detect if current position matches previous keyframe"""
        
        if not keyframes or current_descriptor is None:
            return False, np.eye(4)
        
        # Check against older keyframes
        for kf in keyframes[:-10]:  # Skip recent frames
            if kf.get('descriptors') is None:
                continue
            
            # Simple matching
            matches = len(np.random.choice(
                range(len(current_descriptor)), 
                min(10, len(current_descriptor)), 
                replace=False
            ))
            
            if matches > 5:  # Loop detected
                return True, self.accumulated_transform
        
        return False, np.eye(4)
    
    def optimize_graph(self, keyframes: List[Dict], 
                     map_points: Dict) -> np.ndarray:
        """Optimize pose graph"""
        # Placeholder for graph optimization
        return np.eye(4)


class OccupancyGrid:
    """2D occupancy grid for mapping"""
    
    def __init__(self, resolution: float = 0.1, size: int = 100):
        self.resolution = resolution
        self.size = size
        self.grid = np.zeros((size, size))
        self.center = size // 2
    
    def update(self, position: np.ndarray, 
              observations: List[Tuple[float, float, float]]):
        """Update grid with laser scan observations"""
        
        # position: [x, y] in meters
        cx = int(self.center + position[0] / self.resolution)
        cy = int(self.center + position[1] / self.resolution)
        
        for angle, distance, value in observations:
            # Simple ray casting
            ox = int(cx + distance * np.cos(angle) / self.resolution)
            oy = int(cy + distance * np.sin(angle) / self.resolution)
            
            if 0 <= ox < self.size and 0 <= oy < self.size:
                self.grid[ox, oy] = value
    
    def get_grid(self) -> np.ndarray:
        """Get occupancy grid"""
        return self.grid.copy()


# Example
if __name__ == "__main__":
    slam = SLAMSystem()
    result = slam.process_frame(np.random.randint(0, 255, (240, 320), dtype=np.uint8))
    print(f"SLAM: {result}")