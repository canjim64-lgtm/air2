"""
AirOne v4.0 - Advanced Deep Learning Module
LSTM, CNN, and Transformer models for time series and sequence analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports with fallbacks
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    from tensorflow.keras.layers import (
        LSTM, GRU, Bidirectional, Conv1D, MaxPooling1D, Dense, Dropout,
        BatchNormalization, Attention, MultiHeadAttention, LayerNormalization,
        GlobalAveragePooling1D, Flatten, Input, TimeDistributed,
        Conv2D, MaxPooling2D, AveragePooling2D, Reshape
    )
    from tensorflow.keras.optimizers import Adam, SGD, RMSprop
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
    logger.info("TensorFlow available for deep learning")
except ImportError as e:
    TENSORFLOW_AVAILABLE = False
    logger.warning(f"TensorFlow not available: {e}. Using fallback implementations.")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
    logger.info("PyTorch available for deep learning")
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available")

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


@dataclass
class DLModelConfig:
    """Configuration for deep learning models"""
    sequence_length: int = 50
    forecast_horizon: int = 10
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    dropout_rate: float = 0.2
    l2_regularization: float = 0.001


class LSTMTimeSeriesModel:
    """
    LSTM-based time series forecasting model
    """

    def __init__(self, config: Optional[DLModelConfig] = None):
        self.config = config or DLModelConfig()
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.history = None
        
        if not TENSORFLOW_AVAILABLE:
            logger.warning("LSTM model requires TensorFlow")

    def _create_sequences(self, data: np.ndarray, seq_length: int, 
                          forecast_horizon: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        X, y = [], []
        for i in range(len(data) - seq_length - forecast_horizon + 1):
            X.append(data[i:(i + seq_length)])
            y.append(data[(i + seq_length):(i + seq_length + forecast_horizon)])
        return np.array(X), np.array(y)

    def build_model(self, input_shape: Tuple, forecast_horizon: int, 
                   model_type: str = 'lstm') -> keras.Model:
        """
        Build LSTM/GRU model
        
        Args:
            input_shape: Shape of input data (seq_length, n_features)
            forecast_horizon: Number of steps to predict
            model_type: 'lstm', 'gru', or 'bidirectional'
        """
        inputs = Input(shape=input_shape)
        
        if model_type == 'gru':
            x = GRU(128, return_sequences=True)(inputs)
            x = Dropout(self.config.dropout_rate)(x)
            x = GRU(64, return_sequences=True)(x)
        elif model_type == 'bidirectional':
            x = Bidirectional(LSTM(128, return_sequences=True))(inputs)
            x = Dropout(self.config.dropout_rate)(x)
            x = Bidirectional(LSTM(64, return_sequences=True))(x)
        else:  # lstm
            x = LSTM(128, return_sequences=True)(inputs)
            x = Dropout(self.config.dropout_rate)(x)
            x = LSTM(64, return_sequences=True)(x)
        
        x = Dropout(self.config.dropout_rate)(x)
        x = Dense(32, activation='relu')(x)
        x = Dense(forecast_horizon)(x)
        
        model = keras.Model(inputs=inputs, outputs=x)
        
        optimizer = Adam(learning_rate=self.config.learning_rate)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        return model

    def train(self, data: Union[np.ndarray, List[float]], 
              model_type: str = 'lstm',
              verbose: int = 1) -> Dict[str, Any]:
        """
        Train the LSTM model
        
        Args:
            data: Time series data
            model_type: Type of recurrent model
            verbose: Training verbosity
            
        Returns:
            Training history and metrics
        """
        if not TENSORFLOW_AVAILABLE:
            logger.error("TensorFlow required for LSTM training")
            return {'error': 'TensorFlow not available'}
        
        if isinstance(data, list):
            data = np.array(data)
        
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)
        
        # Scale data
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = self._create_sequences(
            scaled_data, 
            self.config.sequence_length,
            self.config.forecast_horizon
        )
        
        if len(X) < 10:
            logger.error("Insufficient data for training")
            return {'error': 'Insufficient data'}
        
        # Build model
        self.model = self.build_model(
            (self.config.sequence_length, X.shape[2]),
            self.config.forecast_horizon,
            model_type
        )
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=self.config.early_stopping_patience,
            restore_best_weights=True
        )
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6
        )
        
        # Train
        logger.info(f"Training {model_type.upper()} model...")
        self.history = self.model.fit(
            X, y,
            batch_size=self.config.batch_size,
            epochs=self.config.epochs,
            validation_split=self.config.validation_split,
            callbacks=[early_stop, reduce_lr],
            verbose=verbose
        )
        
        self.is_trained = True
        
        # Get metrics
        train_loss = np.min(self.history.history['loss'])
        val_loss = np.min(self.history.history['val_loss'])
        
        logger.info(f"Training complete. Final train loss: {train_loss:.6f}, val loss: {val_loss:.6f}")
        
        return {
            'train_loss': float(train_loss),
            'val_loss': float(val_loss),
            'epochs_trained': len(self.history.history['loss']),
            'model_type': model_type
        }

    def predict(self, input_sequence: np.ndarray, 
                steps: int = 1) -> np.ndarray:
        """
        Make predictions
        
        Args:
            input_sequence: Input sequence (seq_length, n_features)
            steps: Number of prediction steps
            
        Returns:
            Predictions
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")
        
        if len(input_sequence.shape) == 2:
            input_sequence = input_sequence.reshape(1, *input_sequence.shape)
        
        predictions = self.model.predict(input_sequence, verbose=0)
        
        # Inverse transform
        if self.scaler:
            predictions = self.scaler.inverse_transform(predictions)
        
        return predictions

    def forecast(self, data: np.ndarray, steps: int = 10) -> np.ndarray:
        """
        Generate multi-step forecast
        
        Args:
            data: Historical data
            steps: Number of steps to forecast
            
        Returns:
            Forecasted values
        """
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        # Get last sequence
        last_sequence = data[-self.config.sequence_length:]
        
        if self.scaler:
            last_sequence = self.scaler.transform(last_sequence.reshape(-1, 1))
        
        forecasts = []
        current_sequence = last_sequence.copy()
        
        for _ in range(steps):
            # Predict next value
            pred = self.model.predict(
                current_sequence.reshape(1, self.config.sequence_length, -1),
                verbose=0
            )[0, 0]
            
            forecasts.append(pred)
            
            # Update sequence
            current_sequence = np.roll(current_sequence, -1)
            current_sequence[-1] = pred
        
        forecasts = np.array(forecasts).reshape(-1, 1)
        
        if self.scaler:
            forecasts = self.scaler.inverse_transform(forecasts)
        
        return forecasts.flatten()


