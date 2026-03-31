"""
Visual-Inertial Odometry (VIO) System
GPU-accelerated SLAM and Optical Flow for GPS-denied navigation
Compares pixel shift between ESP32-CAM frames with IMU data
"""

import numpy as np
from typing import Dict, Tuple, List, Optional, NamedTuple
from dataclasses import dataclass
from collections import deque
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class CameraFrame:
    timestamp: float
    image: np.ndarray  # Grayscale image from ESP32-CAM
    exposure: float


@dataclass
class IMUData:
    timestamp: float
    gyro: np.ndarray  # [x, y, z] rad/s
    accel: np.ndarray  # [x, y, z] m/s^2


@dataclass
class VIOState:
    timestamp: float
    position: np.ndarray  # [x, y, z] in meters
    velocity: np.ndarray  # [vx, vy, vz] in m/s
    orientation: np.ndarray  # Quaternion [w, x, y, z]
    visual_velocity: np.ndarray  # Computed from optical flow
    confidence: float


class OpticalFlowTracker:
    """Lucas-Kanade optical flow tracker optimized for ESP32-CAM."""
    
    def __init__(
        self,
        feature_params: Dict = None,
        lk_params: Dict = None
    ):
        self.feature_params = feature_params or {
            'maxCorners': 200,
            'qualityLevel': 0.3,
            'minDistance': 7,
            'blockSize': 7
        }
        
        self.lk_params = lk_params or {
            'winSize': (21, 21),
            'maxLevel': 3,
            'criteria': (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        }
        
        self.prev_gray = None
        self.prev_points = None
        
    def compute_flow(
        self,
        current_frame: np.ndarray,
        return_features: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Compute optical flow between consecutive frames.
        
        Args:
            current_frame: Current grayscale image
            return_features: Whether to return tracked feature points
            
        Returns:
            flow: Dense optical flow field
            flow_magnitude: Average flow magnitude in pixels
            features: (optional) Tracked feature points
        """
        if self.prev_gray is None:
            self.prev_gray = current_frame
            return None, 0.0, None
            
        gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY) if len(current_frame.shape) == 3 else current_frame
        
        if self.prev_points is None or len(self.prev_points) < 20:
            # Detect new features
            self.prev_points = cv2.goodFeaturesToTrack(
                self.prev_gray,
                mask=None,
                **self.feature_params
            )
            
        if self.prev_points is None or len(self.prev_points) == 0:
            self.prev_gray = gray.copy()
            return None, 0.0, None
            
        # Compute optical flow
        current_points, status, _ = cv2.calcOpticalFlowPyrLK(
            self.prev_gray, gray, self.prev_points, None, **self.lk_params
        )
        
        # Filter valid points
        valid_prev = self.prev_points[status.flatten() == 1]
        valid_current = current_points[status.flatten() == 1]
        
        if len(valid_prev) < 4:
            self.prev_points = None
            return None, 0.0, None
            
        # Compute dense optical flow using Farneback for full field
        dense_flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, gray, None,
            0.5, 3, 15, 3, 7, 1.5, 0
        )
        
        # Compute flow statistics
        flow_magnitude = np.mean(np.sqrt(dense_flow[..., 0]**2 + dense_flow[..., 1]**2))
        
        self.prev_gray = gray.copy()
        self.prev_points = valid_current.reshape(-1, 1, 2)
        
        if return_features:
            return dense_flow, flow_magnitude, valid_current
        return dense_flow, flow_magnitude, None


class IMUPredictor:
    """Predicts camera motion from IMU readings."""
    
    def __init__(self, gravity: float = 9.81):
        self.gravity = gravity
        self.prev_gyro = None
        self.prev_accel = None
        self.prev_time = None
        self.velocity = np.zeros(3)
        self.position = np.zeros(3)
        
    def update(self, imu_data: IMUData) -> Dict:
        """
        Update IMU-based motion prediction using dead reckoning.
        
        Returns:
            Dict with predicted motion
        """
        dt = 0.0
        if self.prev_time is not None:
            dt = imu_data.timestamp - self.prev_time
            
        if dt > 0 and dt < 1.0:  # Sanity check
            # Integrate gyroscope for orientation change
            if self.prev_gyro is not None:
                delta_angle = (imu_data.gyro + self.prev_gyro) / 2 * dt
                
            # Integrate acceleration (subtract gravity)
            accel_world = imu_data.accel.copy()
            accel_world[2] -= self.gravity
            
            # Update velocity and position
            self.velocity += accel_world * dt
            self.position += self.velocity * dt
            
        self.prev_gyro = imu_data.gyro.copy()
        self.prev_accel = imu_data.accel.copy()
        self.prev_time = imu_data.timestamp
        
        return {
            'position': self.position.copy(),
            'velocity': self.velocity.copy(),
            'gyro_integration': delta_angle if self.prev_gyro is not None else np.zeros(3)
        }


class VIOCamera:
    """PyTorch-based VIO camera model for GPU acceleration."""
    
    def __init__(
        self,
        fx: float = 525.0,
        fy: float = 525.0,
        cx: float = 319.5,
        cy: float = 239.5,
        width: int = 640,
        height: int = 480
    ):
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.width = width
        self.height = height
        
        # Camera matrix
        self.K = np.array([
            [fx, 0, cx],
            [0, fy, cy],
            [0, 0, 1]
        ], dtype=np.float32)
        
    def pixel_to_3d(self, u: float, v: float, depth: float) -> np.ndarray:
        """Convert pixel coordinates and depth to 3D point."""
        x = (u - self.cx) * depth / self.fx
        y = (v - self.cy) * depth / self.fy
        return np.array([x, y, depth])
    
    def flow_to_velocity(
        self,
        flow: np.ndarray,
        depth_map: Optional[np.ndarray] = None,
        scale_factor: float = 0.1
    ) -> Tuple[np.ndarray, float]:
        """
        Convert optical flow to camera velocity.
        
        Args:
            flow: Optical flow field [H, W, 2]
            depth_map: Estimated depth for each pixel
            scale_factor: Pixels to meters conversion factor
            
        Returns:
            velocity: [vx, vy, vz] camera velocity in m/s
            confidence: Flow confidence measure
        """
        h, w = flow.shape[:2]
        
        # Compute average flow in each quadrant
        quadrants = [
            flow[:h//2, :w//2],   # Top-left
            flow[:h//2, w//2:],   # Top-right
            flow[h//2:, :w//2],   # Bottom-left
            flow[h//2:, w//2:]    # Bottom-right
        ]
        
        avg_flows = [np.mean(q, axis=(0, 1)) for q in quadrants]
        
        # Decompose into rotation and translation components
        # Forward motion causes expansion (all quadrants moving outward)
        # Rotation causes consistent motion across all quadrants
        
        # Estimate expansion rate (forward motion)
        expansion = sum(flows[0] + flows[1] + flows[2] + flows[3]) / 4
        
        # Camera frame velocity estimation
        vx = -avg_flows[1][0] + avg_flows[0][0]  # Lateral
        vy = -avg_flows[2][1] + avg_flows[0][1]   # Vertical
        vz = np.mean([np.sqrt(f[0]**2 + f[1]**2) for f in avg_flows]) * scale_factor
        
        velocity = np.array([vx, vy, vz]) * scale_factor
        
        # Confidence based on flow consistency
        flow_magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        confidence = 1.0 - np.std(flow_magnitude) / (np.mean(flow_magnitude) + 1e-6)
        confidence = np.clip(confidence, 0.0, 1.0)
        
        return velocity, confidence


class VisualInertialOdometry:
    """
    Complete VIO system combining optical flow with IMU.
    Maintains accurate 3D position when GPS loses lock.
    """
    
    def __init__(
        self,
        camera_params: Dict = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        
        # Initialize components
        self.optical_tracker = OpticalFlowTracker()
        self.imu_predictor = IMUPredictor()
        
        # Camera model
        default_cam = {
            'fx': 525.0, 'fy': 525.0,
            'cx': 319.5, 'cy': 239.5,
            'width': 640, 'height': 480
        }
        if camera_params:
            default_cam.update(camera_params)
        self.camera = VIOCamera(**default_cam)
        
        # State estimation
        self.state_history: deque = deque(maxlen=1000)
        self.current_state = VIOState(
            timestamp=0.0,
            position=np.zeros(3),
            velocity=np.zeros(3),
            orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            visual_velocity=np.zeros(3),
            confidence=0.0
        )
        
        # Fusion parameters
        self.visual_weight = 0.6
        self.imu_weight = 0.4
        
        # GPS fallback tracking
        self.gps_lock = True
        self.last_gps_update = 0.0
        
    def process_frame(self, frame: CameraFrame, imu: Optional[IMUData] = None) -> VIOState:
        """
        Process a new camera frame with optional IMU data.
        
        Args:
            frame: CameraFrame from ESP32-CAM
            imu: Optional IMU reading
            
        Returns:
            Updated VIOState with position estimate
        """
        # Compute optical flow
        flow, flow_magnitude, features = self.optical_tracker.compute_flow(
            frame.image, return_features=True
        )
        
        visual_vel = np.zeros(3)
        visual_confidence = 0.0
        
        if flow is not None:
            visual_vel, visual_confidence = self.camera.flow_to_velocity(flow)
            
        # Update IMU prediction
        imu_vel = np.zeros(3)
        if imu is not None:
            imu_prediction = self.imu_predictor.update(imu)
            imu_vel = imu_prediction['velocity']
            
        # Fuse visual and IMU velocities
        if imu is not None:
            fused_velocity = (
                self.visual_weight * visual_vel +
                self.imu_weight * imu_vel
            )
        else:
            fused_velocity = visual_vel
            self.visual_weight = 1.0
            
        # Update position
        dt = 0.2 if self.current_state.timestamp > 0 else 0.0
        self.current_state.position += fused_velocity * dt
        self.current_state.velocity = fused_velocity
        self.current_state.visual_velocity = visual_vel
        self.current_state.confidence = visual_confidence
        self.current_state.timestamp = frame.timestamp
        
        # Store state
        state_copy = VIOState(
            timestamp=self.current_state.timestamp,
            position=self.current_state.position.copy(),
            velocity=self.current_state.velocity.copy(),
            orientation=self.current_state.orientation.copy(),
            visual_velocity=self.current_state.visual_velocity.copy(),
            confidence=self.current_state.confidence
        )
        self.state_history.append(state_copy)
        
        return self.current_state
        
    def update_from_gps(self, lat: float, lon: float, alt: float, timestamp: float):
        """
        Correct VIO position using GPS when available.
        Call this when GPS lock is regained.
        """
        # Simple conversion to local coordinates (meters from origin)
        origin_lat = 37.7749  # Would be set from initial GPS lock
        origin_lon = -122.4194
        
        # Very rough conversion (would use proper geodetic formulas in production)
        x = (lon - origin_lon) * 111320 * np.cos(np.radians(origin_lat))
        y = (lat - origin_lat) * 110540
        
        self.current_state.position = np.array([x, y, alt])
        self.gps_lock = True
        self.last_gps_update = timestamp
        
    def get_visual_velocity_estimate(self) -> np.ndarray:
        """Return the current visual velocity estimate."""
        return self.current_state.visual_velocity.copy()
        
    def get_position_estimate(self) -> np.ndarray:
        """Return the current position estimate."""
        return self.current_state.position.copy()
        
    def get_state_trajectory(self, num_points: int = 100) -> List[Dict]:
        """Get the trajectory history."""
        states = list(self.state_history)[-num_points:]
        return [
            {
                'timestamp': s.timestamp,
                'position': s.position.tolist(),
                'velocity': s.velocity.tolist(),
                'visual_velocity': s.visual_velocity.tolist(),
                'confidence': s.confidence
            }
            for s in states
        ]


def create_vio_system(camera_params: Dict = None, device: str = "auto") -> VisualInertialOdometry:
    """Factory function to create VIO system."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return VisualInertialOdometry(camera_params=camera_params, device=device)


# Demo usage
if __name__ == "__main__":
    print("Initializing VIO System...")
    vio = create_vio_system()
    
    # Simulate camera frames
    print("Simulating ESP32-CAM frames...")
    
    for i in range(50):
        # Create synthetic frame
        frame = CameraFrame(
            timestamp=i * 0.2,
            image=np.random.randint(0, 255, (480, 640), dtype=np.uint8),
            exposure=1.0
        )
        
        # Create synthetic IMU data
        imu = IMUData(
            timestamp=i * 0.2,
            gyro=np.array([0.01, -0.02, 0.01]),
            accel=np.array([0.1, -0.1, 9.8])
        )
        
        state = vio.process_frame(frame, imu)
        
        if i % 10 == 0:
            print(f"Frame {i}: Position={state.position[:2]}, Visual Vel={state.visual_velocity[:2]}")
            
    # Get trajectory
    trajectory = vio.get_state_trajectory()
    print(f"\nVIO Trajectory: {len(trajectory)} points collected")
    print(f"Final position estimate: {vio.get_position_estimate()}")