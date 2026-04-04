#!/usr/bin/env python3
"""
CanSat Communication Module - Connect to hardware CanSat via serial/USB
"""
import sys
import time
import serial
import threading
from typing import Optional

class CanSatConnection:
    def __init__(self, port: str = 'COM3', baud: int = 9600):
        self.port = port
        self.baud = baud
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        self.running = False
        self.data_callback = None
    
    def connect(self) -> bool:
        """Connect to CanSat"""
        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=1)
            self.connected = True
            self.running = True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from CanSat"""
        self.running = False
        if self.serial:
            self.serial.close()
        self.connected = False
    
    def read_data(self) -> dict:
        """Read a data packet from CanSat"""
        if not self.connected:
            return {}
        
        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8').strip()
                return self.parse_packet(line)
        except:
            pass
        return {}
    
    def parse_packet(self, data: str) -> dict:
        """Parse CanSat data packet"""
        # Format: TEMP,PRESS,ALT,HUM,BAT
        try:
            parts = data.split(',')
            if len(parts) >= 5:
                return {
                    'temperature': float(parts[0]),
                    'pressure': float(parts[1]),
                    'altitude': float(parts[2]),
                    'humidity': float(parts[3]),
                    'battery': float(parts[4]),
                    'timestamp': time.time()
                }
        except:
            pass
        return {'raw': data}
    
    def send_command(self, cmd: str) -> bool:
        """Send command to CanSat"""
        if not self.connected:
            return False
        try:
            self.serial.write((cmd + '\n').encode())
            return True
        except:
            return False


def main():
    print("""
================================================================================
                CanSat Communication Module
================================================================================
    Connect to CanSat hardware via serial/USB
    
Commands:
    connect <port> - Connect to CanSat (e.g., connect COM3)
    disconnect    - Disconnect
    read          - Read single packet
    monitor       - Continuous monitoring
    calibrate     - Calibrate sensors
    status        - Show connection status
    exit          - Exit
================================================================================
""")
    
    cansat = CanSatConnection()
    
    print("AirOne CanSat> ", end="")
    cmd = input().strip().lower()
    
    while cmd not in ['exit', 'quit']:
        parts = cmd.split()
        
        if not parts:
            print("AirOne CanSat> ", end="")
            cmd = input().strip().lower()
            continue
        
        if parts[0] == 'connect':
            port = parts[1] if len(parts) > 1 else 'COM3'
            print(f"Connecting to {port}...")
            if cansat.connect():
                print(f"Connected to CanSat on {port}")
            else:
                print("Failed to connect")
        
        elif cmd == 'disconnect':
            cansat.disconnect()
            print("Disconnected")
        
        elif cmd == 'read':
            data = cansat.read_data()
            if data:
                print(f"Data: {data}")
            else:
                print("No data received")
        
        elif cmd == 'monitor':
            print("Monitoring CanSat (Ctrl+C to stop)...")
            try:
                while True:
                    data = cansat.read_data()
                    if data:
                        print(f"T: {data.get('temperature', 'N/A')}°C | P: {data.get('pressure', 'N/A')}hPa | Alt: {data.get('altitude', 'N/A')}m")
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopped")
        
        elif cmd == 'status':
            print(f"Connected: {cansat.connected}")
            print(f"Port: {cansat.port}")
        
        else:
            print("Unknown command")
        
        print("AirOne CanSat> ", end="")
        cmd = input().strip().lower()
    
    cansat.disconnect()
    print("Goodbye!")

if __name__ == "__main__":
    main()