"""
Quantum Key Distribution System for AirOne Professional
Implements quantum-safe key exchange using quantum cryptography principles
"""

import asyncio
import threading
import queue
import time
import json
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import sqlite3
import socket
import struct
from functools import wraps
import numpy as np
from math import sqrt, pi, cos, sin, exp
import random
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import concurrent.futures
from collections import defaultdict, deque
import statistics


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QKDProtocol(Enum):
    """Quantum Key Distribution Protocols"""
    BB84 = "BB84"
    SARG04 = "SARG04"
    DECoy_BB84 = "Decoy_BB84"
    MDI_QKD = "Measurement_Device_Independent_QKD"
    TF_QKD = "Twin_Field_QKD"


class QuantumState(Enum):
    """Quantum states for QKD"""
    HORIZONTAL = "horizontal"  # |H⟩
    VERTICAL = "vertical"      # |V⟩
    PLUS_45 = "+45_degrees"    # |+⟩
    MINUS_45 = "-45_degrees"   # |-⟩


class QKDSecurityLevel(Enum):
    """Security levels for QKD"""
    CLASSICAL_RESISTANT = "classical_resistant"
    QUANTUM_SAFE = "quantum_safe"
    MILITARY_GRADE = "military_grade"


@dataclass
class QuantumKey:
    """Represents a quantum key"""
    id: str
    key_bits: List[int]  # Binary representation of the key
    protocol: QKDProtocol
    security_level: QKDSecurityLevel
    creation_time: datetime
    expiration_time: datetime
    error_rate: float
    sifted_key_length: int
    raw_key_length: int
    basis_choices: List[int]  # 0 for rectilinear, 1 for diagonal
    measurement_results: List[int]  # Measurement outcomes
    sender_id: str
    receiver_id: str
    quantum_states: List[QuantumState]
    authenticated: bool = False


@dataclass
class QKDTransmission:
    """Represents a QKD transmission"""
    id: str
    sender_id: str
    receiver_id: str
    protocol: QKDProtocol
    timestamp: datetime
    quantum_states_sent: List[Dict[str, Any]]  # State and basis info
    measurement_results: List[Dict[str, Any]]  # Measurement outcomes
    error_rate: float
    key_rate: float  # Bits per second
    distance_km: float
    photon_loss_rate: float
    security_verification_passed: bool
    final_key: Optional[QuantumKey] = None


class QuantumRandomNumberGenerator:
    """Quantum Random Number Generator for true randomness"""
    
    def __init__(self):
        self.seed = int(time.time() * 1000000) % (2**32)
        self.state = self.seed
        self.lock = threading.Lock()
        
        logger.info("Quantum Random Number Generator initialized")
    
    def quantum_random_bits(self, n_bits: int) -> List[int]:
        """Generate truly random bits using quantum principles simulation"""
        # In a real quantum system, this would use quantum phenomena
        # For simulation, we'll use a combination of system entropy and quantum-inspired randomness
        
        with self.lock:
            bits = []
            for _ in range(n_bits):
                # Simulate quantum randomness using multiple entropy sources
                entropy_sources = [
                    int(time.time() * 1000000) % 2,  # Time-based
                    random.randint(0, 1),           # PRNG
                    secrets.randbits(1),            # OS entropy
                    os.urandom(1)[0] % 2,          # OS random
                ]
                
                # Combine entropy sources using XOR
                combined = entropy_sources[0]
                for source in entropy_sources[1:]:
                    combined ^= source
                
                bits.append(combined)
            
            return bits
    
    def quantum_random_bytes(self, n_bytes: int) -> bytes:
        """Generate quantum random bytes"""
        bits = self.quantum_random_bits(n_bytes * 8)
        byte_list = []
        
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            byte_value = 0
            for bit in byte_bits:
                byte_value = (byte_value << 1) | bit
            byte_list.append(byte_value)
        
        return bytes(byte_list)


