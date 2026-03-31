"""Meta-Learning (MAML) for Rapid Adaptation"""
import numpy as np
from typing import Dict, Any, List

class MAML:
    def __init__(self, input_dim: int, output_dim: int, inner_lr: float = 0.01, outer_lr: float = 0.001):
        self.inner_lr = inner_lr
        self.outer_lr = outer_lr
        self.weights = np.random.randn(output_dim, input_dim) * 0.1
        self.bias = np.random.randn(output_dim) * 0.1

    def inner_update(self, support_data: np.ndarray, support_labels: np.ndarray):
        pred = support_data @ self.weights.T + self.bias
        loss = np.mean((pred - support_labels)**2)
        grad_w = support_data.T @ (pred - support_labels) / len(support_data)
        grad_b = np.mean(pred - support_labels)
        self.weights -= self.inner_lr * grad_w
        self.bias -= self.inner_lr * grad_b

    def outer_update(self, query_data: np.ndarray, query_labels: np.ndarray):
        pred = query_data @ self.weights.T + self.bias
        loss = np.mean((pred - query_labels)**2)
        return loss

    def adapt(self, support: Dict[str, np.ndarray], query: Dict[str, np.ndarray]) -> float:
        for _ in range(5): self.inner_update(support['data'], support['labels'])
        return self.outer_update(query['data'], query['labels'])

class MetaLearner:
    def __init__(self):
        self.maml = MAML(input_dim=10, output_dim=1)

    def fast_adapt(self, new_environment_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        support = {'data': new_environment_data.get('support_x'), 'labels': new_environment_data.get('support_y')}
        query = {'data': new_environment_data.get('query_x'), 'labels': new_environment_data.get('query_y')}
        loss = self.maml.adapt(support, query)
        return {'adaptation_loss': loss, 'adapted': True}
