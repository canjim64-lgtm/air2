"""Package initialization."""
from security.enhanced_security_module import SecurityManager
from security.auth_manager import AuthManager

def main():
    """Main security entry point"""
    sm = SecurityManager()
    print("AirOne Security System Ready")
    print(f"Encryption: {sm.config.get('GLOBAL_SECURITY', 'encryption_algorithm', fallback='AES-256-GCM')}")
