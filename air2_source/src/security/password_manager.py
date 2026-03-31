"""
Minimal Password Manager
Auto-change on login, 256-char required, no save
Login required
"""

import time
import secrets
import threading
import getpass


class AuthManager:
    """Authentication manager with login"""
    
    def __init__(self):
        self.displayed_passwords = {}
        self.lock = threading.Lock()
        self.current_password = None
        self.logged_in = False
        self._cleanup_thread = threading.Thread(target=self._cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def generate_256_char_password(self) -> str:
        """Generate 256-character password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+[]{}|;:,.<>?"
        return ''.join(secrets.choice(alphabet) for _ in range(256))
    
    def auto_change_on_login(self) -> str:
        """Generate new 256-char password on each login"""
        new_password = self.generate_256_char_password()
        
        if self.current_password:
            with self.lock:
                self.displayed_passwords.pop(self.current_password, None)
        
        self.current_password = new_password
        
        expiry = time.time() + 60
        with self.lock:
            self.displayed_passwords[new_password] = expiry
        
        print(f"NEW PASSWORD (valid 60s, 256 chars): {new_password}")
        return new_password
    
    def login(self) -> bool:
        """Login - generates new password, requires input to verify"""
        # Generate new password on login attempt
        new_pwd = self.auto_change_on_login()
        
        # Request password input
        print("\n=== LOGIN REQUIRED ===")
        attempt = getpass.getpass("Enter password: ")
        
        # Verify (auto-expires after 1 min)
        with self.lock:
            if attempt in self.displayed_passwords:
                if time.time() < self.displayed_passwords[attempt]:
                    self.logged_in = True
                    print("✓ LOGIN SUCCESS")
                    return True
        
        print("✗ LOGIN FAILED - Password expired or invalid")
        self.logged_in = False
        return False
    
    def logout(self):
        """Logout"""
        self.logged_in = False
        if self.current_password:
            with self.lock:
                self.displayed_passwords.pop(self.current_password, None)
            self.current_password = None
        print("Logged out")
    
    def require_login(self):
        """Decorator to require login"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.logged_in:
                    print("Please login first")
                    if not self.login():
                        return None
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _cleanup(self):
        """Clean up expired passwords"""
        while True:
            time.sleep(10)
            with self.lock:
                now = time.time()
                expired = [p for p, exp in self.displayed_passwords.items() if now >= exp]
                for p in expired:
                    del self.displayed_passwords[p]


# Example - requires login
if __name__ == "__main__":
    auth = AuthManager()
    
    # Login required
    print("=== AIRONE LOGIN ===")
    success = auth.login()
    
    if success:
        print("\nAccess granted - session active for 60 seconds")