"""Autoencoders for Extreme Anomaly Detection"""
import numpy as np
from typing import Dict, Any, List

class Autoencoder:
    def __init__(self, input_dim: int, latent_dim: int):
        self.encoder_weights = np.random.randn(latent_dim, input_dim) * 0.1
        self.decoder_weights = np.random.randn(input_dim, latent_dim) * 0.1
        self.encoder_bias = np.zeros(latent_dim)
        self.decoder_bias = np.zeros(input_dim)
        self.threshold = 0.1

    def encode(self, x: np.ndarray) -> np.ndarray:
        return np.tanh(x @ self.encoder_weights.T + self.encoder_bias)

    def decode(self, z: np.ndarray) -> np.ndarray:
        return z @ self.decoder_weights.T + self.decoder_bias

    def reconstruct(self, x: np.ndarray) -> np.ndarray:
        z = self.encode(x)
        return self.decode(z)

    def get_reconstruction_error(self, x: np.ndarray) -> float:
        recon = self.reconstruct(x)
        return np.mean((x - recon)**2)

    def detect_anomaly(self, x: np.ndarray) -> Dict[str, Any]:
        error = self.get_reconstruction_error(x)
        is_anomaly = error > self.threshold
        return {'anomaly': is_anomaly, 'reconstruction_error': error, 'threshold': self.threshold}

class HybridAnomalyDetector:
    def __init__(self, input_dim: int):
        self.autoencoder = Autoencoder(input_dim, input_dim // 2)
        self.svm_weights = np.random.randn(input_dim) * 0.1

    def detect(self, x: np.ndarray) -> Dict[str, Any]:
        ae_result = self.autoencoder.detect_anomaly(x)
        svm_score = np.dot(x, self.svm_weights)
        combined = ae_result['reconstruction_error'] * abs(svm_score)
        return {**ae_result, 'hybrid_score': combined, 'svm_score': svm_score}
