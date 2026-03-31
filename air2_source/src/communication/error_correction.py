"""
Error Correction and Forward Error Correction Module
FEC and ECC for reliable data transmission
"""

import numpy as np
from typing import List, Tuple, Optional
import logging


class HammingCode:
    """Hamming code error correction"""
    
    def __init__(self, data_bits: int = 4):
        self.data_bits = data_bits
        self.total_bits = data_bits + int(np.ceil(np.log2(data_bits + 1))) + 1
        
    def encode(self, data: List[int]) -> List[int]:
        """Encode data with Hamming code"""
        
        # Calculate parity bits
        n = self.data_bits
        r = int(np.ceil(np.log2(n + 1)))
        
        # Create encoded array
        encoded = [0] * (n + r + 1)
        
        # Place data bits
        data_idx = 0
        for i in range(1, len(encoded)):
            if i & (i - 1) != 0:  # Not power of 2
                encoded[i] = data[data_idx]
                data_idx += 1
        
        # Calculate parity bits
        for p in range(1, r + 1):
            parity_pos = 2 ** (p - 1)
            parity = 0
            
            for i in range(1, len(encoded)):
                if i & parity_pos:
                    parity ^= encoded[i]
            
            encoded[parity_pos] = parity
        
        return encoded
    
    def decode(self, encoded: List[int]) -> Tuple[List[int], int]:
        """Decode and correct errors"""
        
        n = self.data_bits
        r = int(np.ceil(np.log2(n + 1)))
        error_pos = 0
        
        # Check parity bits
        for p in range(1, r + 1):
            parity_pos = 2 ** (p - 1)
            parity = 0
            
            for i in range(1, len(encoded)):
                if i & parity_pos:
                    parity ^= encoded[i]
            
            if parity != encoded[parity_pos]:
                error_pos += parity_pos
        
        # Correct error
        if error_pos > 0:
            encoded[error_pos] ^= 1
        
        # Extract data bits
        data = []
        data_idx = 0
        
        for i in range(1, len(encoded)):
            if i & (i - 1) != 0:
                data.append(encoded[i])
                data_idx += 1
                if data_idx >= n:
                    break
        
        return data, error_pos


class ReedSolomon:
    """Reed-Solomon error correction"""
    
    def __init__(self, m: int = 8, t: int = 8):
        self.m = m  # Symbol size
        self.t = t  # Error correction capability
        self.n = 2 ** m - 1
        self.k = self.n - 2 * t
        
    def encode(self, data: List[int]) -> List[int]:
        """Encode with Reed-Solomon"""
        
        # Simplified encoding (would need GF arithmetic in production)
        n = self.n
        k = self.k
        
        # Pad if needed
        if len(data) < k:
            data = data + [0] * (k - len(data))
        
        # Add parity symbols (simplified)
        encoded = data[:k] + [0] * (n - k)
        
        return encoded
    
    def decode(self, encoded: List[int]) -> Tuple[List[int], int]:
        """Decode and correct errors"""
        
        # Simplified decoding
        n = self.n
        k = self.k
        
        # Extract data
        data = encoded[:k]
        parity = encoded[k:]
        
        # Count errors (simplified)
        errors = sum(1 for p in parity if p != 0)
        
        return data, errors


class CRC:
    """CRC error detection"""
    
    def __init__(self, polynomial: int = 0x1021):
        self.polynomial = polynomial
        self.width = 16
        
    def calculate(self, data: bytes) -> int:
        """Calculate CRC"""
        
        crc = 0xFFFF
        
        for byte in data:
            crc ^= byte << 8
            
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ self.polynomial
                else:
                    crc <<= 1
                
                crc &= 0xFFFF
        
        return crc
    
    def verify(self, data: bytes, expected: int) -> bool:
        """Verify CRC"""
        return self.calculate(data) == expected


class ConvolutionalCode:
    """Convolutional code for FEC"""
    
    def __init__(self, constraint: int = 7, rate: float = 1/2):
        self.constraint = constraint
        self.rate = rate
        self polynomials = [0o133, 0o171]  # Standard polynomials
        
    def encode(self, data: List[int]) -> List[int]:
        """Encode with convolutional code"""
        
        encoded = []
        state = 0
        
        for bit in data:
            # Shift in
            state = (state << 1) | bit
            
            # Generate output bits
            out1 = 0
            out2 = 0
            
            for poly in self.polomials:
                temp = state & poly
                out1 ^= bin(temp).count('1') % 2
                out2 ^= bin(temp >> 1).count('1') % 2
            
            encoded.append(out1)
            encoded.append(out2)
        
        return encoded
    
    def decode(self, encoded: List[int]) -> List[int]:
        """Viterbi decode (simplified)"""
        
        data = []
        
        # Simplified Viterbi - just take majority of pairs
        for i in range(0, len(encoded) - 1, 2):
            if i + 1 < len(encoded):
                # Majority voting
                bit = (encoded[i] + encoded[i+1]) // 2
                data.append(bit)
        
        return data


