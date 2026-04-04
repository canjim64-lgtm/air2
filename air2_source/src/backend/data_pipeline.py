"""
Data Pipeline Module - Processing and Analysis
- Raw sensor data ingestion
- Data validation and cleaning
- Feature extraction
- Real-time processing
- Storage (CSV, JSON, SQLite)
"""
import json
import csv
import time
import threading
import queue
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics


class SensorDataPacket:
    """Standardized sensor data packet"""
    
    def __init__(self):
        self.timestamp = time.time()
        self.data: Dict[str, Any] = {}
        self.source = ""
        self.valid = True
        self.errors: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'source': self.source,
            'valid': self.valid,
            'errors': self.errors,
            'data': self.data
        }
    
    def to_csv_row(self) -> List:
        row = [self.timestamp, self.source, self.valid]
        for key in sorted(self.data.keys()):
            row.append(self.data[key])
        return row


class DataPipeline:
    """Main data processing pipeline"""
    
    def __init__(self):
        # Data queue for async processing
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Processing state
        self.running = False
        self.processing_thread = None
        
        # Storage
        self.csv_file = None
        self.csv_writer = None
        self.json_file = None
        self.buffer: List[Dict] = []
        
        # Statistics
        self.stats = {
            'packets_received': 0,
            'packets_valid': 0,
            'packets_invalid': 0,
            'processing_time': 0,
            'buffer_size': 0
        }
        
        # Validation rules
        self.validation_rules = {
            'temperature': (-50, 60),
            'humidity': (0, 100),
            'pressure': (800, 1200),
            'altitude': (-500, 50000),
            'latitude': (-90, 90),
            'longitude': (-180, 180),
            'battery': (0, 100)
        }
    
    def start(self):
        """Start the pipeline"""
        self.running = True
        self.processing_thread = threading.Thread(target=self.process_loop, daemon=True)
        self.processing_thread.start()
    
    def stop(self):
        """Stop the pipeline"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
    
    def add_packet(self, data: Dict[str, Any], source: str = "unknown"):
        """Add data packet to pipeline"""
        packet = SensorDataPacket()
        packet.source = source
        packet.data = data
        self.input_queue.put(packet)
    
    def process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Get packet with timeout
                packet = self.input_queue.get(timeout=0.1)
                
                start_time = time.time()
                
                # Validate
                self.validate_packet(packet)
                
                # Process
                self.process_packet(packet)
                
                # Store
                self.store_packet(packet)
                
                # Update stats
                self.stats['packets_received'] += 1
                if packet.valid:
                    self.stats['packets_valid'] += 1
                else:
                    self.stats['packets_invalid'] += 1
                
                self.stats['processing_time'] = time.time() - start_time
                
                # Push to output
                self.output_queue.put(packet)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")
    
    def validate_packet(self, packet: SensorDataPacket):
        """Validate sensor data"""
        for key, value in packet.data.items():
            if key in self.validation_rules:
                min_val, max_val = self.validation_rules[key]
                if not isinstance(value, (int, float)):
                    packet.valid = False
                    packet.errors.append(f"Invalid type for {key}")
                elif value < min_val or value > max_val:
                    packet.valid = False
                    packet.errors.append(f"{key} out of range: {value}")
        
        return packet.valid
    
    def process_packet(self, packet: SensorDataPacket):
        """Process and enrich data"""
        # Add derived values
        data = packet.data
        
        # Calculate dew point if temp and humidity available
        if 'temperature' in data and 'humidity' in data:
            temp = data['temperature']
            humidity = data['humidity']
            # Simple dew point approximation
            a = 17.27
            b = 237.7
            alpha = ((a * temp) / (b + temp)) + (humidity / 100)
            data['dew_point'] = (b * alpha) / (a - alpha)
        
        # Add data quality score
        if 'temperature' in data and 'humidity' in data and 'pressure' in data:
            data['quality_score'] = 0.9  # Simplified
        else:
            data['quality_score'] = 0.5
        
        # Add sequence number
        data['seq'] = self.stats['packets_received']
    
    def store_packet(self, packet: SensorDataPacket):
        """Store packet to file/database"""
        # CSV storage
        if self.csv_writer:
            self.csv_writer.writerow(packet.to_csv_row())
        
        # JSON buffer
        self.buffer.append(packet.to_dict())
        if len(self.buffer) > 1000:
            self.buffer = self.buffer[-500:]
    
    def start_csv_log(self, filename: str):
        """Start CSV logging"""
        self.csv_file = open(filename, 'w', newline='')
        fieldnames = ['timestamp', 'source', 'valid']
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
        self.csv_writer.writeheader()
    
    def stop_csv_log(self):
        """Stop CSV logging"""
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        self.stats['buffer_size'] = len(self.buffer)
        self.stats['queue_size'] = self.input_queue.qsize()
        return self.stats.copy()


class DataAggregator:
    """Aggregate data over time windows"""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size  # seconds
        self.data_buffer: List[Dict] = []
    
    def add(self, data: Dict):
        """Add data point"""
        data['timestamp'] = time.time()
        self.data_buffer.append(data)
        
        # Remove old data
        cutoff = time.time() - self.window_size
        self.data_buffer = [d for d in self.data_buffer if d.get('timestamp', 0) > cutoff]
    
    def get_stats(self, key: str) -> Dict[str, float]:
        """Get statistics for a key"""
        values = [d.get(key) for d in self.data_buffer if key in d]
        
        if not values:
            return {'min': 0, 'max': 0, 'mean': 0, 'median': 0}
        
        return {
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'count': len(values)
        }
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all keys"""
        keys = set()
        for d in self.data_buffer:
            keys.update(d.keys())
        
        return {key: self.get_stats(key) for key in keys if key != 'timestamp'}


class DataExporter:
    """Export data to various formats"""
    
    @staticmethod
    def to_csv(data: List[Dict], filename: str):
        """Export to CSV"""
        if not data:
            return
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def to_json(data: List[Dict], filename: str):
        """Export to JSON"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def to_kml(data: List[Dict], filename: str):
        """Export GPS data to KML"""
        kml = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Flight Path</name>
'''
        for point in data:
            if 'latitude' in point and 'longitude' in point:
                kml += f'''  <Placemark>
    <Point>
      <coordinates>{point['longitude']},{point['latitude']},{point.get('altitude', 0)}</coordinates>
    </Point>
  </Placemark>
'''
        kml += '</Document>\n</kml>'
        
        with open(filename, 'w') as f:
            f.write(kml)


def main():
    """Test pipeline"""
    pipeline = DataPipeline()
    pipeline.start()
    
    # Add test data
    for i in range(10):
        data = {
            'temperature': 20 + i,
            'humidity': 50 + i,
            'pressure': 1013,
            'altitude': 1000 + i * 10
        }
        pipeline.add_packet(data, 'test')
        time.sleep(0.1)
    
    time.sleep(1)
    
    print("Stats:", pipeline.get_stats())
    
    pipeline.stop()

if __name__ == "__main__":
    main()