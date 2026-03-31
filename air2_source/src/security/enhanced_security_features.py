"""
Enhanced Security Features for AirOne v3.0
Additional security modules and features
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import jwt


class ThreatDetectionSystem:
    """
    Advanced threat detection system with behavioral analysis
    """
    
    def __init__(self):
        self.threat_patterns = {}
        self.behavioral_profiles = {}
        self.alerts = []
        self.security_incidents = []
        self.whitelist = set()
        self.blacklist = set()
        
    def analyze_behavior(self, user_id: str, action: str, context: Dict[str, Any]) -> bool:
        """Analyze user behavior for anomalies"""
        if user_id not in self.behavioral_profiles:
            self.behavioral_profiles[user_id] = {
                'actions': [],
                'timestamps': [],
                'locations': [],
                'devices': [],
                'normal_patterns': {}
            }
        
        profile = self.behavioral_profiles[user_id]
        
        # Record the action
        profile['actions'].append(action)
        profile['timestamps'].append(context.get('timestamp', time.time()))
        profile['locations'].append(context.get('location', 'unknown'))
        profile['devices'].append(context.get('device', 'unknown'))
        
        # Keep only recent history (last 1000 actions)
        if len(profile['actions']) > 1000:
            profile['actions'] = profile['actions'][-1000:]
            profile['timestamps'] = profile['timestamps'][-1000:]
            profile['locations'] = profile['locations'][-1000:]
            profile['devices'] = profile['devices'][-1000:]
        
        # Check for anomalies
        anomalies = []
        
        # Check for unusual timing (access at odd hours)
        hour = datetime.fromtimestamp(context.get('timestamp', time.time())).hour
        if hour < 6 or hour > 22:  # Outside normal business hours
            if user_id not in profile['normal_patterns'].get('late_hours', []):
                anomalies.append("access_outside_business_hours")
        
        # Check for unusual location
        current_location = context.get('location', 'unknown')
        if current_location not in profile.get('locations', [])[:10]:  # New location
            anomalies.append("access_from_new_location")
        
        # Check for rapid successive actions
        recent_actions = [ts for ts in profile['timestamps'] 
                         if time.time() - ts < 60]  # Actions in last minute
        if len(recent_actions) > 10:  # Too many actions in short time
            anomalies.append("rapid_successive_actions")
        
        # Check for unusual device
        current_device = context.get('device', 'unknown')
        if current_device not in profile.get('devices', [])[:5]:  # New device
            anomalies.append("access_from_new_device")
        
        # Log threat if anomalies detected
        if anomalies:
            self._log_threat(user_id, action, anomalies, context)
            return True  # Threat detected
        
        return False  # No threat detected
    
    def _log_threat(self, user_id: str, action: str, anomalies: List[str], context: Dict[str, Any]):
        """Log a detected threat"""
        threat = {
            'user_id': user_id,
            'action': action,
            'anomalies': anomalies,
            'context': context,
            'timestamp': time.time(),
            'severity': self._calculate_severity(anomalies),
            'threat_id': secrets.token_hex(8)
        }
        self.alerts.append(threat)
        
        # Add to security incidents if high severity
        if threat['severity'] >= 2:  # High or critical
            self.security_incidents.append(threat)
    
    def _calculate_severity(self, anomalies: List[str]) -> int:
        """Calculate threat severity based on anomalies"""
        severity_map = {
            'access_outside_business_hours': 1,
            'access_from_new_location': 1,
            'rapid_successive_actions': 2,
            'access_from_new_device': 1
        }
        
        total_severity = sum(severity_map.get(a, 0) for a in anomalies)
        
        # Cap at 3 (critical)
        return min(total_severity, 3)
    
    def get_threat_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent threat alerts"""
        return self.alerts[-limit:]
    
    def get_security_incidents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get security incidents"""
        return self.security_incidents[-limit:]
    
    def add_to_whitelist(self, identifier: str):
        """Add identifier to whitelist"""
        self.whitelist.add(identifier)
    
    def add_to_blacklist(self, identifier: str):
        """Add identifier to blacklist"""
        self.blacklist.add(identifier)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if identifier is allowed"""
        if identifier in self.blacklist:
            return False
        if identifier in self.whitelist:
            return True
        return True  # Default allow if not in either list


