# RUNBOOK: Data Breach Scenario

**Phase B5: Incident Response**  
**Severity**: CRITICAL  
**Last Updated**: 2025-12-23

## Overview

Response procedures for suspected or confirmed unauthorized access to student data, exam content, or system infrastructure.

**CRITICAL**: This is our highest-severity incident type due to regulatory and legal implications.

## Detection Signals

### Automated
- Unusual database query patterns
- Mass data export attempts
- Failed authentication spike
- Unauthorized API access
- Privilege escalation attempts

### Manual
- Security researcher disclosure
- Dark web monitoring alerts
- Customer reports of suspicious activity
- Regulatory inquiry

## Severity Classification

| Level | Scope | Examples |
|-------|-------|----------|
| P0 | PII exposure | Student names, IDs, grades leaked |
| P1 | System compromise | Database access, admin panel breach |
| P2 | Attempted breach | Failed attack, vulnerability disclosed |

## IMMEDIATE CONTAINMENT (First 30 Minutes)

### 1. Isolate Affected Systems

```bash
# CRITICAL: Act fast, document later
# Immediately revoke compromised credentials
python scripts/security/revoke_credentials.py --user-id=SUSPECTED

# Isolate affected pod/deployment
kubectl scale deployment/zimprep-api --replicas=0

# Block suspicious IP addresses
kubectl apply -f security/block-ips.yaml

# Enable audit mode (read-only)
kubectl set env deployment/zimprep-api AUDIT_MODE=true
```

### 2. Preserve Forensic Evidence

```bash
# BEFORE making changes, capture state
kubectl logs -l app=zimprep-api --since=24h > breach_logs_$(date +%Y%m%d_%H%M%S).log

# Database snapshot
pg_dump -Fc > breach_db_snapshot_$(date +%Y%m%d_%H%M%S).dump
mongodump --archive=breach_mongo_$(date +%Y%m%d_%H%M%S).gz --gzip

# System state
kubectl get all -A > breach_k8s_state.yaml
ps aux > breach_processes.txt
netstat -an > breach_network.txt
```

### 3. Immediate escalation

**Timeline**: Within 15 minutes of confirmation

**Contacts** (in order):
1. CISO / Security Lead: security@zimprep.com / +263-XXX-XXXX
2. CTO: cto@zimprep.com
3. Legal Counsel: legal@zimprep.com
4. Data Protection Officer: dpo@zimprep.com

## Investigation (Hours 1-4)

### Scope Assessment

```bash
# Identify affected records
python scripts/security/assess_breach.py \
  --start-time="2025-12-23T10:00:00Z" \  --suspicious-ips="1.2.3.4,5.6.7.8" \
  --output=breach_scope.json

# Expected output:
# - Number of records accessed
# - Types of data exposed
# - Attack vector identified
# - Timeline of events
```

### Forensic Analysis

- Review all audit logs with affected trace_ids
- Analyze database query logs
- Check authentication logs
- Review firewall/WAF logs
- Examine application logs

## Regulatory Notification

### Zimbabwe Data Protection Act

**Required if**: Personal data of Zimbabwe citizens compromised

**Timeline**: Within 72 hours of breach detection

**Contact**: Data Protection Authority  
**Method**: Formal written notification + evidence package

**Required Information**:
- Nature of breach
- Categories of data affected
- Approximate number of individuals
- Likely consequences
- Measures taken/proposed
- Contact details for further information

### Exam Board Notification

**Required if**: Exam content or results compromised

**Timeline**: Within 24 hours

**Contact**: exams@zimsec.co.zw

### Affected Students

**Timeline**: "Without undue delay" (interpret as 48-72 hours)

**Method**: Email + in-app notification

**Template**:
> Subject: Important Security Notice
>
> We are writing to inform you of a security incident that may have affected your personal information.
>
> **What Happened**: [Brief description]
> **What Information Was Involved**: [Specific data types]
> **What We're Doing**: [Remediation steps]
> **What You Should Do**: [Recommended actions]
>
> We sincerely apologize for this incident.
>
> For questions: security@zimprep.com

## Recovery (Hours 4-24)

### System Hardening

```bash
# Rotate all secrets
python scripts/security/rotate_all_secrets.py

# Update all user passwords (force reset)
python scripts/security/force_password_reset.py --all

# Patch identified vulnerability
kubectl apply -f security/patch-[vulnerability].yaml

# Re-enable systems with enhanced monitoring
kubectl scale deployment/zimprep-api --replicas=3
kubectl set env deployment/zimprep-api AUDIT_MODE=false
kubectl set env deployment/zimprep-api ENHANCED_LOGGING=true
```

### Verification

```bash
# Penetration test of fixed vulnerability
python scripts/security/pentest_vulnerability.py

# Verify no backdoors
python scripts/security/scan_backdoors.py

# Check all access logs post-recovery
python scripts/security/monitor_post_recovery.py --duration=48h
```

## Post-Incident (Week 1-2)

### Required Actions

1. **Root Cause Analysis**: Technical deep-dive
2. **Impact Assessment**: Final count of affected users/data
3. **Remediation Plan**: Specific technical/process changes
4. **Security Audit**: External 3rd party assessment
5. **User Compensation**: If applicable (fee waivers, credit monitoring)

### Reporting

**Internal Report** (Week 1):
- Executive summary
- Technical timeline
- Root cause
- Lessons learned
- Action items with owners

**Regulatory Report** (as required):
- Use template `/docs/templates/breach_report.docx`
- Include external audit results
- Demonstrate compliance with data protection laws

## Legal Considerations

### Potential Liabilities

- Zimbabwe Data Protection Act: Fines up to 5% of annual turnover
- Contract breach: Customer SLA violations
- Reputational damage
- Class-action lawsuit

### Evidence Preservation

- All logs: Preserve for minimum 7 years
- Forensic snapshots: Store encrypted, access-controlled
- Chain of custody: Document every access to evidence

## Prevention Measures

**Immediate** (Week 1):
- Patch identified vulnerability
- Enhanced monitoring of attack vector
- Security awareness training

**Short-term** (Month 1):
- Penetration testing
- Security code review
- Access control audit

**Long-term** (Quarter 1):
- Implement Zero Trust Architecture
- Enhanced encryption (at rest + in transit)
- Regular security audits
- Bug bounty program

---

## Quick Reference

**IMMEDIATE STEPS**:
1. Isolate systems
2. Preserve evidence
3. Call CISO (+263-XXX-XXXX)
4. Enable AUDIT_MODE
5. Document everything

**CRITICAL TIMELINE**:
- Detection → Containment: < 30 min
- Escalation: < 15 min
- Forensics start: < 1 hour
- Regulatory notification: < 72 hours
- User notification: < 72 hours

**DO NOT**:
- Panic or act without documentation
- Delete any logs
- Communicate publicly before legal review
- Underestimate scope
