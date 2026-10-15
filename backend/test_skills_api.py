"""Integration tests for Skills Matching, Ranking, and Gap Analysis APIs

Tests all three recruiter-facing API endpoints with:
- Authentication validation
- Authorization checks
- Valid requests
- Error handling
- Edge cases
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from app.models import Base, User, Candidate, JobDescription
from app.main import app
from app.database import get_db
from app.services.auth_service import auth_service
import uuid


@pytest.fixture(scope="function")
def db_session(tmp_path):
    """Create file-based SQLite database with all test data"""
    # Use a file-based database to avoid in-memory transaction issues
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionLocal()

    # Create recruiter
    recruiter_id = uuid.uuid4()
    recruiter = User(
        id=recruiter_id,
        email="recruiter@test.com",
        password_hash="$2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUm",
        full_name="Test Recruiter",
        role="recruiter",
        is_active=True
    )
    session.add(recruiter)
    session.commit()

    # Create backend candidate
    candidate_id = uuid.uuid4()
    backend_candidate = Candidate(
        id=candidate_id,
        user_id=recruiter_id,
        email="backend@test.com",
        full_name="Backend Engineer",
        experience_years=6,
        skills="Python,FastAPI,PostgreSQL,Docker,Kubernetes",
        current_title="Senior Backend Engineer",
        current_company="TechCorp"
    )
    session.add(backend_candidate)
    session.commit()

    # Create backend job
    job_id = uuid.uuid4()
    backend_job = JobDescription(
        id=job_id,
        user_id=recruiter_id,
        title="Senior Backend Engineer",
        company="TechStartup",
        required_skills="Python,FastAPI,PostgreSQL,Docker",
        nice_to_have_skills="Kubernetes,AWS,Redis",
        experience_required=6,
        status="open"
    )
    session.add(backend_job)
    session.commit()

    # Store references for tests
    session.recruiter = recruiter
    session.backend_candidate = backend_candidate
    session.backend_job = backend_job

    yield session
    session.close()


@pytest.fixture
def client(db_session):
    """Create test client with overridden database"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_token(db_session):
    """Generate JWT token for test recruiter"""
    token = auth_service.create_access_token(
        user_id=str(db_session.recruiter.id),
        email=db_session.recruiter.email
    )
    return token


@pytest.fixture
def backend_candidate(db_session):
    """Get backend candidate"""
    return db_session.backend_candidate


@pytest.fixture
def backend_job(db_session):
    """Get backend job"""
    return db_session.backend_job


