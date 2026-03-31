"""Bayesian Neural Networks for Uncertainty Quantification"""
import numpy as np
from typing import Dict, Any, List, Tuple

class BayesianLayer:
    def __init__(self, input_size: int, output_size: int, prior_std: float = 1.0):
        self.input_size, self.output_size = input_size, output_size
        self.w_mu = np.random.randn(output_size, input_size) * 0.1
        self.w_rho = np.random.randn(output_size, input_size) * 0.01
        self.b_mu = np.random.randn(output_size) * 0.1
        self.b_rho = np.random.randn(output_size) * 0.01

    def sample_weights(self):
        w_sigma = np.log1p(np.exp(self.w_rho))
        b_sigma = np.log1p(np.exp(self.b_rho))
        return (self.w_mu + w_sigma * np.random.randn(*self.w_mu.shape),
                self.b_mu + b_sigma * np.random.randn(*self.b_mu.shape))

    def forward(self, x: np.ndarray) -> np.ndarray:
        w, b = self.sample_weights()
        return x @ w.T + b

class BayesianNeuralNetwork:
    def __init__(self, layer_sizes: List[int]):
        self.layers = [BayesianLayer(layer_sizes[i], layer_sizes[i+1]) for i in range(len(layer_sizes)-1)]

    def forward(self, x: np.ndarray, n_samples: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        predictions, uncertainties = [], []
        for _ in range(n_samples):
            h = x
            for layer in self.layers:
                h = layer.forward(h)
            predictions.append(h)
        pred_mean = np.mean(predictions, axis=0)
        pred_std = np.std(predictions, axis=0)
        return pred_mean, pred_std

    def predict_with_uncertainty(self, x: np.ndarray) -> Dict[str, Any]:
        mean, std = self.forward(x)
        confidence = 1.0 - np.clip(std, 0, 1)
        return {'prediction': mean, 'uncertainty': std, 'confidence': confidence}

class UncertaintyAwarePredictor:
    def __init__(self, input_dim: int, output_dim: int):
        self.bnn = BayesianNeuralNetwork([input_dim, 64, 32, output_dim])
        self.threshold = 0.4

    def predict(self, data: np.ndarray) -> Dict[str, Any]:
        result = self.bnn.predict_with_uncertainty(data)
        if result['confidence'] < self.threshold:
            result['warning'] = 'Low confidence - revert to raw sensor reading'
        return result
