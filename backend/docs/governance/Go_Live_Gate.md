# ZimPrep Go-Live Decision Gate

**Version:** 1.0  
**Effective Date:** 2025-12-28  
**Classification:** AUTHORITATIVE GOVERNANCE DOCUMENT  
**Purpose:** Define criteria and process for launch authorization

---

## 1. Purpose

This document defines the **Go/No-Go decision framework** for ZimPrep deployment, ensuring launches are **safe, compliant, and defensible**.

**Scope:** Applies to all rollout phase transitions (Internal Pilot → School Pilot → National Rollout).

---

## 2. Core Principle

> **No rollout phase proceeds without explicit governance approval based on objective criteria.**

**Decision Authority:** ZimPrep Governance Board (composition defined below).

---

## 3. Decision Framework

### 3.1 Decision Inputs

The Go/No-Go decision is based on:

1. ✅ **Technical Readiness** (does the system work?)
2. ✅ **Quality Metrics** (is AI accurate and safe?)
3. ✅ **Governance Compliance** (are policies enforced?)
4. ✅ **User Validation** (do users trust and value it?)
5. ✅ **Operational Readiness** (can we support it?)
6. ✅ **Regulatory Clearance** (are we legally compliant?)

### 3.2 Decision Outcomes

| **Decision** | **Meaning**                                  | **Next Steps**                          |
|--------------|----------------------------------------------|-----------------------------------------|
| **GO**       | All criteria met, proceed to next phase     | Launch with monitoring                  |
| **NO-GO**    | Critical criteria unmet, cannot proceed      | Remediate gaps, re-assess in 2-4 weeks  |
| **CONDITIONAL GO** | Most criteria met, minor gaps acceptable | Launch with mitigation plan + close monitoring |

---

## 4. Gate 1: Internal Pilot to School Pilot

### 4.1 Decision Criteria

| **Category**            | **Criterion**                                  | **Target**       | **Measurement**                          | **Mandatory?** |
|-------------------------|------------------------------------------------|------------------|------------------------------------------|----------------|
| **Technical**           | AI marking operational                        | 100%             | All engines functional                   | YES            |
| **Technical**           | Validation engine enforces rules              | 100%             | Test suite passes                        | YES            |
| **Technical**           | Audit trail complete                          | 100%             | All requests logged                      | YES            |
| **Quality**             | AI accuracy vs. human                         | >85%             | Expert comparison study                  | YES            |
| **Quality**             | Validation pass rate                          | >95%             | Automated tracking                       | YES            |
| **Quality**             | Appeal overturn rate                          | <10%             | Appeals resolved                         | NO (advisory)  |
| **Governance**          | AI Usage Policy published                     | 100%             | Policy accessible to users               | YES            |
| **Governance**          | Data Retention Policy published               | 100%             | Policy accessible to users               | YES            |
| **Governance**          | Feedback Policy enforced                      | 100%             | No prohibited language detected          | YES            |
| **User Validation**     | User satisfaction (NPS)                       | >50              | Survey responses                         | NO (advisory)  |
| **User Validation**     | Users recommend to others                     | >60%             | Survey responses                         | NO (advisory)  |
| **Operational**         | System uptime                                 | >99%             | Monitoring dashboard                     | YES            |
| **Operational**         | No critical bugs outstanding                  | 0                | Issue tracker                            | YES            |
| **Regulatory**          | Data protection compliance review complete    | 100%             | Legal memo                               | YES            |

### 4.2 Go/No-Go Decision

**GO if:**
- All **mandatory** criteria met
- At least 50% of **advisory** criteria met
- No critical incidents unresolved

**NO-GO if:**
- Any mandatory criterion UNMET
- Critical security or privacy issue outstanding

**CONDITIONAL GO if:**
- All mandatory criteria met
- <50% of advisory criteria met
- **Mitigation plan** approved for gaps

---

### 4.3 Mitigation Plan (Conditional GO)

If **Conditional GO**, must define:

1. **What gaps exist** (e.g., user satisfaction only 45%)
2. **Why acceptable** (e.g., small sample size, feedback mostly positive)
3. **Mitigation actions** (e.g., extended pilot, user interviews)
4. **Re-assessment trigger** (e.g., re-check after 4 weeks)

**Approval:** Governance Board must approve mitigation plan.

---

## 5. Gate 2: School Pilot to National Rollout

### 5.1 Decision Criteria

