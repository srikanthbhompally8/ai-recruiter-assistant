"""Performance benchmarking for Skills API endpoints

Measures:
- Average response time
- P95 response time
- P99 response time
- Min/Max response times
- Success rate
- Requests per second
"""

import asyncio
import time
import statistics
import json
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Candidate, JobDescription
from app.main import app
from app.database import get_db
from app.services.auth_service import auth_service
import uuid


def setup_test_database():
    """Create test database with test data"""
    import tempfile
    import os

    # Create temp directory for test DB
    temp_dir = tempfile.gettempdir()
    db_file = os.path.join(temp_dir, "perf_test.db")

    # Remove old DB if exists
    if os.path.exists(db_file):
        os.remove(db_file)

    # Create engine
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionLocal()

    # Create recruiter
    recruiter_id = uuid.uuid4()
    recruiter = User(
        id=recruiter_id,
        email="recruiter@perf.com",
        password_hash="$2b$12$R9h7cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUm",
        full_name="Perf Test Recruiter",
        role="recruiter",
        is_active=True
    )
    session.add(recruiter)
    session.commit()

    # Create candidates (10 for ranking tests)
    candidates = []
    for i in range(10):
        candidate = Candidate(
            id=uuid.uuid4(),
            user_id=recruiter_id,
            email=f"candidate{i}@perf.com",
            full_name=f"Candidate {i}",
            experience_years=3 + i,
            skills=f"Python,FastAPI,PostgreSQL,Docker,Kubernetes,AWS,{f'Skill{i}'}",
            current_title=f"Engineer {i}",
            current_company=f"Company {i}"
        )
        session.add(candidate)
        candidates.append(candidate)
    session.commit()

    # Create jobs (5 for testing)
    jobs = []
    for i in range(5):
        job = JobDescription(
            id=uuid.uuid4(),
            user_id=recruiter_id,
            title=f"Backend Engineer {i}",
            company=f"Startup {i}",
            required_skills="Python,FastAPI,PostgreSQL,Docker",
            nice_to_have_skills=f"Kubernetes,AWS,Redis,Skill{i}",
            experience_required=5,
            status="open"
        )
        session.add(job)
        jobs.append(job)
    session.commit()

    # Generate token
    token = auth_service.create_access_token(
        user_id=str(recruiter_id),
        email=recruiter.email
    )

    session.close()

    return {
        "recruiter_id": recruiter_id,
        "candidates": candidates,
        "jobs": jobs,
        "token": token
    }


