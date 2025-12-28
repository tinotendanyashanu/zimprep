# ZimPrep Feature Governance Matrix

**Version:** 1.0  
**Effective Date:** 2025-12-28  
**Classification:** AUTHORITATIVE GOVERNANCE DOCUMENT  
**Review Cycle:** Quarterly or upon feature addition

---

## 1. Purpose and Scope

This matrix defines **which users can access which features**, establishes tier-based entitlements, and ensures **backend enforcement** of feature boundaries.

**Core Principle:** No feature exists unless policy explicitly allows it.

**Scope:** All ZimPrep features across web, mobile, and API interfaces.

---

## 2. User Roles

### 2.1 Role Definitions

| **Role**              | **Description**                                                                 | **Authentication**       |
|-----------------------|---------------------------------------------------------------------------------|--------------------------|
| **Guest**             | Unauthenticated visitor (limited preview access)                                | None                     |
| **Student (Free)**    | Individual student with free account                                            | Email + password         |
| **Student (Premium)** | Individual student with paid subscription                                       | Email + password         |
| **Teacher**           | Educator with access to student analytics (institutional or individual)         | Email + password + verification |
| **School Admin**      | Administrator managing institutional deployment                                 | Email + password + MFA   |
| **Regulator**         | External auditor with read-only compliance access (future)                      | Email + password + MFA   |
| **ZimPrep Admin**     | Internal platform administrator (engineering, support)                          | Email + password + MFA   |

---

## 3. Feature Exposure Matrix

### 3.1 Core Assessment Features

| **Feature**                     | **Guest** | **Student (Free)** | **Student (Premium)** | **Teacher** | **School Admin** | **Regulator** | **ZimPrep Admin** |
|---------------------------------|-----------|--------------------|------------------------|-------------|------------------|---------------|-------------------|
| **Practice Exam Submission**    | ❌        | ✅ (5/day)         | ✅ (Unlimited)         | ❌          | ❌               | ❌            | ✅                |
| **AI Marking & Feedback**       | ❌        | ✅                 | ✅                     | ❌          | ❌               | ❌            | ✅                |
| **Handwriting Upload**          | ❌        | ❌                 | ✅                     | ❌          | ❌               | ❌            | ✅                |
| **View Marking Schemes**        | ❌        | ✅ (after attempt) | ✅ (any time)          | ✅          | ✅               | ❌            | ✅                |
| **Appeal Marks**                | ❌        | ✅                 | ✅                     | ❌          | ✅ (on behalf)   | ❌            | ✅                |

**Notes:**
- **Free students** limited to 5 submissions/day (backend enforced via rate limiting)
- **Handwriting upload** requires Premium (OCR costs)
- **Appeals** free for all authenticated users

---

### 3.2 Analytics & Reporting Features

| **Feature**                     | **Guest** | **Student (Free)** | **Student (Premium)** | **Teacher** | **School Admin** | **Regulator** | **ZimPrep Admin** |
|---------------------------------|-----------|--------------------|------------------------|-------------|------------------|---------------|-------------------|
| **Topic Mastery Dashboard**     | ❌        | ✅ (basic)         | ✅ (detailed)          | ✅ (students only) | ✅ (all students) | ❌         | ✅                |
| **Progress Trends (graphs)**    | ❌        | ❌                 | ✅                     | ✅          | ✅               | ❌            | ✅                |
| **Weakness Recommendations**    | ❌        | ✅ (3 topics)      | ✅ (all topics)        | ✅          | ✅               | ❌            | ✅                |
| **Cohort Analytics**            | ❌        | ❌                 | ❌                     | ✅          | ✅               | ✅            | ✅                |
| **Institutional Reports**       | ❌        | ❌                 | ❌                     | ❌          | ✅               | ✅            | ✅                |

**Notes:**
- **Free students** see topic mastery but no trend graphs
- **Teachers** see analytics only for students in their class
- **Regulators** see anonymized cohort data only

---

