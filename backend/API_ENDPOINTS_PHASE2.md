# API Endpoints Documentation - Phase 2

**Version:** 1.1  
**Status:** Phase 2 Complete  
**Last Updated:** September 17, 2026

---

## Quick Start

### Base URL
```
http://localhost:8000
```

### Authentication
All endpoints require JWT Bearer token (except `/health` and `/auth/login`):
```
Authorization: bearer <your_jwt_token>
```

---

## Endpoints Overview

| Group | Endpoint | Method | Auth | Status |
|-------|----------|--------|------|--------|
| Health | `/health` | GET | ❌ | ✅ |
| Auth | `/api/v1/auth/login` | POST | ❌ | ✅ |
| Auth | `/api/v1/auth/refresh` | POST | ✅ | ✅ |
| Users | `/api/v1/users/me` | GET | ✅ | ✅ |
| Candidates | `/api/v1/candidates/candidates` | GET | ✅ | ✅ |
| Candidates | `/api/v1/candidates/{id}` | GET | ✅ | ✅ |
| Candidates | `/api/v1/candidates` | POST | ✅ | ✅ |
| **Jobs** | **`/api/v1/jobs/jobs`** | **GET** | **✅** | **✅** |
| **Jobs** | **`/api/v1/jobs`** | **POST** | **✅** | **✅** |
| **Jobs** | **`/api/v1/jobs/{id}`** | **GET** | **✅** | **✅** |
| **Job Parsing** | **`/api/v1/jobs/parse`** | **POST** | **✅** | **✅ NEW** |
| **Job Parsing** | **`/api/v1/jobs/extract-skills`** | **POST** | **✅** | **✅ NEW** |
| Matches | `/api/v1/matches/matches` | GET | ✅ | ✅ |
| Matches | `/api/v1/matches/{id}` | GET | ✅ | ✅ |

---

## Detailed Endpoint Documentation

### Authentication

#### 1. Login
```
POST /api/v1/auth/login
```

**Request:**
```json
{
  "email": "recruiter1@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "recruiter1@example.com",
      "full_name": "Recruiter One",
      "role": "recruiter"
    }
  }
}
```

---

### Health Check

#### 2. Health Status
```
GET /health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development"
}
```

---

### Jobs Management

#### 3. Get All Jobs
```
GET /api/v1/jobs/jobs
Authorization: bearer <token>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "id": "697c9249-036c-4f29-8b1b-9839a65bc675",
      "title": "Senior Backend Engineer",
      "company": "TechStartup Inc",
      "description": "We are seeking a Senior Backend Engineer...",
      "job_type": "full-time",
      "experience_required": 6,
      "salary_min": 180000.00,
      "salary_max": 240000.00,
      "status": "open",
      "created_at": "2026-09-17T12:00:00"
    }
  ]
}
```

#### 4. Get Job by ID
```
GET /api/v1/jobs/{id}
Authorization: bearer <token>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "697c9249-036c-4f29-8b1b-9839a65bc675",
    "title": "Senior Backend Engineer",
    "company": "TechStartup Inc",
    "required_skills": "Python, FastAPI, PostgreSQL",
    "nice_to_have_skills": "AWS, Kubernetes, GraphQL",
    "experience_required": 6,
    "job_type": "full-time",
    "job_level": "senior",
    "salary_min": 180000.00,
    "salary_max": 240000.00,
    "job_details_json": {
      "job_title": "Senior Backend Engineer",
      "company": "TechStartup Inc",
      "required_skills": ["Python", "FastAPI", "PostgreSQL"],
      "nice_to_have_skills": ["AWS", "Kubernetes", "GraphQL"],
      "years_required": 6,
      "job_type": "full-time",
      "job_level": "senior",
      "salary_range": "$180,000 - $240,000",
      "responsibilities": ["Design and implement scalable microservices", "Develop robust REST APIs"]
    },
    "status": "open",
    "created_at": "2026-09-17T12:00:00",
    "updated_at": "2026-09-17T12:00:00"
  }
}
```

