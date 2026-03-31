"""
Minimal Password Manager - Auto-delete, 1-min display only, no save
No password history, no storage - just display for 1 minute
"""

import time
import secrets
import threading


class PasswordManager:
    """Minimal password manager - display only, no save"""
    
    def __init__(self):
        self.displayed_passwords = {}  # {password: expiry_time}
        self.lock = threading.Lock()
        self._cleanup_thread = threading.Thread(target=self._cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def generate_password(self, length: int = 12) -> str:
        """Generate random password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def display_password(self, password: str, display_seconds: int = 60):
        """Display password for limited time"""
        expiry = time.time() + display_seconds
        
        with self.lock:
            # Auto-delete after display time
            self.displayed_passwords[password] = expiry
        
        return password
    
    def get_password(self, password: str) -> str:
        """Get password if not expired"""
        with self.lock:
            if password in self.displayed_passwords:
                if time.time() < self.displayed_passwords[password]:
                    return password
                else:
                    # Auto-delete expired
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


# Example
if __name__ == "__main__":
    pm = PasswordManager()
    pwd = pm.generate_password()
    pm.display_password(pwd, 60)  # Show for 60 seconds
    print(f"Password displayed: {pwd}")
    print("Will auto-delete in 60 seconds")