### 3.3 Resource & Practice Features

| **Feature**                     | **Guest** | **Student (Free)** | **Student (Premium)** | **Teacher** | **School Admin** | **Regulator** | **ZimPrep Admin** |
|---------------------------------|-----------|--------------------|------------------------|-------------|------------------|---------------|-------------------|
| **Practice Question Access**    | ❌        | ✅ (limited)       | ✅ (full library)      | ✅          | ✅               | ❌            | ✅                |
| **Topic-Based Practice**        | ❌        | ❌                 | ✅                     | ✅          | ✅               | ❌            | ✅                |
| **Timed Exam Mode**             | ❌        | ✅                 | ✅                     | ❌          | ❌               | ❌            | ✅                |
| **Unlimited Retakes**           | ❌        | ❌ (1/question)    | ✅                     | ❌          | ❌               | ❌            | ✅                |

**Notes:**
- **Free students** can attempt each question **once** per day
- **Premium students** unlimited retakes

---

### 3.4 Audit & Compliance Features

| **Feature**                     | **Guest** | **Student (Free)** | **Student (Premium)** | **Teacher** | **School Admin** | **Regulator** | **ZimPrep Admin** |
|---------------------------------|-----------|--------------------|------------------------|-------------|------------------|---------------|-------------------|
| **View Own Audit Logs**         | ❌        | ✅                 | ✅                     | ❌          | ❌               | ❌            | ✅                |
| **Export Audit Logs**           | ❌        | ❌                 | ✅                     | ❌          | ✅ (institutional)| ✅           | ✅                |
| **Compliance Reporting**        | ❌        | ❌                 | ❌                     | ❌          | ✅               | ✅            | ✅                |
| **AI Usage Transparency**       | ❌        | ✅ (own data)      | ✅ (own data)          | ✅ (students) | ✅ (all)        | ✅            | ✅                |

**Notes:**
- **Students** can view audit logs for their own submissions
- **Regulators** can audit compliance without student PII

---

### 3.5 Administrative Features

| **Feature**                     | **Guest** | **Student (Free)** | **Student (Premium)** | **Teacher** | **School Admin** | **Regulator** | **ZimPrep Admin** |
|---------------------------------|-----------|--------------------|------------------------|-------------|------------------|---------------|-------------------|
| **Manage Student Accounts**     | ❌        | ❌                 | ❌                     | ✅ (own class) | ✅ (all students) | ❌         | ✅                |
| **Configure Feature Flags**     | ❌        | ❌                 | ❌                     | ❌          | ✅               | ❌            | ✅                |
| **Set AI Cost Limits**          | ❌        | ❌                 | ❌                     | ❌          | ✅               | ❌            | ✅                |
| **Access Support Dashboard**    | ❌        | ❌                 | ❌                     | ❌          | ✅               | ❌            | ✅                |
| **Modify Validation Rules**     | ❌        | ❌                 | ❌                     | ❌          | ❌               | ❌            | ✅                |

**Notes:**
- **School admins** can configure features for their institution
- **Only ZimPrep admins** can modify core validation rules (safety-critical)

---

## 4. Tier-Based Entitlements

### 4.1 Free Tier

**Access:**
- 5 practice exam submissions per day
- Basic AI marking and feedback
- Topic mastery dashboard (basic)
- 1 retake per question per day
- Appeal rights

**Limitations:**
- No handwriting upload
- No trend graphs
- No unlimited practice

**Cost:** $0

---

### 4.2 Premium Tier (Individual)

**Access:**
- **All Free Tier features**
- Unlimited practice exam submissions
- Handwriting upload (OCR support)
- Topic mastery dashboard (detailed)
- Progress trends and analytics
- Topic-based practice
- Unlimited retakes
- Audit log export

**Cost:** $5-10/month (TBD based on market research)

---

### 4.3 Institutional Tier (Schools)

