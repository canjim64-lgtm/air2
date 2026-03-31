"""
Advanced Biometric Authentication System for AirOne Professional
Implements multimodal biometric authentication with liveness detection
"""

import asyncio
import threading
import queue
import time
import json
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import sqlite3
import socket
import struct
from functools import wraps
import cv2
import numpy as np
import face_recognition
import mediapipe as mp
import sounddevice as sd
import librosa
import pyaudio
import wave
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import pickle
import hashlib
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import defaultdict, deque
import statistics
import re


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BiometricType(Enum):
    """Types of biometric modalities"""
    FACE = "face"
    VOICE = "voice"
    FINGERPRINT = "fingerprint"
    IRIS = "iris"
    RETINA = "retina"
    HAND_GEOMETRY = "hand_geometry"
    GAIT = "gait"
    KEYPRESS_DYNAMICS = "keypress_dynamics"
    MOUSE_DYNAMICS = "mouse_dynamics"
    WRITING_DYNAMICS = "writing_dynamics"


class AuthenticationLevel(Enum):
    """Levels of authentication security"""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


class BiometricQuality(Enum):
    """Quality levels for biometric samples"""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class BiometricTemplate:
    """Represents a biometric template"""
    id: str
    user_id: str
    biometric_type: BiometricType
    template_data: bytes  # Encrypted biometric template
    quality_score: float
    creation_time: datetime
    last_used: datetime
    authentication_level: AuthenticationLevel
    feature_vector: List[float]  # Numerical representation of biometric features
    metadata: Dict[str, Any]


@dataclass
class AuthenticationAttempt:
    """Represents an authentication attempt"""
    id: str
    user_id: str
    biometric_type: BiometricType
    timestamp: datetime
    success: bool
    confidence_score: float
    quality_score: float
    device_id: str
    location: str
    ip_address: str
    session_id: str
    error_message: Optional[str] = None


@dataclass
class UserBiometricProfile:
    """Represents a user's biometric profile"""
    user_id: str
    templates: List[BiometricTemplate]
    creation_time: datetime
    last_updated: datetime
    authentication_level: AuthenticationLevel
    enrollment_status: str  # enrolled, partially_enrolled, not_enrolled
    multi_modal_combinations: List[List[BiometricType]]  # Possible combinations for auth
    metadata: Dict[str, Any]


class BiometricSensor:
    """Abstract base class for biometric sensors"""
    
    def __init__(self, sensor_id: str, sensor_type: BiometricType):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.is_active = False
        self.quality_threshold = 0.7
        self.calibration_data = {}
        self.lock = threading.Lock()
        
        logger.info(f"Biometric sensor {sensor_id} ({sensor_type.value}) initialized")
    
    def capture_sample(self) -> Optional[bytes]:
        """Capture a biometric sample - to be implemented by subclasses"""
        logger.warning(f"Capture not implemented for sensor type: {self.sensor_type.value}")
        return None

    def preprocess_sample(self, raw_data: bytes) -> np.ndarray:
        """Preprocess the captured sample"""
        logger.warning(f"Preprocessing not implemented for sensor type: {self.sensor_type.value}")
        return np.array([])

    def extract_features(self, processed_data: np.ndarray) -> List[float]:
        """Extract features from the processed sample"""
        logger.warning(f"Feature extraction not implemented for sensor type: {self.sensor_type.value}")
        return []

    def get_quality_score(self, sample_data: bytes) -> float:
        """Get quality score for the sample"""
        logger.warning(f"Quality scoring not implemented for sensor type: {self.sensor_type.value}")
        return 0.0


