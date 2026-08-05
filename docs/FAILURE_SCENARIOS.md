# Failure Scenarios & Error Handling

**Status:** ✅ Documented  
**Date:** August 1, 2026  
**Coverage:** Authentication, RBAC, Data Validation

---

## **Authentication Failures**

### **1. Wrong Password**
```
User: john@example.com
Password: "WrongPassword"
Hash: bcrypt("CorrectPassword")

Result: ❌ REJECTED
Status: 401 Unauthorized
Message: "Invalid email or password"
```

---

### **2. Expired Token**
```
Token Created: 2026-07-31 10:00:00
Expiration: 30 minutes
Current Time: 2026-07-31 10:31:00

Result: ❌ REJECTED
Status: 401 Unauthorized
Message: "Invalid or expired token"
```

---

### **3. Malformed Token**
```
Token: "not.a.real.jwt"
Expected: "eyJhbGc...eyJz..."

Result: ❌ REJECTED
Status: 401 Unauthorized
Message: "Invalid token format"
```

---

### **4. Duplicate Email Registration**
```
Attempt 1: POST /register
  email: john@example.com
  password: Password123!
  
Result: ✅ SUCCESS - User created

Attempt 2: POST /register
  email: john@example.com (same)
  password: DifferentPass!
  
Result: ❌ REJECTED
Status: 400 Bad Request
Message: "Email already registered"
```

---

### **5. Non-existent User Login**
```
POST /login
email: ghost@example.com
password: SomePassword

Result: ❌ REJECTED
Status: 401 Unauthorized
Message: "Invalid email or password"
```

---

### **6. Inactive User Login**
```
User Status: is_active = false
Login Attempt:
email: inactive@example.com
password: CorrectPassword

Result: ❌ REJECTED
Status: 401 Unauthorized
Message: "Invalid email or password"
```

---

## **RBAC Failures**

### **1. Insufficient Permissions**
```
User Role: viewer
Endpoint: PUT /users/{id}/role (requires: admin)

Result: ❌ ACCESS DENIED
Status: 403 Forbidden
Message: "Access denied. Required roles: admin"
```

---

### **2. Cannot Demote Last Admin**
```
Current State:
- 1 admin user (last one)
- 5 recruiter users

Attempt: PUT /users/admin-id/role
New Role: recruiter

Result: ❌ REJECTED
Status: 400 Bad Request
Message: "Cannot demote the last admin user"
```

---

### **3. Cannot Disable Last Active Admin**
```
Current State:
- 1 active admin (last one)
- Other admins: disabled

Attempt: PUT /users/admin-id/status?is_active=false

Result: ❌ REJECTED
Status: 400 Bad Request
Message: "Cannot disable the last active admin"
```

---

### **4. Recruiter Cannot Manage Users**
```
User Role: recruiter
Endpoint: GET /users (requires: admin)

Result: ❌ ACCESS DENIED
Status: 403 Forbidden
Message: "Access denied. Required roles: admin"
```

---

## **Token Failures**

### **1. Wrong Secret**
```
Token signed with: secret_key_A
Verification with: secret_key_B

Result: ❌ INVALID
Status: 401 Unauthorized
Message: "Invalid or expired token"
```

---

### **2. Refresh Token as Access Token**
```
Token Type: refresh
Endpoint: GET /auth/me (requires: access token)

Result: ❌ REJECTED
Status: 401 Unauthorized
Message: "Invalid token type"
```

---

### **3. Access Token as Refresh Token**
```
Token Type: access
Endpoint: POST /auth/refresh (requires: refresh token)

Result: ❌ REJECTED
Status: 401 Unauthorized
Message: "Invalid refresh token"
```

---

## **Data Validation Failures**

### **1. Invalid Email Format**
```
POST /auth/register
email: "notanemail"
password: "Password123!"

Result: ❌ REJECTED
Status: 422 Unprocessable Entity
Message: "Invalid email format"
```

---

### **2. Invalid Role Update**
```
PUT /users/{id}/role
role: "superadmin" (invalid)

Valid roles: admin, recruiter, viewer

Result: ❌ REJECTED
Status: 400 Bad Request
Message: "Invalid role. Must be one of: admin, recruiter, viewer"
```

---

### **3. Missing Required Fields**
```
POST /auth/register
(missing email field)
password: "Password123!"

Result: ❌ REJECTED
Status: 422 Unprocessable Entity
Message: "Field required: email"
```

---

### **4. Missing Authorization Header**
```
GET /auth/me
(no Authorization header)

Result: ❌ REJECTED
Status: 401 Unauthorized
Message: "Missing authorization header"
```

---

## **Concurrency Failures**

### **1. Simultaneous Registration of Same Email**
```
Request 1: POST /register
  email: duplicate@example.com
  
Request 2: POST /register
  email: duplicate@example.com
  (simultaneous)

Result:
- Request 1: ✅ SUCCESS
- Request 2: ❌ REJECTED (400 - Email already registered)
```

---

### **2. Concurrent Role Updates**
```
Admin 1: PUT /users/{id}/role to "admin"
Admin 2: PUT /users/{id}/role to "recruiter"
(concurrent)

Result: Database constraint enforces consistency
One succeeds, other sees updated state
```

---

## **Edge Cases**

### **1. Very Long Password**
```
Password: "a" * 10000 characters

Result: ✅ ACCEPTED (bcrypt handles)
Hash: Successfully created
Verify: Works correctly
```

---

### **2. Special Characters in Password**
```
Password: "P@ssw0rd!#$%^&*()"

Result: ✅ ACCEPTED
Hash: Hashed correctly
Verify: Exact match required
```

---

### **3. Empty Password**
```
Password: ""

Result: ✅ ACCEPTED (no minimum check yet)
Should be: ❌ REJECTED (future enhancement)
```

---

### **4. Null User in Database**
```
POST /auth/me
User ID: "invalid-uuid-not-in-db"

Result: ❌ REJECTED
Status: 404 Not Found
Message: "User not found"
```

---

## **Error Response Format**

All errors follow standard HTTP status codes:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

### **Common Status Codes**

| Code | Scenario |
|------|----------|
| **400** | Bad Request (invalid input, duplicate email) |
| **401** | Unauthorized (invalid credentials, expired token) |
| **403** | Forbidden (insufficient permissions) |
| **404** | Not Found (user, resource not found) |
| **422** | Unprocessable Entity (validation error) |
| **500** | Server Error (unexpected error) |

---

## **Security Implications**

✅ **Implemented:**
- Password never logged (hashed)
- Token verification strict (type + expiration)
- Role enforcement cannot be bypassed
- Admin protection prevents lockout
- Error messages don't reveal user existence

⚠️ **Considerations:**
- Timing attacks possible on password verification
- Rate limiting needed (future)
- Account lockout after N failures (future)
- Audit all admin actions (logged)

---

## **Testing Checklist**

- ✅ Wrong password rejection
- ✅ Expired token rejection
- ✅ Invalid token format rejection
- ✅ Duplicate email prevention
- ✅ Non-existent user handling
- ✅ Inactive user rejection
- ✅ Insufficient permissions (403)
- ✅ Last admin protection
- ✅ Invalid role rejection
- ✅ Missing headers
- ✅ Concurrent registration handling

---

**Status:** ✅ Complete

**Test File:** `backend/tests/test_auth_failures.py`

