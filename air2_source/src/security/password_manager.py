"""
Minimal Password Manager
Auto-change on login, 256-char required, no save
"""

import time
import secrets
import threading
import getpass


class PasswordManager:
    """Minimal password manager - auto-change, 256-char, no save"""
    
    def __init__(self):
        self.displayed_passwords = {}
        self.lock = threading.Lock()
        self.current_password = None
        self._cleanup_thread = threading.Thread(target=self._cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def generate_256_char_password(self) -> str:
        """Generate 256-character password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?"
        return ''.join(secrets.choice(alphabet) for _ in range(256))
    
    def auto_change_on_login(self) -> str:
        """Generate new 256-char password on each login"""
        new_password = self.generate_256_char_password()
        
        # Auto-delete old password
        if self.current_password:
            with self.lock:
                self.displayed_passwords.pop(self.current_password, None)
        
        # Set new password
        self.current_password = new_password
        
        # Display for 1 minute
        expiry = time.time() + 60
        with self.lock:
            self.displayed_passwords[new_password] = expiry
        
        print(f"NEW PASSWORD (valid 60s, 256 chars): {new_password}")
        return new_password
    
    def display_password(self, password: str, display_seconds: int = 60):
        """Display password for limited time only"""
        expiry = time.time() + display_seconds
        
        with self.lock:
            self.displayed_passwords[password] = expiry
        
        print(f"Password (valid {display_seconds}s): {password}")
        return password
    
    def verify_password(self, password: str) -> bool:
        """Verify password - auto-expires after 1 min"""
        with self.lock:
            if password in self.displayed_passwords:
                if time.time() < self.displayed_passwords[password]:
                    return True
                else:
                    del self.displayed_passwords[password]
        return False
    
    def _cleanup(self):
        """Clean up expired passwords"""
        while True:
            time.sleep(10)
            with self.lock:
                now = time.time()
                expired = [p for p, exp in self.displayed_passwords.items() if now >= exp]
                for p in expired:
                    del self.displayed_passwords[p]
    
    def clear_all(self):
        """Clear all passwords"""
        with self.lock:
            self.displayed_passwords.clear()
            self.current_password = None


if __name__ == "__main__":
    pm = PasswordManager()
    
    # Auto-generate new 256-char password on login
    new_pwd = pm.auto_change_on_login()
    print(f"\nPassword length: {len(new_pwd)} chars")