class TestSkillsMatchEndpoint:
    """Test /api/v1/skills/match endpoint"""

    def test_match_authenticated_request(self, client, test_token, backend_candidate, backend_job):
        """Test skill matching with valid token"""
        response = client.post(
            "/api/v1/skills/match",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(backend_job.id)
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "skills_match_score" in data["data"]
        assert "exact_matches" in data["data"]
        assert "missing_required" in data["data"]

    def test_match_missing_auth(self, client, backend_candidate, backend_job):
        """Test skill matching without authentication"""
        response = client.post(
            "/api/v1/skills/match",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(backend_job.id)
            }
        )

        assert response.status_code == 403
        assert "Authorization header missing" in response.json()["detail"]

    def test_match_invalid_token(self, client, backend_candidate, backend_job):
        """Test skill matching with invalid token"""
        response = client.post(
            "/api/v1/skills/match",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(backend_job.id)
            },
            headers={"Authorization": "bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_match_missing_candidate_id(self, client, test_token, backend_job):
        """Test skill matching with missing candidate_id"""
        response = client.post(
            "/api/v1/skills/match",
            json={"job_id": str(backend_job.id)},
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 400
        assert "candidate_id" in response.json()["detail"]

    def test_match_missing_job_id(self, client, test_token, backend_candidate):
        """Test skill matching with missing job_id"""
        response = client.post(
            "/api/v1/skills/match",
            json={"candidate_id": str(backend_candidate.id)},
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 400
        assert "job_id" in response.json()["detail"]

    def test_match_invalid_uuid_format(self, client, test_token):
        """Test skill matching with invalid UUID"""
        response = client.post(
            "/api/v1/skills/match",
            json={
                "candidate_id": "not-a-uuid",
                "job_id": "also-not-uuid"
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 400
        assert "Invalid UUID" in response.json()["detail"]

    def test_match_candidate_not_found(self, client, test_token, backend_job):
        """Test skill matching with non-existent candidate"""
        response = client.post(
            "/api/v1/skills/match",
            json={
                "candidate_id": str(uuid.uuid4()),
                "job_id": str(backend_job.id)
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 404
        assert "Candidate not found" in response.json()["detail"]

    def test_match_job_not_found(self, client, test_token, backend_candidate):
        """Test skill matching with non-existent job"""
        response = client.post(
            "/api/v1/skills/match",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(uuid.uuid4())
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]


class TestSkillsRankEndpoint:
    """Test /api/v1/skills/rank endpoint"""

    def test_rank_authenticated_request(self, client, test_token, backend_job):
        """Test ranking with valid token"""
        response = client.post(
            "/api/v1/skills/rank",
            json={
                "job_id": str(backend_job.id),
                "limit": 10,
                "min_score": 0.5
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "candidates" in data["data"]
        assert "job_id" in data["data"]

    def test_rank_missing_auth(self, client, backend_job):
        """Test ranking without authentication"""
        response = client.post(
            "/api/v1/skills/rank",
            json={"job_id": str(backend_job.id)}
        )

        assert response.status_code == 403

    def test_rank_missing_job_id(self, client, test_token):
        """Test ranking with missing job_id"""
        response = client.post(
            "/api/v1/skills/rank",
            json={},
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 400
        assert "job_id" in response.json()["detail"]

    def test_rank_job_not_found(self, client, test_token):
        """Test ranking with non-existent job"""
        response = client.post(
            "/api/v1/skills/rank",
            json={"job_id": str(uuid.uuid4())},
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_rank_with_limit(self, client, test_token, backend_job):
        """Test ranking with custom limit"""
        response = client.post(
            "/api/v1/skills/rank",
            json={
                "job_id": str(backend_job.id),
                "limit": 5
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 200
        candidates = response.json()["data"]["candidates"]
        assert len(candidates) <= 5

    def test_rank_with_min_score(self, client, test_token, backend_job):
        """Test ranking with minimum score filter"""
        response = client.post(
            "/api/v1/skills/rank",
            json={
                "job_id": str(backend_job.id),
                "min_score": 0.9
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 200
        candidates = response.json()["data"]["candidates"]
        for candidate in candidates:
            assert candidate["skills_match_score"] >= 0.9


class TestSkillsGapsEndpoint:
    """Test /api/v1/skills/gaps endpoint"""

    def test_gaps_authenticated_request(self, client, test_token, backend_candidate, backend_job):
        """Test gap analysis with valid token"""
        response = client.post(
            "/api/v1/skills/gaps",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(backend_job.id)
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "critical_gaps" in data["data"]
        assert "optional_gaps" in data["data"]
        assert "learning_plan" in data["data"]

    def test_gaps_missing_auth(self, client, backend_candidate, backend_job):
        """Test gap analysis without authentication"""
        response = client.post(
            "/api/v1/skills/gaps",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(backend_job.id)
            }
        )

        assert response.status_code == 403

    def test_gaps_missing_candidate_id(self, client, test_token, backend_job):
        """Test gap analysis with missing candidate_id"""
        response = client.post(
            "/api/v1/skills/gaps",
            json={"job_id": str(backend_job.id)},
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 400

    def test_gaps_candidate_not_found(self, client, test_token, backend_job):
        """Test gap analysis with non-existent candidate"""
        response = client.post(
            "/api/v1/skills/gaps",
            json={
                "candidate_id": str(uuid.uuid4()),
                "job_id": str(backend_job.id)
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 404
        assert "Candidate not found" in response.json()["detail"]

    def test_gaps_includes_learning_plan(self, client, test_token, backend_candidate, backend_job):
        """Test that gap analysis includes learning plan"""
        response = client.post(
            "/api/v1/skills/gaps",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(backend_job.id)
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        assert response.status_code == 200
        learning_plan = response.json()["data"]["learning_plan"]
        assert "total_estimated_hours" in learning_plan
        assert "estimated_weeks" in learning_plan
        assert "recommendation" in learning_plan


class TestResponseFormats:
    """Test response format consistency"""

    def test_match_response_format(self, client, test_token, backend_candidate, backend_job):
        """Test that match response has correct structure"""
        response = client.post(
            "/api/v1/skills/match",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(backend_job.id)
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        data = response.json()["data"]
        assert "candidate_id" in data
        assert "job_id" in data
        assert "skills_match_score" in data
        assert isinstance(data["skills_match_score"], (int, float))
        assert 0 <= data["skills_match_score"] <= 1

    def test_rank_response_format(self, client, test_token, backend_job):
        """Test that rank response has correct structure"""
        response = client.post(
            "/api/v1/skills/rank",
            json={"job_id": str(backend_job.id)},
            headers={"Authorization": f"bearer {test_token}"}
        )

        data = response.json()["data"]
        assert "job_id" in data
        assert "candidates" in data
        assert isinstance(data["candidates"], list)

        if len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            assert "candidate_id" in candidate
            assert "name" in candidate
            assert "overall_score" in candidate

    def test_gaps_response_format(self, client, test_token, backend_candidate, backend_job):
        """Test that gaps response has correct structure"""
        response = client.post(
            "/api/v1/skills/gaps",
            json={
                "candidate_id": str(backend_candidate.id),
                "job_id": str(backend_job.id)
            },
            headers={"Authorization": f"bearer {test_token}"}
        )

        data = response.json()["data"]
        assert "critical_gaps" in data
        assert "optional_gaps" in data
        assert "learning_plan" in data
        assert isinstance(data["critical_gaps"], list)
        assert isinstance(data["optional_gaps"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
