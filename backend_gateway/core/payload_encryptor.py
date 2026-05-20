import os
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

class AESGCMCipher:
    """
    Handles secure command encryption using AES-GCM (Galois/Counter Mode).
    Provides authenticated encryption with associated data (AEAD).
    """

    @staticmethod
    def encrypt_command(session_key: bytes, command_dict: dict) -> str:
        """
        Encrypts a command dictionary using AES-GCM.
        
        Args:
            session_key (bytes): 256-bit (32-byte) session key.
            command_dict (dict): The command payload to encrypt.
            
        Returns:
            str: Base64 encoded string containing [Nonce (12) | Ciphertext + Tag].
        """
        try:
            # 1. Serialize Payload
            json_data = json.dumps(command_dict).encode('utf-8')
            
            # 2. Generate Nonce (12 bytes for GCM)
            nonce = os.urandom(12)
            
            # 3. Encrypt
            # AESGCM.encrypt(nonce, data, associated_data)
            # We don't use associated_data (AAD) here, so None.
            aesgcm = AESGCM(session_key)
            ciphertext = aesgcm.encrypt(nonce, json_data, None)
            
            # 4. Pack and Encode
            # Result is Nonce + Ciphertext (Tag is appended to ciphertext by cryptography lib)
            combined = nonce + ciphertext
            return base64.b64encode(combined).decode('utf-8')
            
        except Exception as e:
            print(f"Encryption failed: {e}")
            raise

    @staticmethod
    def decrypt_command(session_key: bytes, encrypted_payload: str) -> dict:
        """
        Decrypts and authenticates an encrypted command payload.
        
        Args:
            session_key (bytes): 256-bit (32-byte) session key.
            encrypted_payload (str): Base64 encoded string [Nonce | Ciphertext].
            
        Returns:
            dict: The original command dictionary.
            
        Raises:
            InvalidTag: If the GCM tag validation fails (tampering detected).
            ValueError: If payload format is invalid.
        """
        try:
            # 1. Decode Base64
            decoded = base64.b64decode(encrypted_payload)
            
            if len(decoded) < 12:
                raise ValueError("Payload too short to contain nonce")
            
            # 2. Extract Nonce and Ciphertext
            nonce = decoded[:12]
            ciphertext = decoded[12:]
            
            # 3. Decrypt and Verify
            aesgcm = AESGCM(session_key)
            # Raises InvalidTag if verification fails
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            
            # 4. Deserialize
            return json.loads(plaintext_bytes.decode('utf-8'))
            
        except InvalidTag:
            print("SECURITY ALERT: GCM Tag Mismatch! Potential tampering or wrong key.")
            raise
        except Exception as e:
            print(f"Decryption failed: {e}")
            raise
