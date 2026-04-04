"""
AirOne Backend Package
Complete CanSat/Ground Station backend with:
- HC-12 433MHz Radio Communication
- u-blox NEO-M8N GPS/GNSS
- Environmental Sensors Suite
- Data Pipeline & Processing
- AI Analysis & Predictions
"""
from .payload import CanSatPayload
from .radio_comms import HC12Radio
from .gnss import NEO_M8N
from .environmental_sensors import EnvironmentalSuite
from .data_pipeline import DataPipeline, DataAggregator, DataExporter
from .ai_module import AIModule

__all__ = [
    'CanSatPayload',
    'HC12Radio',
    'NEO_M8N',
    'EnvironmentalSuite',
    'DataPipeline',
    'DataAggregator',
    'DataExporter',
    'AIModule'
]

__version__ = "4.0.0"