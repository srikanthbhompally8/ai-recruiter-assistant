"""Populate SQLite database with representative test data."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import settings
from app.models.user import User
from app.models.candidate import Candidate
from app.models.job import JobDescription
from app.models.match import Match
import uuid
from datetime import datetime
import json
import hashlib

# Create session
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Test users
users = [
    User(id=uuid.uuid4(), email="recruiter1@example.com", password_hash=hashlib.sha256(b"password123").hexdigest(), full_name="John Recruiter", role="recruiter"),
    User(id=uuid.uuid4(), email="recruiter2@example.com", password_hash=hashlib.sha256(b"password123").hexdigest(), full_name="Jane Recruiter", role="recruiter"),
    User(id=uuid.uuid4(), email="admin@example.com", password_hash=hashlib.sha256(b"password123").hexdigest(), full_name="Admin User", role="admin"),
]
session.add_all(users)
session.commit()
print(f"[OK] Created {len(users)} test users")

# Test candidates
candidates = [
    Candidate(
        id=uuid.uuid4(),
        user_id=users[0].id,
        email="alice@example.com",
        full_name="Alice Johnson",
        phone="555-0001",
        current_company="TechCorp",
        current_title="Senior Python Engineer",
        experience_years=7,
        skills=json.dumps(["Python", "FastAPI", "PostgreSQL", "Docker"]),
    ),
    Candidate(
        id=uuid.uuid4(),
        user_id=users[0].id,
        email="bob@example.com",
        full_name="Bob Smith",
        phone="555-0002",
        current_company="DataSystems",
        current_title="Data Engineer",
        experience_years=5,
        skills=json.dumps(["Python", "Spark", "AWS", "SQL"]),
    ),
    Candidate(
        id=uuid.uuid4(),
        user_id=users[0].id,
        email="carol@example.com",
        full_name="Carol White",
        phone="555-0003",
        current_company="WebDev Inc",
        current_title="Frontend Developer",
        experience_years=4,
        skills=json.dumps(["React", "TypeScript", "JavaScript", "CSS"]),
    ),
]
session.add_all(candidates)
session.commit()
print(f"[OK] Created {len(candidates)} test candidates")

# Test jobs
jobs = [
    JobDescription(
        id=uuid.uuid4(),
        user_id=users[0].id,
        title="Senior Python Engineer",
        company="TechCorp",
        description="Looking for experienced Python developer for backend work. 5+ years required.",
        experience_required=5,
        required_skills=json.dumps(["Python", "FastAPI", "PostgreSQL"]),
        nice_to_have_skills=json.dumps(["Docker", "Kubernetes"]),
        job_details_json={"level": "senior"},
    ),
    JobDescription(
        id=uuid.uuid4(),
        user_id=users[0].id,
        title="Data Engineer",
        company="DataSystems",
        description="Build data pipelines and infrastructure. Experience with Spark and cloud platforms required.",
        experience_required=4,
        required_skills=json.dumps(["Python", "Spark", "AWS", "SQL"]),
        nice_to_have_skills=json.dumps(["Scala", "Kafka"]),
        job_details_json={"level": "mid"},
    ),
    JobDescription(
        id=uuid.uuid4(),
        user_id=users[0].id,
        title="Frontend Developer",
        company="WebDev Inc",
        description="React specialist for modern SPA development.",
        experience_required=3,
        required_skills=json.dumps(["React", "TypeScript", "JavaScript"]),
        nice_to_have_skills=json.dumps(["Next.js", "Tailwind"]),
        job_details_json={"level": "mid"},
    ),
]
session.add_all(jobs)
session.commit()
print(f"[OK] Created {len(jobs)} test job listings")

# Test matches
matches = [
    Match(
        id=uuid.uuid4(),
        candidate_id=candidates[0].id,
        job_id=jobs[0].id,
        skills_match=95.0,
        experience_match=100.0,
        overall_score=97.5,
        matched_skills=json.dumps(["Python", "FastAPI", "PostgreSQL"]),
        missing_skills=json.dumps([]),
        recommendation="Strong match - Excellent fit",
        status="active",
    ),
    Match(
        id=uuid.uuid4(),
        candidate_id=candidates[1].id,
        job_id=jobs[1].id,
        skills_match=92.0,
        experience_match=90.0,
        overall_score=91.0,
        matched_skills=json.dumps(["Python", "Spark", "AWS", "SQL"]),
        missing_skills=json.dumps([]),
        recommendation="Strong match - Good fit",
        status="active",
    ),
    Match(
        id=uuid.uuid4(),
        candidate_id=candidates[2].id,
        job_id=jobs[2].id,
        skills_match=98.0,
        experience_match=85.0,
        overall_score=91.5,
        matched_skills=json.dumps(["React", "TypeScript", "JavaScript"]),
        missing_skills=json.dumps([]),
        recommendation="Strong match - Exact skills match",
        status="active",
    ),
]
session.add_all(matches)
session.commit()
print(f"[OK] Created {len(matches)} test matches")

session.close()

session.close()

print("\n[OK] Database seeding complete!")
print(f"Test data summary:")
print(f"  - Users: {len(users)}")
print(f"  - Candidates: {len(candidates)}")
print(f"  - Job Descriptions: {len(jobs)}")
print(f"  - Matches: {len(matches)}")
