from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.models.models import Document
from app.schemas.schemas import DocumentResponse
from app.services.document_signing import generate_document_hash, sign_document_hash

router = APIRouter()

@router.post("/verify", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def verify_and_sign_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts a file upload, hashes it, checks for malicious contents (simulated), 
    and digitally signs it with ECDSA if it's considered safe.
    """
    try:
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
            
        doc_hash = generate_document_hash(contents)
        
        # Check if already exists
        existing_doc = db.query(Document).filter(Document.hash == doc_hash).first()
        if existing_doc:
            return existing_doc
            
        # Simulate Malware / Trust check
        # In a real app we would scan the file using ClamAV or advanced ML
        trust_score = 95
        status_val = "verified"
        findings = []
        
        if file.filename.endswith((".exe", ".sh", ".bat")):
            trust_score = 10
            status_val = "flagged"
            findings.append({"type": "Security", "severity": "High", "message": "Executable files are not permitted."})
            
        doc_id = str(uuid.uuid4())
        
        # Sign the document if it passed the trust check
        signature_data = {"signature": None, "public_key": None, "timestamp": None}
        if status_val == "verified":
            signature_data = sign_document_hash(doc_hash)
            
        db_doc = Document(
            id=doc_id,
            filename=file.filename,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            hash=doc_hash,
            status=status_val,
            trust_score=trust_score,
            findings=findings,
            signature=signature_data.get("signature"),
            public_key=signature_data.get("public_key"),
            verified_at=signature_data.get("timestamp")
        )
        
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        
        return db_doc
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()

@router.get("/{doc_hash}", response_model=DocumentResponse)
def get_document_by_hash(doc_hash: str, db: Session = Depends(get_db)):
    """
    Retrieves the verification status of a document via its SHA-256 hash.
    """
    doc = db.query(Document).filter(Document.hash == doc_hash).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document hash not found in ledger.")
    return doc
