# Role-Based Access Control (RBAC)

**Status:** ✅ Implemented  
**Date:** August 1, 2026  
**Framework:** FastAPI Dependency Injection

---

## **Overview**

RBAC system provides role-based endpoint protection with three user roles:

- **Admin** - Full system access
- **Recruiter** - Manage candidates, jobs, matches
- **Viewer** - Read-only access

---

## **Roles & Permissions**

### **Admin**
```
✅ Create/read/update/delete users
✅ Manage user roles
✅ Create/read/update/delete candidates
✅ Create/read/update/delete jobs
✅ View all matches
✅ System configuration
```

### **Recruiter**
```
✅ Create/read/update/delete own candidates
✅ Create/read/update/delete own jobs
✅ View matches for own jobs
✅ Update match status
✅ Cannot manage users
```

### **Viewer**
```
✅ Read candidates
✅ Read jobs
✅ Read matches
❌ Create/update/delete anything
```

---

## **Architecture**

```
Request
  ↓
[Authorization Header: Bearer <token>]
  ↓
get_current_user()
  ↓
Verify JWT Token
  ↓
Extract user_id & email
  ↓
get_current_user_with_role()
  ↓
Fetch user from database
  ↓
Include role in request context
  ↓
check_role(["admin", "recruiter"])
  ↓
Match user.role against required roles
  ↓
✅ Allow or ❌ Deny (403)
  ↓
Endpoint Handler
```

---

## **Components**

### **1. Auth Middleware** (`app/middleware/auth_middleware.py`)

**Functions:**

| Function | Purpose |
|----------|---------|
| `get_current_user()` | Extract & verify JWT token |
| `get_current_user_with_role()` | Get user with role from DB |
| `check_role(roles)` | Factory for role checking |
| `require_admin()` | Shortcut for admin role |
| `require_recruiter()` | Shortcut for recruiter role |
| `require_any_role()` | Require any authenticated user |

### **2. User Management API** (`app/api/users.py`)

**Endpoints:**
- `GET /api/v1/users` - List users (admin)
- `GET /api/v1/users/{user_id}` - Get user (admin)
- `PUT /api/v1/users/{user_id}/role` - Update role (admin)
- `PUT /api/v1/users/{user_id}/status` - Enable/disable user (admin)
- `GET /api/v1/users/profile` - Get own profile (any user)

---

## **Usage Examples**

### **Protect Endpoint with Role Check**

```python
from fastapi import APIRouter, Depends
from app.middleware.auth_middleware import check_role

router = APIRouter()

@router.post("/admin-only")
async def admin_endpoint(
    current_user: dict = Depends(check_role(["admin"]))
):
    """Only admin users can access"""
    return {"message": f"Hello {current_user['email']}"}

@router.post("/recruiter-endpoint")
async def recruiter_endpoint(
    current_user: dict = Depends(check_role(["admin", "recruiter"]))
):
    """Admin and recruiter users can access"""
    return {"message": f"Hello {current_user['email']}"}

@router.post("/public-protected")
async def public_endpoint(
    current_user: dict = Depends(check_role(["admin", "recruiter", "viewer"]))
):
    """Any authenticated user can access"""
    return {"message": f"Hello {current_user['email']}"}
```

### **Using Shortcut Dependencies**

```python
from app.middleware.auth_middleware import require_admin, require_recruiter

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)  # Only admin
):
    """Admin only endpoint"""
    pass

@router.post("/jobs")
async def create_job(
    job_data: dict,
    current_user: dict = Depends(require_recruiter)  # Admin or recruiter
):
    """Recruiter endpoint"""
    pass
```

---

## **API Endpoints**

### **1. List Users** (Admin Only)

**Endpoint:** `GET /api/v1/users?skip=0&limit=50`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "recruiter",
      "is_active": true,
      "created_at": "2026-07-31T00:00:00"
    }
  ],
  "total": 1
}
```

---

### **2. Get User** (Admin Only)

**Endpoint:** `GET /api/v1/users/{user_id}`

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "company_name": "Tech Corp",
    "role": "recruiter",
    "is_active": true
  }
}
```

---

### **3. Update User Role** (Admin Only)

**Endpoint:** `PUT /api/v1/users/{user_id}/role`

**Request:**
```json
{
  "role": "admin"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "admin",
    "message": "Role updated from recruiter to admin"
  }
}
```

**Valid Roles:** admin, recruiter, viewer

---

### **4. Enable/Disable User** (Admin Only)

**Endpoint:** `PUT /api/v1/users/{user_id}/status?is_active=false`

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "is_active": false,
    "message": "User deactivated"
  }
}
```

---

### **5. Get Own Profile** (Any User)

**Endpoint:** `GET /api/v1/users/profile`

**Headers:**
```
Authorization: Bearer <any_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "recruiter",
    "is_active": true
  }
}
```

---

## **Error Responses**

### **Missing Authorization Header**
```
Status: 401
{
  "detail": "Missing authorization header"
}
```

### **Invalid Token**
```
Status: 401
{
  "detail": "Invalid or expired token"
}
```

### **Insufficient Permissions**
```
Status: 403
{
  "detail": "Access denied. Required roles: admin"
}
```

### **Invalid Role**
```
Status: 400
{
  "detail": "Invalid role. Must be one of: admin, recruiter, viewer"
}
```

---

## **Safety Features**

✅ **Cannot demote last admin** - At least one admin must exist

✅ **Cannot disable last active admin** - At least one active admin must exist

✅ **Role audit logging** - All role changes logged with admin name

✅ **Token expiration** - Access tokens expire in 30 minutes

✅ **Token type checking** - Only access tokens allowed (not refresh tokens)

---

## **Testing**

### **Test Admin Access**
```bash
# Login as admin
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Pass123!"}' | jq -r '.data.access_token')

# List users (should work)
curl -X GET "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer $TOKEN"
```

### **Test Recruiter Access**
```bash
# Login as recruiter
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"recruiter@example.com","password":"Pass123!"}' | jq -r '.data.access_token')

# Try to list users (should fail with 403)
curl -X GET "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer $TOKEN"
  
# Should return: "Access denied. Required roles: admin"
```

---

## **Best Practices**

✅ Always require authentication for sensitive endpoints

✅ Use specific role requirements (not just any authenticated user)

✅ Log all administrative actions (role changes, user disable)

✅ Audit user access patterns

✅ Enforce strong passwords for admin accounts

✅ Use HTTPS in production (prevent token interception)

✅ Rotate admin credentials regularly

---

## **Future Enhancements**

⏳ Permission-based access (fine-grained permissions)

⏳ Team-based RBAC (user groups)

⏳ Audit trail (immutable action logs)

⏳ Two-factor authentication for admin accounts

⏳ Session management (concurrent logins)

⏳ IP-based access restrictions

---

**Generated:** August 1, 2026  
**Status:** ✅ Complete