**Access:**
- **All Premium Tier features** for all students
- Cohort analytics and reporting
- Teacher dashboards
- Institutional audit logs
- Configuration controls (feature flags, cost limits)
- Priority support

**Cost:** Per-student pricing (TBD, e.g., $3/student/month for bulk)

---

## 5. Enforcement Mechanisms

### 5.1 Backend Enforcement

**Critical Rule:** Feature availability enforced at **backend/orchestrator level**, not UI-only.

**Enforcement Strategy:**

1. **Pipeline Guards:**
   - Orchestrator checks user role and tier before executing pipeline
   - If user lacks entitlement, pipeline execution **rejected** with `403 Forbidden`

2. **Feature Flags:**
   - Each feature has corresponding flag in `EntitlementResolver`
   - Flags checked in real-time (no caching of permissions beyond request scope)

3. **Rate Limiting:**
   - Free tier subject to rate limits (5/day for submissions)
   - Premium tier: higher limits or unlimited

4. **Cost Tracking:**
   - AI usage tracked per user
   - School admins can set budget caps (enforced before AI call)

---

### 5.2 UI Enforcement (Secondary)

- UI **hides** unavailable features (e.g., "Upgrade to Premium" button instead of handwriting upload)
- **Not relied upon** for security (UI can be bypassed)
- **Consistency check:** UI state mirrors backend entitlement resolution

---

### 5.3 Audit Logging

- All entitlement checks logged with `trace_id`
- Unauthorized access attempts flagged for security review

---

## 6. Feature Flag Configuration

### 6.1 Global Flags (Platform-Wide)

| **Flag Name**                  | **Default** | **Controlled By**       | **Purpose**                                |
|--------------------------------|-------------|-------------------------|--------------------------------------------|
| `AI_MARKING_ENABLED`           | ON          | ZimPrep Admin           | Disable AI globally (emergency killswitch) |
| `HANDWRITING_UPLOAD_ENABLED`   | ON          | ZimPrep Admin           | Disable OCR feature                        |
| `APPEALS_ENABLED`              | ON          | ZimPrep Admin           | Disable appeals (maintenance mode)         |
| `ANALYTICS_ENABLED`            | ON          | ZimPrep Admin           | Disable analytics engine                   |

---

### 6.2 Institutional Flags (School-Specific)

| **Flag Name**                  | **Default** | **Controlled By**       | **Purpose**                                |
|--------------------------------|-------------|-------------------------|--------------------------------------------|
| `ALLOW_STUDENT_APPEALS`        | ON          | School Admin            | Schools can disable appeals internally     |
| `ANONYMOUS_ANALYTICS_ONLY`     | OFF         | School Admin            | Hide student names in analytics            |
| `REQUIRE_TEACHER_APPROVAL`     | OFF         | School Admin            | Submissions reviewed by teacher first      |
| `AI_COST_CAP_USD`              | None        | School Admin            | Budget limit for AI usage                  |

---

### 6.3 User-Level Flags (Future)

| **Flag Name**                  | **Default** | **Controlled By**       | **Purpose**                                |
|--------------------------------|-------------|-------------------------|--------------------------------------------|
| `OPT_OUT_ANALYTICS`            | OFF         | Student                 | Student opts out of topic recommendations  |
| `SIMPLIFIED_FEEDBACK`          | OFF         | Student                 | Shorter, simpler feedback language         |

---

## 7. Rollout-Specific Controls

### 7.1 Pilot Mode

**When active:**
- **Limited users** (whitelist by email domain or school ID)
- **Enhanced logging** (every request audited)
- **Manual review** (human checks AI outputs before delivery)

**Feature Availability:**
- **AI marking:** ON (monitored)
- **Handwriting upload:** OFF (not tested at scale)
- **Appeals:** ON (critical for trust)

---

### 7.2 School Pilot Mode

**When active:**
- **Selected schools** only
- **Limited subjects** (e.g., Math and English only)
- **Mandatory teacher review** (feedback reviewed before showing to students)

