"""CLIP-based Visual Search for Natural Language Queries"""
import numpy as np
from typing import Dict, Any, List

class CLIPEncoder:
    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim
        self.text_encoder = np.random.randn(embedding_dim, 77) * 0.02
        self.image_encoder = np.random.randn(embedding_dim, 2048) * 0.02

    def encode_text(self, text: str) -> np.ndarray:
        tokens = list(text.encode())[:77]
        while len(tokens) < 77: tokens.append(0)
        return np.tanh(np.array(tokens[:77]) @ self.text_encoder.T)

    def encode_image(self, image_features: np.ndarray) -> np.ndarray:
        return np.tanh(image_features @ self.image_encoder.T)

    def compute_similarity(self, text_emb: np.ndarray, image_emb: np.ndarray) -> float:
        return np.dot(text_emb, image_emb) / (np.linalg.norm(text_emb) * np.linalg.norm(image_emb) + 1e-8)

class CLIPVisualSearch:
    def __init__(self):
        self.encoder = CLIPEncoder()
        self.image_database: Dict[str, np.ndarray] = {}

    def index_image(self, image_id: str, features: np.ndarray):
        self.image_database[image_id] = self.encoder.encode_image(features)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_emb = self.encoder.encode_text(query)
        results = []
        for img_id, emb in self.image_database.items():
            sim = self.encoder.compute_similarity(query_emb, emb)
            results.append({'image_id': img_id, 'score': float(sim)})
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def find_recovery_tarp(self, images: Dict[str, np.ndarray]) -> List[str]:
        return self.search("red recovery tarp", top_k=3)['image_id'] if self.search("red recovery tarp", top_k=3) else []
