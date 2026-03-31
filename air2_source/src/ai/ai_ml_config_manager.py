"""
AirOne v4.0 - AI/ML Configuration Manager
Manages configuration for all AI/ML systems including model settings,
hyperparameters, and runtime options
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AIMLConfigManager:
    """
    Configuration manager for AI/ML systems
    
    Provides centralized configuration for:
    - Model hyperparameters
    - Training settings
    - Inference options
    - Resource allocation
    - Feature engineering settings
    """

    DEFAULT_CONFIG = {
        # General settings
        "general": {
            "enable_caching": True,
            "cache_max_size": 1000,
            "log_level": "INFO",
            "enable_telemetry": True
        },
        
        # Model training settings
        "training": {
            "default_test_size": 0.2,
            "random_state": 42,
            "enable_cross_validation": False,
            "cv_folds": 5,
            "early_stopping": True,
            "max_training_time_seconds": 300
        },
        
        # Default model hyperparameters
        "models": {
            "random_forest": {
                "regression": {
                    "n_estimators": 100,
                    "max_depth": None,
                    "min_samples_split": 2,
                    "min_samples_leaf": 1
                },
                "classification": {
                    "n_estimators": 100,
                    "max_depth": None,
                    "min_samples_split": 2,
                    "min_samples_leaf": 1
                }
            },
            "gradient_boosting": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 5,
                "subsample": 1.0
            },
            "mlp": {
                "hidden_layer_sizes": [64, 32, 16],
                "activation": "relu",
                "solver": "adam",
                "max_iter": 500,
                "learning_rate": "constant",
                "learning_rate_init": 0.001
            },
            "isolation_forest": {
                "n_estimators": 100,
                "contamination": 0.1,
                "max_samples": "auto"
            },
            "kmeans": {
                "n_clusters": 5,
                "init": "k-means++",
                "n_init": 10,
                "max_iter": 300
            }
        },
        
        # Feature engineering settings
        "features": {
            "default_columns": [
                "altitude", "velocity", "temperature", "pressure",
                "battery_level", "latitude", "longitude", "radio_signal_strength"
            ],
            "enable_derived_features": True,
            "enable_polynomial_features": False,
            "polynomial_degree": 2,
            "enable_interaction_features": True,
            "enable_statistical_features": True,
            "enable_lag_features": False,
            "lag_periods": 3
        },
        
        # Preprocessing settings
        "preprocessing": {
            "scaler_type": "standard",  # standard, minmax, robust
            "handle_missing": "fill_zero",  # fill_zero, fill_mean, drop
            "outlier_detection": True,
            "outlier_method": "isolation_forest",
            "outlier_threshold": 0.1
        },
        
        # Deep learning settings
        "deep_learning": {
            "framework": "tensorflow",  # tensorflow, pytorch
            "default_epochs": 100,
            "batch_size": 32,
            "validation_split": 0.2,
            "early_stopping_patience": 10,
            "model_checkpoint": True
        },
        
        # DeepSeek AI settings
        "deepseek": {
            "enabled": True,
            "model_name": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            "max_context_length": 128000,
            "max_new_tokens": 200,
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 50,
            "cache_responses": True
        },
        
        # Optimization settings
        "optimization": {
            "algorithm": "evolutionary",  # evolutionary, swarm, bayesian
            "population_size": 20,
            "generations": 50,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8,
            "elitism_rate": 0.1
        },
        
        # Resource allocation
        "resources": {
            "max_cpu_cores": -1,  # -1 for all available
            "gpu_enabled": True,
            "gpu_memory_fraction": 0.8,
            "memory_limit_gb": 16,
            "enable_parallel_processing": True,
            "n_jobs": -1
        },
        
        # Anomaly detection settings
        "anomaly_detection": {
            "method": "isolation_forest",  # isolation_forest, lof, dbscan
            "contamination": 0.1,
            "threshold_low": -0.15,
            "threshold_medium": -0.05,
            "severity_levels": ["low", "medium", "high", "critical"]
        },
        
        # Time series settings
        "time_series": {
            "enable_forecasting": True,
            "forecast_horizon": 10,
            "seasonality_detection": True,
            "trend_detection": True,
            "decomposition": True
        },
        
        # Reporting settings
        "reporting": {
            "include_visualizations": True,
            "include_statistics": True,
            "include_recommendations": True,
            "output_format": "markdown",  # markdown, html, json
            "auto_generate": True
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to custom config file (JSON)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_path = config_path or "config/ai_ml_config.json"
        self.config_history: List[Dict] = []
        
        # Load custom config if provided
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
        
        logger.info("AI/ML Configuration Manager initialized")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation)
        
        Args:
            key: Configuration key (e.g., "training.random_state")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value
        
        Args:
            key: Configuration key (e.g., "training.random_state")
            value: Value to set
            
        Returns:
            True if successful
        """
        # Save to history
        current_value = self.get(key)
        self.config_history.append({
            'timestamp': datetime.now().isoformat(),
            'key': key,
            'old_value': current_value,
            'new_value': value
        })
        
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.info(f"Configuration updated: {key} = {value}")
        return True

    def get_model_config(self, model_type: str, task_type: str) -> Dict[str, Any]:
        """
        Get model-specific configuration
        
        Args:
            model_type: Type of model (e.g., "random_forest")
            task_type: Task type (e.g., "regression", "classification")
            
        Returns:
            Model configuration dictionary
        """
        models_config = self.config.get("models", {})
        
        if model_type in models_config:
            model_config = models_config[model_type]
            
            # Handle task-specific configs
            if task_type in model_config:
                return model_config[task_type]
            else:
                return model_config
        
        return {}

    def get_feature_columns(self) -> List[str]:
        """Get default feature columns"""
        return self.config.get("features.default_columns", [])

    def get_training_params(self) -> Dict[str, Any]:
        """Get training parameters"""
        return self.config.get("training", {})

    def get_resource_limits(self) -> Dict[str, Any]:
        """Get resource allocation settings"""
        return self.config.get("resources", {})

    def update_model_config(self, model_type: str, task_type: str, 
                           new_params: Dict[str, Any]) -> bool:
        """
        Update model-specific configuration
        
        Args:
            model_type: Type of model
            task_type: Task type
            new_params: New parameters to set
            
        Returns:
            True if successful
        """
        key = f"models.{model_type}"
        
        if task_type in ["regression", "classification"]:
            if model_type in self.config.get("models", {}):
                if task_type not in self.config["models"][model_type]:
                    self.config["models"][model_type][task_type] = {}
                key = f"models.{model_type}.{task_type}"
        
        for param_key, param_value in new_params.items():
            self.set(f"{key}.{param_key}", param_value)
        
        return True

    def save_config(self, filepath: Optional[str] = None) -> bool:
        """
        Save configuration to file
        
        Args:
            filepath: Path to save config (uses default if not provided)
            
        Returns:
            True if successful
        """
        path = filepath or self.config_path
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def load_config(self, filepath: str) -> bool:
        """
        Load configuration from file
        
        Args:
            filepath: Path to config file
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                custom_config = json.load(f)
            
            # Merge with default config
            self._merge_configs(custom_config)
            
            logger.info(f"Configuration loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False

    def _merge_configs(self, custom_config: Dict[str, Any]):
        """Merge custom config with default config"""
        for key, value in custom_config.items():
            if key in self.config and isinstance(value, dict) and isinstance(self.config[key], dict):
                self.config[key].update(value)
            else:
                self.config[key] = value

    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self.DEFAULT_CONFIG.copy()
        logger.info("Configuration reset to defaults")

    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            "config_path": self.config_path,
            "sections": list(self.config.keys()),
            "feature_columns": self.get_feature_columns(),
            "default_model": "random_forest",
            "deepseek_enabled": self.get("deepseek.enabled", False),
            "gpu_enabled": self.get("resources.gpu_enabled", False),
            "cache_enabled": self.get("general.enable_caching", True),
            "history_entries": len(self.config_history)
        }

    def export_config(self, filepath: str, include_history: bool = False) -> bool:
        """
        Export configuration with optional history
        
        Args:
            filepath: Export path
            include_history: Whether to include config history
            
        Returns:
            True if successful
        """
        export_data = {
            "config": self.config,
            "exported_at": datetime.now().isoformat()
        }
        
        if include_history:
            export_data["history"] = self.config_history
        
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Configuration exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return False

    def validate_config(self) -> List[str]:
        """
        Validate current configuration
        
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check training settings
        test_size = self.get("training.default_test_size", 0.2)
        if not 0 < test_size < 1:
            issues.append(f"Invalid test_size: {test_size}. Must be between 0 and 1.")
        
        # Check resource limits
        memory_limit = self.get("resources.memory_limit_gb", 16)
        if memory_limit <= 0:
            issues.append(f"Invalid memory_limit_gb: {memory_limit}. Must be positive.")
        
        # Check DeepSeek settings
        max_tokens = self.get("deepseek.max_new_tokens", 200)
        if max_tokens <= 0:
            issues.append(f"Invalid max_new_tokens: {max_tokens}. Must be positive.")
        
        # Check optimization settings
        population_size = self.get("optimization.population_size", 20)
        if population_size <= 0:
            issues.append(f"Invalid population_size: {population_size}. Must be positive.")
        
        return issues


# Convenience function
def create_ai_ml_config(config_path: Optional[str] = None) -> AIMLConfigManager:
    """Create and return an AI/ML Configuration Manager instance"""
    return AIMLConfigManager(config_path)


# Export
__all__ = ['AIMLConfigManager', 'create_ai_ml_config']
