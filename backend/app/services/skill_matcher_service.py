"""Advanced Skill Matching & Ranking Service

Implements semantic skill matching with:
- Skill normalization and similarity detection
- Configurable scoring weights by job category and experience level
- Skill ranking (exact matches, related skills, missing skills)
- Integration with RecommendationEngine for detailed explanations
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from app.models import Candidate, JobDescription

logger = logging.getLogger(__name__)


class ExperienceLevel(str, Enum):
    """Experience levels for weight configuration"""
    JUNIOR = "junior"      # 0-2 years
    MID = "mid"            # 3-5 years
    SENIOR = "senior"      # 6-10 years
    EXPERT = "expert"      # 10+ years


class JobCategory(str, Enum):
    """Job categories for configurable weights"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    DATA = "data"
    ML = "ml"
    QA = "qa"
    OTHER = "other"


@dataclass
class SkillMatch:
    """Represents a skill match result"""
    skill_name: str
    candidate_has: bool
    is_exact_match: bool
    is_related_match: bool
    proficiency_level: Optional[str] = None
    importance: str = "medium"  # low, medium, high, critical
    score: float = 0.0


@dataclass
class SkillMatchResult:
    """Complete skill matching result"""
    exact_matches: List[SkillMatch]
    related_matches: List[SkillMatch]
    missing_required: List[SkillMatch]
    missing_preferred: List[SkillMatch]
    skills_match_score: float  # 0-100
    gap_analysis: Dict[str, any]


class SkillWeights:
    """Configurable scoring weights for skill matching"""

    def __init__(
        self,
        exact_match_weight: float = 1.0,
        related_match_weight: float = 0.6,
        missing_required_penalty: float = -0.5,
        missing_preferred_penalty: float = -0.1,
        proficiency_bonus_weight: float = 0.3
    ):
        """Initialize skill match weights"""
        self.exact_match_weight = exact_match_weight
        self.related_match_weight = related_match_weight
        self.missing_required_penalty = missing_required_penalty
        self.missing_preferred_penalty = missing_preferred_penalty
        self.proficiency_bonus_weight = proficiency_bonus_weight

    def to_dict(self) -> Dict[str, float]:
        """Convert weights to dictionary"""
        return {
            "exact_match": self.exact_match_weight,
            "related_match": self.related_match_weight,
            "missing_required_penalty": self.missing_required_penalty,
            "missing_preferred_penalty": self.missing_preferred_penalty,
            "proficiency_bonus": self.proficiency_bonus_weight
        }


# Skill normalization mappings - maps variations to canonical form
SKILL_NORMALIZATION = {
    # Python variants
    "python": "python",
    "python3": "python",
    "python 3": "python",
    "py": "python",

    # JavaScript variants
    "javascript": "javascript",
    "js": "javascript",
    "node": "nodejs",
    "node.js": "nodejs",
    "nodejs": "nodejs",

    # REST API variants
    "rest": "rest_api",
    "rest api": "rest_api",
    "restful": "rest_api",
    "restful api": "rest_api",

    # Database variants
    "sql": "sql",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "mongo": "mongodb",

    # Cloud platforms
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "azure": "azure",

    # Containerization
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",

    # Frontend frameworks
    "react": "react",
    "vue": "vue",
    "vue.js": "vue",
    "angular": "angular",

    # Testing
    "jest": "jest",
    "pytest": "pytest",
    "unittest": "unittest",
    "mocha": "mocha",
}

# Skill similarity groups - skills that are related/transferable
SKILL_SIMILARITY_GROUPS = {
    "python": {"programming", "backend", "data", "automation"},
    "javascript": {"frontend", "web", "nodejs"},
    "java": {"backend", "programming", "android"},
    "rest_api": {"api_design", "web_services"},
    "postgresql": {"databases", "sql", "relational"},
    "mongodb": {"databases", "nosql", "document"},
    "docker": {"containerization", "devops", "deployment"},
    "kubernetes": {"orchestration", "devops", "distributed"},
    "react": {"frontend", "ui", "web"},
    "aws": {"cloud", "devops", "infrastructure"},
    "gcp": {"cloud", "devops", "infrastructure"},
}


