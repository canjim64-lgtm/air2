"""
Predictive Analytics Module
Advanced predictive modeling for telemetry forecasting
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging


class PredictiveModel:
    """Base predictive model"""
    
    def __init__(self):
        self.is_fitted = False
        
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit the model"""
        raise NotImplementedError
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        raise NotImplementedError


class ARIMAModel(PredictiveModel):
    """ARIMA time series model"""
    
    def __init__(self, p: int = 2, d: int = 1, q: int = 2):
        super().__init__()
        self.p = p
        self.d = d
        self.q = q
        self.ar_params = None
        self.ma_params = None
        
    def fit(self, X: np.ndarray, y: np.ndarray = None):
        """Fit ARIMA model"""
        series = X.flatten()
        
        # Difference for stationarity
        diff = series.copy()
        for _ in range(self.d):
            diff = np.diff(diff)
        
        # Fit AR
        n = len(diff)
        if n > self.p:
            X_mat = np.zeros((n - self.p, self.p))
            for i in range(self.p):
                X_mat[:, i] = diff[self.p - 1 - i:-1 - i if i > 0 else None]
            
            y_vec = diff[self.p:]
            self.ar_params = np.linalg.lstsq(X_mat, y_vec, rcond=None)[0]
        
        # Fit MA (simplified)
        self.ma_params = np.zeros(self.q)
        
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray, steps: int = 10) -> np.ndarray:
        """Forecast future values"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        predictions = []
        last_values = list(X.flatten()[-self.p:]) if len(X) >= self.p else [0] * self.p
        
        for _ in range(steps):
            pred = 0
            
            # AR component
            for i, coef in enumerate(self.ar_params):
                if i < len(last_values):
                    pred += coef * last_values[-(i + 1)]
            
            predictions.append(pred)
            last_values.append(pred)
            last_values.pop(0)
        
        return np.array(predictions)


class ProphetModel(PredictiveModel):
    """Prophet-style forecasting model"""
    
    def __init__(self, yearly_seasonality: bool = True, 
                 weekly_seasonality: bool = True, daily_seasonality: bool = False):
        super().__init__()
        self.yearly = yearly_seasonality
        self.weekly = weekly_seasonality
        self.daily = daily_seasonality
        self.trend = None
        self.seasonalities = {}
        
    def fit(self, X: np.ndarray, y: np.ndarray = None):
        """Fit Prophet model"""
        t = np.arange(len(X))
        
        # Linear trend
        coeffs = np.polyfit(t, X.flatten(), 1)
        self.trend = {'slope': coeffs[0], 'intercept': coeffs[1]}
        
        # Yearly seasonality
        if self.yearly:
            yearly = np.sin(2 * np.pi * t / 365) * np.cos(2 * np.pi * t / 365)
            self.seasonalities['yearly'] = yearly
        
        # Weekly seasonality  
        if self.weekly:
            weekly = np.sin(2 * np.pi * t / 7)
            self.seasonalities['weekly'] = weekly
        
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray, steps: int = 10) -> np.ndarray:
        """Forecast"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        start_t = len(X)
        future_t = np.arange(start_t, start_t + steps)
        
        predictions = []
        
        for t in future_t:
            # Trend
            pred = self.trend['slope'] * t + self.trend['intercept']
            
            # Seasonality
            if 'yearly' in self.seasonalities:
                pred += np.sin(2 * np.pi * t / 365) * 0.1
            if 'weekly' in self.seasonalities:
                pred += np.sin(2 * np.pi * t / 7) * 0.05
            
            predictions.append(pred)
        
        return np.array(predictions)


class EnsemblePredictor(PredictiveModel):
    """Ensemble of multiple predictors"""
    
    def __init__(self):
        super().__init__()
        self.models = []
        self.weights = []
        
    def add_model(self, model: PredictiveModel, weight: float = 1.0):
        """Add a model to ensemble"""
        self.models.append(model)
        self.weights.append(weight)
    
    def fit(self, X: np.ndarray, y: np.ndarray = None):
        """Fit all models"""
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]
        
        for model in self.models:
            model.fit(X, y)
        
        self.is_fitted = True
        return self
    
    def predict(self, X: np.ndarray, steps: int = 10) -> np.ndarray:
        """Weighted ensemble prediction"""
        predictions = []
        
        for model in self.models:
            pred = model.predict(X, steps)
            predictions.append(pred)
        
        # Weighted average
        ensemble_pred = np.zeros(steps)
        for pred, weight in zip(predictions, self.weights):
            ensemble_pred += weight * pred
        
        return ensemble_pred


