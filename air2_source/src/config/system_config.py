"""
Configuration Module
Configuration management
"""

import json
from typing import Dict, Any


class Config:
    """Configuration"""
    
    def __init__(self, config_file: str = None):
        self.config = {}
        if config_file:
            self.load(config_file)
    
    def load(self, filepath: str):
        """Load config"""
        with open(filepath, 'r') as f:
            self.config = json.load(f)
    
    def save(self, filepath: str):
        """Save config"""
        with open(filepath, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value == default:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set config value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value


# Example
if __name__ == "__main__":
    c = Config()
    c.set("database.host", "localhost")
    print(c.get("database.host"))