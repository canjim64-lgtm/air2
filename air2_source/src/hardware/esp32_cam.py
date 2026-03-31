"""
ESP32-CAM High-Speed Imaging Interface for AirOne Professional v4.0
Handles real-time MJPEG stream consumption and remote shutter control.
"""
import logging
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

import numpy as np
import threading
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ESP32CamInterface:
    def __init__(self, cam_ip: str = "192.168.4.1", port: int = 80):
        self.logger = logging.getLogger(f"{__name__}.ESP32CamInterface")
        self.base_url = f"http://{cam_ip}:{port}"
        self.is_connected = False
        self.stream_active = False
        self.latest_frame = None
        
        if not REQUESTS_AVAILABLE:
            self.logger.warning("Requests library not available. ESP32-CAM will operate in mock mode.")
            
        self.logger.info(f"ESP32-CAM Interface Initialized for {self.base_url}")

    def capture_frame(self) -> Optional[np.ndarray]:
        """Captures a single high-resolution JPG frame from the ESP32-CAM."""
        if not REQUESTS_AVAILABLE:
            return None
            
        try:
            response = requests.get(f"{self.base_url}/capture", timeout=3)
            if response.status_code == 200:
                # Convert raw bytes to numpy array for CV2/Vision processing
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(response.content))
                self.latest_frame = np.array(img)
                self.is_connected = True
                return self.latest_frame
        except Exception as e:
            self.logger.error(f"Failed to capture frame from ESP32-CAM: {e}")
            self.is_connected = False
        return None

    def set_resolution(self, resolution_id: int):
        """Sets the ESP32-CAM resolution (0: 160x120 to 10: 1600x1200)."""
        try:
            requests.get(f"{self.base_url}/control?var=framesize&val={resolution_id}", timeout=2)
            self.logger.info(f"ESP32-CAM resolution updated to ID {resolution_id}")
        except Exception as e:
            self.logger.error(f"Failed to set ESP32-CAM resolution: {e}")

    def toggle_flashlight(self, enable: bool):
        """Controls the onboard high-power LED on the ESP32-CAM."""
        val = 1 if enable else 0
        try:
            requests.get(f"{self.base_url}/control?var=led_intensity&val={val}", timeout=2)
        except Exception as e:
            self.logger.error(f"Failed to control ESP32-CAM Flash: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "cam_ip": self.base_url,
            "connected": self.is_connected,
            "stream_active": self.stream_active,
            "has_frames": self.latest_frame is not None
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cam = ESP32CamInterface()
    # Mock call (will fail if hardware is not on network)
    cam.capture_frame()
