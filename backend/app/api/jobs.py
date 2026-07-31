"""Job Description Management API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
import logging

from app.database import get_db
from app.models import JobDescription
from app.celery_app import calculate_matches_async

router = APIRouter()
logger = logging.getLogger(__name__)


class JobDescriptionCreate(BaseModel):
    """Schema for creating job description"""
    title: str
    company: str
    description: str
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    experience_required: Optional[int] = None
    job_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None


class JobDescriptionUpdate(BaseModel):
    """Schema for updating job description"""
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    nice_to_have_skills: Optional[List[str]] = None
    experience_required: Optional[int] = None
    job_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    status: Optional[str] = None


@router.post("/jobs")
async def create_job(
    job_data: JobDescriptionCreate,
    db: Session = Depends(get_db),
):
    """
    Create new job description

    Args:
        job_data: Job description details

    Returns:
        Created job with ID
    """
    try:
        job = JobDescription(
            id=uuid4(),
            user_id=uuid4(),  # TODO: Get from authenticated user
            title=job_data.title,
            company=job_data.company,
            description=job_data.description,
            required_skills=job_data.required_skills,
            nice_to_have_skills=job_data.nice_to_have_skills,
            experience_required=job_data.experience_required,
            job_type=job_data.job_type,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        # Queue async matching task
        calculate_matches_async.delay(str(job.id))

        logger.info(f"Job created and queued for matching: {job.id}")

        return {
            "status": "success",
            "data": {
                "id": str(job.id),
                "title": job.title,
                "company": job.company,
                "required_skills": job.required_skills,
                "nice_to_have_skills": job.nice_to_have_skills,
                "experience_required": job.experience_required,
                "job_type": job.job_type,
                "message": "Job created. Matching candidates in progress...",
            },
        }

    except Exception as e:
        logger.error(f"Job creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
):
    """
    List all job descriptions with optional filtering

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum records to return
        status: Filter by status (open, closed, etc)

    Returns:
        List of jobs
    """
    try:
        query = db.query(JobDescription)

        if status:
            query = query.filter(JobDescription.status == status)

        jobs = query.offset(skip).limit(limit).all()

        return {
            "status": "success",
            "data": [
                {
                    "id": str(j.id),
                    "title": j.title,
                    "company": j.company,
                    "required_skills": j.required_skills,
                    "experience_required": j.experience_required,
                    "job_type": j.job_type,
                    "status": j.status,
                    "salary_min": float(j.salary_min) if j.salary_min else None,
                    "salary_max": float(j.salary_max) if j.salary_max else None,
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                }
                for j in jobs
            ],
            "total": len(jobs),
        }

    except Exception as e:
        logger.error(f"List jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Get job description details by ID"""
    try:
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "status": "success",
            "data": {
                "id": str(job.id),
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "required_skills": job.required_skills,
                "nice_to_have_skills": job.nice_to_have_skills,
                "experience_required": job.experience_required,
                "job_type": job.job_type,
                "salary_min": float(job.salary_min) if job.salary_min else None,
                "salary_max": float(job.salary_max) if job.salary_max else None,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/jobs/{job_id}")
async def update_job(
    job_id: str,
    job_data: JobDescriptionUpdate,
    db: Session = Depends(get_db),
):
    """Update job description"""
    try:
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Update fields if provided
        for field, value in job_data.dict(exclude_unset=True).items():
            setattr(job, field, value)

        db.commit()
        db.refresh(job)

        logger.info(f"Job updated: {job_id}")

        return {
            "status": "success",
            "data": {
                "id": str(job.id),
                "title": job.title,
                "company": job.company,
                "status": job.status,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