class AnomalyPredictor:
    """Predict future anomalies"""
    
    def __init__(self):
        self.baseline_stats = {}
        
    def fit(self, data: Dict[str, np.ndarray]):
        """Learn baseline statistics"""
        for param, values in data.items():
            self.baseline_stats[param] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'q25': np.percentile(values, 25),
                'q75': np.percentile(values, 75),
                'iqr': np.percentile(values, 75) - np.percentile(values, 25)
            }
    
    def predict_anomaly_probability(self, param: str, value: float) -> float:
        """Predict anomaly probability"""
        if param not in self.baseline_stats:
            return 0.0
        
        stats = self.baseline_stats[param]
        
        # Z-score based probability
        z = abs(value - stats['mean']) / (stats['std'] + 1e-10)
        
        # Convert to probability (higher z = higher probability)
        prob = min(1.0, z / 4.0)
        
        return prob
    
    def predict_next_anomalies(self, data: Dict[str, List[float]], 
                              horizon: int = 10) -> Dict[str, List[float]]:
        """Predict potential anomalies"""
        predictions = {}
        
        for param, values in data.items():
            if param in self.baseline_stats:
                # Use ARIMA-like prediction
                recent = values[-20:] if len(values) >= 20 else values
                trend = np.polyfit(np.arange(len(recent)), recent, 1)[0]
                
                param_preds = []
                last_val = values[-1] if values else 0
                
                for h in range(horizon):
                    pred = last_val + trend * (h + 1)
                    prob = self.predict_anomaly_probability(param, pred)
                    param_preds.append(prob)
                
                predictions[param] = param_preds
        
        return predictions


class FeatureImportanceAnalyzer:
    """Analyze feature importance for predictions"""
    
    def __init__(self):
        self.feature_importance = {}
    
    def analyze(self, X: np.ndarray, y: np.ndarray, 
                feature_names: List[str] = None) -> Dict[str, float]:
        """Analyze feature importance"""
        n_features = X.shape[1] if len(X.shape) > 1 else 1
        
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]
        
        importance = {}
        
        # Correlation-based importance
        for i, name in enumerate(feature_names):
            if len(X.shape) > 1:
                corr = abs(np.corrcoef(X[:, i], y)[0, 1])
                importance[name] = corr if not np.isnan(corr) else 0
            else:
                importance[name] = 1.0
        
        self.feature_importance = importance
        return importance
    
    def get_top_features(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N important features"""
        sorted_features = sorted(
            self.feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return sorted_features[:n]


class ModelEvaluator:
    """Evaluate predictive model performance"""
    
    def __init__(self):
        self.metrics = {}
    
    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate evaluation metrics"""
        
        # MSE
        mse = np.mean((y_true - y_pred) ** 2)
        
        # RMSE
        rmse = np.sqrt(mse)
        
        # MAE
        mae = np.mean(np.abs(y_true - y_pred))
        
        # R-squared
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / (ss_tot + 1e-10))
        
        # MAPE
        mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
        
        # SMAPE
        smape = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-10)) * 100
        
        self.metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mape': mape,
            'smape': smape
        }
        
        return self.metrics


