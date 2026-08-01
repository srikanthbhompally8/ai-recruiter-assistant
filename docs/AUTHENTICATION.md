# Authentication Guide

**Status:** ✅ Implemented  
**Date:** July 26, 2026  
**Framework:** FastAPI + JWT + bcrypt

---

## **Overview**

The AI Recruiter Assistant uses **JWT (JSON Web Tokens)** for stateless authentication with refresh token rotation.

---

## **Architecture**

```
User Request
    ↓
[Email + Password]
    ↓
Auth Service (bcrypt verification)
    ↓
JWT Token Generation (HS256)
    ↓
Access Token (30 min) + Refresh Token (7 days)
    ↓
[Protected Endpoints]
    ↓
Token Verification Middleware
    ↓
User Context Extracted
```

---

## **Components**

### **1. Auth Service** (`app/services/auth_service.py`)

**Methods:**

| Method | Purpose |
|--------|---------|
| `hash_password(password)` | Hash password with bcrypt |
| `verify_password(plain, hashed)` | Compare password with hash |
| `create_access_token(user_id, email)` | Generate 30-min access token |
| `create_refresh_token(user_id, email)` | Generate 7-day refresh token |
| `verify_token(token)` | Decode & validate JWT |
| `register_user(email, password, full_name)` | Create new user account |
| `authenticate_user(email, password)` | Login & return tokens |
| `refresh_access_token(refresh_token)` | Issue new access token |

### **2. Auth Schemas** (`app/schemas/auth.py`)

- `UserRegister` - Registration request
- `UserLogin` - Login request
- `UserResponse` - User data response
- `TokenResponse` - Token response
- `AuthResponse` - Complete auth response
- `RefreshTokenRequest` - Refresh token request

### **3. Auth Endpoints** (`app/api/auth.py`)

All endpoints at `/api/v1/auth/`

---

## **API Endpoints**

### **1. Register User**

**Endpoint:** `POST /api/v1/auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "recruiter"
  }
}
```

**Errors:**
- `400` - Email already registered
- `500` - Registration failed

---

### **2. Login User**

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "company_name": null,
      "role": "recruiter"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Errors:**
- `401` - Invalid email or password
- `500` - Login failed

---

### **3. Refresh Access Token**

**Endpoint:** `POST /api/v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

**Errors:**
- `401` - Invalid or expired refresh token
- `500` - Token refresh failed

---

### **4. Get Current User**

**Endpoint:** `GET /api/v1/auth/me`

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  }
}
```

**Errors:**
- `401` - Missing or invalid token
- `500` - Failed to get user info

---

## **JWT Token Structure**

### **Access Token Payload**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "type": "access",
  "exp": 1690000000,
  "iat": 1689997800
}
```

**Expiration:** 30 minutes

### **Refresh Token Payload**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "type": "refresh",
  "exp": 1690604800,
  "iat": 1690000000
}
```

**Expiration:** 7 days

---

## **Configuration**

In `.env`:

```bash
# JWT
JWT_SECRET=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## **Usage Examples**

### **cURL**

**Register:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

**Use Token:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Refresh Token:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

---

### **Python Requests**

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Register
response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
})
print(response.json())

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "john@example.com",
    "password": "SecurePass123!"
})
auth_data = response.json()["data"]
access_token = auth_data["access_token"]

# Use token
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(response.json())
```

---

### **JavaScript (Axios)**

```javascript
const axios = require('axios');

const BASE_URL = "http://localhost:8000/api/v1";

// Register
async function register() {
  const response = await axios.post(`${BASE_URL}/auth/register`, {
    email: "john@example.com",
    password: "SecurePass123!",
    full_name: "John Doe"
  });
  console.log(response.data);
}

// Login
async function login() {
  const response = await axios.post(`${BASE_URL}/auth/login`, {
    email: "john@example.com",
    password: "SecurePass123!"
  });
  return response.data.data;
}

// Use token
async function getCurrentUser(accessToken) {
  const response = await axios.get(`${BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` }
  });
  console.log(response.data);
}
```

---

## **Password Requirements**

Currently, there are **no strict requirements**. Recommended:
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, special characters

*To add password validation:*

```python
# In app/schemas/auth.py
from pydantic import Field, validator

class UserRegister(BaseModel):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

---

## **Token Refresh Flow**

```
1. User logs in
   ↓
2. Receives access_token (30 min) + refresh_token (7 days)
   ↓
3. Use access_token for API calls
   ↓
4. Access token expires after 30 minutes
   ↓
5. Send refresh_token to /auth/refresh endpoint
   ↓
6. Receive new access_token
   ↓
7. Continue using new access_token
   ↓
8. Refresh token expires after 7 days → Re-login required
```

---

## **Security Best Practices**

✅ **Implemented:**
- bcrypt password hashing (10 rounds)
- HS256 JWT algorithm
- Short-lived access tokens (30 min)
- Long-lived refresh tokens (7 days)
- Token type validation (access vs refresh)

⏳ **To Implement (Phase 2):**
- HTTPS only (in production)
- Secure cookie storage (HttpOnly, Secure flags)
- Rate limiting on auth endpoints
- Account lockout after N failed attempts
- Email verification for new accounts
- Password reset flow
- Two-factor authentication (2FA)
- Token blacklist/revocation
- Audit logging for auth events

---

## **Troubleshooting**

### **"Invalid token format"**
- Token must be in format: `Bearer eyJhbGc...`
- Check Authorization header spelling

### **"Token expired"**
- Use refresh_token to get new access_token
- Or re-login

### **"Invalid email or password"**
- Check email and password spelling
- Ensure user is registered

### **"Email already registered"**
- Use different email
- Or login with existing email

---

## **Testing**

### **Manual Testing (Postman/cURL)**

1. Register user
2. Login → Save tokens
3. Call protected endpoint with access_token
4. Wait 30 minutes (or manually expire token for testing)
5. Use refresh_token to get new access_token
6. Verify new token works

### **Unit Tests** (TODO - Day 4)

```python
def test_register_user():
    response = client.post("/api/v1/auth/register", json={...})
    assert response.status_code == 200

def test_login_user():
    response = client.post("/api/v1/auth/login", json={...})
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_invalid_password():
    response = client.post("/api/v1/auth/login", json={...})
    assert response.status_code == 401
```

---

## **Next Steps**

1. ✅ Implement RBAC (Role-Based Access Control)
2. ✅ Add auth middleware to protect endpoints
3. ✅ Implement password reset flow
4. ✅ Add email verification
5. ✅ Implement 2FA

---

**Generated:** July 26, 2026  
**Status:** ✅ Complete  
**Owner:** Srikanth Bhompally
