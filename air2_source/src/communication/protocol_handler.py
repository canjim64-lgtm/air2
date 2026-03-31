"""
Protocol Handler Module
Communication protocol implementation for telemetry
"""

import struct
import json
import hashlib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging


class PacketType(Enum):
    """Packet types"""
    TELEMETRY = 0x01
    COMMAND = 0x02
    ACK = 0x03
    NACK = 0x04
    HEARTBEAT = 0x05
    FILE_TRANSFER = 0x06
    CONFIG = 0x07
    STATUS = 0x08


class ProtocolVersion(Enum):
    """Protocol versions"""
    V1 = 1
    V2 = 2


@dataclass
class ProtocolHeader:
    """Protocol packet header"""
    version: int
    packet_type: int
    sequence: int
    length: int
    checksum: int


class ProtocolHandler:
    """Handle communication protocol"""
    
    def __init__(self, version: ProtocolVersion = ProtocolVersion.V2):
        self.version = version
        self.sequence = 0
        self.max_packet_size = 1024
        
    def create_packet(self, packet_type: PacketType, 
                    payload: bytes) -> bytes:
        """Create protocol packet"""
        
        # Header
        header = struct.pack('BBHI',
            self.version.value,
            packet_type.value,
            self.sequence,
            len(payload)
        )
        
        # Checksum
        checksum = self._calculate_checksum(payload)
        
        # Full packet
        packet = header + struct.pack('H', checksum) + payload
        
        self.sequence = (self.sequence + 1) % 65536
        
        return packet
    
    def parse_packet(self, packet: bytes) -> Optional[Tuple[ProtocolHeader, bytes]]:
        """Parse incoming packet"""
        
        if len(packet) < 10:
            return None
        
        try:
            # Parse header
            version, ptype, sequence, length = struct.unpack('BBHI', packet[:8])
            checksum = struct.unpack('H', packet[8:10])[0]
            
            # Parse payload
            payload = packet[10:10+length]
            
            # Verify checksum
            calc_checksum = self._calculate_checksum(payload)
            if checksum != calc_checksum:
                logging.warning("Checksum mismatch")
                return None
            
            header = ProtocolHeader(
                version=version,
                packet_type=ptype,
                sequence=sequence,
                length=length,
                checksum=checksum
            )
            
            return header, payload
            
        except Exception as e:
            logging.error(f"Parse error: {e}")
            return None
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate checksum"""
        return sum(data) % 65536


class TelemetryProtocol:
    """Telemetry data protocol"""
    
    def __init__(self):
        self.handler = ProtocolHandler()
        
    def encode_telemetry(self, data: Dict) -> bytes:
        """Encode telemetry data"""
        
        # Convert to JSON
        json_data = json.dumps(data, default=str)
        
        # Compress (simple)
        payload = json_data.encode('utf-8')
        
        # Create packet
        return self.handler.create_packet(PacketType.TELEMETRY, payload)
    
    def decode_telemetry(self, packet: bytes) -> Optional[Dict]:
        """Decode telemetry packet"""
        
        result = self.handler.parse_packet(packet)
        
        if result is None:
            return None
        
        header, payload = result
        
        # Parse JSON
        try:
            data = json.loads(payload.decode('utf-8'))
            return data
        except:
            return None


class CommandProtocol:
    """Command protocol"""
    
    def __init__(self):
        self.handler = ProtocolHandler()
        
    def encode_command(self, command: str, params: Dict = None) -> bytes:
        """Encode command"""
        
        cmd_data = {
            'command': command,
            'params': params or {}
        }
        
        json_data = json.dumps(cmd_data)
        payload = json_data.encode('utf-8')
        
        return self.handler.create_packet(PacketType.COMMAND, payload)
    
    def decode_command(self, packet: bytes) -> Optional[Dict]:
        """Decode command"""
        
        result = self.handler.parse_packet(packet)
        
        if result is None:
            return None
        
        header, payload = result
        
        try:
            cmd = json.loads(payload.decode('utf-8'))
            return cmd
        except:
            return None


class ACKProtocol:
    """Acknowledgment protocol"""
    
    def __init__(self):
        self.handler = ProtocolHandler()
        
    def create_ack(self, sequence: int, status: int = 0) -> bytes:
        """Create ACK packet"""
        
        payload = struct.pack('HH', sequence, status)
        
        return self.handler.create_packet(PacketType.ACK, payload)
    
    def create_nack(self, sequence: int, error_code: int) -> bytes:
        """Create NACK packet"""
        
        payload = struct.pack('HH', sequence, error_code)
        
        return self.handler.create_packet(PacketType.NACK, payload)
    
    def parse_response(self, packet: bytes) -> Optional[Tuple[int, int]]:
        """Parse ACK/NACK"""
        
        result = self.handler.parse_packet(packet)
        
        if result is None:
            return None
        
        header, payload = result
        
        sequence, status = struct.unpack('HH', payload)
        
        return sequence, status


class HeartbeatProtocol:
    """Heartbeat protocol"""
    
    def __init__(self):
        self.handler = ProtocolHandler()
        self.last_heartbeat = 0
        
    def create_heartbeat(self, status: Dict = None) -> bytes:
        """Create heartbeat"""
        
        status_data = json.dumps(status or {}).encode('utf-8')
        
        return self.handler.create_packet(PacketType.HEARTBEAT, status_data)
    
    def parse_heartbeat(self, packet: bytes) -> Optional[Dict]:
        """Parse heartbeat"""
        
        result = self.handler.parse_packet(packet)
        
        if result is None:
            return None
        
        header, payload = result
        
        self.last_heartbeat = header.sequence
        
        try:
            return json.loads(payload.decode('utf-8'))
        except:
            return {}


class FragmentationHandler:
    """Handle packet fragmentation"""
    
    def __init__(self, max_fragment_size: int = 256):
        self.max_fragment_size = max_fragment_size
        self.fragments = {}
        
    def fragment(self, packet: bytes) -> List[bytes]:
        """Fragment large packet"""
        
        fragments = []
        total_fragments = (len(packet) + self.max_fragment_size - 1) // self.max_fragment_size
        
        for i in range(total_fragments):
            start = i * self.max_fragment_size
            end = min(start + self.max_fragment_size, len(packet))
            
            # Fragment header: fragment_index, total_fragments, total_size
            fragment_header = struct.pack('HHI', 
                i, 
                total_fragments, 
                len(packet)
            )
            
            fragments.append(fragment_header + packet[start:end])
        
        return fragments
    
    def reassemble(self, fragment: bytes) -> Optional[bytes]:
        """Reassemble fragments"""
        
        frag_index, total_fragments, total_size = struct.unpack('HHI', fragment[:8])
        payload = fragment[8:]
        
        # Store fragment
        if frag_index not in self.fragments:
            self.fragments = {}
        
        self.fragments[frag_index] = (total_fragments, total_size, payload)
        
        # Check if complete
        if len(self.fragments) == total_fragments:
            # Reassemble
            packet = b''
            for i in range(total_fragments):
                packet += self.fragments[i][2]
            
            self.fragments.clear()
            return packet
        
        return None


class ProtocolValidator:
    """Validate protocol packets"""
    
    def __init__(self):
        self.expected_sequences = set()
        
    def validate_sequence(self, sequence: int) -> bool:
        """Validate sequence number"""
        
        if sequence in self.expected_sequences:
            self.expected_sequences.remove(sequence)
            return True
        
        # Allow some out-of-order
        if len(self.expected_sequences) < 10:
            self.expected_sequences.add(sequence)
            return True
        
        return False
    
    def validate_length(self, length: int, max_size: int = 2048) -> bool:
        """Validate packet length"""
        
        return 0 < length <= max_size
    
    def validate_checksum(self, data: bytes, checksum: int) -> bool:
        """Validate checksum"""
        
        calc = sum(data) % 65536
        return calc == checksum


class ProtocolManager:
    """Complete protocol management"""
    
    def __init__(self):
        self.telemetry = TelemetryProtocol()
        self.command = CommandProtocol()
        self.ack = ACKProtocol()
        self.heartbeat = HeartbeatProtocol()
        self.fragmentation = FragmentationHandler()
        self.validator = ProtocolValidator()
        
    def send_telemetry(self, data: Dict) -> bytes:
        """Send telemetry"""
        packet = self.telemetry.encode_telemetry(data)
        
        # Fragment if needed
        if len(packet) > 256:
            return self.fragmentation.fragment(packet)
        
        return [packet]
    
    def send_command(self, command: str, params: Dict = None) -> bytes:
        """Send command"""
        return self.command.encode_command(command, params)
    
    def handle_packet(self, packet: bytes) -> Optional[Dict]:
        """Handle incoming packet"""
        
        # Parse header
        result = self.telemetry.handler.parse_packet(packet)
        
        if result is None:
            return None
        
        header, payload = result
        
        # Validate
        if not self.validator.validate_sequence(header.sequence):
            return None
        
        # Route to appropriate handler
        ptype = PacketType(header.packet_type)
        
        if ptype == PacketType.TELEMETRY:
            return {'type': 'telemetry', 'data': self.telemetry.decode_telemetry(packet)}
        elif ptype == PacketType.COMMAND:
            return {'type': 'command', 'data': self.command.decode_command(packet)}
        elif ptype == PacketType.ACK:
            return {'type': 'ack'}
        elif ptype == PacketType.HEARTBEAT:
            return {'type': 'heartbeat', 'data': self.heartbeat.parse_heartbeat(packet)}
        
        return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Protocol Handler...")
    
    # Test Protocol Handler
    print("\n1. Testing Protocol Handler...")
    handler = ProtocolHandler()
    packet = handler.create_packet(PacketType.TELEMETRY, b"Test data")
    result = handler.parse_packet(packet)
    print(f"   Packet created: {len(packet)} bytes")
    print(f"   Parsed: {result is not None}")
    
    # Test Telemetry Protocol
    print("\n2. Testing Telemetry Protocol...")
    telemetry = TelemetryProtocol()
    data = {'altitude': 1000, 'velocity': 50}
    packet = telemetry.encode_telemetry(data)
    decoded = telemetry.decode_telemetry(packet)
    print(f"   Original: {data}")
    print(f"   Decoded: {decoded}")
    
    # Test Command Protocol
    print("\n3. Testing Command Protocol...")
    cmd = CommandProtocol()
    packet = cmd.encode_command('START_MISSION', {'param1': 10})
    decoded = cmd.decode_command(packet)
    print(f"   Command: {decoded}")
    
    # Test Fragmentation
    print("\n4. Testing Fragmentation...")
    frag = FragmentationHandler(max_fragment_size=50)
    large_data = b"X" * 200
    fragments = frag.fragment(large_data)
    print(f"   Original: {len(large_data)} bytes")
    print(f"   Fragments: {len(fragments)}")
    
    # Reassemble
    for f in fragments:
        result = frag.reassemble(f)
        if result:
            print(f"   Reassembled: {len(result)} bytes")
    
    # Test Complete Manager
    print("\n5. Testing Protocol Manager...")
    manager = ProtocolManager()
    packets = manager.send_telemetry({'test': 123})
    print(f"   Telemetry packets: {len(packets)}")
    
    print("\n✅ Protocol Handler test completed!")