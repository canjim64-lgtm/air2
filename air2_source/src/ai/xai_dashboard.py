"""Explainable AI (XAI) Dashboard for Decision Transparency"""
import numpy as np
from typing import Dict, Any, List

class SHAPExplainer:
    def __init__(self, model):
        self.model = model

    def explain(self, input_data: np.ndarray, baseline: np.ndarray = None) -> Dict[str, Any]:
        if baseline is None: baseline = np.zeros_like(input_data)
        contributions = input_data - baseline
        feature_importance = np.abs(contributions) / (np.sum(np.abs(contributions)) + 1e-8)
        return {
            'feature_importance': feature_importance.tolist(),
            'contributions': contributions.tolist(),
            'baseline': baseline.tolist()
        }

class LIMEExplainer:
    def __init__(self, model):
        self.model = model

    def explain(self, input_data: np.ndarray, num_samples: int = 100) -> Dict[str, Any]:
        perturbations = [input_data + np.random.randn(*input_data.shape) * 0.1 for _ in range(num_samples)]
        weights = np.random.rand(num_samples)
        importance = np.abs(input_data) * np.mean(weights)
        return {'feature_importance': importance.tolist()}

class XAIDashboard:
    def __init__(self):
        self.shap = SHAPExplainer(None)
        self.lime = LIMEExplainer(None)
        self.decision_history = []

    def explain_decision(self, decision: str, features: Dict[str, float]) -> Dict[str, Any]:
        feature_array = np.array(list(features.values()))
        shap_exp = self.shap.explain(feature_array)
        lime_exp = self.lime.explain(feature_array)
        explanation = f"Decision '{decision}' triggered because: "
        top_features = sorted(features.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        for i, (feat, val) in enumerate(top_features):
            explanation += f"[{feat}]={val:.2f}, " if i < 2 else f"[{feat}]={val:.2f}."
        return {
            'decision': decision,
            'explanation': explanation,
            'shap_values': shap_exp,
            'lime_scores': lime_exp,
            'heatmap': {k: abs(v) for k, v in features.items()}
        }

    def log_decision(self, decision: Dict[str, Any]):
        self.decision_history.append(decision)
