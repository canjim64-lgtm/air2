"""
Multimedia Processing Module
Audio, video, and image processing for telemetry
"""

import numpy as np
from typing import List, Tuple, Optional
import logging


class AudioProcessor:
    """Process audio data"""
    
    def __init__(self, sample_rate: int = 8000):
        self.sample_rate = sample_rate
        
    def encode_audio(self, samples: np.ndarray, 
                   bits_per_sample: int = 16) -> bytes:
        """Encode audio samples"""
        
        # Convert to int16
        if samples.dtype != np.int16:
            samples = (samples * 32767).astype(np.int16)
        
        return samples.tobytes()
    
    def decode_audio(self, data: bytes) -> np.ndarray:
        """Decode audio"""
        
        samples = np.frombuffer(data, dtype=np.int16)
        return samples.astype(np.float32) / 32767.0
    
    def apply_gain(self, samples: np.ndarray, gain_db: float) -> np.ndarray:
        """Apply gain to audio"""
        
        gain = 10 ** (gain_db / 20)
        return samples * gain
    
    def detect_voice_activity(self, samples: np.ndarray,
                            threshold: float = 0.1) -> List[Tuple[int, int]]:
        """Voice activity detection"""
        
        energy = np.abs(samples)
        
        # Find segments above threshold
        in_speech = False
        segments = []
        start = 0
        
        for i, e in enumerate(energy):
            if e > threshold and not in_speech:
                start = i
                in_speech = True
            elif e < threshold and in_speech:
                segments.append((start, i))
                in_speech = False
        
        if in_speech:
            segments.append((start, len(samples)))
        
        return segments


class VideoProcessor:
    """Process video data"""
    
    def __init__(self):
        self.frames = []
        
    def add_frame(self, frame: np.ndarray):
        """Add frame to buffer"""
        
        self.frames.append(frame)
        
        # Keep last 1000 frames
        if len(self.frames) > 1000:
            self.frames.pop(0)
    
    def get_frame(self, index: int) -> Optional[np.ndarray]:
        """Get frame by index"""
        
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None
    
    def detect_motion(self, threshold: float = 30.0) -> List[int]:
        """Detect motion between frames"""
        
        motion_frames = []
        
        for i in range(1, len(self.frames)):
            diff = np.abs(self.frames[i].astype(float) - self.frames[i-1].astype(float))
            mean_diff = np.mean(diff)
            
            if mean_diff > threshold:
                motion_frames.append(i)
        
        return motion_frames
    
    def apply_temporal_filter(self, window: int = 3) -> np.ndarray:
        """Apply temporal filter"""
        
        if len(self.frames) < window:
            return np.zeros(10)
        
        # Average last N frames
        frames = self.frames[-window:]
        return np.mean(frames, axis=0)


class ImageProcessor:
    """Process images"""
    
    def __init__(self):
        pass
    
    def normalize(self, image: np.ndarray) -> np.ndarray:
        """Normalize image"""
        
        img_min = np.min(image)
        img_max = np.max(image)
        
        if img_max - img_min > 0:
            return (image - img_min) / (img_max - img_min)
        
        return image
    
    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Simple edge detection"""
        
        # Sobel filters
        from scipy import ndimage
        sx = ndimage.sobel(image, axis=0)
        sy = ndimage.sobel(image, axis=1)
        
        edges = np.hypot(sx, sy)
        
        return edges
    
    def extract_features(self, image: np.ndarray) -> dict:
        """Extract image features"""
        
        features = {}
        
        # Basic statistics
        features['mean'] = np.mean(image)
        features['std'] = np.std(image)
        features['min'] = np.min(image)
        features['max'] = np.max(image)
        
        # Histogram
        if len(image.shape) == 2:
            hist, _ = np.histogram(image.flatten(), bins=256, range=(0, 1))
            features['histogram'] = hist.tolist()
        
        return features


class MultimediaEncoder:
    """Encode multimedia for transmission"""
    
    def __init__(self):
        self.audio = AudioProcessor()
        self.video = VideoProcessor()
        self.image = ImageProcessor()
    
    def encode_audio_frame(self, samples: np.ndarray) -> bytes:
        """Encode audio frame"""
        return self.audio.encode_audio(samples)
    
    def encode_video_frame(self, frame: np.ndarray,
                          quality: int = 75) -> bytes:
        """Encode video frame (simplified)"""
        
        import zlib
        return zlib.compress(frame.tobytes(), level=quality//10)
    
    def encode_image(self, image: np.ndarray) -> bytes:
        """Encode image"""
        
        normalized = self.image.normalize(image)
        
        import zlib
        return zlib.compress(normalized.tobytes())
    
    def create_multimedia_packet(self, audio: bytes = None,
                              video: bytes = None,
                              image: bytes = None) -> dict:
        """Create multimedia packet"""
        
        packet = {
            'has_audio': audio is not None,
            'has_video': video is not None,
            'has_image': image is not None,
            'audio': audio,
            'video': video,
            'image': image
        }
        
        return packet


# Example usage
if __name__ == "__main__":
    print("Testing Multimedia Processing...")
    
    # Test Audio
    print("\n1. Testing Audio Processor...")
    audio = AudioProcessor()
    samples = np.random.randn(16000) * 0.5
    encoded = audio.encode_audio(samples)
    decoded = audio.decode_audio(encoded)
    print(f"   Encoded: {len(encoded)} bytes")
    
    # Test Video
    print("\n2. Testing Video Processor...")
    video = VideoProcessor()
    for _ in range(10):
        video.add_frame(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
    motion = video.detect_motion()
    print(f"   Frames: {len(video.frames)}, Motion: {len(motion)} frames")
    
    # Test Image
    print("\n3. Testing Image Processor...")
    img_proc = ImageProcessor()
    img = np.random.rand(100, 100, 3)
    features = img_proc.extract_features(img)
    print(f"   Features: {list(features.keys())[:4]}...")
    
    # Test Encoder
    print("\n4. Testing Multimedia Encoder...")
    encoder = MultimediaEncoder()
    packet = encoder.create_multimedia_packet(audio=encoded[:100])
    print(f"   Packet created: audio={packet['has_audio']}")
    
    print("\n✅ Multimedia Processing test completed!")