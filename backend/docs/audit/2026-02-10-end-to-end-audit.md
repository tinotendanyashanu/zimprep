# ZimPrep End-to-End Audit

Date: 2026-02-10
Environment: Windows local, staging docker-compose
Scope: Backend tests + frontend build/tests

## Summary
- Staging Docker build failed while installing Python dependencies (pip timeout).
- Backend dependency install failed on Python 3.14 due to asyncpg build error.
- Backend test collection failed because tests could not import app module.
- Frontend production build failed due to a JSX attribute typo.
- Frontend build warned about incorrect workspace root and reported one high vulnerability.

## Commands Run
- docker compose -f backend/docker-compose.staging.yml up --build -d
- C:/Users/tinot/Desktop/zimprep/backend/venv/Scripts/python.exe -m pip install -r backend/requirements.txt
- C:/Users/tinot/Desktop/zimprep/backend/venv/Scripts/python.exe -m pytest backend/tests -q
- npm install (frontend)
- npm run build (frontend)

## Breakpoints and Fix Guidance

### 1) Staging Docker build fails during pip install
- Failure: pip ReadTimeout from files.pythonhosted.org while running pip install in Docker build.
- Impact: Staging container cannot build or start.
- Fix guidance:
  - Add a pip download cache or a retry strategy in Docker build.
  - Consider prebuilding wheels or pinning a local wheel cache for large deps.
  - Optionally add build arg for PIP_DEFAULT_TIMEOUT.

### 2) Backend dependency install fails on Python 3.14
- Failure: asyncpg fails to build a wheel on Python 3.14 (C compiler error).
- Impact: Local backend dependencies cannot be installed, blocking tests.
- Fix guidance:
  - Use Python 3.11 for local dev (match Docker image).
  - Alternatively pin asyncpg to a version with cp314 wheels, or make asyncpg optional for non-Postgres dev.

### 3) Backend tests fail to collect (ModuleNotFoundError: app)
- Failure: tests/manual/minimal_test.py cannot import app.
- Impact: Entire pytest collection fails, no tests run.
- Fix guidance:
  - Run pytest from backend directory, or set PYTHONPATH=backend.
  - Add a pytest.ini with pythonpath = .
  - Avoid calling sys.exit in collection-time tests.

### 4) Frontend build fails (JSX typo)
- Failure: TypeScript error in components/exam-countdown.tsx: class Name should be className.
- Impact: Production build fails.
- Fix guidance:
  - Replace class Name with className.

### 5) Frontend build root warning and security warning
- Failure: Next.js inferred wrong workspace root due to extra lockfile; npm audit reports one high vulnerability.
- Impact: Build may use incorrect root; security risk flagged.
- Fix guidance:
  - Remove stray lockfile or set turbopack.root in next.config.
  - Run npm audit fix and validate dependency changes.

## SaaS Readiness Gaps (Observed)
- docker-compose.staging.yml defines API only; no MongoDB/Redis/Postgres services included.
- Staging environment depends on external secrets and databases but does not document provisioning steps.
- No automated migration or seed step for staging startup.

## Recommended Next Steps
- Standardize on Python 3.11 across local dev and CI.
- Add CI build steps for Docker and Next.js build.
- Add a minimal staging compose that includes required data services or a stubbed dev stack.