| **Category**            | **Criterion**                                  | **Target**       | **Measurement**                          | **Mandatory?** |
|-------------------------|------------------------------------------------|------------------|------------------------------------------|----------------|
| **Technical**           | All Gate 1 criteria still met                 | 100%             | Re-verification                          | YES            |
| **Technical**           | Infrastructure scaled for national load       | 100%             | Load testing results                     | YES            |
| **Quality**             | AI accuracy vs. human                         | >90%             | Expanded expert study                    | YES            |
| **Quality**             | Validation pass rate                          | >97%             | Automated tracking (larger sample)       | YES            |
| **Quality**             | Appeal overturn rate                          | <8%              | Appeals resolved                         | YES            |
| **Governance**          | All Phase 7 policies published                | 100%             | Policy portal accessible                 | YES            |
| **Governance**          | Feature Governance Matrix enforced            | 100%             | Entitlement checks operational           | YES            |
| **Governance**          | Certification Checklist 90% complete          | >90%             | Self-assessment + audit                  | YES            |
| **User Validation**     | Teacher satisfaction                          | >70% positive    | End-of-pilot survey                      | YES            |
| **User Validation**     | Student engagement                            | >60% weekly use  | Active user analytics                    | YES            |
| **User Validation**     | School endorsements                           | >80% of schools  | Would recommend ZimPrep                  | YES            |
| **Operational**         | System uptime                                 | >99.5%           | Monitoring dashboard                     | YES            |
| **Operational**         | Support team ready                            | 100%             | Support SLA defined, staff trained       | YES            |
| **Operational**         | Billing system operational                    | 100%             | Payments processed successfully          | YES (if monetized) |
| **Regulatory**          | ZIMSEC liaison consulted                      | 100%             | Meeting minutes / correspondence         | NO (advisory)  |
| **Regulatory**          | No regulatory objections                      | 0 objections     | Legal review + stakeholder feedback      | YES            |

### 5.2 Go/No-Go Decision

**GO if:**
- All **mandatory** criteria met
- At least 70% of **advisory** criteria met
- **Case studies** demonstrate student benefit

**NO-GO if:**
- Any mandatory criterion UNMET
- Teacher satisfaction <60%
- Regulatory concerns raised

**CONDITIONAL GO if:**
- All mandatory criteria met except 1-2 (with approved mitigation)
- Strong mitigation plan for gaps

---

## 6. Governance Board Composition

### 6.1 Voting Members

| **Role**                    | **Responsibility**                          | **Vote Weight** |
|-----------------------------|---------------------------------------------|-----------------|
| **CEO / Founder**           | Strategic vision, final accountability      | 1               |
| **CTO / Engineering Lead**  | Technical readiness, system safety          | 1               |
| **Product Lead**            | User validation, feature readiness          | 1               |
| **Legal Counsel**           | Regulatory compliance, risk mitigation      | 1               |
| **Education Advisor**       | ZIMSEC alignment, pedagogical soundness     | 1               |

**Decision Rule:** Majority vote required (3/5 or greater for GO).

---

### 6.2 Advisory Members (Non-Voting)

| **Role**                    | **Responsibility**                          |
|-----------------------------|---------------------------------------------|
| **School Partners**         | User perspective, institutional needs       |
| **Student Representatives** | Student experience, usability feedback      |
| **External Auditor**        | Independent compliance verification         |

**Advisors provide input** but do not vote on Go/No-Go.

---

## 7. Decision Process

### 7.1 Pre-Decision (T-2 weeks before gate)

1. **Self-assessment:** Engineering/Product complete [Certification Checklist](Certification_Checklist.md)
2. **Evidence collection:** Gather metrics, user feedback, test results
3. **Draft decision packet:** Summarize criteria status (GO/NO-GO/CONDITIONAL)

### 7.2 Decision Review (T-1 week)

1. **Governance Board meeting:** Review decision packet
2. **Q&A:** Board asks clarifying questions
3. **Advisory input:** Non-voting members provide feedback
4. **Mitigation discussion:** If Conditional GO, debate mitigation plan

### 7.3 Decision (T-0)

1. **Vote:** Each voting member casts GO / NO-GO / CONDITIONAL GO
2. **Tally:** Majority required for GO
3. **Record:** Decision logged with rationale
4. **Notify stakeholders:** Communicate decision within 24 hours

### 7.4 Post-Decision

**If GO:**
- **Launch plan activated** (per [Rollout Playbook](Rollout_Playbook.md))
- **Monitoring intensified** (daily dashboards for first 2 weeks)
- **Retrospective scheduled** (30 days post-launch)

**If NO-GO:**
- **Gap remediation plan** created (with timeline)
- **Re-assessment scheduled** (2-4 weeks)
- **Stakeholders notified** (transparent communication)

**If CONDITIONAL GO:**
- **Mitigation plan activated**
- **Enhanced monitoring** (daily check-ins)
- **Re-assessment trigger defined** (e.g., 4 weeks or after 100 users)

---

## 8. Emergency Rollback Authority

### 8.1 Rollback Triggers

Post-launch, **immediate rollback** authorized if:

- 🚨 **Data breach** affecting >100 users
- 🚨 **AI accuracy drops <70%** (systemic failure)
- 🚨 **System uptime <90%** for >24 hours
- 🚨 **Regulatory injunction** (legal order to cease operations)
- 🚨 **Student harm reported** (incorrect marks causing severe distress)

### 8.2 Rollback Decision Authority

**Emergency rollback** can be authorized by:
- **CEO + CTO** (joint decision, no board vote required)
- **Legal Counsel** (unilateral if legal/regulatory threat)

**Process:**
1. **Immediate containment** (disable affected features or entire platform)
2. **User notification** (within 4 hours via email + in-app)
3. **Root cause investigation** (within 48 hours)
4. **Governance Board briefing** (within 72 hours)

