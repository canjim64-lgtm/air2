"""
Mode Manager for AirOne v4.0 Ultimate
Enterprise-grade operational mode management and initialization
"""

from enum import Enum
from typing import Any, Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class OperationalMode(Enum):
    """Operational modes for AirOne system"""
    DESKTOP_GUI = "desktop_gui"
    HEADLESS_CLI = "headless_cli"
    OFFLINE = "offline"
    SIMULATION = "simulation"
    RECEIVER = "receiver"
    REPLAY = "replay"
    SAFE = "safe"
    WEB = "web"
    DIGITAL_TWIN = "digital_twin"
    POWERFUL = "powerful"
    SECURITY = "security"
    ULTIMATE = "ultimate"
    COSMIC = "cosmic"
    MISSION = "mission"


class ModeManager:
    """Manages operational modes for the AirOne system"""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModeManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.current_mode = None
        self.mode_instances = {}
        self.mode_history = []
        self.initialized = True
        logger.info("Mode Manager initialized")
    
    def set_mode(self, mode: OperationalMode) -> bool:
        """Set the current operational mode with history tracking"""
        if not isinstance(mode, OperationalMode):
            logger.error(f"Invalid mode type: {type(mode)}")
            return False
            
        if self.current_mode:
            self.mode_history.append(self.current_mode)
            
        self.current_mode = mode
        logger.info(f"System mode transitioned to: {mode.value}")
        return True
    
    def get_current_mode(self) -> Optional[OperationalMode]:
        """Get the current operational mode"""
        return self.current_mode
    
    def register_mode_instance(self, mode: OperationalMode, instance: Any):
        """Register a running instance of a mode"""
        self.mode_instances[mode] = instance
        
    def get_mode_instance(self, mode: OperationalMode) -> Optional[Any]:
        """Get a running instance of a mode"""
        return self.mode_instances.get(mode)
    
    def reset(self):
        """Reset the mode manager state"""
        self.current_mode = None
        self.mode_instances.clear()
        self.mode_history.clear()
        logger.info("Mode Manager state reset")

def get_mode_manager() -> ModeManager:
    """Get the singleton mode manager instance"""
    return ModeManager()

def initialize_mode_manager() -> ModeManager:
    """Initialize and return the mode manager"""
    return ModeManager()
