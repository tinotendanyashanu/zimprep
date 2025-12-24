# Production Deployment Checklist

## Pre-Deployment Validation

### ✅ **Environment Configuration**

- [ ] `JWT_SECRET` set to strong value (32+ characters, NOT default)
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- [ ] `OPENAI_API_KEY` configured with valid key

- [ ] `MONGODB_URI` points to production MongoDB cluster (not localhost)

- [ ] `REDIS_URL` points to production Redis instance (for distributed rate limiting)

- [ ] `ENV=production` set in environment

- [ ] `LOG_FORMAT=json` for structured logging

---

### ✅ **Database Setup**

**MongoDB Indexes** (Critical for performance):
```javascript
// Exam results collection
db.exam_results.createIndex({trace_id: 1}, {unique: true})
db.exam_results.createIndex({user_id: 1})
db.exam_results.createIndex({exam_id: 1})

// Mark overrides collection
db.mark_overrides.createIndex({trace_id: 1})
db.mark_overrides.createIndex({override_id: 1}, {unique: true})
db.mark_overrides.createIndex({overridden_by_user_id: 1})

// Audit events collection
db.audit_events.createIndex({trace_id: 1})
db.audit_events.createIndex({event_type: 1})
db.audit_events.createIndex({timestamp: -1})
```

---

### ✅ **Security Validation**

- [ ] JWT tokens require `role` claim (invalid tokens rejected with 401)

- [ ] Role validation whitelist enforced: `{student, parent, school_admin, examiner, admin}`

- [ ] RBAC pipeline access enforced:
  - Students → `exam_attempt_v1` only
  - School admins → `reporting_v1`
  - Examiners → all pipelines + override API
  - Admins → all access

- [ ] Override API restricted to examiners/admins only (403 for others)

---

### ✅ **Operational Robustness**

- [ ] Rate limiting active (verify `RateLimitMiddleware` registered)

- [ ] Rate limits configured per role:
  - Student: 10 req/hour
  - Parent: 20 req/hour
  - School admin: 100 req/hour
  - Examiner: 100 req/hour
  - Admin: unlimited

- [ ] `AI_TIMEOUT_SECONDS` set appropriately (default: 30)

- [ ] Health check endpoint responding: `/health`

- [ ] Metrics endpoint accessible: `/metrics`

---

### ✅ **Data Integrity**

- [ ] Grade boundary snapshots schema exists

- [ ] Override records are immutable (frozen Pydantic models)

- [ ] Results Engine applies overrides correctly:
  - Original AI marks preserved
  - Adjusted marks used for final grade
  - Override metadata stored in result

- [ ] Audit trail captures:
  - Real user IDs (not temporary)
  - Override events with justification
  - Full decision timeline

---

### ✅ **Testing**

**Run integration tests**:
```bash
cd backend
pytest tests/integration/test_production_implementation.py -v
```

**Expected results**:
- ✅ Authentication tests pass
- ✅ RBAC enforcement tests pass
- ✅ Override access control tests pass
- ✅ Rate limiting tests pass

---

### ✅ **Monitoring & Alerting**

Configure alerts for:
- [ ] Failed authentication attempts (potential security breach)
- [ ] Unauthorized access attempts (403 responses)
- [ ] Override activity spikes (unusual examiner activity)
- [ ] Rate limit violations (potential abuse)
- [ ] AI timeout failures (service degradation)
- [ ] Database connection errors

---

### ✅ **Documentation**

- [ ] API documentation updated with new endpoints:
  - `POST /api/v1/exams/{trace_id}/overrides`
  - `GET /api/v1/exams/{trace_id}/overrides`

- [ ] Role permission matrix documented

- [ ] Override workflow documented for examiners

- [ ] Appeal reconstruction process documented

---

## Post-Deployment Verification

### Day 1 Checks

- [ ] Monitor authentication success rate (should be >95%)
- [ ] Verify no 403 errors for legitimate users
- [ ] Check override API usage (should only be examiners)
- [ ] Monitor rate limiting effectiveness (check 429 responses)
- [ ] Verify audit logs capturing user_id correctly

### Week 1 Checks

- [ ] Review override justifications (quality check)
- [ ] Analyze appeal reconstruction usage
- [ ] Monitor AI timeout frequency
- [ ] Review database index performance
- [ ] Check for any security anomalies

---

## Rollback Plan

If critical issues arise:

1. **Authentication Issues**:
   - Rollback JWT validation changes
   - Temporarily disable role requirement
   - Log all auth failures for analysis

2. **RBAC Issues**:
   - Temporarily grant broader access
   - Log all 403 responses
   - Fix pipeline requirements mapping

3. **Override Issues**:
   - Disable override API endpoint
   - Investigate database consistency
   - Review override logic

4. **Rate Limiting Issues**:
   - Disable `RateLimitMiddleware`
   - Investigate Redis connection
   - Adjust rate limits if too restrictive

---

## Support Contacts

- **Security Issues**: [security team contact]
- **Database Issues**: [DBA contact]
- **API Issues**: [backend team contact]
- **Examiner Support**: [examiner support contact]

---

## Implementation Status

**Completed** (Production-Ready):
- ✅ Phase 1: Authentication hardening
- ✅ Phase 2: RBAC enforcement
- ✅ Phase 3: Human override flow
- ✅ Phase 6: Rate limiting

**Pending** (Integration Required):
- ⏭️ Phase 4: Boundary snapshot integration
- ⏭️ Phase 5: Appeal reconstruction enhancements
- ⏭️ Phase 6: AI timeout enforcement
- ⏭️ Phase 7: Comprehensive test suite

**Production Readiness**: ~75% complete
