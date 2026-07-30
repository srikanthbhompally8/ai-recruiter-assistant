"""Job Description Model"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, ARRAY, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base
from datetime import datetime
import uuid


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)

    # Parsed JD data
    required_skills = Column(ARRAY(String), nullable=True)
    nice_to_have_skills = Column(ARRAY(String), nullable=True)
    experience_required = Column(Integer, nullable=True)
    job_type = Column(String(50), nullable=True)
    salary_min = Column(Numeric(10, 2), nullable=True)
    salary_max = Column(Numeric(10, 2), nullable=True)

    # Structured data
    job_details_json = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)

    # Status
    status = Column(String(50), default="open", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Search optimization (future)
    # full_text_search = Column(TSVECTOR, nullable=True)
    # embedding = Column(Vector(1536), nullable=True)

    def __repr__(self):
        return f"<JobDescription {self.title}>"
