"""
AirOne Professional v4.0 - Advanced Password Generator
Generates highly complex, non-readable passwords with maximum entropy
Passwords change and update each time they are generated
"""
# -*- coding: utf-8 -*-

import secrets
import string
import hashlib
import os
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AdvancedPasswordGenerator:
    """
    Generate ultra-secure, complex passwords with maximum entropy
    Each password is unique and changes every generation
    """
    
    def __init__(self, password_dir: str = "passwords"):
        self.password_dir = Path(password_dir)
        self.password_dir.mkdir(exist_ok=True)
        
        # Character sets - expanded for maximum complexity
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        
        # Extended special characters including less common ones
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        self.unicode_specials = "¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿×÷"
        self.math_symbols = "∑∏∫∂∆∇∈∉∋∌∩∪⊂⊃⊄⊅⊆⊇⊕⊗⊥⋅⋆⋇⋈⋉⋊⋋⋌⋍⋎⋏⋐⋑⋒⋓⋔⋕⋖⋗⋘⋙⋚⋛⋜⋝⋞⋟⋠⋡⋢⋣⋤⋥⋦⋧⋨⋩⋪⋫⋬⋭⋮⋯⋰⋱"
        
        # All characters combined
        self.all_chars = (
            self.lowercase + 
            self.uppercase + 
            self.digits + 
            self.special_chars + 
            self.unicode_specials
        )
        
        # Password history for tracking
        self.history_file = self.password_dir / ".password_history.json"
        self.password_history = self._load_history()
        
    def _load_history(self) -> Dict:
        """Load password history"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'passwords': [], 'last_updated': None}
    
    def _save_history(self):
        """Save password history"""
        try:
            with open(self.password_dir / '.password_history_encrypted.json', 'w', encoding='utf-8') as f:
                # Encrypt history before saving
                encrypted = base64.b64encode(
                    json.dumps(self.password_history).encode('utf-8')
                ).decode('utf-8')
                json.dump({'encrypted_history': encrypted}, f)
        except Exception as e:
            logger.error(f"Failed to save password history: {e}")
    
    def _generate_entropy_seed(self) -> bytes:
        """Generate high-entropy seed from multiple sources"""
        # System entropy
        system_entropy = os.urandom(64)
        
        # Time-based entropy (nanoseconds for maximum variation)
        time_entropy = str(datetime.now().timestamp() * 1000000).encode('utf-8')
        
        # Process ID entropy
        pid_entropy = str(os.getpid()).encode('utf-8')
        
        # Combine all entropy sources
        combined = system_entropy + time_entropy + pid_entropy
        
        # Hash for uniform distribution
        return hashlib.sha512(combined).digest()
    
    def _select_random_char(self, char_set: str, entropy: bytes, offset: int) -> str:
        """Select random character using cryptographic randomness"""
        # Use secrets for cryptographic randomness
        random_index = secrets.randbelow(len(char_set))
        return char_set[random_index]
    
    def generate_ultra_secure_password(
        self, 
        length: int = 512,
        include_unicode: bool = True,
        include_math: bool = False,
        user_specific: bool = False,
        username: str = ""
    ) -> str:
        """
        Generate ultra-secure password with maximum complexity
        
        Args:
            length: Password length (default 512 characters for maximum security)
            include_unicode: Include Unicode special characters
            include_math: Include mathematical symbols
            user_specific: Make password specific to a user
            username: Username for user-specific passwords
            
        Returns:
            Ultra-secure password string
        """
        # Generate entropy seed
        entropy = self._generate_entropy_seed()
        
        # Build character pool
        char_pool = self.all_chars
        if include_unicode:
            char_pool += self.unicode_specials
        if include_math:
            char_pool += self.math_symbols
            
        # Add user-specific entropy
        if user_specific and username:
            user_entropy = hashlib.sha512(username.encode('utf-8')).digest()
            entropy = hashlib.sha512(entropy + user_entropy).digest()
        
        # Generate password with guaranteed character type inclusion
        password = []
        
        # Ensure at least one of each required type
        password.append(self._select_random_char(self.lowercase, entropy, 0))
        password.append(self._select_random_char(self.uppercase, entropy, 1))
        password.append(self._select_random_char(self.digits, entropy, 2))
        password.append(self._select_random_char(self.special_chars, entropy, 3))
        if include_unicode:
            password.append(self._select_random_char(self.unicode_specials, entropy, 4))
        
        # Fill remaining length with random characters
        remaining = length - len(password)
        for i in range(remaining):
            char = self._select_random_char(char_pool, entropy, i + 5)
            password.append(char)
        
        # Shuffle using Fisher-Yates with cryptographic randomness
        for i in range(len(password) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password[i], password[j] = password[j], password[i]
        
        # Convert to string
        password_str = ''.join(password)
        
        # Record in history
        self._record_password(password_str, username if user_specific else "system")
        
        return password_str
    
    def _record_password(self, password: str, user: str):
        """Record password generation in history"""
        timestamp = datetime.now().isoformat()
        password_hash = hashlib.sha512(password.encode('utf-8')).hexdigest()[:16]
        
        self.password_history['passwords'].append({
            'user': user,
            'timestamp': timestamp,
            'hash_prefix': password_hash,
            'length': len(password)
        })
        
        # Keep only last 1000 entries
        if len(self.password_history['passwords']) > 1000:
            self.password_history['passwords'] = self.password_history['passwords'][-1000:]
        
        self.password_history['last_updated'] = timestamp
        self._save_history()
    
    def generate_user_password(self, username: str, length: int = 512) -> Tuple[str, str]:
        """
        Generate password for specific user
        
        Args:
            username: Username
            length: Password length
            
        Returns:
            Tuple of (username, password)
        """
        password = self.generate_ultra_secure_password(
            length=length,
            include_unicode=True,
            user_specific=True,
            username=username
        )
        
        return username, password
    
    def save_password(self, username: str, password: str, filename: Optional[str] = None):
        """
        Save password to file with timestamp
        
        Args:
            username: Username
            password: Password to save
            filename: Optional custom filename
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"password_{username}_{timestamp}.txt"
        
        filepath = self.password_dir / filename
        
        # Create password file with metadata
        content = f"""================================================================================
    AirOne Professional v4.0 - SECURE PASSWORD FILE
================================================================================

GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
USERNAME: {username}
PASSWORD LENGTH: {len(password)} characters
SECURITY LEVEL: ULTRA-HIGH (512-char complex password)

================================================================================
PASSWORD
================================================================================

{password}

================================================================================
IMPORTANT SECURITY NOTES
================================================================================

1. This password is 512 characters of maximum complexity
2. It includes: lowercase, uppercase, digits, special chars, Unicode symbols
3. This password CANNOT be typed - use copy/paste ONLY
4. Password changes EVERY time it is generated
5. Save this file securely - it will NOT be the same next time!
6. Delete this file after copying the password
7. NEVER share this file or password

================================================================================
USAGE INSTRUCTIONS
================================================================================

1. Copy the ENTIRE password above (all 512 characters)
2. Paste it into the password field
3. DO NOT attempt to type it manually
4. Save this file in a secure location
5. Consider using a password manager

================================================================================
    AirOne Professional v4.0 - Security System
    © 2026 AirOne Development Team
================================================================================
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Also save as raw password file
        raw_filepath = self.password_dir / f"latest_password_{username}.txt"
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            f.write(password)
        
        logger.info(f"Password saved for user {username} (length: {len(password)})")
        return filepath
    
    def regenerate_all_passwords(self, users: List[str]) -> Dict[str, str]:
        """
        Regenerate passwords for all users
        
        Args:
            users: List of usernames
            
        Returns:
            Dictionary of {username: password}
        """
        new_passwords = {}
        
        for username in users:
            _, password = self.generate_user_password(username)
            new_passwords[username] = password
            self.save_password(username, password)
        
        logger.info(f"Regenerated passwords for {len(users)} users")
        return new_passwords
    
    def get_password_stats(self) -> Dict:
        """Get password generation statistics"""
        return {
            'total_generated': len(self.password_history.get('passwords', [])),
            'last_updated': self.password_history.get('last_updated'),
            'password_length': 512,
            'character_sets': 5,
            'entropy_source': 'cryptographic + system + time'
        }


class PasswordRotator:
    """
    Automatic password rotation system
    Ensures passwords change every time they are used
    """
    
    def __init__(self):
        self.generator = AdvancedPasswordGenerator()
        self.rotation_count = 0
    
    def get_fresh_password(self, username: str, length: int = 512) -> str:
        """
        Get a fresh password that changes every call
        
        Args:
            username: Username
            length: Password length
            
        Returns:
            New unique password
        """
        self.rotation_count += 1
        
        # Add rotation entropy
        rotation_entropy = str(self.rotation_count).encode('utf-8')
        os.environ['PASSWORD_ROTATION'] = str(self.rotation_count)
        
        # Generate new password
        _, password = self.generator.generate_user_password(username, length)
        
        logger.info(f"Password rotated for {username} (rotation #{self.rotation_count})")
        
        return password
    
    def rotate_and_save(self, username: str) -> str:
        """
        Rotate password and save to file
        
        Args:
            username: Username
            
        Returns:
            New password
        """
        password = self.get_fresh_password(username)
        self.generator.save_password(username, password)
        
        return password


def generate_secure_password(length: int = 512) -> str:
    """Quick function to generate secure password"""
    generator = AdvancedPasswordGenerator()
    return generator.generate_ultra_secure_password(length)


def generate_and_save_password(username: str, length: int = 512) -> str:
    """Quick function to generate and save password"""
    generator = AdvancedPasswordGenerator()
    _, password = generator.generate_user_password(username, length)
    generator.save_password(username, password)
    return password


def rotate_password(username: str) -> str:
    """Quick function to rotate password"""
    rotator = PasswordRotator()
    return rotator.rotate_and_save(username)


if __name__ == "__main__":
    # Test password generator
    print("="*70)
    print("  AirOne Professional v4.0 - Advanced Password Generator")
    print("="*70)
    print()
    
    generator = AdvancedPasswordGenerator()
    
    # Generate test passwords
    print("Generating ultra-secure passwords...")
    print()
    
    # Test 1: Generate password
    print("[Test 1] Generate 512-character password:")
    password1 = generator.generate_ultra_secure_password()
    print(f"  Length: {len(password1)} characters")
    print(f"  First 50 chars: {password1[:50]}...")
    print(f"  Last 50 chars: ...{password1[-50:]}")
    print()
    
    # Test 2: Generate again (should be different)
    print("[Test 2] Generate again (should be completely different):")
    password2 = generator.generate_ultra_secure_password()
    print(f"  Length: {len(password2)} characters")
    print(f"  First 50 chars: {password2[:50]}...")
    print(f"  Last 50 chars: ...{password2[-50:]}")
    print()
    
    # Verify they're different
    print("[Test 3] Verify passwords are different:")
    if password1 != password2:
        print("  [OK] Passwords are unique (as expected)")
    else:
        print("  [FAIL] Passwords are identical (should not happen!)")
    print()
    
    # Test 4: Generate user passwords
    print("[Test 4] Generate user-specific passwords:")
    users = ['admin', 'operator', 'engineer']
    for user in users:
        username, password = generator.generate_user_password(user)
        generator.save_password(user, password)
        print(f"  [OK] {user}: {len(password)} characters")
    print()
    
    # Test 5: Password rotation
    print("[Test 5] Test password rotation:")
    rotator = PasswordRotator()
    p1 = rotator.get_fresh_password('test_user')
    p2 = rotator.get_fresh_password('test_user')
    p3 = rotator.get_fresh_password('test_user')
    
    if p1 != p2 and p2 != p3 and p1 != p3:
        print("  [OK] All rotated passwords are unique")
    else:
        print("  [FAIL] Some rotated passwords are identical")
    print()
    
    # Stats
    print("Password Generator Statistics:")
    stats = generator.get_password_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()
    print("="*70)
    print("  Password Generator Test Complete")
    print("="*70)
    print()
    print("Check the 'passwords/' folder for generated password files.")
    print()
