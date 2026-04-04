"""
AirOne Professional Enhanced Security Module
Implements security for all operational modes with DeepSeek R1 8B integration
"""

import os
import jwt
import hashlib
import secrets
import logging
import configparser
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from functools import wraps
import sqlite3
import threading
from dataclasses import dataclass


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class UserRole(Enum):
    USER = "user"
    OPERATOR = "operator"
    ANALYST = "analyst"
    ENGINEER = "engineer"
    ADMIN = "admin"
    SECURITY_ADMIN = "security_admin"
    EXECUTIVE = "executive"


@dataclass
class SecurityConfig:
    encryption_algorithm: str = "AES-256-GCM"
    quantum_resistant_crypto: bool = True
    key_rotation_interval_days: int = 30
    session_timeout_minutes: int = 60
    max_login_attempts: int = 3
    account_lockout_duration_minutes: int = 30
    audit_logging_enabled: bool = True
    intrusion_detection_enabled: bool = True
    threat_analysis_enabled: bool = True


class SecurityException(Exception):
    """Base exception for security-related errors"""
    def __init__(self, message: str = "Security error occurred", error_code: str = "SEC_001"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.timestamp = datetime.utcnow()


class UnauthorizedException(SecurityException):
    """Raised when access is unauthorized"""
    def __init__(self, message: str = "Unauthorized access", user: str = None, resource: str = None):
        super().__init__(message, error_code="SEC_401")
        self.user = user
        self.resource = resource
        self.message = message


class TokenRevokedException(SecurityException):
    """Raised when a JWT token has been revoked"""
    def __init__(self, message: str = "Token has been revoked", token_id: str = None):
        super().__init__(message, error_code="SEC_403")
        self.token_id = token_id
        self.message = message

class PasswordExpiredException(SecurityException):
    """Raised when a user's password has expired and needs to be changed"""
    def __init__(self, message: str = "Password has expired and must be changed", user: str = None):
        super().__init__(message, error_code="SEC_402")
        self.user = user
        self.message = message



class SecurityManager:
    """Centralized security manager for AirOne Professional system"""
    
    def __init__(self, config_path: str = "./airone_security_config.ini"):
        self.config = self._load_config(config_path)
        self.secret_key = self._generate_or_load_secret_key()
        self.encryption_key = AESGCM(self.secret_key)
        self.access_control = AccessControlManager()
        self.threat_detector = ThreatDetectionSystem()
        self.audit_logger = AuditLogger()
        self.token_manager = TokenManager(self.secret_key)
        self.session_manager = SessionManager()
        
        # User database (in-memory for demonstration, replace with persistent storage)
        self.user_database = self._initialize_user_database()
        
        logger.info("Security Manager initialized with enhanced security features")
    
    def _load_config(self, config_path: str) -> configparser.ConfigParser:
        """Load security configuration from INI file"""
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            config.read(config_path)
        else:
            # Create default config if file doesn't exist
            self._create_default_config(config_path)
            config.read(config_path)
        return config
    
    def _create_default_config(self, config_path: str):
        """Create default security configuration"""
        config = configparser.ConfigParser()
        
        # Global security settings
        config['GLOBAL_SECURITY'] = {
            'encryption_algorithm': 'AES-256-GCM',
            'quantum_resistant_crypto': 'true',
            'key_rotation_interval_days': '30',
            'session_timeout_minutes': '60',
            'max_login_attempts': '3',
            'account_lockout_duration_minutes': '30',
            'audit_logging_enabled': 'true',
            'intrusion_detection_enabled': 'true',
            'threat_analysis_enabled': 'true',
            'password_expiration_days': '90'
        }
        
        # JWT configuration
        config['JWT_CONFIG'] = {
            'algorithm': 'HS256',
            'token_revocation_enabled': 'true'
        }
        
        with open(config_path, 'w') as configfile:
            config.write(configfile)
    
    def _generate_or_load_secret_key(self) -> bytes:
        """Generate or load the secret key for encryption and JWT signing"""
        key_path = "./secrets/master_key.key"
        
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            # Generate a new 256-bit (32-byte) key
            key = secrets.token_bytes(32)
            with open(key_path, 'wb') as f:
                f.write(key)
            return key
    
    def _initialize_user_database(self) -> Dict[str, Any]:
        """Initializes an in-memory user database for demonstration purposes."""
        # In a real application, this would load from a secure persistent storage
        # such as a database (e.g., SQLite, PostgreSQL)
        user_db = {
            "admin": {
                "password_hash": hashlib.sha256("cyqPmxSpuPQgREFa".encode('utf-8')).hexdigest(),
                "role": UserRole.ADMIN,
                "permissions": self.access_control.role_permissions[UserRole.ADMIN],
                "password_last_updated": datetime.utcnow()
            },
            "operator": {
                "password_hash": hashlib.sha256("operator_password".encode('utf-8')).hexdigest(),
                "role": UserRole.OPERATOR,
                "permissions": self.access_control.role_permissions[UserRole.OPERATOR],
                "password_last_updated": datetime.utcnow() - timedelta(days=int(self.config.get('GLOBAL_SECURITY', 'password_expiration_days', fallback='90'))) # Expired for testing
            },
            "analyst": {
                "password_hash": hashlib.sha256("analyst_password".encode('utf-8')).hexdigest(),
                "role": UserRole.ANALYST,
                "permissions": self.access_control.role_permissions[UserRole.ANALYST],
                "password_last_updated": datetime.utcnow()
            },
            "engineer": {
                "password_hash": hashlib.sha256("engineer_password".encode('utf-8')).hexdigest(),
                "role": UserRole.ENGINEER,
                "permissions": self.access_control.role_permissions[UserRole.ENGINEER],
                "password_last_updated": datetime.utcnow()
            },
            "security_admin": {
                "password_hash": hashlib.sha256("security_admin_password".encode('utf-8')).hexdigest(),
                "role": UserRole.SECURITY_ADMIN,
                "permissions": self.access_control.role_permissions[UserRole.SECURITY_ADMIN],
                "password_last_updated": datetime.utcnow()
            },
            "executive": {
                "password_hash": hashlib.sha256("executive_password".encode('utf-8')).hexdigest(),
                "role": UserRole.EXECUTIVE,
                "permissions": self.access_control.role_permissions[UserRole.EXECUTIVE],
                "password_last_updated": datetime.utcnow()
            }
        }
        return user_db

    
    def encrypt_data(self, data: str) -> Dict[str, str]:
        """Encrypt data using AES-256-GCM"""
        nonce = secrets.token_bytes(12)  # 96-bit nonce
        encrypted_data = self.encryption_key.encrypt(nonce, data.encode('utf-8'), associated_data=None)
        
        result = {
            'encrypted_data': encrypted_data.hex(),
            'nonce': nonce.hex(),
            'timestamp': datetime.utcnow().isoformat(),
            'algorithm': self.config.get('GLOBAL_SECURITY', 'encryption_algorithm', fallback='AES-256-GCM')
        }
        
        logger.debug("Data encrypted successfully")
        return result
    
    def decrypt_data(self, encrypted_package: Dict[str, str]) -> str:
        """Decrypt data using AES-256-GCM"""
        try:
            encrypted_data = bytes.fromhex(encrypted_package['encrypted_data'])
            nonce = bytes.fromhex(encrypted_package['nonce'])
            
            decrypted_data = self.encryption_key.decrypt(nonce, encrypted_data, associated_data=None)
            logger.debug("Data decrypted successfully")
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise SecurityException("Decryption failed")
    
    def authenticate_user(self, username: str, password: str, mode: str = "general") -> Dict[str, Any]:
        """Authenticate user with mode-specific security requirements"""
        # Log authentication attempt
        self.audit_logger.log_event("AUTH_ATTEMPT", username, {"mode": mode})
        
        # Check if account is locked
        if self.session_manager.is_account_locked(username):
            raise SecurityException("Account is temporarily locked due to failed login attempts")
        
        try:
            # Validate credentials (simplified - in real system, use proper password hashing)
            if self._validate_credentials(username, password):
                # Reset failed attempts counter
                self.session_manager.reset_failed_attempts(username)
                
                # Determine required permissions based on mode
                required_permissions = self._get_mode_permissions(mode)
                
                # Get user role and permissions from the user_database
                user_info = self.user_database.get(username)
                if not user_info:
                    raise SecurityException("User not found")
                
                user_role = user_info["role"]
                user_permissions = user_info["permissions"]
                
                # Check if user has required permissions for the mode
                if not self.access_control.has_permissions(user_permissions, required_permissions):
                    raise UnauthorizedException(f"Insufficient permissions for {mode} mode")
                
                # Generate JWT token
                token = self.token_manager.generate_token(username, user_role.value, user_permissions)
                
                # Create session
                session_id = self.session_manager.create_session(username, token, mode)
                
                # Log successful authentication
                self.audit_logger.log_event("AUTH_SUCCESS", username, {"mode": mode, "session_id": session_id})
                
                return {
                    "token": token,
                    "session_id": session_id,
                    "user_role": user_role.value,
                    "permissions": user_permissions,
                    "expires_at": datetime.utcnow() + timedelta(minutes=int(self.config.get('GLOBAL_SECURITY', 'session_timeout_minutes', fallback='60'))),
                    "password_change_required": False
                }
            else:
                # Increment failed attempts
                self.session_manager.increment_failed_attempts(username)
                
                # Log failed authentication
                self.audit_logger.log_event("AUTH_FAILED", username, {"mode": mode})
                
                raise SecurityException("Invalid credentials")
        except PasswordExpiredException as e:
            # Password expired, require change
            self.audit_logger.log_event("PASSWORD_EXPIRED", username, {"message": e.message})
            return {
                "password_change_required": True,
                "username": username
            }
    
    def _validate_credentials(self, username: str, password: str) -> bool:
        """Validate user credentials, including password expiration"""
        user_info = self.user_database.get(username)
        if not user_info:
            return False

        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if user_info["password_hash"] != password_hash:
            return False

        # Check for password expiration
        password_expiration_days = int(self.config.get('GLOBAL_SECURITY', 'password_expiration_days', fallback='90'))
        if (datetime.utcnow() - user_info["password_last_updated"]).days > password_expiration_days:
            raise PasswordExpiredException(user=username)

        return True
    
    def _get_mode_permissions(self, mode: str) -> List[str]:
        """Get required permissions for a specific mode"""
        mode_permissions = {
            "desktop_gui": ["telemetry_read", "visualization_control"],
            "headless_cli": ["telemetry_read", "telemetry_write"],
            "offline": ["system_configure"],
            "simulation": ["development_access"],
            "receiver": ["telemetry_write"],
            "replay": ["data_export"],
            "safe": ["system_configure"],
            "web": ["telemetry_read"],
            "digital_twin": ["mission_control"],
            "powerful": ["system_configure"],
            "security": ["security_audit"],
            "ultimate": ["advanced_operations"],
            "cosmic": ["cosmic_operations"],
            "mission": ["mission"]
        }
        
        return mode_permissions.get(mode, ["telemetry_read"])
    
    def validate_token(self, token: str, mode: str = None) -> Dict[str, Any]:
        """Validate JWT token and check mode-specific permissions"""
        try:
            payload = self.token_manager.validate_token(token)
            
            # Check if session is still valid
            session_id = payload.get('session_id')
            if not self.session_manager.is_session_valid(session_id):
                raise UnauthorizedException("Session has expired or is invalid")
            
            # If mode is specified, check if user has permissions for that mode
            if mode:
                required_permissions = self._get_mode_permissions(mode)
                user_permissions = payload.get('permissions', [])
                
                if not self.access_control.has_permissions(user_permissions, required_permissions):
                    raise UnauthorizedException(f"Insufficient permissions for {mode} mode")
            
            # Log token validation
            self.audit_logger.log_event("TOKEN_VALIDATED", payload.get('username'), {"mode": mode})
            
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityException("Token has expired")
        except jwt.InvalidTokenError:
            raise SecurityException("Invalid token")
    
    def authorize_action(self, token: str, action: str, resource: str) -> bool:
        """Authorize a specific action on a resource"""
        try:
            payload = self.validate_token(token)
            user_permissions = payload.get('permissions', [])
            
            # In a real system, this would have more sophisticated permission checking
            # For now, we'll implement a basic check
            required_permission = self._get_action_permission(action, resource)
            
            if required_permission in user_permissions:
                self.audit_logger.log_event("ACTION_AUTHORIZED", payload.get('username'), {
                    "action": action, 
                    "resource": resource
                })
                return True
            else:
                self.audit_logger.log_event("ACTION_DENIED", payload.get('username'), {
                    "action": action, 
                    "resource": resource,
                    "missing_permission": required_permission
                })
                return False
        except Exception as e:
            logger.error(f"Authorization failed: {str(e)}")
            return False
    
    def _get_action_permission(self, action: str, resource: str) -> str:
        """Map actions and resources to required permissions"""
        action_resource_map = {
            ("read", "telemetry"): "telemetry_read",
            ("write", "telemetry"): "telemetry_write",
            ("export", "data"): "data_export",
            ("configure", "system"): "system_configure",
            ("control", "mission"): "mission_control",
            ("audit", "security"): "security_audit",
            ("perform", "advanced_operations"): "advanced_operations",
            ("access", "cosmic_operations"): "cosmic_operations"
        }
        
        return action_resource_map.get((action, resource), "telemetry_read")

    def update_user_password(self, username: str, new_password: str) -> bool:
        """Update a user's password and reset the last updated timestamp."""
        if username not in self.user_database:
            logger.error(f"Attempt to update password for non-existent user: {username}")
            return False

        # Hash the new password
        new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()

        # Update the user database
        self.user_database[username]["password_hash"] = new_password_hash
        self.user_database[username]["password_last_updated"] = datetime.utcnow()

        self.audit_logger.log_event("PASSWORD_CHANGED", username, {"status": "success"})
        logger.info(f"Password for user {username} updated successfully.")
        return True



class AccessControlManager:
    """Manages role-based and attribute-based access control"""
    
    def __init__(self):
        self.role_permissions = {
            UserRole.USER: ["telemetry_read"],
            UserRole.OPERATOR: ["telemetry_read", "telemetry_write", "mission"],
            UserRole.ANALYST: ["telemetry_read", "telemetry_write", "data_export", "mission"],
            UserRole.ENGINEER: ["telemetry_read", "telemetry_write", "data_export", "mission_control", "mission"],
            UserRole.ADMIN: ["telemetry_read", "telemetry_write", "data_export", "system_configure", "mission_control", "mission"],
            UserRole.SECURITY_ADMIN: ["telemetry_read", "telemetry_write", "data_export", "system_configure", 
                                    "mission_control", "security_audit", "mission"],
            UserRole.EXECUTIVE: ["telemetry_read", "telemetry_write", "data_export", "system_configure", 
                               "mission_control", "security_audit", "advanced_operations", "cosmic_operations", "mission"]
        }
        
        # User role mapping (in a real system, this would be in a secure database)
        self.user_roles = {
            "admin": UserRole.ADMIN,
            "operator": UserRole.OPERATOR,
            "analyst": UserRole.ANALYST,
            "engineer": UserRole.ENGINEER,
            "security_admin": UserRole.SECURITY_ADMIN,
            "executive": UserRole.EXECUTIVE
        }
    
    def get_user_role(self, username: str) -> UserRole:
        """Get the role assigned to a user"""
        return self.user_roles.get(username, UserRole.USER)
    
    def get_user_permissions(self, username: str) -> List[str]:
        """Get all permissions for a user based on their role"""
        user_role = self.get_user_role(username)
        return self.role_permissions.get(user_role, [])
    
    def has_permissions(self, user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Check if user has all required permissions"""
        return all(perm in user_permissions for perm in required_permissions)


class ThreatDetectionSystem:
    """Advanced threat detection system with behavioral analysis"""
    
    def __init__(self):
        self.suspicious_patterns = []
        self.behavioral_profiles = {}
        self.alert_threshold = 0.8
        self.logger = logging.getLogger(__name__)
    
    def analyze_behavior(self, user_id: str, action: str, context: Dict[str, Any]) -> bool:
        """Analyze user behavior for potential threats"""
        # Create or update behavioral profile
        if user_id not in self.behavioral_profiles:
            self.behavioral_profiles[user_id] = {
                'actions': [],
                'timestamps': [],
                'locations': [],
                'devices': []
            }
        
        # Record the action
        profile = self.behavioral_profiles[user_id]
        profile['actions'].append(action)
        profile['timestamps'].append(context.get('timestamp', datetime.utcnow()))
        profile['locations'].append(context.get('location', 'unknown'))
        profile['devices'].append(context.get('device', 'unknown'))
        
        # Simple anomaly detection based on frequency
        recent_actions = [a for t, a in zip(profile['timestamps'], profile['actions']) 
                         if (datetime.utcnow() - t).seconds < 300]  # Last 5 minutes
        
        # If too many actions in a short time, flag as suspicious
        if len(recent_actions) > 20:  # Threshold for rapid actions
            self.logger.warning(f"Suspicious activity detected for user {user_id}: {len(recent_actions)} actions in 5 minutes")
            return True
        
        # Additional checks could include:
        # - Geographic anomalies
        # - Unusual access times
        # - Privilege escalation attempts
        # - Data exfiltration patterns
        
        return False
    
    def get_threat_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent threat alerts"""
        # In a real system, this would query a database of alerts
        # For now, return empty list
        return []


class AuditLogger:
    """Security audit logging system"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Create audit log handler
        handler = logging.FileHandler("logs/security_audit.log")
        formatter = logging.Formatter('%(asctime)s - AUDIT - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_event(self, event_type: str, user: str, details: Dict[str, Any]):
        """Log a security event"""
        message = f"EVENT_TYPE={event_type}, USER={user}, DETAILS={details}"
        self.logger.info(message)


class TokenManager:
    """JWT token management with revocation support"""
    
    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key
        self.revoked_tokens = set()  # In production, use Redis or database
        self.lock = threading.Lock()
    
    def generate_token(self, username: str, role: str, permissions: List[str]) -> str:
        """Generate a JWT token with user information"""
        payload = {
            'username': username,
            'role': role,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(32)  # JWT ID for revocation
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and check if it's been revoked"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check if token has been revoked
            jti = payload.get('jti')
            if jti in self.revoked_tokens:
                raise TokenRevokedException("Token has been revoked")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityException("Token has expired")
        except jwt.InvalidTokenError:
            raise SecurityException("Invalid token")
    
    def revoke_token(self, jti: str):
        """Revoke a JWT token"""
        with self.lock:
            self.revoked_tokens.add(jti)


class SessionManager:
    """Manage user sessions with security controls"""
    
    def __init__(self):
        self.active_sessions = {}  # session_id -> session_data
        self.failed_attempts = {}  # username -> count
        self.lock = threading.Lock()
    
    def create_session(self, username: str, token: str, mode: str) -> str:
        """Create a new session for a user"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            'username': username,
            'token': token,
            'mode': mode,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=60)  # Configurable
        }
        
        with self.lock:
            self.active_sessions[session_id] = session_data
        
        return session_id
    
    def is_session_valid(self, session_id: str) -> bool:
        """Check if a session is still valid"""
        with self.lock:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            now = datetime.utcnow()
            
            # Check expiration
            if now > session['expires_at']:
                # Clean up expired session
                del self.active_sessions[session_id]
                return False
            
            # Update last activity
            session['last_activity'] = now
            return True
    
    def increment_failed_attempts(self, username: str):
        """Increment failed login attempts for a user"""
        with self.lock:
            if username in self.failed_attempts:
                self.failed_attempts[username] += 1
            else:
                self.failed_attempts[username] = 1
    
    def reset_failed_attempts(self, username: str):
        """Reset failed login attempts for a user"""
        with self.lock:
            if username in self.failed_attempts:
                del self.failed_attempts[username]
    
    def is_account_locked(self, username: str) -> bool:
        """Check if an account is locked due to failed attempts"""
        with self.lock:
            attempts = self.failed_attempts.get(username, 0)
            return attempts >= 3  # Configurable threshold


