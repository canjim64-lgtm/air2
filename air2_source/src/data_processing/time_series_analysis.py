"""
Time Series Analysis Module
Advanced time series analysis and forecasting for telemetry
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from collections import deque


@dataclass
class TimeSeries:
    """Time series data"""
    values: np.ndarray
    timestamps: np.ndarray
    frequency: float  # Hz


class TimeSeriesAnalyzer:
    """Analyze time series data"""
    
    def __init__(self):
        self.decomposition = {}
    
    def decompose(self, series: np.ndarray, 
                  period: int = 10) -> Dict[str, np.ndarray]:
        """Decompose time series into trend, seasonal, residual"""
        
        n = len(series)
        
        # Trend (moving average)
        trend = np.convolve(series, np.ones(period)/period, mode='same')
        
        # Detrended
        detrended = series - trend
        
        # Seasonal
        n_periods = n // period
        seasonal_pattern = np.mean(detrended.reshape(n_periods, period), axis=0)
        seasonal = np.tile(seasonal_pattern, n_periods + 1)[:n]
        
        # Residual
        residual = series - trend - seasonal
        
        return {
            'trend': trend,
            'seasonal': seasonal,
            'residual': residual
        }
    
    def stationarity_test(self, series: np.ndarray) -> Dict[str, float]:
        """Test for stationarity (simplified ADF test)"""
        
        n = len(series)
        
        # First difference
        diff = np.diff(series)
        
        # Simple test: variance ratio
        var_original = np.var(series)
        var_diff = np.var(diff)
        
        variance_ratio = var_original / (var_diff + 1e-10)
        
        # Autocorrelation at lag 1
        acf_1 = np.corrcoef(series[:-1], series[1:])[0, 1]
        
        return {
            'variance_ratio': variance_ratio,
            'acf_lag1': acf_1 if not np.isnan(acf_1) else 0,
            'is_stationary': abs(acf_1) < 0.5 if not np.isnan(acf_1) else True
        }
    
    def autocorrelation(self, series: np.ndarray, 
                       max_lag: int = 20) -> np.ndarray:
        """Calculate ACF"""
        
        n = len(series)
        mean = np.mean(series)
        
        acf = []
        
        for lag in range(max_lag + 1):
            if lag == 0:
                acf.append(1.0)
            else:
                numerator = np.sum((series[:-lag] - mean) * (series[lag:] - mean))
                denominator = np.sum((series - mean)**2)
                acf.append(numerator / (denominator + 1e-10))
        
        return np.array(acf)
    
    def partial_autocorrelation(self, series: np.ndarray,
                               max_lag: int = 20) -> np.ndarray:
        """Calculate PACF using Durbin-Levinson"""
        
        n = len(series)
        acf = self.autocorrelation(series, max_lag)
        
        pacf = np.zeros(max_lag + 1)
        pacf[0] = 1.0
        
        for k in range(1, max_lag + 1):
            # Solve Yule-Walker
            from numpy.linalg import solve
            
            # Build Toeplitz matrix
            Toep = np.zeros((k, k))
            for i in range(k):
                for j in range(k):
                    Toep[i, j] = acf[abs(i - j)]
            
            try:
                phi = solve(Toep, acf[1:k+1])
                pacf[k] = phi[-1]
            except:
                pacf[k] = 0
        
        return pacf


class TimeSeriesForecaster:
    """Forecast future values"""
    
    def __init__(self):
        self.models = {}
    
    def fit_arima(self, series: np.ndarray, 
                  p: int = 2, d: int = 1, q: int = 2) -> Dict[str, Any]:
        """Fit ARIMA model"""
        
        # Difference if needed
        if d > 0:
            differenced = series.copy()
            for _ in range(d):
                differenced = np.diff(differenced)
        else:
            differenced = series
        
        # AR part (simplified)
        n = len(differenced)
        X = np.zeros((n - p, p))
        y = differenced[p:]
        
        for i in range(n - p):
            X[i] = differenced[i:i+p]
        
        # Solve for AR coefficients
        from numpy.linalg import lstsq
        try:
            ar_coeffs, _, _, _ = lstsq(X, y, rcond=None)
        except:
            ar_coeffs = np.zeros(p)
        
        # MA part (simplified using residuals)
        residuals = y - X @ ar_coeffs
        
        # Calculate MA coefficients from residuals
        ma_coeffs = np.array([np.mean(residuals[i:]*residuals[:-i] if i > 0 else residuals**2) 
                             for i in range(min(q, len(residuals)))])
        
        return {
            'ar_coeffs': ar_coeffs,
            'ma_coeffs': ma_coeffs,
            'differencing_order': d,
            'residuals': residuals
        }
    
    def forecast_arima(self, model: Dict[str, Any], 
                      steps: int = 10) -> np.ndarray:
        """Forecast using ARIMA model"""
        
        ar = model['ar_coeffs']
        d = model['differencing_order']
        
        # Last values for AR
        # Simplified one-step ahead forecasting
        predictions = []
        
        # Work backwards from d differencing
        last_vals = np.zeros(len(ar) + d)
        last_vals[:] = 0.1
        
        for _ in range(steps):
            # AR prediction
            pred = np.dot(ar, last_vals[:len(ar)])
            
            if d > 0:
                # Add back differencing
                pred = last_vals[0] + pred
            
            predictions.append(pred)
            last_vals = np.roll(last_vals, -1)
            last_vals[-1] = pred
        
        return np.array(predictions)
    
    def fit_exponential_smoothing(self, series: np.ndarray,
                                 alpha: float = 0.3) -> Dict[str, float]:
        """Fit exponential smoothing"""
        
        n = len(series)
        
        # Initialize
        level = series[0]
        trend = 0
        
        # Fit
        for t in range(1, n):
            prev_level = level
            level = alpha * series[t] + (1 - alpha) * (level + trend)
            trend = 0.1 * (level - prev_level) + 0.9 * trend
        
        return {
            'level': level,
            'trend': trend,
            'alpha': alpha
        }
    
    def forecast_exponential(self, model: Dict[str, float],
                           steps: int = 10) -> np.ndarray:
        """Forecast using exponential smoothing"""
        
        level = model['level']
        trend = model['trend']
        
        predictions = []
        
        for h in range(1, steps + 1):
            pred = level + h * trend
            predictions.append(pred)
        
        return np.array(predictions)
    
    def fit_prophet(self, series: np.ndarray, 
                   period: int = 24) -> Dict[str, Any]:
        """Simple Prophet-like model"""
        
        n = len(series)
        
        # Trend (linear)
        x = np.arange(n)
        coeffs = np.polyfit(x, series, 1)
        trend = np.polyval(coeffs, x)
        
        # Seasonality
        seasonal = series - trend
        
        # Seasonality components
        seasonal_pattern = np.zeros(period)
        for i in range(period):
            seasonal_pattern[i] = np.mean(seasonal[i::period])
        
        return {
            'trend_coeffs': coeffs,
            'seasonal_pattern': seasonal_pattern,
            'period': period
        }
    
    def forecast_prophet(self, model: Dict[str, Any],
                       steps: int) -> np.ndarray:
        """Forecast using Prophet model"""
        
        coeffs = model['trend_coeffs']
        seasonal = model['seasonal_pattern']
        period = model['period']
        
        n = len(coeffs) - 1
        intercept = coeffs[-1] if n > 0 else coeffs[0]
        slope = coeffs[0] if n == 1 else coeffs[0]
        
        predictions = []
        
        for h in range(steps):
            # Trend
            future_x = 1000 + h  # arbitrary base
            trend = np.polyval(coeffs, future_x)
            
            # Seasonal
            season = seasonal[h % period]
            
            predictions.append(trend + season)
        
        return np.array(predictions)


class SeasonalDetector:
    """Detect seasonal patterns"""
    
    def __init__(self):
        self.detected_periods = []
    
    def detect_period(self, series: np.ndarray, 
                     min_period: int = 2, max_period: int = 100) -> int:
        """Detect dominant period using FFT"""
        
        n = len(series)
        
        # FFT
        fft_vals = np.fft.fft(series - np.mean(series))
        power = np.abs(fft_vals)**2
        
        # Frequencies
        freqs = np.fft.fftfreq(n)
        
        # Find peaks
        positive_freqs = freqs[:n//2]
        positive_power = power[:n//2]
        
        # Ignore zero frequency
        positive_power[0] = 0
        
        # Find dominant frequency
        peak_idx = np.argmax(positive_power)
        peak_freq = positive_freqs[peak_idx]
        
        if peak_freq > 0:
            period = int(1 / peak_freq)
            if min_period <= period <= max_period:
                self.detected_periods.append(period)
                return period
        
        return 1
    
    def find_periods(self, series: np.ndarray) -> List[int]:
        """Find multiple seasonal periods"""
        
        periods = []
        
        # Check various periods
        for period in [2, 3, 5, 7, 10, 12, 24, 48, 168]:
            if period < len(series) // 2:
                # Calculate correlation with seasonal pattern
                seasonal_corr = self._seasonal_correlation(series, period)
                if seasonal_corr > 0.5:
                    periods.append(period)
        
        return periods
    
    def _seasonal_correlation(self, series: np.ndarray, period: int) -> float:
        """Calculate seasonal correlation"""
        
        n = len(series)
        n_periods = n // period
        
        if n_periods < 2:
            return 0
        
        # Extract seasonal pattern
        pattern = np.zeros(period)
        for i in range(period):
            pattern[i] = np.mean(series[i::period])
        
        # Reconstruct and correlate
        reconstructed = np.zeros(n)
        for i in range(n):
            reconstructed[i] = pattern[i % period]
        
        return np.corrcoef(series, reconstructed)[0, 1]


class ChangePointDetector:
    """Detect change points in time series"""
    
    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold
    
    def detect_cusum(self, series: np.ndarray) -> List[int]:
        """Detect using CUSUM"""
        
        mean = np.mean(series)
        std = np.std(series)
        
        # Normalize
        normalized = (series - mean) / (std + 1e-10)
        
        # CUSUM
        cusum_pos = np.zeros(len(series))
        cusum_neg = np.zeros(len(series))
        
        change_points = []
        
        for i in range(1, len(series)):
            cusum_pos[i] = max(0, cusum_pos[i-1] + normalized[i] - 0.5)
            cusum_neg[i] = max(0, cusum_neg[i-1] - normalized[i] - 0.5)
            
            if cusum_pos[i] > self.threshold or cusum_neg[i] > self.threshold:
                change_points.append(i)
                cusum_pos[i] = 0
                cusum_neg[i] = 0
        
        return change_points
    
    def detect_binary_segmentation(self, series: np.ndarray) -> List[int]:
        """Binary segmentation for change point detection"""
        
        def segmentation_cost(seg):
            return len(seg) * np.var(seg) if len(seg) > 1 else 0
        
        n = len(series)
        change_points = []
        
        # Find optimal split
        best_cost = np.inf
        best_split = -1
        
        for i in range(1, n):
            left = series[:i]
            right = series[i:]
            
            cost = segmentation_cost(left) + segmentation_cost(right)
            
            if cost < best_cost:
                best_cost = cost
                best_split = i
        
        if best_split > 0:
            change_points.append(best_split)
        
        return change_points
    
    def detect_window_based(self, series: np.ndarray,
                          window_size: int = 50) -> List[int]:
        """Window-based change detection"""
        
        change_points = []
        
        for i in range(window_size, len(series) - window_size):
            left = series[i-window_size:i]
            right = series[i:i+window_size]
            
            # Statistical test
            mean_diff = abs(np.mean(left) - np.mean(right))
            pooled_std = np.sqrt((np.var(left) + np.var(right)) / 2)
            
            if pooled_std > 0:
                z_score = mean_diff / pooled_std
                
                if z_score > self.threshold:
                    change_points.append(i)
        
        return change_points


class TimeSeriesFeatureExtractor:
    """Extract features from time series"""
    
    def extract_all(self, series: np.ndarray) -> Dict[str, float]:
        """Extract all features"""
        
        features = {}
        
        # Statistical
        features['mean'] = np.mean(series)
        features['std'] = np.std(series)
        features['min'] = np.min(series)
        features['max'] = np.max(series)
        features['range'] = features['max'] - features['min']
        features['median'] = np.median(series)
        
        # Shape
        features['skewness'] = self._skewness(series)
        features['kurtosis'] = self._kurtosis(series)
        
        # Temporal
        features['first_diff_mean'] = np.mean(np.diff(series))
        features['first_diff_std'] = np.std(np.diff(series))
        
        # Trend
        x = np.arange(len(series))
        slope, _ = np.polyfit(x, series, 1)
        features['trend_slope'] = slope
        
        # Autocorrelation
        acf = TimeSeriesAnalyzer().autocorrelation(series, 5)
        features['acf_1'] = acf[1]
        features['acf_2'] = acf[2]
        
        return features
    
    def _skewness(self, series: np.ndarray) -> float:
        """Calculate skewness"""
        mean = np.mean(series)
        std = np.std(series)
        
        if std == 0:
            return 0
        
        return np.mean(((series - mean) / std) ** 3)
    
    def _kurtosis(self, series: np.ndarray) -> float:
        """Calculate kurtosis"""
        mean = np.mean(series)
        std = np.std(series)
        
        if std == 0:
            return 0
        
        return np.mean(((series - mean) / std) ** 4)


# Example usage
if __name__ == "__main__":
    print("Testing Time Series Analysis...")
    
    # Generate sample data
    np.random.seed(42)
    t = np.arange(200)
    trend = 0.5 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 24)
    noise = np.random.randn(200) * 2
    series = trend + seasonal + noise
    
    # Test Analyzer
    print("\n1. Testing Time Series Analyzer...")
    analyzer = TimeSeriesAnalyzer()
    decomp = analyzer.decompose(series, period=24)
    print(f"   Decomposition: trend, seasonal, residual")
    
    stationary = analyzer.stationarity_test(series)
    print(f"   Stationary: {stationary['is_stationary']}")
    
    # Test Forecaster
    print("\n2. Testing Time Series Forecaster...")
    forecaster = TimeSeriesForecaster()
    
    model = forecaster.fit_exponential_smoothing(series)
    forecast = forecaster.forecast_exponential(model, steps=10)
    print(f"   Exponential smoothing forecast: {forecast[:3]}...")
    
    # Test Seasonal Detector
    print("\n3. Testing Seasonal Detector...")
    detector = SeasonalDetector()
    period = detector.detect_period(series)
    print(f"   Detected period: {period}")
    
    # Test Change Point Detector
    print("\n4. Testing Change Point Detector...")
    cp_detector = ChangePointDetector()
    cps = cp_detector.detect_cusum(series)
    print(f"   Change points: {len(cps)}")
    
    # Test Feature Extractor
    print("\n5. Testing Feature Extractor...")
    extractor = TimeSeriesFeatureExtractor()
    features = extractor.extract_all(series)
    print(f"   Features: {list(features.keys())[:5]}...")
    
    print("\n✅ Time Series Analysis test completed!")