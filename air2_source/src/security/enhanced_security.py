"""
Enhanced Security for AirOne v3.0
Handles security features and encryption
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityManager:
    """Security manager for AirOne system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.encryption_key = self._generate_or_load_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.access_log = []
        self.failed_attempts = 0
        self.max_failed_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        self.locked_until = None
        
        # Session management
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 hour
        
    def _generate_or_load_key(self) -> bytes:
        """Generate or load encryption key"""
        # In a real implementation, this would securely store/load the key
        # For now, we'll generate a new one each time
        return Fernet.generate_key()
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet symmetric encryption"""
        encrypted_data = self.cipher_suite.encrypt(data.encode('utf-8'))
        return encrypted_data.decode()
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt data using Fernet symmetric encryption"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_data.decode()
        except Exception:
            # Log the decryption failure
            self.log_access("SECURITY", "Decryption failed", {"encrypted_data_length": len(encrypted_data)})
            return None
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """Hash a password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    def verify_password(self, password: str, hashed: bytes, salt: bytes) -> bool:
        """Verify a password against its hash"""
        try:
            _, computed_salt = self.hash_password(password, salt)
            # Recompute the hash with the provided salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            computed_key = kdf.derive(password.encode('utf-8'))
            return hmac.compare_digest(hashed, computed_key)
        except Exception:
            return False
    
    def generate_session_token(self, user_id: str) -> str:
        """Generate a secure session token"""
        token_data = f"{user_id}:{datetime.now().isoformat()}:{secrets.token_hex(16)}"
        token = hashlib.sha256(token_data.encode('utf-8')).hexdigest()
        
        # Store session info
        self.active_sessions[token] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=self.session_timeout)
        }
        
        return token
    
    def validate_session_token(self, token: str) -> bool:
        """Validate a session token"""
        if token not in self.active_sessions:
            return False
            
        session_info = self.active_sessions[token]
        if datetime.now() > session_info['expires_at']:
            # Token expired, remove it
            del self.active_sessions[token]
            return False
            
        return True
    
    def revoke_session_token(self, token: str) -> bool:
        """Revoke a session token"""
        if token in self.active_sessions:
            del self.active_sessions[token]
            return True
        return False
    
    def check_authentication(self, username: str, password: str) -> bool:
        """Check user authentication against internal registry"""
        # Check if locked out
        if self.is_locked_out():
            self.log_access("AUTH", "Blocked - Account locked", {"username": username})
            return False
        
        # Internal user registry (In real system, load from encrypted DB)
        # Using the admin password generated for v4.0 Ultimate
        users = {
            "admin": "cyqPmxSpuPQgREFa",
            "operator": "operator_v4_access",
            "mission_ctrl": "mc_secure_2026"
        }
        
        is_valid = users.get(username) == password
        
        if is_valid:
            self.failed_attempts = 0  # Reset on successful login
            self.log_access("AUTH", "Login successful", {"username": username})
            return True
        else:
            self.failed_attempts += 1
            self.log_access("AUTH", "Login failed", {"username": username})
            
            # Check if we need to lock the account
            if self.failed_attempts >= self.max_failed_attempts:
                self.locked_until = datetime.now() + timedelta(seconds=self.lockout_duration)
                self.log_access("AUTH", "Account locked due to failed attempts", {"username": username})
            
            return False
    
    def is_locked_out(self) -> bool:
        """Check if the system is locked out due to failed attempts"""
        if self.locked_until is None:
            return False
            
        if datetime.now() < self.locked_until:
            return True
        else:
            # Lockout period has expired
            self.locked_until = None
            self.failed_attempts = 0
            return False
    
    def log_access(self, category: str, action: str, details: Dict[str, Any] = None):
        """Log security-related events"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'action': action,
            'details': details or {},
            'session_info': {}
        }
        
        self.access_log.append(log_entry)
        
        # Keep log size manageable
        if len(self.access_log) > 10000:
            self.access_log = self.access_log[-5000:]  # Keep last 5000 entries
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get security status information"""
        return {
            'failed_attempts': self.failed_attempts,
            'max_failed_attempts': self.max_failed_attempts,
            'is_locked_out': self.is_locked_out(),
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'active_sessions': len(self.active_sessions),
            'total_logged_events': len(self.access_log),
            'engine_version': '3.0.0'
        }
    
    def encrypt_telemetry_packet(self, packet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt a telemetry packet"""
        # Serialize the packet data
        serialized_data = str(packet_data)
        
        # Encrypt the data
        encrypted_data = self.encrypt_data(serialized_data)
        
        # Return a new packet with encrypted data
        encrypted_packet = {
            'encrypted_payload': encrypted_data,
            'encryption_method': 'fernet_aes_128',
            'original_timestamp': packet_data.get('timestamp', datetime.now().isoformat()),
            'encrypted_at': datetime.now().isoformat()
        }
        
        return encrypted_packet
    
    def decrypt_telemetry_packet(self, encrypted_packet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Decrypt a telemetry packet"""
        if 'encrypted_payload' not in encrypted_packet:
            return None
            
        # Decrypt the payload
        decrypted_data = self.decrypt_data(encrypted_packet['encrypted_payload'])
        if decrypted_data is None:
            return None
            
        # In a real implementation, we would deserialize the data back to a dict
        # For now, we'll return a basic structure
        try:
            # This is a simplified representation - in reality, you'd deserialize the actual data
            return {
                'decrypted': True,
                'original_data': decrypted_data,  # In practice, this would be deserialized
                'decryption_method': encrypted_packet.get('encryption_method'),
                'decrypted_at': datetime.now().isoformat()
            }
        except Exception:
            return None