class QKDBasisSelector:
    """Manages basis selection for QKD protocols"""
    
    def __init__(self):
        self.qrng = QuantumRandomNumberGenerator()
        self.lock = threading.Lock()
        
        logger.info("QKD Basis Selector initialized")
    
    def generate_basis_sequence(self, length: int) -> List[int]:
        """Generate random basis sequence (0=rectilinear, 1=diagonal)"""
        return self.qrng.quantum_random_bits(length)
    
    def generate_quantum_states(self, basis_sequence: List[int]) -> List[QuantumState]:
        """Generate quantum states based on basis sequence"""
        states = []
        
        for basis in basis_sequence:
            # Generate random bit for the state
            bit = self.qrng.quantum_random_bits(1)[0]
            
            if basis == 0:  # Rectilinear basis
                if bit == 0:
                    states.append(QuantumState.HORIZONTAL)  # |H⟩
                else:
                    states.append(QuantumState.VERTICAL)    # |V⟩
            else:  # Diagonal basis
                if bit == 0:
                    states.append(QuantumState.PLUS_45)     # |+⟩
                else:
                    states.append(QuantumState.MINUS_45)    # |-⟩
        
        return states


class QKDErrorCorrection:
    """Implements error correction for QKD"""
    
    def __init__(self):
        self.lock = threading.Lock()
        
        logger.info("QKD Error Correction initialized")
    
    def cascade_error_correction(self, alice_bits: List[int], bob_bits: List[int], 
                                alice_bases: List[int], bob_bases: List[int]) -> tuple[List[int], List[int]]:
        """Implement Cascade error correction algorithm"""
        # Only keep bits where Alice and Bob used the same basis
        corrected_alice = []
        corrected_bob = []
        
        for i in range(min(len(alice_bits), len(bob_bits))):
            if alice_bases[i] == bob_bases[i]:
                corrected_alice.append(alice_bits[i])
                corrected_bob.append(bob_bits[i])
        
        # Calculate initial error rate
        initial_errors = sum(a != b for a, b in zip(corrected_alice, corrected_bob))
        initial_length = len(corrected_alice)
        initial_error_rate = initial_errors / initial_length if initial_length > 0 else 0
        
        # Apply Cascade error correction
        final_alice, final_bob = self._cascade_passes(corrected_alice, corrected_bob)
        
        return final_alice, final_bob
    
    def _cascade_passes(self, alice_bits: List[int], bob_bits: List[int], 
                       passes: int = 4) -> tuple[List[int], List[int]]:
        """Perform multiple Cascade error correction passes"""
        a_bits = alice_bits[:]
        b_bits = bob_bits[:]
        
        for pass_num in range(passes):
            # Divide bits into blocks of increasing size
            block_size = 2 ** (pass_num + 1)
            
            for i in range(0, len(a_bits), block_size):
                block_a = a_bits[i:i+block_size]
                block_b = b_bits[i:i+block_size]
                
                # Check parity of the block
                parity_a = sum(block_a) % 2
                parity_b = sum(block_b) % 2
                
                if parity_a != parity_b:
                    # Error detected in this block, bisect to find it
                    corrected_a, corrected_b = self._bisect_and_correct(block_a, block_b)
                    a_bits[i:i+block_size] = corrected_a
                    b_bits[i:i+block_size] = corrected_b
        
        return a_bits, b_bits
    
    def _bisect_and_correct(self, block_a: List[int], block_b: List[int]) -> tuple[List[int], List[int]]:
        """Bisect a block to find and correct single error"""
        if len(block_a) <= 1:
            # Flip one bit to make parities match
            if sum(block_a) % 2 != sum(block_b) % 2:
                if block_b:
                    block_b[0] = 1 - block_b[0]  # Flip first bit
            return block_a, block_b
        
        mid = len(block_a) // 2
        left_a, right_a = block_a[:mid], block_a[mid:]
        left_b, right_b = block_b[:mid], block_b[mid:]
        
        # Check parities of halves
        parity_left_a = sum(left_a) % 2
        parity_left_b = sum(left_b) % 2
        parity_right_a = sum(right_a) % 2
        parity_right_b = sum(right_b) % 2
        
        if parity_left_a != parity_left_b:
            # Error in left half
            corrected_left_a, corrected_left_b = self._bisect_and_correct(left_a, left_b)
            return corrected_left_a + right_a, corrected_left_b + right_b
        else:
            # Error in right half
            corrected_right_a, corrected_right_b = self._bisect_and_correct(right_a, right_b)
            return left_a + corrected_right_a, left_b + corrected_right_b


