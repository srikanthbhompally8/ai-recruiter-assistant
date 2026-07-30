"""Candidate Model"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime
import uuid


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    full_name = Column(String(255), nullable=False)

    # Parsed profile data
    skills = Column(ARRAY(String), nullable=True)
    experience_years = Column(Integer, nullable=True)
    current_title = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)

    # Structured data
    profile_json = Column(JSONB, nullable=True)

    # File references
    resume_file_path = Column(String(512), nullable=True)
    resume_s3_key = Column(String(512), nullable=True)

    # Status & metadata
    status = Column(String(50), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Search optimization (future)
    # full_text_search = Column(TSVECTOR, nullable=True)
    # embedding = Column(Vector(1536), nullable=True)

    def __repr__(self):
        return f"<Candidate {self.full_name}>"