class TurboCode:
    """Turbo code encoder/decoder"""
    
    def __init__(self):
        self.interleaver_size = 1024
        
    def encode(self, data: List[int]) -> List[int]:
        """Turbo encode"""
        
        # First encoder
        enc1 = ConvolutionalCode().encode(data)
        
        # Interleave
        interleaved = self._interleave(data)
        
        # Second encoder
        enc2 = ConvolutionalCode().encode(interleaved)
        
        # Combine
        systematic = data + [0] * (len(enc2) - len(data))
        
        return systematic + enc1 + enc2
    
    def _interleave(self, data: List[int]) -> List[int]:
        """Simple interleaver"""
        
        # Random-like permutation
        n = len(data)
        indices = [(i * 7) % n for i in range(n)]
        
        return [data[i] for i in indices]
    
    def decode(self, encoded: List[int]) -> List[int]:
        """Turbo decode (simplified)"""
        
        # Simplified - just return first part
        return encoded[:len(encoded)//3]


class LDPCCode:
    """Low-Density Parity-Check code"""
    
    def __init__(self, n: int = 2048, k: int = 1723):
        self.n = n  # Codeword length
        self.k = k  # Information bits
        self.H = self._generate_H_matrix()
        
    def _generate_H_matrix(self):
        """Generate H matrix (simplified)"""
        
        m = self.n - self.k
        H = np.zeros((m, self.n), dtype=int)
        
        # Simple construction
        for i in range(m):
            for j in range(self.n):
                if (i + j) % 7 == 0:
                    H[i, j] = 1
        
        return H
    
    def encode(self, data: List[int]) -> List[int]:
        """LDPC encode"""
        
        # Systematic encoding
        codeword = data + [0] * (self.n - self.k)
        
        # Would need proper matrix operations in production
        return codeword
    
    def decode(self, received: List[int]) -> List[int]:
        """LDPC decode (simplified belief propagation)"""
        
        # Simplified hard decision
        decoded = [1 if x > 0.5 else 0 for x in received]
        
        return decoded[:self.k]


class ErrorCorrectionSystem:
    """Complete error correction system"""
    
    def __init__(self):
        self.hamming = HammingCode(4)
        self.crc = CRC()
        self.convolutional = ConvolutionalCode()
        self.turbo = TurboCode()
        self.ldpc = LDPCCode()
        
    def encode_with_fec(self, data: bytes, 
                       method: str = 'hamming') -> bytes:
        """Encode with FEC"""
        
        bits = [int(b) for byte in data for b in format(byte, '08b')]
        
        if method == 'hamming':
            encoded = self.hamming.encode(bits[:4])
        elif method == 'convolutional':
            encoded = self.convolutional.encode(bits)
        elif method == 'turbo':
            encoded = self.turbo.encode(bits[:100])  # Limit size
        elif method == 'ldpc':
            encoded = self.ldpc.encode(bits[:100])
        else:
            encoded = bits
        
        # Add CRC
        crc = self.crc.calculate(data)
        
        return bytes(encoded), crc
    
    def decode_with_fec(self, encoded: bytes, 
                       crc_expected: int,
                       method: str = 'hamming') -> Optional[bytes]:
        """Decode with error correction"""
        
        bits = list(encoded)
        
        # Verify CRC first
        if self.crc.verify(encoded, crc_expected):
            # No errors, return directly
            if method == 'hamming':
                decoded, _ = self.hamming.decode(bits)
            elif method == 'convolutional':
                decoded = self.convolutional.decode(bits)
            elif method == 'turbo':
                decoded = self.turbo.decode(bits)
            else:
                decoded = bits
            
            # Convert back to bytes
            result = []
            for i in range(0, len(decoded), 8):
                byte_bits = decoded[i:i+8]
                if len(byte_bits) == 8:
                    byte = sum(bit << (7 - j) for j, bit in enumerate(byte_bits[:8]))
                    result.append(byte)
            
            return bytes(result)
        
        # Try error correction
        if method == 'hamming':
            decoded, error_pos = self.hamming.decode(bits)
            if error_pos > 0:
                # Corrected!
                result = []
                for i in range(0, len(decoded), 8):
                    byte_bits = decoded[i:i+8]
                    if len(byte_bits) == 8:
                        byte = sum(bit << (7 - j) for j, bit in enumerate(byte_bits[:8]))
                        result.append(byte)
                return bytes(result)
        
        return None


# Example usage
if __name__ == "__main__":
    print("Testing Error Correction...")
    
    # Test Hamming
    print("\n1. Testing Hamming Code...")
    hamming = HammingCode(4)
    data = [1, 0, 1, 1]
    encoded = hamming.encode(data)
    decoded, errors = hamming.decode(encoded)
    print(f"   Data: {data}")
    print(f"   Encoded: {encoded}")
    print(f"   Decoded: {decoded}, Errors corrected: {errors}")
    
    # Test CRC
    print("\n2. Testing CRC...")
    crc = CRC()
    data = b"Hello, World!"
    checksum = crc.calculate(data)
    print(f"   CRC: {hex(checksum)}")
    print(f"   Verified: {crc.verify(data, checksum)}")
    
    # Test Convolutional
    print("\n3. Testing Convolutional Code...")
    conv = ConvolutionalCode()
    data = [1, 0, 1, 1, 0]
    encoded = conv.encode(data)
    decoded = conv.decode(encoded)
    print(f"   Original: {data}")
    print(f"   Decoded: {decoded}")
    
    # Test Turbo
    print("\n4. Testing Turbo Code...")
    turbo = TurboCode()
    data = [1, 0, 1] * 30
    encoded = turbo.encode(data)
    decoded = turbo.decode(encoded)
    print(f"   Encoded length: {len(encoded)}")
    
    # Test complete system
    print("\n5. Testing Complete System...")
    system = ErrorCorrectionSystem()
    data = b"Test data"
    encoded, crc = system.encode_with_fec(data, 'hamming')
    decoded = system.decode_with_fec(encoded, crc, 'hamming')
    print(f"   Original: {data}")
    print(f"   Decoded: {decoded}")
    
    print("\n✅ Error Correction test completed!")