"""
AirOne v4.0 Operational Modes
5 core modes with full implementations
"""
from .desktop_gui_mode import DesktopGUIMode
from .web_mode import WebMode
from .powerful_security_mode import PowerfulSecurityMode
from .ultimate_enhanced_mode import UltimateEnhancedMode
from .database_mode import DatabaseMode

__all__ = [
    'DesktopGUIMode',
    'WebMode', 
    'PowerfulSecurityMode',
    'UltimateEnhancedMode',
    'DatabaseMode'
]

MODE_CLASSES = {
    'desktop': DesktopGUIMode,
    'web': WebMode,
    'security': PowerfulSecurityMode,
    'enhanced': UltimateEnhancedMode,
    'database': DatabaseMode,
}

def get_mode(mode_name: str):
    return MODE_CLASSES.get(mode_name.lower())