class PredictiveMaintenancePredictor:
    """Predict equipment maintenance needs"""
    
    def __init__(self):
        self.thresholds = {}
        self.usage_patterns = {}
        
    def fit(self, telemetry_data: Dict[str, List[float]]):
        """Learn usage patterns"""
        for param, values in telemetry_data.items():
            if len(values) > 10:
                # Learn degradation trend
                x = np.arange(len(values))
                slope, _ = np.polyfit(x, values, 1)
                
                self.usage_patterns[param] = {
                    'slope': slope,
                    'current': values[-1],
                    'initial': values[0],
                    'degradation_rate': slope / (np.mean(values) + 1e-10)
                }
    
    def predict_remaining_useful_life(self, param: str, 
                                      current_value: float,
                                      failure_threshold: float) -> float:
        """Predict remaining useful life (RUL)"""
        if param not in self.usage_patterns:
            return -1
        
        pattern = self.usage_patterns[param]
        
        if pattern['slope'] <= 0:
            return float('inf')
        
        # Calculate RUL
        remaining = (current_value - failure_threshold) / pattern['slope']
        
        return max(0, remaining)
    
    def predict_maintenance_window(self, params: Dict[str, float],
                                  thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Predict optimal maintenance window"""
        predictions = {}
        
        for param, value in params.items():
            if param in thresholds:
                rul = self.predict_remaining_useful_life(
                    param, value, thresholds[param]
                )
                
                predictions[param] = {
                    'rul': rul,
                    'urgency': 'high' if rul < 10 else 'medium' if rul < 100 else 'low',
                    'recommended_action': self._get_action(rul)
                }
        
        return predictions
    
    def _get_action(self, rul: float) -> str:
        """Get recommended action based on RUL"""
        if rul < 0:
            return "IMMEDIATE MAINTENANCE REQUIRED"
        elif rul < 10:
            return "Schedule maintenance within 10 cycles"
        elif rul < 50:
            return "Plan maintenance soon"
        else:
            return "Continue normal operation"


class TimeSeriesFeatureGenerator:
    """Generate features for time series prediction"""
    
    def __init__(self):
        pass
    
    def generate_lag_features(self, series: np.ndarray, 
                            lags: List[int] = None) -> np.ndarray:
        """Generate lag features"""
        if lags is None:
            lags = [1, 2, 3, 5, 10]
        
        features = []
        
        for lag in lags:
            if lag < len(series):
                lagged = np.roll(series, lag)
                lagged[:lag] = series[0]
                features.append(lagged)
            else:
                features.append(np.zeros_like(series))
        
        return np.column_stack(features) if features else series
    
    def generate_rolling_features(self, series: np.ndarray,
                                 windows: List[int] = None) -> np.ndarray:
        """Generate rolling statistics"""
        if windows is None:
            windows = [3, 5, 10, 20]
        
        features = []
        
        for w in windows:
            # Rolling mean
            rolling_mean = np.convolve(series, np.ones(w)/w, mode='same')
            features.append(rolling_mean)
            
            # Rolling std
            rolling_std = np.zeros_like(series)
            for i in range(len(series)):
                start = max(0, i - w // 2)
                end = min(len(series), i + w // 2)
                rolling_std[i] = np.std(series[start:end])
            features.append(rolling_std)
        
        return np.column_stack(features)
    
    def generate_diff_features(self, series: np.ndarray) -> np.ndarray:
        """Generate difference features"""
        diff1 = np.diff(series, prepend=series[0])
        diff2 = np.diff(diff1, prepend=diff1[0])
        
        return np.column_stack([diff1, diff2])
    
    def generate_all_features(self, series: np.ndarray) -> np.ndarray:
        """Generate all time series features"""
        lag_feats = self.generate_lag_features(series)
        rolling_feats = self.generate_rolling_features(series)
        diff_feats = self.generate_diff_features(series)
        
        return np.column_stack([series.reshape(-1, 1), lag_feats, rolling_feats, diff_feats])


# Example usage
if __name__ == "__main__":
    print("Testing Predictive Analytics...")
    
    # Generate sample data
    np.random.seed(42)
    t = np.arange(100)
    trend = 0.1 * t
    seasonal = 5 * np.sin(2 * np.pi * t / 20)
    noise = np.random.randn(100) * 2
    data = trend + seasonal + noise
    
    # Test ARIMA
    print("\n1. Testing ARIMA Model...")
    arima = ARIMAModel(p=2, d=1, q=2)
    arima.fit(data.reshape(-1, 1))
    predictions = arima.predict(data.reshape(-1, 1), steps=10)
    print(f"   ARIMA predictions: {predictions[:3]}...")
    
    # Test Prophet
    print("\n2. Testing Prophet Model...")
    prophet = ProphetModel()
    prophet.fit(data.reshape(-1, 1))
    predictions = prophet.predict(data.reshape(-1, 1), steps=10)
    print(f"   Prophet predictions: {predictions[:3]}...")
    
    # Test Ensemble
    print("\n3. Testing Ensemble...")
    ensemble = EnsemblePredictor()
    ensemble.add_model(arima, 0.5)
    ensemble.add_model(prophet, 0.5)
    ensemble.fit(data.reshape(-1, 1))
    predictions = ensemble.predict(data.reshape(-1, 1), steps=10)
    print(f"   Ensemble predictions: {predictions[:3]}...")
    
    # Test Anomaly Predictor
    print("\n4. Testing Anomaly Predictor...")
    anomaly_pred = AnomalyPredictor()
    anomaly_pred.fit({'temperature': data})
    prob = anomaly_pred.predict_anomaly_probability('temperature', np.max(data) + 10)
    print(f"   Anomaly probability: {prob:.4f}")
    
    # Test Predictive Maintenance
    print("\n5. Testing Predictive Maintenance...")
    maint = PredictiveMaintenancePredictor()
    maint.fit({'battery': 100 - 0.1 * np.arange(100)})
    rul = maint.predict_remaining_useful_life('battery', 50, 20)
    print(f"   RUL: {rul:.1f} cycles")
    
    # Test Feature Generator
    print("\n6. Testing Feature Generator...")
    generator = TimeSeriesFeatureGenerator()
    features = generator.generate_all_features(data)
    print(f"   Generated features shape: {features.shape}")
    
    print("\n✅ Predictive Analytics test completed!")