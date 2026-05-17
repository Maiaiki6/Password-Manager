"""
Cryptographic utilities for password encryption and key derivation.
Uses AES-256-CBC for symmetric encryption and PBKDF2 for key derivation.
"""

import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class CryptoManager:
    """Handles encryption, decryption, and key derivation."""
    
    # Constants
    ALGORITHM_AES = "AES"
    MODE_CBC = "CBC"
    KEY_SIZE = 32  # 256 bits for AES-256
    IV_SIZE = 16   # 128 bits for CBC mode
    HASH_ALGORITHM = hashes.SHA256()
    PBKDF2_ITERATIONS = 100000  # OWASP recommendation (2023)
    
    @staticmethod
    def generate_salt(length=16):
        """Generate a random salt for key derivation."""
        return os.urandom(length)
    
    @staticmethod
    def generate_iv():
        """Generate a random IV for AES encryption."""
        return os.urandom(CryptoManager.IV_SIZE)
    
    @staticmethod
    def derive_master_key(master_password, salt):
        """
        Derive a 256-bit encryption key from master password using PBKDF2.
        
        Args:
            master_password (str): The master password
            salt (bytes): Random salt for key derivation
            
        Returns:
            bytes: 256-bit derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=CryptoManager.HASH_ALGORITHM,
            length=CryptoManager.KEY_SIZE,
            salt=salt,
            iterations=CryptoManager.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(master_password.encode('utf-8'))
    
    @staticmethod
    def hash_master_password(master_password, salt):
        """
        Hash the master password for verification (not for encryption).
        Uses PBKDF2 with SHA-256.
        
        Args:
            master_password (str): The master password
            salt (bytes): Random salt
            
        Returns:
            bytes: Hashed password for verification
        """
        kdf = PBKDF2HMAC(
            algorithm=CryptoManager.HASH_ALGORITHM,
            length=32,  # 256-bit hash
            salt=salt,
            iterations=CryptoManager.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(master_password.encode('utf-8'))
    
    @staticmethod
    def encrypt_password(plaintext_password, master_key):
        """
        Encrypt a password using AES-256-CBC.
        
        Args:
            plaintext_password (str): The password to encrypt
            master_key (bytes): The derived 256-bit encryption key
            
        Returns:
            dict: Contains 'iv' (bytes) and 'ciphertext' (bytes)
        """
        iv = CryptoManager.generate_iv()
        cipher = Cipher(
            algorithms.AES(master_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Convert plaintext to bytes
        plaintext_bytes = plaintext_password.encode('utf-8')
        
        # Apply PKCS7 padding
        padding_length = 16 - (len(plaintext_bytes) % 16)
        padded_plaintext = plaintext_bytes + bytes([padding_length] * padding_length)
        
        # Encrypt
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
        
        return {
            'iv': iv,
            'ciphertext': ciphertext
        }
    
    @staticmethod
    def decrypt_password(iv, ciphertext, master_key):
        """
        Decrypt a password using AES-256-CBC.
        
        Args:
            iv (bytes): The initialization vector
            ciphertext (bytes): The encrypted password
            master_key (bytes): The derived 256-bit encryption key
            
        Returns:
            str: The decrypted password
            
        Raises:
            ValueError: If decryption fails
        """
        try:
            cipher = Cipher(
                algorithms.AES(master_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove PKCS7 padding
            padding_length = padded_plaintext[-1]
            plaintext_bytes = padded_plaintext[:-padding_length]
            
            return plaintext_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    @staticmethod
    def verify_master_password(provided_password, salt, stored_hash):
        """
        Verify that the provided master password matches the stored hash.
        
        Args:
            provided_password (str): The password to verify
            salt (bytes): The salt used for hashing
            stored_hash (bytes): The stored hash to compare against
            
        Returns:
            bool: True if password matches, False otherwise
        """
        provided_hash = CryptoManager.hash_master_password(provided_password, salt)
        return provided_hash == stored_hash
