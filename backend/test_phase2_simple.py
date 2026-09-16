"""Phase 2: Simplified End-to-End Testing"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def run_tests():
    """Run Phase 2 tests"""
    print("\n" + "="*70)
    print("PHASE 2: END-TO-END TESTING")
    print("="*70)
    print(f"Target: {BASE_URL}\n")

    results = {"passed": 0, "failed": 0}

    async with httpx.AsyncClient(timeout=30) as client:
        # Test 1: Health Check
        print("[TEST 1] Health Check")
        try:
            resp = await client.get(f"{BASE_URL}/health")
            if resp.status_code == 200:
                print("  [OK] Health check passed\n")
                results["passed"] += 1
            else:
                print(f"  [FAIL] Status {resp.status_code}\n")
                results["failed"] += 1
        except Exception as e:
            print(f"  [FAIL] {str(e)}\n")
            results["failed"] += 1

        # Test 2: Login with seed user
        print("[TEST 2] Authentication (Seed User Login)")
        access_token = None
        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={
                    "email": "recruiter1@example.com",
                    "password": "password123",
                }
            )

            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and "access_token" in data["data"]:
                    access_token = data["data"]["access_token"]
                    print(f"  [OK] Login successful")
                    print(f"       Token: {access_token[:50]}...")
                    print(f"       User: recruiter1@example.com\n")
                    results["passed"] += 1
                else:
                    print(f"  [FAIL] No token in response\n")
                    results["failed"] += 1
            else:
                print(f"  [FAIL] Status {resp.status_code}")
                print(f"         Response: {resp.text}\n")
                results["failed"] += 1
        except Exception as e:
            print(f"  [FAIL] {str(e)}\n")
            results["failed"] += 1

        # Test 3: Get Candidates (if authenticated)
        if access_token:
            print("[TEST 3] Get Candidates List")
            try:
                headers = {"Authorization": f"bearer {access_token}"}
                resp = await client.get(
                    f"{BASE_URL}/api/v1/candidates/candidates",
                    headers=headers
                )

                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("data", [])
                    print(f"  [OK] Retrieved {len(candidates)} candidates\n")
                    results["passed"] += 1
                else:
                    print(f"  [FAIL] Status {resp.status_code}\n")
                    results["failed"] += 1
            except Exception as e:
                print(f"  [FAIL] {str(e)}\n")
                results["failed"] += 1

            # Test 4: Get Jobs (if authenticated)
            print("[TEST 4] Get Jobs List")
            try:
                headers = {"Authorization": f"bearer {access_token}"}
                resp = await client.get(
                    f"{BASE_URL}/api/v1/jobs/jobs",
                    headers=headers
                )

                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("data", [])
                    print(f"  [OK] Retrieved {len(jobs)} jobs\n")
                    results["passed"] += 1
                else:
                    print(f"  [FAIL] Status {resp.status_code}\n")
                    results["failed"] += 1
            except Exception as e:
                print(f"  [FAIL] {str(e)}\n")
                results["failed"] += 1

    # Print Summary
    print("="*70)
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
        print("[OK] PHASE 2 TESTING COMPLETE - ALL TESTS PASSED\n")
    else:
        print(f"[WARN] {results['failed']} test(s) failed\n")


if __name__ == "__main__":
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    asyncio.run(run_tests())
