"""Skills Matching, Ranking, and Gap Analysis API Endpoints

Recruiter-facing APIs for:
- Skill matching between candidates and jobs
- Candidate ranking by skill match
- Skills gap analysis with learning recommendations
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List
import logging
from app.services.recommendation_service import RecommendationService
from app.services.skill_matcher_service import SkillMatcherService
from app.services.auth_service import auth_service
from app.database import SessionLocal
from app.models import Candidate, JobDescription
from sqlalchemy.orm import Session
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)


def get_db():
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=403, detail="Authorization header missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]
    payload = auth_service.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


@router.post("/match", response_model=dict)
async def match_candidate_skills(
    request: dict,
    token_payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Match candidate skills to job requirements.

    Request body:
    {
        "candidate_id": "uuid",
        "job_id": "uuid"
    }

    Returns:
        Detailed skill match analysis with scoring breakdown
    """
    try:
        candidate_id = request.get("candidate_id")
        job_id = request.get("job_id")

        if not candidate_id or not job_id:
            raise HTTPException(
                status_code=400,
                detail="candidate_id and job_id are required"
            )

        # Convert strings to UUIDs
        try:
            candidate_id = uuid.UUID(candidate_id)
            job_id = uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        # Get candidate and job from database
        candidate = db.query(Candidate).filter(
            Candidate.id == candidate_id
        ).first()

        job = db.query(JobDescription).filter(
            JobDescription.id == job_id
        ).first()

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        logger.info(f"Matching skills: candidate {candidate_id} -> job {job_id}")

        # Match skills using SkillMatcherService
        skill_matcher = SkillMatcherService(db)
        match_result = skill_matcher.match_skills(candidate, job)

        # Also get recommendation score for confidence
        recommendation = RecommendationService(db)
        rec_score, rec_breakdown = recommendation.calculate_recommendation_score(
            str(candidate_id),
            str(job_id)
        )

        return {
            "status": "success",
            "data": {
                "candidate_id": str(candidate_id),
                "candidate_name": candidate.full_name,
                "job_id": str(job_id),
                "job_title": job.title,
                "skills_match_score": round(match_result.skills_match_score / 100.0, 3),
                "confidence_score": round(rec_score / 100.0, 3),
                "exact_matches": [
                    {
                        "skill": m.skill_name,
                        "proficiency": m.proficiency_level or "unspecified",
                        "importance": m.importance
                    }
                    for m in match_result.exact_matches
                ],
                "related_matches": [
                    {
                        "skill": m.skill_name,
                        "similarity_score": round(m.score / 100.0, 2),
                        "importance": m.importance
                    }
                    for m in match_result.related_matches
                ],
                "missing_required": [
                    {
                        "skill": m.skill_name,
                        "importance": m.importance,
                        "priority": "high"
                    }
                    for m in match_result.missing_required
                ],
                "missing_preferred": [
                    {
                        "skill": m.skill_name,
                        "importance": m.importance,
                        "priority": "low"
                    }
                    for m in match_result.missing_preferred
                ],
                "gap_analysis": match_result.gap_analysis,
                "recommendation": {
                    "match_quality": "excellent" if rec_score >= 80 else "good" if rec_score >= 60 else "fair" if rec_score >= 40 else "poor",
                    "recommendation_score": round(rec_score / 100.0, 3),
                    "scoring_breakdown": rec_breakdown
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching skills: {e}")
        raise HTTPException(status_code=500, detail=f"Skill matching error: {str(e)}")


@router.post("/rank", response_model=dict)
async def rank_candidates_by_skills(
    request: dict,
    token_payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Rank candidates by skill match for a specific job.

    Request body:
    {
        "job_id": "uuid",
        "limit": 10,
        "min_score": 0.6
    }

    Returns:
        Ranked list of candidates with skill match scores
    """
    try:
        job_id = request.get("job_id")
        limit = request.get("limit", 10)
        min_score = request.get("min_score", 0.6)

        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")

        # Convert to UUID
        try:
            job_id = uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        # Verify job exists
        job = db.query(JobDescription).filter(
            JobDescription.id == job_id
        ).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        logger.info(f"Ranking candidates for job {job_id}")

        # Get top candidates using SkillMatcherService
        skill_matcher = SkillMatcherService(db)
        top_candidates = skill_matcher.get_top_candidates_by_skills(
            str(job_id),
            limit=limit,
            min_score=min_score
        )

        # Enhance with recommendation scores
        recommendation = RecommendationService(db)
        enhanced_candidates = []

        for candidate_data in top_candidates:
            cand_id = uuid.UUID(candidate_data["candidate_id"])
            rec_score, _ = recommendation.calculate_recommendation_score(
                str(cand_id),
                str(job_id)
            )

            candidate_data["recommendation_score"] = round(rec_score / 100.0, 3)
            candidate_data["overall_score"] = round(
                (candidate_data["score"] * 0.6 + rec_score / 100.0 * 0.4),
                3
            )
            enhanced_candidates.append(candidate_data)

        # Sort by overall score
        enhanced_candidates.sort(key=lambda x: x["overall_score"], reverse=True)

        return {
            "status": "success",
            "data": {
                "job_id": str(job_id),
                "job_title": job.title,
                "total_candidates_evaluated": len(top_candidates),
                "candidates": [
                    {
                        "rank": idx + 1,
                        "candidate_id": c["candidate_id"],
                        "name": c["name"],
                        "email": c["email"],
                        "current_title": c.get("current_title", ""),
                        "experience_years": c.get("experience_years", 0),
                        "skills_match_score": c["score"],
                        "recommendation_score": c["recommendation_score"],
                        "overall_score": c["overall_score"],
                        "exact_matches": c["exact_matches"],
                        "related_matches": c["related_matches"],
                        "missing_required": c["missing_required"]
                    }
                    for idx, c in enumerate(enhanced_candidates)
                ]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ranking candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Ranking error: {str(e)}")


@router.post("/gaps", response_model=dict)
async def analyze_skills_gaps(
    request: dict,
    token_payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Analyze skills gaps between candidate and job requirements.

    Request body:
    {
        "candidate_id": "uuid",
        "job_id": "uuid"
    }

    Returns:
        Detailed gap analysis with prioritized missing skills
    """
    try:
        candidate_id = request.get("candidate_id")
        job_id = request.get("job_id")

        if not candidate_id or not job_id:
            raise HTTPException(
                status_code=400,
                detail="candidate_id and job_id are required"
            )

        # Convert to UUIDs
        try:
            candidate_id = uuid.UUID(candidate_id)
            job_id = uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        # Get candidate and job
        candidate = db.query(Candidate).filter(
            Candidate.id == candidate_id
        ).first()

        job = db.query(JobDescription).filter(
            JobDescription.id == job_id
        ).first()

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        logger.info(f"Analyzing skill gaps: candidate {candidate_id} -> job {job_id}")

        # Get skill match details
        skill_matcher = SkillMatcherService(db)
        match_result = skill_matcher.match_skills(candidate, job)

        # Get recommendation score
        recommendation = RecommendationService(db)
        rec_score, _ = recommendation.calculate_recommendation_score(
            str(candidate_id),
            str(job_id)
        )

        # Prioritize missing skills
        critical_gaps = [
            {
                "skill": m.skill_name,
                "importance": m.importance,
                "priority": "critical",
                "estimated_learning_time_hours": 40 if m.importance == "high" else 20,
                "resources": [
                    {"type": "course", "platform": "Udemy", "estimated_cost": 15},
                    {"type": "certification", "platform": "freeCodeCamp", "estimated_cost": 0}
                ]
            }
            for m in match_result.missing_required
        ]

        optional_gaps = [
            {
                "skill": m.skill_name,
                "importance": m.importance,
                "priority": "optional",
                "estimated_learning_time_hours": 20,
                "resources": [
                    {"type": "course", "platform": "Udemy", "estimated_cost": 15}
                ]
            }
            for m in match_result.missing_preferred
        ]

        # Calculate readiness
        total_required = len(match_result.exact_matches) + len(match_result.missing_required)
        readiness = (len(match_result.exact_matches) / total_required * 100) if total_required > 0 else 0

        return {
            "status": "success",
            "data": {
                "candidate_id": str(candidate_id),
                "candidate_name": candidate.full_name,
                "job_id": str(job_id),
                "job_title": job.title,
                "readiness_score": round(readiness, 1),
                "recommendation_score": round(rec_score / 100.0, 3),
                "skill_coverage": match_result.gap_analysis.get("coverage", "0%"),
                "critical_gaps": critical_gaps,
                "optional_gaps": optional_gaps,
                "learning_plan": {
                    "total_estimated_hours": sum(g["estimated_learning_time_hours"] for g in critical_gaps),
                    "estimated_weeks": max(2, sum(g["estimated_learning_time_hours"] for g in critical_gaps) // 20),
                    "priority": "high" if len(critical_gaps) > 0 else "low",
                    "recommendation": (
                        f"Candidate should focus on {', '.join(g['skill'] for g in critical_gaps[:3])} "
                        f"before applying. Estimated {sum(g['estimated_learning_time_hours'] for g in critical_gaps)} hours of learning required."
                        if critical_gaps else "Candidate is well-qualified for this position."
                    )
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing gaps: {e}")
        raise HTTPException(status_code=500, detail=f"Gap analysis error: {str(e)}")
