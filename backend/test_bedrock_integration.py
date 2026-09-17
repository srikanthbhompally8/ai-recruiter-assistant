"""Test Bedrock API Integration for Job Description Parsing"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.bedrock_service import bedrock_service
from datetime import datetime
import json

# Test job descriptions
TEST_JOB_DESCRIPTIONS = [
    {
        "name": "Senior Python Developer",
        "description": """
        We are looking for an experienced Senior Python Developer to join our backend team.

        Required Skills:
        - 7+ years of Python development experience
        - Expert-level knowledge of FastAPI or Django
        - Strong PostgreSQL and database design skills
        - AWS (EC2, RDS, S3) experience
        - Docker and Kubernetes proficiency
        - Git version control

        Nice to Have:
        - Machine Learning experience
        - Microservices architecture
        - DevOps background

        Responsibilities:
        - Design and implement scalable backend systems
        - Lead code reviews and mentor junior developers
        - Collaborate with product team on feature development
        - Optimize database performance

        Salary: $150,000 - $200,000
        Job Type: Full-time
        Location: Remote
        Level: Senior
        """
    },
    {
        "name": "Full Stack JavaScript Developer",
        "description": """
        Join our startup as a Full Stack JavaScript Developer!

        Technical Requirements:
        - 3+ years JavaScript/TypeScript experience
        - React.js or Vue.js frontend experience
        - Node.js backend development
        - MongoDB or PostgreSQL knowledge
        - Git and CI/CD pipelines

        Bonus Skills:
        - GraphQL experience
        - Docker containerization
        - AWS cloud services
        - Agile/Scrum methodology

        You will:
        - Build responsive web applications
        - Develop RESTful APIs
        - Participate in architecture decisions
        - Collaborate with design team

        Salary Range: $90,000 - $130,000
        Position Type: Full-time, Remote
        Level: Mid-level
        """
    },
    {
        "name": "Data Engineer",
        "description": """
        Data Engineering Role at Scale

        Core Requirements:
        - 5+ years data engineering experience
        - Proficiency in Python, Scala, or Java
        - Apache Spark expertise
        - Hadoop ecosystem knowledge
        - ETL/ELT pipeline development
        - AWS or GCP data services

        Preferred:
        - Kafka streaming experience
        - Data warehouse design (Snowflake/BigQuery)
        - SQL optimization
        - Cloud data platforms

        Responsibilities:
        - Design and build data pipelines
        - Optimize data processing
        - Implement data quality checks
        - Support analytics team

        Salary: $140,000 - $180,000
        Type: Full-time
        Level: Senior
        """
    }
]

def test_job_parsing():
    """Test job description parsing with Bedrock"""
    print("\n" + "="*70)
    print("BEDROCK API INTEGRATION TEST: JOB DESCRIPTION PARSING")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    results = {"passed": 0, "failed": 0}

    for job in TEST_JOB_DESCRIPTIONS:
        print(f"\n[TEST] Parsing: {job['name']}")
        print("-" * 70)

        try:
            result = bedrock_service.parse_job_description(job['description'])

            if result and result.get("status") == "success":
                parsed = result.get("data", {})
                print(f"  [OK] Parsing successful")
                print(f"\n  Extracted Data:")
                print(f"    Job Title: {parsed.get('job_title', 'N/A')}")
                print(f"    Company: {parsed.get('company', 'N/A')}")
                print(f"    Years Required: {parsed.get('years_required', 'N/A')}")
                print(f"    Job Type: {parsed.get('job_type', 'N/A')}")
                print(f"    Level: {parsed.get('job_level', 'N/A')}")
                print(f"    Required Skills: {', '.join(parsed.get('required_skills', [])[:3])}")
                print(f"    Nice-to-Have: {', '.join(parsed.get('nice_to_have_skills', [])[:2])}")

                results["passed"] += 1
            else:
                print(f"  [FAIL] Parsing failed")
                print(f"  Error: {result.get('message', 'Unknown error')}")
                results["failed"] += 1
        except Exception as e:
            print(f"  [FAIL] Exception: {str(e)}")
            results["failed"] += 1

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0

    print(f"Total Tests: {total}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print("="*70 + "\n")

    if results["failed"] == 0:
        print("[OK] BEDROCK INTEGRATION TESTS PASSED\n")
    else:
        print(f"[WARN] {results['failed']} test(s) failed\n")

    return results["passed"], results["failed"]


def test_skill_extraction():
    """Test skill extraction from text"""
    print("\n" + "="*70)
    print("BEDROCK API INTEGRATION TEST: SKILL EXTRACTION")
    print("="*70 + "\n")

    test_text = """
    I have 8 years of Python development experience with expertise in FastAPI and Django.
    I'm proficient in PostgreSQL, MongoDB, and Redis. Strong AWS knowledge including EC2, RDS, and S3.
    Experience with Docker, Kubernetes, and Terraform for infrastructure.
    Soft skills: Leadership, mentoring, excellent communication, problem-solving.
    """

    print("[TEST] Extracting skills from candidate profile")
    print("-" * 70)

    try:
        result = bedrock_service.extract_skills(test_text)

        if result and result.get("status") == "success":
            skills = result.get("data", {})
            print(f"  [OK] Skills extraction successful\n")
            print(f"  Technical Skills: {', '.join(skills.get('technical_skills', []))}")
            print(f"  Soft Skills: {', '.join(skills.get('soft_skills', []))}")
            print(f"\n  Proficiency Levels:")
            for skill, level in skills.get('proficiency_levels', {}).items():
                print(f"    - {skill}: {level}")
            return 1, 0
        else:
            print(f"  [FAIL] Extraction failed: {result.get('message', 'Unknown error')}")
            return 0, 1
    except Exception as e:
        print(f"  [FAIL] Exception: {str(e)}")
        return 0, 1


if __name__ == "__main__":
    print(f"\n{'='*70}")
    print("BEDROCK SERVICE VERIFICATION")
    print(f"{'='*70}")

    # Run tests
    job_passed, job_failed = test_job_parsing()
    skill_passed, skill_failed = test_skill_extraction()

    # Final summary
    total_passed = job_passed + skill_passed
    total_failed = job_failed + skill_failed

    print(f"\n{'='*70}")
    print("OVERALL RESULTS")
    print(f"{'='*70}")
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")

    if total_failed == 0:
        print("\n[OK] ALL BEDROCK INTEGRATION TESTS PASSED\n")
        exit(0)
    else:
        print(f"\n[WARN] {total_failed} test(s) failed\n")
        exit(1)
