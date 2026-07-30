# Contributing to AI Recruiter Assistant

## Git Workflow

### Branch Naming
- `feature/` - New features (e.g., `feature/resume-upload`)
- `bugfix/` - Bug fixes (e.g., `bugfix/parsing-error`)
- `docs/` - Documentation (e.g., `docs/setup-guide`)
- `hotfix/` - Production hotfixes (e.g., `hotfix/critical-bug`)

### Commit Messages
```
<type>: <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore  
**Subject:** Lowercase, imperative, no period (max 50 chars)  
**Body:** Wrapped at 72 chars, explain what and why

### Pull Request Process

1. Create feature branch from `develop`
2. Keep commits focused and logical
3. Push branch and create PR
4. Wait for CI/CD to pass
5. Request review (minimum 2 reviewers for main)
6. Address feedback
7. Squash commits if needed
8. Merge to develop

## Code Standards

### Python (Backend)
- **Style:** PEP 8 (enforced by Black)
- **Linting:** flake8
- **Type Hints:** Required (mypy)
- **Formatting:** Black (auto-format)
- **Import Sorting:** isort

```bash
cd backend
black app/
mypy app/
flake8 app/
isort app/
```

### JavaScript (Frontend)
- **Style:** Airbnb ESLint config
- **Linting:** ESLint
- **Formatting:** Prettier
- **Type Hints:** TypeScript

```bash
cd frontend
npm run lint
npm run format
```

## Testing Requirements

### Backend
- **Framework:** pytest
- **Coverage:** >70% required
- **Location:** `backend/tests/`

```bash
cd backend
pytest --cov=app --cov-report=html
```

### Frontend
- **Framework:** Jest + React Testing Library
- **Coverage:** >70% required
- **Location:** `frontend/src/__tests__/`

```bash
cd frontend
npm run test:coverage
```

## Running Tests Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
pytest

# Frontend
cd frontend
npm install
npm run test
```

## Documentation

- Keep README.md current
- Add docs for new features
- Update API docs (Swagger auto-generated)
- Document breaking changes

## Release Process

1. Update version in:
   - `backend/app/__init__.py`
   - `frontend/package.json`
   - `README.md`

2. Create CHANGELOG entry

3. Create release branch: `release/v1.x.x`

4. Merge to main and develop

5. Tag commit: `git tag v1.x.x`

## Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Coverage maintained (>70%)
- [ ] No security vulnerabilities
- [ ] Documentation updated
- [ ] No debug code or console.logs
- [ ] Performance impact minimal

## Questions?

Open an issue or contact the team via Slack.

---

Thank you for contributing! 🚀
