from typing import Dict, Any, Optional
import os
import json
import yaml

class ConfigManager:
    """Configuration Manager for API and external tools"""
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self._config_cache = None # Cache for loaded config

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration from file or return defaults. Caches loaded config."""
        if self._config_cache is not None and not force_reload:
            return self._config_cache

        config = {
            'system': {
                'id': 'AIRONE-GS-01',
                'name': 'AirOne Ground Station',
                'version': '3.0.0'
            },
            'network': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            },
            'security': {
                'jwt_secret': 'dev-secret-key-change-in-prod',
                'jwt_expiration_hours': 24,
                'admin_password': 'cyqPmxSpuPQgREFa' # Generated for v4.0 Ultimate
            },
            'simulation': {
                'enabled': True,
                'update_rate_hz': 10
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                    # Deep merge dictionaries
                    self._deep_merge(config, file_config)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")
                
        self._config_cache = config # Cache the loaded config
        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation"""
        config = self.load_config() # Always use the cached version unless forced
        keys = key.split('.')
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any, save_to_file: bool = False):
        """Set a config value by dot notation. Optionally saves to file."""
        config = self.load_config() # Get current (potentially cached) config
        keys = key.split('.')
        target = config
        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                target[k] = value
            else:
                if k not in target or not isinstance(target[k], dict):
                    target[k] = {}
                target = target[k]
        
        self._config_cache = config # Update cache
        if save_to_file:
            self.save_config()

    def save_config(self, path: Optional[str] = None):
        """Save the current configuration to file."""
        save_path = path or self.config_path
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w') as f:
                if save_path.endswith('.yaml') or save_path.endswith('.yml'):
                    yaml.dump(self.load_config(), f, default_flow_style=False, indent=2)
                else:
                    json.dump(self.load_config(), f, indent=2)
            print(f"Configuration saved to {save_path}")
        except Exception as e:
            print(f"Error saving config to {save_path}: {e}")

    def _deep_merge(self, base: Dict, new: Dict):
        """Recursively merges new dictionary into base dictionary."""
        for k, v in new.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v