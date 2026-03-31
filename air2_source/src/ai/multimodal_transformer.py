"""Multi-Modal Fusion Transformer for Vision + Telemetry"""
import numpy as np
from typing import List, Dict, Any, Optional

class MultiModalAttention:
    def __init__(self, dim: int, heads: int = 8):
        self.dim, self.heads = dim, heads
        self.head_dim = dim // heads
        self.scale = self.head_dim ** -0.5
        self.q_proj = np.random.randn(dim, dim) * 0.01
        self.k_proj = np.random.randn(dim, dim) * 0.01
        self.v_proj = np.random.randn(dim, dim) * 0.01

    def forward(self, x: np.ndarray) -> np.ndarray:
        B, N, C = x.shape
        q = (x @ self.q_proj).reshape(B, N, self.heads, self.head_dim).transpose(0, 2, 1, 3)
        k = (x @ self.k_proj).reshape(B, N, self.heads, self.head_dim).transpose(0, 2, 1, 3)
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = np.exp(attn - np.max(attn, axis=-1, keepdims=True))
        attn = attn / (attn.sum(axis=-1, keepdims=True) + 1e-8)
        v = (x @ self.v_proj).reshape(B, N, self.heads, self.head_dim).transpose(0, 2, 1, 3)
        return (attn @ v).transpose(0, 2, 1, 3).reshape(B, N, C)

class MultiModalTransformer:
    def __init__(self, vision_dim: int, telemetry_dim: int, hidden_dim: int = 256):
        self.vision_proj = np.random.randn(vision_dim, hidden_dim) * 0.01
        self.telemetry_proj = np.random.randn(telemetry_dim, hidden_dim) * 0.01
        self.cross_attention = MultiModalAttention(hidden_dim)
        self.norm1 = lambda x: x

    def fuse(self, vision_features: np.ndarray, telemetry_features: np.ndarray) -> np.ndarray:
        v = vision_features @ self.vision_proj
        t = telemetry_features @ self.telemetry_proj
        combined = np.concatenate([v, t], axis=1)
        fused = self.cross_attention(combined)
        return self.norm1(fused) + combined

    def detect_spoofing(self, vision_data: np.ndarray, imu_data: np.ndarray) -> Dict[str, Any]:
        fused = self.fuse(vision_data, imu_data)
        discrepancy = abs(np.mean(vision_data[:10]) - np.mean(imu_data[:10]))
        is_spoofed = discrepancy > 0.7
        return {'spoofing_detected': is_spoofing, 'discrepancy': discrepancy}
