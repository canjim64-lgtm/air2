"""
Liquid Neural Networks for Fluid Time-Series Processing
"""
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

class LiquidNeuralNetwork:
    def __init__(self, input_size: int, hidden_size: int, output_size: int, time_constant: float = 1.0):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.time_constant = time_constant
        self.W_in = np.random.randn(hidden_size, input_size) * 0.1
        self.W_rec = np.random.randn(hidden_size, hidden_size) * 0.1
        self.W_out = np.random.randn(output_size, hidden_size) * 0.1
        self.time_scales = np.random.exponential(time_constant, hidden_size)

    def forward(self, x: np.ndarray, h_prev: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        if h_prev is None: h_prev = np.zeros(self.hidden_size)
        alpha_adaptive = np.exp(-1.0 / self.time_scales)
        h_new = alpha_adaptive * h_prev + (1 - alpha_adaptive) * np.tanh(self.W_in @ x + self.W_rec @ h_prev)
        y = self.W_out @ h_new
        return y, h_new

    def process_sequence(self, sequence: List[np.ndarray]) -> List[np.ndarray]:
        outputs, h = [], None
        for x in sequence:
            y, h = self.forward(x, h)
            outputs.append(y)
        return outputs

    def adapt_to_sparse_data(self, new_rate: float):
        self.time_scales = np.clip(self.time_scales * (new_rate / 10.0), 0.1, 10.0)

    def predict_trajectory(self, current_state: np.ndarray, steps: int) -> List[np.ndarray]:
        predictions, h, state = [], None, current_state
        for _ in range(steps):
            y, h = self.forward(state, h)
            predictions.append(y)
            state = y[:self.input_size] if y.shape[0] >= self.input_size else state
        return predictions

class LiquidStateSpaceModel:
    def __init__(self, state_dim: int, obs_dim: int):
        self.lnn = LiquidNeuralNetwork(obs_dim, state_dim * 2, state_dim)

    def predict(self, observation: np.ndarray) -> Dict[str, Any]:
        state_pred, _ = self.lnn.forward(observation)
        return {'state': state_pred, 'confidence': 1.0 - np.std(state_pred) / (np.mean(np.abs(state_pred)) + 1e-6)}
