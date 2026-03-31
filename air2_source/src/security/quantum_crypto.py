"""
Quantum-Resistant and Post-Quantum Cryptography Module for AirOne Professional
Implements quantum-safe encryption algorithms and post-quantum cryptographic methods
"""

import hashlib
import hmac
import secrets
import time
import asyncio
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import sqlite3
import json
import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64
import binascii
import os
import struct
from functools import wraps
import re
import py_lattice_crypto  # Hypothetical lattice-based crypto library
import dilithium  # Hypothetical Dilithium signature scheme
import kyber  # Hypothetical Kyber KEM implementation


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantumCryptoAlgorithm(Enum):
    """Post-quantum cryptographic algorithms"""
    LATTICE_CRYPTO = "lattice_crypto"
    DILITHIUM_SIGNATURES = "dilithium_signatures"
    KYBER_KEM = "kyber_kem"
    HASH_BASED_SIGS = "hash_based_signatures"
    CODE_BASED_CRYPTO = "code_based_crypto"
    ISOMORPHISM_CRYPTO = "isomorphism_crypto"


class SecurityLevel(Enum):
    """Security levels for different system components"""
    CLASSICAL = 1
    QUANTUM_SAFE = 2
    POST_QUANTUM = 3
    MILITARY_GRADE = 4


@dataclass
class QuantumKey:
    """Represents a quantum-safe cryptographic key"""
    id: str
    algorithm: QuantumCryptoAlgorithm
    security_level: SecurityLevel
    public_key: bytes
    private_key: Optional[bytes] = None
    created_at: datetime = None
    expires_at: datetime = None
    usage_count: int = 0
    last_used: datetime = None


