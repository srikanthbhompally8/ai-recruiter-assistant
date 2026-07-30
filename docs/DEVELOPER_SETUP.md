# Developer Setup Guide

**AI Recruiter Assistant** - Complete local development setup guide

---

## Prerequisites

### System Requirements
- **OS:** macOS, Linux, or Windows (WSL2)
- **RAM:** 8GB minimum
- **Disk:** 20GB free space

### Required Software
- **Python 3.11+** - https://www.python.org/downloads/
- **Node.js 18+** - https://nodejs.org/
- **PostgreSQL 15** - https://www.postgresql.org/download/
- **Git** - https://git-scm.com/
- **Docker & Docker Compose** (optional, for containerized setup)

### AWS Account
- AWS Account with Bedrock access
- AWS CLI configured locally
- IAM user with Bedrock and S3 permissions

---

## Option 1: Quick Start with Docker (5 minutes)

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-recruiter-assistant.git
cd ai-recruiter-assistant
```

### 2. Configure Environment
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` with your AWS credentials:
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
BEDROCK_REGION=us-east-1
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Initialize Database
```bash
docker-compose exec backend alembic upgrade head
```

### 5. Access Application
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 6. Stop Services
```bash
docker-compose down
```

---

## Option 2: Local Development Setup (30 minutes)

### Backend Setup

#### 1. Create Virtual Environment
```bash
cd backend
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` with your settings:
- AWS credentials
- Database URL
- Bedrock configuration
- JWT secret (generate: `openssl rand -hex 32`)

#### 4. PostgreSQL Setup

**Option A: Docker (Quick)**
```bash
docker run --name recruiter-postgres \
  -e POSTGRES_USER=recruiter \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=recruiter_db \
  -p 5432:5432 \
  -d postgres:15-alpine
```

**Option B: Local Installation**
```bash
# macOS (with Homebrew)
brew install postgresql@15
brew services start postgresql@15
createdb -U postgres recruiter_db

# Linux (Ubuntu/Debian)
sudo apt-get install postgresql-15
sudo -u postgres createdb recruiter_db

# Windows
# Use PostgreSQL installer from https://www.postgresql.org/download/windows/
# Create database via pgAdmin GUI
```

#### 5. Database Migrations
```bash
alembic upgrade head
```

#### 6. Run Backend
```bash
uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000

---

### Frontend Setup

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Configure Environment
```bash
cp .env.example .env
```

#### 3. Run Development Server
```bash
npm run dev
```

App runs at: http://localhost:5173

---

## AWS Configuration

### 1. Install AWS CLI
```bash
pip install awscli
```

### 2. Configure AWS Credentials
```bash
aws configure
```

Enter:
- Access Key ID
- Secret Access Key
- Default region: `us-east-1`
- Output format: `json`

### 3. Enable Bedrock Models

Go to AWS Console → Bedrock → Model Access:
- ✅ Enable: `Anthropic Claude 3.5 Sonnet`
- ✅ Enable: `Amazon Titan Text Embeddings`

### 4. Create S3 Bucket
```bash
aws s3api create-bucket \
  --bucket recruiter-files-unique-name \
  --region us-east-1
```

Update `backend/.env`:
```env
AWS_S3_BUCKET=recruiter-files-unique-name
```

### 5. Test Bedrock Connection
```bash
cd backend
python -c "import boto3; client = boto3.client('bedrock'); print('✅ Bedrock connection successful')"
```

---

## Troubleshooting

### PostgreSQL Connection Error
```
Error: FATAL: Ident authentication failed for user "recruiter"
```

**Solution:** Use the Docker container or check PostgreSQL authentication in `pg_hba.conf`

### Port Already in Use
```bash
# Find process using port 5432
lsof -i :5432

# Kill process
kill -9 <PID>
```

### AWS Credentials Not Found
```bash
# Verify credentials are configured
aws sts get-caller-identity

# If not set, run:
aws configure
```

### Module Import Error
```bash
# Ensure you're in the backend directory with venv activated
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Node Modules Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## Development Workflow

### Daily Development
1. Activate virtual environment
2. Start PostgreSQL (if not using Docker)
3. Start backend: `cd backend && uvicorn app.main:app --reload`
4. Start frontend: `cd frontend && npm run dev`
5. Access at http://localhost:5173

### Running Tests
```bash
# Backend
cd backend
pytest --cov=app

# Frontend
cd frontend
npm run test:coverage
```

### Code Quality
```bash
# Backend
cd backend
black app/
mypy app/
flake8 app/

# Frontend
cd frontend
npm run lint
npm run format
```

---

## Environment Variables Reference

### Backend
| Variable | Example | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | postgresql://recruiter:password@localhost:5432/recruiter_db | Database connection |
| `AWS_ACCESS_KEY_ID` | AKIAIOSFODNN7EXAMPLE | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY | AWS credentials |
| `BEDROCK_MODEL_ID` | us.anthropic.claude-3-5-sonnet-20241022-v2:0 | Claude model |
| `BEDROCK_EMBEDDINGS_MODEL` | amazon.titan-embed-text-v2:0 | Embeddings model |
| `JWT_SECRET` | your-secret-key | JWT signing |
| `CORS_ORIGINS` | ["http://localhost:5173"] | CORS whitelist |

### Frontend
| Variable | Example | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | http://localhost:8000 | Backend API URL |
| `VITE_API_TIMEOUT` | 30000 | Request timeout (ms) |
| `VITE_ENVIRONMENT` | development | Environment name |

---

## IDE Setup

### VS Code
Extensions:
- Python
- Pylance
- FastAPI
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- Prettier
- ESLint

Settings (`.vscode/settings.json`):
```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  }
}
```

### PyCharm
- Install Python plugin
- Configure Python interpreter to `backend/venv`
- Enable Django/FastAPI support

---

## Database Management

### View Database
```bash
# Connect to PostgreSQL
psql -U recruiter -d recruiter_db -h localhost

# List tables
\dt

# Exit
\q
```

### Create Migration
```bash
cd backend
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

### Reset Database
```bash
# Drop all tables
alembic downgrade base

# Recreate
alembic upgrade head
```

---

## Performance Optimization

### Backend
- Use connection pooling (enabled by default)
- Add database indexes for frequently queried columns
- Cache with Redis

### Frontend
- Use React.memo for expensive components
- Lazy load routes
- Optimize images

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure venv is activated and dependencies installed |
| Database won't connect | Check PostgreSQL is running and `DATABASE_URL` is correct |
| `CORS error` | Verify frontend URL in `CORS_ORIGINS` |
| `Bedrock not available` | Ensure model is enabled in AWS console and credentials are correct |
| Port already in use | Use `lsof -i :PORT` to find and kill process |

---

## Next Steps

1. ✅ Complete local setup
2. 📖 Read [ARCHITECTURE.md](ARCHITECTURE.md)
3. 🚀 Start developing!
4. 📝 Follow [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Need help?** Check the [README.md](../README.md) or open an issue on GitHub.