def run_performance_test():
    """Run performance tests on all three endpoints"""

    print("\n" + "="*80)
    print("SKILLS API PERFORMANCE BENCHMARKING")
    print("="*80 + "\n")

    # Setup test data
    print("Setting up test database...")
    test_data = setup_test_database()

    # Override database dependency
    def override_get_db():
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        import tempfile
        import os

        temp_dir = tempfile.gettempdir()
        db_file = os.path.join(temp_dir, "perf_test.db")
        engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    results = {
        "timestamp": datetime.now().isoformat(),
        "endpoints": {}
    }

    # Test 1: /skills/match endpoint
    print("\n" + "-"*80)
    print("TEST 1: POST /api/v1/skills/match")
    print("-"*80)

    match_times = []
    match_success = 0
    match_errors = []

    num_requests = 50
    print(f"Running {num_requests} requests...")

    for i in range(num_requests):
        candidate = test_data["candidates"][i % len(test_data["candidates"])]
        job = test_data["jobs"][i % len(test_data["jobs"])]

        start = time.time()
        try:
            response = client.post(
                "/api/v1/skills/match",
                json={
                    "candidate_id": str(candidate.id),
                    "job_id": str(job.id)
                },
                headers={"Authorization": f"bearer {test_data['token']}"}
            )
            elapsed = (time.time() - start) * 1000  # Convert to ms
            match_times.append(elapsed)

            if response.status_code == 200:
                match_success += 1
            else:
                match_errors.append(f"Status {response.status_code}")
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            match_times.append(elapsed)
            match_errors.append(str(e))

    # Calculate statistics
    match_times.sort()
    match_stats = {
        "total_requests": num_requests,
        "successful": match_success,
        "success_rate": f"{(match_success/num_requests)*100:.1f}%",
        "response_times_ms": {
            "min": round(min(match_times), 2),
            "max": round(max(match_times), 2),
            "average": round(statistics.mean(match_times), 2),
            "median": round(statistics.median(match_times), 2),
            "p95": round(match_times[int(len(match_times) * 0.95)], 2),
            "p99": round(match_times[int(len(match_times) * 0.99)], 2),
        },
        "errors": match_errors if match_errors else "None"
    }

    results["endpoints"]["/skills/match"] = match_stats

    print(f"✅ Success Rate: {match_stats['success_rate']}")
    print(f"⏱️  Average: {match_stats['response_times_ms']['average']}ms")
    print(f"📊 P95: {match_stats['response_times_ms']['p95']}ms")
    print(f"📊 P99: {match_stats['response_times_ms']['p99']}ms")
    print(f"🔹 Min: {match_stats['response_times_ms']['min']}ms")
    print(f"🔸 Max: {match_stats['response_times_ms']['max']}ms")

    # Test 2: /skills/rank endpoint
    print("\n" + "-"*80)
    print("TEST 2: POST /api/v1/skills/rank")
    print("-"*80)

    rank_times = []
    rank_success = 0
    rank_errors = []

    print(f"Running {num_requests} requests...")

    for i in range(num_requests):
        job = test_data["jobs"][i % len(test_data["jobs"])]

        start = time.time()
        try:
            response = client.post(
                "/api/v1/skills/rank",
                json={
                    "job_id": str(job.id),
                    "limit": 10,
                    "min_score": 0.5
                },
                headers={"Authorization": f"bearer {test_data['token']}"}
            )
            elapsed = (time.time() - start) * 1000
            rank_times.append(elapsed)

            if response.status_code == 200:
                rank_success += 1
            else:
                rank_errors.append(f"Status {response.status_code}")
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            rank_times.append(elapsed)
            rank_errors.append(str(e))

    rank_times.sort()
    rank_stats = {
        "total_requests": num_requests,
        "successful": rank_success,
        "success_rate": f"{(rank_success/num_requests)*100:.1f}%",
        "response_times_ms": {
            "min": round(min(rank_times), 2),
            "max": round(max(rank_times), 2),
            "average": round(statistics.mean(rank_times), 2),
            "median": round(statistics.median(rank_times), 2),
            "p95": round(rank_times[int(len(rank_times) * 0.95)], 2),
            "p99": round(rank_times[int(len(rank_times) * 0.99)], 2),
        },
        "errors": rank_errors if rank_errors else "None"
    }

    results["endpoints"]["/skills/rank"] = rank_stats

    print(f"✅ Success Rate: {rank_stats['success_rate']}")
    print(f"⏱️  Average: {rank_stats['response_times_ms']['average']}ms")
    print(f"📊 P95: {rank_stats['response_times_ms']['p95']}ms")
    print(f"📊 P99: {rank_stats['response_times_ms']['p99']}ms")
    print(f"🔹 Min: {rank_stats['response_times_ms']['min']}ms")
    print(f"🔸 Max: {rank_stats['response_times_ms']['max']}ms")

    # Test 3: /skills/gaps endpoint
    print("\n" + "-"*80)
    print("TEST 3: POST /api/v1/skills/gaps")
    print("-"*80)

    gaps_times = []
    gaps_success = 0
    gaps_errors = []

    print(f"Running {num_requests} requests...")

    for i in range(num_requests):
        candidate = test_data["candidates"][i % len(test_data["candidates"])]
        job = test_data["jobs"][i % len(test_data["jobs"])]

        start = time.time()
        try:
            response = client.post(
                "/api/v1/skills/gaps",
                json={
                    "candidate_id": str(candidate.id),
                    "job_id": str(job.id)
                },
                headers={"Authorization": f"bearer {test_data['token']}"}
            )
            elapsed = (time.time() - start) * 1000
            gaps_times.append(elapsed)

            if response.status_code == 200:
                gaps_success += 1
            else:
                gaps_errors.append(f"Status {response.status_code}")
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            gaps_times.append(elapsed)
            gaps_errors.append(str(e))

    gaps_times.sort()
    gaps_stats = {
        "total_requests": num_requests,
        "successful": gaps_success,
        "success_rate": f"{(gaps_success/num_requests)*100:.1f}%",
        "response_times_ms": {
            "min": round(min(gaps_times), 2),
            "max": round(max(gaps_times), 2),
            "average": round(statistics.mean(gaps_times), 2),
            "median": round(statistics.median(gaps_times), 2),
            "p95": round(gaps_times[int(len(gaps_times) * 0.95)], 2),
            "p99": round(gaps_times[int(len(gaps_times) * 0.99)], 2),
        },
        "errors": gaps_errors if gaps_errors else "None"
    }

    results["endpoints"]["/skills/gaps"] = gaps_stats

    print(f"✅ Success Rate: {gaps_stats['success_rate']}")
    print(f"⏱️  Average: {gaps_stats['response_times_ms']['average']}ms")
    print(f"📊 P95: {gaps_stats['response_times_ms']['p95']}ms")
    print(f"📊 P99: {gaps_stats['response_times_ms']['p99']}ms")
    print(f"🔹 Min: {gaps_stats['response_times_ms']['min']}ms")
    print(f"🔸 Max: {gaps_stats['response_times_ms']['max']}ms")

    # Summary
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)

    all_times = match_times + rank_times + gaps_times
    total_requests = num_requests * 3
    total_success = match_success + rank_success + gaps_success

    print(f"\n📈 Total Requests: {total_requests}")
    print(f"✅ Total Success: {total_success} ({(total_success/total_requests)*100:.1f}%)")
    print(f"⏱️  Overall Average: {round(statistics.mean(all_times), 2)}ms")
    print(f"📊 Overall P95: {round(all_times[int(len(all_times) * 0.95)], 2)}ms")
    print(f"📊 Overall P99: {round(all_times[int(len(all_times) * 0.99)], 2)}ms")

    # Performance targets
    print("\n" + "-"*80)
    print("PERFORMANCE TARGETS VALIDATION")
    print("-"*80)

    target_avg = 500  # ms
    target_p95 = 750  # ms
    target_p99 = 1000  # ms

    overall_avg = round(statistics.mean(all_times), 2)
    overall_p95 = round(all_times[int(len(all_times) * 0.95)], 2)
    overall_p99 = round(all_times[int(len(all_times) * 0.99)], 2)

    print(f"Average Response Time: {overall_avg}ms (Target: <{target_avg}ms) {'✅' if overall_avg < target_avg else '⚠️'}")
    print(f"P95 Response Time: {overall_p95}ms (Target: <{target_p95}ms) {'✅' if overall_p95 < target_p95 else '⚠️'}")
    print(f"P99 Response Time: {overall_p99}ms (Target: <{target_p99}ms) {'✅' if overall_p99 < target_p99 else '⚠️'}")

    results["summary"] = {
        "total_requests": total_requests,
        "total_success": total_success,
        "success_rate": f"{(total_success/total_requests)*100:.1f}%",
        "overall_response_times_ms": {
            "average": overall_avg,
            "p95": overall_p95,
            "p99": overall_p99
        },
        "targets": {
            "average_ms": target_avg,
            "p95_ms": target_p95,
            "p99_ms": target_p99
        }
    }

    # Save results to file
    report_file = "performance_report_skills_api.json"
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Full report saved to: {report_file}")

    # Cleanup
    app.dependency_overrides.clear()

    return results


if __name__ == "__main__":
    run_performance_test()
