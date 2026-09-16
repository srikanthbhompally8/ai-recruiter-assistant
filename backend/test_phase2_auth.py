"""Phase 2 Step 1: Authentication End-to-End Testing"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test credentials
TEST_USER = {
    "email": f"phase2test_{datetime.now().timestamp()}@example.com",
    "password": "Test123",
    "full_name": "Phase 2 Test User",
}

async def test_auth_flow():
    """Test complete authentication flow"""
    print("\n" + "="*70)
    print("PHASE 2 STEP 1: AUTHENTICATION TESTING")
    print("="*70)

    async with httpx.AsyncClient(timeout=30) as client:
        # Test 1: Register new user
        print("\n[TEST 1] User Registration")
        print(f"  Registering: {TEST_USER['email']}")

        try:
            register_response = await client.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"],
                    "full_name": TEST_USER["full_name"],
                }
            )

            if register_response.status_code == 200:
                register_data = register_response.json()
                print(f"  [OK] Registration successful")
                print(f"       Response: {register_data}")
                user_id = register_data.get("id") or register_data.get("user_id")
            elif register_response.status_code == 400:
                print(f"  [WARN] User already exists (expected on rerun)")
                print(f"         Response: {register_response.json()}")
                user_id = None
            else:
                print(f"  [FAIL] Registration failed: {register_response.status_code}")
                print(f"         Response: {register_response.text}")
                return False
        except Exception as e:
            print(f"  [FAIL] Registration error: {str(e)}")
            return False

        # Test 2: Login
        print("\n[TEST 2] User Login (JWT Token)")
        print(f"  Logging in: {TEST_USER['email']}")

        try:
            login_response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"],
                }
            )

            if login_response.status_code == 200:
                login_data = login_response.json()
                access_token = login_data.get("access_token")
                token_type = login_data.get("token_type")

                if access_token and token_type:
                    print(f"  [OK] Login successful")
                    print(f"       Token Type: {token_type}")
                    print(f"       Token Length: {len(access_token)} chars")
                else:
                    print(f"  [FAIL] Missing token in response")
                    print(f"         Response: {login_data}")
                    return False
            else:
                print(f"  [FAIL] Login failed: {login_response.status_code}")
                print(f"         Response: {login_response.text}")
                return False
        except Exception as e:
            print(f"  [FAIL] Login error: {str(e)}")
            return False

        # Test 3: Access protected endpoint with token
        print("\n[TEST 3] Protected Endpoint Access")
        print(f"  Accessing: /api/v1/auth/me (requires JWT token)")

        try:
            headers = {
                "Authorization": f"{token_type} {access_token}"
            }

            me_response = await client.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers=headers
            )

            if me_response.status_code == 200:
                me_data = me_response.json()
                print(f"  [OK] Protected endpoint accessible")
                print(f"       Email: {me_data.get('email')}")
                print(f"       Full Name: {me_data.get('full_name')}")
                print(f"       Role: {me_data.get('role')}")
            else:
                print(f"  [FAIL] Protected endpoint access failed: {me_response.status_code}")
                print(f"         Response: {me_response.text}")
                return False
        except Exception as e:
            print(f"  [FAIL] Protected endpoint error: {str(e)}")
            return False

        # Test 4: Invalid token rejection
        print("\n[TEST 4] Invalid Token Rejection")
        print(f"  Testing: Invalid token should be rejected")

        try:
            invalid_headers = {
                "Authorization": "Bearer invalid.token.here"
            }

            invalid_response = await client.get(
                f"{BASE_URL}/api/v1/auth/me",
                headers=invalid_headers
            )

            if invalid_response.status_code == 401:
                print(f"  [OK] Invalid token rejected correctly")
                print(f"       Status: {invalid_response.status_code} Unauthorized")
            else:
                print(f"  [FAIL] Invalid token not rejected: {invalid_response.status_code}")
                return False
        except Exception as e:
            print(f"  [FAIL] Invalid token test error: {str(e)}")
            return False

        # Test 5: Missing Authorization header
        print("\n[TEST 5] Missing Authorization Header")
        print(f"  Testing: Missing token should be rejected")

        try:
            no_auth_response = await client.get(
                f"{BASE_URL}/api/v1/auth/me"
            )

            if no_auth_response.status_code == 403:
                print(f"  [OK] Missing auth rejected correctly")
                print(f"       Status: {no_auth_response.status_code} Forbidden")
            else:
                print(f"  [FAIL] Missing auth not rejected: {no_auth_response.status_code}")
                return False
        except Exception as e:
            print(f"  [FAIL] Missing auth test error: {str(e)}")
            return False

    return True


async def main():
    """Run all authentication tests"""
    print("\n[INFO] Starting Phase 2 authentication tests...")
    print(f"[INFO] Target: {BASE_URL}")
    print(f"[INFO] Timestamp: {datetime.now().isoformat()}")

    try:
        success = await test_auth_flow()

        print("\n" + "="*70)
        if success:
            print("[OK] PHASE 2 STEP 1: ALL AUTHENTICATION TESTS PASSED")
        else:
            print("[FAIL] PHASE 2 STEP 1: SOME TESTS FAILED")
        print("="*70 + "\n")

        return success
    except Exception as e:
        print(f"\n[FAIL] Test execution error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
