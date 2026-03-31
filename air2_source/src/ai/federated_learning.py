"""Federated Learning for Swarm Intelligence"""
import numpy as np
from typing import Dict, Any, List

class LocalModel:
    def __init__(self, model_id: str, input_dim: int, output_dim: int):
        self.model_id = model_id
        self.weights = np.random.randn(output_dim, input_dim) * 0.1
        self.bias = np.random.randn(output_dim) * 0.1
        self.local_data = []

    def train_local(self, data: np.ndarray, labels: np.ndarray):
        self.local_data.append((data, labels))

    def get_weights(self) -> Dict[str, np.ndarray]:
        return {'weights': self.weights.copy(), 'bias': self.bias.copy()}

    def update_weights(self, global_weights: Dict[str, np.ndarray]):
        self.weights = global_weights['weights'] * 0.7 + self.weights * 0.3

class FederatedServer:
    def __init__(self):
        self.global_weights = {}
        self.clients: Dict[str, LocalModel] = {}

    def register_client(self, client_id: str, input_dim: int, output_dim: int):
        self.clients[client_id] = LocalModel(client_id, input_dim, output_dim)

    def aggregate(self) -> Dict[str, np.ndarray]:
        if not self.clients: return {}
        client_weights = [c.get_weights() for c in self.clients.values()]
        global_weights = {
            'weights': np.mean([w['weights'] for w in client_weights], axis=0),
            'bias': np.mean([w['bias'] for w in client_weights], axis=0)
        }
        self.global_weights = global_weights
        return global_weights

    def distribute_global_model(self):
        for client in self.clients.values():
            client.update_weights(self.global_weights)
