# RUNBOOK: Exam Outage Mid-Session

**Phase B5: Incident Response**  
**Severity**: CRITICAL  
**Last Updated**: 2025-12-23

## Overview

This runbook covers procedures for handling exam outages that occur while students are actively taking exams. This is a CRITICAL scenario as exam interruptions directly impact student outcomes and have regulatory implications.

## Detection Signals

### Automated Alerts

- **Health check failures**: `/health` endpoint returns 500/503
- **Error rate spike**: >5% of requests failing
- **Latency spike**: p95 latency >5 seconds
- **Database unavailability**: Connection pool exhausted
- **Metrics gap**: No metrics received for >2 minutes

### Manual Reports

- Support tickets from students/schools
- Direct reports from proctors
- Social media monitoring

## Severity Classification

| Level | Impact | Response Time |
|-------|--------|---------------|
| P0 | >50% of students affected | Immediate (5 min) |
| P1 | 10-50% of students affected | 15 minutes |
| P2 | <10% of students affected | 1 hour |

## Immediate Containment (First 5 Minutes)

### 1. Confirm Outage

```bash
# Check API health
curl https://api.zimprep.com/health

# Check metrics
curl https://api.zimprep.com/metrics | grep zimprep_pipeline_failures_total

# Check database connectivity
psql -h $DB_HOST -U $USER -d zimprep -c "SELECT 1;"
mongosh "$MONGO_URI" --eval "db.adminCommand('ping')"
```

### 2. Identify Active Sessions

```bash
# Query active exam sessions
python scripts/query_active_sessions.py

# Expected output:
# - Number of active sessions
# - Students affected
# - Time remaining per session
```

### 3. Enable Maintenance Mode (if necessary)

```bash
# Set read-only mode for new sessions
# Existing sessions continue but new ones blocked
kubectl set env deployment/zimprep-api MAINTENANCE_MODE=true
```

## Escalation Path

### Level 1: On-Call Engineer (0-15 min)
- **Action**: Initial triage and containment
- **Authority**: Enable maintenance mode, restart services
- **Contact**: #oncall-engineering (Slack), PagerDuty

### Level 2: Engineering Lead (15-30 min)
- **Action**: Technical decision-making, resource allocation
- **Authority**: Database failover, traffic rerouting
- **Contact**: engineering-lead@zimprep.com

### Level 3: CTO + Regulatory Officer (30+ min)
- **Action**: Stakeholder communication, regulatory compliance
- **Authority**: Exam cancellation/postponement decisions
- **Contact**: cto@zimprep.com, regulatory@zimprep.com

## Recovery Procedures

### Scenario A: API Service Failure

```bash
# 1. Check recent deployments
kubectl rollout history deployment/zimprep-api

# 2. Rollback if recent deployment
kubectl rollout undo deployment/zimprep-api

# 3. Scale up replicas for load distribution
kubectl scale deployment/zimprep-api --replicas=10

# 4. Monitor recovery
watch kubectl get pods
```

### Scenario B: Database Connection Issues

```bash
# 1. Check connection pool
psql -c "SELECT count(*) FROM pg_stat_activity;"

# 2. Kill idle connections if needed
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# 3. Restart connection pool
kubectl rollout restart deployment/zimprep-api

# 4. Monitor connections
watch "psql -c 'SELECT count(*) FROM pg_stat_activity;'"
```

### Scenario C: AI Provider Downtime

See: `/docs/runbooks/ai_provider_downtime.md`

```bash
# 1. Switch to fallback AI provider
kubectl set env deployment/zimprep-api AI_PROVIDER=anthropic

# 2. Verify fallback working
curl -X POST https://api.zimprep.com/api/v1/exam/test-ai-connection
```

### Scenario D: MongoDB Outage

```bash
# 1. Check MongoDB status
mongosh "$MONGO_URI" --eval "rs.status()"

# 2. Failover to secondary if needed
mongosh "$MONGO_URI" --eval "rs.stepDown()"

# 3. Verify replica set health
mongosh "$MONGO_URI" --eval "rs.printReplicationInfo()"
```

## Student Communication

### Immediate (Within 15 minutes)

**Via Platform Banner**:
> "We're experiencing technical difficulties. Your exam session is being preserved. Do not refresh your browser. Updates in 10 minutes."

**Email Template** (if outage >30 min):
> Subject: Exam Technical Issue - Your Progress is Safe
>
> Dear Student,
>
> We are currently experiencing a technical issue affecting exam access. Please note:
> - Your progress has been automatically saved
> - Your exam time will be extended by [X] minutes
> - You will NOT lose any answers you've submitted
>
> Expected resolution: [TIME]
> 
> We apologize for the inconvenience.
>
> ZimPrep Technical Team

### Post-Recovery Communication

- Send confirmation email when service restored
- Provide incident summary (non-technical)
- Confirm time extensions applied

## Data Integrity Verification

After recovery, MUST verify:

```bash
# 1. Check for orphaned sessions
python scripts/verify_session_integrity.py

# 2. Verify submission completeness
python scripts/verify_submissions.py --since="2025-12-23 14:00"

# 3. Audit trail verification
python scripts/verify_audit_trail.py --incident-id=INC-20251223-001

# 4. Generate integrity report
python scripts/generate_integrity_report.py --output=incident_report.pdf
```

## Post-Incident Review

Within 24 hours of resolution:

1. **Timeline reconstruction**: Document exact sequence of events
2. **Root cause analysis**: Identify underlying cause (not just symptoms)
3. **Impact assessment**: Students affected, time lost, data integrity
4. **Actionable improvements**: Specific technical/process changes
5. **Regulatory reporting**: Notify exam board if required

### Required Attendees

- On-call engineer who responded
- Engineering lead
- Product manager
- Regulatory officer (if student data impacted)

## Regulatory Compliance

### Zimbabwe Exam Board Notification

Required if:
- Outage affects official/certificated exams
- Duration >30 minutes
- >100 students affected

**Notification timeline**: Within 4 hours
**Contact**: exams@zimsec.co.zw
**Report format**: Use template in `/docs/templates/regulatory_incident_report.docx`

### Data Protection Officer Notification

Required if:
- Student data potentially compromised
- Audit trail gaps detected

**Notification timeline**: Within 1 hour
**Contact**: dpo@zimprep.com

## Prevention Measures

- **Load testing**: Monthly load tests simulating peak exam periods
- **Chaos engineering**: Quarterly failure injection tests
- **Capacity planning**: Review before major exam seasons
- **Circuit breakers**: Implement timeout/fallback patterns
- **Monitoring enhancements**: Reduce detection time to <30 seconds

---

## Quick Reference Card

```
Detection → Confirm (5 min) → Escalate (if >P1) → Contain → Recover → Verify → Communicate
```

**Critical Contacts**:
- OnCALL: Page via PagerDuty
- Engineering Lead: +263-XXX-XXXX
- CTO: +263-XXX-XXXX
- Regulatory: +263-XXX-XXXX

**Critical Commands**:
```bash
# Status check
curl https://api.zimprep.com/health

# Active sessions
python scripts/query_active_sessions.py

# Rollback deployment
kubectl rollout undo deployment/zimprep-api

# Enable maintenance mode
kubectl set env deployment/zimprep-api MAINTENANCE_MODE=true
```
