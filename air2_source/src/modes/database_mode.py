"""
Database Mode for AirOne v4.0
Full SQL/NoSQL database operations with image storage
"""
import sqlite3
import json
import os
import time
import hashlib
import base64
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import threading
import queue

class DatabaseManager:
    """Core database manager with SQLite"""
    def __init__(self, db_path: str = "./airone.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        cursor = self.conn.cursor()
        # Telemetry table
        cursor.execute('''CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            altitude REAL,
            pressure REAL,
            temperature REAL,
            voltage REAL,
            gps_lat REAL,
            gps_lon REAL,
            battery_pct INTEGER,
            descent_rate REAL,
            image_data BLOB,
            packet_id INTEGER
        )''')
        # Images table
        cursor.execute('''CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            image_data BLOB NOT NULL,
            width INTEGER,
            height INTEGER,
            format TEXT,
            mission_time REAL,
            altitude REAL
        )''')
        # Events table
        cursor.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT,
            severity TEXT,
            data TEXT
        )''')
        # Mission log
        cursor.execute('''CREATE TABLE IF NOT EXISTS mission_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time REAL,
            end_time REAL,
            status TEXT,
            total_packets INTEGER,
            total_images INTEGER
        )''')
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_time ON images(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_time ON events(timestamp)')
        self.conn.commit()
    
    def insert_telemetry(self, data: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO telemetry 
            (timestamp, altitude, pressure, temperature, voltage, gps_lat, gps_lon, 
             battery_pct, descent_rate, image_data, packet_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (data.get('timestamp', time.time()),
             data.get('altitude'),
             data.get('pressure'),
             data.get('temperature'),
             data.get('voltage'),
             data.get('gps_lat'),
             data.get('gps_lon'),
             data.get('battery_pct'),
             data.get('descent_rate'),
             data.get('image_data'),
             data.get('packet_id')))
        self.conn.commit()
        return cursor.lastrowid
    
    def insert_image(self, image_data: bytes, metadata: Dict[str, Any]) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO images 
            (timestamp, image_data, width, height, format, mission_time, altitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (time.time(), image_data, metadata.get('width', 320), 
             metadata.get('height', 240), metadata.get('format', 'jpg'),
             metadata.get('mission_time'), metadata.get('altitude')))
        self.conn.commit()
        return cursor.lastrowid
    
    def insert_event(self, event_type: str, description: str, 
                     severity: str = "INFO", data: Dict = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO events 
            (timestamp, event_type, description, severity, data)
            VALUES (?, ?, ?, ?, ?)''',
            (time.time(), event_type, description, severity, 
             json.dumps(data) if data else None))
        self.conn.commit()
        return cursor.lastrowid
    
    def query_telemetry(self, start_time: float = None, end_time: float = None,
                       limit: int = 1000) -> List[Dict]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM telemetry"
        params = []
        if start_time and end_time:
            query += " WHERE timestamp BETWEEN ? AND ?"
            params = [start_time, end_time]
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def query_images(self, start_time: float = None, limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        query = "SELECT id, timestamp, width, height, format, mission_time, altitude FROM images"
        if start_time:
            query += " WHERE timestamp > ?"
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            cursor.execute(query, [start_time])
        else:
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_image_data(self, image_id: int) -> Optional[bytes]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT image_data FROM images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        return row['image_data'] if row else None
    
    def close(self):
        self.conn.close()

class ImageBuffer:
    """Circular buffer for camera images - 200ms capture rate"""
    def __init__(self, max_size: int = 100):
        self.buffer = []
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def add(self, image_data: bytes, metadata: Dict):
        with self.lock:
            self.buffer.append({
                'data': image_data,
                'timestamp': time.time(),
                'metadata': metadata
            })
            if len(self.buffer) > self.max_size:
                self.buffer.pop(0)
    
    def get_latest(self) -> Optional[Dict]:
        with self.lock:
            return self.buffer[-1] if self.buffer else None
    
    def get_all(self) -> List[Dict]:
        with self.lock:
            return list(self.buffer)
    
    def clear(self):
        with self.lock:
            self.buffer.clear()

class CameraIntegrator:
    """Integrates ESP32 camera feed into data packets every 200ms"""
    def __init__(self):
        self.image_buffer = ImageBuffer()
        self.last_capture = 0
        self.capture_interval = 0.2  # 200ms
    
    def capture_frame(self, image_data: bytes, sensor_data: Dict) -> Dict:
        """Capture frame and combine with sensor data"""
        current_time = time.time()
        if current_time - self.last_capture < self.capture_interval:
            return None
        
        self.last_capture = current_time
        
        # Encode image to base64 for storage
        b64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create combined data packet
        packet = {
            'timestamp': current_time,
            'packet_type': 'telemetry_with_image',
            'image': {
                'data': b64_image,
                'format': 'jpeg',
                'size': len(image_data)
            },
            'sensors': sensor_data,
            'mission_time': sensor_data.get('mission_time', 0),
            'altitude': sensor_data.get('altitude', 0)
        }
        
        # Add to buffer
        self.image_buffer.add(image_data, packet)
        
        return packet
    
    def simulate_esp32_frame(self, width: int = 320, height: int = 240) -> bytes:
        """Simulate ESP32 camera frame (grayscale JPEG-like)"""
        # Create synthetic image data
        img_data = np.random.randint(0, 256, (height, width), dtype=np.uint8)
        return bytes(img_data.tobytes()[:min(len(img_data.tobytes()), 10000)])

class DatabaseMode:
    """Main database mode for ground station"""
    def __init__(self, db_path: str = "./airone_data.db"):
        self.db = DatabaseManager(db_path)
        self.camera = CameraIntegrator()
        self.running = False
        self.data_queue = queue.Queue()
        self.mission_start = None
    
    def start_mission(self, mission_name: str = "default"):
        """Start new mission"""
        self.mission_start = time.time()
        self.db.insert_event("MISSION_START", f"Mission {mission_name} started", "INFO")
        self.running = True
    
    def stop_mission(self):
        """Stop mission and log summary"""
        if self.mission_start:
            duration = time.time() - self.mission_start
            self.db.insert_event("MISSION_END", f"Mission ended", "INFO", 
                               {'duration': duration})
        self.running = False
    
    def process_packet(self, sensor_data: Dict, include_image: bool = True) -> int:
        """Process incoming sensor packet with optional image"""
        packet_id = None
        
        # Check if we should include an image (every 200ms)
        if include_image:
            # Simulate ESP32 camera frame
            image_data = self.camera.simulate_esp32_frame()
            packet = self.camera.capture_frame(image_data, sensor_data)
            
            if packet:
                # Store image in database
                image_id = self.db.insert_image(image_data, {
                    'width': 320, 'height': 240, 'format': 'jpg',
                    'mission_time': sensor_data.get('mission_time', 0),
                    'altitude': sensor_data.get('altitude', 0)
                })
                sensor_data['image_id'] = image_id
        
        # Store telemetry
        packet_id = self.db.insert_telemetry(sensor_data)
        return packet_id
    
    def log_event(self, event_type: str, description: str, 
                  severity: str = "INFO", data: Dict = None):
        """Log an event"""
        return self.db.insert_event(event_type, description, severity, data)
    
    def get_telemetry(self, limit: int = 100) -> List[Dict]:
        """Get recent telemetry"""
        return self.db.query_telemetry(limit=limit)
    
    def get_images(self, limit: int = 50) -> List[Dict]:
        """Get recent images"""
        return self.db.query_images(limit=limit)
    
    def export_csv(self, output_path: str = "./telemetry_export.csv") -> str:
        """Export telemetry to CSV"""
        import csv
        data = self.db.query_telemetry(limit=10000)
        if not data:
            return "No data"
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return f"Exported {len(data)} records to {output_path}"
    
    def close(self):
        """Clean up resources"""
        self.running = False
        self.db.close()
