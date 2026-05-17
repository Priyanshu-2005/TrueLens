"""
TrueLens Cryptographic Signing Service
======================================
Provides document hashing and digital signatures.
Upgraded to support Ed25519 (default) and RSA-4096.
"""

import os
import hashlib
import logging
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa, ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)

# Default algorithm (can be ed25519, rsa4096, ecdsa)
SIGNING_ALGORITHM = os.getenv("SIGNING_ALGORITHM", "ed25519").lower()

class KeyManager:
    """Manages cryptographic keys. In production, this interfaces with AWS KMS."""
    def __init__(self):
        self.algo = SIGNING_ALGORITHM
        self._private_key = None
        self._public_key = None
        self._initialize_keys()

    def _initialize_keys(self):
        logger.info(f"Initializing document signing keys with algorithm: {self.algo}")
        if self.algo == "ed25519":
            self._private_key = ed25519.Ed25519PrivateKey.generate()
            self._public_key = self._private_key.public_key()
        elif self.algo == "rsa4096":
            self._private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
            )
            self._public_key = self._private_key.public_key()
        else: # Fallback to ECDSA
            self._private_key = ec.generate_private_key(ec.SECP256R1())
            self._public_key = self._private_key.public_key()

    def sign(self, data: bytes) -> bytes:
        if self.algo == "ed25519":
            return self._private_key.sign(data)
        elif self.algo == "rsa4096":
            return self._private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        else:
            return self._private_key.sign(data, ec.ECDSA(hashes.SHA256()))

    def get_public_key_pem(self) -> str:
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

# Global key manager instance
key_manager = KeyManager()


def generate_document_hash(file_bytes: bytes) -> str:
    """Generates a SHA-256 fingerprint of the document bytes."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_bytes)
    return sha256_hash.hexdigest()


def sign_document_hash(doc_hash: str) -> dict:
    """
    Signs the document hash cryptographically.
    Returns the signature and the public key for verification.
    """
    signature_bytes = key_manager.sign(doc_hash.encode('utf-8'))
    
    return {
        "signature": signature_bytes.hex(),
        "public_key": key_manager.get_public_key_pem(),
        "timestamp": datetime.now(timezone.utc),
        "algorithm": SIGNING_ALGORITHM
    }


def verify_document_signature(doc_hash: str, signature_hex: str, pub_key_pem: str, algo: str = "ed25519") -> bool:
    """
    Verifies that a document hash matches the provided signature.
    """
    try:
        loaded_public_key = serialization.load_pem_public_key(
            pub_key_pem.encode('utf-8')
        )
        sig_bytes = bytes.fromhex(signature_hex)
        data_bytes = doc_hash.encode('utf-8')

        if isinstance(loaded_public_key, ed25519.Ed25519PublicKey):
            loaded_public_key.verify(sig_bytes, data_bytes)
        elif isinstance(loaded_public_key, rsa.RSAPublicKey):
            loaded_public_key.verify(
                sig_bytes,
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        elif isinstance(loaded_public_key, ec.EllipticCurvePublicKey):
            loaded_public_key.verify(sig_bytes, data_bytes, ec.ECDSA(hashes.SHA256()))
        else:
            return False
            
        return True
    except Exception as e:
        logger.warning(f"Signature Verification Failed: {e}")
        return False
