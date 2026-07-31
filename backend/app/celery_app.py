"""Celery Configuration for Async Tasks"""
from celery import Celery
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "ai_recruiter",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(bind=True)
def parse_resume_async(self, candidate_id: str, resume_text: str):
    """
    Async task for parsing resume

    Args:
        candidate_id: UUID of candidate
        resume_text: Raw resume text
    """
    try:
        from app.services.resume_parser import resume_parser
        from app.database import SessionLocal
        from app.models import Candidate

        logger.info(f"Starting async resume parsing for candidate: {candidate_id}")

        # Parse resume
        parsed_data = resume_parser.parse_resume(resume_text)

        # Update candidate in database
        db = SessionLocal()
        try:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if candidate:
                candidate.profile_json = parsed_data
                candidate.skills = parsed_data.get("skills", [])
                candidate.current_title = parsed_data.get("current_title")
                candidate.current_company = parsed_data.get("current_company")
                candidate.experience_years = parsed_data.get("experience_years")
                db.commit()
                logger.info(f"Resume parsed and saved for candidate: {candidate_id}")
            else:
                logger.warning(f"Candidate not found: {candidate_id}")

        finally:
            db.close()

        return {
            "status": "success",
            "candidate_id": candidate_id,
            "data": parsed_data,
        }

    except Exception as e:
        logger.error(f"Error parsing resume for candidate {candidate_id}: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def calculate_matches_async(self, job_id: str):
    """
    Async task for calculating matches for a job

    Args:
        job_id: UUID of job description
    """
    try:
        from app.database import SessionLocal
        from app.models import JobDescription, Candidate, Match
        from app.services.matching_engine import matching_engine

        logger.info(f"Starting async match calculation for job: {job_id}")

        db = SessionLocal()
        try:
            job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return

            candidates = db.query(Candidate).filter(Candidate.status == "active").all()

            matches_created = 0
            for candidate in candidates:
                # Calculate match
                match_result = matching_engine.calculate_match(
                    candidate_skills=candidate.skills or [],
                    job_required_skills=job.required_skills or [],
                    job_nice_to_have_skills=job.nice_to_have_skills or [],
                    candidate_experience=candidate.experience_years or 0,
                    job_experience_required=job.experience_required or 0,
                )

                # Check if match already exists
                existing_match = db.query(Match).filter(
                    Match.candidate_id == candidate.id,
                    Match.job_id == job.id,
                ).first()

                if existing_match:
                    # Update existing match
                    existing_match.skills_match = match_result["skills_match"]
                    existing_match.experience_match = match_result["experience_match"]
                    existing_match.overall_score = match_result["overall_score"]
                    existing_match.matched_skills = match_result["matched_skills"]
                    existing_match.missing_skills = match_result["missing_skills"]
                    existing_match.recommendation = match_result["recommendation"]
                    existing_match.match_details_json = match_result["details"]
                else:
                    # Create new match
                    from uuid import uuid4
                    match = Match(
                        id=uuid4(),
                        candidate_id=candidate.id,
                        job_id=job.id,
                        skills_match=match_result["skills_match"],
                        experience_match=match_result["experience_match"],
                        overall_score=match_result["overall_score"],
                        matched_skills=match_result["matched_skills"],
                        missing_skills=match_result["missing_skills"],
                        recommendation=match_result["recommendation"],
                        match_details_json=match_result["details"],
                    )
                    db.add(match)
                    matches_created += 1

            db.commit()
            logger.info(f"Match calculation complete for job {job_id}. Created/updated: {matches_created}")

        finally:
            db.close()

        return {
            "status": "success",
            "job_id": job_id,
            "matches_created": matches_created,
        }

    except Exception as e:
        logger.error(f"Error calculating matches for job {job_id}: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)
