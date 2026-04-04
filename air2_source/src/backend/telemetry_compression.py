"""
Telemetry Compression Module
Advanced compression for telemetry data transmission
"""

import numpy as np
import zlib
import json
import struct
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging


class CompressionType(Enum):
    """Compression algorithms"""
    NONE = "none"
    ZLIB = "zlib"
    LZ4 = "lz4"
    PNG = "png"
    CUSTOM = "custom"


class TelemetryCompressor:
    """Compress telemetry data"""
    
    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level
        self.compression_stats = {
            'original_size': 0,
            'compressed_size': 0,
            'packets_compressed': 0
        }
    
    def compress(self, data: Dict) -> bytes:
        """Compress telemetry data"""
        # Convert to bytes
        json_data = json.dumps(data, default=str)
        json_bytes = json_data.encode('utf-8')
        
        self.compression_stats['original_size'] += len(json_bytes)
        
        # Compress
        compressed = zlib.compress(json_bytes, level=self.compression_level)
        
        self.compression_stats['compressed_size'] += len(compressed)
        self.compression_stats['packets_compressed'] += 1
        
        return compressed
    
    def decompress(self, compressed: bytes) -> Dict:
        """Decompress telemetry data"""
        decompressed = zlib.decompress(compressed)
        return json.loads(decompressed.decode('utf-8'))
    
    def get_ratio(self) -> float:
        """Get compression ratio"""
        if self.compression_stats['original_size'] > 0:
            return self.compression_stats['compressed_size'] / self.compression_stats['original_size']
        return 1.0


class DifferentialEncoder:
    """Differential encoding for time series"""
    
    def __init__(self):
        self.last_values = {}
    
    def encode(self, data: Dict) -> Dict:
        """Encode with differential"""
        encoded = {}
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if key in self.last_values:
                    encoded[key] = value - self.last_values[key]
                else:
                    encoded[key] = value
                self.last_values[key] = value
            else:
                encoded[key] = value
        
        return encoded
    
    def decode(self, data: Dict) -> Dict:
        """Decode differential"""
        decoded = {}
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if key in self.last_values:
                    decoded[key] = self.last_values[key] + value
                else:
                    decoded[key] = value
                self.last_values[key] = decoded[key]
            else:
                decoded[key] = value
        
        return decoded


class RunLengthEncoder:
    """Run-length encoding for repetitive data"""
    
    def encode(self, data: List) -> List:
        """Encode with run-length"""
        if not data:
            return []
        
        encoded = []
        current = data[0]
        count = 1
        
        for value in data[1:]:
            if value == current:
                count += 1
            else:
                encoded.append((current, count))
                current = value
                count = 1
        
        encoded.append((current, count))
        return encoded
    
    def decode(self, encoded: List) -> List:
        """Decode run-length"""
        decoded = []
        
        for value, count in encoded:
            decoded.extend([value] * count)
        
        return decoded


class DeltaEncoder:
    """Delta encoding for monotonic data"""
    
    def __init__(self):
        self.first_value = None
    
    def encode(self, data: List[float]) -> List[float]:
        """Encode with delta"""
        if not data:
            return []
        
        self.first_value = data[0]
        encoded = [data[0]]
        
        for i in range(1, len(data)):
            encoded.append(data[i] - data[i-1])
        
        return encoded
    
    def decode(self, encoded: List[float]) -> List[float]:
        """Decode delta"""
        if not encoded:
            return []
        
        self.first_value = encoded[0]
        decoded = [encoded[0]]
        
        for i in range(1, len(encoded)):
            decoded.append(decoded[-1] + encoded[i])
        
        return decoded


class HuffmanEncoder:
    """Huffman encoding for efficient storage"""
    
    def __init__(self):
        self.frequency = {}
        self.codes = {}
    
    def build_tree(self, data: List):
        """Build Huffman tree"""
        # Count frequencies
        for value in data:
            self.frequency[value] = self.frequency.get(value, 0) + 1
        
        # Build tree (simplified)
        self.codes = {k: bin(i)[2:] for i, k in enumerate(self.frequency.keys())}
    
    def encode(self, data: List) -> Tuple[str, Dict]:
        """Encode data"""
        self.build_tree(data)
        
        encoded = ''.join(self.codes.get(v, '') for v in data)
        
        return encoded, self.codes
    
    def decode(self, encoded: str, codes: Dict) -> List:
        """Decode data"""
        # Build reverse lookup
        reverse = {v: k for k, v in codes.items()}
        
        decoded = []
        current = ''
        
        for bit in encoded:
            current += bit
            if current in reverse:
                decoded.append(reverse[current])
                current = ''
        
        return decoded