---

## 9. Rollback Procedures

### 9.1 Partial Rollback (Feature-Level)

**Scenario:** Specific feature causing issues (e.g., handwriting upload)

**Action:**
1. **Feature flag OFF** (disable problematic feature)
2. **User notification** (feature temporarily unavailable)
3. **Fix and re-enable** (after root cause resolved)

**Authority:** CTO or Product Lead

---

### 9.2 Full Rollback (Phase-Level)

**Scenario:** Entire rollout phase unsustainable

**Action:**
1. **Revert to previous phase** (e.g., National → School Pilot)
2. **Disable new user signups** (limit to prior user base)
3. **Communication plan** (transparent explanation to users)
4. **Re-certification** (must pass gate again before re-launch)

**Authority:** CEO + Governance Board majority vote

---

## 10. Continuous Go/No-Go Monitoring

### 10.1 Post-Launch Monitoring (Ongoing)

Even after **GO** decision, continuous monitoring ensures sustained compliance:

| **Metric**                  | **Threshold**          | **Action if Breached**                     |
|-----------------------------|------------------------|--------------------------------------------|
| AI accuracy                 | <85%                   | Engineering investigation, model review    |
| Validation pass rate        | <90%                   | Validation rules review                    |
| System uptime               | <99%                   | Infrastructure scaling, incident review    |
| Appeal overturn rate        | >15%                   | AI tuning, appeals process review          |
| User satisfaction (NPS)     | <30                    | UX review, feature prioritization          |

**Review Frequency:** Weekly for first month, then monthly.

---

### 10.2 Quarterly Re-Certification

Every **3 months**, re-run [Certification Checklist](Certification_Checklist.md):
- Verify criteria still met
- Identify new gaps
- Update policies as needed

**Decision:** Governance Board confirms continued operation or mandates remediation.

---

## 11. Transparent Communication

### 11.1 Internal Communication

**Governance Board decisions** communicated to:
- **Engineering team** (within 24 hours)
- **All employees** (summary at all-hands)

### 11.2 External Communication

**Stakeholder notifications:**

| **Stakeholder**       | **Timing**         | **Channel**                              |
|-----------------------|--------------------|------------------------------------------|
| Pilot users           | Within 24 hours    | Email + in-app notification              |
| School admins         | Within 48 hours    | Email + phone call (if applicable)       |
| Public (if operational)| Within 1 week     | Blog post, social media                  |

**Transparency:** If NO-GO, explain **why** (without exposing security details).

---

## 12. Decision Audit Trail

### 12.1 Record Keeping

Every Go/No-Go decision logged with:

- **Date of decision**
- **Phase/Gate** (e.g., Gate 1: Internal Pilot → School Pilot)
- **Decision outcome** (GO / NO-GO / CONDITIONAL GO)
- **Vote tally** (individual board member votes)
- **Rationale** (why decision was made)
- **Evidence reviewed** (links to certification checklist, metrics)
- **Mitigation plan** (if Conditional GO)

**Storage:** Governance Board meeting minutes (confidential)

---

### 12.2 Historical Decisions

| **Gate**               | **Date**       | **Decision** | **Vote** | **Notes**                          |
|------------------------|----------------|--------------|----------|------------------------------------|
| Gate 1: School Pilot   | YYYY-MM-DD     | GO / NO-GO   | X/5      | (rationale summary)                |
| Gate 2: National Rollout| YYYY-MM-DD    | GO / NO-GO   | X/5      | (rationale summary)                |

---

## 13. External Audit (Optional)

For **critical gates** (e.g., National Rollout), consider **external audit**:

### 13.1 Auditor Role

- **Independent verification** of certification checklist completion
- **Technical assessment** (penetration testing, code review)
- **Compliance review** (data protection, educational standards)

### 13.2 Auditor Report

- **Findings:** Gaps or risks identified
- **Recommendations:** Remediation suggestions
- **Certification opinion:** "Ready to launch" or "Not ready"

**Board Decision:** External audit report is **advisory input**, not binding.

---

## 14. Policy Governance

### 14.1 Ownership

- **Owner:** ZimPrep Governance Board (collectively)
- **Approvers:** All voting board members
- **Reviewers:** Legal Counsel, External Auditors

### 14.2 Amendment

Go-Live Gate criteria updated when:
- **New risks identified** (add new criteria)
- **Regulatory requirements change** (adjust compliance criteria)
- **Operational learnings** (refine thresholds based on experience)

**Amendment Process:** Requires unanimous Governance Board approval.

---

## Document Control

| **Version** | **Date**       | **Author**              | **Changes**            |
|-------------|----------------|-------------------------|------------------------|
| 1.0         | 2025-12-28     | ZimPrep Governance Team | Initial gate framework |

---

**Related Policies:**  
- [Rollout Playbook](Rollout_Playbook.md)  
- [Certification Checklist](Certification_Checklist.md)  
- [Feature Governance Matrix](Feature_Governance_Matrix.md)

---

**END OF GO-LIVE DECISION GATE**
