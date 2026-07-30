"""Base Schema Classes"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