class QKDPrivacyAmplification:
    """Implements privacy amplification for QKD"""
    
    def __init__(self):
        self.lock = threading.Lock()
        
        logger.info("QKD Privacy Amplification initialized")
    
    def universal_hashing(self, raw_key: List[int], target_length: int) -> List[int]:
        """Apply universal hashing for privacy amplification"""
        if target_length >= len(raw_key):
            return raw_key[:]  # No amplification needed
        
        # Use a universal hash family (Toeplitz matrices)
        # For simplicity, we'll use a polynomial hash
        prime = 2**31 - 1  # Large prime
        
        # Convert key to integer
        key_int = 0
        for bit in raw_key:
            key_int = (key_int * 2 + bit) % prime
        
        # Generate hash coefficients randomly
        coefficients = []
        qrng = QuantumRandomNumberGenerator()
        for _ in range(target_length):
            coefficients.append(qrng.quantum_random_bytes(4))  # 32-bit coefficient
        
        # Apply polynomial hash
        result = 0
        for i, coeff_bytes in enumerate(coefficients):
            coeff = int.from_bytes(coeff_bytes, 'big') % prime
            result = (result + coeff * pow(key_int, i, prime)) % prime
        
        # Convert result back to binary
        result_bits = []
        for _ in range(target_length):
            result_bits.append(result & 1)
            result >>= 1
        
        return result_bits[:target_length]


