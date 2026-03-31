"""
YOLOv8/v10 Terrain Segmentation for Real-Time Hazard Detection
GPU-accelerated object detection on ESP32-CAM 200ms image packets
Detects landing targets, power lines, roads, and points of interest
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import torch
import torch.nn as nn


class TerrainClass(Enum):
    """Terrain classification categories."""
    LANDING_TARGET = 0
    POWER_LINES = 1
    ROAD = 2
    WATER = 3
    BUILDING = 4
    FOREST = 5
    GRASS = 6
    CLEARING = 7
    UNKNOWN = 8


@dataclass
class DetectedObject:
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]


@dataclass
class TerrainAnalysis:
    timestamp: float
    frame_id: int
    detections: List[DetectedObject]
    hazard_map: np.ndarray
    safest_direction: str
    dominant_terrain: str
    poi_locations: Dict[str, Tuple[float, float]]


class YOLOTerrainSegmenter:
    """
    YOLO-based terrain segmentation for real-time hazard detection.
    Processes ESP32-CAM frames every 200ms to detect POIs and hazards.
    """
    
    # Class mappings for terrain detection
    CLASS_NAMES = [
        'landing_target', 'power_line', 'road', 'water',
        'building', 'forest', 'grass', 'clearing', 'obstacle'
    ]
    
    # Hazard weights (higher = more dangerous)
    HAZARD_WEIGHTS = {
        'landing_target': -1.0,  # Good - negative is safe
        'power_line': 2.0,
        'road': 0.5,
        'water': 1.5,
        'building': 1.0,
        'forest': 0.3,
        'grass': -0.8,
        'clearing': -0.9,
        'obstacle': 2.0
    }
    
    def __init__(
        self,
        model_size: str = "n",  # n, s, m, l, x
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        
        # Initialize model (using a simplified CNN in practice)
        # In production, load actual YOLO weights
        self.model = self._create_model(model_size)
        self.model.eval()
        
        # Detection history
        self.detection_history: List[TerrainAnalysis] = []
        
    def _create_model(self, size: str) -> nn.Module:
        """Create YOLO-style model."""
        # Simplified architecture - in production use ultralytics YOLO
        base_channels = {'n': 16, 's': 32, 'm': 64, 'l': 128, 'x': 256}[size]
        
        class SimpleYOLO(nn.Module):
            def __init__(self, channels):
                super().__init__()
                # Backbone
                self.backbone = nn.Sequential(
                    nn.Conv2d(3, channels, 3, 2, 1),
                    nn.BatchNorm2d(channels),
                    nn.SiLU(),
                    nn.Conv2d(channels, channels * 2, 3, 2, 1),
                    nn.BatchNorm2d(channels * 2),
                    nn.SiLU(),
                    nn.Conv2d(channels * 2, channels * 2, 3, 2, 1),
                    nn.BatchNorm2d(channels * 2),
                    nn.SiLU(),
                )
                
                # Detection heads
                self.det_head = nn.Sequential(
                    nn.Conv2d(channels * 2, channels * 4, 3, 1, 1),
                    nn.BatchNorm2d(channels * 4),
                    nn.SiLU(),
                    nn.Conv2d(channels * 4, 45, 1)  # 9 classes * 5 (bbox + obj + cls)
                )
                
            def forward(self, x):
                feat = self.backbone(x)
                return self.det_head(feat)
                
        return SimpleYOLO(base_channels).to(device)
        
    def process_frame(
        self,
        frame: np.ndarray,
        timestamp: float,
        frame_id: int
    ) -> TerrainAnalysis:
        """
        Process a single frame for terrain detection.
        
        Args:
            frame: RGB image from ESP32-CAM
            timestamp: Frame timestamp
            frame_id: Frame identifier
            
        Returns:
            TerrainAnalysis with detections and hazard map
        """
        # Preprocess
        input_tensor = self._preprocess_frame(frame)
        
        # Run inference
        with torch.no_grad():
            predictions = self.model(input_tensor)
            
        # Post-process detections
        detections = self._postprocess_predictions(predictions, frame.shape[:2])
        
        # Generate hazard map
        hazard_map = self._generate_hazard_map(frame.shape[:2], detections)
        
        # Determine safest direction
        safest_dir, direction_scores = self._find_safest_direction(hazard_map)
        
        # Get dominant terrain
        dominant = self._get_dominant_terrain(detections)
        
        # Collect POI locations
        poi_locations = self._extract_poi_locations(detections)
        
        analysis = TerrainAnalysis(
            timestamp=timestamp,
            frame_id=frame_id,
            detections=detections,
            hazard_map=hazard_map,
            safest_direction=safest_dir,
            dominant_terrain=dominant,
            poi_locations=poi_locations
        )
        
        self.detection_history.append(analysis)
        
        return analysis
        
    def _preprocess_frame(self, frame: np.ndarray) -> torch.Tensor:
        """Preprocess frame for model input."""
        # Resize to 640x640
        import cv2
        resized = cv2.resize(frame, (640, 640))
        
        # Normalize
        normalized = resized.astype(np.float32) / 255.0
        
        # Convert to tensor
        tensor = torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0)
        
        return tensor.to(self.device)
        
    def _postprocess_predictions(
        self,
        predictions: torch.Tensor,
        image_shape: Tuple[int, int]
    ) -> List[DetectedObject]:
        """Parse model predictions into DetectedObjects."""
        detections = []
        
        # This is a simplified version - real YOLO uses NMS
        pred_np = predictions[0].cpu().numpy()
        
        # Iterate through predictions (simplified)
        h, w = image_shape
        grid_size = 20
        
        for i in range(0, len(pred_np[0]), 5):
            if i + 4 >= len(pred_np[0]):
                break
                
            # Extract prediction
            pred = pred_np[:, i:i+5]
            
            # Find max confidence
            max_idx = np.argmax(pred[:, 4])
            conf = pred[max_idx, 4]
            
            if conf > self.confidence_threshold:
                class_id = np.argmax(pred[max_idx, 5:]) if pred.shape[1] > 5 else 0
                
                # Create detection
                # Convert grid coordinates to pixel coordinates
                grid_x = i % grid_size
                grid_y = i // grid_size
                
                x1 = int((grid_x / grid_size) * w)
                y1 = int((grid_y / grid_size) * h)
                x2 = int(x1 + 50)
                y2 = int(y1 + 50)
                
                detection = DetectedObject(
                    class_id=int(class_id),
                    class_name=self.CLASS_NAMES[class_id] if class_id < len(self.CLASS_NAMES) else 'unknown',
                    confidence=float(conf),
                    bbox=(x1, y1, x2, y2),
                    center=((x1 + x2) // 2, (y1 + y2) // 2)
                )
                detections.append(detection)
                
        return detections
        
    def _generate_hazard_map(
        self,
        shape: Tuple[int, int],
        detections: List[DetectedObject]
    ) -> np.ndarray:
        """Generate a heat map of hazard probabilities."""
        h, w = shape
        hazard_map = np.zeros((h, w), dtype=np.float32)
        
        # Add base terrain gradient (lower is safer)
        center_y, center_x = h // 2, w // 2
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        
        # Radial gradient - center is safest for landing
        distance_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        hazard_map -= np.clip(100 - distance_from_center, 0, 100) / 100
        
        # Add hazard zones from detections
        for det in detections:
            class_name = det.class_name
            if class_name in self.HAZARD_WEIGHTS:
                weight = self.HAZARD_WEIGHTS[class_name]
                
                x1, y1, x2, y2 = det.bbox
                # Create gaussian blob around detection
                y_range = slice(max(0, y1 - 20), min(h, y2 + 20))
                x_range = slice(max(0, x1 - 20), min(w, x2 + 20))
                
                yy, xx = np.mgrid[y_range, x_range]
                center_y, center_x = (y1 + y2) // 2, (x1 + x2) // 2
                
                sigma = 30
                blob = np.exp(-((xx - center_x)**2 + (yy - center_y)**2) / (2 * sigma**2))
                
                if weight > 0:
                    hazard_map[y_range, x_range] += blob * weight
                else:
                    hazard_map[y_range, x_range] += blob * weight  # Negative adds safety
                    
        return np.clip(hazard_map, -1, 1)
        
    def _find_safest_direction(
        self,
        hazard_map: np.ndarray
    ) -> Tuple[str, Dict[str, float]]:
        """Find the safest direction to steer."""
        h, w = hazard_map.shape
        center_y, center_x = h // 2, w // 2
        
        directions = {
            'UP': hazard_map[:center_y, :],
            'DOWN': hazard_map[center_y:, :],
            'LEFT': hazard_map[:, :center_x],
            'RIGHT': hazard_map[:, center_x:],
            'UP_LEFT': hazard_map[:center_y, :center_x],
            'UP_RIGHT': hazard_map[:center_y, center_x:],
            'DOWN_LEFT': hazard_map[center_y:, :center_x],
            'DOWN_RIGHT': hazard_map[center_y:, center_x:]
        }
        
        # Compute mean hazard for each direction
        scores = {dir: np.mean(arr) for dir, arr in directions.items()}
        
        safest = min(scores, key=scores.get)
        
        return safest, scores
        
    def _get_dominant_terrain(self, detections: List[DetectedObject]) -> str:
        """Get the dominant terrain type."""
        if not detections:
            return "unknown"
            
        class_counts = {}
        for det in detections:
            class_name = det.class_name
            class_counts[class_name] = class_counts.get(class_name, 0) + det.confidence
            
        return max(class_counts, key=class_counts.get)
        
    def _extract_poi_locations(
        self,
        detections: List[DetectedObject]
    ) -> Dict[str, Tuple[float, float]]:
        """Extract point of interest locations."""
        pois = {}
        
        for det in detections:
            if det.class_name in ['landing_target', 'power_line', 'road']:
                pois[det.class_name] = det.center
                
        return pois
        
    def get_hazard_report(self) -> Dict:
        """Generate a summary report of hazards detected."""
        if not self.detection_history:
            return {"status": "No data"}
            
        recent = self.detection_history[-50:]
        
        all_detections = []
        for analysis in recent:
            all_detections.extend(analysis.detections)
            
        # Count by class
        class_counts = {}
        for det in all_detections:
            class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
            
        return {
            "total_detections": len(all_detections),
            "class_distribution": class_counts,
            "frame_count": len(recent),
            "latest_safest_direction": recent[-1].safest_direction if recent else "unknown"
        }


def create_yolo_terrain_segmenter(
    model_size: str = "n",
    device: str = "auto"
) -> YOLOTerrainSegmenter:
    """Factory function."""
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return YOLOTerrainSegmenter(model_size=model_size, device=device)


# Demo
if __name__ == "__main__":
    import cv2
    
    print("Initializing YOLOTerrainSegmenter...")
    segmenter = create_yolo_terrain_segmenter()
    
    # Simulate frame processing
    print("Processing simulated frames...")
    
    for i in range(20):
        # Create synthetic frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        analysis = segmenter.process_frame(frame, timestamp=i * 0.2, frame_id=i)
        
        if i % 5 == 0:
            print(f"Frame {i}: {len(analysis.detections)} detections, "
                  f"Safest: {analysis.safest_direction}, "
                  f"Dominant: {analysis.dominant_terrain}")
                
    # Get hazard report
    report = segmenter.get_hazard_report()
    print(f"\nHazard Report: {report}")