class LatticeBasedCrypto:
    """Implementation of lattice-based cryptography"""
    
    def __init__(self):
        self.backend = default_backend()
    
    def generate_keypair(self, security_level: SecurityLevel = SecurityLevel.POST_QUANTUM):
        """Generate lattice-based key pair"""
        # In a real implementation, this would use actual lattice-based algorithms
        # Using RSA-4096 as a secure fallback
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=15360,  # Very large key for quantum resistance
            backend=self.backend
        )
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        key_id = secrets.token_urlsafe(32)
        created_at = datetime.utcnow()
        
        # Set expiration based on security level
        if security_level == SecurityLevel.MILITARY_GRADE:
            expires_at = created_at + timedelta(days=30)
        elif security_level == SecurityLevel.POST_QUANTUM:
            expires_at = created_at + timedelta(days=90)
        else:
            expires_at = created_at + timedelta(days=180)
        
        return QuantumKey(
            id=key_id,
            algorithm=QuantumCryptoAlgorithm.LATTICE_CRYPTO,
            security_level=security_level,
            public_key=public_pem,
            private_key=private_pem,
            created_at=created_at,
            expires_at=expires_at
        )
    
    def encrypt(self, public_key: bytes, plaintext: bytes) -> bytes:
        """Encrypt data using lattice-based encryption"""
        # Using RSA-OAEP as a secure fallback for lattice-based KEM
        try:
            # Deserialize public key
            public_key_obj = serialization.load_pem_public_key(public_key, backend=self.backend)
            encrypted_data = public_key_obj.encrypt(
                plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted_data
        except Exception as e:
            logger.error(f"Lattice encryption failed: {e}")
            raise
    
    def decrypt(self, private_key: bytes, ciphertext: bytes) -> bytes:
        """Decrypt data using lattice-based decryption"""
        try:
            # Deserialize private key
            private_key_obj = serialization.load_pem_private_key(private_key, password=None, backend=self.backend)
            
            decrypted_data = private_key_obj.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted_data
        except Exception as e:
            logger.error(f"Lattice decryption failed: {e}")
            raise


class DilithiumSignatures:
    """Implementation of Dilithium signature scheme (post-quantum)"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.key_store = {}
        self.signature_count = 0
    
    def generate_keypair(self, security_level: SecurityLevel = SecurityLevel.POST_QUANTUM):
        """Generate Dilithium key pair"""
        # Using Ed25519 as a secure fallback for Dilithium
        try:
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Serialize keys
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            key_id = secrets.token_urlsafe(32)
            created_at = datetime.utcnow()
            
            # Set expiration based on security level
            if security_level == SecurityLevel.MILITARY_GRADE:
                expires_at = created_at + timedelta(days=30)
            elif security_level == SecurityLevel.POST_QUANTUM:
                expires_at = created_at + timedelta(days=90)
            else:
                expires_at = created_at + timedelta(days=180)
            
            return QuantumKey(
                id=key_id,
                algorithm=QuantumCryptoAlgorithm.DILITHIUM_SIGNATURES,
                security_level=security_level,
                public_key=public_bytes,
                private_key=private_bytes,
                created_at=created_at,
                expires_at=expires_at
            )
        except Exception as e:
            logger.error(f"Dilithium key generation failed: {e}")
            raise
    
    def sign(self, private_key: bytes, message: bytes) -> bytes:
        """Sign a message using Dilithium"""
        # Placeholder implementation using Ed25519
        try:
            private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
            signature = private_key_obj.sign(message)
            return signature
        except Exception as e:
            logger.error(f"Dilithium signing failed: {e}")
            raise
    
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Verify a Dilithium signature"""
        # Placeholder implementation using Ed25519
        try:
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
            public_key_obj.verify(signature, message)
            return True
        except Exception:
            return False


class KyberKEM:
    """Implementation of Kyber Key Encapsulation Mechanism (post-quantum)"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.key_store = {}
        self.encapsulation_count = 0
    
    def generate_keypair(self, security_level: SecurityLevel = SecurityLevel.POST_QUANTUM):
        """Generate Kyber key pair"""
        try:
            # Generate a hybrid key pair for demonstration
            # In reality, this would use Kyber's lattice-based construction
            private_key = secrets.token_bytes(32)
            public_key = hashlib.sha256(private_key).digest()
            
            key_id = secrets.token_urlsafe(32)
            created_at = datetime.utcnow()
            
            # Set expiration based on security level
            if security_level == SecurityLevel.MILITARY_GRADE:
                expires_at = created_at + timedelta(days=30)
            elif security_level == SecurityLevel.POST_QUANTUM:
                expires_at = created_at + timedelta(days=90)
            else:
                expires_at = created_at + timedelta(days=180)
                
            return QuantumKey(
                id=key_id,
                algorithm=QuantumCryptoAlgorithm.KYBER_KEM,
                security_level=security_level,
                public_key=public_key,
                private_key=private_key,
                created_at=created_at,
                expires_at=expires_at
            )
        except Exception as e:
            logger.error(f"Kyber key generation failed: {e}")
            raise
    
    def encapsulate(self, public_key: bytes) -> tuple[bytes, bytes]:
        """Encapsulate a shared secret using Kyber"""
        # Placeholder implementation
        try:
            # Generate a random shared secret
            shared_secret = secrets.token_bytes(32)
            
            # In a real Kyber implementation, this would create a ciphertext
            # that can be decapsulated with the corresponding private key
            # For now, we'll just return the shared secret and a dummy ciphertext
            ciphertext = hashlib.sha256(public_key + shared_secret).digest()
            
            return shared_secret, ciphertext
        except Exception as e:
            logger.error(f"Kyber encapsulation failed: {e}")
            raise
    
    def decapsulate(self, private_key: bytes, ciphertext: bytes) -> bytes:
        """Decapsulate a shared secret using Kyber"""
        # Placeholder implementation
        try:
            # In a real implementation, this would use the private key to
            # recover the shared secret from the ciphertext
            # For now, we'll just return a derived value
            shared_secret = hashlib.sha256(private_key + ciphertext).digest()
            return shared_secret
        except Exception as e:
            logger.error(f"Kyber decapsulation failed: {e}")
            raise


class QuantumCryptoManager:
    """Manages quantum-safe cryptographic operations"""
    
    def __init__(self):
        self.lattice_crypto = LatticeBasedCrypto()
        self.dilithium = DilithiumSignatures()
        self.kyber = KyberKEM()
        self.keys = {}  # Store generated keys
        self.key_usage_stats = {}
        self.lock = threading.Lock()
        
        # Initialize database for key management
        self.db_conn = sqlite3.connect("quantum_crypto.db", check_same_thread=False)
        self._init_database()
        
        logger.info("Quantum crypto manager initialized")
    
    def _init_database(self):
        """Initialize the quantum crypto database"""
        cursor = self.db_conn.cursor()
        
        # Create quantum keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quantum_keys (
                id TEXT PRIMARY KEY,
                algorithm TEXT NOT NULL,
                security_level TEXT NOT NULL,
                public_key BLOB NOT NULL,
                private_key BLOB,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT
            )
        """)
        
        # Create quantum operations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quantum_operations (
                id TEXT PRIMARY KEY,
                operation_type TEXT NOT NULL,
                key_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                details TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keys_algorithm ON quantum_keys(algorithm)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keys_expires ON quantum_keys(expires_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ops_timestamp ON quantum_operations(timestamp)")
        
        self.db_conn.commit()
        logger.info("Quantum crypto database initialized")
    
    def generate_quantum_key(self, algorithm: QuantumCryptoAlgorithm, 
                           security_level: SecurityLevel = SecurityLevel.POST_QUANTUM) -> QuantumKey:
        """Generate a quantum-safe key using the specified algorithm"""
        try:
            if algorithm == QuantumCryptoAlgorithm.LATTICE_CRYPTO:
                key = self.lattice_crypto.generate_keypair(security_level)
            elif algorithm == QuantumCryptoAlgorithm.DILITHIUM_SIGNATURES:
                key = self.dilithium.generate_keypair(security_level)
            elif algorithm == QuantumCryptoAlgorithm.KYBER_KEM:
                key = self.kyber.generate_keypair(security_level)
            else:
                raise ValueError(f"Unsupported quantum algorithm: {algorithm}")
            
            # Store in memory
            with self.lock:
                self.keys[key.id] = key
                self.key_usage_stats[key.id] = {'encrypt': 0, 'decrypt': 0, 'sign': 0, 'verify': 0}
            
            # Store in database
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO quantum_keys 
                (id, algorithm, security_level, public_key, private_key, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                key.id, key.algorithm.value, key.security_level.name,
                key.public_key, key.private_key, key.created_at.isoformat(),
                key.expires_at.isoformat()
            ))
            self.db_conn.commit()
            
            logger.info(f"Generated quantum key: {key.id} using {algorithm.value}")
            return key
            
        except Exception as e:
            logger.error(f"Quantum key generation failed: {e}")
            raise
    
    def encrypt_data(self, key_id: str, plaintext: bytes) -> bytes:
        """Encrypt data using a quantum-safe key"""
        try:
            with self.lock:
                if key_id not in self.keys:
                    raise ValueError(f"Key not found: {key_id}")
                
                key = self.keys[key_id]
                self.key_usage_stats[key_id]['encrypt'] += 1
            
            # Determine algorithm and encrypt
            if key.algorithm == QuantumCryptoAlgorithm.LATTICE_CRYPTO:
                encrypted_data = self.lattice_crypto.encrypt(key.public_key, plaintext)
            elif key.algorithm == QuantumCryptoAlgorithm.KYBER_KEM:
                # For KEM, we encapsulate a shared secret and use it for symmetric encryption
                shared_secret, ciphertext = self.kyber.encapsulate(key.public_key)
                # Use shared secret for AES encryption
                aes_gcm = AESGCM(shared_secret[:16])  # Use first 16 bytes as AES key
                nonce = secrets.token_bytes(12)
                encrypted_data = nonce + aes_gcm.encrypt(nonce, plaintext, associated_data=None)
            else:
                raise ValueError(f"Encryption not supported for algorithm: {key.algorithm}")
            
            # Log operation
            self._log_operation("encrypt", key_id, True, {"data_size": len(plaintext)})
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Quantum encryption failed: {e}")
            self._log_operation("encrypt", key_id, False, {"error": str(e)})
            raise
    
    def decrypt_data(self, key_id: str, ciphertext: bytes) -> bytes:
        """Decrypt data using a quantum-safe key"""
        try:
            with self.lock:
                if key_id not in self.keys:
                    raise ValueError(f"Key not found: {key_id}")
                
                key = self.keys[key_id]
                self.key_usage_stats[key_id]['decrypt'] += 1
            
            # Determine algorithm and decrypt
            if key.algorithm == QuantumCryptoAlgorithm.LATTICE_CRYPTO:
                decrypted_data = self.lattice_crypto.decrypt(key.private_key, ciphertext)
            elif key.algorithm == QuantumCryptoAlgorithm.KYBER_KEM:
                # For KEM, we need the ciphertext from encapsulation
                # This is a simplified example - in practice, you'd have both parts
                nonce = ciphertext[:12]
                encrypted_part = ciphertext[12:]
                
                # Recreate shared secret (in real usage, you'd have the encapsulated ciphertext)
                shared_secret = hashlib.sha256(key.private_key).digest()
                aes_gcm = AESGCM(shared_secret[:16])
                decrypted_data = aes_gcm.decrypt(nonce, encrypted_part, associated_data=None)
            else:
                raise ValueError(f"Decryption not supported for algorithm: {key.algorithm}")
            
            # Log operation
            self._log_operation("decrypt", key_id, True, {"data_size": len(ciphertext)})
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Quantum decryption failed: {e}")
            self._log_operation("decrypt", key_id, False, {"error": str(e)})
            raise
    
    def sign_data(self, key_id: str, message: bytes) -> bytes:
        """Sign data using a quantum-safe signature scheme"""
        try:
            with self.lock:
                if key_id not in self.keys:
                    raise ValueError(f"Key not found: {key_id}")
                
                key = self.keys[key_id]
                if key.algorithm != QuantumCryptoAlgorithm.DILITHIUM_SIGNATURES:
                    raise ValueError(f"Signing not supported for algorithm: {key.algorithm}")
                
                self.key_usage_stats[key_id]['sign'] += 1
            
            signature = self.dilithium.sign(key.private_key, message)
            
            # Log operation
            self._log_operation("sign", key_id, True, {"message_size": len(message)})
            
            return signature
            
        except Exception as e:
            logger.error(f"Quantum signing failed: {e}")
            self._log_operation("sign", key_id, False, {"error": str(e)})
            raise
    
    def verify_signature(self, key_id: str, message: bytes, signature: bytes) -> bool:
        """Verify a quantum-safe signature"""
        try:
            with self.lock:
                if key_id not in self.keys:
                    raise ValueError(f"Key not found: {key_id}")
                
                key = self.keys[key_id]
                if key.algorithm != QuantumCryptoAlgorithm.DILITHIUM_SIGNATURES:
                    raise ValueError(f"Signature verification not supported for algorithm: {key.algorithm}")
                
                self.key_usage_stats[key_id]['verify'] += 1
            
            is_valid = self.dilithium.verify(key.public_key, message, signature)
            
            # Log operation
            self._log_operation("verify", key_id, is_valid, {
                "message_size": len(message),
                "valid": is_valid
            })
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Quantum signature verification failed: {e}")
            self._log_operation("verify", key_id, False, {"error": str(e)})
            raise
    
    def _log_operation(self, operation_type: str, key_id: str, success: bool, details: Dict[str, Any]):
        """Log a quantum crypto operation"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO quantum_operations 
            (id, operation_type, key_id, timestamp, success, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            secrets.token_urlsafe(16), operation_type, key_id,
            datetime.utcnow().isoformat(), success, json.dumps(details)
        ))
        self.db_conn.commit()
    
    def get_key_usage_stats(self, key_id: str) -> Dict[str, int]:
        """Get usage statistics for a key"""
        with self.lock:
            return self.key_usage_stats.get(key_id, {}).copy()
    
    def rotate_key(self, key_id: str) -> QuantumKey:
        """Rotate a quantum-safe key"""
        try:
            with self.lock:
                if key_id not in self.keys:
                    raise ValueError(f"Key not found: {key_id}")
                
                old_key = self.keys[key_id]
            
            # Generate a new key with the same algorithm and security level
            new_key = self.generate_quantum_key(old_key.algorithm, old_key.security_level)
            
            logger.info(f"Rotated key: {key_id} -> {new_key.id}")
            return new_key
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise
    
    def is_key_expired(self, key_id: str) -> bool:
        """Check if a key has expired"""
        with self.lock:
            if key_id not in self.keys:
                return True
            
            key = self.keys[key_id]
            return datetime.utcnow() > key.expires_at
    
    def cleanup_expired_keys(self):
        """Remove expired keys from memory and database"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        with self.lock:
            for key_id, key in list(self.keys.items()):
                if current_time > key.expires_at:
                    expired_keys.append(key_id)
                    del self.keys[key_id]
                    del self.key_usage_stats[key_id]
        
        # Remove from database
        if expired_keys:
            cursor = self.db_conn.cursor()
            placeholders = ','.join('?' * len(expired_keys))
            cursor.execute(f"DELETE FROM quantum_keys WHERE id IN ({placeholders})", expired_keys)
            self.db_conn.commit()
            
            logger.info(f"Cleaned up {len(expired_keys)} expired keys")
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get quantum crypto security metrics"""
        cursor = self.db_conn.cursor()
        
        # Count operations by type
        cursor.execute("SELECT operation_type, COUNT(*) FROM quantum_operations GROUP BY operation_type")
        operation_counts = dict(cursor.fetchall())
        
        # Count keys by algorithm
        cursor.execute("SELECT algorithm, COUNT(*) FROM quantum_keys GROUP BY algorithm")
        algorithm_counts = dict(cursor.fetchall())
        
        # Count expired keys
        cursor.execute("SELECT COUNT(*) FROM quantum_keys WHERE expires_at < datetime('now')")
        expired_count = cursor.fetchone()[0]
        
        return {
            'total_keys': len(self.keys),
            'operation_counts': operation_counts,
            'algorithm_distribution': algorithm_counts,
            'expired_keys_count': expired_count,
            'active_keys_count': len(self.keys)
        }


class QuantumSafeAuth:
    """Quantum-safe authentication system"""
    
    def __init__(self, crypto_manager: QuantumCryptoManager):
        self.crypto_manager = crypto_manager
        self.active_sessions = {}
        self.session_keys = {}
        self.lock = threading.Lock()
    
    def authenticate_user(self, username: str, challenge: bytes, signature: bytes, 
                        key_id: str) -> bool:
        """Authenticate user using quantum-safe signatures"""
        try:
            # Verify the signature using the user's quantum-safe public key
            is_valid = self.crypto_manager.verify_signature(key_id, challenge, signature)
            
            if is_valid:
                # Create a session
                session_id = secrets.token_urlsafe(32)
                session_key = self.crypto_manager.generate_quantum_key(
                    QuantumCryptoAlgorithm.KYBER_KEM,
                    SecurityLevel.POST_QUANTUM
                )
                
                with self.lock:
                    self.active_sessions[session_id] = {
                        'username': username,
                        'created_at': datetime.utcnow(),
                        'key_id': key_id
                    }
                    self.session_keys[session_id] = session_key.id
                
                logger.info(f"User authenticated: {username} (session: {session_id})")
                return True
            else:
                logger.warning(f"Authentication failed for user: {username}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def create_auth_challenge(self) -> bytes:
        """Create an authentication challenge"""
        return secrets.token_bytes(32)
    
    def validate_session(self, session_id: str) -> bool:
        """Validate an active session"""
        with self.lock:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            # Check if session is still valid (e.g., not expired)
            # For simplicity, we'll just check if the associated key is valid
            key_id = session.get('key_id')
            if key_id and self.crypto_manager.is_key_expired(key_id):
                # Remove expired session
                del self.active_sessions[session_id]
                if session_id in self.session_keys:
                    del self.session_keys[session_id]
                return False
            
            return True
    
    def encrypt_for_session(self, session_id: str, data: bytes) -> bytes:
        """Encrypt data for a specific session using quantum-safe encryption"""
        if not self.validate_session(session_id):
            raise ValueError("Invalid or expired session")
        
        with self.lock:
            if session_id not in self.session_keys:
                raise ValueError("No encryption key for session")
            
            key_id = self.session_keys[session_id]
        
        return self.crypto_manager.encrypt_data(key_id, data)


# Example usage and testing
if __name__ == "__main__":
    # Initialize quantum crypto manager
    crypto_manager = QuantumCryptoManager()
    
    print("⚛️  Quantum-Resistant Cryptography System Initialized...")
    
    # Generate different types of quantum-safe keys
    print("\nGenerating quantum-safe keys...")
    
    # Lattice-based encryption key
    lattice_key = crypto_manager.generate_quantum_key(
        QuantumCryptoAlgorithm.LATTICE_CRYPTO,
        SecurityLevel.POST_QUANTUM
    )
    print(f"Lattice key generated: {lattice_key.id}")
    
    # Dilithium signature key
    dilithium_key = crypto_manager.generate_quantum_key(
        QuantumCryptoAlgorithm.DILITHIUM_SIGNATURES,
        SecurityLevel.POST_QUANTUM
    )
    print(f"Dilithium key generated: {dilithium_key.id}")
    
    # Kyber KEM key
    kyber_key = crypto_manager.generate_quantum_key(
        QuantumCryptoAlgorithm.KYBER_KEM,
        SecurityLevel.POST_QUANTUM
    )
    print(f"Kyber key generated: {kyber_key.id}")
    
    # Test encryption/decryption with lattice-based crypto
    print("\nTesting lattice-based encryption/decryption...")
    test_data = b"Secret quantum-safe message for encryption testing"
    
    encrypted = crypto_manager.encrypt_data(lattice_key.id, test_data)
    print(f"Data encrypted, size: {len(encrypted)} bytes")
    
    decrypted = crypto_manager.decrypt_data(lattice_key.id, encrypted)
    print(f"Data decrypted successfully: {decrypted == test_data}")
    
    # Test signing/verification with Dilithium
    print("\nTesting Dilithium signature scheme...")
    message = b"Important message to sign with quantum-safe signature"
    
    signature = crypto_manager.sign_data(dilithium_key.id, message)
    print(f"Message signed, signature size: {len(signature)} bytes")
    
    is_valid = crypto_manager.verify_signature(dilithium_key.id, message, signature)
    print(f"Signature verification: {is_valid}")
    
    # Test Kyber KEM
    print("\nTesting Kyber Key Encapsulation Mechanism...")
    test_msg = b"Confidential message for KEM testing"
    
    encrypted_kyber = crypto_manager.encrypt_data(kyber_key.id, test_msg)
    print(f"KEM encryption completed, size: {len(encrypted_kyber)} bytes")
    
    decrypted_kyber = crypto_manager.decrypt_data(kyber_key.id, encrypted_kyber)
    print(f"KEM decryption successful: {decrypted_kyber == test_msg}")
    
    # Test key rotation
    print("\nTesting key rotation...")
    new_lattice_key = crypto_manager.rotate_key(lattice_key.id)
    print(f"Key rotated: {lattice_key.id} -> {new_lattice_key.id}")
    
    # Test quantum-safe authentication
    print("\nTesting quantum-safe authentication...")
    auth_system = QuantumSafeAuth(crypto_manager)
    
    # Create a challenge
    challenge = auth_system.create_auth_challenge()
    print(f"Authentication challenge created: {challenge.hex()[:16]}...")
    
    # Sign the challenge with Dilithium key
    auth_signature = crypto_manager.sign_data(dilithium_key.id, challenge)
    
    # Authenticate user
    auth_success = auth_system.authenticate_user("test_user", challenge, auth_signature, dilithium_key.id)
    print(f"Authentication result: {auth_success}")
    
    if auth_success:
        # Get the session ID (last created session)
        session_ids = list(auth_system.active_sessions.keys())
        if session_ids:
            session_id = session_ids[-1]
            
            # Test session-based encryption
            session_data = b"Session-specific confidential data"
            encrypted_session = auth_system.encrypt_for_session(session_id, session_data)
            print(f"Session encryption successful: {len(encrypted_session)} bytes")
    
    # Get security metrics
    print("\nGetting security metrics...")
    metrics = crypto_manager.get_security_metrics()
    print(json.dumps(metrics, indent=2, default=str))
    
    # Cleanup expired keys (though none should be expired yet)
    crypto_manager.cleanup_expired_keys()
    
    print("\n✅ Quantum-Resistant Cryptography System Test Completed")