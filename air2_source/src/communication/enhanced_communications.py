"""
Enhanced Communications for AirOne v3.0
Handles communication protocols and data transmission
"""

import struct
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime


class BinaryTelemetryProtocol:
    """Binary protocol for telemetry data"""
    
    def __init__(self):
        self.protocol_version = 2
        self.header_size = 16  # Fixed header size
        
    def encode_packet(self, data: Dict[str, Any]) -> bytes:
        """Encode telemetry data into binary packet"""
        # Create header
        timestamp = int(datetime.now().timestamp() * 1000)  # milliseconds
        packet_type = 1  # telemetry packet
        data_json = json.dumps(data)
        data_bytes = data_json.encode('utf-8')
        data_len = len(data_bytes)
        
        # Pack header: timestamp(8) + type(2) + length(2) + reserved(4)
        header = struct.pack('<QHHI', timestamp, packet_type, data_len, 0)
        
        # Combine header and data
        packet = header + data_bytes
        
        # Add simple checksum
        checksum = sum(packet) % 65536
        packet_with_checksum = packet + struct.pack('<H', checksum)
        
        return packet_with_checksum
    
    def decode_packet(self, packet_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Decode binary packet to telemetry data"""
        if len(packet_bytes) < self.header_size + 2:  # +2 for checksum
            return None
            
        # Extract checksum
        checksum = struct.unpack('<H', packet_bytes[-2:])[0]
        packet_without_checksum = packet_bytes[:-2]
        
        # Verify checksum
        calculated_checksum = sum(packet_without_checksum) % 65536
        if checksum != calculated_checksum:
            return None
            
        # Extract header
        header = packet_without_checksum[:self.header_size]
        timestamp, packet_type, data_len, reserved = struct.unpack('<QHHI', header)
        
        # Extract data
        data_bytes = packet_without_checksum[self.header_size:self.header_size + data_len]
        
        try:
            data_json = data_bytes.decode('utf-8')
            data = json.loads(data_json)
            data['timestamp'] = datetime.fromtimestamp(timestamp / 1000)
            data['packet_type'] = packet_type
            return data
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None


class CommunicationManager:
    """Manages communications for AirOne system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.protocol = BinaryTelemetryProtocol()
        self.is_connected = False
        self.connection_type = self.config.get('connection_type', 'serial')
        self.port = self.config.get('port', '/dev/ttyUSB0')
        self.baud_rate = self.config.get('baud_rate', 9600)
        
        # Encryption key
        self.encryption_key = self.config.get('encryption_key', b'default_key_for_testing')
        
        # Simulated hardware interface for testing
        class SimulatedHardwareInterface:
            def __init__(self, port, baud_rate):
                self.port = port
                self.baud_rate = baud_rate
                self.buffer = deque() # Simulate incoming data
                self.logger = logging.getLogger(self.__class__.__name__)

            def connect(self):
                self.logger.info(f"Simulating connection to {self.port} at {self.baud_rate} baud.")
                time.sleep(0.5) # Simulate connection delay
                if random.random() < 0.9: # 90% success rate
                    self.logger.info("Simulated connection successful.")
                    return True
                self.logger.warning("Simulated connection failed.")
                return False

            def send(self, data: bytes):
                self.logger.info(f"Simulating sending {len(data)} bytes to {self.port}.")
                time.sleep(0.01) # Simulate transmission delay

            def receive(self) -> Optional[bytes]:
                if random.random() < 0.1: # Simulate 10% packet loss
                    self.logger.debug("Simulated packet loss.")
                    return None
                
                if self.buffer:
                    return self.buffer.popleft()
                
                # Simulate incoming data
                if random.random() < 0.2: # 20% chance of receiving some data
                    num_telemetry_points = random.randint(1, 3)
                    telemetry_list = []
                    for _ in range(num_telemetry_points):
                        telemetry_list.append({
                            'timestamp': datetime.now().timestamp(),
                            'altitude': round(random.uniform(100, 1000), 2),
                            'velocity': round(random.uniform(0, 100), 2),
                            'temperature': round(random.uniform(15, 35), 2),
                            'pressure': round(random.uniform(1000, 1020), 2),
                            'battery': round(random.uniform(80, 100), 2),
                            'signal_strength': round(random.uniform(-80, -30), 2)
                        })
                    
                    data_to_send = self.protocol.encode_packet(telemetry_list[0]) # Only send first for now
                    self.logger.debug(f"Simulating receiving {len(data_to_send)} bytes from {self.port}.")
                    return data_to_send
                return None
            
            def add_to_buffer(self, data: bytes):
                self.buffer.append(data)

        self.hardware_interface = SimulatedHardwareInterface(self.port, self.baud_rate)
        
    def connect(self) -> bool:
        """Connect to communication channel (simulated)"""
        if self.hardware_interface.connect():
            self.is_connected = True
            logging.info("Communication connection established (simulated).")
            return True
        logging.error("Communication connection failed (simulated).")
        return False
    
    def disconnect(self):
        """Disconnect from communication channel"""
        self.is_connected = False
        logging.info("Communication disconnected.")
        
    def send_telemetry(self, data: Dict[str, Any]) -> bool:
        """Send telemetry data"""
        if not self.is_connected:
            logging.warning("Not connected, cannot send telemetry.")
            return False
            
        try:
            packet = self.protocol.encode_packet(data)
            self.hardware_interface.send(packet)
            logging.info(f"Sending telemetry packet of {len(packet)} bytes (simulated).")
            return True
        except Exception as e:
            logging.error(f"Failed to send telemetry (simulated): {e}")
            return False
    
    def receive_telemetry(self) -> Optional[Dict[str, Any]]:
        """Receive telemetry data"""
        if not self.is_connected:
            logging.warning("Not connected, cannot receive telemetry.")
            return None
            
        try:
            raw_packet_bytes = self.hardware_interface.receive()
            if raw_packet_bytes:
                decoded_data = self.protocol.decode_packet(raw_packet_bytes)
                if decoded_data:
                    logging.info(f"Received and decoded telemetry packet (simulated).")
                    return decoded_data
                logging.warning("Failed to decode received packet (simulated).")
            return None
        except Exception as e:
            logging.error(f"Failed to receive telemetry (simulated): {e}")
            return None
    
    def send_command(self, command: str, params: Dict[str, Any] = None) -> bool:
        """Send command to remote device"""
        if not self.is_connected:
            print("Not connected, cannot send command")
            return False
            
        cmd_data = {
            'command': command,
            'params': params or {},
            'timestamp': datetime.now().isoformat()
        }
        
        return self.send_telemetry(cmd_data)