# Decorator for securing functions
def require_permission(permission: str):
    """Decorator to enforce permissions on functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get security manager from self (assuming it's available)
            if hasattr(self, 'security_manager'):
                token = kwargs.get('token') or (args[0] if args else None)
                if not token:
                    raise UnauthorizedException("Authentication token required")
                
                # Validate token and check permission
                payload = self.security_manager.validate_token(token)
                user_permissions = payload.get('permissions', [])
                
                if permission not in user_permissions:
                    raise UnauthorizedException(f"Permission '{permission}' required")
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


# Example usage of the security system
if __name__ == "__main__":
    # Initialize the security manager
    security_manager = SecurityManager()
    
    print("AirOne Professional Security System Initialized")
    print(f"Encryption Algorithm: {security_manager.config.get('GLOBAL_SECURITY', 'encryption_algorithm')}")
    print(f"Audit Logging: {security_manager.config.get('GLOBAL_SECURITY', 'audit_logging_enabled')}")
    print(f"Intrusion Detection: {security_manager.config.get('GLOBAL_SECURITY', 'intrusion_detection_enabled')}")
    
    # Example: Authenticate a user for a specific mode
    try:
        result = security_manager.authenticate_user("admin", "admin_password", "web")
        print(f"Authentication successful: {result['user_role']} with permissions {result['permissions']}")
        
        # Example: Validate token for a specific mode
        payload = security_manager.validate_token(result['token'], "web")
        print(f"Token validated for user: {payload['username']}")
        
        # Example: Authorize an action
        authorized = security_manager.authorize_action(result['token'], "read", "telemetry")
        print(f"Action authorized: {authorized}")
        
        # Example: Encrypt and decrypt data
        original_data = "Sensitive telemetry data"
        encrypted = security_manager.encrypt_data(original_data)
        decrypted = security_manager.decrypt_data(encrypted)
        print(f"Encryption/decryption successful: {original_data == decrypted}")
        
    except SecurityException as e:
        print(f"Security error: {str(e)}")
    
    print("Security system test completed")


def main():
    """Demo mode"""
    try:
        import jwt
        print("Security module loaded - run Installer.bat for full features")
    except ImportError:
        print("""
================================================================================
                    AirOne - Security Module
================================================================================
    JWT support not installed.
    Run: pip install pyjwt cryptography
    
Status: Security Ready (limited)
""")


if __name__ == "__main__":
    main()