"""Match Management API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

from app.database import get_db
from app.models import Match, Candidate, JobDescription

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/matches/job/{job_id}")
async def get_job_matches(
    job_id: str,
    min_score: Optional[float] = None,
    recommendation: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Get all matches for a specific job

    Args:
        job_id: Job ID
        min_score: Minimum overall score filter
        recommendation: Filter by recommendation (recommended, marginal, not_recommended)
        skip: Pagination offset
        limit: Pagination limit

    Returns:
        List of matches with candidate details
    """
    try:
        # Verify job exists
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        query = db.query(Match).filter(Match.job_id == job_id)

        if min_score is not None:
            query = query.filter(Match.overall_score >= min_score)

        if recommendation:
            query = query.filter(Match.recommendation == recommendation)

        matches = query.order_by(Match.overall_score.desc()).offset(skip).limit(limit).all()

        result = []
        for match in matches:
            candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
            result.append({
                "match_id": str(match.id),
                "candidate_id": str(match.candidate_id),
                "candidate_name": candidate.full_name if candidate else "Unknown",
                "candidate_email": candidate.email if candidate else None,
                "skills_match": float(match.skills_match) if match.skills_match else 0,
                "experience_match": float(match.experience_match) if match.experience_match else 0,
                "overall_score": float(match.overall_score) if match.overall_score else 0,
                "matched_skills": match.matched_skills,
                "missing_skills": match.missing_skills,
                "recommendation": match.recommendation,
                "status": match.status,
                "created_at": match.created_at.isoformat() if match.created_at else None,
            })

        return {
            "status": "success",
            "data": result,
            "total": len(result),
            "job_title": job.title,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job matches error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches/candidate/{candidate_id}")
async def get_candidate_matches(
    candidate_id: str,
    min_score: Optional[float] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Get all matches for a specific candidate

    Args:
        candidate_id: Candidate ID
        min_score: Minimum overall score filter
        skip: Pagination offset
        limit: Pagination limit

    Returns:
        List of matches with job details
    """
    try:
        # Verify candidate exists
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        query = db.query(Match).filter(Match.candidate_id == candidate_id)

        if min_score is not None:
            query = query.filter(Match.overall_score >= min_score)

        matches = query.order_by(Match.overall_score.desc()).offset(skip).limit(limit).all()

        result = []
        for match in matches:
            job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
            result.append({
                "match_id": str(match.id),
                "job_id": str(match.job_id),
                "job_title": job.title if job else "Unknown",
                "company": job.company if job else None,
                "skills_match": float(match.skills_match) if match.skills_match else 0,
                "experience_match": float(match.experience_match) if match.experience_match else 0,
                "overall_score": float(match.overall_score) if match.overall_score else 0,
                "matched_skills": match.matched_skills,
                "missing_skills": match.missing_skills,
                "recommendation": match.recommendation,
                "status": match.status,
                "created_at": match.created_at.isoformat() if match.created_at else None,
            })

        return {
            "status": "success",
            "data": result,
            "total": len(result),
            "candidate_name": candidate.full_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get candidate matches error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches/{match_id}")
async def get_match(
    match_id: str,
    db: Session = Depends(get_db),
):
    """Get detailed match information"""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()

        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()

        return {
            "status": "success",
            "data": {
                "id": str(match.id),
                "candidate": {
                    "id": str(candidate.id),
                    "name": candidate.full_name,
                    "email": candidate.email,
                } if candidate else None,
                "job": {
                    "id": str(job.id),
                    "title": job.title,
                    "company": job.company,
                } if job else None,
                "skills_match": float(match.skills_match) if match.skills_match else 0,
                "experience_match": float(match.experience_match) if match.experience_match else 0,
                "overall_score": float(match.overall_score) if match.overall_score else 0,
                "matched_skills": match.matched_skills,
                "missing_skills": match.missing_skills,
                "match_explanation": match.match_explanation,
                "recommendation": match.recommendation,
                "match_details": match.match_details_json,
                "status": match.status,
                "created_at": match.created_at.isoformat() if match.created_at else None,
                "viewed_at": match.viewed_at.isoformat() if match.viewed_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get match error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/matches/{match_id}/status")
async def update_match_status(
    match_id: str,
    status: str,
    db: Session = Depends(get_db),
):
    """Update match status (e.g., contacted, hired, rejected)"""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()

        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        # Mark as viewed if first time updating
        if not match.viewed_at:
            match.viewed_at = datetime.utcnow()

        match.status = status
        db.commit()
        db.refresh(match)

        logger.info(f"Match status updated: {match_id} -> {status}")

        return {
            "status": "success",
            "data": {
                "id": str(match.id),
                "status": match.status,
                "updated_at": match.updated_at.isoformat() if match.updated_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update match status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
