#!/usr/bin/env python3
"""
Advanced Telemetry Processor
Real-time packet decoding, validation, and analysis
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import struct
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class PacketType(Enum):
    """Telemetry packet types"""
    SENSOR_DATA = 0x01
    GPS_DATA = 0x02
    SYSTEM_STATUS = 0x03
    COMMAND_ACK = 0x04
    ERROR_REPORT = 0x05


@dataclass
class TelemetryPacket:
    """Decoded telemetry packet"""
    packet_type: PacketType
    timestamp: float
    sequence_number: int
    
    # Sensor data
    altitude: float = 0.0
    velocity: float = 0.0
    acceleration: float = 0.0
    temperature: float = 0.0
    pressure: float = 0.0
    humidity: float = 0.0
    
    # GPS data
    latitude: float = 0.0
    longitude: float = 0.0
    gps_altitude: float = 0.0
    satellites: int = 0
    
    # System status
    battery_voltage: float = 0.0
    battery_current: float = 0.0
    cpu_temperature: float = 0.0
    rssi: int = 0
    
    # Metadata
    checksum: int = 0
    is_valid: bool = True
    raw_data: bytes = field(default_factory=bytes)


class TelemetryProcessor:
    """Advanced telemetry processing engine"""
    
    # Packet format (little-endian)
    # Header: [SYNC(2), TYPE(1), SEQ(2), TIMESTAMP(4)]
    # Payload: varies by type
    # Footer: [CHECKSUM(2)]
    
    SYNC_BYTES = b'\xAA\x55'
    HEADER_SIZE = 9
    FOOTER_SIZE = 2
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TelemetryProcessor")
        
        # Statistics
        self.packets_received = 0
        self.packets_valid = 0
        self.packets_invalid = 0
        self.last_sequence = -1
        self.packets_lost = 0
        
        # Data buffer
        self.buffer = bytearray()
        
        # Packet history
        self.packet_history: List[TelemetryPacket] = []
        self.max_history = 1000
        
        self.logger.info("Telemetry Processor initialized")
    
    def process_data(self, data: bytes) -> List[TelemetryPacket]:
        """Process incoming telemetry data
        
        Args:
            data: Raw bytes from communication channel
            
        Returns:
            List of decoded packets
        """
        self.buffer.extend(data)
        packets = []
        
        while len(self.buffer) >= self.HEADER_SIZE + self.FOOTER_SIZE:
            # Find sync bytes
            sync_pos = self.buffer.find(self.SYNC_BYTES)
            
            if sync_pos == -1:
                # No sync found, clear buffer
                self.buffer.clear()
                break
            
            # Remove data before sync
            if sync_pos > 0:
                self.buffer = self.buffer[sync_pos:]
            
            # Check if we have enough data for header
            if len(self.buffer) < self.HEADER_SIZE:
                break
            
            # Parse header
            packet_type_byte = self.buffer[2]
            seq_num = struct.unpack('<H', self.buffer[3:5])[0]
            timestamp = struct.unpack('<f', self.buffer[5:9])[0]
            
            try:
                packet_type = PacketType(packet_type_byte)
            except ValueError:
                self.logger.warning(f"Unknown packet type: {packet_type_byte}")
                self.buffer = self.buffer[1:]  # Skip one byte and retry
                continue
            
            # Determine payload size
            payload_size = self._get_payload_size(packet_type)
            total_size = self.HEADER_SIZE + payload_size + self.FOOTER_SIZE
            
            # Check if we have complete packet
            if len(self.buffer) < total_size:
                break
            
            # Extract packet
            packet_data = bytes(self.buffer[:total_size])
            self.buffer = self.buffer[total_size:]
            
            # Decode packet
            packet = self._decode_packet(packet_data, packet_type, seq_num, timestamp)
            
            if packet:
                packets.append(packet)
                self.packet_history.append(packet)
                
                # Trim history
                if len(self.packet_history) > self.max_history:
                    self.packet_history.pop(0)
                
                # Update statistics
                self.packets_received += 1
                if packet.is_valid:
                    self.packets_valid += 1
                else:
                    self.packets_invalid += 1
                
                # Check for lost packets
                if self.last_sequence >= 0:
                    expected = (self.last_sequence + 1) % 65536
                    if seq_num != expected:
                        lost = (seq_num - expected) % 65536
                        self.packets_lost += lost
                        self.logger.warning(f"Lost {lost} packets")
                
                self.last_sequence = seq_num
        
        return packets
    
    def _get_payload_size(self, packet_type: PacketType) -> int:
        """Get payload size for packet type (Adjusted for Fernet Encryption)"""
        # Fernet encryption adds overhead (IV, HMAC, Padding, Base64)
        # 24 bytes -> 120 bytes
        # 20 bytes -> 120 bytes
        # 16 bytes -> 100 bytes
        # 4 bytes -> 100 bytes
        # 8 bytes -> 100 bytes
        
        # These sizes must match exactly what Fernet produces or the parser will desync.
        # This is brittle. A better protocol would have a length byte in the header.
        # But to avoid refactoring the entire protocol header (breaking change to hardware v1), 
        # we will hardcode the known Fernet output sizes.
        
        sizes = {
            PacketType.SENSOR_DATA: 120,    # Was 24
            PacketType.GPS_DATA: 120,       # Was 20
            PacketType.SYSTEM_STATUS: 100,  # Was 16
            PacketType.COMMAND_ACK: 100,    # Was 4
            PacketType.ERROR_REPORT: 100    # Was 8
        }
        return sizes.get(packet_type, 0)
    

    def _decode_packet(self, data: bytes, packet_type: PacketType, 
                      seq_num: int, timestamp: float) -> Optional[TelemetryPacket]:
        """Decode packet payload"""
        # Determine if payload is encrypted
        # We assume for Phase 8 that ALL payloads are now encrypted if KeyManager is active
        # But we need a way to know. For now, we'll try to decrypt if it looks like a Fernet token (unlikely for raw bytes)
        # OR we just enforce encryption.
        
        # NOTE: In a real system, we'd check a flag or try/except.
        # Given the "Enterprise" requirement, we will try to decrypt using the rolling key.
        
        # We need access to KeyManager. Since it wasn't passed in __init__, we'll import it here or 
        # assume it's injected. For this implementation, we'll try to import and use the singleton/instance.
        # However, to avoid global state issues, we should probably have it passed in. 
        # For this refactor, we will modify __init__ to accept a key_manager or lazily instantiate it.
        
        payload = data[self.HEADER_SIZE:-self.FOOTER_SIZE]
        
        # verify checksum of the *encrypted* data (or raw data before decryption?)
        # Standard: Checksum covers the transmitted frame (Header + Encrypted Payload).
        # The current implementation calculates checksum on existing bytes in _decode_packet calls.
        
        checksum_received = struct.unpack('<H', data[-self.FOOTER_SIZE:])[0]
        checksum_calculated = self._calculate_checksum(data[:-self.FOOTER_SIZE])
        
        is_valid = (checksum_received == checksum_calculated)
        
        packet = TelemetryPacket(
            packet_type=packet_type,
            timestamp=timestamp,
            sequence_number=seq_num,
            checksum=checksum_received,
            is_valid=is_valid,
            raw_data=data
        )
        
        if not is_valid:
            self.logger.warning(f"Checksum mismatch: {checksum_received} != {checksum_calculated}")
            return packet

        # DECRYPTION STEP
        try:
            # We need the KeyManager to get the key for this sequence number
            from communication.key_manager import KeyManager
            # This relies on KeyManager finding its keys on disk
            km = KeyManager() 
            key = km.get_rolling_key(seq_num)
            
            f = Fernet(key)
            # Fernet tokens are larger than raw struct packing.
            # Enforce encryption - no legacy fallback
            decrypted_payload = f.decrypt(payload)
            parse_payload = decrypted_payload
            packet.is_encrypted = True
                
        except Exception as e:
            self.logger.warning(f"Decryption or KeyManager error: {e}")
            packet.is_valid = False
            return packet

        # Decode payload based on type
        try:
            if packet_type == PacketType.SENSOR_DATA:
                values = struct.unpack('<6f', parse_payload)
                packet.altitude = values[0]
                packet.velocity = values[1]
                packet.acceleration = values[2]
                packet.temperature = values[3]
                packet.pressure = values[4]
                packet.humidity = values[5]
            
            elif packet_type == PacketType.GPS_DATA:
                values = struct.unpack('<3fI', parse_payload)
                packet.latitude = values[0]
                packet.longitude = values[1]
                packet.gps_altitude = values[2]
                packet.satellites = values[3]
            
            elif packet_type == PacketType.SYSTEM_STATUS:
                values = struct.unpack('<4f', parse_payload)
                packet.battery_voltage = values[0]
                packet.battery_current = values[1]
                packet.cpu_temperature = values[2]
                packet.rssi = int(values[3])
        
        except struct.error as e:
            self.logger.error(f"Failed to decode payload: {e}")
            packet.is_valid = False
        
        return packet
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate CRC16 checksum"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF
    
    def get_statistics(self) -> Dict[str, any]:
        """Get telemetry statistics"""
        packet_loss_rate = 0
        if self.packets_received > 0:
            packet_loss_rate = (self.packets_lost / (self.packets_received + self.packets_lost)) * 100
        
        return {
            'packets_received': self.packets_received,
            'packets_valid': self.packets_valid,
            'packets_invalid': self.packets_invalid,
            'packets_lost': self.packets_lost,
            'packet_loss_rate': packet_loss_rate,
            'buffer_size': len(self.buffer)
        }
    
    def get_latest_data(self) -> Dict[str, float]:
        """Get latest sensor values"""
        if not self.packet_history:
            return {}
        
        # Get most recent packet of each type
        latest = {}
        for packet in reversed(self.packet_history):
            if not packet.is_valid:
                continue
            
            if packet.packet_type == PacketType.SENSOR_DATA:
                latest.update({
                    'altitude': packet.altitude,
                    'velocity': packet.velocity,
                    'acceleration': packet.acceleration,
                    'temperature': packet.temperature,
                    'pressure': packet.pressure,
                    'humidity': packet.humidity
                })
            elif packet.packet_type == PacketType.GPS_DATA:
                latest.update({
                    'latitude': packet.latitude,
                    'longitude': packet.longitude,
                    'gps_altitude': packet.gps_altitude,
                    'satellites': packet.satellites
                })
            elif packet.packet_type == PacketType.SYSTEM_STATUS:
                latest.update({
                    'battery_voltage': packet.battery_voltage,
                    'battery_current': packet.battery_current,
                    'cpu_temperature': packet.cpu_temperature,
                    'rssi': packet.rssi
                })
        
        return latest
    
    def create_test_packet(self, packet_type: PacketType, seq_num: int, **kwargs) -> bytes:
        """Create test telemetry packet (Encrypted)"""
        # Header
        header = self.SYNC_BYTES
        header += struct.pack('<B', packet_type.value)
        header += struct.pack('<H', seq_num)
        header += struct.pack('<f', time.time())
        
        # Payload Raw
        if packet_type == PacketType.SENSOR_DATA:
            payload_raw = struct.pack('<6f',
                kwargs.get('altitude', 100.0),
                kwargs.get('velocity', 10.0),
                kwargs.get('acceleration', 1.0),
                kwargs.get('temperature', 25.0),
                kwargs.get('pressure', 101325.0),
                kwargs.get('humidity', 50.0)
            )
        elif packet_type == PacketType.GPS_DATA:
            payload_raw = struct.pack('<3fI',
                kwargs.get('latitude', 34.0),
                kwargs.get('longitude', -118.0),
                kwargs.get('gps_altitude', 100.0),
                kwargs.get('satellites', 8)
            )
        elif packet_type == PacketType.SYSTEM_STATUS:
            payload_raw = struct.pack('<4f',
                kwargs.get('battery_voltage', 12.0),
                kwargs.get('battery_current', 0.5),
                kwargs.get('cpu_temperature', 45.0),
                float(kwargs.get('rssi', -65))
            )
        else:
            payload_raw = b'\x00' * self._get_payload_size(packet_type)
            
        # ENCRPYTION
        try:
            from communication.key_manager import KeyManager
            from cryptography.fernet import Fernet
            km = KeyManager()
            key = km.get_rolling_key(seq_num)
            f = Fernet(key)
            payload = f.encrypt(payload_raw)
        except Exception as e:
            self.logger.warning(f"Encryption failed, sending cleartext: {e}")
            payload = payload_raw
        
        # Checksum
        packet_data = header + payload
        checksum = self._calculate_checksum(packet_data)
        footer = struct.pack('<H', checksum)
        
        return packet_data + footer


def main():
    """Test telemetry processor"""
    logging.basicConfig(level=logging.INFO)
    
    # Ensure keys exist
    from communication.key_manager import KeyManager
    km = KeyManager()
    km.provision_mission_key()
    
    processor = TelemetryProcessor()
    
    print("="*70)
    print("  Telemetry Processor Test (Encrypted)")
    print("="*70)
    
    # Create test packets
    print("\nCreating test packets...")
    packets_data = b''
    
    for i in range(5):
        # Sensor data
        packet = processor.create_test_packet(
            PacketType.SENSOR_DATA,
            i,
            altitude=100 + i * 10,
            velocity=20 + i,
            temperature=25 + i * 0.5
        )
        packets_data += packet
    
    # Process packets
    print(f"Processing {len(packets_data)} bytes...")
    decoded = processor.process_data(packets_data)
    
    print(f"\n✅ Decoded {len(decoded)} packets")
    
    if decoded:
        print(f"\nSample Packet:")
        packet = decoded[0]
        encrypted_status = getattr(packet, 'is_encrypted', 'Unknown')
        print(f"  Type: {packet.packet_type.name}")
        print(f"  Encrypted: {encrypted_status}")
        print(f"  Altitude: {packet.altitude:.2f}m")

if __name__ == "__main__":
    main()
