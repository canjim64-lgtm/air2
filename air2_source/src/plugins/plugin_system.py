#!/usr/bin/env python3
"""
AirOne v4.0 - Plugin System
===========================

Extensible plugin architecture for AirOne
"""

import os
import sys
import json
import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))


class PluginType(Enum):
    """Plugin types"""
    SENSOR = "sensor"
    COMMUNICATION = "communication"
    UI = "ui"
    ANALYSIS = "analysis"
    NOTIFICATION = "notification"
    EXPORT = "export"
    CUSTOM = "custom"


class PluginState(Enum):
    """Plugin states"""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"


@dataclass
class PluginInfo:
    """Plugin metadata"""
    id: str
    name: str
    version: str
    author: str
    description: str
    plugin_type: PluginType
    dependencies: List[str] = None
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config is None:
            self.config = {}


class Plugin:
    """Base plugin class"""
    
    def __init__(self, info: PluginInfo):
        self.info = info
        self.state = PluginState.UNLOADED
        self.logger = logging.getLogger(f"plugin.{info.id}")
        
    def initialize(self) -> bool:
        """Initialize plugin"""
        return True
        
    def activate(self) -> bool:
        """Activate plugin"""
        self.state = PluginState.ACTIVE
        self.logger.info(f"Plugin {self.info.name} activated")
        return True
        
    def deactivate(self):
        """Deactivate plugin"""
        self.state = PluginState.LOADED
        self.logger.info(f"Plugin {self.info.name} deactivated")
        
    def cleanup(self):
        """Cleanup plugin resources"""
        self.state = PluginState.UNLOADED
        self.logger.info(f"Plugin {self.info.name} cleaned up")
        
    def get_config(self) -> Dict[str, Any]:
        """Get plugin configuration"""
        return self.info.config
        
    def set_config(self, config: Dict[str, Any]):
        """Set plugin configuration"""
        self.info.config = config


class PluginRegistry:
    """Plugin registry and manager"""
    
    def __init__(self, plugins_dir: str = None):
        self.plugins: Dict[str, Plugin] = {}
        self.plugins_dir = plugins_dir or str(Path(__file__).parent / "plugins")
        self.logger = logging.getLogger("plugin_registry")
        
    def discover_plugins(self) -> List[PluginInfo]:
        """Discover available plugins"""
        discovered = []
        
        if not os.path.exists(self.plugins_dir):
            return discovered
            
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"plugins.{module_name}")
                    
                    # Look for PLUGIN_INFO
                    if hasattr(module, 'PLUGIN_INFO'):
                        discovered.append(module.PLUGIN_INFO)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to load {filename}: {e}")
                    
        return discovered
        
    def load_plugin(self, plugin_id: str) -> bool:
        """Load a plugin"""
        try:
            module = importlib.import_module(f"plugins.{plugin_id}")
            
            if hasattr(module, 'PLUGIN_CLASS'):
                plugin_class = module.PLUGIN_CLASS
                plugin = plugin_class(module.PLUGIN_INFO)
                
                if plugin.initialize():
                    plugin.state = PluginState.LOADED
                    self.plugins[plugin_id] = plugin
                    self.logger.info(f"Loaded plugin: {plugin_id}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_id}: {e}")
            
        return False
        
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].cleanup()
            del self.plugins[plugin_id]
            return True
        return False
        
    def activate_plugin(self, plugin_id: str) -> bool:
        """Activate a plugin"""
        if plugin_id in self.plugins:
            return self.plugins[plugin_id].activate()
        return False
        
    def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate a plugin"""
        if plugin_id in self.plugins:
            self.plugins[plugin_id].deactivate()
            return True
        return False
        
    def list_plugins(self) -> List[Plugin]:
        """List all plugins"""
        return list(self.plugins.values())
        
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get plugin by ID"""
        return self.plugins.get(plugin_id)


# Example plugins

def create_example_plugins():
    """Create example plugin files"""
    
    # GPS Sensor Plugin
    gps_plugin = '''
from src.plugins.plugin_system import Plugin, PluginInfo, PluginType

PLUGIN_INFO = PluginInfo(
    id="gps_sensor",
    name="GPS Sensor Plugin",
    version="1.0.0",
    author="AirOne",
    description="GPS sensor integration for location tracking",
    plugin_type=PluginType.SENSOR
)

class GPSSensorPlugin(Plugin):
    """GPS Sensor Plugin"""
    
    def initialize(self) -> bool:
        self.position = {"lat": 0.0, "lon": 0.0, "alt": 0.0}
        return True
        
    def get_position(self):
        """Get current GPS position"""
        return self.position
        
    def update_position(self, lat, lon, alt):
        """Update GPS position"""
        self.position = {"lat": lat, "lon": lon, "alt": alt}
'''
    
    # Telemetry Export Plugin  
    export_plugin = '''
from src.plugins.plugin_system import Plugin, PluginInfo, PluginType

PLUGIN_INFO = PluginInfo(
    id="telemetry_export",
    name="Telemetry Export Plugin",
    version="1.0.0",
    author="AirOne",
    description="Export telemetry data to various formats",
    plugin_type=PluginType.EXPORT
)

class TelemetryExportPlugin(Plugin):
    """Telemetry Export Plugin"""
    
    def initialize(self) -> bool:
        self.formats = ["csv", "json", "xml"]
        return True
        
    def export(self, data, format="csv"):
        """Export telemetry data"""
        if format not in self.formats:
            return None
        return f"Exported {len(data)} records to {format}"
'''
    
    # Write plugins
    os.makedirs("/workspace/project/air2/src/plugins", exist_ok=True)
    
    with open("/workspace/project/air2/src/plugins/gps_sensor.py", "w") as f:
        f.write(gps_plugin)
        
    with open("/workspace/project/air2/src/plugins/telemetry_export.py", "w") as f:
        f.write(export_plugin)
        
    # Empty __init__
    with open("/workspace/project/air2/src/plugins/__init__.py", "w") as f:
        f.write("# AirOne Plugins\\n")


def demo():
    """Demo plugin system"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              AirOne v4.0 - Plugin System              ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Create example plugins
    print("Creating example plugins...")
    create_example_plugins()
    
    # Use plugin system
    registry = PluginRegistry()
    
    print("\\nDiscovering plugins...")
    discovered = registry.discover_plugins()
    
    for info in discovered:
        print(f"  • {info.name} ({info.plugin_type.value})")
        
    print("\\n✓ Plugin system demo complete!")
    print(f"  Plugins directory: {registry.plugins_dir}")


if __name__ == "__main__":
    demo()
