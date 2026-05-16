from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ContentTypeEnum(str, enum.Enum):
    url = "url"
    text = "text"
    file = "file"

class ScanStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class VerdictEnum(str, enum.Enum):
    authentic = "Authentic"
    suspicious = "Suspicious"
    ai_generated = "AI-Generated"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    plan = Column(String, default="free")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    scans = relationship("Scan", back_populates="user")
    documents = relationship("Document", back_populates="user")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    url = Column(String, nullable=True)
    content_type = Column(Enum(ContentTypeEnum), nullable=False)
    raw_text = Column(Text, nullable=True)
    trust_score = Column(Integer, nullable=True)
    verdict = Column(Enum(VerdictEnum), nullable=True)
    status = Column(Enum(ScanStatusEnum), default=ScanStatusEnum.pending)
    scan_duration = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="scans")
    signals = relationship("Signal", back_populates="scan", cascade="all, delete-orphan")


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String, primary_key=True, default=generate_uuid)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)
    type = Column(String, nullable=False) # e.g. text, image, metadata, review
    score = Column(Integer, nullable=False)
    label = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    evidence = Column(JSON, nullable=True) # stores JSON breakdown
    highlights = Column(JSON, nullable=True) # stores array of strings

    scan = relationship("Scan", back_populates="signals")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    hash = Column(String, nullable=False, index=True)
    status = Column(String, default="pending")
    trust_score = Column(Integer, nullable=True)
    findings = Column(JSON, nullable=True) # stores array of document findings
    
    # Signature info
    signature = Column(String, nullable=True)
    public_key = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents")
