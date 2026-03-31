"""
AirOne Professional v4.0 - Plugin System
Extensible plugin architecture
"""
# -*- coding: utf-8 -*-

import os
import json
import importlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class Plugin:
    """Base plugin class"""
    
    name = "Base Plugin"
    version = "1.0.0"
    description = "Base plugin class"
    author = "Unknown"
    
    def __init__(self):
        self.enabled = False
        self.config: Dict[str, Any] = {}
    
    def initialize(self):
        """Initialize plugin"""
        self.enabled = True
        logger.info(f"Plugin '{self.name}' initialized")
    
    def shutdown(self):
        """Shutdown plugin"""
        self.enabled = False
        logger.info(f"Plugin '{self.name}' shutdown")
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'enabled': self.enabled
        }


class PluginManager:
    """Manage plugins"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(exist_ok=True)
        
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        
        # Load plugin registry
        self.registry_file = self.plugin_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load plugin registry"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'plugins': {}}
    
    def _save_registry(self):
        """Save plugin registry"""
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def register_plugin(self, plugin_class) -> bool:
        """Register a plugin class"""
        try:
            plugin = plugin_class()
            plugin_id = plugin.name.lower().replace(' ', '_')
            
            self.plugins[plugin_id] = plugin
            self.registry['plugins'][plugin_id] = {
                'name': plugin.name,
                'version': plugin.version,
                'enabled': True,
                'registered_at': datetime.now().isoformat()
            }
            
            self._save_registry()
            logger.info(f"Plugin registered: {plugin.name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            return False
    
    def load_plugin(self, plugin_path: str) -> bool:
        """Load plugin from file"""
        try:
            plugin_path = Path(plugin_path)
            if not plugin_path.exists():
                return False
            
            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                plugin_path.stem,
                plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for plugin class
            if hasattr(module, 'Plugin'):
                return self.register_plugin(module.Plugin)
            
            logger.warning(f"No Plugin class found in {plugin_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load plugin: {e}")
            return False
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_id]
        plugin.initialize()
        
        if plugin_id in self.registry['plugins']:
            self.registry['plugins'][plugin_id]['enabled'] = True
            self._save_registry()
        
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_id]
        plugin.shutdown()
        
        if plugin_id in self.registry['plugins']:
            self.registry['plugins'][plugin_id]['enabled'] = False
            self._save_registry()
        
        return True
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
        logger.debug(f"Hook registered: {hook_name}")
    
    def trigger_hook(self, hook_name: str, *args, **kwargs):
        """Trigger a hook"""
        if hook_name not in self.hooks:
            return
        
        for callback in self.hooks[hook_name]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook {hook_name} callback failed: {e}")
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get plugin by ID"""
        return self.plugins.get(plugin_id)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all plugins"""
        return [plugin.get_info() for plugin in self.plugins.values()]
    
    def get_active_plugins(self) -> List[Plugin]:
        """Get active plugins"""
        return [p for p in self.plugins.values() if p.enabled]


# Example plugins
class TelemetryPlugin(Plugin):
    """Example telemetry plugin"""
    
    name = "Telemetry Plugin"
    version = "1.0.0"
    description = "Provides telemetry data processing"
    author = "AirOne Team"
    
    def __init__(self):
        super().__init__()
        self.data_buffer = []
    
    def process_telemetry(self, data: Dict[str, Any]):
        """Process telemetry data"""
        if not self.enabled:
            return
        
        self.data_buffer.append({
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
        
        # Keep buffer size manageable
        if len(self.data_buffer) > 1000:
            self.data_buffer = self.data_buffer[-1000:]


class AlertPlugin(Plugin):
    """Example alert plugin"""
    
    name = "Alert Plugin"
    version = "1.0.0"
    description = "Provides alert and notification system"
    author = "AirOne Team"
    
    def __init__(self):
        super().__init__()
        self.alerts = []
    
    def create_alert(self, message: str, level: str = "info"):
        """Create an alert"""
        if not self.enabled:
            return
        
        alert = {
            'id': len(self.alerts),
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        }
        
        self.alerts.append(alert)
        logger.info(f"Alert: {message}")
        return alert


class DataLoggerPlugin(Plugin):
    """Example data logger plugin"""
    
    name = "Data Logger"
    version = "1.0.0"
    description = "Logs data to files"
    author = "AirOne Team"
    
    def __init__(self, log_dir: str = "plugin_logs"):
        super().__init__()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
    
    def log(self, category: str, data: Dict[str, Any]):
        """Log data"""
        if not self.enabled:
            return
        
        log_file = self.log_dir / f"{category}.json"
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')


# Global plugin manager
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def register_plugin(plugin_class) -> bool:
    """Quick plugin registration"""
    return get_plugin_manager().register_plugin(plugin_class)


def trigger_hook(hook_name: str, *args, **kwargs):
    """Quick hook trigger"""
    get_plugin_manager().trigger_hook(hook_name, *args, **kwargs)


if __name__ == "__main__":
    # Test plugin system
    print("="*70)
    print("  AirOne Professional v4.0 - Plugin System Test")
    print("="*70)
    print()
    
    manager = PluginManager()
    
    # Register example plugins
    print("Registering plugins...")
    manager.register_plugin(TelemetryPlugin)
    manager.register_plugin(AlertPlugin)
    manager.register_plugin(DataLoggerPlugin)
    
    print(f"Registered {len(manager.plugins)} plugins")
    print()
    
    # List plugins
    print("Active plugins:")
    for plugin in manager.list_plugins():
        print(f"  - {plugin['name']} v{plugin['version']} ({plugin['description']})")
    
    print()
    
    # Test hooks
    print("Testing hooks...")
    manager.register_hook('startup', lambda: print("  Startup hook triggered"))
    manager.trigger_hook('startup')
    
    print()
    
    # Test plugins
    print("Testing plugin functionality...")
    telemetry_plugin = manager.get_plugin('telemetry_plugin')
    if telemetry_plugin:
        telemetry_plugin.initialize()
        telemetry_plugin.process_telemetry({'altitude': 100, 'velocity': 25})
        print(f"  Telemetry processed: {len(telemetry_plugin.data_buffer)} records")
    
    alert_plugin = manager.get_plugin('alert_plugin')
    if alert_plugin:
        alert_plugin.initialize()
        alert = alert_plugin.create_alert("Test alert", "info")
        print(f"  Alert created: {alert['message']}")
    
    print()
    print("="*70)
    print("  Plugin System Test Complete")
    print("="*70)
