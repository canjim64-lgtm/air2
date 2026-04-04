"""
AirOne Backend Integration Module
Integrates all sensors, radio, GPS, data pipeline, and AI
"""
import time
import threading
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Import all backend modules
from .radio_comms import HC12Radio
from .gnss import NEO_M8N
from .environmental_sensors import EnvironmentalSuite
from .data_pipeline import DataPipeline, DataAggregator, DataExporter
from .ai_module import AIModule


class CanSatPayload:
    """Complete CanSat payload integrating all subsystems"""
    
    def __init__(self):
        # Radio
        self.radio = HC12Radio('/dev/ttyUSB0', 9600)
        
        # GPS
        self.gps = NEO_M8N('/dev/ttyUSB1', 9600)
        
        # Environmental sensors
        self.sensors = EnvironmentalSuite()
        
        # Data pipeline
        self.pipeline = DataPipeline()
        self.aggregator = DataAggregator(window_size=60)
        
        # AI
        self.ai = AIModule()
        
        # State
        self.running = False
        self.payload_id = "CANSAT-001"
        self.flight_mode = "ground"  # ground, flight, descent, landing
        
        # Configuration
        self.config = {
            'telemetry_rate': 1.0,  # seconds between transmissions
            'sensor_rate': 0.1,      # seconds between sensor reads
            'data_retention': 3600,  # seconds
            'enable_ai': True,
            'enable_radio': True
        }
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize all subsystems"""
        results = {
            'radio': False,
            'gps': False,
            'sensors': False,
            'pipeline': False
        }
        
        # Initialize sensors
        self.sensors.initialize()
        results['sensors'] = True
        
        # Initialize radio
        results['radio'] = self.radio.connect()
        
        # Initialize GPS
        results['gps'] = self.gps.connect()
        
        # Start data pipeline
        self.pipeline.start()
        
        results['pipeline'] = True
        
        return results
    
    def shutdown(self):
        """Shutdown all subsystems"""
        self.running = False
        
        if self.radio.connected:
            self.radio.disconnect()
        
        if self.gps.connected:
            self.gps.disconnect()
        
        self.pipeline.stop()
    
    def read_all_sensors(self) -> Dict[str, Any]:
        """Read all sensor data"""
        data = {}
        
        # GPS data
        gps_data = self.gps.get_position()
        data.update(gps_data)
        
        # Environmental sensors
        env_data = self.sensors.read_all()
        data.update(env_data)
        
        # Add metadata
        data['payload_id'] = self.payload_id
        data['flight_mode'] = self.flight_mode
        data['timestamp'] = time.time()
        data['datetime'] = datetime.now().isoformat()
        
        return data
    
    def process_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw data through pipeline and AI"""
        # Add to pipeline
        self.pipeline.add_packet(raw_data, self.payload_id)
        
        # Add to aggregator
        self.aggregator.add(raw_data)
        
        # AI analysis
        ai_result = self.ai.process(raw_data)
        
        # Combine results
        processed = {
            'raw': raw_data,
            'ai_analysis': ai_result['analysis'],
            'ai_recommendations': ai_result['recommendations'],
            'aggregated': self.aggregator.get_all_stats()
        }
        
        return processed
    
    def transmit_data(self, data: Dict[str, Any]):
        """Transmit data via radio"""
        if not self.radio.connected:
            return
        
        # Format for transmission (limited bandwidth)
        tx_data = {
            'id': self.payload_id,
            't': data.get('timestamp', time.time()),
            'lat': data.get('latitude', 0),
            'lon': data.get('longitude', 0),
            'alt': data.get('altitude', 0),
            'temp': data.get('temperature', 0),
            'pres': data.get('pressure', 0),
            'bat': data.get('battery', 0)
        }
        
        # Convert to string format
        msg = json.dumps(tx_data)
        self.radio.send(msg)
    
    def run_mission(self, duration: int = 3600):
        """Run mission for specified duration"""
        self.running = True
        start_time = time.time()
        
        print(f"Starting mission: {self.payload_id}")
        print(f"Duration: {duration}s")
        
        iteration = 0
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # Read sensors
                sensor_data = self.read_all_sensors()
                
                # Process
                processed = self.process_data(sensor_data)
                
                # Transmit (if enabled)
                if self.config['enable_radio']:
                    self.transmit_data(sensor_data)
                
                # Print status
                if iteration % 10 == 0:
                    print(f"\n--- Iteration {iteration} ---")
                    print(f"GPS: {sensor_data.get('latitude', 0):.6f}, {sensor_data.get('longitude', 0):.6f}")
                    print(f"Alt: {sensor_data.get('altitude', 0):.0f}m")
                    print(f"Temp: {sensor_data.get('temperature', 0):.1f}°C")
                    print(f"Bat: {sensor_data.get('battery', 0):.0f}%")
                    print(f"AI: {processed['ai_analysis'].get('phase', 'unknown')}")
                    
                    if processed['ai_recommendations']:
                        print("Recommendations:")
                        for rec in processed['ai_recommendations']:
                            print(f"  {rec}")
                
                iteration += 1
                
                # Sleep
                time.sleep(self.config['telemetry_rate'])
                
            except KeyboardInterrupt:
                print("\nMission interrupted!")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
        
        print("Mission complete!")
        
        # Export data
        self.export_data()
    
    def export_data(self):
        """Export all collected data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get all buffered data
        data = self.pipeline.buffer
        
        if data:
            # Export to CSV
            DataExporter.to_csv(data, f"flight_data_{timestamp}.csv")
            
            # Export to JSON
            DataExporter.to_json(data, f"flight_data_{timestamp}.json")
            
            # Export GPS to KML
            DataExporter.to_kml(data, f"flight_path_{timestamp}.kml")
            
            print(f"Data exported: flight_data_{timestamp}.csv/json/kml")
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            'payload_id': self.payload_id,
            'running': self.running,
            'flight_mode': self.flight_mode,
            'radio': self.radio.get_status(),
            'gps_fixed': self.gps.is_fixed(),
            'sensors': self.sensors.get_status(),
            'pipeline': self.pipeline.get_stats(),
            'ai': self.ai.get_status()
        }


def main():
    """Test complete payload"""
    print("Initializing CanSat Payload...")
    
    payload = CanSatPayload()
    
    # Initialize
    results = payload.initialize()
    print("Initialization results:", results)
    
    # Run short mission (60 seconds for testing)
    print("\nRunning 60 second test mission...")
    payload.run_mission(duration=60)
    
    # Get final status
    print("\nFinal Status:")
    status = payload.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Shutdown
    payload.shutdown()


if __name__ == "__main__":
    main()