class DataIntegrityManager:
    """
    Manages data integrity with advanced hashing and verification
    """
    
    def __init__(self):
        self.integrity_hashes = {}
        self.backup_hashes = {}
        self.signature_keys = {}
        self.verification_history = []
    
    def create_integrity_hash(self, data: bytes, algorithm: str = 'sha3_512') -> str:
        """Create an integrity hash for data"""
        if algorithm == 'sha3_512':
            hasher = hashlib.sha3_512()
        elif algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'blake2b':
            hasher = hashlib.blake2b()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        hasher.update(data)
        return hasher.hexdigest()
    
    def sign_data(self, data: bytes, key_id: str = 'default') -> str:
        """Sign data with a private key"""
        if key_id not in self.signature_keys:
            # Generate a new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend()
            )
            self.signature_keys[key_id] = {
                'private': private_key,
                'public': private_key.public_key()
            }
        
        private_key = self.signature_keys[key_id]['private']
        
        signature = private_key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_signature(self, data: bytes, signature: str, key_id: str = 'default') -> bool:
        """Verify data signature"""
        if key_id not in self.signature_keys:
            return False
        
        public_key = self.signature_keys[key_id]['public']
        signature_bytes = base64.b64decode(signature.encode('utf-8'))
        
        try:
            public_key.verify(
                signature_bytes,
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except:
            return False
    
    def store_protected_data(self, key: str, data: bytes) -> Dict[str, str]:
        """Store data with integrity protection"""
        integrity_hash = self.create_integrity_hash(data)
        signature = self.sign_data(data)
        
        protected_data = {
            'data': base64.b64encode(data).decode('utf-8'),
            'integrity_hash': integrity_hash,
            'signature': signature,
            'stored_at': time.time(),
            'key_id': 'default'
        }
        
        self.integrity_hashes[key] = protected_data
        return protected_data
    
    def retrieve_protected_data(self, key: str) -> Optional[bytes]:
        """Retrieve and verify protected data"""
        if key not in self.integrity_hashes:
            return None
        
        protected_data = self.integrity_hashes[key]
        
        # Decode the data
        data = base64.b64decode(protected_data['data'].encode('utf-8'))
        
        # Verify integrity
        calculated_hash = self.create_integrity_hash(data)
        if calculated_hash != protected_data['integrity_hash']:
            self.verification_history.append({
                'key': key,
                'timestamp': time.time(),
                'result': 'integrity_violation',
                'calculated_hash': calculated_hash,
                'stored_hash': protected_data['integrity_hash']
            })
            return None
        
        # Verify signature
        if not self.verify_signature(data, protected_data['signature'], protected_data['key_id']):
            self.verification_history.append({
                'key': key,
                'timestamp': time.time(),
                'result': 'signature_verification_failed'
            })
            return None
        
        # Log successful verification
        self.verification_history.append({
            'key': key,
            'timestamp': time.time(),
            'result': 'verified_successfully'
        })
        
        return data
    
    def backup_integrity_check(self, key: str) -> bool:
        """Perform backup integrity check"""
        if key not in self.integrity_hashes:
            return False
        
        protected_data = self.integrity_hashes[key]
        data = base64.b64decode(protected_data['data'].encode('utf-8'))
        
        # Create backup hash
        backup_hash = self.create_integrity_hash(data)
        self.backup_hashes[key] = backup_hash
        
        return True
    
    def verify_backup_integrity(self, key: str) -> bool:
        """Verify backup integrity"""
        if key not in self.integrity_hashes or key not in self.backup_hashes:
            return False
        
        protected_data = self.integrity_hashes[key]
        data = base64.b64decode(protected_data['data'].encode('utf-8'))
        
        current_hash = self.create_integrity_hash(data)
        backup_hash = self.backup_hashes[key]
        
        return current_hash == backup_hash
    
    def get_verification_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get verification history"""
        return self.verification_history[-limit:]


class AdvancedAccessControl:
    """
    Advanced access control with role-based permissions and attribute-based access
    """
    
    def __init__(self):
        self.roles = {}
        self.permissions = {}
        self.role_assignments = {}
        self.attribute_policies = {}
        self.access_logs = []
        
    def define_role(self, role_name: str, permissions: List[str]):
        """Define a role with specific permissions"""
        self.roles[role_name] = {
            'permissions': set(permissions),
            'created_at': time.time(),
            'modified_at': time.time()
        }
    
    def assign_role(self, user_id: str, role_name: str):
        """Assign a role to a user"""
        if role_name not in self.roles:
            raise ValueError(f"Role {role_name} does not exist")
        
        if user_id not in self.role_assignments:
            self.role_assignments[user_id] = set()
        
        self.role_assignments[user_id].add(role_name)
        
        # Log the assignment
        self.access_logs.append({
            'user_id': user_id,
            'action': 'role_assignment',
            'role': role_name,
            'timestamp': time.time()
        })
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission"""
        if user_id not in self.role_assignments:
            return False
        
        user_roles = self.role_assignments[user_id]
        
        for role_name in user_roles:
            if role_name in self.roles:
                if permission in self.roles[role_name]['permissions']:
                    # Log access check
                    self.access_logs.append({
                        'user_id': user_id,
                        'action': 'permission_check',
                        'permission': permission,
                        'granted': True,
                        'timestamp': time.time()
                    })
                    return True
        
        # Log denied access
        self.access_logs.append({
            'user_id': user_id,
            'action': 'permission_check',
            'permission': permission,
            'granted': False,
            'timestamp': time.time()
        })
        return False
    
    def define_attribute_policy(self, policy_name: str, attributes: Dict[str, Any], 
                              required_permissions: List[str]):
        """Define an attribute-based access policy"""
        self.attribute_policies[policy_name] = {
            'attributes': attributes,
            'required_permissions': set(required_permissions),
            'created_at': time.time()
        }
    
    def check_attribute_access(self, user_id: str, resource_attributes: Dict[str, Any], 
                             required_permission: str) -> bool:
        """Check access based on attributes and permissions"""
        # First check basic permission
        if not self.check_permission(user_id, required_permission):
            return False
        
        # Then check attribute policies
        for policy_name, policy in self.attribute_policies.items():
            # Check if resource attributes match policy requirements
            matches = True
            for attr, required_value in policy['attributes'].items():
                if attr not in resource_attributes:
                    matches = False
                    break
                if resource_attributes[attr] != required_value:
                    matches = False
                    break
            
            if matches and required_permission in policy['required_permissions']:
                return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user"""
        if user_id not in self.role_assignments:
            return []
        
        permissions = set()
        for role_name in self.role_assignments[user_id]:
            if role_name in self.roles:
                permissions.update(self.roles[role_name]['permissions'])
        
        return list(permissions)
    
    def get_access_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get access logs"""
        return self.access_logs[-limit:]
    
    def revoke_role(self, user_id: str, role_name: str):
        """Revoke a role from a user"""
        if user_id in self.role_assignments and role_name in self.role_assignments[user_id]:
            self.role_assignments[user_id].remove(role_name)
            
            # Log the revocation
            self.access_logs.append({
                'user_id': user_id,
                'action': 'role_revocation',
                'role': role_name,
                'timestamp': time.time()
            })


# Global instances
threat_detector = ThreatDetectionSystem()
data_integrity = DataIntegrityManager()
access_control = AdvancedAccessControl()


# Predefined roles and permissions for AirOne system
access_control.define_role('admin', [
    'system_configure', 'user_manage', 'telemetry_read', 'telemetry_write', 
    'mission_control', 'security_audit', 'data_export', 'system_shutdown'
])
access_control.define_role('operator', [
    'telemetry_read', 'mission_control', 'data_export'
])
access_control.define_role('analyst', [
    'telemetry_read', 'data_export'
])
access_control.define_role('guest', [
    'telemetry_read'
])


def initialize_security_systems():
    """Initialize all security systems with default configurations"""
    # Add default trusted IPs/devices to whitelist
    threat_detector.add_to_whitelist('127.0.0.1')
    threat_detector.add_to_whitelist('::1')
    
    # Define attribute-based policies
    access_control.define_attribute_policy(
        'critical_system_access',
        {'classification': 'critical'},
        ['system_configure', 'system_shutdown']
    )
    
    print("🔒 Advanced security systems initialized")


# Initialize security systems
initialize_security_systems()