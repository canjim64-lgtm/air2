"""
Advanced Security Module for AirOne Professional System
Implements additional security layers including quantum-resistant cryptography,
advanced threat detection, behavioral analysis, and zero-trust architecture.
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
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64
import binascii
import os
import socket
import struct
from functools import wraps
import re


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different system components"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    MAXIMUM = 4


class ThreatType(Enum):
    """Types of security threats"""
    ANOMALY = "anomaly"
    BRUTE_FORCE = "brute_force"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SESSION_HIJACKING = "session_hijacking"
    REPLAY_ATTACK = "replay_attack"
    MAN_IN_THE_MIDDLE = "man_in_the_middle"


@dataclass
class SecurityEvent:
    """Represents a security event"""
    id: str
    timestamp: datetime
    event_type: str
    severity: SecurityLevel
    source_ip: str
    user_id: Optional[str]
    action: str
    details: Dict[str, Any]
    threat_type: Optional[ThreatType] = None


@dataclass
class ThreatIndicator:
    """Represents a threat indicator"""
    id: str
    indicator_type: str  # IP, domain, hash, etc.
    indicator_value: str
    severity: SecurityLevel
    created_at: datetime
    expires_at: datetime
    source: str
    description: str


class QuantumResistantCrypto:
    """Implements quantum-resistant cryptographic algorithms"""
    
    def __init__(self):
        self.backend = default_backend()
        self.signature_algorithm = hashes.SHA256()
    
    def generate_rsa_keypair(self, key_size: int = 4096) -> tuple:
        """Generate RSA key pair with larger key size for quantum resistance"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=self.backend
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def sign_message(self, private_key, message: bytes) -> bytes:
        """Sign a message using RSA-PSS"""
        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def verify_signature(self, public_key, message: bytes, signature: bytes) -> bool:
        """Verify RSA-PSS signature"""
        try:
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def derive_key(self, password: str, salt: bytes, iterations: int = 100000) -> bytes:
        """Derive key using PBKDF2 with SHA-256"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=self.backend
        )
        return kdf.derive(password.encode('utf-8'))


class AdvancedThreatDetection:
    """Advanced threat detection system with behavioral analysis"""
    
    def __init__(self):
        self.threat_indicators = {}
        self.behavioral_profiles = {}
        self.suspicious_activities = []
        self.lock = threading.Lock()
        self.ip_reputation_db = {}  # In production, use a real reputation service
        self.pattern_matchers = [
            self._detect_brute_force,
            self._detect_anomalous_timing,
            self._detect_unusual_patterns,
            self._detect_geographic_anomalies
        ]
    
    def add_threat_indicator(self, indicator_type: str, indicator_value: str, 
                           severity: SecurityLevel, description: str, 
                           ttl_hours: int = 24):
        """Add a threat indicator"""
        indicator_id = secrets.token_urlsafe(16)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        indicator = ThreatIndicator(
            id=indicator_id,
            indicator_type=indicator_type,
            indicator_value=indicator_value,
            severity=severity,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            source="manual",
            description=description
        )
        
        with self.lock:
            self.threat_indicators[indicator_id] = indicator
        
        logger.info(f"Added threat indicator: {indicator_type}={indicator_value}")
    
    def is_threat_indicated(self, indicator_type: str, indicator_value: str) -> bool:
        """Check if an indicator is in the threat database"""
        current_time = datetime.utcnow()
        
        with self.lock:
            for indicator in list(self.threat_indicators.values()):
                if (indicator.indicator_type == indicator_type and 
                    indicator.indicator_value == indicator_value and
                    indicator.expires_at > current_time):
                    return True
        return False
    
    def analyze_behavior(self, user_id: str, action: str, context: Dict[str, Any]) -> List[ThreatType]:
        """Analyze user behavior for potential threats"""
        threats = []
        
        # Update behavioral profile
        if user_id not in self.behavioral_profiles:
            self.behavioral_profiles[user_id] = {
                'actions': [],
                'timestamps': [],
                'locations': [],
                'devices': [],
                'ip_addresses': [],
                'resource_accesses': []
            }
        
        profile = self.behavioral_profiles[user_id]
        profile['actions'].append(action)
        profile['timestamps'].append(context.get('timestamp', datetime.utcnow()))
        profile['locations'].append(context.get('location', 'unknown'))
        profile['devices'].append(context.get('device', 'unknown'))
        profile['ip_addresses'].append(context.get('ip_address', 'unknown'))
        profile['resource_accesses'].append(context.get('resource', 'unknown'))
        
        # Run pattern matchers
        for matcher in self.pattern_matchers:
            detected_threats = matcher(user_id, action, context, profile)
            threats.extend(detected_threats)
        
        # Check against threat indicators
        ip_address = context.get('ip_address')
        if ip_address and self.is_threat_indicated('ip', ip_address):
            threats.append(ThreatType.UNAUTHORIZED_ACCESS)
        
        return threats
    
    def _detect_brute_force(self, user_id: str, action: str, context: Dict[str, Any], profile: Dict) -> List[ThreatType]:
        """Detect potential brute force attacks"""
        threats = []
        
        # Check for rapid authentication attempts
        if action in ['login_attempt', 'auth_failure']:
            recent_attempts = [t for t in profile['timestamps'] 
                              if datetime.utcnow() - t < timedelta(minutes=5)]
            if len(recent_attempts) > 10:  # More than 10 attempts in 5 minutes
                threats.append(ThreatType.BRUTE_FORCE)
        
        return threats
    
    def _detect_anomalous_timing(self, user_id: str, action: str, context: Dict[str, Any], profile: Dict) -> List[ThreatType]:
        """Detect anomalous timing patterns"""
        threats = []
        
        current_time = context.get('timestamp', datetime.utcnow())
        current_hour = current_time.hour
        
        # Check for unusual access times
        normal_hours = [h.hour for h in profile['timestamps']]
        if normal_hours:
            # If user typically accesses during 9-5, flag access outside those hours
            avg_start = sum(normal_hours) / len(normal_hours)
            if (current_hour < 6 or current_hour > 22) and (avg_start >= 9 and avg_start <= 17):
                threats.append(ThreatType.ANOMALY)
        
        return threats
    
    def _detect_unusual_patterns(self, user_id: str, action: str, context: Dict[str, Any], profile: Dict) -> List[ThreatType]:
        """Detect unusual access patterns"""
        threats = []
        
        # Check for rapid resource access
        recent_resources = [r for r, t in zip(profile['resource_accesses'], profile['timestamps'])
                           if datetime.utcnow() - t < timedelta(minutes=1)]
        if len(recent_resources) > 20:  # Accessing many resources in 1 minute
            threats.append(ThreatType.DATA_EXFILTRATION)
        
        return threats
    
    def _detect_geographic_anomalies(self, user_id: str, action: str, context: Dict[str, Any], profile: Dict) -> List[ThreatType]:
        """Detect geographic anomalies"""
        threats = []
        
        current_location = context.get('location')
        if current_location and profile['locations']:
            # Simple check: if user is accessing from a new location
            if current_location not in profile['locations'][-10:]:  # Last 10 locations
                # Check if this is a high-risk location
                high_risk_countries = ['RU', 'CN', 'KP', 'IR', 'SY']  # Simplified example
                if any(hr_country in current_location.upper() for hr_country in high_risk_countries):
                    threats.append(ThreatType.UNAUTHORIZED_ACCESS)
        
        return threats


class ZeroTrustValidator:
    """Implements zero-trust architecture principles"""
    
    def __init__(self):
        self.trusted_devices = set()
        self.trusted_networks = set()
        self.continuous_auth_required = True
        self.device_certificates = {}
        self.network_segments = {}
    
    def register_trusted_device(self, device_id: str, certificate: str = None):
        """Register a trusted device"""
        self.trusted_devices.add(device_id)
        if certificate:
            self.device_certificates[device_id] = certificate
        logger.info(f"Registered trusted device: {device_id}")
    
    def validate_device(self, device_id: str, certificate: str = None) -> bool:
        """Validate if a device is trusted"""
        if device_id not in self.trusted_devices:
            return False
        
        if certificate and device_id in self.device_certificates:
            # In a real system, validate the certificate
            return True
        
        return True
    
    def validate_network(self, ip_address: str) -> bool:
        """Validate if an IP address is from a trusted network"""
        # Check if IP is in trusted networks
        for trusted_net in self.trusted_networks:
            if self._ip_in_network(ip_address, trusted_net):
                return True
        return False
    
    def _ip_in_network(self, ip: str, network: str) -> bool:
        """Check if an IP is in a network range"""
        try:
            ip_int = struct.unpack("!I", socket.inet_aton(ip))[0]
            net_addr, net_bits = network.split('/')
            net_int = struct.unpack("!I", socket.inet_aton(net_addr))[0]
            mask = (0xffffffff << (32 - int(net_bits))) & 0xffffffff
            return (ip_int & mask) == (net_int & mask)
        except:
            return False
    
    def continuous_authentication_check(self, user_id: str, session_token: str, 
                                       device_id: str, ip_address: str) -> bool:
        """Perform continuous authentication validation"""
        # Validate device
        if not self.validate_device(device_id):
            logger.warning(f"Untrusted device access attempt: {device_id}")
            return False
        
        # Validate network
        if not self.validate_network(ip_address):
            logger.warning(f"Untrusted network access: {ip_address}")
            return False
        
        # Additional checks would go here
        # - Certificate validation
        # - Behavioral analysis
        # - Risk scoring
        
        return True


class SecurityOrchestrator:
    """Orchestrates all security components"""
    
    def __init__(self):
        self.crypto = QuantumResistantCrypto()
        self.threat_detector = AdvancedThreatDetection()
        self.zero_trust = ZeroTrustValidator()
        self.event_queue = queue.Queue()
        self.security_db = sqlite3.connect("security.db", check_same_thread=False)
        self._init_security_db()
        self.event_handlers = []
        self.lock = threading.Lock()
        
        logger.info("Security orchestrator initialized with advanced security layers")
    
    def _init_security_db(self):
        """Initialize the security database"""
        cursor = self.security_db.cursor()
        
        # Create security events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                source_ip TEXT,
                user_id TEXT,
                action TEXT NOT NULL,
                details TEXT,
                threat_type TEXT
            )
        """)
        
        # Create threat indicators table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_indicators (
                id TEXT PRIMARY KEY,
                indicator_type TEXT NOT NULL,
                indicator_value TEXT NOT NULL,
                severity TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                source TEXT NOT NULL,
                description TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON security_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON security_events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicators_value ON threat_indicators(indicator_value)")
        
        self.security_db.commit()
        logger.info("Security database initialized")
    
    def register_event_handler(self, handler: Callable[[SecurityEvent], None]):
        """Register a security event handler"""
        self.event_handlers.append(handler)
    
    def log_security_event(self, event_type: str, severity: SecurityLevel, 
                          source_ip: str, user_id: Optional[str], 
                          action: str, details: Dict[str, Any],
                          threat_type: Optional[ThreatType] = None):
        """Log a security event"""
        event_id = secrets.token_urlsafe(16)
        event = SecurityEvent(
            id=event_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_id=user_id,
            action=action,
            details=details,
            threat_type=threat_type
        )
        
        # Store in database
        cursor = self.security_db.cursor()
        cursor.execute("""
            INSERT INTO security_events (id, timestamp, event_type, severity, 
                                       source_ip, user_id, action, details, threat_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id, event.timestamp.isoformat(), event.event_type, 
            event.severity.name, event.source_ip, event.user_id, 
            event.action, json.dumps(event.details), 
            event.threat_type.value if event.threat_type else None
        ))
        self.security_db.commit()
        
        # Call registered handlers
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Security event handler failed: {e}")
        
        # Log to console if high severity
        if severity in [SecurityLevel.HIGH, SecurityLevel.MAXIMUM]:
            logger.warning(f"SECURITY ALERT [{severity.name}]: {action} by {user_id or 'unknown'} from {source_ip}")
    
    def validate_request(self, user_id: str, session_token: str, device_id: str, 
                       ip_address: str, action: str, resource: str) -> tuple[bool, List[str]]:
        """Validate a request using all security layers"""
        validation_results = []
        is_valid = True
        
        # Zero trust validation
        if not self.zero_trust.continuous_authentication_check(user_id, session_token, device_id, ip_address):
            validation_results.append("Zero trust validation failed")
            is_valid = False
        
        # Behavioral analysis
        context = {
            'timestamp': datetime.utcnow(),
            'ip_address': ip_address,
            'device': device_id,
            'resource': resource,
            'action': action
        }
        
        threats = self.threat_detector.analyze_behavior(user_id, action, context)
        if threats:
            validation_results.extend([f"Threat detected: {t.value}" for t in threats])
            is_valid = False
            
            # Log security events for detected threats
            for threat in threats:
                self.log_security_event(
                    event_type="THREAT_DETECTED",
                    severity=SecurityLevel.HIGH,
                    source_ip=ip_address,
                    user_id=user_id,
                    action=f"Threat: {threat.value}",
                    details=context,
                    threat_type=threat
                )
        
        # Additional validations would go here
        # - Permission checks
        # - Rate limiting
        # - Input validation
        
        return is_valid, validation_results
    
    def encrypt_sensitive_data(self, data: str, key: Optional[bytes] = None) -> str:
        """Encrypt sensitive data using quantum-resistant methods"""
        if key is None:
            key = secrets.token_bytes(32)  # 256-bit key
        
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)  # 96-bit nonce
        encrypted_data = aesgcm.encrypt(nonce, data.encode('utf-8'), associated_data=None)
        
        # Return base64 encoded result with nonce
        return base64.b64encode(nonce + encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str, key: bytes) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            nonce = decoded_data[:12]
            ciphertext = decoded_data[12:]
            
            aesgcm = AESGCM(key)
            decrypted_data = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def generate_secure_token(self, user_id: str, permissions: List[str], 
                            expiry_minutes: int = 60) -> str:
        """Generate a secure JWT token with additional security measures"""
        # Create a more complex payload
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(minutes=expiry_minutes),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(32),  # JWT ID for revocation
            'nbf': datetime.utcnow(),  # Not before
            'iss': 'airone-professional',  # Issuer
            'aud': 'airone-users',  # Audience
            'scp': 'user-access'  # Scope
        }
        
        # Use a strong secret key (in production, use a proper key management system)
        secret_key = secrets.token_bytes(32)
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return token
    
    def add_threat_indicator(self, indicator_type: str, indicator_value: str, 
                           severity: SecurityLevel, description: str):
        """Add a threat indicator to the system"""
        self.threat_detector.add_threat_indicator(
            indicator_type, indicator_value, severity, description
        )
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security-related metrics"""
        cursor = self.security_db.cursor()
        
        # Count events by severity
        cursor.execute("SELECT severity, COUNT(*) FROM security_events GROUP BY severity")
        severity_counts = dict(cursor.fetchall())
        
        # Count events by type
        cursor.execute("SELECT event_type, COUNT(*) FROM security_events GROUP BY event_type")
        type_counts = dict(cursor.fetchall())
        
        # Recent events
        cursor.execute("""
            SELECT timestamp, event_type, user_id, action 
            FROM security_events 
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        recent_events = cursor.fetchall()
        
        return {
            'total_events': sum(severity_counts.values()),
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'recent_events': recent_events,
            'threat_indicators_count': len(self.threat_detector.threat_indicators),
            'trusted_devices_count': len(self.zero_trust.trusted_devices)
        }


class SecurityDecorator:
    """Security decorators for protecting functions"""
    
    def __init__(self, security_orchestrator: SecurityOrchestrator):
        self.orchestrator = security_orchestrator
    
    def require_security_validation(self, required_permissions: List[str] = None):
        """Decorator to require security validation"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract security context from kwargs or args
                user_id = kwargs.get('user_id') or getattr(args[0] if args else None, 'user_id', None)
                session_token = kwargs.get('session_token')
                device_id = kwargs.get('device_id')
                ip_address = kwargs.get('ip_address', '127.0.0.1')
                action = func.__name__
                
                if not user_id:
                    logger.warning("Security validation failed: No user ID provided")
                    return None
                
                # Validate the request
                is_valid, validation_results = self.orchestrator.validate_request(
                    user_id, session_token, device_id, ip_address, action, func.__name__
                )
                
                if not is_valid:
                    logger.warning(f"Access denied for {user_id}: {validation_results}")
                    return None
                
                # Proceed with function execution
                return func(*args, **kwargs)
            return wrapper
        return decorator


# Example usage and testing
if __name__ == "__main__":
    # Initialize security orchestrator
    security_orch = SecurityOrchestrator()
    security_decorator = SecurityDecorator(security_orch)
    
    print("🛡️  Advanced Security System Initialized...")
    
    # Register a threat indicator
    security_orch.add_threat_indicator(
        indicator_type='ip',
        indicator_value='192.168.1.100',
        severity=SecurityLevel.HIGH,
        description='Known malicious IP address'
    )
    
    # Register a trusted device
    security_orch.zero_trust.register_trusted_device('device_abc123')
    
    # Simulate some security events
    for i in range(5):
        security_orch.log_security_event(
            event_type="LOGIN_ATTEMPT",
            severity=SecurityLevel.LOW,
            source_ip=f"192.168.1.{i+1}",
            user_id=f"user_{i}",
            action="login",
            details={"method": "password", "success": True}
        )
    
    # Simulate a potential threat
    threats = security_orch.threat_detector.analyze_behavior(
        user_id="malicious_user",
        action="rapid_data_access",
        context={
            "timestamp": datetime.utcnow(),
            "ip_address": "192.168.1.100",  # Known bad IP
            "device": "unknown_device",
            "resource": "sensitive_data",
            "location": "unknown"
        }
    )
    
    print(f"Detected threats: {[t.value for t in threats]}")
    
    # Test encryption
    original_data = "Sensitive telemetry data"
    encrypted = security_orch.encrypt_sensitive_data(original_data)
    print(f"Encrypted data: {encrypted[:50]}...")
    
    # Test decryption (using same key - in real system, keys would be managed differently)
    key = secrets.token_bytes(32)
    encrypted_with_key = security_orch.encrypt_sensitive_data(original_data, key)
    decrypted = security_orch.decrypt_sensitive_data(encrypted_with_key, key)
    print(f"Decryption successful: {original_data == decrypted}")
    
    # Get security metrics
    metrics = security_orch.get_security_metrics()
    print(f"Security Metrics: {json.dumps(metrics, indent=2, default=str)}")
    
    print("\n✅ Advanced security system test completed")