"""
Communication Protocol Module for AirOne Professional
Defines communication protocols and packet structures
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import time


@dataclass
class CommunicationPacket:
    """Represents a communication packet"""
    packet_id: str
    timestamp: float
    source: str
    destination: str
    packet_type: str
    payload: Dict[str, Any]
    checksum: str = ""
    sequence_number: int = 0
    
    def __post_init__(self):
        # Automatically calculate checksum if not provided
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate CRC32 checksum of the packet's core data."""
        # Use a simplified approach with CRC32 for example
        import zlib
        # Exclude checksum itself from calculation
        data_to_hash = json.dumps({
            'packet_id': self.packet_id,
            'timestamp': self.timestamp,
            'source': self.source,
            'destination': self.destination,
            'packet_type': self.packet_type,
            'payload': self.payload,
            'sequence_number': self.sequence_number
        }).encode('utf-8')
        return str(zlib.crc32(data_to_hash))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to dictionary"""
        return {
            'packet_id': self.packet_id,
            'timestamp': self.timestamp,
            'source': self.source,
            'destination': self.destination,
            'packet_type': self.packet_type,
            'payload': self.payload,
            'checksum': self.checksum,
            'sequence_number': self.sequence_number
        }
    
    def to_json(self) -> str:
        """Convert packet to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommunicationPacket':
        """Create packet from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CommunicationPacket':
        """Create packet from JSON string"""
        return cls.from_dict(json.loads(json_str))


class ProtocolHandler:
    """Base protocol handler"""
    
    def __init__(self, protocol_name: str):
        self.protocol_name = protocol_name
        self.initialized = False
        self.last_sequence_number = -1 # Track last seen sequence for basic check
        
    def initialize(self) -> bool:
        """Initialize protocol handler"""
        self.initialized = True
        return True
    
    def encode(self, data: Dict[str, Any]) -> bytes:
        """Encode data to bytes"""
        # Assume data is already a dict representation of CommunicationPacket
        packet = CommunicationPacket.from_dict(data)
        # Ensure checksum is calculated before encoding
        packet.checksum = packet._calculate_checksum()
        return json.dumps(asdict(packet)).encode('utf-8') # Use asdict for dataclass
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        """Decode bytes to data"""
        decoded_dict = json.loads(data.decode('utf-8'))
        return decoded_dict
    
    def validate(self, packet: CommunicationPacket) -> bool:
        """Validate packet integrity: checksum, timestamp, sequence number."""
        # 1. Checksum verification
        calculated_checksum = packet._calculate_checksum()
        if packet.checksum != calculated_checksum:
            print(f"Validation failed: Checksum mismatch for packet {packet.packet_id}")
            return False

        # 2. Timestamp check (e.g., not too far in the past or future)
        current_time = time.time()
        # Allow +/- 5 minutes for clock skew and network latency
        if not (current_time - 300 < packet.timestamp < current_time + 300):
            print(f"Validation failed: Timestamp out of range for packet {packet.packet_id}")
            return False

        # 3. Sequence number check (simple monotonic increase)
        if packet.sequence_number <= self.last_sequence_number:
            print(f"Validation failed: Sequence number not increasing for packet {packet.packet_id}")
            return False
        
        self.last_sequence_number = packet.sequence_number # Update last seen sequence
        return True


class TelemetryProtocol(ProtocolHandler):
    """Telemetry data protocol"""
    
    def __init__(self):
        super().__init__('telemetry')
        self.packet_count = 0
        
    def create_telemetry_packet(self, telemetry_data: Dict[str, Any]) -> CommunicationPacket:
        """Create a telemetry packet"""
        self.packet_count += 1
        
        return CommunicationPacket(
            packet_id=f"telem_{self.packet_count}_{int(time.time())}",
            timestamp=time.time(),
            source="ground_station",
            destination="canSat",
            packet_type="telemetry",
            payload=telemetry_data,
            sequence_number=self.packet_count
        )


class CommandProtocol(ProtocolHandler):
    """Command protocol"""
    
    def __init__(self):
        super().__init__('command')
        self.command_count = 0
        
    def create_command_packet(self, command: str, params: Dict[str, Any]) -> CommunicationPacket:
        """Create a command packet"""
        self.command_count += 1
        
        return CommunicationPacket(
            packet_id=f"cmd_{self.command_count}_{int(time.time())}",
            timestamp=time.time(),
            source="ground_station",
            destination="canSat",
            packet_type="command",
            payload={'command': command, 'params': params},
            sequence_number=self.command_count
        )


def create_protocol_handler(protocol_type: str) -> ProtocolHandler:
    """Factory function to create protocol handlers"""
    protocols = {
        'telemetry': TelemetryProtocol,
        'command': CommandProtocol,
        'default': ProtocolHandler
    }
    
    handler_class = protocols.get(protocol_type, ProtocolHandler)
    return handler_class()
