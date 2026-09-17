"""Job Description Parsing API Endpoint"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from app.services.bedrock_service import bedrock_service
from app.services.auth_service import auth_service
from app.database import SessionLocal
from app.models import JobDescription
from sqlalchemy.orm import Session
import uuid
import logging

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


@router.post("/parse", response_model=dict)
async def parse_job_description(
    request: dict,
    token_payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Parse raw job description and extract structured data using Bedrock AI

    Request body:
    {
        "job_description": "Raw job description text",
        "company": "Optional company name",
        "source": "Optional source (linkedin, indeed, etc)"
    }

    Returns:
        Parsed job data with extracted fields
    """
    try:
        job_description = request.get("job_description", "").strip()
        company = request.get("company", "").strip()
        source = request.get("source", "").strip()

        if not job_description:
            raise HTTPException(status_code=400, detail="job_description is required")

        if len(job_description) < 50:
            raise HTTPException(status_code=400, detail="Job description too short (minimum 50 characters)")

        logger.info(f"Parsing job description (length: {len(job_description)} chars)")

        # Call Bedrock service to parse job description
        result = bedrock_service.parse_job_description(job_description)

        if not result or result.get("status") != "success":
            logger.error(f"Bedrock parsing failed: {result.get('message', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Job parsing failed: {result.get('message', 'AI service error')}"
            )

        parsed_data = result.get("data", {})
        user_id = uuid.UUID(token_payload.get("user_id"))

        # Create job record in database
        job = JobDescription(
            id=uuid.uuid4(),
            user_id=user_id,
            title=parsed_data.get("job_title", "Untitled"),
            company=company or parsed_data.get("company", ""),
            description=job_description,
            required_skills=",".join(parsed_data.get("required_skills", [])),
            nice_to_have_skills=",".join(parsed_data.get("nice_to_have_skills", [])),
            experience_required=parsed_data.get("years_required"),
            job_type=parsed_data.get("job_type", ""),
            job_details_json=parsed_data
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Job created: {job.title} (ID: {job.id})")

        return {
            "status": "success",
            "message": "Job description parsed and saved successfully",
            "data": {
                "job_id": str(job.id),
                "title": job.title,
                "company": job.company,
                "job_type": parsed_data.get("job_type"),
                "experience_required": parsed_data.get("years_required"),
                "job_level": parsed_data.get("job_level"),
                "required_skills": parsed_data.get("required_skills", []),
                "nice_to_have_skills": parsed_data.get("nice_to_have_skills", []),
                "salary_range": parsed_data.get("salary_range"),
                "responsibilities": parsed_data.get("responsibilities", [])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job parsing error: {e}")
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")


@router.post("/extract-skills", response_model=dict)
async def extract_skills_from_text(
    request: dict,
    token_payload: dict = Depends(verify_token)
):
    """
    Extract technical and soft skills from text (candidate profile, resume, etc)

    Request body:
    {
        "text": "Candidate profile or resume text"
    }

    Returns:
        Extracted skills with proficiency levels
    """
    try:
        text = request.get("text", "").strip()

        if not text:
            raise HTTPException(status_code=400, detail="text is required")

        if len(text) < 50:
            raise HTTPException(status_code=400, detail="Text too short (minimum 50 characters)")

        logger.info(f"Extracting skills from text (length: {len(text)} chars)")

        # Call Bedrock service to extract skills
        result = bedrock_service.extract_skills(text)

        if not result or result.get("status") != "success":
            logger.error(f"Skill extraction failed: {result.get('message', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Skill extraction failed: {result.get('message', 'AI service error')}"
            )

        skills_data = result.get("data", {})
        logger.info(f"Skills extracted: {len(skills_data.get('technical_skills', []))} technical, {len(skills_data.get('soft_skills', []))} soft")

        return {
            "status": "success",
            "message": "Skills extracted successfully",
            "data": {
                "technical_skills": skills_data.get("technical_skills", []),
                "soft_skills": skills_data.get("soft_skills", []),
                "proficiency_levels": skills_data.get("proficiency_levels", {}),
                "total_technical": len(skills_data.get("technical_skills", [])),
                "total_soft": len(skills_data.get("soft_skills", []))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skill extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")
