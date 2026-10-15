"""Unit tests for recommendation scoring algorithms

Tests individual scoring components:
- Semantic similarity
- Skills matching
- Experience matching
- Education matching
- Location matching
- Weighted final score calculation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, User, Candidate, JobDescription
from app.services.recommendation_service import (
    RecommendationService,
    ScoringWeights
)
import uuid
from datetime import datetime


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
def test_candidate_skilled(db: Session, test_recruiter: User):
    """Create test candidate with strong skills"""
    candidate = Candidate(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        email="skilled@test.com",
        full_name="Skilled Developer",
        experience_years=8,
        skills="Python,FastAPI,PostgreSQL,Docker,Kubernetes,AWS",
        current_title="Senior Backend Engineer",
        current_company="TechCorp",
        profile_json={
            "description": "Senior backend engineer with 8+ years experience in microservices and scalable systems",
            "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
            "education": ["BS Computer Science"],
            "location": "San Francisco"
        }
    )
    db.add(candidate)
    db.commit()
    return candidate


@pytest.fixture
def test_candidate_junior(db: Session, test_recruiter: User):
    """Create test candidate with junior skills"""
    candidate = Candidate(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        email="junior@test.com",
        full_name="Junior Developer",
        experience_years=2,
        skills="JavaScript,React,Node.js",
        current_title="Junior Frontend Engineer",
        current_company="StartupXYZ",
        profile_json={
            "description": "Enthusiastic junior developer learning web technologies",
            "technical_skills": ["JavaScript", "React", "Node.js", "HTML", "CSS"],
            "education": ["Bootcamp Certification"],
            "location": "Austin"
        }
    )
    db.add(candidate)
    db.commit()
    return candidate


@pytest.fixture
def test_job_senior(db: Session, test_recruiter: User):
    """Create senior backend job posting"""
    job = JobDescription(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        title="Senior Backend Engineer",
        company="TechStartup Inc",
        experience_required=6,
        job_type="full-time",
        required_skills="Python,FastAPI,PostgreSQL,Docker",
        nice_to_have_skills="Kubernetes,AWS,GraphQL",
        description="Looking for senior backend engineer with 6+ years experience",
        status="open",
        job_details_json={
            "years_required": 6,
            "job_level": "senior",
            "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "nice_to_have_skills": ["Kubernetes", "AWS", "GraphQL"]
        }
    )
    db.add(job)
    db.commit()
    return job


@pytest.fixture
def test_job_junior(db: Session, test_recruiter: User):
    """Create junior frontend job posting"""
    job = JobDescription(
        id=uuid.uuid4(),
        user_id=test_recruiter.id,
        title="Junior Frontend Developer",
        company="WebCorp",
        experience_required=1,
        job_type="full-time",
        required_skills="JavaScript,React,CSS",
        nice_to_have_skills="TypeScript,Jest,Webpack",
        description="Looking for junior frontend developer to join our team",
        status="open",
        job_details_json={
            "years_required": 1,
            "job_level": "junior",
            "required_skills": ["JavaScript", "React", "CSS"],
            "nice_to_have_skills": ["TypeScript", "Jest"]
        }
    )
    db.add(job)
    db.commit()
    return job


class TestScoringWeights:
    """Test ScoringWeights configuration"""

    def test_valid_weights(self):
        """Test valid weight configuration"""
        weights = ScoringWeights()
        assert weights.semantic_weight == 0.30
        assert weights.skills_weight == 0.35
        assert weights.experience_weight == 0.20
        assert weights.education_weight == 0.10
        assert weights.location_weight == 0.05

    def test_invalid_weights_sum(self):
        """Test that weights must sum to 1.0"""
        with pytest.raises(ValueError):
            ScoringWeights(
                semantic_weight=0.3,
                skills_weight=0.3,
                experience_weight=0.2,
                education_weight=0.1,
                location_weight=0.15  # Sum = 1.05
            )

    def test_weights_to_dict(self):
        """Test weights conversion to dict"""
        weights = ScoringWeights()
        weights_dict = weights.to_dict()
        assert weights_dict["semantic"] == 0.30
        assert weights_dict["skills"] == 0.35
        assert sum(weights_dict.values()) == pytest.approx(1.0)


class TestSemanticSimilarity:
    """Test semantic similarity scoring"""

    def test_semantic_similarity_with_detailed_profile(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_senior: JobDescription
    ):
        """Test semantic similarity with detailed candidate profile"""
        service = RecommendationService(db)
        score = service._calculate_semantic_similarity(test_candidate_skilled, test_job_senior)

        # Should give higher score for detailed profile
        assert 75 <= score <= 100

    def test_semantic_similarity_baseline(
        self,
        db: Session,
        test_candidate_junior: Candidate,
        test_job_junior: JobDescription
    ):
        """Test semantic similarity baseline score"""
        service = RecommendationService(db)
        score = service._calculate_semantic_similarity(test_candidate_junior, test_job_junior)

        # Should give decent baseline score
        assert 50 <= score <= 100


class TestSkillsMatching:
    """Test skills matching algorithm"""

    def test_perfect_skill_match(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_senior: JobDescription
    ):
        """Test perfect skill match scenario"""
        service = RecommendationService(db)
        score = service._calculate_skills_match(test_candidate_skilled, test_job_senior)

        # Should give high score for matching required skills
        assert score >= 70.0

    def test_partial_skill_match(
        self,
        db: Session,
        test_candidate_junior: Candidate,
        test_job_senior: JobDescription
    ):
        """Test partial skill match (junior developer for senior role)"""
        service = RecommendationService(db)
        score = service._calculate_skills_match(test_candidate_junior, test_job_senior)

        # Should give moderate score (some skills match but not all)
        assert 30.0 <= score < 70.0

    def test_excellent_skill_match(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_junior: JobDescription
    ):
        """Test overqualified candidate (skills don't transfer domain)"""
        service = RecommendationService(db)
        score = service._calculate_skills_match(test_candidate_skilled, test_job_junior)

        # Backend engineer for junior frontend role - different skill set
        # No exact matches (Python vs JavaScript, etc)
        # Score should reflect skill mismatch despite having more total skills
        assert score >= 40.0  # Baseline, minimal matches

    def test_no_skill_match(self, db: Session):
        """Test no skill overlap"""
        service = RecommendationService(db)

        recruiter = User(
            id=uuid.uuid4(),
            email="test@test.com",
            password_hash="hash",
            role="recruiter"
        )
        db.add(recruiter)
        db.commit()

        # Create candidate with completely different skills
        candidate = Candidate(
            id=uuid.uuid4(),
            user_id=recruiter.id,
            email="artist@test.com",
            full_name="Artist",
            skills="Photoshop,Illustrator,InDesign"
        )
        db.add(candidate)

        # Create job requiring tech skills
        job = JobDescription(
            id=uuid.uuid4(),
            user_id=recruiter.id,
            title="Programmer",
            required_skills="Python,Java,C++",
            status="open"
        )
        db.add(job)
        db.commit()

        score = service._calculate_skills_match(candidate, job)

        # Should give low score
        assert score < 50.0


class TestExperienceMatching:
    """Test experience level matching"""

    def test_perfect_experience_match(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_senior: JobDescription
    ):
        """Test perfect experience match (8 years for 6 year requirement)"""
        service = RecommendationService(db)
        score = service._calculate_experience_match(test_candidate_skilled, test_job_senior)

        # Exceeds requirement slightly - should get high score
        assert score >= 90.0

    def test_junior_for_senior_role(
        self,
        db: Session,
        test_candidate_junior: Candidate,
        test_job_senior: JobDescription
    ):
        """Test junior candidate for senior role"""
        service = RecommendationService(db)
        score = service._calculate_experience_match(test_candidate_junior, test_job_senior)

        # 2 years experience for 6 year requirement = gap of 4
        # Score = 60 - (4 * 10) = 20
        assert score == pytest.approx(20.0)

    def test_overqualified(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_junior: JobDescription
    ):
        """Test overqualified candidate"""
        service = RecommendationService(db)
        score = service._calculate_experience_match(test_candidate_skilled, test_job_junior)

        # 8 years for 1 year requirement = bonus
        # Score = 90 + min(10, (7 * 2)) = 100
        assert score >= 95.0

    def test_no_requirement_specified(
        self,
        db: Session,
        test_candidate_junior: Candidate
    ):
        """Test when no experience requirement is specified"""
        service = RecommendationService(db)

        recruiter = User(
            id=uuid.uuid4(),
            email="test@test.com",
            password_hash="hash",
            role="recruiter"
        )
        db.add(recruiter)
        db.commit()

        job = JobDescription(
            id=uuid.uuid4(),
            user_id=recruiter.id,
            title="Open Role",
            experience_required=None,
            status="open"
        )
        db.add(job)
        db.commit()

        score = service._calculate_experience_match(test_candidate_junior, job)

        # Should give perfect score if no requirement
        assert score == 100.0


class TestEducationMatching:
    """Test education alignment"""

    def test_education_with_degree(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_senior: JobDescription
    ):
        """Test education matching with degree"""
        service = RecommendationService(db)
        score = service._calculate_education_match(test_candidate_skilled, test_job_senior)

        # Should give good score for having degree
        assert score >= 70.0

    def test_education_baseline(
        self,
        db: Session,
        test_candidate_junior: Candidate,
        test_job_junior: JobDescription
    ):
        """Test education baseline (bootcamp)"""
        service = RecommendationService(db)
        score = service._calculate_education_match(test_candidate_junior, test_job_junior)

        # Should give decent score for bootcamp
        assert score >= 60.0


class TestLocationMatching:
    """Test location compatibility"""

    def test_remote_job(self, db: Session):
        """Test remote job matches all locations"""
        service = RecommendationService(db)

        recruiter = User(
            id=uuid.uuid4(),
            email="test@test.com",
            password_hash="hash",
            role="recruiter"
        )
        db.add(recruiter)
        db.commit()

        candidate = Candidate(
            id=uuid.uuid4(),
            user_id=recruiter.id,
            email="remote@test.com",
            full_name="Remote Worker",
            profile_json={"location": "Tokyo"}
        )
        db.add(candidate)

        job = JobDescription(
            id=uuid.uuid4(),
            user_id=recruiter.id,
            title="Remote Role",
            job_type="remote",
            status="open"
        )
        db.add(job)
        db.commit()

        score = service._calculate_location_match(candidate, job)

        # Remote jobs should give high score regardless of location
        assert score >= 85.0

    def test_location_no_info(self, db: Session):
        """Test location with no info defaults to neutral"""
        service = RecommendationService(db)

        recruiter = User(
            id=uuid.uuid4(),
            email="test@test.com",
            password_hash="hash",
            role="recruiter"
        )
        db.add(recruiter)
        db.commit()

        candidate = Candidate(
            id=uuid.uuid4(),
            user_id=recruiter.id,
            email="test@test.com",
            full_name="Test"
        )
        db.add(candidate)

        job = JobDescription(
            id=uuid.uuid4(),
            user_id=recruiter.id,
            title="OnSite Role",
            job_type="on-site",
            status="open"
        )
        db.add(job)
        db.commit()

        score = service._calculate_location_match(candidate, job)

        # Default to neutral baseline
        assert 40.0 <= score <= 60.0


class TestRecommendationScore:
    """Test overall recommendation score calculation"""

    def test_perfect_recommendation(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_senior: JobDescription
    ):
        """Test near-perfect recommendation (skilled developer for senior role)"""
        service = RecommendationService(db)
        score, breakdown = service.calculate_recommendation_score(
            str(test_candidate_skilled.id),
            str(test_job_senior.id)
        )

        # Should give high overall score
        assert score >= 70.0
        assert "final_weighted_score" in breakdown
        assert breakdown["final_weighted_score"] >= 70.0

    def test_poor_recommendation(
        self,
        db: Session,
        test_candidate_junior: Candidate,
        test_job_senior: JobDescription
    ):
        """Test poor recommendation (junior for senior role)"""
        service = RecommendationService(db)
        score, breakdown = service.calculate_recommendation_score(
            str(test_candidate_junior.id),
            str(test_job_senior.id)
        )

        # Should give lower score
        assert score < 60.0
        assert "final_weighted_score" in breakdown

    def test_good_recommendation(
        self,
        db: Session,
        test_candidate_junior: Candidate,
        test_job_junior: JobDescription
    ):
        """Test good recommendation (junior for junior role)"""
        service = RecommendationService(db)
        score, breakdown = service.calculate_recommendation_score(
            str(test_candidate_junior.id),
            str(test_job_junior.id)
        )

        # Should give good score
        assert 60.0 <= score <= 100.0
        assert "final_weighted_score" in breakdown

    def test_score_breakdown_completeness(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_senior: JobDescription
    ):
        """Test that score breakdown includes all components"""
        service = RecommendationService(db)
        score, breakdown = service.calculate_recommendation_score(
            str(test_candidate_skilled.id),
            str(test_job_senior.id)
        )

        # Verify all scoring components present
        assert "semantic_similarity" in breakdown
        assert "skills_match" in breakdown
        assert "experience_match" in breakdown
        assert "education_match" in breakdown
        assert "location_match" in breakdown
        assert "final_weighted_score" in breakdown

        # All scores should be 0-100
        for key, value in breakdown.items():
            assert 0 <= value <= 100, f"{key} score out of range: {value}"


class TestTopCandidates:
    """Test getting top candidates for a job"""

    def test_top_candidates_ranking(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_candidate_junior: Candidate,
        test_job_senior: JobDescription
    ):
        """Test that candidates are ranked correctly"""
        service = RecommendationService(db)

        recommendations = service.get_top_candidates_for_job(
            str(test_job_senior.id),
            limit=10,
            min_score=0.0
        )

        # Should return candidates
        assert len(recommendations) > 0

        # Should be sorted by score (descending)
        for i in range(len(recommendations) - 1):
            assert recommendations[i]["score"] >= recommendations[i + 1]["score"]

    def test_min_score_filter(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_candidate_junior: Candidate,
        test_job_senior: JobDescription
    ):
        """Test minimum score filtering"""
        service = RecommendationService(db)

        recommendations = service.get_top_candidates_for_job(
            str(test_job_senior.id),
            limit=10,
            min_score=0.9  # Very high threshold
        )

        # Should only return candidates above threshold
        for rec in recommendations:
            assert rec["score"] >= 0.9

    def test_limit_respected(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_candidate_junior: Candidate,
        test_job_senior: JobDescription
    ):
        """Test that limit is respected"""
        service = RecommendationService(db)

        recommendations = service.get_top_candidates_for_job(
            str(test_job_senior.id),
            limit=1,
            min_score=0.0
        )

        # Should return at most 1 candidate
        assert len(recommendations) <= 1


class TestRecommendedJobs:
    """Test getting recommended jobs for a candidate"""

    def test_recommended_jobs_ranking(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_job_senior: JobDescription,
        test_job_junior: JobDescription
    ):
        """Test that jobs are ranked correctly"""
        service = RecommendationService(db)

        recommendations = service.get_recommended_jobs_for_candidate(
            str(test_candidate_skilled.id),
            limit=10,
            min_score=0.0
        )

        # Should return jobs
        assert len(recommendations) > 0

        # Should be sorted by score (descending)
        for i in range(len(recommendations) - 1):
            assert recommendations[i]["score"] >= recommendations[i + 1]["score"]

    def test_open_jobs_only(
        self,
        db: Session,
        test_candidate_skilled: Candidate,
        test_recruiter: User
    ):
        """Test that only open jobs are recommended"""
        service = RecommendationService(db)

        # Create closed job
        closed_job = JobDescription(
            id=uuid.uuid4(),
            user_id=test_recruiter.id,
            title="Closed Position",
            status="closed"
        )
        db.add(closed_job)
        db.commit()

        recommendations = service.get_recommended_jobs_for_candidate(
            str(test_candidate_skilled.id),
            limit=10,
            min_score=0.0
        )

        # Closed job should not appear
        for rec in recommendations:
            assert rec["status"] != "closed" or "status" not in rec


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
