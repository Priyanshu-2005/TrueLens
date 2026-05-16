from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import time

from app.core.database import get_db
from app.models.models import Scan, Signal, ContentTypeEnum, ScanStatusEnum, VerdictEnum
from app.schemas.schemas import ScanRequest, ScanResponse
from app.tasks.ml_pipeline import process_scan_task

router = APIRouter()

@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
def create_scan(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Creates a new scan request and initiates processing.
    """
    db_scan = Scan(
        id=str(uuid.uuid4()),
        url=str(request.url) if request.url else None,
        raw_text=request.text,
        content_type=request.content_type,
        status=ScanStatusEnum.pending
    )
    
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    
    # Trigger the Celery task for asynchronous processing.
    process_scan_task.delay(db_scan.id)
    
    return db_scan

@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the status and result of a scan.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.get("/", response_model=List[ScanResponse])
def list_scans(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Lists recent scans.
    """
    scans = db.query(Scan).order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()
    return scans
