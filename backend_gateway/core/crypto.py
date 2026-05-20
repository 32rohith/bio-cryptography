import os
import struct
import numpy as np
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

class BioCryptoEngine:
    """
    Bio-Cryptographic Key Generation Engine.
    
    Uses physiological tremor entropy to derive strong cryptographic keys using
    HMAC-based Extract-and-Expand Key Derivation Function (HKDF) as defined in RFC 5869.
    """
    
    def __init__(self):
        self.backend = default_backend()
        
    def quantize_residuals(self, residuals):
        """
        Quantizes a stream of float residuals into a raw byte string for entropy.
        
        Process:
        1. Normalize residuals to 0-1 range (using min/max of the window).
        2. Scale to 0-255 integer range.
        3. Pack into bytes.
        
        Args:
            residuals (list or np.array): Array of float innovation residuals from Kalman filter.
            
        Returns:
            bytes: Quantized raw entropy bytes.
        """
        data = np.array(residuals, dtype=np.float32)
        
        # dynamic range scaling
        min_val = np.min(data)
        max_val = np.max(data)
        range_val = max_val - min_val
        
        if range_val == 0:
            # Avoid division by zero if flatline
            return b'\x00' * len(data)
            
        # Normalize to 0.0 - 1.0
        normalized = (data - min_val) / range_val
        
        # Scale to 0 - 255 and cast to uint8
        quantized = (normalized * 255).astype(np.uint8)
        
        # Convert to raw bytes
        return quantized.tobytes()

    def derive_aes_key(self, raw_entropy_bytes, salt=None):
        """
        Derives a 256-bit AES session key from biological entropy using HKDF.
        
        Reference: RFC 5869 (HMAC-based Extract-and-Expand Key Derivation Function)
        
        Args:
            raw_entropy_bytes (bytes): The quantized tremor data (Input Keying Material).
            salt (bytes, optional): Non-secret random salt. If None, a default is used. 
                                    In production, this should be exchanged or fixed.
                                    
        Returns:
            tuple: (key_bytes (bytes), key_hex (str))
                   key_bytes: 32 bytes (256 bits) for AES-256.
                   key_hex: Hexadecimal string representation for UI.
        """
        if salt is None:
            # RFC 5869: if salt is not provided, it is set to a string of HashLen zeros.
            # However, for this bio-crypto pairing, a constant salt or a session salt is better.
            # We'll use a fixed salt for this simulation to ensure reproducibility across nodes if we were sharing it,
            # but ideally this is generated per session.
            salt = b'telesurgery_bio_salt_v1'

        # HKDF Setup
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32, # 32 bytes = 256 bits
            salt=salt,
            info=b"telesurgery_session_key_v1", # Context-specific info
            backend=self.backend
        )
        
        # Derive Key
        key_bytes = hkdf.derive(raw_entropy_bytes)
        key_hex = key_bytes.hex()
        
        return key_bytes, key_hex
