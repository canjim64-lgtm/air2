"""
Minimal Password Manager
Requires input, auto-delete after 1 min, no save
"""

import time
import secrets
import threading
import getpass


class PasswordManager:
    """Minimal password manager - requires input, auto-delete, no save"""
    
    def __init__(self):
        self.displayed_passwords = {}
        self.lock = threading.Lock()
        self._cleanup_thread = threading.Thread(target=self._cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def input_password(self, prompt: str = "Enter password: ") -> str:
        """Input password (hidden)"""
        return getpass.getpass(prompt)
    
    def input_new_password(self) -> str:
        """Input new password with confirmation"""
        p1 = getpass.getpass("Enter new password: ")
        p2 = getpass.getpass("Confirm password: ")
        
        if p1 != p2:
            raise ValueError("Passwords don't match")
        
        if len(p1) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        return p1
    
    def generate_password(self, length: int = 12) -> str:
        """Generate random password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def display_password(self, password: str, display_seconds: int = 60):
        """Display password for limited time only"""
        expiry = time.time() + display_seconds
        
        with self.lock:
            self.displayed_passwords[password] = expiry
        
        print(f"Password (valid for {display_seconds}s): {password}")
        return password
    
    def get_password(self, password: str) -> str:
        """Get password if not expired"""
        with self.lock:
            if password in self.displayed_passwords:
                if time.time() < self.displayed_passwords[password]:
                    return password
                else:
                    del self.displayed_passwords[password]
        return None
    
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
        """Clear all displayed passwords"""
        with self.lock:
            self.displayed_passwords.clear()


if __name__ == "__main__":
    pm = PasswordManager()
    
    # Input password
    pwd = pm.input_new_password()
    pm.display_password(pwd, 60)