class CNNTimeSeriesModel:
    """
    1D CNN for time series analysis
    """

    def __init__(self, config: Optional[DLModelConfig] = None):
        self.config = config or DLModelConfig()
        self.model = None
        self.scaler = None
        self.is_trained = False

    def build_model(self, input_shape: Tuple, n_outputs: int) -> keras.Model:
        """Build 1D CNN model"""
        inputs = Input(shape=input_shape)
        
        # Convolutional blocks
        x = Conv1D(128, kernel_size=3, activation='relu', padding='same')(inputs)
        x = BatchNormalization()(x)
        x = MaxPooling1D(pool_size=2)(x)
        x = Dropout(self.config.dropout_rate)(x)
        
        x = Conv1D(64, kernel_size=3, activation='relu', padding='same')(x)
        x = BatchNormalization()(x)
        x = MaxPooling1D(pool_size=2)(x)
        x = Dropout(self.config.dropout_rate)(x)
        
        x = Conv1D(32, kernel_size=3, activation='relu', padding='same')(x)
        x = BatchNormalization()(x)
        x = GlobalAveragePooling1D()(x)
        
        # Dense layers
        x = Dense(64, activation='relu')(x)
        x = Dropout(self.config.dropout_rate)(x)
        x = Dense(32, activation='relu')(x)
        outputs = Dense(n_outputs)(x)
        
        model = keras.Model(inputs=inputs, outputs=outputs)
        
        optimizer = Adam(learning_rate=self.config.learning_rate)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        return model

    def train(self, X: np.ndarray, y: np.ndarray, verbose: int = 1) -> Dict[str, Any]:
        """Train CNN model"""
        if not TENSORFLOW_AVAILABLE:
            return {'error': 'TensorFlow not available'}
        
        # Scale data
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        
        # Build model
        self.model = self.build_model((X.shape[1], X.shape[2]), y.shape[1] if len(y.shape) > 1 else 1)
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=self.config.early_stopping_patience,
            restore_best_weights=True
        )
        
        # Train
        self.model.fit(
            X_scaled, y,
            batch_size=self.config.batch_size,
            epochs=self.config.epochs,
            validation_split=self.config.validation_split,
            callbacks=[early_stop],
            verbose=verbose
        )
        
        self.is_trained = True
        return {'status': 'trained', 'input_shape': X.shape}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        return self.model.predict(X_scaled, verbose=0)


