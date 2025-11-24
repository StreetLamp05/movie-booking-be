from cryptography.fernet import Fernet
import os

class CardEncryption:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a card field. Returns base64 string."""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a card field."""
        return self.cipher.decrypt(ciphertext.encode()).decode()