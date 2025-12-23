# RUNBOOK: Appeal Dispute Escalation

**Phase B5: Incident Response**  
**Severity**: MEDIUM-HIGH  
**Last Updated**: 2025-12-23

## Overview

Handles situations where students dispute appeal reconstruction results and escalate to legal/regulatory review, requiring comprehensive evidence collection.

## Detection Signals

- Formal appeal dispute lodged through support
- Regulatory inquiry from exam board
- Legal notice received
-Discrepancy reported in reconstruction

## Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| Standard | Student questions results | 48 hours |
| Escalated | Formal dispute filed | 24 hours |
| Legal | Legal/regulatory involvement | 4 hours |

## Immediate Actions (Legal Level)

### 1. Preserve Evidence

```bash
# CRITICAL: Enable audit mode immediately
kubectl set env deployment/zimprep-api AUDIT_MODE=true

# Lock all related records
python scripts/appeals/lock_records.py --appeal-id=APPEAL-20251223-001

# Generate forensic evidence package
python scripts/appeals/generate_evidence.py \
  --appeal-id=APPEAL-20251223-001 \
  --include-audit-trail \
  --include-ai-prompts \
  --include-timestamps \
  --output=evidence_package.zip
```

### 2. Notify Legal Team

**Contact**: legal@zimprep.com  
**Timeline**: Within 1 hour of legal notice

**Evidence Package Includes**:
- Complete audit trail with all trace_ids
- Original submission (immutable)
- AI reasoning outputs
- Marking rubric used
- Final grade calculation
- Appeal reconstruction log
- All timestamps and signatures

### 3. Verification Checklist

```bash
# Verify reconstruction correctness
python scripts/appeals/verify_reconstruction.py \
  --appeal-id=APPEAL-20251223-001 \
  --compare-original

# Check for data integrity
python scripts/appeals/check_integrity.py \
  --appeal-id=APPEAL-20251223-001

# Validate hash chains
python scripts/appeals/validate_hashes.py \
  --submission-id=SUB-20251220-12345
```

## Response Timeline

### Hour 1: Evidence Collection
- Collect all audit records
- Generate evidence package
- Notify legal team

### Hour 2-4: Technical Analysis
- Reproduce appeal reconstruction
- Verify correctness
- Identify any discrepancies

### Hour 4-24: Legal Preparation
- Prepare technical summary (non-technical language)
- Create timeline of events
- Document all system behavior

### 24-48 hours: Response
- Provide formal response to inquiry
- Submit evidence package
- Technical expert availability

## Evidence Package Structure

```
evidence_package/
├── summary.pdf                 # Executive summary
├── audit_trail/
│   ├── submission_record.json
│   ├── reasoning_output.json
│   ├── appeal_reconstruction.json
│   └── all_traces.log
├── technical_details/
│   ├── ai_prompts.txt
│   ├── rubric_used.json
│   ├── calculations.xlsx
│   └── system_config.json
└── compliance/
    ├── integrity_checks.pdf
    ├── hash_verification.txt
    └── regulatory_compliance.pdf
```

## Regulatory Reporting

### Zimbabwe Exam Board

**Required if**: Grade change >10% or formal dispute

**Report Template**: `/docs/templates/appeal_dispute_report.docx`

**Submission**:
- Email: appeals@zimsec.co.zw  
- Deadline: 72 hours from notice
- Include: Evidence package + technical summary

## Communication Templates

### To Student (Standard Dispute)

> Subject: Appeal Dispute Review - [APPEAL-ID]
>
> We have received your dispute regarding appeal [ID]. Our technical team is reviewing:
> - Original submission integrity
> - Reconstruction accuracy
> - Calculation correctness
>
> Expected response: Within 48 hours
> Reference: [APPEAL-ID]

### To Regulatory Body

> Subject: Appeal Dispute Evidence - [STUDENT-ID]
>
> Per your inquiry [REF-NUMBER], attached is the complete technical evidence package for student [STUDENT-ID].
>
> Package includes: [list]
>
> Technical contact: [NAME], [EMAIL], [PHONE]

## Post-Resolution

```bash
# Document outcome
python scripts/appeals/record_outcome.py \
  --appeal-id=APPEAL-20251223-001 \
  --outcome="upheld|revised|rejected" \
  --notes="..."

# Disable audit mode if no other incidents
kubectl set env deployment/zimprep-api AUDIT_MODE=false

# Generate lessons learned
python scripts/appeals/generate_report.py \
  --appeal-id=APPEAL-20251223-001
```

## Prevention

- Quarterly audit of appeal reconstruction accuracy
- Student communication improvements
- Clear appeal process documentation
- Regular legal team training on technical systems

---

**Critical Contacts**:
- Legal Team: legal@zimprep.com / +263-XXX-XXXX
- Compliance Officer: compliance@zimprep.com
- Exam Board Liaison: liaison@zimsec.co.zw
