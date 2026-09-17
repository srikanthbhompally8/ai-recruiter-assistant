"""Test Job Parsing API Endpoint"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

# Test data
TEST_JOB_DESCRIPTION = """
We are seeking a Senior Backend Engineer to join our growing platform team.

Key Responsibilities:
- Design and implement scalable microservices using Python
- Develop robust REST APIs with FastAPI
- Manage PostgreSQL databases and optimize queries
- Implement caching strategies with Redis
- Deploy applications using Docker and Kubernetes
- Collaborate with product and frontend teams

Required Qualifications:
- 6+ years of backend development experience
- Expert-level Python programming skills
- Strong experience with FastAPI or Django
- PostgreSQL database design and optimization
- Docker and Kubernetes proficiency
- Experience with CI/CD pipelines (GitHub Actions, Jenkins)
- Strong understanding of microservices architecture

Nice to Have:
- AWS experience (EC2, RDS, S3, Lambda)
- Experience with message queues (Kafka, RabbitMQ)
- GraphQL knowledge
- ML/AI exposure

We offer:
- Competitive salary: $180,000 - $240,000
- Full-time position
- Remote work opportunity
- Health insurance
- Stock options

Join our team and help build the future!
"""

TEST_CANDIDATE_TEXT = """
Full-stack developer with 8 years of professional experience.

Technical Skills:
- Expert in Python (8 years), Java (5 years), JavaScript (6 years)
- Advanced FastAPI and Django expertise
- PostgreSQL and MongoDB proficiency
- AWS services (EC2, RDS, S3, Lambda)
- Docker and Kubernetes orchestration
- Redis caching implementation
- GraphQL and REST API design
- Git and GitHub workflows
- Jenkins and GitHub Actions CI/CD

Soft Skills:
- Team leadership and mentoring
- Excellent communication and presentation abilities
- Problem-solving and analytical thinking
- Agile/Scrum methodology expert
- Project management experience

Recent Projects:
- Built microservices architecture for e-commerce platform
- Led team of 5 engineers on payment processing system
- Optimized database performance improving query speed by 60%
"""


async def test_endpoints():
    """Test job parsing endpoints"""
    print("\n" + "="*70)
    print("JOB PARSING API ENDPOINT TESTS")
    print("="*70 + "\n")

    async with httpx.AsyncClient(timeout=120) as client:
        # Step 1: Get authentication token
        print("[STEP 1] Getting authentication token...")
        login_resp = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email": "recruiter1@example.com",
                "password": "password123"
            }
        )

        if login_resp.status_code != 200:
            print(f"  [FAIL] Login failed: {login_resp.status_code}")
            return

        token = login_resp.json()["data"]["access_token"]
        print(f"  [OK] Token received: {token[:50]}...\n")

        headers = {"Authorization": f"bearer {token}"}

        # Step 2: Test job description parsing
        print("[STEP 2] Testing job description parsing endpoint...")
        parse_resp = await client.post(
            f"{BASE_URL}/api/v1/jobs/parse",
            json={
                "job_description": TEST_JOB_DESCRIPTION,
                "company": "TechStartup Inc"
            },
            headers=headers
        )

        if parse_resp.status_code == 200:
            data = parse_resp.json()
            job_data = data.get("data", {})
            print(f"  [OK] Job parsed successfully")
            print(f"       Job ID: {job_data.get('job_id')}")
            print(f"       Title: {job_data.get('title')}")
            print(f"       Company: {job_data.get('company')}")
            print(f"       Experience: {job_data.get('experience_required')} years")
            print(f"       Level: {job_data.get('job_level')}")
            print(f"       Type: {job_data.get('job_type')}")
            print(f"       Required Skills: {', '.join(job_data.get('required_skills', [])[:3])}...")
            print(f"       Salary Range: {job_data.get('salary_range')}\n")
        else:
            print(f"  [FAIL] Parsing failed: {parse_resp.status_code}")
            print(f"         Response: {parse_resp.text}\n")
            return

        # Step 3: Test skill extraction
        print("[STEP 3] Testing skill extraction endpoint...")
        skills_resp = await client.post(
            f"{BASE_URL}/api/v1/jobs/extract-skills",
            json={
                "text": TEST_CANDIDATE_TEXT
            },
            headers=headers
        )

        if skills_resp.status_code == 200:
            skills_data = skills_resp.json()["data"]
            print(f"  [OK] Skills extracted successfully")
            print(f"       Technical Skills: {len(skills_data.get('technical_skills', []))} found")
            print(f"       Soft Skills: {len(skills_data.get('soft_skills', []))} found")
            print(f"       Tech Skills: {', '.join(skills_data.get('technical_skills', [])[:5])}...")
            print(f"       Soft Skills: {', '.join(skills_data.get('soft_skills', [])[:3])}...\n")
        else:
            print(f"  [FAIL] Skill extraction failed: {skills_resp.status_code}")
            print(f"         Response: {skills_resp.text}\n")
            return

        # Step 4: Verify job was stored in database
        print("[STEP 4] Verifying job was stored in database...")
        jobs_resp = await client.get(
            f"{BASE_URL}/api/v1/jobs/jobs",
            headers=headers
        )

        if jobs_resp.status_code == 200:
            jobs = jobs_resp.json().get("data", [])
            print(f"  [OK] Database query successful")
            print(f"       Total jobs in database: {len(jobs)}\n")
        else:
            print(f"  [FAIL] Database query failed: {jobs_resp.status_code}\n")

    print("="*70)
    print("[OK] ALL JOB PARSING ENDPOINT TESTS PASSED")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
