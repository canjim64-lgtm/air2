"""
Enhanced Authentication Manager for AirOne Professional v4.0
With Automatic Password Rotation and Mandatory Save to TXT File
"""

import getpass
import hashlib
import os
import time
import secrets
import string
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
import json
from pathlib import Path


class AuthManager:
    """Authentication manager with automatic password rotation"""

    def __init__(self):
        self.authenticated = False
        self.user_sessions = {}
        self.failed_attempts = {}
        self.current_user = None
        self.security_level = "enhanced"
        self.auth_method = "password"
        self.session_timeout = 3600
        self.max_failed_attempts = 5
        self.lockout_duration = 300
        
        # Password rotation settings
        self.password_rotation_enabled = True
        self.password_length = 256
        self.password_history = {}  # Store previous passwords
        self.last_password_change = {}
        self.password_save_directory = Path(__file__).parent.parent.parent / "passwords"
        
        # Create passwords directory if it doesn't exist
        if not self.password_save_directory.exists():
            self.password_save_directory.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize user database with default 256-character passwords
        self.users = self._initialize_users()
        
        # Load existing passwords from file
        self._load_passwords_from_file()

    def _initialize_users(self) -> Dict[str, Dict[str, Any]]:
        """Initialize user database"""
        return {
            'admin': {
                'password': self._generate_secure_password(),
                'role': 'administrator',
                'permissions': ['all'],
                'created_at': datetime.utcnow().isoformat(),
                'password_changed_at': datetime.utcnow().isoformat(),
                'must_save_password': True
            },
            'operator': {
                'password': self._generate_secure_password(),
                'role': 'operator',
                'permissions': ['telemetry_read', 'telemetry_write'],
                'created_at': datetime.utcnow().isoformat(),
                'password_changed_at': datetime.utcnow().isoformat(),
                'must_save_password': True
            },
            'analyst': {
                'password': self._generate_secure_password(),
                'role': 'analyst',
                'permissions': ['telemetry_read', 'telemetry_write', 'data_export'],
                'created_at': datetime.utcnow().isoformat(),
                'password_changed_at': datetime.utcnow().isoformat(),
                'must_save_password': True
            },
            'engineer': {
                'password': self._generate_secure_password(),
                'role': 'engineer',
                'permissions': ['telemetry_read', 'telemetry_write', 'data_export', 'mission_control'],
                'created_at': datetime.utcnow().isoformat(),
                'password_changed_at': datetime.utcnow().isoformat(),
                'must_save_password': True
            },
            'security_admin': {
                'password': self._generate_secure_password(),
                'role': 'security_admin',
                'permissions': ['telemetry_read', 'telemetry_write', 'data_export', 'system_configure', 'mission_control', 'security_audit'],
                'created_at': datetime.utcnow().isoformat(),
                'password_changed_at': datetime.utcnow().isoformat(),
                'must_save_password': True
            },
            'executive': {
                'password': self._generate_secure_password(),
                'role': 'executive',
                'permissions': ['all'],
                'created_at': datetime.utcnow().isoformat(),
                'password_changed_at': datetime.utcnow().isoformat(),
                'must_save_password': True
            }
        }

    def _generate_secure_password(self, length: int = 256) -> str:
        """Generate a secure 256-character password with alphanumeric and special characters"""
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest with random characters from all sets
        all_chars = lowercase + uppercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle to avoid predictable pattern
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)

    def _save_password_to_file(self, username: str, password: str, force: bool = False) -> str:
        """Save password to TXT file (mandatory on each login)"""
        try:
            # Create filename with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"password_{username}_{timestamp}.txt"
            filepath = self.password_save_directory / filename
            
            # Get user info
            user_info = self.users.get(username, {})
            role = user_info.get('role', 'unknown')
            permissions = user_info.get('permissions', [])
            
            # Create content
            content = f"""================================================================================
    AirOne Professional v4.0 - PASSWORD CREDENTIALS
================================================================================

IMPORTANT SECURITY NOTICE:
--------------------------
This password was automatically generated and MUST be saved securely.
Password changes on EVERY login - save this password immediately!

================================================================================
ACCOUNT INFORMATION
================================================================================
Username: {username}
Role: {role}
Permissions: {', '.join(permissions)}
Generated: {datetime.utcnow().isoformat()}
Password Length: {len(password)} characters
Expires: On next login (automatic rotation)

================================================================================
PASSWORD (COPY AND SAVE THIS)
================================================================================
{password}

================================================================================
INSTRUCTIONS:
================================================================================
1. COPY the entire password above (all 256 characters)
2. SAVE this file in a secure location
3. DO NOT share this file with anyone
4. DELETE this file after saving password to password manager
5. Password will change on next login - you must save the new password

================================================================================
SECURITY WARNINGS:
================================================================================
- This password is 256 characters long
- Contains uppercase, lowercase, numbers, and special characters
- Case-sensitive - must be entered exactly
- Changes automatically on every login
- MUST be saved each time you login
- Never reuse passwords from other systems
- Store in a secure password manager

================================================================================
    AirOne Professional v4.0 - Security System
    © 2026 AirOne Development Team
================================================================================
"""
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Also save to latest password file for easy access
            latest_file = self.password_save_directory / f"latest_password_{username}.txt"
            with open(latest_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return str(filepath)
        
        except Exception as e:
            self.logger.error(f"Failed to save password to file: {e}")
            return None

    def _load_passwords_from_file(self):
        """Load existing passwords from file if available"""
        password_file = self.password_save_directory / "user_passwords.json"
        if password_file.exists():
            try:
                with open(password_file, 'r', encoding='utf-8') as f:
                    saved_passwords = json.load(f)
                
                # Update users with saved passwords
                for username, password in saved_passwords.items():
                    if username in self.users:
                        self.users[username]['password'] = password
            except Exception as e:
                self.logger.warning(f"Could not load saved passwords: {e}")

    def _save_passwords_to_file(self):
        """Save current passwords to JSON file for persistence"""
        try:
            password_file = self.password_save_directory / "user_passwords.json"
            passwords_to_save = {
                username: data['password'] 
                for username, data in self.users.items()
            }
            
            with open(password_file, 'w', encoding='utf-8') as f:
                json.dump(passwords_to_save, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save passwords: {e}")

    def _rotate_password(self, username: str) -> str:
        """Rotate password for a user (called on each login)"""
        if username not in self.users:
            return None
        
        # Store old password in history
        old_password = self.users[username]['password']
        if username not in self.password_history:
            self.password_history[username] = []
        self.password_history[username].append({
            'password': old_password,
            'changed_at': self.users[username]['password_changed_at'],
            'archived_at': datetime.utcnow().isoformat()
        })
        
        # Generate new password
        new_password = self._generate_secure_password()
        
        # Update user record
        self.users[username]['password'] = new_password
        self.users[username]['password_changed_at'] = datetime.utcnow().isoformat()
        self.users[username]['must_save_password'] = True
        
        # Save new password to file
        password_file = self._save_password_to_file(username, new_password)
        
        # Save to JSON for persistence
        self._save_passwords_to_file()
        
        return password_file

    def authenticate(self) -> bool:
        """Authentication with mandatory password rotation and save"""
        print("="*80)
        print("    AirOne Professional v4.0 - Authentication System")
        print("    Automatic Password Rotation Enabled")
        print("="*80)
        print()
        print("SECURITY NOTICE:")
        print("-" * 80)
        print("• Passwords are 256 characters long (alphanumeric + special characters)")
        print("• Password changes AUTOMATICALLY on EVERY login")
        print("• You MUST save the new password to a TXT file each time")
        print("• Copy and save the password file location shown after login")
        print("-" * 80)
        print()
        
        # Get username
        username = input("Username: ").strip()
        
        if username not in self.users:
            print("\n❌ Invalid username")
            return False
        
        # Get password
        print("\nNote: Password is 256 characters - use copy/paste")
        password = getpass.getpass("Password: ").strip()
        
        # Verify password
        if password != self.users[username]['password']:
            print("\n❌ Invalid password")
            return False
        
        # Password is correct - rotate it for next login
        print("\n✅ Authentication successful!")
        print("\n🔄 Rotating password for next login...")
        
        # Rotate password
        new_password_file = self._rotate_password(username)
        
        if new_password_file:
            print("\n" + "="*80)
            print("    ⚠️  PASSWORD CHANGED - SAVE THIS INFORMATION")
            print("="*80)
            print(f"\n📁 Your NEW password has been saved to:")
            print(f"   {new_password_file}")
            print(f"\n📁 Latest password also saved to:")
            print(f"   {self.password_save_directory / 'latest_password_' + username + '.txt'}")
            print("\n⚠️  IMPORTANT:")
            print("   • Your password has been AUTOMATICALLY CHANGED")
            print("   • This password will be DIFFERENT next time you login")
            print("   • You MUST save the new password file EACH TIME you login")
            print("   • Copy the password from the TXT file to your password manager")
            print("   • Delete the TXT file after saving to password manager")
            print("="*80)
        else:
            print("\n⚠️  WARNING: Failed to save password to file")
            print("   Please manually save your password!")
        
        # Set authenticated state
        self.authenticated = True
        self.current_user = username
        self.user_sessions[username] = {
            'session_id': secrets.token_hex(32),
            'started_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(seconds=self.session_timeout)).isoformat(),
            'role': self.users[username]['role'],
            'permissions': self.users[username]['permissions']
        }
        
        print("\n✅ Login complete. You are now authenticated.")
        print(f"   Session expires in {self.session_timeout // 60} minutes")
        
        return True

    def get_current_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        if not self.current_user or self.current_user not in self.users:
            return {}
        
        return {
            'username': self.current_user,
            'role': self.users[self.current_user]['role'],
            'permissions': self.users[self.current_user]['permissions'],
            'session': self.user_sessions.get(self.current_user, {}),
            'password_last_changed': self.users[self.current_user]['password_changed_at'],
            'must_save_password': self.users[self.current_user]['must_save_password']
        }

    def logout(self):
        """Logout current user"""
        if self.current_user:
            if self.current_user in self.user_sessions:
                del self.user_sessions[self.current_user]
            self.authenticated = False
            self.current_user = None
            print("Logged out successfully")

    def get_all_users(self) -> List[str]:
        """Get list of all users"""
        return list(self.users.keys())

    def get_user_role(self, username: str) -> str:
        """Get user role"""
        if username in self.users:
            return self.users[username]['role']
        return 'unknown'

    def get_user_permissions(self, username: str) -> List[str]:
        """Get user permissions"""
        if username in self.users:
            return self.users[username]['permissions']
        return []

    def has_permission(self, username: str, permission: str) -> bool:
        """Check if user has specific permission"""
        if username not in self.users:
            return False
        
        user_perms = self.users[username]['permissions']
        return permission in user_perms or 'all' in user_perms


def initialize_auth_manager() -> AuthManager:
    """Initialize and return auth manager"""
    return AuthManager()