class Quantizer:
    """Quantize float data"""
    
    def __init__(self, bits: int = 8):
        self.bits = bits
        self.levels = 2 ** bits
        self.min_val = None
        self.max_val = None
    
    def fit(self, data: List[float]):
        """Fit quantizer to data"""
        self.min_val = min(data)
        self.max_val = max(data)
    
    def encode(self, data: List[float]) -> List[int]:
        """Quantize data"""
        if self.min_val is None:
            self.fit(data)
        
        range_val = self.max_val - self.min_val
        if range_val == 0:
            return [self.levels // 2] * len(data)
        
        quantized = []
        
        for value in data:
            # Normalize to 0-1
            normalized = (value - self.min_val) / range_val
            # Quantize
            level = int(normalized * (self.levels - 1))
            quantized.append(level)
        
        return quantized
    
    def decode(self, quantized: List[int]) -> List[float]:
        """Dequantize data"""
        if self.min_val is None:
            return []
        
        range_val = self.max_val - self.min_val
        
        return [
            self.min_val + (q / (self.levels - 1)) * range_val
            for q in quantized
        ]


class PacketBuilder:
    """Build compressed telemetry packets"""
    
    def __init__(self):
        self.compressor = TelemetryCompressor()
        self.delta_encoder = DeltaEncoder()
        self.quantizer = Quantizer(bits=8)
    
    def build_packet(self, telemetry: Dict) -> bytes:
        """Build compressed packet"""
        
        # Encode
        encoded = self.delta_encoder.encode(telemetry)
        
        # Quantize numeric values
        for key in encoded:
            if isinstance(encoded[key], float):
                # Simple quantization by rounding
                encoded[key] = round(encoded[key], 2)
        
        # Compress
        compressed = self.compressor.compress(encoded)
        
        return compressed
    
    def parse_packet(self, packet: bytes) -> Dict:
        """Parse compressed packet"""
        
        # Decompress
        decompressed = self.compressor.decompress(packet)
        
        # Decode
        decoded = self.delta_encoder.decode(decompressed)
        
        return decoded


class AdaptiveCompressor:
    """Adaptive compression based on data characteristics"""
    
    def __init__(self):
        self.compressors = {
            'json': TelemetryCompressor(),
            'binary': None  # Add binary compressor
        }
        self.best_compressor = 'json'
    
    def compress(self, data: Dict) -> Tuple[bytes, str]:
        """Compress with best method"""
        
        # Try each compressor
        best_size = float('inf')
        best_data = None
        best_type = 'json'
        
        for name, compressor in self.compressors.items():
            if compressor is not None:
                try:
                    compressed = compressor.compress(data)
                    if len(compressed) < best_size:
                        best_size = len(compressed)
                        best_data = compressed
                        best_type = name
                except:
                    pass
        
        return best_data, best_type
    
    def decompress(self, data: bytes, comp_type: str) -> Dict:
        """Decompress"""
        if comp_type == 'json':
            return self.compressors['json'].decompress(data)
        return {}


# Example usage
if __name__ == "__main__":
    print("Testing Telemetry Compression...")
    
    # Test basic compression
    print("\n1. Testing Basic Compression...")
    comp = TelemetryCompressor()
    data = {'altitude': 1000.5, 'velocity': 50.2, 'temp': 25.0}
    compressed = comp.compress(data)
    decompressed = comp.decompress(compressed)
    print(f"   Ratio: {comp.get_ratio():.2%}")
    
    # Test differential encoding
    print("\n2. Testing Differential Encoding...")
    diff = DifferentialEncoder()
    encoded = diff.encode({'value': 100, 'value': 110, 'value': 120})
    decoded = diff.decode(encoded)
    print(f"   Encoded: {encoded}")
    
    # Test quantizer
    print("\n3. Testing Quantizer...")
    quant = Quantizer(bits=4)
    data = [0.0, 0.25, 0.5, 0.75, 1.0]
    quantized = quant.encode(data)
    decoded = quant.decode(quantized)
    print(f"   Original: {data}")
    print(f"   Decoded: {decoded}")
    
    # Test packet builder
    print("\n4. Testing Packet Builder...")
    builder = PacketBuilder()
    telemetry = {
        'altitude': 1000,
        'velocity': 50,
        'temperature': 25
    }
    packet = builder.build_packet(telemetry)
    parsed = builder.parse_packet(packet)
    print(f"   Packet size: {len(packet)} bytes")
    
    print("\n✅ Telemetry Compression test completed!")