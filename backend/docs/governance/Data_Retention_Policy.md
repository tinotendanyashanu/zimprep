# ZimPrep Data Retention & Privacy Policy

**Version:** 1.0  
**Effective Date:** 2025-12-28  
**Classification:** AUTHORITATIVE GOVERNANCE DOCUMENT  
**Review Cycle:** Annual or upon regulatory change

---

## 1. Purpose and Scope

This policy defines **how long ZimPrep retains data**, establishes data ownership, outlines deletion rights, and ensures compliance with privacy regulations.

**Scope:** All data collected, processed, or stored by ZimPrep, including student answers, AI outputs, audit logs, and analytics.

---

## 2. Core Principles

### 2.1 Data Minimization
- Collect **only necessary data** for platform functionality
- Avoid storing **personally identifiable information (PII)** unless essential

### 2.2 Purpose Limitation
- Data used **only for stated purposes** (exam prep, analytics, auditing)
- **No secondary use** without explicit consent (e.g., no marketing to students)

### 2.3 User Control
- Students and institutions have **rights to access, export, and delete** their data
- Deletion requests honored within **30 days** (subject to legal/audit retention)

### 2.4 Security
- Data encrypted **in transit** (TLS) and **at rest** (encryption at rest)
- Access controls enforce **role-based permissions**

---

## 3. Data Categories and Retention

### 3.1 Student Response Data

| **Data Type**                  | **Retention Period**       | **Justification**                          | **Deletion Rights**         |
|--------------------------------|----------------------------|--------------------------------------------|-----------------------------|
| Student answers (text)         | **2 years** from submission| Educational analytics, audit               | Yes (anonymization option)  |
| Handwriting images             | **2 years** from submission| Audit trail, appeal support                | Yes (with answer deletion)  |
| AI-generated feedback          | **2 years** from submission| Student review, appeal evidence            | Yes (with answer deletion)  |
| Marks (awarded)                | **2 years** from submission| Progress tracking, analytics               | Yes (anonymization option)  |

**Rationale:** 2-year retention allows students to review historical performance and supports appeals within a reasonable window. After 2 years, data is anonymized or deleted.

---

### 3.2 Audit and Compliance Data

| **Data Type**                  | **Retention Period**       | **Justification**                          | **Deletion Rights**         |
|--------------------------------|----------------------------|--------------------------------------------|-----------------------------|
| Audit logs (`trace_id` records)| **5 years** from creation  | Regulatory compliance, incident investigation| **No** (legal requirement)  |
| Validation results             | **5 years** from creation  | AI governance, quality assurance           | **No** (compliance)         |
| Appeal records                 | **5 years** from resolution| Regulatory audit, pattern analysis         | **No** (legal requirement)  |
| AI cost logs                   | **3 years** from creation  | Financial audit, budget analysis           | **No** (financial records)  |

**Rationale:** Extended retention for audit data ensures ZimPrep can respond to regulatory inquiries and demonstrate compliance long after student use.

---

### 3.3 User Account Data

| **Data Type**                  | **Retention Period**       | **Justification**                          | **Deletion Rights**         |
|--------------------------------|----------------------------|--------------------------------------------|-----------------------------|
| User credentials (hashed)      | **Until account deletion** | Authentication                              | Yes (account deletion)      |
| Email address                  | **Until account deletion** | Communication, password recovery           | Yes (account deletion)      |
| User role (student/teacher)    | **Until account deletion** | Access control                              | Yes (account deletion)      |
| Subscription status            | **3 years** after deletion | Billing disputes, fraud prevention         | No (financial records)      |

**Rationale:** User data retained as long as account is active. Post-deletion, only anonymized billing metadata retained for financial compliance.

---

### 3.4 Analytics and Aggregated Data

| **Data Type**                  | **Retention Period**       | **Justification**                          | **Deletion Rights**         |
|--------------------------------|----------------------------|--------------------------------------------|-----------------------------|
| Topic mastery trends           | **Indefinitely** (anonymized)| Product improvement, research             | N/A (no PII)                |
| Institutional analytics        | **Indefinitely** (anonymized)| Educational research, platform reporting  | N/A (no PII)                |
| AI performance metrics         | **Indefinitely** (anonymized)| Model tuning, quality assurance           | N/A (no technical data)     |

**Rationale:** Aggregated, anonymized data enables continuous improvement without privacy risk. No individual students identifiable.

---

### 3.5 Vector Embeddings and Evidence

| **Data Type**                  | **Retention Period**       | **Justification**                          | **Deletion Rights**         |
|--------------------------------|----------------------------|--------------------------------------------|-----------------------------|
| ZIMSEC marking scheme embeddings| **Indefinitely**          | Core platform functionality                | N/A (no student data)       |
| Student answer embeddings      | **2 years** (aligned with answers)| Similarity search, plagiarism detection | Yes (with answer deletion)  |
| Retrieved evidence logs        | **5 years** (aligned with audit)| Audit trail, evidence of AI decisions   | No (compliance)             |

