"""
Data Compression Module - Full Implementation
Onboard compression, packetization, and time sync
"""

import zlib
import struct
import time
from typing import Dict, List, Tuple
from collections import deque


class RunLengthEncoder:
    """Run-length encoding for telemetry"""
    
    def __init__(self):
        pass
    
    def encode(self, data: List[float]) -> List[Tuple]:
        """Encode data with RLE"""
        if not data:
            return []
        
        encoded = []
        current_val = data[0]
        count = 1
        
        for i in range(1, len(data)):
            if data[i] == current_val:
                count += 1
            else:
                encoded.append((current_val, count))
                current_val = data[i]
                count = 1
        
        encoded.append((current_val, count))
        return encoded
    
    def decode(self, encoded: List[Tuple]) -> List[float]:
        """Decode RLE data"""
        decoded = []
        for val, count in encoded:
            decoded.extend([val] * count)
        return decoded


class DeltaEncoder:
    """Delta encoding for sequential data"""
    
    def __init__(self):
        self.last_value = 0
    
    def encode(self, data: List[float]) -> List[float]:
        """Encode with delta"""
        encoded = []
        self.last_value = 0
        
        for val in data:
            delta = val - self.last_value
            encoded.append(delta)
            self.last_value = val
        
        return encoded
    
    def decode(self, encoded: List[float]) -> List[float]:
        """Decode delta"""
        decoded = []
        self.last_value = 0
        
        for delta in encoded:
            val = self.last_value + delta
            decoded.append(val)
            self.last_value = val
        
        return decoded


class HuffmanCoder:
    """Huffman coding for compression"""
    
    def __init__(self):
        self.tree = {}
        self.frequency = {}
    
    def build_tree(self, data: List):
        """Build Huffman tree"""
        
        # Count frequencies
        for item in data:
            self.frequency[item] = self.frequency.get(item, 0) + 1
        
        # Simple placeholder - real implementation would build proper tree
        return self.frequency
    
    def encode(self, data: List) -> bytes:
        """Encode data"""
        # Use zlib as practical compression
        return zlib.compress(str(data).encode())
    
    def decode(self, encoded: bytes) -> List:
        """Decode data"""
        return eval(zlib.decompress(encoded).decode())


class TelemetryPacker:
    """Pack telemetry into efficient binary format"""
    
    def __init__(self):
        self.format_specs = {
            'altitude': ('H', 1000, 0, 50000),    # uint16, scale, offset, max
            'temperature': ('h', 100, -40, 160),  # int16, scale, offset, max
            'pressure': ('I', 10, 80000, 120000), # uint32, scale, offset, max
            'voltage': ('H', 1000, 0, 12),        # uint16, scale
            'latitude': ('i', 10000000, 0, 180),   # int32
            'longitude': ('i', 10000000, 0, 180),
        }
    
    def pack(self, telemetry: Dict) -> bytes:
        """Pack telemetry into binary"""
        
        packed = b''
        
        for key, value in telemetry.items():
            if key in self.format_specs and value is not None:
                fmt, scale = self.format_specs[key][0], self.format_specs[key][1]
                
                # Quantize
                quantized = int(value * scale)
                
                # Pack
                packed += struct.pack(fmt, quantized)
        
        return packed
    
    def unpack(self, packed: bytes, keys: List[str]) -> Dict:
        """Unpack binary telemetry"""
        
        telemetry = {}
        pos = 0
        
        for key in keys:
            if key in self.format_specs:
                fmt = self.format_specs[key][0]
                size = struct.calcsize(fmt)
                
                if pos + size <= len(packed):
                    value = struct.unpack(fmt, packed[pos:pos+size])[0]
                    scale = self.format_specs[key][1]
                    telemetry[key] = value / scale
                    pos += size
        
        return telemetry


class TimeSynchronizer:
    """Precise time synchronization for telemetry"""
    
    def __init__(self):
        self.local_offset = 0
        self.drift_rate = 0
        self.samples = deque(maxlen=20)
        self.last_sync = None
    
    def sync(self, remote_timestamp: float, local_timestamp: float = None):
        """Synchronize with remote"""
        
        if local_timestamp is None:
            local_timestamp = time.time()
        
        # Calculate offset
        offset = remote_timestamp - local_timestamp
        self.samples.append(offset)
        
        # Update offset (moving average)
        self.local_offset = sum(self.samples) / len(self.samples)
        
        self.last_sync = local_timestamp
    
    def get_synced_time(self, local_time: float = None) -> float:
        """Get time-synchronized timestamp"""
        
        if local_time is None:
            local_time = time.time()
        
        # Apply offset
        return local_time + self.local_offset
    
    def get_drift(self) -> float:
        """Get clock drift rate"""
        
        if len(self.samples) < 2:
            return 0
        
        # Simple drift calculation
        return (self.samples[-1] - self.samples[0]) / len(self.samples)