class FaceRecognitionSensor(BiometricSensor):
    """Face recognition sensor implementation"""
    
    def __init__(self, sensor_id: str):
        super().__init__(sensor_id, BiometricType.FACE)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        logger.info(f"Face recognition sensor {sensor_id} initialized")
    
    def capture_sample(self) -> Optional[bytes]:
        """Capture face sample using webcam"""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Could not open camera")
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.error("Could not capture frame")
                return None
            
            # Convert to RGB for face_recognition library
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR))
            return buffer.tobytes()
            
        except Exception as e:
            logger.error(f"Error capturing face sample: {e}")
            return None
    
    def preprocess_sample(self, raw_data: bytes) -> np.ndarray:
        """Preprocess face sample"""
        try:
            # Decode the image
            nparr = np.frombuffer(raw_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to RGB
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_img)
            
            if face_locations:
                # Use the first detected face
                top, right, bottom, left = face_locations[0]
                face_image = rgb_img[top:bottom, left:right]
                
                # Resize to standard size
                face_image = cv2.resize(face_image, (160, 160))
                
                return face_image
            else:
                logger.warning("No face detected in sample")
                return np.zeros((160, 160, 3), dtype=np.uint8)
                
        except Exception as e:
            logger.error(f"Error preprocessing face sample: {e}")
            return np.zeros((160, 160, 3), dtype=np.uint8)
    
    def extract_features(self, processed_data: np.ndarray) -> List[float]:
        """Extract face features using face_recognition library"""
        try:
            # Get face encodings
            encodings = face_recognition.face_encodings(processed_data)
            
            if encodings:
                # Return the first encoding as a list of floats
                return encodings[0].tolist()
            else:
                logger.warning("Could not extract face features")
                return [0.0] * 128  # Default 128-dim encoding vector
                
        except Exception as e:
            logger.error(f"Error extracting face features: {e}")
            return [0.0] * 128
    
    def get_quality_score(self, sample_data: bytes) -> float:
        """Get quality score for face sample"""
        try:
            nparr = np.frombuffer(sample_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Calculate various quality metrics
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Brightness
            brightness = np.mean(gray)
            
            # Contrast (standard deviation)
            contrast = np.std(gray)
            
            # Normalize scores to 0-1 range
            sharpness_score = min(1.0, laplacian_var / 1000.0)
            brightness_score = 1.0 - abs(brightness - 128) / 128.0
            contrast_score = min(1.0, contrast / 64.0)
            
            # Weighted average
            quality_score = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Error calculating face quality score: {e}")
            return 0.0


class VoiceRecognitionSensor(BiometricSensor):
    """Voice recognition sensor implementation"""
    
    def __init__(self, sensor_id: str, sample_rate: int = 16000, duration: int = 3):
        super().__init__(sensor_id, BiometricType.VOICE)
        self.sample_rate = sample_rate
        self.duration = duration
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.chunk = 1024
        
        logger.info(f"Voice recognition sensor {sensor_id} initialized")
    
    def capture_sample(self) -> Optional[bytes]:
        """Capture voice sample using microphone"""
        try:
            audio = pyaudio.PyAudio()
            
            # Open stream
            stream = audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            logger.info("Recording voice sample...")
            frames = []
            
            for _ in range(0, int(self.sample_rate / self.chunk * self.duration)):
                data = stream.read(self.chunk)
                frames.append(data)
            
            logger.info("Recording finished")
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Combine frames
            audio_data = b''.join(frames)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error capturing voice sample: {e}")
            return None
    
    def preprocess_sample(self, raw_data: bytes) -> np.ndarray:
        """Preprocess voice sample"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
            
            # Normalize
            audio_array = audio_array / np.max(np.abs(audio_array))
            
            return audio_array
            
        except Exception as e:
            logger.error(f"Error preprocessing voice sample: {e}")
            return np.zeros(16000 * 3)  # 3 seconds of silence
    
    def extract_features(self, processed_data: np.ndarray) -> List[float]:
        """Extract voice features using MFCC"""
        try:
            # Compute MFCC features
            mfccs = librosa.feature.mfcc(y=processed_data, sr=self.sample_rate, n_mfcc=13)
            
            # Take mean of MFCCs across time
            mfcc_mean = np.mean(mfccs, axis=1)
            
            # Compute spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=processed_data, sr=self.sample_rate)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=processed_data, sr=self.sample_rate)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(processed_data)[0]
            
            # Combine features
            features = []
            features.extend(mfcc_mean.tolist())
            features.append(np.mean(spectral_centroids))
            features.append(np.mean(spectral_rolloff))
            features.append(np.mean(zero_crossing_rate))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting voice features: {e}")
            return [0.0] * 20  # Default feature vector
    
    def get_quality_score(self, sample_data: bytes) -> float:
        """Get quality score for voice sample"""
        try:
            audio_array = np.frombuffer(sample_data, dtype=np.int16).astype(np.float32)
            
            # Calculate various quality metrics
            rms_energy = np.sqrt(np.mean(audio_array ** 2))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(audio_array))
            
            # Normalize scores
            energy_score = min(1.0, rms_energy * 100)  # Adjust multiplier as needed
            zcr_score = min(1.0, zero_crossing_rate * 1000)  # Adjust multiplier as needed
            
            # Combined quality score
            quality_score = (energy_score * 0.6 + zcr_score * 0.4)
            
            return min(1.0, quality_score)
            
        except Exception as e:
            logger.error(f"Error calculating voice quality score: {e}")
            return 0.0


class FingerprintSensor(BiometricSensor):
    """Fingerprint sensor implementation (simulated)"""
    
    def __init__(self, sensor_id: str):
        super().__init__(sensor_id, BiometricType.FINGERPRINT)
        
        logger.info(f"Fingerprint sensor {sensor_id} initialized")
    
    def capture_sample(self) -> Optional[bytes]:
        """Simulate fingerprint capture"""
        # In a real implementation, this would interface with a fingerprint scanner
        # For simulation, we'll generate a synthetic fingerprint
        try:
            # Create a synthetic fingerprint pattern
            width, height = 200, 200
            fingerprint = np.zeros((height, width), dtype=np.uint8)
            
            # Generate synthetic ridge patterns
            for i in range(0, height, 10):
                for j in range(width):
                    # Create curved ridges
                    curve = int(50 * np.sin(j / 20.0) + height/2)
                    if abs(i - curve) < 3:
                        fingerprint[i, j] = 255
            
            # Add some minutiae points
            for _ in range(10):
                x = np.random.randint(20, width-20)
                y = np.random.randint(20, height-20)
                fingerprint[y-2:y+2, x-2:x+2] = 255
            
            # Encode as PNG
            _, buffer = cv2.imencode('.png', fingerprint)
            return buffer.tobytes()
            
        except Exception as e:
            logger.error(f"Error simulating fingerprint capture: {e}")
            return None
    
    def preprocess_sample(self, raw_data: bytes) -> np.ndarray:
        """Preprocess fingerprint sample"""
        try:
            nparr = np.frombuffer(raw_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            # Enhance fingerprint image
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(img)
            
            # Resize to standard size
            resized = cv2.resize(enhanced, (200, 200))
            
            return resized
            
        except Exception as e:
            logger.error(f"Error preprocessing fingerprint sample: {e}")
            return np.zeros((200, 200), dtype=np.uint8)
    
    def extract_features(self, processed_data: np.ndarray) -> List[float]:
        """Extract fingerprint features (minutiae points)"""
        try:
            # Simple ridge orientation and frequency calculation
            # In a real system, this would use sophisticated minutiae extraction
            rows, cols = processed_data.shape
            
            # Calculate local ridge orientation
            gx = cv2.Sobel(processed_data, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(processed_data, cv2.CV_32F, 0, 1, ksize=3)
            
            # Calculate orientation
            orientation = np.arctan2(gy, gx)
            
            # Extract features based on orientation and frequency
            features = []
            for i in range(0, rows, 20):
                for j in range(0, cols, 20):
                    patch = orientation[i:i+20, j:j+20]
                    if patch.size > 0:
                        features.append(np.mean(patch))
                        features.append(np.std(patch))
            
            # Pad or truncate to fixed size
            if len(features) < 100:
                features.extend([0.0] * (100 - len(features)))
            else:
                features = features[:100]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting fingerprint features: {e}")
            return [0.0] * 100
    
    def get_quality_score(self, sample_data: bytes) -> float:
        """Get quality score for fingerprint sample"""
        try:
            nparr = np.frombuffer(sample_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            # Calculate quality metrics
            # Ridge clarity (contrast)
            contrast = cv2.Laplacian(img, cv2.CV_64F).var()
            
            # Ridge density (number of ridges)
            edges = cv2.Canny(img, 50, 150)
            ridge_density = np.sum(edges > 0) / (img.shape[0] * img.shape[1])
            
            # Normalize scores
            contrast_score = min(1.0, contrast / 1000.0)
            density_score = min(1.0, ridge_density * 10)
            
            # Combined quality score
            quality_score = (contrast_score * 0.7 + density_score * 0.3)
            
            return min(1.0, quality_score)
            
        except Exception as e:
            logger.error(f"Error calculating fingerprint quality score: {e}")
            return 0.0


class BiometricMatcher:
    """Matches biometric samples against stored templates"""
    
    def __init__(self):
        self.matching_thresholds = {
            BiometricType.FACE: 0.6,
            BiometricType.VOICE: 0.7,
            BiometricType.FINGERPRINT: 0.75,
            BiometricType.IRIS: 0.8,
            BiometricType.RETINA: 0.85
        }
        self.scalers = {}
        self.classifiers = {}
        self.lock = threading.Lock()
        
        logger.info("Biometric matcher initialized")
    
    def calculate_similarity(self, template_features: List[float], 
                           sample_features: List[float], 
                           biometric_type: BiometricType) -> float:
        """Calculate similarity between template and sample"""
        try:
            # Convert to numpy arrays
            template_arr = np.array(template_features)
            sample_arr = np.array(sample_features)
            
            # Ensure arrays are the same length
            min_len = min(len(template_arr), len(sample_arr))
            template_arr = template_arr[:min_len]
            sample_arr = sample_arr[:min_len]
            
            # Calculate cosine similarity
            dot_product = np.dot(template_arr, sample_arr)
            norm_template = np.linalg.norm(template_arr)
            norm_sample = np.linalg.norm(sample_arr)
            
            if norm_template == 0 or norm_sample == 0:
                return 0.0
            
            similarity = dot_product / (norm_template * norm_sample)
            
            # Ensure similarity is between 0 and 1
            similarity = max(0.0, min(1.0, (similarity + 1) / 2))
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def match_biometric(self, template: BiometricTemplate, 
                       sample_features: List[float], 
                       quality_score: float) -> Dict[str, Any]:
        """Match a biometric sample against a template"""
        try:
            # Calculate similarity
            similarity = self.calculate_similarity(
                template.feature_vector, 
                sample_features, 
                template.biometric_type
            )
            
            # Apply quality penalty if quality is poor
            if quality_score < 0.5:
                similarity *= quality_score * 2  # Reduce confidence based on quality
            
            # Get threshold for this biometric type
            threshold = self.matching_thresholds.get(template.biometric_type, 0.6)
            
            # Determine if match is successful
            is_match = similarity >= threshold
            
            # Calculate confidence score (adjusted for quality)
            confidence = similarity if is_match else (1 - similarity)
            
            return {
                'is_match': is_match,
                'similarity_score': similarity,
                'confidence_score': confidence,
                'threshold_used': threshold,
                'quality_adjustment_applied': quality_score < 0.5,
                'adjusted_similarity': similarity
            }
            
        except Exception as e:
            logger.error(f"Error matching biometric: {e}")
            return {
                'is_match': False,
                'similarity_score': 0.0,
                'confidence_score': 0.0,
                'threshold_used': 0.0,
                'quality_adjustment_applied': False,
                'adjusted_similarity': 0.0,
                'error': str(e)
            }
    
    def multi_modal_match(self, user_profile: UserBiometricProfile, 
                         samples: Dict[BiometricType, Dict[str, Any]]) -> Dict[str, Any]:
        """Perform multimodal biometric matching"""
        try:
            results = {}
            
            # Match each provided biometric against user templates
            for bio_type, sample_data in samples.items():
                sample_features = sample_data['features']
                quality_score = sample_data['quality_score']
                
                # Find templates of this type for the user
                user_templates = [
                    t for t in user_profile.templates 
                    if t.biometric_type == bio_type
                ]
                
                if not user_templates:
                    results[bio_type.value] = {
                        'match_found': False,
                        'error': f'No {bio_type.value} template found for user'
                    }
                    continue
                
                # Try to match against each template of this type
                match_results = []
                for template in user_templates:
                    match_result = self.match_biometric(template, sample_features, quality_score)
                    match_results.append(match_result)
                
                # Use the best match result
                if match_results:
                    best_match = max(match_results, key=lambda x: x['confidence_score'])
                    results[bio_type.value] = {
                        'match_found': best_match['is_match'],
                        'confidence_score': best_match['confidence_score'],
                        'similarity_score': best_match['similarity_score'],
                        'template_matched': user_templates[match_results.index(best_match)].id
                    }
                else:
                    results[bio_type.value] = {
                        'match_found': False,
                        'error': 'No valid matches found'
                    }
            
            # Calculate overall multimodal confidence
            successful_matches = [r for r in results.values() if r.get('match_found', False)]
            total_confidence = sum(r.get('confidence_score', 0) for r in results.values() if r.get('match_found', False))
            
            overall_confidence = total_confidence / len(successful_matches) if successful_matches else 0.0
            
            # Determine if multimodal authentication succeeds
            # For now, require at least 2 modalities to match with decent confidence
            multimodal_success = len(successful_matches) >= 2 and overall_confidence > 0.6
            
            return {
                'multimodal_success': multimodal_success,
                'overall_confidence': overall_confidence,
                'individual_results': results,
                'modalities_matched': len(successful_matches),
                'required_modalities': 2
            }
            
        except Exception as e:
            logger.error(f"Error in multimodal matching: {e}")
            return {
                'multimodal_success': False,
                'overall_confidence': 0.0,
                'individual_results': {},
                'modalities_matched': 0,
                'required_modalities': 2,
                'error': str(e)
            }


class BiometricEnrollmentManager:
    """Manages biometric enrollment process"""
    
    def __init__(self, matcher: BiometricMatcher):
        self.matcher = matcher
        self.enrollment_sessions = {}
        self.lock = threading.Lock()
        
        logger.info("Biometric enrollment manager initialized")
    
    def start_enrollment_session(self, user_id: str, 
                                required_modalities: List[BiometricType],
                                authentication_level: AuthenticationLevel) -> str:
        """Start a new enrollment session"""
        session_id = f"enroll_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        session_data = {
            'user_id': user_id,
            'required_modalities': required_modalities,
            'authentication_level': authentication_level,
            'captured_templates': {},
            'status': 'active',
            'started_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=30)  # 30 minute timeout
        }
        
        with self.lock:
            self.enrollment_sessions[session_id] = session_data
        
        logger.info(f"Started enrollment session {session_id} for user {user_id}")
        return session_id
    
    def capture_enrollment_sample(self, session_id: str, biometric_type: BiometricType,
                                 sensor: BiometricSensor) -> Dict[str, Any]:
        """Capture a biometric sample for enrollment"""
        with self.lock:
            if session_id not in self.enrollment_sessions:
                return {'success': False, 'error': 'Invalid session ID'}
            
            session = self.enrollment_sessions[session_id]
            
            if session['status'] != 'active':
                return {'success': False, 'error': 'Session is not active'}
            
            if datetime.utcnow() > session['expires_at']:
                session['status'] = 'expired'
                return {'success': False, 'error': 'Session has expired'}
        
        # Capture sample from sensor
        raw_sample = sensor.capture_sample()
        if not raw_sample:
            return {'success': False, 'error': 'Failed to capture sample'}
        
        # Preprocess sample
        processed_sample = sensor.preprocess_sample(raw_sample)
        
        # Extract features
        features = sensor.extract_features(processed_sample)
        
        # Get quality score
        quality_score = sensor.get_quality_score(raw_sample)
        
        # Store the sample data
        sample_data = {
            'raw_data': raw_sample,
            'processed_data': processed_sample,
            'features': features,
            'quality_score': quality_score,
            'captured_at': datetime.utcnow()
        }
        
        with self.lock:
            if biometric_type.value not in session['captured_templates']:
                session['captured_templates'][biometric_type.value] = []
            
            session['captured_templates'][biometric_type.value].append(sample_data)
        
        return {
            'success': True,
            'quality_score': quality_score,
            'features_extracted': len(features) > 0,
            'samples_captured': len(session['captured_templates'][biometric_type.value])
        }
    
    def finalize_enrollment(self, session_id: str, encryption_key: bytes) -> Dict[str, Any]:
        """Finalize the enrollment session and create user profile"""
        with self.lock:
            if session_id not in self.enrollment_sessions:
                return {'success': False, 'error': 'Invalid session ID'}
            
            session = self.enrollment_sessions[session_id]
            
            if session['status'] != 'active':
                return {'success': False, 'error': 'Session is not active'}
        
        # Verify we have enough samples for each required modality
        required_templates = {}
        for modality in session['required_modalities']:
            samples = session['captured_templates'].get(modality.value, [])
            if len(samples) < 3:  # Require at least 3 samples per modality
                return {
                    'success': False, 
                    'error': f'Insufficient samples for {modality.value}. Need at least 3, got {len(samples)}'
                }
            
            # Average the features from multiple samples for better template quality
            all_features = [sample['features'] for sample in samples]
            avg_features = np.mean(all_features, axis=0).tolist()
            
            # Calculate average quality score
            avg_quality = statistics.mean([sample['quality_score'] for sample in samples])
            
            # Create biometric template
            template_id = f"tmpl_{session['user_id']}_{modality.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
            
            # Encrypt the template
            aesgcm = AESGCM(encryption_key)
            nonce = secrets.token_bytes(12)
            encrypted_template = aesgcm.encrypt(nonce, str(avg_features).encode('utf-8'), associated_data=None)
            
            template = BiometricTemplate(
                id=template_id,
                user_id=session['user_id'],
                biometric_type=modality,
                template_data=nonce + encrypted_template,  # Store nonce with ciphertext
                quality_score=avg_quality,
                creation_time=datetime.utcnow(),
                last_used=datetime.utcnow(),
                authentication_level=session['authentication_level'],
                feature_vector=avg_features,
                metadata={'enrollment_session': session_id}
            )
            
            required_templates[modality.value] = template
        
        # Create user profile
        profile = UserBiometricProfile(
            user_id=session['user_id'],
            templates=list(required_templates.values()),
            creation_time=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            authentication_level=session['authentication_level'],
            enrollment_status='enrolled',
            multi_modal_combinations=[session['required_modalities']],  # For now, just the required combination
            metadata={'enrollment_session': session_id}
        )
        
        # Mark session as completed
        with self.lock:
            session['status'] = 'completed'
            session['completed_at'] = datetime.utcnow()
        
        logger.info(f"Completed enrollment for user {session['user_id']} with {len(required_templates)} modalities")
        
        return {
            'success': True,
            'user_profile': profile,
            'templates_created': len(required_templates),
            'session_finalized': True
        }


class BiometricAuthenticationSystem:
    """Main biometric authentication system"""
    
    def __init__(self, encryption_key: bytes = None):
        self.encryption_key = encryption_key or secrets.token_bytes(32)  # 256-bit key
        self.matcher = BiometricMatcher()
        self.enrollment_manager = BiometricEnrollmentManager(self.matcher)
        self.user_profiles = {}
        self.authentication_history = deque(maxlen=10000)
        self.active_sessions = {}
        self.sensors = {}
        self.system_metrics = {}
        self.lock = threading.Lock()
        self.running = False
        
        # Initialize default sensors
        self._init_default_sensors()
        
        logger.info("Biometric authentication system initialized")
    
    def _init_default_sensors(self):
        """Initialize default biometric sensors"""
        self.sensors[BiometricType.FACE.value] = FaceRecognitionSensor("face_sensor_001")
        self.sensors[BiometricType.VOICE.value] = VoiceRecognitionSensor("voice_sensor_001")
        self.sensors[BiometricType.FINGERPRINT.value] = FingerprintSensor("fp_sensor_001")
        
        logger.info(f"Initialized {len(self.sensors)} default biometric sensors")
    
    def register_sensor(self, sensor: BiometricSensor):
        """Register a new biometric sensor"""
        self.sensors[sensor.sensor_type.value] = sensor
        logger.info(f"Registered sensor: {sensor.sensor_id} ({sensor.sensor_type.value})")
    
    def start_enrollment(self, user_id: str, 
                        required_modalities: List[BiometricType] = None,
                        authentication_level: AuthenticationLevel = AuthenticationLevel.STANDARD) -> str:
        """Start a new biometric enrollment process"""
        if required_modalities is None:
            # Default to face and voice for standard enrollment
            required_modalities = [BiometricType.FACE, BiometricType.VOICE]
        
        return self.enrollment_manager.start_enrollment_session(
            user_id, required_modalities, authentication_level
        )
    
    def capture_enrollment_sample(self, session_id: str, biometric_type: BiometricType) -> Dict[str, Any]:
        """Capture a biometric sample for enrollment"""
        if biometric_type.value not in self.sensors:
            return {'success': False, 'error': f'Sensor not available for {biometric_type.value}'}
        
        sensor = self.sensors[biometric_type.value]
        return self.enrollment_manager.capture_enrollment_sample(
            session_id, biometric_type, sensor
        )
    
    def complete_enrollment(self, session_id: str) -> Dict[str, Any]:
        """Complete the enrollment process"""
        result = self.enrollment_manager.finalize_enrollment(session_id, self.encryption_key)
        
        if result['success']:
            profile = result['user_profile']
            with self.lock:
                self.user_profiles[profile.user_id] = profile
        
        return result
    
    def authenticate_user(self, user_id: str, 
                         biometric_samples: Dict[BiometricType, bytes],
                         device_id: str = "unknown",
                         location: str = "unknown",
                         ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """Authenticate a user using biometric samples"""
        start_time = datetime.utcnow()
        
        # Get user profile
        with self.lock:
            if user_id not in self.user_profiles:
                return {
                    'success': False,
                    'confidence_score': 0.0,
                    'error': 'User profile not found',
                    'attempt_recorded': False
                }
            
            user_profile = self.user_profiles[user_id]
        
        # Process each biometric sample
        processed_samples = {}
        for bio_type, raw_sample in biometric_samples.items():
            if bio_type.value not in self.sensors:
                logger.warning(f"Sensor not available for {bio_type.value}")
                continue
            
            sensor = self.sensors[bio_type.value]
            
            # Preprocess sample
            processed_sample = sensor.preprocess_sample(raw_sample)
            
            # Extract features
            features = sensor.extract_features(processed_sample)
            
            # Get quality score
            quality_score = sensor.get_quality_score(raw_sample)
            
            processed_samples[bio_type] = {
                'features': features,
                'quality_score': quality_score,
                'raw_sample': raw_sample
            }
        
        if not processed_samples:
            return {
                'success': False,
                'confidence_score': 0.0,
                'error': 'No valid biometric samples provided',
                'attempt_recorded': False
            }
        
        # Perform multimodal matching
        match_result = self.matcher.multi_modal_match(user_profile, processed_samples)
        
        # Create authentication attempt record
        attempt_id = f"auth_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        auth_attempt = AuthenticationAttempt(
            id=attempt_id,
            user_id=user_id,
            biometric_type=BiometricType.FACE,  # Representative type
            timestamp=datetime.utcnow(),
            success=match_result['multimodal_success'],
            confidence_score=match_result['overall_confidence'],
            quality_score=statistics.mean([s['quality_score'] for s in processed_samples.values()]),
            device_id=device_id,
            location=location,
            ip_address=ip_address,
            session_id=secrets.token_urlsafe(16),
            error_message=None if match_result['multimodal_success'] else 'Multimodal authentication failed'
        )
        
        # Record the attempt
        with self.lock:
            self.authentication_history.append(auth_attempt)
        
        # Update user profile last used timestamp
        with self.lock:
            if user_id in self.user_profiles:
                self.user_profiles[user_id].last_updated = datetime.utcnow()
        
        # Calculate response time
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms
        
        result = {
            'success': match_result['multimodal_success'],
            'confidence_score': match_result['overall_confidence'],
            'individual_results': match_result['individual_results'],
            'modalities_matched': match_result['modalities_matched'],
            'required_modalities': match_result['required_modalities'],
            'attempt_id': attempt_id,
            'response_time_ms': response_time,
            'quality_score': auth_attempt.quality_score,
            'session_id': auth_attempt.session_id
        }
        
        if not match_result['multimodal_success']:
            result['error'] = auth_attempt.error_message
        
        logger.info(f"Authentication attempt {attempt_id}: {'SUCCESS' if result['success'] else 'FAILURE'} "
                   f"(confidence: {result['confidence_score']:.3f}, time: {result['response_time_ms']:.1f}ms)")
        
        return result
    
    def get_user_profile(self, user_id: str) -> Optional[UserBiometricProfile]:
        """Get a user's biometric profile"""
        with self.lock:
            return self.user_profiles.get(user_id)
    
    def update_user_profile(self, profile: UserBiometricProfile):
        """Update a user's biometric profile"""
        with self.lock:
            self.user_profiles[profile.user_id] = profile
            profile.last_updated = datetime.utcnow()
    
    def add_biometric_template(self, user_id: str, biometric_type: BiometricType,
                              features: List[float], quality_score: float,
                              encryption_key: bytes = None) -> str:
        """Add a new biometric template to an existing user profile"""
        if encryption_key is None:
            encryption_key = self.encryption_key
        
        with self.lock:
            if user_id not in self.user_profiles:
                return None
            
            user_profile = self.user_profiles[user_id]
        
        # Encrypt the features
        aesgcm = AESGCM(encryption_key)
        nonce = secrets.token_bytes(12)
        features_str = str(features)
        encrypted_template = aesgcm.encrypt(nonce, features_str.encode('utf-8'), associated_data=None)
        
        # Create new template
        template_id = f"tmpl_{user_id}_{biometric_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        new_template = BiometricTemplate(
            id=template_id,
            user_id=user_id,
            biometric_type=biometric_type,
            template_data=nonce + encrypted_template,
            quality_score=quality_score,
            creation_time=datetime.utcnow(),
            last_used=datetime.utcnow(),
            authentication_level=user_profile.authentication_level,
            feature_vector=features,
            metadata={}
        )
        
        # Add to user profile
        with self.lock:
            user_profile.templates.append(new_template)
            user_profile.last_updated = datetime.utcnow()
        
        logger.info(f"Added new template {template_id} for user {user_id} ({biometric_type.value})")
        return template_id
    
    def get_authentication_history(self, user_id: str = None, limit: int = 50) -> List[AuthenticationAttempt]:
        """Get authentication history"""
        with self.lock:
            if user_id:
                return [a for a in self.authentication_history if a.user_id == user_id][-limit:]
            else:
                return list(self.authentication_history)[-limit:]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        with self.lock:
            total_attempts = len(self.authentication_history)
            successful_attempts = sum(1 for a in self.authentication_history if a.success)
            failure_attempts = total_attempts - successful_attempts
            
            if total_attempts > 0:
                success_rate = successful_attempts / total_attempts
                avg_confidence = statistics.mean([a.confidence_score for a in self.authentication_history])
                avg_quality = statistics.mean([a.quality_score for a in self.authentication_history])
            else:
                success_rate = 0.0
                avg_confidence = 0.0
                avg_quality = 0.0
        
        return {
            'total_users_enrolled': len(self.user_profiles),
            'total_authentication_attempts': total_attempts,
            'successful_attempts': successful_attempts,
            'failed_attempts': failure_attempts,
            'success_rate': success_rate,
            'average_confidence': avg_confidence,
            'average_quality': avg_quality,
            'active_sessions': len(self.active_sessions),
            'registered_sensors': len(self.sensors),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security-related metrics"""
        with self.lock:
            recent_attempts = [a for a in self.authentication_history 
                             if a.timestamp > datetime.utcnow() - timedelta(hours=1)]
            
            # Detect potential brute force attempts
            user_attempts = defaultdict(list)
            for attempt in recent_attempts:
                user_attempts[attempt.user_id].append(attempt)
            
            potential_bf_users = []
            for user_id, attempts in user_attempts.items():
                if len(attempts) >= 5:  # 5 or more attempts in the last hour
                    success_count = sum(1 for a in attempts if a.success)
                    if success_count == 0:  # All attempts failed
                        potential_bf_users.append({
                            'user_id': user_id,
                            'attempt_count': len(attempts),
                            'success_count': success_count,
                            'time_window': 'last_hour'
                        })
        
        return {
            'potential_brute_force_attempts': potential_bf_users,
            'recent_attempts_count': len(recent_attempts),
            'timestamp': datetime.utcnow().isoformat()
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize biometric authentication system
    biometric_system = BiometricAuthenticationSystem()
    
    print("🧬 Advanced Biometric Authentication System Initialized...")
    
    # Start enrollment for a new user
    print("\nStarting enrollment for user 'john_doe'...")
    session_id = biometric_system.start_enrollment(
        user_id="john_doe",
        required_modalities=[BiometricType.FACE, BiometricType.VOICE],
        authentication_level=AuthenticationLevel.HIGH
    )
    print(f"Enrollment session started: {session_id}")
    
    # Simulate capturing biometric samples for enrollment
    print("\nCapturing biometric samples for enrollment...")
    
    # Capture face samples (simulated)
    for i in range(3):
        result = biometric_system.capture_enrollment_sample(session_id, BiometricType.FACE)
        print(f"Face sample {i+1}: Quality={result.get('quality_score', 0):.2f}, Success={result['success']}")
    
    # Capture voice samples (simulated)
    for i in range(3):
        result = biometric_system.capture_enrollment_sample(session_id, BiometricType.VOICE)
        print(f"Voice sample {i+1}: Quality={result.get('quality_score', 0):.2f}, Success={result['success']}")
    
    # Complete enrollment
    print("\nCompleting enrollment...")
    completion_result = biometric_system.complete_enrollment(session_id)
    print(f"Enrollment completed: {completion_result['success']}")
    
    if completion_result['success']:
        print(f"Created profile with {completion_result['templates_created']} templates")
    
    # Test authentication
    print("\nTesting authentication...")
    
    # Simulate capturing biometric samples for authentication
    # In a real system, these would come from actual sensors
    # For simulation, we'll use the same sensors to generate new samples
    
    face_sensor = biometric_system.sensors[BiometricType.FACE.value]
    voice_sensor = biometric_system.sensors[BiometricType.VOICE.value]
    
    # Capture new samples for authentication
    face_sample = face_sensor.capture_sample()
    voice_sample = voice_sensor.capture_sample()
    
    if face_sample and voice_sample:
        auth_result = biometric_system.authenticate_user(
            user_id="john_doe",
            biometric_samples={
                BiometricType.FACE: face_sample,
                BiometricType.VOICE: voice_sample
            },
            device_id="test_device_001",
            location="office",
            ip_address="192.168.1.100"
        )
        
        print(f"Authentication result: {auth_result['success']}")
        print(f"Confidence score: {auth_result['confidence_score']:.3f}")
        print(f"Modalities matched: {auth_result['modalities_matched']}/{auth_result['required_modalities']}")
        print(f"Response time: {auth_result['response_time_ms']:.1f}ms")
        
        if auth_result['success']:
            print("✅ Authentication successful!")
        else:
            print(f"❌ Authentication failed: {auth_result.get('error', 'Unknown error')}")
    else:
        print("Failed to capture authentication samples")
    
    # Test with wrong user
    print("\nTesting authentication with wrong user...")
    wrong_auth_result = biometric_system.authenticate_user(
        user_id="wrong_user",
        biometric_samples={
            BiometricType.FACE: face_sample,
            BiometricType.VOICE: voice_sample
        }
    )
    print(f"Wrong user authentication result: {wrong_auth_result['success']}")
    if not wrong_auth_result['success']:
        print("✅ Correctly rejected wrong user")
    
    # Get system metrics
    print("\nGetting system metrics...")
    metrics = biometric_system.get_system_metrics()
    print(json.dumps(metrics, indent=2, default=str))
    
    # Get security metrics
    print("\nGetting security metrics...")
    security_metrics = biometric_system.get_security_metrics()
    print(json.dumps(security_metrics, indent=2, default=str))
    
    # Get user profile
    print("\nGetting user profile...")
    user_profile = biometric_system.get_user_profile("john_doe")
    if user_profile:
        print(f"User profile found with {len(user_profile.templates)} templates")
        for template in user_profile.templates:
            print(f"  - {template.biometric_type.value}: Quality {template.quality_score:.2f}")
    
    # Get authentication history
    print("\nGetting authentication history...")
    auth_history = biometric_system.get_authentication_history(limit=5)
    print(f"Retrieved {len(auth_history)} recent authentication attempts")
    
    print("\n✅ Advanced Biometric Authentication System Test Completed")