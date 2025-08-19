import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_image(data: bytes, password: str) -> tuple:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    encrypted_data = aesgcm.encrypt(nonce, data, None)
    tag = encrypted_data[-16:]
    ciphertext = encrypted_data[:-16]
    return ciphertext, salt, nonce, tag

def decrypt_image(encrypted_data: bytes, salt: bytes, nonce: bytes, tag: bytes, password: str) -> bytes:
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, encrypted_data + tag, None)