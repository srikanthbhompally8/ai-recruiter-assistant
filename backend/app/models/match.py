"""Match Model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, ARRAY, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base
from datetime import datetime
import uuid


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False)

    # Match scores (0-100)
    skills_match = Column(Numeric(5, 2), nullable=True)
    experience_match = Column(Numeric(5, 2), nullable=True)
    overall_score = Column(Numeric(5, 2), nullable=True)

    # Matching details
    matched_skills = Column(ARRAY(String), nullable=True)
    missing_skills = Column(ARRAY(String), nullable=True)
    match_explanation = Column(Text, nullable=True)
    match_details_json = Column(JSONB, nullable=True)

    # Recommendation
    recommendation = Column(String(50), nullable=True)

    # Status
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    viewed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_matches_candidate_job', 'candidate_id', 'job_id', unique=True),
    )

    def __repr__(self):
        return f"<Match candidate:{self.candidate_id} job:{self.job_id}>"