**Feature Availability:**
- **AI marking:** ON (subject-restricted)
- **Cohort analytics:** ON
- **Institutional reporting:** ON

---

### 7.3 National Rollout Mode

**When active:**
- **All users** (no whitelisting)
- **All subjects**
- **Automated validation** (no manual review)

**Feature Availability:**
- **All features:** ON
- **Appeals:** Fully operational
- **Monitoring:** Automated

---

## 8. Special Access: Regulators

### 8.1 Regulator Role (Future)

**Purpose:** Allow ZIMSEC or educational authorities to audit ZimPrep compliance.

**Access Rights:**
- **Read-only** audit logs (anonymized student data)
- **Compliance reports** (AI usage, validation pass rates, appeal outcomes)
- **Evidence review** (which ZIMSEC sources used)

**Restrictions:**
- **No student PII** (only anonymized IDs)
- **No modification rights** (cannot change data)
- **Activity logged** (regulator actions audited)

### 8.2 Regulator Onboarding

- **Requires legal agreement** (NDA, MOU with ZIMSEC)
- **Role provisioned** by ZimPrep Admin only
- **Access time-limited** (e.g., 90-day audit window)

---

## 9. Feature Addition Protocol

### 9.1 New Feature Checklist

Before adding a new feature:

1. ✅ **Define which roles** can access it
2. ✅ **Determine tier requirements** (Free, Premium, Institutional)
3. ✅ **Implement backend enforcement** (orchestrator guards)
4. ✅ **Update this matrix** (document entitlements)
5. ✅ **Test enforcement** (verify unauthorized users blocked)
6. ✅ **Audit log integration** (entitlement checks logged)
7. ✅ **User disclosure** (update feature documentation)

**Approval Required:** Feature Governance Board (Product, Legal, Engineering)

---

### 9.2 Prohibited Shortcuts

❌ **UI-only enforcement** (backend must validate)  
❌ **Implicit entitlements** (must be explicitly documented)  
❌ **Feature flags without audit logging**  
❌ **Bypassing entitlement checks** (no "admin backdoors" without logging)  

---

## 10. Monitoring and Compliance

### 10.1 Entitlement Violation Detection

- **Automated monitoring:** Failed entitlement checks tracked
- **Threshold alerts:** >10 violations/day triggers investigation
- **Pattern analysis:** Repeated violations = potential abuse

### 10.2 Quarterly Reviews

- **Feature usage audit:** Are features used as expected?
- **Role assignment review:** Are users in correct roles?
- **Tier upgrade recommendations:** Suggest Premium for heavy Free users

---

## 11. Policy Governance

### 11.1 Policy Ownership

- **Owner:** ZimPrep Product Team
- **Approvers:** Legal, Engineering, Governance Board
- **Reviewers:** School partners, student representatives

### 11.2 Amendment Process

Policy changes require:
- **Impact assessment** (does it affect current users?)
- **User notification** (30 days for tier/feature changes)
- **Version control** with changelog
- **Testing** (ensure enforcement works)

---

## 12. User Communication

### 12.1 Transparency

Users must know:
- **What tier they are on** (displayed in account settings)
- **What features are available to them** (clear UI labeling)
- **How to upgrade** (if applicable)

### 12.2 Upgrade Prompts

- **Non-intrusive:** Suggest upgrades when users attempt restricted features
- **Value-focused:** "Unlock handwriting upload with Premium"
- **No dark patterns:** Clear pricing, cancel anytime

---

## Document Control

| **Version** | **Date**       | **Author**              | **Changes**            |
|-------------|----------------|-------------------------|------------------------|
| 1.0         | 2025-12-28     | ZimPrep Governance Team | Initial policy release |

---

**Related Policies:**  
- [AI Usage Policy](AI_Usage_Policy.md)  
- [Data Retention Policy](Data_Retention_Policy.md)  
- [Rollout Playbook](Rollout_Playbook.md)

---

**END OF FEATURE GOVERNANCE MATRIX**