class CircularBuffer:
    """Efficient circular buffer for data logging"""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.buffer = []
        self.head = 0
    
    def append(self, item):
        """Append item"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(item)
        else:
            self.buffer[self.head] = item
            self.head = (self.head + 1) % self.capacity
    
    def get_all(self) -> List:
        """Get all items in order"""
        if len(self.buffer) < self.capacity:
            return self.buffer.copy()
        
        return self.buffer[self.head:] + self.buffer[:self.head]
    
    def get_latest(self, n: int) -> List:
        """Get n latest items"""
        items = self.get_all()
        return items[-n:] if len(items) > n else items


class DataValidator:
    """Validate and sanitize telemetry data"""
    
    def __init__(self):
        self.ranges = {
            'altitude': (-100, 50000),
            'temperature': (-50, 150),
            'pressure': (0, 120000),
            'battery': (0, 12),
            'voc': (0, 10000),
            'radiation': (0, 100),
            'latitude': (-90, 90),
            'longitude': (-180, 180),
        }
    
    def validate(self, telemetry: Dict) -> Tuple[bool, Dict]:
        """Validate telemetry"""
        
        valid = True
        sanitized = {}
        errors = []
        
        for key, value in telemetry.items():
            if value is None:
                continue
            
            if key in self.ranges:
                min_val, max_val = self.ranges[key]
                
                if value < min_val or value > max_val:
                    errors.append(f"{key} out of range: {value}")
                    valid = False
                    value = max(min_val, min(max_val, value))  # Clamp
            
            sanitized[key] = value
        
        return valid, sanitized
    
    def detect_gaps(self, telemetry_list: List[Dict], 
                   expected_interval: float = 0.2) -> List[Dict]:
        """Detect gaps in telemetry"""
        
        gaps = []
        
        for i in range(1, len(telemetry_list)):
            t1 = telemetry_list[i-1].get('timestamp', 0)
            t2 = telemetry_list[i].get('timestamp', 0)
            
            if t2 > 0 and t1 > 0:
                delta = t2 - t1
                
                if delta > expected_interval * 1.5:
                    gaps.append({
                        'index': i,
                        'gap_seconds': delta,
                        'expected_interval': expected_interval
                    })
        
        return gaps


class ChecksumVerifier:
    """Verify data integrity"""
    
    @staticmethod
    def crc16(data: bytes) -> int:
        """Calculate CRC-16"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    @staticmethod
    def crc32(data: bytes) -> int:
        """Calculate CRC-32"""
        return zlib.crc32(data) & 0xFFFFFFFF
    
    @staticmethod
    def fletcher16(data: bytes) -> int:
        """Fletcher-16 checksum"""
        sum1 = 0
        sum2 = 0
        
        for byte in data:
            sum1 = (sum1 + byte) % 255
            sum2 = (sum2 + sum1) % 255
        
        return (sum2 << 8) | sum1
    
    def verify(self, data: bytes, checksum: int, method: str = 'crc16') -> bool:
        """Verify checksum"""
        
        if method == 'crc16':
            return self.crc16(data) == checksum
        elif method == 'crc32':
            return self.crc32(data) == checksum
        elif method == 'fletcher':
            return self.fletcher16(data) == checksum
        
        return False


# Example
if __name__ == "__main__":
    # Test compression
    rle = RunLengthEncoder()
    data = [1.0, 1.0, 1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 3.0]
    encoded = rle.encode(data)
    print(f"RLE encoded: {encoded}")
    
    # Test packer
    packer = TelemetryPacker()
    telemetry = {'altitude': 1000, 'temperature': 25.5, 'pressure': 101325}
    packed = packer.pack(telemetry)
    print(f"Packed size: {len(packed)} bytes")
    
    # Test sync
    sync = TimeSynchronizer()
    sync.sync(1000.0, 1000.0)
    print(f"Synced time: {sync.get_synced_time()}")