import hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timezone

# In a real app, this would be loaded from a secure vault or HSM
# We generate a keypair for demonstration
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

def generate_document_hash(file_bytes: bytes) -> str:
    """Generates a SHA-256 hash of the document bytes."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_bytes)
    return sha256_hash.hexdigest()

def sign_document_hash(doc_hash: str) -> dict:
    """
    Signs the document hash using ECDSA.
    Returns the signature and the public key for verification.
    """
    signature = private_key.sign(
        doc_hash.encode('utf-8'),
        ec.ECDSA(hashes.SHA256())
    )
    
    # Serialize public key to PEM format for distribution
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return {
        "signature": signature.hex(),
        "public_key": pem_public_key.decode('utf-8'),
        "timestamp": datetime.now(timezone.utc)
    }

def verify_document_signature(doc_hash: str, signature_hex: str, pub_key_pem: str) -> bool:
    """
    Verifies that a document hash matches the provided ECDSA signature.
    """
    try:
        loaded_public_key = serialization.load_pem_public_key(
            pub_key_pem.encode('utf-8')
        )
        loaded_public_key.verify(
            bytes.fromhex(signature_hex),
            doc_hash.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except Exception as e:
        print(f"Signature Verification Failed: {e}")
        return False