class QuantumKeyDistributionNode:
    """A node in the QKD network"""
    
    def __init__(self, node_id: str, node_type: str = "qkd_node"):
        self.node_id = node_id
        self.node_type = node_type
        self.qrng = QuantumRandomNumberGenerator()
        self.basis_selector = QKDBasisSelector()
        self.error_correction = QKDErrorCorrection()
        self.privacy_amplification = QKDPrivacyAmplification()
        self.active_keys = {}
        self.transmission_history = []
        self.lock = threading.Lock()
        self.channel_noise = 0.01  # Base noise level
        self.distance_attenuation = 0.2  # dB/km
        
        logger.info(f"QKD Node {node_id} initialized")
    
    def initiate_bb84_protocol(self, partner_node_id: str, key_length: int = 256) -> QKDTransmission:
        """Initiate BB84 protocol with another node"""
        start_time = datetime.utcnow()
        
        # Step 1: Alice prepares quantum states
        alice_basis = self.basis_selector.generate_basis_sequence(key_length * 2)  # Extra for sifting
        alice_states = self.basis_selector.generate_quantum_states(alice_basis)
        
        # Step 2: Alice sends quantum states (simulated)
        quantum_transmission = self._simulate_quantum_transmission(
            alice_states, partner_node_id, key_length
        )
        
        # Step 3: Bob measures in random bases
        bob_basis = self.basis_selector.generate_basis_sequence(len(quantum_transmission))
        bob_results = self._simulate_quantum_measurement(
            quantum_transmission, bob_basis
        )
        
        # Step 4: Public discussion of bases (classical channel)
        matching_positions = [
            i for i in range(len(alice_basis)) 
            if i < len(bob_basis) and alice_basis[i] == bob_basis[i]
        ]
        
        # Step 5: Sift the key
        alice_sifted = [alice_states[i] for i in matching_positions if i < len(alice_states)]
        bob_sifted = [bob_results[i] for i in matching_positions if i < len(bob_results)]
        
        # Convert quantum states to bits
        alice_bits = [0 if state in [QuantumState.HORIZONTAL, QuantumState.PLUS_45] else 1 
                     for state in alice_sifted]
        bob_bits = [0 if state in [QuantumState.HORIZONTAL, QuantumState.PLUS_45] else 1 
                   for state in bob_sifted]
        
        # Step 6: Error correction
        corrected_alice, corrected_bob = self.error_correction.cascade_error_correction(
            alice_bits, bob_bits, 
            [alice_basis[i] for i in matching_positions], 
            [bob_basis[i] for i in matching_positions]
        )
        
        # Calculate error rate
        errors = sum(a != b for a, b in zip(corrected_alice, corrected_bob))
        error_rate = errors / len(corrected_alice) if corrected_alice else 0
        
        # Step 7: Privacy amplification
        final_key_length = max(1, int(len(corrected_alice) * 0.5))  # Reduce for privacy
        final_key_bits = self.privacy_amplification.universal_hashing(
            corrected_alice, final_key_length
        )
        
        # Create quantum key
        key_id = f"qk_{self.node_id}_{partner_node_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        quantum_key = QuantumKey(
            id=key_id,
            key_bits=final_key_bits,
            protocol=QKDProtocol.BB84,
            security_level=QKDSecurityLevel.QUANTUM_SAFE,
            creation_time=datetime.utcnow(),
            expiration_time=datetime.utcnow() + timedelta(hours=24),
            error_rate=error_rate,
            sifted_key_length=len(corrected_alice),
            raw_key_length=len(alice_bits),
            basis_choices=[alice_basis[i] for i in matching_positions],
            measurement_results=corrected_bob,
            sender_id=self.node_id,
            receiver_id=partner_node_id,
            quantum_states=alice_sifted
        )
        
        # Store the key
        with self.lock:
            self.active_keys[key_id] = quantum_key
        
        # Create transmission record
        transmission = QKDTransmission(
            id=f"tx_{key_id}",
            sender_id=self.node_id,
            receiver_id=partner_node_id,
            protocol=QKDProtocol.BB84,
            timestamp=start_time,
            quantum_states_sent=[
                {"state": alice_states[i].value, "basis": alice_basis[i]}
                for i in matching_positions
            ],
            measurement_results=[
                {"result": bob_results[i], "basis": bob_basis[i]}
                for i in matching_positions
            ],
            error_rate=error_rate,
            key_rate=len(final_key_bits) / (datetime.utcnow() - start_time).total_seconds(),
            distance_km=10.0,  # Simulated distance
            photon_loss_rate=self.channel_noise,
            security_verification_passed=error_rate < 0.11,  # BB84 threshold
            final_key=quantum_key
        )
        
        # Store transmission
        self.transmission_history.append(transmission)
        
        logger.info(f"BB84 protocol completed with {partner_node_id}. Key ID: {key_id}, Length: {len(final_key_bits)}, Error Rate: {error_rate:.4f}")
        return transmission
    
    def _simulate_quantum_transmission(self, states: List[QuantumState], 
                                     partner_node_id: str, expected_length: int) -> List[QuantumState]:
        """Simulate quantum state transmission over quantum channel"""
        # In a real system, this would involve actual quantum transmission
        # For simulation, we'll apply channel effects
        transmitted_states = []
        
        for state in states[:expected_length]:
            # Apply channel noise
            if random.random() < self.channel_noise:
                # State flipped due to noise
                if state == QuantumState.HORIZONTAL:
                    transmitted_states.append(QuantumState.VERTICAL)
                elif state == QuantumState.VERTICAL:
                    transmitted_states.append(QuantumState.HORIZONTAL)
                elif state == QuantumState.PLUS_45:
                    transmitted_states.append(QuantumState.MINUS_45)
                elif state == QuantumState.MINUS_45:
                    transmitted_states.append(QuantumState.PLUS_45)
            else:
                transmitted_states.append(state)
        
        return transmitted_states
    
    def _simulate_quantum_measurement(self, received_states: List[QuantumState], 
                                    measurement_bases: List[int]) -> List[QuantumState]:
        """Simulate quantum measurement by Bob"""
        measured_states = []
        
        for i, state in enumerate(received_states):
            if i >= len(measurement_bases):
                break
                
            basis = measurement_bases[i]
            
            # If basis matches, measurement is accurate
            # If basis doesn't match, result is random
            if (basis == 0 and state in [QuantumState.HORIZONTAL, QuantumState.VERTICAL]) or \
               (basis == 1 and state in [QuantumState.PLUS_45, QuantumState.MINUS_45]):
                # Correct basis - measurement preserves state
                measured_states.append(state)
            else:
                # Wrong basis - measurement gives random result
                if basis == 0:  # Measuring in rectilinear basis
                    if random.random() < 0.5:
                        measured_states.append(QuantumState.HORIZONTAL)
                    else:
                        measured_states.append(QuantumState.VERTICAL)
                else:  # Measuring in diagonal basis
                    if random.random() < 0.5:
                        measured_states.append(QuantumState.PLUS_45)
                    else:
                        measured_states.append(QuantumState.MINUS_45)
        
        return measured_states
    
    def get_active_key(self, key_id: str) -> Optional[QuantumKey]:
        """Get an active quantum key by ID"""
        with self.lock:
            return self.active_keys.get(key_id)
    
    def get_keys_for_partner(self, partner_node_id: str) -> List[QuantumKey]:
        """Get all keys shared with a specific partner"""
        with self.lock:
            return [
                key for key in self.active_keys.values()
                if key.receiver_id == partner_node_id or key.sender_id == partner_node_id
            ]
    
    def encrypt_data(self, data: bytes, key_id: str) -> bytes:
        """Encrypt data using a quantum key"""
        key = self.get_active_key(key_id)
        if not key:
            raise ValueError(f"Key {key_id} not found")
        
        # Convert key bits to bytes
        key_bytes = self._bits_to_bytes(key.key_bits)
        
        # Use AES-GCM for encryption (the quantum key provides the AES key)
        aesgcm = AESGCM(key_bytes[:32])  # Use first 256 bits as AES key
        
        # Generate random nonce
        nonce = secrets.token_bytes(12)
        
        # Encrypt the data
        encrypted_data = aesgcm.encrypt(nonce, data, associated_data=None)
        
        # Prepend nonce to encrypted data
        return nonce + encrypted_data
    
    def decrypt_data(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data using a quantum key"""
        key = self.get_active_key(key_id)
        if not key:
            raise ValueError(f"Key {key_id} not found")
        
        # Extract nonce (first 12 bytes)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        # Convert key bits to bytes
        key_bytes = self._bits_to_bytes(key.key_bits)
        
        # Use AES-GCM for decryption
        aesgcm = AESGCM(key_bytes[:32])  # Use first 256 bits as AES key
        
        # Decrypt the data
        decrypted_data = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
        
        return decrypted_data
    
    def _bits_to_bytes(self, bits: List[int]) -> bytes:
        """Convert a list of bits to bytes"""
        # Pad bits to make length multiple of 8
        padded_bits = bits + [0] * ((8 - len(bits) % 8) % 8)
        
        byte_list = []
        for i in range(0, len(padded_bits), 8):
            byte_bits = padded_bits[i:i+8]
            byte_value = 0
            for bit in byte_bits:
                byte_value = (byte_value << 1) | bit
            byte_list.append(byte_value)
        
        return bytes(byte_list)
    
    def get_node_status(self) -> Dict[str, Any]:
        """Get the status of this QKD node"""
        with self.lock:
            return {
                'node_id': self.node_id,
                'node_type': self.node_type,
                'active_keys_count': len(self.active_keys),
                'transmission_count': len(self.transmission_history),
                'channel_noise': self.channel_noise,
                'distance_attenuation': self.distance_attenuation,
                'timestamp': datetime.utcnow().isoformat()
            }


class QuantumKeyDistributionNetwork:
    """Manages a network of QKD nodes"""
    
    def __init__(self):
        self.nodes = {}
        self.connections = {}
        self.network_topology = {}
        self.lock = threading.Lock()
        self.running = False
        self.network_thread = None
        
        logger.info("Quantum Key Distribution Network initialized")
    
    def add_node(self, node_id: str, node_type: str = "qkd_node") -> QuantumKeyDistributionNode:
        """Add a node to the QKD network"""
        node = QuantumKeyDistributionNode(node_id, node_type)
        
        with self.lock:
            self.nodes[node_id] = node
            self.network_topology[node_id] = []
        
        logger.info(f"Added QKD node: {node_id}")
        return node
    
    def connect_nodes(self, node1_id: str, node2_id: str, distance_km: float = 10.0):
        """Connect two nodes in the network"""
        with self.lock:
            if node1_id in self.nodes and node2_id in self.nodes:
                # Update network topology
                if node2_id not in self.network_topology[node1_id]:
                    self.network_topology[node1_id].append(node2_id)
                if node1_id not in self.network_topology[node2_id]:
                    self.network_topology[node2_id].append(node1_id)
                
                # Store connection info
                connection_id = f"conn_{node1_id}_{node2_id}"
                self.connections[connection_id] = {
                    'node1': node1_id,
                    'node2': node2_id,
                    'distance_km': distance_km,
                    'established_at': datetime.utcnow()
                }
        
        logger.info(f"Connected nodes: {node1_id} <-> {node2_id}")
    
    def establish_quantum_key(self, node1_id: str, node2_id: str, 
                            key_length: int = 256) -> Optional[QKDTransmission]:
        """Establish a quantum key between two nodes"""
        with self.lock:
            node1 = self.nodes.get(node1_id)
            node2 = self.nodes.get(node2_id)
        
        if not node1 or not node2:
            logger.error(f"One or both nodes not found: {node1_id}, {node2_id}")
            return None
        
        # Check if nodes are connected
        if node2_id not in self.network_topology.get(node1_id, []):
            logger.error(f"Nodes {node1_id} and {node2_id} are not connected")
            return None
        
        # Initiate QKD protocol
        try:
            transmission = node1.initiate_bb84_protocol(node2_id, key_length)
            return transmission
        except Exception as e:
            logger.error(f"Error establishing quantum key: {e}")
            return None
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """Get network-wide metrics"""
        with self.lock:
            total_keys = 0
            avg_error_rate = 0
            total_transmissions = 0
            secure_transmissions = 0
            
            for node in self.nodes.values():
                for key in node.active_keys.values():
                    total_keys += 1
                    avg_error_rate += key.error_rate
                
                for tx in node.transmission_history:
                    total_transmissions += 1
                    if tx.security_verification_passed:
                        secure_transmissions += 1
            
            avg_error_rate = avg_error_rate / total_keys if total_keys > 0 else 0
            security_success_rate = secure_transmissions / total_transmissions if total_transmissions > 0 else 0
            
            return {
                'total_nodes': len(self.nodes),
                'total_connections': len(self.connections),
                'total_active_keys': total_keys,
                'average_error_rate': avg_error_rate,
                'total_transmissions': total_transmissions,
                'secure_transmission_rate': security_success_rate,
                'network_topology': self.network_topology,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def start_network_monitoring(self):
        """Start network monitoring"""
        self.running = True
        self.network_thread = threading.Thread(target=self._network_monitoring_loop, daemon=True)
        self.network_thread.start()
        logger.info("QKD Network monitoring started")
    
    def stop_network_monitoring(self):
        """Stop network monitoring"""
        self.running = False
        if self.network_thread:
            self.network_thread.join(timeout=5)
        logger.info("QKD Network monitoring stopped")
    
    def _network_monitoring_loop(self):
        """Network monitoring loop"""
        while self.running:
            try:
                # Perform periodic health checks
                self._perform_health_checks()
                
                # Clean up expired keys
                self._cleanup_expired_keys()
                
                # Sleep before next iteration
                time.sleep(60)  # Every minute
                
            except Exception as e:
                logger.error(f"Error in network monitoring loop: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _perform_health_checks(self):
        """Perform health checks on all nodes"""
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_nodes': len(self.nodes),
            'healthy_nodes': 0,
            'degraded_nodes': 0,
            'offline_nodes': 0,
            'quantum_channel_quality': {},
            'node_status': {}
        }
        
        for node_id, node in self.nodes.items():
            try:
                status = node.get_status()
                channel_quality = node.get_channel_quality() if hasattr(node, 'get_channel_quality') else {'quality': 'unknown'}
                
                if status.get('status', 'unknown') == 'online':
                    health_status['healthy_nodes'] += 1
                elif status.get('status', 'unknown') == 'degraded':
                    health_status['degraded_nodes'] += 1
                else:
                    health_status['offline_nodes'] += 1
                
                health_status['node_status'][node_id] = status
                health_status['quantum_channel_quality'][node_id] = channel_quality
                
            except Exception as e:
                logger.error(f"Health check failed for node {node_id}: {e}")
                health_status['offline_nodes'] += 1
                health_status['node_status'][node_id] = {'status': 'error', 'error': str(e)}
        
        self.qkd_network_health = health_status
        return health_status
    
    def _cleanup_expired_keys(self):
        """Remove expired keys from all nodes"""
        current_time = datetime.utcnow()
        
        for node in self.nodes.values():
            expired_keys = []
            for key_id, key in node.active_keys.items():
                if current_time > key.expiration_time:
                    expired_keys.append(key_id)
            
            for key_id in expired_keys:
                del node.active_keys[key_id]
                logger.info(f"Removed expired key: {key_id}")


class QKDCoordinator:
    """Coordinates QKD operations across the network"""
    
    def __init__(self, network: QuantumKeyDistributionNetwork):
        self.network = network
        self.key_rotation_interval = timedelta(hours=1)
        self.lock = threading.Lock()
        
        logger.info("QKD Coordinator initialized")
    
    def coordinate_key_establishment(self, node_pairs: List[tuple], 
                                   key_length: int = 256) -> List[QKDTransmission]:
        """Coordinate key establishment for multiple node pairs"""
        transmissions = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(node_pairs)) as executor:
            # Submit all key establishment tasks
            future_to_pair = {
                executor.submit(self.network.establish_quantum_key, pair[0], pair[1], key_length): pair
                for pair in node_pairs
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_pair):
                pair = future_to_pair[future]
                try:
                    transmission = future.result()
                    if transmission:
                        transmissions.append(transmission)
                        logger.info(f"Successfully established key for pair: {pair}")
                    else:
                        logger.warning(f"Failed to establish key for pair: {pair}")
                except Exception as e:
                    logger.error(f"Error establishing key for pair {pair}: {e}")
        
        return transmissions
    
    def initiate_network_wide_key_refresh(self) -> Dict[str, Any]:
        """Initiate a network-wide key refresh"""
        start_time = datetime.utcnow()
        
        # Get all connected node pairs
        node_pairs = []
        for node_id, connections in self.network.network_topology.items():
            for connected_node in connections:
                # Avoid duplicate pairs
                if node_id < connected_node:  # Lexicographic ordering
                    node_pairs.append((node_id, connected_node))
        
        # Establish new keys for all pairs
        transmissions = self.coordinate_key_establishment(node_pairs)
        
        end_time = datetime.utcnow()
        
        result = {
            'initiated_at': start_time.isoformat(),
            'completed_at': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'node_pairs_targeted': len(node_pairs),
            'successful_establishments': len(transmissions),
            'success_rate': len(transmissions) / len(node_pairs) if node_pairs else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Network-wide key refresh completed: {result}")
        return result
    
    def get_coordinated_metrics(self) -> Dict[str, Any]:
        """Get coordinated network metrics"""
        network_metrics = self.network.get_network_metrics()
        
        # Add coordinator-specific metrics
        with self.lock:
            return {
                **network_metrics,
                'key_rotation_interval': self.key_rotation_interval.total_seconds(),
                'timestamp': datetime.utcnow().isoformat()
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize QKD network
    qkd_network = QuantumKeyDistributionNetwork()
    coordinator = QKDCoordinator(qkd_network)
    
    print("⚛️  Quantum Key Distribution System Initialized...")
    
    # Start network monitoring
    qkd_network.start_network_monitoring()
    
    # Add nodes to the network
    print("\nAdding QKD nodes...")
    node_a = qkd_network.add_node("Alice_Node", "sender")
    node_b = qkd_network.add_node("Bob_Node", "receiver")
    node_c = qkd_network.add_node("Charlie_Node", "relay")
    
    print(f"Added {len(qkd_network.nodes)} nodes to the network")
    
    # Connect nodes
    print("\nConnecting nodes...")
    qkd_network.connect_nodes("Alice_Node", "Bob_Node", distance_km=15.0)
    qkd_network.connect_nodes("Alice_Node", "Charlie_Node", distance_km=20.0)
    qkd_network.connect_nodes("Bob_Node", "Charlie_Node", distance_km=18.0)
    
    print(f"Established {len(qkd_network.connections)} connections")
    
    # Establish quantum keys
    print("\nEstablishing quantum keys...")
    
    # Single key establishment
    transmission = qkd_network.establish_quantum_key("Alice_Node", "Bob_Node", key_length=512)
    if transmission:
        print(f"Key established: {transmission.final_key.id}")
        print(f"Key length: {len(transmission.final_key.key_bits)} bits")
        print(f"Error rate: {transmission.error_rate:.4f}")
        print(f"Security verified: {transmission.security_verification_passed}")
    
    # Multiple key establishments
    node_pairs = [("Alice_Node", "Charlie_Node"), ("Bob_Node", "Charlie_Node")]
    transmissions = coordinator.coordinate_key_establishment(node_pairs, key_length=256)
    print(f"Established {len(transmissions)} additional keys")
    
    # Test encryption/decryption
    print("\nTesting quantum key encryption/decryption...")
    if transmission:
        test_data = b"Secret quantum-encrypted message for secure communication"
        
        # Encrypt with quantum key
        encrypted = node_a.encrypt_data(test_data, transmission.final_key.id)
        print(f"Data encrypted, size: {len(encrypted)} bytes")
        
        # Decrypt with quantum key
        decrypted = node_b.decrypt_data(encrypted, transmission.final_key.id)
        print(f"Data decrypted successfully: {decrypted == test_data}")
        
        if decrypted == test_data:
            print("✅ Encryption/decryption test passed")
        else:
            print("❌ Encryption/decryption test failed")
    
    # Perform network-wide key refresh
    print("\nPerforming network-wide key refresh...")
    refresh_result = coordinator.initiate_network_wide_key_refresh()
    print(f"Key refresh completed: {refresh_result['success_rate']:.2%} success rate")
    
    # Get network metrics
    print("\nGetting network metrics...")
    metrics = qkd_network.get_network_metrics()
    print(json.dumps(metrics, indent=2, default=str))
    
    # Get coordinator metrics
    print("\nGetting coordinator metrics...")
    coord_metrics = coordinator.get_coordinated_metrics()
    print(json.dumps(coord_metrics, indent=2, default=str))
    
    # Get individual node status
    print("\nGetting node statuses...")
    for node_id, node in qkd_network.nodes.items():
        status = node.get_node_status()
        print(f"Node {node_id}: {status['active_keys_count']} active keys")
    
    # Stop network monitoring
    qkd_network.stop_network_monitoring()
    
    print("\n✅ Quantum Key Distribution System Test Completed")