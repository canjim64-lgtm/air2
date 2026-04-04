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

# Import from AirOne modules - sensors, telemetry, gnss, ai
BACKEND_full = True

try:
    from ..sensors import SensorManager, CombinedSensors
    HAS_SENSORS = True
except ImportError:
    HAS_SENSORS = False

try:
    from ..telemetry import TelemetryProcessor, TelemetryAnalyzer
    HAS_TELEMETRY = True
except ImportError:
    HAS_TELEMETRY = False

try:
    from ..gnss import GNSSProcessor
    HAS_GNSS = True
except ImportError:
    HAS_GNSS = False

try:
    from ..ai import AIModel, UnifiedAIService
    HAS_AI = True
except ImportError:
    HAS_AI = False

__all__ = [
    # Core
    'CanSatPayload',
    'HC12Radio',
    'NEO_M8N',
    'EnvironmentalSuite',
    # Sensors
    'BME688Sensor',
    'BMP388Sensor', 
    'MiCS6814Sensor',
    'SGP30Sensor',
    # Data
    'DataPipeline',
    'DataAggregator',
    'DataExporter',
    # AI
    'AIModule',
    'AnomalyDetector',
    'FlightPhaseClassifier',
    'Predictor',
    # AirOne modules
    'HAS_SENSORS',
    'HAS_TELEMETRY',
    'HAS_GNSS',
    'HAS_AI',
    'SensorManager',
    'TelemetryProcessor',
    'GNSSProcessor',
    'AIModel',
    'AirOneBackend',
    'get_backend',
]

__version__ = "4.0.0"


class AirOneBackend:
    """Unified AirOne Backend"""
    
    def __init__(self):
        self.radio = None
        self.gps = None
        self.sensors = None
        self.pipeline = None
        self.ai = None
        self.initialized = False
    
    def init_all(self):
        """Initialize all subsystems"""
        print("Initializing AirOne Backend...")
        
        # Initialize sensors
        self.sensors = EnvironmentalSuite()
        self.sensors.initialize()
        
        # Initialize GPS
        self.gps = NEO_M8N()
        
        # Initialize radio
        self.radio = HC12Radio()
        
        # Initialize pipeline
        self.pipeline = DataPipeline()
        self.pipeline.start()
        
        # Initialize AI
        self.ai = AIModule()
        
        self.initialized = True
        print("✓ Backend initialized")
        return True
    
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
            'sensors': self.sensors.get_status() if self.sensors else {},
            'gps_fixed': self.gps.is_fixed() if self.gps else False,
            'radio': self.radio.get_status() if self.radio else {},
            'pipeline': self.pipeline.get_stats() if self.pipeline else {},
            'ai': self.ai.get_status() if self.ai else {},
        }


def get_backend():
    """Get AirOne Backend instance"""
    return AirOneBackend()