"""Quick start guide for running ZimPrep backend with new production features.

PHASE 1-6 Implementation.
"""

# Quick Start: Running ZimPrep Backend

## Prerequisites

```bash
# Python 3.11, 3.12, or 3.13 (NOT 3.14 - SQLAlchemy compatibility issues)
python --version
# Expected output: Python 3.11.x, 3.12.x, or 3.13.x

# MongoDB running locally or accessible
# Redis running (for distributed rate limiting in production)
```

## Setup

### 1. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cd backend
cp .env.example .env
```

**Edit `.env` and configure**:

```env
# CRITICAL: Change JWT secret (generate with command below)
JWT_SECRET=<run: python -c "import secrets; print(secrets.token_urlsafe(32))">

# AI Engine
OPENAI_API_KEY=your_openai_key

# Databases
MONGODB_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0

# Timeout (optional, default 30s)
AI_TIMEOUT_SECONDS=30
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Application

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testing Authentication & RBAC

### Generate Test JWT

```python
import jwt
from datetime import datetime, timedelta

# Generate student token
payload = {
    "sub": "student_001",
    "email": "student@test.com",
    "role": "student",  # Required!
    "exp": datetime.utcnow() + timedelta(hours=1)
}

token = jwt.encode(payload, "YOUR_JWT_SECRET", algorithm="HS256")
print(f"Bearer {token}")
```

### Test API with Token

```bash
# List pipelines (any authenticated user)
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/pipelines

# Try to execute exam (student only)
curl -H "Authorization: Bearer <student_token>" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8000/api/v1/pipeline/execute \
     -d '{"pipeline_name": "exam_attempt_v1", "input_data": {...}}'

# Try to access reporting (should fail for students)
curl -H "Authorization: Bearer <student_token>" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8000/api/v1/pipeline/execute \
     -d '{"pipeline_name": "reporting_v1", "input_data": {...}}'
# Expected: 403 Forbidden
```

## Testing Overrides (Examiner Only)

```bash
# Generate examiner token (role: "examiner")
examiner_token="<generated_token_with_role_examiner>"

# Apply override
curl -H "Authorization: Bearer $examiner_token" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8000/api/v1/exams/trace_test_123/overrides \
     -d '{
       "question_id": "q_math_01",
       "adjusted_mark": 8.0,
       "override_reason": "Alternative solution is mathematically valid"
     }'

# List overrides for exam
curl -H "Authorization: Bearer $examiner_token" \
     http://localhost:8000/api/v1/exams/trace_test_123/overrides
```

## Testing Rate Limiting

```bash
# Make 11 requests rapidly as student (limit: 10/hour)
for i in {1..11}; do
  echo "Request $i"
  curl -H "Authorization: Bearer <student_token>" \
       http://localhost:8000/api/v1/pipelines
done

# Expected: 11th request returns 429 Too Many Requests
```

## Running Tests

```bash
# Install test dependencies
pip install pytest

# Run integration tests
pytest tests/integration/test_production_implementation.py -v

# Run with coverage
pytest tests/integration/test_production_implementation.py --cov=app -v
```

## Database Setup

### MongoDB Collections

```javascript
// Connect to MongoDB
use zimprep

// Create indexes
db.exam_results.createIndex({trace_id: 1}, {unique: true})
db.exam_results.createIndex({user_id: 1})
db.mark_overrides.createIndex({trace_id: 1})
db.mark_overrides.createIndex({override_id: 1}, {unique: true})
db.audit_events.createIndex({trace_id: 1})
db.audit_events.createIndex({event_type: 1})
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Metrics

```bash
curl http://localhost:8000/metrics
# Returns Prometheus-compatible metrics
```

## Common Issues

### JWT Token Rejected (401)

- **Missing role claim**: Add `"role": "student"` to JWT payload
- **Invalid role**: Use one of: `student`, `parent`, `school_admin`, `examiner`, `admin`
- **Wrong secret**: JWT_SECRET must match between token generation and server

### Access Denied (403)

- **Wrong role for pipeline**: Check `PIPELINE_ROLE_REQUIREMENTS` in `pipelines.py`
- Students can only access: `exam_attempt_v1`
- School admins can access: `reporting_v1`
- Examiners can access: all pipelines + override API

### Rate Limit (429)

- **Too many requests**: Wait for rate limit window to reset
- **Check headers**: `Retry-After` tells you how long to wait
- **Adjust limits**: Modify `RateLimitMiddleware` role_limits if needed

### Override Fails (404/500)

- **Exam not found**: trace_id must exist in database
- **MongoDB connection**: Check MONGODB_URI in .env
- **Missing permissions**: Only examiners and admins can override

## Production Deployment

See [`PRODUCTION_DEPLOYMENT.md`](./PRODUCTION_DEPLOYMENT.md) for full checklist.

**Key points**:
1. ✅ Set strong JWT_SECRET (32+ chars)
2. ✅ Configure production MongoDB/Redis
3. ✅ Set OPENAI_API_KEY
4. ✅ Create database indexes
5. ✅ Set ENV=production
6. ✅ Enable monitoring/alerting

## Support

- **Documentation**: See `docs/` folder
- **Tests**: See `tests/integration/`
- **Issues**: Check logs at `backend/error.txt`
