"""
GNSS Module - u-blox NEO-M8N GPS + Patch Antenna
"""
import serial
import time
from typing import Optional, Dict, Any
from datetime import datetime

class NEO_M8N:
    """u-blox NEO-M8N GNSS Module"""
    
    def __init__(self, port: str = '/dev/ttyUSB1', baud: int = 9600):
        self.port = port
        self.baud = baud
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        
        # GPS Data
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.speed = 0.0
        self.heading = 0.0
        self.satellites = 0
        self.fix_quality = 0
        self.timestamp = None
        self.hdop = 0.0
        
    def connect(self) -> bool:
        """Connect to GPS module"""
        try:
            self.serial = serial.Serial(
                self.port,
                self.baud,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"GPS connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from GPS"""
        if self.serial:
            self.serial.close()
        self.connected = False
    
    def read_nmea(self) -> Optional[str]:
        """Read raw NMEA sentence"""
        if not self.connected:
            return None
        
        try:
            line = self.serial.readline()
            return line.decode('utf-8', errors='ignore').strip()
        except:
            return None
    
    def parse_gga(self, sentence: str) -> Dict[str, Any]:
        """Parse GGA (Global Positioning System Fix Data)"""
        if not sentence.startswith('$GNGGA') and not sentence.startswith('$GPGGA'):
            return {}
        
        parts = sentence.split(',')
        if len(parts) < 15:
            return {}
        
        try:
            # Time
            if parts[1]:
                hour = int(parts[1][0:2])
                minute = int(parts[1][2:4])
                second = int(parts[1][4:6])
                self.timestamp = f"{hour:02d}:{minute:02d}:{second:02d}"
            
            # Latitude
            if parts[2] and parts[3]:
                lat = float(parts[2])
                lat_deg = int(lat // 100)
                lat_min = lat - lat_deg * 100
                self.latitude = lat_deg + lat_min / 60
                if parts[3] == 'S':
                    self.latitude = -self.latitude
            
            # Longitude
            if parts[4] and parts[5]:
                lon = float(parts[4])
                lon_deg = int(lon // 100)
                lon_min = lon - lon_deg * 100
                self.longitude = lon_deg + lon_min / 60
                if parts[5] == 'W':
                    self.longitude = -self.longitude
            
            # Fix quality
            self.fix_quality = int(parts[6]) if parts[6] else 0
            
            # Satellites
            self.satellites = int(parts[7]) if parts[7] else 0
            
            # HDOP
            self.hdop = float(parts[8]) if parts[8] else 0.0
            
            # Altitude
            if parts[9]:
                self.altitude = float(parts[9])
                
            return {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'altitude': self.altitude,
                'fix_quality': self.fix_quality,
                'satellites': self.satellites,
                'hdop': self.hdop
            }
        except:
            return {}
    
    def parse_rmc(self, sentence: str) -> Dict[str, Any]:
        """Parse RMC (Recommended Minimum Specific GPS Data)"""
        if not sentence.startswith('$GNRMC') and not sentence.startswith('$GPRMC'):
            return {}
        
        parts = sentence.split(',')
        if len(parts) < 10:
            return {}
        
        try:
            # Speed (knots to m/s)
            if parts[7]:
                self.speed = float(parts[7]) * 0.514444
            
            # Heading
            if parts[8]:
                self.heading = float(parts[8])
                
            return {
                'speed': self.speed,
                'heading': self.heading
            }
        except:
            return {}
    
    def update(self) -> Dict[str, Any]:
        """Update GPS data"""
        data = {}
        
        while self.serial.in_waiting:
            line = self.read_nmea()
            if line:
                if '$GNGGA' in line or '$GPGGA' in line:
                    data.update(self.parse_gga(line))
                elif '$GNRMC' in line or '$GPRMC' in line:
                    data.update(self.parse_rmc(line))
        
        return data
    
    def get_position(self) -> Dict[str, Any]:
        """Get current position"""
        self.update()
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'timestamp': self.timestamp,
            'fix': self.fix_quality,
            'satellites': self.satellites,
            'speed': self.speed,
            'heading': self.heading,
            'hdop': self.hdop
        }
    
    def is_fixed(self) -> bool:
        """Check if GPS has a fix"""
        return self.fix_quality > 0
    
    def wait_for_fix(self, timeout: int = 60) -> bool:
        """Wait for GPS fix"""
        start = time.time()
        while time.time() - start < timeout:
            self.update()
            if self.is_fixed():
                return True
            time.sleep(1)
        return False


def main():
    """Test GPS module"""
    gps = NEO_M8N('/dev/ttyUSB1', 9600)
    
    if gps.connect():
        print("GPS connected!")
        print("Waiting for fix...")
        
        if gps.wait_for_fix(30):
            print(f"Fix acquired: {gps.satellites} satellites")
            while True:
                pos = gps.get_position()
                print(f"Lat: {pos['latitude']:.6f}, Lon: {pos['longitude']:.6f}, Alt: {pos['altitude']}m")
                time.sleep(1)
        else:
            print("No GPS fix")
        
        gps.disconnect()

if __name__ == "__main__":
    main()