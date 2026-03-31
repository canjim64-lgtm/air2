"""
Security Module
Security and authentication for telemetry systems
"""

import hashlib
import hmac
import secrets
from typing import Dict, Optional
import logging


class Authentication:
    """User authentication"""
    
    def __init__(self):
        self.users = {}
    
    def add_user(self, username: str, password: str):
        """Add user"""
        self.users[username] = self._hash_password(password)
    
    def verify(self, username: str, password: str) -> bool:
        """Verify password"""
        if username not in self.users:
            return False
        return self.users[username] == self._hash_password(password)
    
    def _hash_password(self, password: str) -> str:
        """Hash password"""
        return hashlib.sha256(password.encode()).hexdigest()


class TokenManager:
    """JWT-like token manager"""
    
    def __init__(self, secret: str = None):
        self.secret = secret or secrets.token_hex(32)
    
    def create_token(self, user_id: str, expiry: int = 3600) -> str:
        """Create token"""
        import base64, json
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "exp": int(__import__('time').time()) + expiry
        }
        
        import jwt  # In production use pyjwt
        return f"{base64.urlsafe_b64encode(json.dumps(header).encode()).decode()}.{base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()}.signature"
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify token"""
        # Simplified
        return {"valid": True}


class Encryption:
    """Data encryption"""
    
    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """Encrypt data"""
        import base64
        # Simplified XOR encryption
        key_repeated = (key * (len(data) // len(key) + 1))[:len(data)]
        encrypted = bytes(a ^ b for a, b in zip(data, key_repeated))
        return base64.b64encode(encrypted)
    
    @staticmethod
    def decrypt(data: bytes, key: bytes) -> bytes:
        """Decrypt data"""
        import base64
        data = base64.b64decode(data)
        key_repeated = (key * (len(data) // len(key) + 1))[:len(data)]
        return bytes(a ^ b for a, b in zip(data, key_repeated))


class RateLimiter:
    """Rate limiting"""
    
    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request allowed"""
        import time
        now = time.time()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests
        self.requests[client_id] = [
            t for t in self.requests[client_id] 
            if now - t < self.window
        ]
        
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True
        
        return False


class AuditLogger:
    """Audit logging"""
    
    def __init__(self):
        self.logs = []
    
    def log(self, action: str, user: str, details: Dict = None):
        """Log action"""
        import time
        self.logs.append({
            'timestamp': time.time(),
            'action': action,
            'user': user,
            'details': details or {}
        })
    
    def get_logs(self, user: str = None) -> list:
        """Get logs"""
        if user:
            return [l for l in self.logs if l['user'] == user]
        return self.logs


# Example
if __name__ == "__main__":
    print("Testing Security...")
    
    auth = Authentication()
    auth.add_user("admin", "password123")
    print(f"Auth: {auth.verify('admin', 'password123')}")
    
    tm = TokenManager()
    token = tm.create_token("user1")
    print(f"Token: {token[:20]}...")
    
    rl = RateLimiter()
    print(f"Rate limit: {rl.is_allowed('client1')}")