**Rationale:** Evidence embeddings contain no student PII. Student answer embeddings follow same retention as raw answers.

---

## 4. Data Ownership

### 4.1 Student Data

- **Individual students** own data submitted via **personal accounts**
- **Schools** own data submitted via **institutional accounts** (joint ownership with student)

**Clarification:**
- If student uses free account → Student owns data
- If student uses school-provisioned account → School + student jointly own data

### 4.2 AI Outputs

- AI-generated feedback and marks are **owned by ZimPrep** as derived works
- **Students have usage rights** (can access, export, share their feedback)
- **Schools have usage rights** for their students (institutional dashboards)

### 4.3 Audit Logs

- Audit logs are **owned by ZimPrep** for compliance and governance
- **Students and schools have access rights** (can view, not modify)

---

## 5. Data Subject Rights

### 5.1 Right to Access

Students and institutions may request:
- **All data** associated with their account
- **Audit logs** for their submissions (redacted for other users' privacy)
- **Evidence** used in AI marking decisions

**How to exercise:** Via in-platform data export tool or support request

**Response time:** Within **30 days**

---

### 5.2 Right to Rectification

Students may request correction of:
- **Inaccurate profile information** (name, email)
- **Incorrect institutional affiliation**

**Not correctable:**
- **Historical marks** (use appeal process instead)
- **Audit logs** (immutable for compliance)

**How to exercise:** Via account settings or support request

**Response time:** Within **14 days**

---

### 5.3 Right to Deletion (Erasure)

Students may request deletion of:
- **Account and profile data** (immediate upon request)
- **Submitted answers and feedback** (subject to retention exceptions)

**Deletion exceptions:**
- **Audit logs** retained for 5 years (regulatory requirement)
- **Anonymized analytics** (no PII to delete)
- **Active legal/appeals cases** (data held until resolution)

**How deletion works:**
1. **Immediate:** Account disabled, login credentials deleted
2. **Within 30 days:** Student answers and feedback anonymized (user_id replaced with anonymous ID)
3. **After 5 years:** Audit logs purged

**How to exercise:** Via account settings ("Delete Account") or support request

---

### 5.4 Right to Data Portability

Students may request:
- **Export of all submissions** (JSON or PDF format)
- **Export of feedback history** (PDF with original answers)
- **Export of analytics** (topic mastery reports)

**Format:** Machine-readable JSON or human-readable PDF

**How to exercise:** Via in-platform "Export My Data" tool

**Response time:** Within **30 days** (large exports may take longer)

---

### 5.5 Right to Object

Students may object to:
- **AI marking** (opt for manual review only – may incur delays)
- **Analytics usage** (opt out of topic recommendations)
- **Marketing communications** (can unsubscribe anytime)

**Cannot object to:**
- **Audit logging** (mandatory for compliance)
- **Validation enforcement** (core safety mechanism)

**How to exercise:** Via account settings or support request

---

## 6. Institutional Data Management

### 6.1 School Data Ownership

Schools that provide **institutional accounts** have rights to:
- **Access student data** for their enrolled students
- **Export cohort analytics** (anonymized)
- **Configure retention policies** (within ZimPrep's minimum requirements)

### 6.2 School Data Deletion

When a school **terminates** ZimPrep subscription:
- **Student data** retained per individual student preferences (students may continue with personal accounts)
- **Institutional audit logs** retained for 5 years (compliance)
- **School admin accounts** deleted within 90 days

### 6.3 Student Graduation/Transfer

When a student **graduates or leaves** a school:
- **Institutional affiliation** removed from account
- **Student data** retained per student's account status (if student keeps account, data persists)
- **School analytics** anonymized (student no longer identifiable in cohort data)

---

## 7. Data Processing and Third Parties

### 7.1 Third-Party AI Providers

| **Provider**       | **Data Shared**                  | **Purpose**              | **Data Retention (by provider)** | **DPA in place?** |
|--------------------|----------------------------------|--------------------------|----------------------------------|-------------------|
| OpenAI (GPT-4)     | Student answers (anonymized)     | AI marking, feedback     | **Not retained** (per contract)  | ✅ Yes            |
| MongoDB Atlas      | All ZimPrep data                 | Database hosting         | Per ZimPrep retention policy     | ✅ Yes            |

**Key Protections:**
- **No training on student data** (contractually prohibited)
- **Data residency:** MongoDB Atlas configured for Zimbabwe-compliant region (if applicable)
- **Encryption:** All data encrypted in transit and at rest

### 7.2 Analytics and Monitoring Tools

- **Internal analytics only** (no third-party analytics providers with student PII access)
- **Error logging** (Sentry or equivalent) – anonymized error traces only

---

## 8. Data Security Measures

### 8.1 Encryption

- **In transit:** TLS 1.2+ for all API communications
- **At rest:** MongoDB encryption at rest enabled
- **Backups:** Encrypted backups stored in secure cloud storage

### 8.2 Access Controls

- **Role-based access control (RBAC):** Users see only data they are authorized for
- **Administrative access:** Limited to authorized ZimPrep personnel, logged and audited
- **Multi-factor authentication (MFA):** Required for admin accounts

### 8.3 Anonymization

- **Audit logs:** Anonymized after retention period (user_id replaced with hash)
- **Analytics:** Aggregated data contains no student identifiers
- **Research use:** Only anonymized data used for product improvement

---

## 9. Data Breach Response

### 9.1 Detection and Containment

If a data breach is detected:
1. **Immediate containment** (disable affected systems)
2. **Impact assessment** (what data was exposed?)
3. **Notification** (users, schools, regulators within 72 hours)

### 9.2 User Notification

Affected users notified via:
- **Email** to registered address
- **In-platform alert** (prominent banner)
- **Public disclosure** (if legally required)

### 9.3 Remediation

- **Root cause analysis** (how did breach occur?)
- **Security patches** (fix vulnerabilities)
- **Compensation** (if applicable, per Terms of Service)

---

## 10. Children's Privacy (Under 18)

### 10.1 Parental Consent

- **Students under 18** require **parental consent** (or school consent via institutional accounts)
- **Parental access:** Parents can request access to their child's data

### 10.2 Enhanced Protections

- **No marketing** to students under 18
- **No data sharing** with third parties (beyond essential AI providers)
- **Simplified privacy settings** (age-appropriate controls)

---

## 11. Cross-Border Data Transfers

### 11.1 Data Residency

- **Primary storage:** MongoDB Atlas (region: TBD based on Zimbabwe compliance)
- **AI processing:** OpenAI (US-based) – student data anonymized before sending

### 11.2 Compliance

- **Zimbabwe data protection laws:** Compliance under legal review
- **GDPR-equivalent protections:** Applied regardless of jurisdiction
- **Standard Contractual Clauses (SCCs):** Used for international transfers (if required)

---

## 12. Retention Policy Exceptions

### 12.1 Legal Holds

Data may be retained **beyond standard periods** if:
- **Litigation pending** (data relevant to legal case)
- **Regulatory investigation** (data required for compliance inquiry)
- **Criminal investigation** (law enforcement request with valid legal process)

**User notification:** Users notified if their data is under legal hold (unless prohibited by law)

---

### 12.2 Institutional Overrides

Schools may request **extended retention** (beyond 2 years) for:
- **Accreditation requirements** (educational standards compliance)
- **Longitudinal studies** (with student consent)

**Maximum extension:** 5 years (aligned with audit retention)

---

## 13. Data Deletion Procedures

### 13.1 Automated Deletion

- **Scheduled jobs** run monthly to purge expired data
- **Soft deletion** (data marked as deleted, purged after grace period)
- **Verification:** Deletion logs audited quarterly

### 13.2 Manual Deletion

- **User-initiated:** Via account settings or support request
- **Administrative:** In case of Terms of Service violations
- **Emergency:** Immediate deletion for safety/legal reasons

---

## 14. Compliance and Audit

### 14.1 Internal Audits

- **Quarterly reviews** of data retention compliance
- **Access log audits** (who accessed what data?)
- **Retention policy adherence** (are expired data purged on time?)

### 14.2 External Audits

- **Regulatory inspections:** Regulators may audit data handling practices
- **Third-party certifications:** ISO 27001, SOC 2 (in progress)

---

## 15. Policy Governance

### 15.1 Policy Ownership

- **Owner:** ZimPrep Governance Board
- **Approvers:** Legal, Privacy Officer, Data Security Lead
- **Reviewers:** ZIMSEC Liaison (if applicable), Student Representatives

### 15.2 Amendment Process

Policy changes require:
- **Privacy impact assessment** (PIAs)
- **User notification** 30 days prior to enforcement
- **Opt-out options** (if changes are material)
- **Version control** with clear changelog

---

## 16. Contact and Requests

### 16.1 Data Protection Officer (DPO)

- **Email:** privacy@zimprep.com
- **Responsibilities:** Data protection inquiries, deletion requests, breach notifications

### 16.2 User Requests

- **Access, deletion, export:** Via in-platform tools or privacy@zimprep.com
- **Response time:** 30 days maximum (14 days for urgent requests)

---

## Document Control

| **Version** | **Date**       | **Author**              | **Changes**            |
|-------------|----------------|-------------------------|------------------------|
| 1.0         | 2025-12-28     | ZimPrep Governance Team | Initial policy release |

---

**Related Policies:**  
- [AI Usage Policy](AI_Usage_Policy.md)  
- [Appeals Policy](Appeals_Policy.md)  
- [Feature Governance Matrix](Feature_Governance_Matrix.md)

---

**END OF DATA RETENTION & PRIVACY POLICY**
