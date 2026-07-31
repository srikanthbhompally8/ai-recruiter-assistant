"""Skill Taxonomy Model"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from datetime import datetime
import uuid


class SkillTaxonomy(Base):
    __tablename__ = "skill_taxonomy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    proficiency_levels = Column(ARRAY(String), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SkillTaxonomy {self.skill_name}>"
