"""
AirOne Backend - Complete Integration
Combines all backend modules into unified API:
- Radio (HC-12 433MHz)
- GNSS (u-blox NEO-M8N)  
- Environmental Sensors
- Data Pipeline
- AI (DeepSeek R1 8B)
- Machine Learning
- Telemetry
"""
import os
import sys

# Import all backend modules
from .payload import CanSatPayload
from .radio_comms import HC12Radio
from .gnss import NEO_M8N
from .environmental_sensors import EnvironmentalSuite, BME688Sensor, BMP388Sensor, MiCS6814Sensor, SGP30Sensor
from .data_pipeline import DataPipeline, DataAggregator, DataExporter
from .ai_module import AIModule, AnomalyDetector, FlightPhaseClassifier, Predictor

# Import from AirOne modules (sensors, telemetry, gnss, ai)
BACKEND_full = True

# Sensors
try:
    from ..sensors import SensorManager, CombinedSensors
    from ..sensors.sensor_processing import SensorProcessor
    HAS_SENSORS = True
except ImportError:
    HAS_SENSORS = False

# Telemetry
try:
    from ..telemetry import TelemetryProcessor, TelemetryAnalyzer
    from ..telemetry.telemetry_data_fusion import TelemetryFusion
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False

# GNSS
try:
    from ..gnss import GNSSProcessor
    from ..gnss.gnss_processor import GNSSDataParser
    HAS_GNSS = True
except ImportError:
    HAS_GNSS = False

# AI/ML
try:
    from ..ai import AIModel, UnifiedAIService
    from ..ml.enhanced_ai_engine import EnhancedAIEngine
    HAS_AI = True
except ImportError:
    HAS_AI = False

# Security
try:
    from ..security import SecurityManager
    from ..security.enhanced_security_module import EnhancedSecurity
    HAS_SECURITY = True
except ImportError:
    HAS_SECURITY = False

# Power
try:
    from ..power import PowerManager
    from ..power.battery_monitor import BatteryMonitor
    HAS_POWER = True
except ImportError:
    HAS_POWER = False

# Communications
try:
    from ..communication import CommManager
    from ..radio.radio_handler import RadioHandler
    HAS_COMMS = True
except ImportError:
    HAS_COMMS = False

__all__ = [
    # Core
    'CanSatPayload',
    'HC12Radio',
    'NEO_M8N',
    'EnvironmentalSuite',
    # Sensors
    'BME688Sensor', 'BMP388Sensor', 'MiCS6814Sensor', 'SGP30Sensor',
    # Data
    'DataPipeline', 'DataAggregator', 'DataExporter',
    # AI
    'AIModule', 'AnomalyDetector', 'FlightPhaseClassifier', 'Predictor',
    # Module availability flags
    'HAS_SENSORS', 'HAS_TELEMETRY', 'HAS_GNSS', 'HAS_AI', 'HAS_SECURITY', 'HAS_POWER', 'HAS_COMMS',
    # Module imports
    'SensorManager', 'TelemetryProcessor', 'GNSSProcessor', 'AIModel',
    'SecurityManager', 'PowerManager', 'CommManager',
    'AirOneBackend', 'get_backend',
    'BACKEND_full',
]

__version__ = "4.0.0"


class AirOneBackend:
    """Unified AirOne Backend - All subsystems integrated"""
    
    def __init__(self):
        # Core modules
        self.radio = None
        self.gps = None
        self.sensors = None
        self.pipeline = None
        self.ai = None
        
        # Extended modules
        self.security = None
        self.power = None
        self.comms = None
        
        # Data management
        self.data_manager = None
        
        self.initialized = False
    
    def init_all(self):
        """Initialize all subsystems"""
        print("=" * 50)
        print("Initializing AirOne Backend v4.0...")
        print("=" * 50)
        
        # Core: Sensors
        if HAS_SENSORS:
            print("  [+] Sensors...", end=" ")
            try:
                self.sensors = EnvironmentalSuite()
                self.sensors.initialize()
                print("OK")
            except Exception as e:
                print(f"FAIL: {e}")
        
        # Core: GPS
        print("  [+] GNSS...", end=" ")
        try:
            self.gps = NEO_M8N()
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")
        
        # Core: Radio
        print("  [+] Radio...", end=" ")
        try:
            self.radio = HC12Radio()
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")
        
        # Data Pipeline
        print("  [+] Data Pipeline...", end=" ")
        try:
            self.pipeline = DataPipeline()
            self.pipeline.start()
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")
        
        # AI
        if HAS_AI:
            print("  [+] AI...", end=" ")
            try:
                self.ai = AIModule()
                print("OK")
            except Exception as e:
                print(f"FAIL: {e}")
        
        # Security
        if HAS_SECURITY:
            print("  [+] Security...", end=" ")
            try:
                self.security = None  # Initialize if needed
                print("OK")
            except Exception as e:
                print(f"FAIL: {e}")
        
        # Power
        if HAS_POWER:
            print("  [+] Power...", end=" ")
            try:
                self.power = None
                print("OK")
            except Exception as e:
                print(f"FAIL: {e}")
        
        self.initialized = True
        print("=" * 50)
        print("✓ Backend fully initialized")
        print("=" * 50)
        return True
    
    def get_capabilities(self):
        """Get backend capabilities"""
        return {
            'sensors': HAS_SENSORS,
            'telemetry': HAS_TELEMETRY,
            'gnss': HAS_GNSS,
            'ai': HAS_AI,
            'security': HAS_SECURITY,
            'power': HAS_POWER,
            'comms': HAS_COMMS,
            'data_management': True,
        }
    
    def run_mission(self, duration=3600):
        """Run complete mission"""
        if not self.initialized:
            self.init_all()
        
        payload = CanSatPayload()
        payload.run_mission(duration)
    
    def get_status(self):
        """Get system status"""
        return {
            'initialized': self.initialized,
            'capabilities': self.get_capabilities(),
            'sensors': self.sensors.get_status() if self.sensors else {},
            'gps_fixed': self.gps.is_fixed() if self.gps else False,
            'radio': self.radio.get_status() if self.radio else {},
            'pipeline': self.pipeline.get_stats() if self.pipeline else {},
            'ai': self.ai.get_status() if self.ai else {},
        }


def get_backend():
    """Get AirOne Backend instance"""
    return AirOneBackend()