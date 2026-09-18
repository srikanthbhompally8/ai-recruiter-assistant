"""Candidate-Job Recommendation Engine Service

Implements weighted scoring model for matching candidates to jobs using:
- Semantic similarity (job description understanding)
- Skills matching (technical alignment)
- Experience matching (years requirement)
- Education alignment (degree/certification)
- Location compatibility (geographic fit)
"""

import logging
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User, Candidate, JobDescription, Match
from sqlalchemy import text

logger = logging.getLogger(__name__)


class ScoringWeights:
    """Configurable scoring weights for recommendation algorithm"""

    def __init__(
        self,
        semantic_weight: float = 0.30,
        skills_weight: float = 0.35,
        experience_weight: float = 0.20,
        education_weight: float = 0.10,
        location_weight: float = 0.05
    ):
        """Initialize scoring weights (must sum to 1.0)"""
        self.semantic_weight = semantic_weight
        self.skills_weight = skills_weight
        self.experience_weight = experience_weight
        self.education_weight = education_weight
        self.location_weight = location_weight

        # Validate weights sum to 1.0
        total = (semantic_weight + skills_weight + experience_weight +
                education_weight + location_weight)
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for storage"""
        return {
            "semantic": self.semantic_weight,
            "skills": self.skills_weight,
            "experience": self.experience_weight,
            "education": self.education_weight,
            "location": self.location_weight
        }


class RecommendationService:
    """Main recommendation engine service"""

    def __init__(self, db: Session, weights: Optional[ScoringWeights] = None):
        """Initialize recommendation service with database session and weights"""
        self.db = db
        self.weights = weights or ScoringWeights()
        logger.info(f"RecommendationService initialized with weights: {self.weights.to_dict()}")

    def calculate_recommendation_score(
        self,
        candidate_id: str,
        job_id: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate final recommendation score between candidate and job.

        Returns:
            Tuple of (final_score: 0-100, score_breakdown: dict)

        Score breakdown includes:
        - semantic_similarity: 0-100
        - skills_match: 0-100
        - experience_match: 0-100
        - education_match: 0-100
        - location_match: 0-100
        - final_weighted_score: 0-100
        """
        try:
            import uuid as uuid_module

            # Convert string to UUID if needed
            if isinstance(candidate_id, str):
                try:
                    candidate_id = uuid_module.UUID(candidate_id)
                except:
                    pass

            if isinstance(job_id, str):
                try:
                    job_id = uuid_module.UUID(job_id)
                except:
                    pass

            # Get candidate and job from database
            candidate = self.db.query(Candidate).filter(
                Candidate.id == candidate_id
            ).first()

            job = self.db.query(JobDescription).filter(
                JobDescription.id == job_id
            ).first()

            if not candidate or not job:
                logger.warning(f"Candidate {candidate_id} or Job {job_id} not found")
                return 0.0, {}

            # Calculate individual scores
            semantic_score = self._calculate_semantic_similarity(candidate, job)
            skills_score = self._calculate_skills_match(candidate, job)
            experience_score = self._calculate_experience_match(candidate, job)
            education_score = self._calculate_education_match(candidate, job)
            location_score = self._calculate_location_match(candidate, job)

            # Build score breakdown
            score_breakdown = {
                "semantic_similarity": round(semantic_score, 2),
                "skills_match": round(skills_score, 2),
                "experience_match": round(experience_score, 2),
                "education_match": round(education_score, 2),
                "location_match": round(location_score, 2)
            }

            # Calculate weighted final score
            final_score = (
                (semantic_score * self.weights.semantic_weight) +
                (skills_score * self.weights.skills_weight) +
                (experience_score * self.weights.experience_weight) +
                (education_score * self.weights.education_weight) +
                (location_score * self.weights.location_weight)
            )

            score_breakdown["final_weighted_score"] = round(final_score, 2)

            logger.debug(f"Recommendation score for candidate {candidate_id} -> job {job_id}: {final_score}")
            return final_score, score_breakdown

        except Exception as e:
            logger.error(f"Error calculating recommendation score: {e}")
            return 0.0, {}

    def _calculate_semantic_similarity(self, candidate: Candidate, job: JobDescription) -> float:
        """
        Calculate semantic similarity between candidate profile and job description.

        For now, uses simple heuristic scoring based on profile overlap.
        Future: integrate with Bedrock embeddings API for true semantic matching.

        Returns: Score 0-100
        """
        try:
            score = 75.0  # Default baseline

            # Check if candidate has relevant experience description
            if candidate.profile_json:
                profile = candidate.profile_json if isinstance(candidate.profile_json, dict) else {}

                # Bonus if profile description exists and is detailed
                description = profile.get("description", "")
                if description and len(description) > 200:
                    score += 10.0

                # Bonus if relevant keywords match job type
                if job.job_type and job.job_type.lower() in str(description).lower():
                    score += 5.0

            # Ensure score stays within 0-100
            return min(100.0, max(0.0, score))

        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 50.0

    def _calculate_skills_match(self, candidate: Candidate, job: JobDescription) -> float:
        """
        Calculate skills match between candidate and job.

        Scoring:
        - Each required skill match: +5 points (per skill)
        - Each nice-to-have match: +2 points (per skill)
        - Base score: 30 points

        Returns: Score 0-100
        """
        try:
            score = 40.0  # Base score (40 points baseline)

            # Parse job required skills
            job_required_skills = []
            job_nice_skills = []

            if job.required_skills:
                if isinstance(job.required_skills, str):
                    job_required_skills = [s.strip().lower() for s in job.required_skills.split(",")]
                elif isinstance(job.required_skills, list):
                    job_required_skills = [str(s).strip().lower() for s in job.required_skills]

            if job.nice_to_have_skills:
                if isinstance(job.nice_to_have_skills, str):
                    job_nice_skills = [s.strip().lower() for s in job.nice_to_have_skills.split(",")]
                elif isinstance(job.nice_to_have_skills, list):
                    job_nice_skills = [str(s).strip().lower() for s in job.nice_to_have_skills]

            # Parse candidate skills
            candidate_skills = []
            if candidate.skills:
                if isinstance(candidate.skills, str):
                    candidate_skills = [s.strip().lower() for s in candidate.skills.split(",")]
                elif isinstance(candidate.skills, list):
                    candidate_skills = [str(s).strip().lower() for s in candidate.skills]

            # Check profile_json for additional skills
            if candidate.profile_json and isinstance(candidate.profile_json, dict):
                profile_skills = candidate.profile_json.get("technical_skills", [])
                if isinstance(profile_skills, list):
                    candidate_skills.extend([str(s).strip().lower() for s in profile_skills])

            # Calculate matches
            required_matched = 0
            for req_skill in job_required_skills:
                if req_skill and any(req_skill in cs or cs in req_skill
                                     for cs in candidate_skills):
                    required_matched += 1

            nice_matched = 0
            for nice_skill in job_nice_skills:
                if nice_skill and any(nice_skill in cs or cs in nice_skill
                                      for cs in candidate_skills):
                    nice_matched += 1

            # Add points for matches
            score += required_matched * 8.0  # 8 points per required skill matched
            score += nice_matched * 3.0      # 3 points per nice-to-have skill matched

            # Bonus for extra skills beyond requirements
            required_and_nice = set(job_required_skills + job_nice_skills)
            extra_skills = len(candidate_skills) - len(required_and_nice)
            if extra_skills > 0:
                score += min(10.0, extra_skills * 0.5)  # Max 10 point bonus

            # Ensure score stays within 0-100
            return min(100.0, max(0.0, score))

        except Exception as e:
            logger.error(f"Error calculating skills match: {e}")
            return 40.0

    def _calculate_experience_match(self, candidate: Candidate, job: JobDescription) -> float:
        """
        Calculate experience level match.

        Scoring:
        - Perfect match (candidate years == required years): 100
        - Below requirement: 60 - (gap * 10)
        - Above requirement: 90 + min(10, (excess * 2))

        Returns: Score 0-100
        """
        try:
            required_years = job.experience_required or 0
            candidate_years = candidate.experience_years or 0

            if required_years == 0:
                return 100.0  # No requirement specified

            if candidate_years == required_years:
                return 100.0  # Perfect match

            if candidate_years < required_years:
                # Penalize for under-qualification
                gap = required_years - candidate_years
                score = 60.0 - (gap * 10.0)
                return max(0.0, score)

            # Bonus for exceeding requirement
            excess = candidate_years - required_years
            score = 90.0 + min(10.0, excess * 2.0)
            return min(100.0, score)

        except Exception as e:
            logger.error(f"Error calculating experience match: {e}")
            return 50.0

    def _calculate_education_match(self, candidate: Candidate, job: JobDescription) -> float:
        """
        Calculate education alignment.

        Returns: Score 0-100 (simplified - full implementation would check actual degrees)
        """
        try:
            # Simplified implementation
            # Full version would check candidate.education against job.preferred_education
            score = 70.0  # Default baseline

            # Bonus if candidate has profile information
            if candidate.profile_json:
                profile = candidate.profile_json if isinstance(candidate.profile_json, dict) else {}

                education = profile.get("education", [])
                if education and len(education) > 0:
                    score += 20.0

                # Bonus for advanced degrees
                education_str = str(education).lower()
                if "master" in education_str or "phd" in education_str or "mba" in education_str:
                    score += 10.0

            return min(100.0, max(0.0, score))

        except Exception as e:
            logger.error(f"Error calculating education match: {e}")
            return 60.0

    def _calculate_location_match(self, candidate: Candidate, job: JobDescription) -> float:
        """
        Calculate location compatibility.

        Returns: Score 0-100
        """
        try:
            score = 50.0  # Neutral baseline

            # If location info available, bonus for match
            if candidate.profile_json:
                profile = candidate.profile_json if isinstance(candidate.profile_json, dict) else {}
                candidate_location = profile.get("location", "")

                if job.company:
                    # Check for exact match
                    if candidate_location and candidate_location.lower() == str(job.company).lower():
                        score = 100.0
                    # Check if remote
                    elif "remote" in str(job.job_type or "").lower():
                        score = 85.0
                    # Check for same state/region (simplified)
                    elif candidate_location:
                        score += 30.0

            # Default to good score if remote job
            if job.job_type and "remote" in job.job_type.lower():
                score = max(score, 85.0)

            return min(100.0, max(0.0, score))

        except Exception as e:
            logger.error(f"Error calculating location match: {e}")
            return 50.0

    def get_top_candidates_for_job(
        self,
        job_id: str,
        limit: int = 10,
        min_score: float = 0.6
    ) -> List[Dict]:
        """
        Get top recommended candidates for a specific job.

        Returns:
            List of dicts with candidate info and scores, sorted by score descending
        """
        try:
            candidates = self.db.query(Candidate).all()
            recommendations = []

            for candidate in candidates:
                score, breakdown = self.calculate_recommendation_score(
                    str(candidate.id),
                    job_id
                )

                # Normalize score to 0-1
                normalized_score = score / 100.0

                if normalized_score >= min_score:
                    recommendations.append({
                        "candidate_id": str(candidate.id),
                        "name": candidate.full_name,
                        "email": candidate.email,
                        "current_title": candidate.current_title,
                        "experience_years": candidate.experience_years,
                        "score": round(normalized_score, 3),
                        "score_breakdown": breakdown
                    })

            # Sort by score descending
            recommendations.sort(key=lambda x: x["score"], reverse=True)

            # Return top N
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error getting top candidates for job: {e}")
            return []

    def get_recommended_jobs_for_candidate(
        self,
        candidate_id: str,
        limit: int = 10,
        min_score: float = 0.6
    ) -> List[Dict]:
        """
        Get top recommended jobs for a specific candidate.

        Returns:
            List of dicts with job info and scores, sorted by score descending
        """
        try:
            jobs = self.db.query(JobDescription).filter(
                JobDescription.status == "open"
            ).all()

            recommendations = []

            for job in jobs:
                score, breakdown = self.calculate_recommendation_score(
                    candidate_id,
                    str(job.id)
                )

                # Normalize score to 0-1
                normalized_score = score / 100.0

                if normalized_score >= min_score:
                    recommendations.append({
                        "job_id": str(job.id),
                        "title": job.title,
                        "company": job.company,
                        "job_type": job.job_type,
                        "experience_required": job.experience_required,
                        "score": round(normalized_score, 3),
                        "score_breakdown": breakdown
                    })

            # Sort by score descending
            recommendations.sort(key=lambda x: x["score"], reverse=True)

            # Return top N
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error getting recommended jobs for candidate: {e}")
            return []

    def update_weights(self, new_weights: ScoringWeights) -> None:
        """Update scoring weights"""
        try:
            self.weights = new_weights
            logger.info(f"Scoring weights updated: {new_weights.to_dict()}")
        except Exception as e:
            logger.error(f"Error updating weights: {e}")

    def get_current_weights(self) -> Dict[str, float]:
        """Get current scoring weights"""
        return self.weights.to_dict()


# Singleton instance for dependency injection
_recommendation_service = None


def get_recommendation_service(db: Session) -> RecommendationService:
    """Get or create recommendation service instance"""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService(db)
    return _recommendation_service
