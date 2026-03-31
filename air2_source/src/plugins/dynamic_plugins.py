"""
Plugin Module
Plugin system for extensibility
"""

from typing import Dict, Callable, Any


class Plugin:
    """Plugin base class"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = False
    
    def on_enable(self):
        """Enable plugin"""
        self.enabled = True
    
    def on_disable(self):
        """Disable plugin"""
        self.enabled = False
    
    def process(self, data: Any) -> Any:
        """Process data"""
        return data


class PluginManager:
    """Manage plugins"""
    
    def __init__(self):
        self.plugins = {}
    
    def register(self, plugin: Plugin):
        """Register plugin"""
        self.plugins[plugin.name] = plugin
    
    def enable(self, name: str):
        """Enable plugin"""
        if name in self.plugins:
            self.plugins[name].on_enable()
    
    def disable(self, name: str):
        """Disable plugin"""
        if name in self.plugins:
            self.plugins[name].on_disable()
    
    def process(self, name: str, data: Any) -> Any:
        """Process with plugin"""
        if name in self.plugins:
            return self.plugins[name].process(data)
        return data


# Example
if __name__ == "__main__":
    pm = PluginManager()
    print("Plugin system ready")