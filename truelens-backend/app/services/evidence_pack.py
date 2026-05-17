"""
TrueLens Evidence Pack Service
==============================
Generates a verifiable evidence pack for authentic documents.
An evidence pack includes:
  - A JSON manifest with the signature and findings
  - A QR code that points to the verification portal
"""

import io
import json
import base64
import logging
from typing import Dict, Any

import qrcode

logger = logging.getLogger(__name__)

def generate_evidence_pack(doc: Any) -> Dict[str, Any]:
    """
    Generates an evidence pack for a verified document.
    """
    # Create the JSON manifest
    manifest = {
        "document_id": doc.id,
        "filename": doc.filename,
        "hash_sha256": doc.hash,
        "trust_score": doc.trust_score,
        "verified_at": doc.verified_at.isoformat() if doc.verified_at else None,
        "signature": doc.signature,
        "public_key": doc.public_key,
        "findings": doc.findings,
        "issuer": "TrueLens Security Ledger"
    }

    # Generate the QR Code pointing to the verification portal
    verification_url = f"http://localhost:3000/verify?hash={doc.hash}"
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to generate QR code: {e}")
        qr_base64 = None

    return {
        "manifest": manifest,
        "qr_code_base64": qr_base64,
        "verification_url": verification_url
    }
