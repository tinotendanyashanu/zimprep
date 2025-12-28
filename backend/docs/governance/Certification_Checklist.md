# ZimPrep Certification & Compliance Checklist

**Version:** 1.0  
**Effective Date:** 2025-12-28  
**Classification:** GOVERNANCE VERIFICATION DOCUMENT  
**Purpose:** Pre-launch certification readiness assessment

---

## PURPOSE

This checklist ensures ZimPrep meets **technical, governance, legal, and operational** standards required for safe, defensible, and compliant deployment at national scale.

**Usage:** Complete this checklist before **each rollout phase gate** (Internal Pilot → School Pilot → National Rollout).

---

## CERTIFICATION DOMAINS

The checklist is organized into **8 certification domains**:

1. **AI Governance & Ethics**
2. **Auditability & Transparency**
3. **Data Protection & Privacy**
4. **Assessment Integrity & Fairness**
5. **Operational Resilience**
6. **Regulatory Compliance**
7. **User Rights & Safety**
8. **Business & Legal Readiness**

---

## DOMAIN 1: AI Governance & Ethics

### 1.1 AI Usage Policy ✅/❌

- [ ] **AI Usage Policy published** and accessible to users
- [ ] **AI roles clearly defined** (assists, does not decide)
- [ ] **Human oversight enforced** (validation veto power operational)
- [ ] **Evidence-based operation** (REG mandatory, no hallucination tolerance)
- [ ] **Model versioning tracked** (every AI call logged with model version)
- [ ] **AI timeout enforcement** (<30s per marking operation)
- [ ] **Cost controls operational** (caching, rate limiting, budget caps)

**Evidence Required:**
- Link to published AI Usage Policy
- Code reference: Validation engine with veto power
- Audit log sample showing model version tracking

---

### 1.2 Bias & Fairness Controls ✅/❌

- [ ] **Deterministic marking** (identical inputs = identical outputs)
- [ ] **No demographic bias** (tested across sample populations)
- [ ] **Handwriting neutrality** (marks based on content, not penmanship)
- [ ] **Rubric adherence only** (no subjective AI interpretation)
- [ ] **Bias monitoring dashboard** (automated detection of inconsistencies)

**Evidence Required:**
- Test results: Same answer submitted 10 times = same mark
- Bias audit report (if sample size sufficient)

---

### 1.3 AI Transparency ✅/❌

- [ ] **Students informed** when AI is used (disclosure notices delivered)
- [ ] **Schools informed** (institutional disclosure provided)
- [ ] **Feedback attributed** (clearly labeled as AI-generated)
- [ ] **Evidence citations** (AI outputs reference ZIMSEC sources)
- [ ] **Explainability** (AI reasoning interpretable by educators)

**Evidence Required:**
- Student disclosure notice (published)
- Sample AI feedback showing evidence citations

---

## DOMAIN 2: Auditability & Transparency

### 2.1 Audit Trail Completeness ✅/❌

- [ ] **Every request has unique trace_id** (no gaps in audit log)
- [ ] **Immutable audit collections** (append-only, no edits/deletions)
- [ ] **Full input/output logging** (student answer, AI output, validation result)
- [ ] **Evidence retrieval logged** (which ZIMSEC sources used)
- [ ] **Validation decisions logged** (pass/fail reasons recorded)
- [ ] **Appeals logged** (human review decisions recorded)

**Evidence Required:**
- Sample audit log showing complete trace
- Database configuration proving append-only enforcement

---

### 2.2 Deterministic Replay ✅/❌

- [ ] **Appeals use audit logs** (no AI re-execution)
- [ ] **Historical marks retrievable** (can reproduce decision from logs)
- [ ] **Evidence immutable** (retrieved evidence cannot be altered post-submission)

**Evidence Required:**
- Appeal process documentation
- Test case: Reproduce marking decision from audit log

---

### 2.3 Compliance Reporting ✅/❌

- [ ] **Audit log export functional** (authorized users can export)
- [ ] **Compliance dashboard operational** (validation pass rates, appeal outcomes)
- [ ] **Regulator access prepared** (read-only access to anonymized data)

**Evidence Required:**
- Screenshot of compliance dashboard
- Sample audit log export (anonymized)