#### 5. Create Job (Manual)
```
POST /api/v1/jobs
Authorization: bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "title": "Full Stack Engineer",
  "company": "WebCorp",
  "description": "Looking for a full stack engineer...",
  "required_skills": "React, Node.js, PostgreSQL",
  "experience_required": 4
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": "new-job-id-uuid",
    "title": "Full Stack Engineer",
    "company": "WebCorp",
    "status": "open"
  }
}
```

---

### **Phase 2: Job Parsing (AWS Bedrock Integration)**

#### 6. Parse Job Description ✨ NEW
```
POST /api/v1/jobs/parse
Authorization: bearer <token>
Content-Type: application/json
```

**Purpose:** Automatically parse raw job descriptions using AWS Bedrock AI to extract structured data.

**Request:**
```json
{
  "job_description": "We are seeking a Senior Backend Engineer to join our growing platform team.\n\nKey Responsibilities:\n- Design and implement scalable microservices using Python\n- Develop robust REST APIs with FastAPI\n- Manage PostgreSQL databases and optimize queries\n\nRequired Qualifications:\n- 6+ years of backend development experience\n- Expert-level Python programming skills\n- Strong experience with FastAPI\n- PostgreSQL database design and optimization\n\nWe offer:\n- Competitive salary: $180,000 - $240,000\n- Full-time position",
  "company": "TechStartup Inc"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Job description parsed and saved successfully",
  "data": {
    "job_id": "697c9249-036c-4f29-8b1b-9839a65bc675",
    "title": "Senior Backend Engineer",
    "company": "TechStartup Inc",
    "job_type": "full-time",
    "experience_required": 6,
    "job_level": "senior",
    "required_skills": [
      "Python",
      "FastAPI",
      "PostgreSQL",
      "Docker",
      "Kubernetes"
    ],
    "nice_to_have_skills": [
      "AWS",
      "Redis",
      "Kafka",
      "GraphQL"
    ],
    "salary_range": "$180,000 - $240,000",
    "responsibilities": [
      "Design and implement scalable microservices using Python",
      "Develop robust REST APIs with FastAPI",
      "Manage PostgreSQL databases and optimize queries"
    ]
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Job description too short (minimum 50 characters)"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid or expired token"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "detail": "Job parsing failed: API service error"
}
```

**Request Parameters:**
- `job_description` (string, required): Raw job description text (min 50 characters)
- `company` (string, optional): Company name for context
- `source` (string, optional): Job source (linkedin, indeed, etc)

**Response Fields:**
- `job_id`: UUID of newly created job in database
- `title`: Parsed job title
- `company`: Company name
- `job_type`: Employment type (full-time, contract, part-time)
- `experience_required`: Years of experience required
- `job_level`: Job level (entry, mid, senior)
- `required_skills`: List of required technical skills
- `nice_to_have_skills`: List of optional skills
- `salary_range`: Formatted salary range
- `responsibilities`: List of key responsibilities

**Database Impact:**
- ✅ Job automatically saved to `job_descriptions` table
- ✅ Structured data stored in `job_details_json` column
- ✅ User_id automatically set from JWT token
- ✅ Status set to "open"

---

#### 7. Extract Skills from Text ✨ NEW
```
POST /api/v1/jobs/extract-skills
Authorization: bearer <token>
Content-Type: application/json
```

**Purpose:** Extract technical and soft skills from candidate profile, resume, or any text using AWS Bedrock AI.

