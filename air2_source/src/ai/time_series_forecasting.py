"""
AirOne v4.0 - Advanced Time Series Forecasting
Statistical and ML-based time series analysis and forecasting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")

try:
    import statsmodels.api as sm
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller, acf, pacf
    STATSmodels_AVAILABLE = True
except ImportError:
    STATSmodels_AVAILABLE = False
    logger.warning("statsmodels not available")


class TrendType(Enum):
    """Trend types"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STATIONARY = "stationary"
    MIXED = "mixed"


class SeasonalityType(Enum):
    """Seasonality types"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


@dataclass
class TimeSeriesResult:
    """Time series analysis result"""
    forecast: np.ndarray
    confidence_interval_lower: np.ndarray
    confidence_interval_upper: np.ndarray
    model_type: str
    accuracy_metrics: Dict[str, float]
    trend: str
    seasonality: str
    is_stationary: bool


class TimeSeriesAnalyzer:
    """
    Comprehensive time series analysis
    
    Provides statistical tests, decomposition, and feature extraction
    """

    def __init__(self):
        self.data = None
        self.dates = None
        self.frequency = None
        self.is_stationary = None
        self.trend = None
        self.seasonality = None
        self.decomposition = None

    def load_data(self, data: Union[np.ndarray, List[float], pd.Series],
                  dates: Optional[List[datetime]] = None,
                  frequency: str = 'D'):
        """
        Load time series data
        
        Args:
            data: Time series values
            dates: Optional datetime index
            frequency: Data frequency (D=day, H=hour, M=month, etc.)
        """
        if isinstance(data, list):
            data = np.array(data)
        
        self.data = data
        self.frequency = frequency
        
        if dates is None:
            self.dates = pd.date_range(start=datetime.now() - timedelta(len(data)), 
                                       periods=len(data), freq=frequency)
        else:
            self.dates = pd.DatetimeIndex(dates)
        
        logger.info(f"Loaded {len(data)} time series data points")

    def check_stationarity(self, method: str = 'adf') -> Tuple[bool, float]:
        """
        Check if series is stationary
        
        Args:
            method: Test method ('adf' for Augmented Dickey-Fuller)
            
        Returns:
            Tuple of (is_stationary, p_value)
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        if not STATSmodels_AVAILABLE:
            # Simple variance-based check as fallback
            first_half_var = np.var(self.data[:len(self.data)//2])
            second_half_var = np.var(self.data[len(self.data)//2:])
            is_stationary = abs(first_half_var - second_half_var) / max(first_half_var, second_half_var) < 0.5
            return is_stationary, 0.0
        
        # ADF test
        result = adfuller(self.data, autolag='AIC')
        self.is_stationary = result[1] < 0.05
        return self.is_stationary, result[1]

    def detect_trend(self) -> str:
        """Detect trend direction"""
        if self.data is None:
            raise ValueError("No data loaded")
        
        # Use linear regression on indices
        X = np.arange(len(self.data)).reshape(-1, 1)
        y = self.data
        
        model = LinearRegression()
        model.fit(X, y)
        slope = model.coef_[0]
        
        # Calculate trend strength
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        if slope > 0:
            self.trend = TrendType.INCREASING.value
        elif slope < 0:
            self.trend = TrendType.DECREASING.value
        else:
            self.trend = TrendType.STATIONARY.value
        
        return self.trend

    def detect_seasonality(self, max_period: int = None) -> Tuple[str, int]:
        """
        Detect seasonality in the series
        
        Returns:
            Tuple of (seasonality_type, period)
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        if max_period is None:
            max_period = min(len(self.data) // 2, 365)
        
        if not STATSmodels_AVAILABLE:
            # Simple autocorrelation-based detection
            return SeasonalityType.NONE.value, 0
        
        # Use ACF to detect seasonality
        acf_values = acf(self.data, nlags=max_period, fft=True)
        
        # Find significant peaks
        threshold = 2 / np.sqrt(len(self.data))
        significant_lags = np.where(acf_values > threshold)[0]
        
        if len(significant_lags) > 1:
            # Find the first significant peak after lag 0
            for lag in significant_lags[1:]:
                if lag > 1:
                    if lag <= 7:
                        self.seasonality = SeasonalityType.WEEKLY.value
                    elif lag <= 31:
                        self.seasonality = SeasonalityType.MONTHLY.value
                    elif lag <= 366:
                        self.seasonality = SeasonalityType.YEARLY.value
                    else:
                        self.seasonality = SeasonalityType.CUSTOM.value
                    return self.seasonality, lag
        
        self.seasonality = SeasonalityType.NONE.value
        return self.seasonality, 0

    def decompose(self, model: str = 'additive') -> Dict[str, np.ndarray]:
        """
        Decompose time series into components
        
        Args:
            model: 'additive' or 'multiplicative'
            
        Returns:
            Dictionary with trend, seasonal, and residual components
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        if not STATSmodels_AVAILABLE:
            # Simple moving average trend as fallback
            window = min(7, len(self.data) // 4)
            trend = pd.Series(self.data).rolling(window=window, center=True).mean().values
            detrended = self.data - trend
            seasonal = np.zeros_like(self.data)
            residual = detrended
        else:
            # Determine period
            _, period = self.detect_seasonality()
            if period == 0:
                period = min(7, len(self.data) // 4)
            
            result = seasonal_decompose(self.data, model=model, period=period)
            trend = result.trend.values
            seasonal = result.seasonal.values
            residual = result.resid.values
        
        self.decomposition = {
            'trend': trend,
            'seasonal': seasonal,
            'residual': residual
        }
        
        return self.decomposition

    def get_autocorrelation(self, max_lag: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get autocorrelation and partial autocorrelation
        
        Returns:
            Tuple of (acf_values, pacf_values)
        """
        if self.data is None:
            raise ValueError("No data loaded")
        
        if max_lag is None:
            max_lag = min(len(self.data) // 2, 50)
        
        if not STATSmodels_AVAILABLE:
            # Simple autocorrelation calculation
            acf_values = np.correlate(self.data - np.mean(self.data), 
                                      self.data - np.mean(self.data), 
                                      mode='full')
            acf_values = acf_values[len(acf_values)//2:len(acf_values)//2 + max_lag + 1]
            acf_values = acf_values / acf_values[0]
            pacf_values = acf_values.copy()
        else:
            acf_values = acf(self.data, nlags=max_lag, fft=True)
            pacf_values = pacf(self.data, nlags=max_lag)
        
        return acf_values, pacf_values

    def get_statistics(self) -> Dict[str, float]:
        """Get descriptive statistics"""
        if self.data is None:
            return {}
        
        return {
            'mean': float(np.mean(self.data)),
            'std': float(np.std(self.data)),
            'min': float(np.min(self.data)),
            'max': float(np.max(self.data)),
            'median': float(np.median(self.data)),
            'skewness': float(pd.Series(self.data).skew()),
            'kurtosis': float(pd.Series(self.data).kurtosis()),
            'cv': float(np.std(self.data) / np.mean(self.data)) if np.mean(self.data) != 0 else 0
        }


class TimeSeriesForecaster:
    """
    Time series forecasting with multiple models
    """

    def __init__(self):
        self.model = None
        self.model_type = None
        self.is_fitted = False
        self.scaler = StandardScaler()
        self.last_values = None
        self.residuals = None

    def fit(self, data: Union[np.ndarray, List[float]], 
            model_type: str = 'auto',
            seasonal_period: Optional[int] = None) -> Dict[str, Any]:
        """
        Fit forecasting model
        
        Args:
            data: Time series data
            model_type: Model type ('auto', 'arima', 'ets', 'ml', 'naive')
            seasonal_period: Seasonal period (auto-detected if None)
            
        Returns:
            Fitting results
        """
        if isinstance(data, list):
            data = np.array(data)
        
        self.last_values = data[-10:].copy()
        
        # Auto-select model
        if model_type == 'auto':
            model_type = self._select_best_model(data)
        
        self.model_type = model_type
        
        if model_type == 'naive':
            self.model = {'last_value': data[-1]}
            self.is_fitted = True
            return {'model_type': 'naive', 'status': 'fitted'}
        
        elif model_type == 'moving_average':
            window = min(7, len(data) // 4)
            self.model = {'ma_values': data[-window:]}
            self.is_fitted = True
            return {'model_type': 'moving_average', 'window': window}
        
        elif model_type == 'linear':
            X = np.arange(len(data)).reshape(-1, 1)
            self.model = LinearRegression()
            self.model.fit(X, data)
            self.is_fitted = True
            return {'model_type': 'linear', 'slope': self.model.coef_[0]}
        
        elif model_type == 'ml':
            # ML-based forecasting using lag features
            X, y = self._create_lag_features(data, n_lags=5)
            X_train, X_test = X[:-10], X[-10:]
            y_train, y_test = y[:-10], y[-10:]
            
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)
            
            # Calculate residuals
            train_pred = self.model.predict(X_train)
            self.residuals = y_train - train_pred
            
            self.is_fitted = True
            return {
                'model_type': 'ml',
                'training_samples': len(X_train),
                'r2_score': r2_score(y_train, train_pred) if SKLEARN_AVAILABLE else None
            }
        
        elif model_type == 'arima' and STATSmodels_AVAILABLE:
            # Auto-detect order
            order = self._auto_arima_order(data)
            self.model = ARIMA(data, order=order)
            self.model = self.model.fit()
            self.is_fitted = True
            return {'model_type': 'arima', 'order': order}
        
        elif model_type == 'ets' and STATSmodels_AVAILABLE:
            self.model = ETSModel(data)
            self.model = self.model.fit()
            self.is_fitted = True
            return {'model_type': 'ets'}
        
        else:
            # Fallback to naive
            self.model = {'last_value': data[-1]}
            self.model_type = 'naive'
            self.is_fitted = True
            return {'model_type': 'naive (fallback)', 'reason': f'{model_type} not available'}

    def _select_best_model(self, data: np.ndarray) -> str:
        """Automatically select best model based on data characteristics"""
        n = len(data)
        
        if n < 10:
            return 'naive'
        
        # Check for trend
        analyzer = TimeSeriesAnalyzer()
        analyzer.load_data(data)
        trend = analyzer.detect_trend()
        
        # Check for seasonality
        seasonality, period = analyzer.detect_seasonality()
        
        if seasonality != 'none' and STATSmodels_AVAILABLE:
            return 'arima'
        
        if trend == 'stationary':
            return 'moving_average'
        
        if n > 50 and SKLEARN_AVAILABLE:
            return 'ml'
        
        return 'linear'

    def _auto_arima_order(self, data: np.ndarray) -> Tuple[int, int, int]:
        """Auto-select ARIMA order"""
        if not STATSmodels_AVAILABLE:
            return (1, 0, 1)
        
        # Use ACF and PACF to determine order
        acf_values = acf(data, nlags=min(20, len(data)//4))
        pacf_values = pacf(data, nlags=min(20, len(data)//4))
        
        # Simple heuristic for order selection
        p = np.argmax(np.abs(pacf_values[1:]) < 0.1) + 1 if len(pacf_values) > 1 else 1
        q = np.argmax(np.abs(acf_values[1:]) < 0.1) + 1 if len(acf_values) > 1 else 1
        
        # Limit orders
        p = min(p, 3)
        q = min(q, 3)
        
        # Check for differencing
        _, pval = adfuller(data)
        d = 0 if pval < 0.05 else 1
        
        return (p, d, q)

    def _create_lag_features(self, data: np.ndarray, n_lags: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Create lag features for ML model"""
        X, y = [], []
        for i in range(n_lags, len(data)):
            X.append(data[i-n_lags:i])
            y.append(data[i])
        return np.array(X), np.array(y)

    def predict(self, steps: int = 10, 
                confidence_level: float = 0.95) -> TimeSeriesResult:
        """
        Generate forecast
        
        Args:
            steps: Number of steps to forecast
            confidence_level: Confidence level for intervals
            
        Returns:
            TimeSeriesResult with forecast and intervals
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        forecast = np.zeros(steps)
        
        if self.model_type == 'naive':
            forecast = np.full(steps, self.model['last_value'])
        
        elif self.model_type == 'moving_average':
            ma_values = self.model['ma_values']
            for i in range(steps):
                forecast[i] = np.mean(ma_values)
                ma_values = np.roll(ma_values, -1)
                ma_values[-1] = forecast[i]
        
        elif self.model_type == 'linear':
            last_idx = len(self.last_values) - 1
            for i in range(steps):
                forecast[i] = self.model.predict([[last_idx + i + 1]])[0]
        
        elif self.model_type == 'ml':
            current_window = self.last_values.copy()
            for i in range(steps):
                pred = self.model.predict(current_window.reshape(1, -1))[0]
                forecast[i] = pred
                current_window = np.roll(current_window, -1)
                current_window[-1] = pred
        
        elif self.model_type == 'arima' and STATSmodels_AVAILABLE:
            forecast = self.model.forecast(steps)
        
        elif self.model_type == 'ets' and STATSmodels_AVAILABLE:
            forecast = self.model.forecast(steps)
        
        else:
            forecast = np.full(steps, self.last_values[-1])
        
        # Calculate confidence intervals
        if self.residuals is not None and len(self.residuals) > 0:
            residual_std = np.std(self.residuals)
        else:
            residual_std = np.std(self.last_values) * 0.1
        
        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
        # Widening intervals for longer horizons
        horizon_factor = np.sqrt(np.arange(1, steps + 1))
        margin = z_score * residual_std * horizon_factor
        
        return TimeSeriesResult(
            forecast=forecast,
            confidence_interval_lower=forecast - margin,
            confidence_interval_upper=forecast + margin,
            model_type=self.model_type,
            accuracy_metrics={},
            trend='unknown',
            seasonality='unknown',
            is_stationary=False
        )

    def forecast_with_evaluation(self, data: np.ndarray, 
                                 steps: int = 10,
                                 train_ratio: float = 0.8) -> Dict[str, Any]:
        """
        Fit and evaluate forecast
        
        Args:
            data: Time series data
            steps: Forecast steps
            train_ratio: Training data ratio
            
        Returns:
            Dictionary with forecast and evaluation metrics
        """
        # Split data
        split_idx = int(len(data) * train_ratio)
        train_data = data[:split_idx]
        test_data = data[split_idx:]
        
        # Fit model
        self.fit(train_data)
        
        # Forecast
        result = self.predict(steps=min(steps, len(test_data)))
        
        # Evaluate
        if len(test_data) >= len(result.forecast):
            mae = mean_absolute_error(test_data[:len(result.forecast)], result.forecast)
            rmse = np.sqrt(mean_squared_error(test_data[:len(result.forecast)], result.forecast))
            r2 = r2_score(test_data[:len(result.forecast)], result.forecast)
        else:
            mae, rmse, r2 = None, None, None
        
        return {
            'forecast': result.forecast,
            'confidence_lower': result.confidence_interval_lower,
            'confidence_upper': result.confidence_interval_upper,
            'model_type': result.model_type,
            'metrics': {
                'mae': mae,
                'rmse': rmse,
                'r2': r2
            }
        }


class EnsembleForecaster:
    """
    Ensemble of multiple forecasting models
    """

    def __init__(self):
        self.forecasters = {}
        self.weights = {}
        self.is_fitted = False

    def fit(self, data: np.ndarray, 
            model_types: List[str] = None) -> Dict[str, Any]:
        """
        Fit ensemble of forecasters
        
        Args:
            data: Training data
            model_types: List of model types to include
        """
        if model_types is None:
            model_types = ['naive', 'moving_average', 'linear', 'ml']
        
        results = {}
        for model_type in model_types:
            try:
                forecaster = TimeSeriesForecaster()
                result = forecaster.fit(data, model_type=model_type)
                self.forecasters[model_type] = forecaster
                results[model_type] = result
            except Exception as e:
                logger.warning(f"Failed to fit {model_type}: {e}")
        
        # Set equal weights
        n_models = len(self.forecasters)
        self.weights = {m: 1.0 / n_models for m in self.forecasters}
        self.is_fitted = True
        
        return results

    def predict(self, steps: int = 10) -> Dict[str, Any]:
        """Ensemble prediction"""
        if not self.is_fitted:
            raise ValueError("Ensemble not fitted")
        
        forecasts = []
        for model_type, forecaster in self.forecasters.items():
            result = forecaster.predict(steps)
            forecasts.append(result.forecast * self.weights[model_type])
        
        ensemble_forecast = np.sum(forecasts, axis=0)
        
        # Calculate uncertainty from model disagreement
        forecast_std = np.std([f.forecast for f in self.forecasters.values()], axis=0)
        
        return {
            'forecast': ensemble_forecast,
            'uncertainty': forecast_std,
            'model_contributions': self.weights,
            'individual_forecasts': {
                m: f.predict(steps).forecast 
                for m, f in self.forecasters.items()
            }
        }


__all__ = [
    'TimeSeriesAnalyzer',
    'TimeSeriesForecaster',
    'EnsembleForecaster',
    'TimeSeriesResult',
    'TrendType',
    'SeasonalityType'
]