---

## DOMAIN 3: Data Protection & Privacy

### 3.1 Data Retention Policy ✅/❌

- [ ] **Retention periods defined** per data type (published policy)
- [ ] **Automated purging operational** (expired data deleted on schedule)
- [ ] **User deletion rights honored** (account deletion functional)
- [ ] **Anonymization enforced** (PII removed after retention period)

**Evidence Required:**
- Published Data Retention Policy
- Scheduled job logs showing automated purging

---

### 3.2 Data Security ✅/❌

- [ ] **Encryption in transit** (TLS 1.2+ enforced)
- [ ] **Encryption at rest** (MongoDB encryption enabled)
- [ ] **Access controls enforced** (RBAC operational, tested)
- [ ] **MFA required** (for admin accounts)
- [ ] **Backup encryption** (backups stored encrypted)

**Evidence Required:**
- SSL/TLS configuration verification
- Database encryption status screenshot
- RBAC test results (unauthorized access blocked)

---

### 3.3 Third-Party Data Processing ✅/❌

- [ ] **Data Processing Agreements signed** (OpenAI, MongoDB Atlas)
- [ ] **No training on student data** (contractually prohibited)
- [ ] **Data residency compliant** (Zimbabwe regulations, if applicable)
- [ ] **Vendor audit rights** (ZimPrep can audit vendor practices)

**Evidence Required:**
- Signed DPAs (redacted for confidentiality)
- Vendor data handling documentation

---

### 3.4 Data Subject Rights ✅/❌

- [ ] **Right to access** (data export functional)
- [ ] **Right to rectification** (profile updates functional)
- [ ] **Right to deletion** (account deletion works, anonymization verified)
- [ ] **Right to portability** (export in machine-readable format)
- [ ] **Right to object** (opt-out options available)

**Evidence Required:**
- Test: Request data export, verify contents
- Test: Delete account, verify data purged/anonymized

---

## DOMAIN 4: Assessment Integrity & Fairness

### 4.1 Marking Accuracy ✅/❌

- [ ] **AI accuracy validated** (>85% agreement with human examiners in pilot)
- [ ] **Validation pass rate acceptable** (>95% of AI outputs pass validation)
- [ ] **Appeal overturn rate low** (<10% of appealed marks overturned)
- [ ] **No systematic errors** (no topics consistently marked wrong)

**Evidence Required:**
- Accuracy study results (AI vs. human expert comparison)
- Validation and appeal metrics dashboard

---

### 4.2 Rubric Compliance ✅/❌

- [ ] **ZIMSEC marking schemes ingested** (vector store populated)
- [ ] **Evidence retrieval functional** (AI retrieves correct schemes)
- [ ] **Rubric enforcement tested** (AI cannot award marks beyond rubric)
- [ ] **Evidence citations verified** (AI outputs cite correct sources)

**Evidence Required:**
- Vector store population logs
- Sample AI output with evidence citations

---

### 4.3 Appeals Process ✅/❌

- [ ] **Appeals Policy published** (students know their rights)
- [ ] **Human review operational** (trained reviewers available)
- [ ] **30-day appeal window enforced** (late appeals rejected)
- [ ] **Decision explanations provided** (students receive reasoning)
- [ ] **Escalation path defined** (senior review available)

**Evidence Required:**
- Published Appeals Policy
- Sample appeal resolution (anonymized)

---

## DOMAIN 5: Operational Resilience

### 5.1 System Reliability ✅/❌

- [ ] **Uptime >99%** (during pilot phase)
- [ ] **AI timeout handling** (requests >30s fail gracefully)
- [ ] **Retry logic operational** (transient failures retried up to 2x)
- [ ] **Fallback to manual review** (if AI repeatedly fails)
- [ ] **Load testing completed** (system handles expected peak load)

**Evidence Required:**
- Uptime monitoring dashboard
- Load test results report

---

### 5.2 Error Handling ✅/❌

