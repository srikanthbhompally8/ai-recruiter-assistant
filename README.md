# AI Recruiter Assistant

**Intelligent recruitment platform powered by AWS Bedrock**

An end-to-end recruitment solution that automates resume parsing, candidate matching, and job requisition management using AI-powered analysis and semantic search.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15
- AWS Account with Bedrock access

### Local Development Setup (30 minutes)

Complete step-by-step guide in `docs/DEVELOPER_SETUP.md`:
1. Backend setup with virtual environment
2. Frontend setup with npm
3. PostgreSQL configuration
4. AWS Bedrock setup
5. Running both services locally

## 📋 Project Structure

```
ai-recruiter-assistant/
├── backend/          # FastAPI application
├── frontend/         # React application
├── docs/            # Documentation
├── .github/         # CI/CD pipelines
└── docker-compose.yml
```

## ✨ Features

**Phase 1:**
- ✅ User authentication (JWT)
- ✅ Resume upload and parsing
- ✅ Candidate profile management
- ✅ Job description management
- ✅ AI-powered matching (Claude Sonnet)
- ✅ Semantic search (Titan Embeddings)
- ✅ REST APIs (Swagger docs)
- ✅ React UI (Tailwind CSS)

**Future Phases:**
- Phase 2: Advanced matching, bulk operations
- Phase 3: Interview scheduling, analytics
- Phase 4: ATS integration, ML training

## 🛠️ Technology Stack

**Backend:** FastAPI, PostgreSQL 15 + pgvector, SQLAlchemy, AWS Bedrock  
**Frontend:** React 18, Redux Toolkit, Tailwind CSS, Vite  
**Infrastructure:** Docker, EC2, RDS, S3  
**CI/CD:** GitHub Actions  

## 📖 Documentation

- **Setup:** `docs/DEVELOPER_SETUP.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **API Reference:** Backend Swagger at `/docs`
- **Contributing:** `CONTRIBUTING.md`

## 🧪 Testing

```bash
# Backend
cd backend && pytest --cov=app

# Frontend
cd frontend && npm test:coverage
```

## 📊 Performance Targets

- API response: < 500ms
- Database queries: < 100ms
- Test coverage: > 70%
- Frontend build: < 30s

## 🔐 Security

- JWT authentication
- bcrypt password hashing
- SQL injection protection (SQLAlchemy)
- CORS configuration
- Environment-based secrets

## 📞 Support

**Issues:** GitHub Issues  
**Documentation:** See `docs/` folder  
**Setup Help:** Read `docs/DEVELOPER_SETUP.md`

## 📄 License

Proprietary - TeamitserveUSA

---

**Ready to get started?**

1. **Local Setup:** Follow `docs/DEVELOPER_SETUP.md`
2. **Learn More:** Check `docs/ARCHITECTURE.md`
3. **Contribute:** See `CONTRIBUTING.md`

---

*Phase 1 - Sprint 1 - July 24, 2026*
