"""Candidate Management API Endpoints"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
import logging

from app.database import get_db
from app.models import Candidate
from app.services.s3_service import s3_service
from app.services.resume_parser import resume_parser
from app.celery_app import parse_resume_async
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    candidate_id: str = None,
    db: Session = Depends(get_db),
):
    """
    Upload and parse resume for candidate

    Args:
        file: Resume file (PDF, DOCX, or TXT)
        candidate_id: Existing candidate ID (optional)

    Returns:
        Candidate data with parsing status
    """
    try:
        # Validate file type
        if file.filename:
            file_ext = file.filename.split(".")[-1].lower()
            if file_ext not in settings.ALLOWED_FILE_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}",
                )

        # Read file content
        content = await file.read()

        # Check file size
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
            )

        # Upload to S3
        file_key = f"resumes/{uuid4()}/{file.filename}"
        s3_url = s3_service.upload_file(
            file_key=file_key,
            file_content=content,
            content_type=file.content_type or "application/octet-stream",
            metadata={"candidate_id": candidate_id or "unknown"},
        )

        # Convert file to text (basic implementation)
        # In production, use Apache Tika or similar for proper conversion
        resume_text = content.decode("utf-8", errors="ignore")

        # Find or create candidate
        if candidate_id:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
        else:
            candidate = Candidate(
                id=uuid4(),
                email=f"candidate_{uuid4()}@example.com",  # Placeholder
                full_name="Uploaded Candidate",
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

        # Update candidate with file info
        candidate.resume_file_path = file_key
        candidate.resume_s3_key = file_key
        db.commit()

        # Queue async parsing task
        parse_resume_async.delay(str(candidate.id), resume_text)

        logger.info(f"Resume uploaded and queued for parsing: {candidate.id}")

        return {
            "status": "success",
            "candidate_id": str(candidate.id),
            "message": "Resume uploaded successfully. Parsing in progress...",
            "s3_url": s3_url,
            "file_key": file_key,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/candidates")
async def list_candidates(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
):
    """
    List all candidates with optional filtering

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum records to return
        status: Filter by status (active, archived, etc)

    Returns:
        List of candidates
    """
    try:
        query = db.query(Candidate)

        if status:
            query = query.filter(Candidate.status == status)

        candidates = query.offset(skip).limit(limit).all()

        return {
            "status": "success",
            "data": [
                {
                    "id": str(c.id),
                    "email": c.email,
                    "full_name": c.full_name,
                    "current_title": c.current_title,
                    "current_company": c.current_company,
                    "skills": c.skills,
                    "experience_years": c.experience_years,
                    "status": c.status,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in candidates
            ],
            "total": len(candidates),
        }

    except Exception as e:
        logger.error(f"List candidates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidates/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
):
    """Get candidate details by ID"""
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return {
            "status": "success",
            "data": {
                "id": str(candidate.id),
                "email": candidate.email,
                "full_name": candidate.full_name,
                "phone": candidate.phone,
                "current_title": candidate.current_title,
                "current_company": candidate.current_company,
                "skills": candidate.skills,
                "experience_years": candidate.experience_years,
                "profile_json": candidate.profile_json,
                "resume_s3_key": candidate.resume_s3_key,
                "status": candidate.status,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
                "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get candidate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