class SkillMatcherService:
    """Advanced skill matching and ranking service"""

    def __init__(
        self,
        db: Session,
        weights: Optional[SkillWeights] = None,
        job_category: JobCategory = JobCategory.OTHER,
        experience_level: ExperienceLevel = ExperienceLevel.MID
    ):
        """Initialize skill matcher service"""
        self.db = db
        self.weights = weights or SkillWeights()
        self.job_category = job_category
        self.experience_level = experience_level
        logger.info(f"SkillMatcherService initialized: {job_category}, {experience_level}")

    def normalize_skill(self, skill: str) -> str:
        """
        Normalize skill name to canonical form.

        Args:
            skill: Raw skill name

        Returns:
            Normalized skill name
        """
        try:
            normalized = skill.lower().strip()
            return SKILL_NORMALIZATION.get(normalized, normalized)
        except Exception as e:
            logger.warning(f"Error normalizing skill '{skill}': {e}")
            return skill.lower().strip()

    def calculate_skill_similarity(self, skill1: str, skill2: str) -> float:
        """
        Calculate similarity between two skills (0-1).

        Args:
            skill1: First skill (normalized)
            skill2: Second skill (normalized)

        Returns:
            Similarity score 0-1
        """
        try:
            # Exact match
            if skill1 == skill2:
                return 1.0

            # Check if skills are in same similarity group
            for group_skill, group_set in SKILL_SIMILARITY_GROUPS.items():
                if skill1 == group_skill and skill2 in group_set:
                    return 0.7
                if skill2 == group_skill and skill1 in group_set:
                    return 0.7

            # Check for substring similarity
            if skill1 in skill2 or skill2 in skill1:
                return 0.5

            # No similarity
            return 0.0

        except Exception as e:
            logger.warning(f"Error calculating similarity: {e}")
            return 0.0

    def match_skills(
        self,
        candidate: Candidate,
        job: JobDescription
    ) -> SkillMatchResult:
        """
        Match candidate skills to job requirements.

        Args:
            candidate: Candidate object
            job: JobDescription object

        Returns:
            SkillMatchResult with detailed matching analysis
        """
        try:
            # Parse candidate skills
            candidate_skills = self._parse_skills(candidate)
            candidate_skills_normalized = {self.normalize_skill(s) for s in candidate_skills}

            # Parse job required and preferred skills
            required_skills = self._parse_skills_from_string(job.required_skills)
            preferred_skills = self._parse_skills_from_string(job.nice_to_have_skills)

            required_normalized = {self.normalize_skill(s) for s in required_skills}
            preferred_normalized = {self.normalize_skill(s) for s in preferred_skills}

            # Find matches
            exact_matches = []
            related_matches = []
            missing_required = []
            missing_preferred = []

            # Check required skills
            for req_skill in required_normalized:
                if req_skill in candidate_skills_normalized:
                    # Exact match
                    exact_matches.append(SkillMatch(
                        skill_name=req_skill,
                        candidate_has=True,
                        is_exact_match=True,
                        is_related_match=False,
                        importance="high",
                        score=100.0
                    ))
                else:
                    # Check for related skills
                    related_score = self._find_related_skill(req_skill, candidate_skills_normalized)
                    if related_score > 0.5:
                        related_matches.append(SkillMatch(
                            skill_name=req_skill,
                            candidate_has=True,
                            is_exact_match=False,
                            is_related_match=True,
                            importance="high",
                            score=related_score * 100
                        ))
                    else:
                        missing_required.append(SkillMatch(
                            skill_name=req_skill,
                            candidate_has=False,
                            is_exact_match=False,
                            is_related_match=False,
                            importance="high",
                            score=0.0
                        ))

            # Check preferred skills
            for pref_skill in preferred_normalized:
                if pref_skill in candidate_skills_normalized:
                    exact_matches.append(SkillMatch(
                        skill_name=pref_skill,
                        candidate_has=True,
                        is_exact_match=True,
                        is_related_match=False,
                        importance="medium",
                        score=100.0
                    ))
                else:
                    related_score = self._find_related_skill(pref_skill, candidate_skills_normalized)
                    if related_score > 0.5:
                        related_matches.append(SkillMatch(
                            skill_name=pref_skill,
                            candidate_has=True,
                            is_exact_match=False,
                            is_related_match=True,
                            importance="medium",
                            score=related_score * 100
                        ))
                    else:
                        missing_preferred.append(SkillMatch(
                            skill_name=pref_skill,
                            candidate_has=False,
                            is_exact_match=False,
                            is_related_match=False,
                            importance="medium",
                            score=0.0
                        ))

            # Calculate overall skills match score
            skills_match_score = self._calculate_overall_score(
                exact_matches, related_matches, missing_required, missing_preferred
            )

            # Build gap analysis
            gap_analysis = {
                "exact_match_count": len(exact_matches),
                "related_match_count": len(related_matches),
                "missing_required_count": len(missing_required),
                "missing_preferred_count": len(missing_preferred),
                "total_required": len(required_normalized),
                "total_preferred": len(preferred_normalized),
                "coverage": f"{(len(exact_matches) / (len(required_normalized) + len(preferred_normalized)) * 100):.1f}%"
                    if (len(required_normalized) + len(preferred_normalized)) > 0 else "0%"
            }

            return SkillMatchResult(
                exact_matches=exact_matches,
                related_matches=related_matches,
                missing_required=missing_required,
                missing_preferred=missing_preferred,
                skills_match_score=skills_match_score,
                gap_analysis=gap_analysis
            )

        except Exception as e:
            logger.error(f"Error matching skills: {e}")
            return SkillMatchResult(
                exact_matches=[],
                related_matches=[],
                missing_required=[],
                missing_preferred=[],
                skills_match_score=0.0,
                gap_analysis={"error": str(e)}
            )

    def _parse_skills(self, candidate: Candidate) -> List[str]:
        """Parse candidate skills from multiple sources"""
        skills = []

        # From skills field
        if candidate.skills:
            if isinstance(candidate.skills, str):
                skills.extend([s.strip() for s in candidate.skills.split(",")])
            elif isinstance(candidate.skills, list):
                skills.extend([str(s).strip() for s in candidate.skills])

        # From profile_json
        if candidate.profile_json and isinstance(candidate.profile_json, dict):
            profile_skills = candidate.profile_json.get("technical_skills", [])
            if isinstance(profile_skills, list):
                skills.extend([str(s).strip() for s in profile_skills])

        return skills

    def _parse_skills_from_string(self, skills_str: Optional[str]) -> List[str]:
        """Parse skills from comma-separated string"""
        if not skills_str:
            return []

        if isinstance(skills_str, str):
            return [s.strip() for s in skills_str.split(",") if s.strip()]
        elif isinstance(skills_str, list):
            return [str(s).strip() for s in skills_str]

        return []

    def _find_related_skill(self, required_skill: str, candidate_skills: Set[str]) -> float:
        """Find best related skill match for required skill"""
        best_score = 0.0

        for cand_skill in candidate_skills:
            score = self.calculate_skill_similarity(required_skill, cand_skill)
            if score > best_score:
                best_score = score

        return best_score

    def _calculate_overall_score(
        self,
        exact_matches: List[SkillMatch],
        related_matches: List[SkillMatch],
        missing_required: List[SkillMatch],
        missing_preferred: List[SkillMatch]
    ) -> float:
        """Calculate overall skills match score (0-100)"""
        try:
            score = 50.0  # Base score

            # Add points for exact matches
            score += len(exact_matches) * self.weights.exact_match_weight * 5.0

            # Add points for related matches
            score += len(related_matches) * self.weights.related_match_weight * 3.0

            # Subtract for missing required skills
            score += len(missing_required) * self.weights.missing_required_penalty * 10.0

            # Subtract for missing preferred skills
            score += len(missing_preferred) * self.weights.missing_preferred_penalty * 3.0

            # Ensure score stays within 0-100
            return max(0.0, min(100.0, score))

        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 50.0

    def get_top_candidates_by_skills(
        self,
        job_id: str,
        limit: int = 10,
        min_score: float = 0.6
    ) -> List[Dict]:
        """
        Get top candidates ranked by skill match for a specific job.

        Args:
            job_id: Job ID
            limit: Maximum results
            min_score: Minimum score threshold (0-1)

        Returns:
            List of candidates with skill match details
        """
        try:
            import uuid as uuid_module

            # Convert string to UUID if needed
            if isinstance(job_id, str):
                try:
                    job_id = uuid_module.UUID(job_id)
                except:
                    pass

            job = self.db.query(JobDescription).filter(
                JobDescription.id == job_id
            ).first()

            if not job:
                logger.warning(f"Job {job_id} not found")
                return []

            candidates = self.db.query(Candidate).all()
            rankings = []

            for candidate in candidates:
                match_result = self.match_skills(candidate, job)
                normalized_score = match_result.skills_match_score / 100.0

                if normalized_score >= min_score:
                    rankings.append({
                        "candidate_id": str(candidate.id),
                        "name": candidate.full_name,
                        "email": candidate.email,
                        "score": round(normalized_score, 3),
                        "exact_matches": len(match_result.exact_matches),
                        "related_matches": len(match_result.related_matches),
                        "missing_required": len(match_result.missing_required),
                        "gap_analysis": match_result.gap_analysis
                    })

            # Sort by score descending
            rankings.sort(key=lambda x: x["score"], reverse=True)

            return rankings[:limit]

        except Exception as e:
            logger.error(f"Error getting top candidates: {e}")
            return []

    def update_weights(self, new_weights: SkillWeights) -> None:
        """Update scoring weights at runtime"""
        try:
            self.weights = new_weights
            logger.info(f"Skill weights updated: {new_weights.to_dict()}")
        except Exception as e:
            logger.error(f"Error updating weights: {e}")

    def get_current_weights(self) -> Dict[str, float]:
        """Get current weights configuration"""
        return self.weights.to_dict()