- [ ] **Graceful degradation** (partial outages don't crash system)
- [ ] **User-friendly error messages** (no raw stack traces shown)
- [ ] **Error logging operational** (errors tracked, categorized)
- [ ] **Incident response tested** (engineering knows how to respond)

**Evidence Required:**
- Error handling test results
- Incident response runbook (published)

---

### 5.3 Connectivity Resilience ✅/❌

- [ ] **Offline buffering operational** (Phase 6 - brief disconnects handled)
- [ ] **Sync upon reconnection** (buffered answers synced safely)
- [ ] **Connectivity status visible** (students know if online/offline)
- [ ] **Server authority preserved** (no client-side mark calculation)

**Evidence Required:**
- Offline buffering test results (Phase 6 validation)
- Connectivity state service logs

---

## DOMAIN 6: Regulatory Compliance

### 6.1 ZIMSEC Alignment ✅/❌

- [ ] **ZIMSEC marking schemes used exclusively** (no custom rubrics)
- [ ] **ZIMSEC standards followed** (examiner-style feedback)
- [ ] **No official endorsement claimed** (messaging clear: independent prep tool)
- [ ] **ZIMSEC liaison established** (informal or formal, if applicable)

**Evidence Required:**
- Vector store evidence source list (all ZIMSEC)
- Marketing materials review (no false claims)

---

### 6.2 Data Protection Laws ✅/❌

- [ ] **Zimbabwe data protection compliance** (legal review completed)
- [ ] **GDPR-style principles applied** (even if not in EU)
- [ ] **Cross-border transfer safeguards** (SCCs or equivalent, if applicable)
- [ ] **Breach notification procedures** (72-hour window defined)

**Evidence Required:**
- Legal compliance memo
- Data protection impact assessment (DPIA)

---

### 6.3 Educational Standards ✅/❌

- [ ] **No misleading marketing** ("guaranteed results" language prohibited)
- [ ] **Practice-only positioning** (clear that ZimPrep is not official exam)
- [ ] **Parental consent** (for students under 18, if required)
- [ ] **Accessibility standards** (basic WCAG compliance for web UI)

**Evidence Required:**
- Marketing copy review
- Parental consent form (if applicable)

---

## DOMAIN 7: User Rights & Safety

### 7.1 Student Rights ✅/❌

- [ ] **AI disclosure delivered** (students informed when AI used)
- [ ] **Feedback explained** (students understand marks)
- [ ] **Appeal rights accessible** (clear UI path to appeal)
- [ ] **Data access granted** (students can export their data)
- [ ] **No harmful predictions** (no "you will fail" language)

**Evidence Required:**
- Student disclosure notice delivery log
- Feedback policy compliance check (no prohibited language)

---

### 7.2 Institutional Rights ✅/❌

- [ ] **School data ownership respected** (institutional accounts managed properly)
- [ ] **Cohort analytics available** (schools see aggregate performance)
- [ ] **Configuration controls operational** (schools can set feature flags)
- [ ] **Audit access granted** (schools can inspect student data)

**Evidence Required:**
- Institutional dashboard screenshot
- Feature flag configuration test

---

### 7.3 Safety & Wellbeing ✅/❌

- [ ] **No student harm reported** (during pilot phases)
- [ ] **Constructive feedback only** (no demoralizing language)
- [ ] **Mental health resources** (support links if student distressed)
- [ ] **Abuse reporting mechanism** (students can report issues)

**Evidence Required:**
- Feedback policy enforcement test
- Support resource links (in UI)

---

## DOMAIN 8: Business & Legal Readiness

### 8.1 Legal Documentation ✅/❌

- [ ] **Terms of Service published** (legally binding)
- [ ] **Privacy Policy published** (GDPR-compliant)
- [ ] **Refund policy defined** (for Premium subscriptions)
- [ ] **Liability disclaimers** (practice tool, not official exam)
- [ ] **Intellectual property protected** (ZimPrep brand, codebase)

**Evidence Required:**
- Published Terms of Service
- Published Privacy Policy

---

### 8.2 Billing & Subscriptions ✅/❌

- [ ] **Payment processing secure** (PCI-compliant provider used)
- [ ] **Subscription management functional** (users can upgrade/downgrade)
- [ ] **Billing disputes handled** (refund process defined)
- [ ] **Free tier enforced** (rate limits operational)

**Evidence Required:**
- Payment provider integration documentation
- Subscription flow test results

---

### 8.3 Support & Documentation ✅/❌

- [ ] **User documentation published** (help center, FAQs)
- [ ] **Support contact available** (email, in-app support)
- [ ] **Response time targets defined** (SLA for support tickets)
- [ ] **Teacher training materials** (for institutional deployments)

**Evidence Required:**
- Help center link
- Support ticket response time metrics

---

## CERTIFICATION GATES

### Gate 1: Internal Pilot Certification

**Minimum Required Domains:** 1-5 (AI Governance, Auditability, Data Protection, Assessment Integrity, Operational Resilience)

**Acceptable Completion:** 80% of items in Domains 1-5 must be ✅

**Decision:** Governance Board approves progression to School Pilot

---

### Gate 2: School Pilot Certification

**Minimum Required Domains:** 1-7 (add User Rights & Safety)

**Acceptable Completion:** 90% of items in Domains 1-7 must be ✅

**Decision:** Governance Board + External Advisors approve progression to National Rollout

---

### Gate 3: National Rollout Certification

**Minimum Required Domains:** All 8 domains

**Acceptable Completion:** 95% of items in all domains must be ✅

**Decision:** Full Governance Board + Legal + Regulator Liaison (if applicable) approve launch

---

## CERTIFICATION WORKFLOW

### Pre-Certification

1. **Self-assessment:** Engineering/Product complete checklist
2. **Evidence collection:** Gather all required documentation
3. **Gap analysis:** Identify incomplete items

### Certification Review

1. **Governance Board review:** Board validates completeness
2. **External audit** (optional): Third-party verification
3. **Remediation:** Fix identified gaps
4. **Re-review:** Validate remediation

### Post-Certification

1. **Document approval:** Board signs off on phase progression
2. **User notification:** Inform stakeholders of launch
3. **Continuous monitoring:** Ongoing compliance tracking

---

## AUDIT TRAIL

| **Phase**              | **Date Certified** | **Approver**            | **Completion %** | **Notes**          |
|------------------------|---------------------|-------------------------|------------------|--------------------|
| Internal Pilot         | YYYY-MM-DD          | Governance Board        | XX%              |                    |
| School Pilot           | YYYY-MM-DD          | Governance Board + Advisors | XX%         |                    |
| National Rollout       | YYYY-MM-DD          | Full Board + Legal      | XX%              |                    |

---

## REGULATORY SUBMISSION PACKAGE

For regulatory review (if required), prepare the following package:

1. **Completed Certification Checklist** (this document)
2. **AI Usage Policy** (with evidence of enforcement)
3. **Data Retention Policy** (with audit logs)
4. **Audit Log Samples** (anonymized)
5. **Accuracy Study Results** (AI vs. human comparison)
6. **Appeals Process Documentation** (with sample resolutions)
7. **Incident Response Plan**
8. **Legal Compliance Memo** (from counsel)

---

## CONTINUOUS COMPLIANCE

Certification is **not one-time**:

- **Quarterly re-certification:** Re-run checklist every 3 months
- **Post-incident re-certification:** After any P0/P1 incident
- **Post-policy change:** After any governance policy update
- **Regulatory audit:** As requested by authorities

---

## Policy Governance

### Ownership

- **Owner:** ZimPrep Governance Board
- **Approvers:** Legal, Engineering, Product
- **Reviewers:** External Auditors (if engaged)

### Amendment

Checklist updated after:
- **New regulatory requirements** (add compliance items)
- **Incident learnings** (add preventive checks)
- **Technology changes** (e.g., new AI model requires new validation)

---

## Document Control

| **Version** | **Date**       | **Author**              | **Changes**            |
|-------------|----------------|-------------------------|------------------------|
| 1.0         | 2025-12-28     | ZimPrep Governance Team | Initial checklist      |

---

**Related Policies:**  
- [AI Usage Policy](AI_Usage_Policy.md)  
- [Data Retention Policy](Data_Retention_Policy.md)  
- [Rollout Playbook](Rollout_Playbook.md)  
- [Go-Live Decision Gate](Go_Live_Gate.md)

---

**END OF CERTIFICATION & COMPLIANCE CHECKLIST**