class TransformerModel:
    """
    Transformer-based model for time series forecasting
    """

    def __init__(self, config: Optional[DLModelConfig] = None):
        self.config = config or DLModelConfig()
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        # Transformer parameters
        self.d_model = 64
        self.n_heads = 4
        self.dff = 128
        self.n_layers = 3

    def _positional_encoding(self, position: int, d_model: int) -> np.ndarray:
        """Generate positional encoding"""
        angles = np.arange(0, d_model, 2) / d_model
        angles = 1 / np.power(10000, angles)
        
        pe = np.zeros((position, d_model))
        pe[:, 0::2] = np.sin(np.arange(position)[:, None] * angles)
        pe[:, 1::2] = np.cos(np.arange(position)[:, None] * angles)
        
        return pe[None, :, :]

    def build_transformer(self, input_shape: Tuple, forecast_horizon: int) -> keras.Model:
        """Build transformer model"""
        inputs = Input(shape=input_shape)
        
        # Input projection
        x = Dense(self.d_model)(inputs)
        
        # Add positional encoding
        pos_enc = self._positional_encoding(self.config.sequence_length, self.d_model)
        x = x + pos_enc[:, :self.config.sequence_length, :]
        
        # Transformer blocks
        for _ in range(self.n_layers):
            # Multi-head attention
            attn_output = MultiHeadAttention(
                num_heads=self.n_heads,
                key_dim=self.d_model // self.n_heads
            )(x, x)
            x = LayerNormalization(epsilon=1e-6)(x + attn_output)
            
            # Feed-forward network
            ffn_output = Dense(self.dff, activation='relu')(x)
            ffn_output = Dense(self.d_model)(ffn_output)
            x = LayerNormalization(epsilon=1e-6)(x + ffn_output)
        
        # Global pooling and output
        x = GlobalAveragePooling1D()(x)
        x = Dense(64, activation='relu')(x)
        x = Dropout(self.config.dropout_rate)(x)
        outputs = Dense(forecast_horizon)(x)
        
        model = keras.Model(inputs=inputs, outputs=outputs)
        
        optimizer = Adam(learning_rate=self.config.learning_rate)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        return model

    def train(self, X: np.ndarray, y: np.ndarray, verbose: int = 1) -> Dict[str, Any]:
        """Train transformer model"""
        if not TENSORFLOW_AVAILABLE:
            return {'error': 'TensorFlow not available'}
        
        # Scale data
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        
        # Build model
        self.model = self.build_transformer(
            (self.config.sequence_length, X.shape[2]),
            self.config.forecast_horizon
        )
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=self.config.early_stopping_patience,
            restore_best_weights=True
        )
        
        # Train
        self.model.fit(
            X_scaled, y,
            batch_size=self.config.batch_size,
            epochs=self.config.epochs,
            validation_split=self.config.validation_split,
            callbacks=[early_stop],
            verbose=verbose
        )
        
        self.is_trained = True
        return {'status': 'trained', 'model_type': 'transformer'}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_scaled = self.scaler.transform(X.reshape(-1, X.shape[-1])).reshape(X.shape)
        return self.model.predict(X_scaled, verbose=0)


class DeepLearningEnsemble:
    """
    Ensemble of deep learning models
    """

    def __init__(self, config: Optional[DLModelConfig] = None):
        self.config = config or DLModelConfig()
        self.models = {}
        self.weights = {}
        self.is_trained = False

    def train_ensemble(self, data: np.ndarray, 
                       model_types: List[str] = None) -> Dict[str, Any]:
        """
        Train ensemble of models
        
        Args:
            data: Time series data
            model_types: List of model types to include
        """
        if model_types is None:
            model_types = ['lstm', 'gru', 'cnn', 'transformer']
        
        results = {}
        
        for model_type in model_types:
            logger.info(f"Training {model_type.upper()} model...")
            
            if model_type == 'cnn':
                model = CNNTimeSeriesModel(self.config)
                # Prepare data for CNN
                X, y = self._prepare_cnn_data(data)
                result = model.train(X, y, verbose=0)
            elif model_type == 'transformer':
                model = TransformerModel(self.config)
                X, y = self._prepare_transformer_data(data)
                result = model.train(X, y, verbose=0)
            else:
                model = LSTMTimeSeriesModel(self.config)
                result = model.train(data, model_type=model_type, verbose=0)
            
            self.models[model_type] = model
            results[model_type] = result
        
        # Set equal weights initially
        self.weights = {m: 1.0 / len(model_types) for m in model_types}
        self.is_trained = True
        
        return results

    def _prepare_cnn_data(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for CNN"""
        seq_length = self.config.sequence_length
        forecast_horizon = self.config.forecast_horizon
        
        X, y = [], []
        for i in range(len(data) - seq_length - forecast_horizon + 1):
            X.append(data[i:(i + seq_length)])
            y.append(data[(i + seq_length):(i + seq_length + forecast_horizon)])
        
        return np.array(X), np.array(y)

    def _prepare_transformer_data(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for transformer"""
        return self._prepare_cnn_data(data)

    def predict(self, input_data: np.ndarray) -> np.ndarray:
        """Ensemble prediction"""
        if not self.is_trained:
            raise ValueError("Ensemble not trained")
        
        predictions = []
        for model_type, model in self.models.items():
            try:
                if model_type in ['lstm', 'gru', 'bidirectional']:
                    pred = model.predict(input_data)
                elif model_type == 'cnn':
                    pred = model.predict(input_data)
                elif model_type == 'transformer':
                    pred = model.predict(input_data)
                predictions.append(pred * self.weights[model_type])
            except Exception as e:
                logger.warning(f"{model_type} prediction failed: {e}")
        
        return np.sum(predictions, axis=0)


# Export classes
__all__ = [
    'LSTMTimeSeriesModel',
    'CNNTimeSeriesModel',
    'TransformerModel',
    'DeepLearningEnsemble',
    'DLModelConfig'
]
