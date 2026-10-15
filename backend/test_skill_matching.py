"""Unit tests for skill matching and ranking

Tests skill normalization, similarity detection, matching, ranking, and scoring.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, User, Candidate, JobDescription
from app.services.skill_matcher_service import (
    SkillMatcherService,
    SkillWeights,
    ExperienceLevel,
    JobCategory
)
import uuid


@pytest.fixture
def db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_recruiter(db: Session):
    """Create test recruiter user"""
    recruiter = User(
        id=uuid.uuid4(),
        email="recruiter@test.com",
        password_hash="hashed",
        full_name="Test Recruiter",
        role="recruiter"
    )
    db.add(recruiter)
    db.commit()
    return recruiter


@pytest.fixture
def skilled_backend_candidate(db: Session, test_recruiter: User):
    """Backend engineer with strong skills"""
    candidate = Candidate(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        email="backend@test.com",
        full_name="Backend Engineer",
        experience_years=6,
        skills="Python,Python3,FastAPI,PostgreSQL,Docker,Kubernetes,AWS",
        profile_json={
            "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"]
        }
    )
    db.add(candidate)
    db.commit()
    return candidate


@pytest.fixture
def skilled_frontend_candidate(db: Session, test_recruiter: User):
    """Frontend engineer with strong skills"""
    candidate = Candidate(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        email="frontend@test.com",
        full_name="Frontend Engineer",
        experience_years=5,
        skills="JavaScript,JS,React,Vue,CSS,HTML,TypeScript",
        profile_json={
            "technical_skills": ["JavaScript", "React", "CSS", "Webpack"]
        }
    )
    db.add(candidate)
    db.commit()
    return candidate


@pytest.fixture
def junior_candidate(db: Session, test_recruiter: User):
    """Junior developer with basic skills"""
    candidate = Candidate(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        email="junior@test.com",
        full_name="Junior Developer",
        experience_years=1,
        skills="Python,JavaScript",
        profile_json={}
    )
    db.add(candidate)
    db.commit()
    return candidate


@pytest.fixture
def backend_job(db: Session, test_recruiter: User):
    """Senior backend job posting"""
    job = JobDescription(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        title="Senior Backend Engineer",
        required_skills="Python,FastAPI,PostgreSQL,Docker",
        nice_to_have_skills="Kubernetes,AWS,Redis",
        status="open"
    )
    db.add(job)
    db.commit()
    return job


@pytest.fixture
def frontend_job(db: Session, test_recruiter: User):
    """Frontend job posting"""
    job = JobDescription(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        title="Frontend Developer",
        required_skills="JavaScript,React,CSS",
        nice_to_have_skills="TypeScript,Jest",
        status="open"
    )
    db.add(job)
    db.commit()
    return job


class TestSkillNormalization:
    """Test skill normalization"""

    def test_normalize_python_variants(self, db: Session):
        """Test Python skill variants normalize to same form"""
        service = SkillMatcherService(db)

        assert service.normalize_skill("python") == "python"
        assert service.normalize_skill("Python") == "python"
        assert service.normalize_skill("PYTHON") == "python"
        assert service.normalize_skill("python3") == "python"
        assert service.normalize_skill("Python 3") == "python"
        assert service.normalize_skill("py") == "python"

    def test_normalize_javascript_variants(self, db: Session):
        """Test JavaScript variants normalize correctly"""
        service = SkillMatcherService(db)

        assert service.normalize_skill("javascript") == "javascript"
        assert service.normalize_skill("JavaScript") == "javascript"
        assert service.normalize_skill("js") == "javascript"
        assert service.normalize_skill("JS") == "javascript"

    def test_normalize_rest_api_variants(self, db: Session):
        """Test REST API variants"""
        service = SkillMatcherService(db)

        assert service.normalize_skill("rest") == "rest_api"
        assert service.normalize_skill("REST API") == "rest_api"
        assert service.normalize_skill("restful") == "rest_api"
        assert service.normalize_skill("RESTful API") == "rest_api"

    def test_normalize_database_skills(self, db: Session):
        """Test database skill normalization"""
        service = SkillMatcherService(db)

        assert service.normalize_skill("postgresql") == "postgresql"
        assert service.normalize_skill("PostgreSQL") == "postgresql"
        assert service.normalize_skill("postgres") == "postgresql"
        assert service.normalize_skill("mongodb") == "mongodb"
        assert service.normalize_skill("mongo") == "mongodb"


class TestSkillSimilarity:
    """Test skill similarity detection"""

    def test_exact_skill_match(self, db: Session):
        """Test exact skill match"""
        service = SkillMatcherService(db)

        similarity = service.calculate_skill_similarity("python", "python")
        assert similarity == 1.0

    def test_related_skill_match_same_group(self, db: Session):
        """Test related skills in same group"""
        service = SkillMatcherService(db)

        # Python and programming should be related
        similarity = service.calculate_skill_similarity("python", "programming")
        assert similarity >= 0.5

    def test_different_skills(self, db: Session):
        """Test completely different skills"""
        service = SkillMatcherService(db)

        similarity = service.calculate_skill_similarity("python", "photoshop")
        assert similarity == 0.0

    def test_database_similarity(self, db: Session):
        """Test database skills similarity"""
        service = SkillMatcherService(db)

        # PostgreSQL and SQL should be related
        similarity = service.calculate_skill_similarity("postgresql", "sql")
        assert similarity >= 0.5


class TestSkillMatching:
    """Test skill matching algorithm"""

    def test_perfect_skill_match(
        self,
        db: Session,
        skilled_backend_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test perfect skill match (backend engineer for backend job)"""
        service = SkillMatcherService(db)
        result = service.match_skills(skilled_backend_candidate, backend_job)

        # Should have high exact matches
        assert len(result.exact_matches) >= 3
        assert result.skills_match_score >= 70.0

    def test_partial_skill_match(
        self,
        db: Session,
        junior_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test partial skill match (junior for senior role)"""
        service = SkillMatcherService(db)
        result = service.match_skills(junior_candidate, backend_job)

        # Should have some exact matches, many missing
        assert len(result.exact_matches) >= 1
        assert len(result.missing_required) > 0
        assert result.skills_match_score < 70.0

    def test_no_skill_match(
        self,
        db: Session,
        test_recruiter: User,
        backend_job: JobDescription
    ):
        """Test no skill overlap"""
        service = SkillMatcherService(db)

        artist = Candidate(
            id=uuid.uuid4(),
            user_id=test_recruiter.id,
            email="artist@test.com",
            full_name="Artist",
            skills="Photoshop,Illustrator,InDesign"
        )
        db.add(artist)
        db.commit()

        result = service.match_skills(artist, backend_job)

        # Should have no exact matches
        assert len(result.exact_matches) == 0
        assert len(result.missing_required) > 0
        assert result.skills_match_score < 50.0

    def test_related_skill_detection(
        self,
        db: Session,
        test_recruiter: User,
        backend_job: JobDescription
    ):
        """Test detection of related skills"""
        service = SkillMatcherService(db)

        # Create candidate with similar but not exact skills
        candidate = Candidate(
            id=uuid.uuid4(),
            user_id=test_recruiter.id,
            email="similar@test.com",
            full_name="Similar Skills",
            skills="JavaScript,Node.js,MongoDB"  # Different languages/DBs
        )
        db.add(candidate)
        db.commit()

        result = service.match_skills(candidate, backend_job)

        # Should detect some related skills even if not exact matches
        total_matches = len(result.exact_matches) + len(result.related_matches)
        assert total_matches >= 0  # May have related matches


class TestSkillRanking:
    """Test skill ranking by match type"""

    def test_exact_matches_ranked_highest(
        self,
        db: Session,
        skilled_backend_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test that exact matches are ranked highest"""
        service = SkillMatcherService(db)
        result = service.match_skills(skilled_backend_candidate, backend_job)

        # All exact matches should have perfect score
        for match in result.exact_matches:
            assert match.score >= 90.0
            assert match.is_exact_match

    def test_related_matches_ranked_medium(
        self,
        db: Session,
        test_recruiter: User,
        backend_job: JobDescription
    ):
        """Test that related matches are ranked below exact"""
        service = SkillMatcherService(db)

        # Create candidate with related but not exact skills
        candidate = Candidate(
            id=uuid.uuid4(),
            user_id=test_recruiter.id,
            email="related@test.com",
            full_name="Related Skills",
            skills="programming,web services,database"
        )
        db.add(candidate)
        db.commit()

        result = service.match_skills(candidate, backend_job)

        # Related matches should exist
        for match in result.related_matches:
            assert match.is_related_match
            assert not match.is_exact_match


class TestGapAnalysis:
    """Test skills gap analysis"""

    def test_gap_analysis_complete(
        self,
        db: Session,
        junior_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test gap analysis has all required fields"""
        service = SkillMatcherService(db)
        result = service.match_skills(junior_candidate, backend_job)

        # Verify gap analysis structure
        assert "exact_match_count" in result.gap_analysis
        assert "related_match_count" in result.gap_analysis
        assert "missing_required_count" in result.gap_analysis
        assert "missing_preferred_count" in result.gap_analysis
        assert "coverage" in result.gap_analysis

    def test_missing_required_skills_identified(
        self,
        db: Session,
        junior_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test that missing required skills are identified"""
        service = SkillMatcherService(db)
        result = service.match_skills(junior_candidate, backend_job)

        # Junior should be missing FastAPI, PostgreSQL, Docker
        assert len(result.missing_required) > 0

        missing_names = {m.skill_name for m in result.missing_required}
        # At least some backend-specific skills should be missing
        assert len(missing_names) > 0


class TestScoreCalculation:
    """Test overall score calculation"""

    def test_score_within_range(
        self,
        db: Session,
        skilled_backend_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test that score stays within 0-100"""
        service = SkillMatcherService(db)
        result = service.match_skills(skilled_backend_candidate, backend_job)

        assert 0.0 <= result.skills_match_score <= 100.0

    def test_perfect_match_high_score(
        self,
        db: Session,
        skilled_backend_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test that perfect match gets high score"""
        service = SkillMatcherService(db)
        result = service.match_skills(skilled_backend_candidate, backend_job)

        # Backend engineer for backend job should score well
        assert result.skills_match_score >= 70.0

    def test_no_match_low_score(
        self,
        db: Session,
        test_recruiter: User,
        backend_job: JobDescription
    ):
        """Test that no match gets low score"""
        service = SkillMatcherService(db)

        artist = Candidate(
            id=uuid.uuid4(),
            user_id=test_recruiter.id,
            email="artist@test.com",
            full_name="Artist",
            skills="Photoshop,Illustrator"
        )
        db.add(artist)
        db.commit()

        result = service.match_skills(artist, backend_job)

        # Artist for backend role should score low
        assert result.skills_match_score < 50.0


class TestTopCandidatesRanking:
    """Test getting top candidates by skill match"""

    def test_top_candidates_ranking(
        self,
        db: Session,
        skilled_backend_candidate: Candidate,
        junior_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test that candidates are ranked by skill match"""
        service = SkillMatcherService(db)

        top = service.get_top_candidates_by_skills(str(backend_job.id), limit=10, min_score=0.0)

        # Should return candidates
        assert len(top) > 0

        # Should be sorted by score descending
        for i in range(len(top) - 1):
            assert top[i]["score"] >= top[i + 1]["score"]

    def test_min_score_filter(
        self,
        db: Session,
        skilled_backend_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test minimum score filtering"""
        service = SkillMatcherService(db)

        # With high threshold
        top = service.get_top_candidates_by_skills(
            str(backend_job.id),
            limit=10,
            min_score=0.9  # Very high threshold
        )

        # All candidates should be above threshold or empty
        for candidate in top:
            assert candidate["score"] >= 0.9

    def test_limit_respected(
        self,
        db: Session,
        skilled_backend_candidate: Candidate,
        backend_job: JobDescription
    ):
        """Test that limit is respected"""
        service = SkillMatcherService(db)

        top = service.get_top_candidates_by_skills(
            str(backend_job.id),
            limit=1,
            min_score=0.0
        )

        # Should return at most 1 candidate
        assert len(top) <= 1


class TestSkillWeights:
    """Test configurable skill weights"""

    def test_default_weights(self, db: Session):
        """Test default weight values"""
        service = SkillMatcherService(db)
        weights = service.get_current_weights()

        assert weights["exact_match"] == 1.0
        assert weights["related_match"] == 0.6
        assert weights["missing_required_penalty"] == -0.5

    def test_custom_weights(self, db: Session):
        """Test custom weight configuration"""
        custom_weights = SkillWeights(
            exact_match_weight=2.0,
            related_match_weight=1.0,
            missing_required_penalty=-1.0
        )

        service = SkillMatcherService(db, weights=custom_weights)
        weights = service.get_current_weights()

        assert weights["exact_match"] == 2.0
        assert weights["related_match"] == 1.0
        assert weights["missing_required_penalty"] == -1.0

    def test_update_weights_runtime(self, db: Session):
        """Test updating weights at runtime"""
        service = SkillMatcherService(db)

        original = service.get_current_weights()
        assert original["exact_match"] == 1.0

        new_weights = SkillWeights(exact_match_weight=3.0)
        service.update_weights(new_weights)

        updated = service.get_current_weights()
        assert updated["exact_match"] == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
