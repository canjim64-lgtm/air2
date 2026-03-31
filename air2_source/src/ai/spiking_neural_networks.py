"""
Spiking Neural Networks (SNNs) for Neuromorphic Low-Latency Processing
"""
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Spike:
    neuron_id: int
    timestamp: float
    layer: int

class SpikingNeuron:
    def __init__(self, threshold: float = 1.0, tau: float = 20.0):
        self.threshold = threshold
        self.tau = tau
        self.voltage = 0.0
        self.last_spike_time = -float('inf')
        self.refractory_period = 2.0

    def update(self, current: float, dt: float) -> bool:
        self.voltage += (-self.voltage / self.tau + current) * dt
        if self.voltage >= self.threshold:
            self.voltage = 0.0
            self.last_spike_time = 0
            return True
        return False

class SpikingNeuralLayer:
    def __init__(self, size: int, threshold: float = 1.0):
        self.neurons = [SpikingNeuron(threshold) for _ in range(size)]
        self.spikes: List[Spike] = []

    def forward(self, inputs: np.ndarray, dt: float, current_time: float) -> np.ndarray:
        output = np.zeros(len(self.neurons))
        for i, neuron in enumerate(self.neurons):
            if inputs[i] > 0:
                if neuron.update(inputs[i], dt):
                    self.spikes.append(Spike(i, current_time, 0))
                    output[i] = 1.0
        return output

class SpikingNeuralNetwork:
    def __init__(self, layer_sizes: List[int]):
        self.layers = [SpikingNeuralLayer(s) for s in layer_sizes]
        self.spike_history: List[List[Spike]] = []

    def forward(self, input_data: np.ndarray, dt: float = 0.1) -> np.ndarray:
        current = input_data
        self.spike_history.append([])
        for layer in self.layers:
            current = layer.forward(current, dt, len(self.spike_history))
        return current

    def detect_event(self, pattern: List[int]) -> bool:
        if len(self.spike_history) < len(pattern): return False
        last_layer = [s.neuron_id for s in self.spike_history[-1]]
        return last_layer == pattern

    def get_spike_rate(self, window: int = 10) -> float:
        if len(self.spike_history) < window: return 0.0
        total = sum(len(layer) for layer in self.spike_history[-window:])
        return total / (window * len(self.layers))

class EventBasedAnomalyDetector:
    def __init__(self):
        self.snn = SpikingNeuralNetwork([32, 16, 8])
        self.baseline_rate = 0.0

    def train_baseline(self, normal_data: List[np.ndarray]):
        rates = []
        for d in normal_data:
            self.snn.forward(d)
            rates.append(self.snn.get_spike_rate())
        self.baseline_rate = np.mean(rates)

    def detect(self, data: np.ndarray) -> Dict[str, Any]:
        self.snn.forward(data)
        rate = self.snn.get_spike_rate()
        anomaly = abs(rate - self.baseline_rate) / (self.baseline_rate + 1e-6) > 0.5
        return {'anomaly': anomaly, 'spike_rate': rate, 'deviation': abs(rate - self.baseline_rate)}