**Request:**
```json
{
  "text": "Full-stack developer with 8 years of professional experience.\n\nTechnical Skills:\n- Expert in Python (8 years), Java (5 years), JavaScript (6 years)\n- Advanced FastAPI and Django expertise\n- PostgreSQL and MongoDB proficiency\n- AWS services (EC2, RDS, S3, Lambda)\n- Docker and Kubernetes orchestration\n- Redis caching implementation\n\nSoft Skills:\n- Team leadership and mentoring\n- Excellent communication and presentation abilities\n- Problem-solving and analytical thinking\n- Agile/Scrum methodology expert"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Skills extracted successfully",
  "data": {
    "technical_skills": [
      "Python",
      "Java",
      "JavaScript",
      "FastAPI",
      "Django",
      "PostgreSQL",
      "MongoDB",
      "AWS",
      "Docker",
      "Kubernetes",
      "Redis"
    ],
    "soft_skills": [
      "Team leadership",
      "Mentoring",
      "Communication",
      "Problem-solving",
      "Analytical thinking",
      "Agile/Scrum"
    ],
    "proficiency_levels": {
      "Python": "expert",
      "Java": "advanced",
      "JavaScript": "advanced",
      "FastAPI": "expert",
      "Django": "advanced",
      "AWS": "intermediate",
      "Docker": "intermediate",
      "Kubernetes": "intermediate"
    },
    "total_technical": 11,
    "total_soft": 6
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Text too short (minimum 50 characters)"
}
```

**Request Parameters:**
- `text` (string, required): Candidate profile, resume, or skill description (min 50 characters)

**Response Fields:**
- `technical_skills`: List of identified technical skills
- `soft_skills`: List of identified soft/interpersonal skills
- `proficiency_levels`: Proficiency level for each skill (beginner, intermediate, expert)
- `total_technical`: Count of technical skills
- `total_soft`: Count of soft skills

---

### Candidates

#### 8. Get All Candidates
```
GET /api/v1/candidates/candidates
Authorization: bearer <token>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "id": "candidate-uuid",
      "email": "john.doe@example.com",
      "full_name": "John Doe",
      "current_title": "Software Engineer",
      "current_company": "TechCorp",
      "experience_years": 5,
      "status": "active"
    }
  ]
}
```

---

### Matches

#### 9. Get All Matches
```
GET /api/v1/matches/matches
Authorization: bearer <token>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "id": "match-uuid",
      "candidate_id": "candidate-uuid",
      "job_id": "job-uuid",
      "skills_match": 85.5,
      "experience_match": 92.0,
      "overall_score": 88.75,
      "recommendation": "strong",
      "status": "pending"
    }
  ]
}
```

---

## Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET/POST |
| 201 | Created | New resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Missing auth header |
| 404 | Not Found | Resource not found |
| 500 | Server Error | API service error |

---

## Example Usage

### Complete Workflow: Parse Job + Extract Skills

**Step 1: Login**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "recruiter1@example.com",
    "password": "password123"
  }'
```

**Step 2: Parse Job Description**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/api/v1/jobs/parse \
  -H "Authorization: bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Backend Engineer with Python expertise...",
    "company": "TechStartup Inc"
  }'
```

**Step 3: Extract Skills from Candidate**
```bash
curl -X POST http://localhost:8000/api/v1/jobs/extract-skills \
  -H "Authorization: bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "8 years Python expert, FastAPI, Docker, Kubernetes..."
  }'
```

**Step 4: View Parsed Jobs**
```bash
curl -X GET http://localhost:8000/api/v1/jobs/jobs \
  -H "Authorization: bearer $TOKEN"
```

---

## Rate Limits

Currently no rate limits. Future versions will implement:
- 100 requests/minute per user
- Bedrock API rate limits (AWS account limits)

---

## Troubleshooting

### 401 Unauthorized
- Token has expired (refresh with `/api/v1/auth/refresh`)
- Token format incorrect (should be `bearer <token>`)
- User credentials invalid

### 500 Bedrock API Errors
- AWS credentials not configured
- Bedrock API service unavailable
- Request format invalid

### Job Parsing Issues
- Job description too short (< 50 characters)
- Special characters causing encoding issues
- API timeout (adjust timeout to 120s)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | July 30, 2026 | Initial API endpoints |
| 1.1 | September 17, 2026 | Added job parsing endpoints (Phase 2) |

---

**Last Updated:** September 17, 2026  
**Next Update:** Phase 3 (Skill Matching)  
**Documentation Source:** PHASE2_COMPLETION_REPORT.md

