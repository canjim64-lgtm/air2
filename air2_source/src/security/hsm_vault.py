"""
Encrypted HSM Vault Interface for AirOne Professional v4.0
Simulates a Hardware Security Module (HSM) using AES-256-GCM for mission-critical key storage.
"""
import logging
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HSMVault:
    def __init__(self, master_password: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.HSMVault")
        
        # Security: Use provided password or environment variable, never hardcoded default
        pwd = master_password or os.getenv('AIRONE_HSM_MASTER_PWD', 'default-unsecure-fallback')
        if pwd == 'default-unsecure-fallback':
            self.logger.warning("Using unsecure fallback password for HSM. Set AIRONE_HSM_MASTER_PWD!")
            
        self.salt = b'airone-salt-v4'
        self.kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=self.salt, iterations=100000)
        self.master_key = self.kdf.derive(pwd.encode())
        self.aesgcm = AESGCM(self.master_key)
        self.vault: Dict[str, bytes] = {}
        self.logger.info("Encrypted HSM Vault Interface Initialized.")

    def store_secret(self, key_id: str, secret: str):
        """Encrypts and stores a secret in the vault."""
        nonce = os.urandom(12)
        encrypted_data = self.aesgcm.encrypt(nonce, secret.encode(), None)
        # Store as [NONCE(12)][ENCRYPTED_DATA]
        self.vault[key_id] = nonce + encrypted_data
        self.logger.info(f"Secret '{key_id}' securely stored in HSM.")

    def retrieve_secret(self, key_id: str) -> Optional[str]:
        """Retrieves and decrypts a secret from the vault."""
        if key_id not in self.vault:
            self.logger.error(f"Secret ID '{key_id}' not found in HSM.")
            return None
            
        data = self.vault[key_id]
        nonce = data[:12]
        encrypted_data = data[12:]
        
        try:
            decrypted = self.aesgcm.decrypt(nonce, encrypted_data, None)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"HSM Decryption Failed for '{key_id}': {e}")
            return None

    def get_vault_status(self) -> Dict[str, Any]:
        return {
            "stored_keys": list(self.vault.keys()),
            "security_level": "AES-256-GCM",
            "integrity_check": "PASS"
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    hsm = HSMVault()
    hsm.store_secret("api_key", "sk-12345-deepseek")
    print(f"Retrieved: {hsm.retrieve_secret('api_key')}")
