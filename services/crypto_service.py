import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class CryptoService:
    """
    Service for encrypting and decrypting data using AES-GCM.
    Uses a 32-byte (256-bit) key in Base64 format.
    """
    
    def __init__(self):
        encryption_key = os.getenv("DATABASE_ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError("DATABASE_ENCRYPTION_KEY environment variable is required")
        
        try:
            self.key = base64.urlsafe_b64decode(encryption_key)
        except Exception as e:
            raise ValueError(f"Invalid DATABASE_ENCRYPTION_KEY format: {e}")
        
        if len(self.key) != 32:
            raise ValueError("Encryption key must decode to exactly 32 bytes")
        
        self.aes = AESGCM(self.key)

    def encrypt(self, value: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aes.encrypt(nonce, value.encode(), None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def decrypt(self, value: str) -> str:
        try:
            raw = base64.urlsafe_b64decode(value)
            nonce = raw[:12]
            ciphertext = raw[12:]
            plaintext = self.aes.decrypt(nonce, ciphertext, None)
            return plaintext.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")