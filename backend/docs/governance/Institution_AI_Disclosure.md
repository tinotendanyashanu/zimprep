# Institution AI Disclosure

**For Schools, Educators, and Institutional Administrators**

**Version:** 1.0  
**Effective Date:** 2025-12-28  
**Classification:** INSTITUTIONAL GOVERNANCE DOCUMENT

---

## 1. Purpose

This document provides **schools, colleges, and educational institutions** with comprehensive disclosure of how ZimPrep uses artificial intelligence (AI) in assessment and analytics operations.

**Target Audience:** School administrators, teachers, department heads, IT directors, and institutional decision-makers.

---

## 2. Executive Summary

ZimPrep is an **AI-assisted** ZIMSEC exam preparation platform that:

- Uses **AI to mark practice exams** and generate feedback
- Operates under **strict validation and audit controls**
- Provides **evidence-based, ZIMSEC-aligned** marking
- Maintains **human oversight** and **appeal rights**
- Ensures **data privacy** and **regulatory compliance**

**Critical Understanding:** AI **assists** marking but does not make final educational decisions without validation and institutional oversight.

---

## 3. AI System Architecture Overview

### 3.1 Core AI Components

| **Component**                         | **AI Technology**                  | **Purpose**                                      |
|---------------------------------------|-----------------------------------|--------------------------------------------------|
| Reasoning & Marking Engine            | OpenAI GPT-4 (or equivalent)      | Analyze student answers, suggest marks           |
| Embedding & Retrieval Engine          | Sentence Transformers + Vector DB | Retrieve ZIMSEC marking schemes and evidence     |
| Handwriting Interpretation Engine     | OCR + LLM-based correction        | Convert handwritten answers to text              |
| Topic Intelligence & Analytics Engine | Pattern analysis algorithms       | Identify strengths/weaknesses, recommend topics  |
| Validation & Consistency Engine       | Rule-based AI governance          | Verify AI outputs, enforce hard constraints      |

### 3.2 AI Governance Layer

Every AI operation is:
- **Evidence-constrained** (must cite ZIMSEC sources)
- **Validation-enforced** (AI outputs are vetted before acceptance)
- **Audit-logged** (full traceability via immutable records)
- **Human-reviewable** (appeals bypass AI, use audit logs)

---

## 4. How AI Marking Works (Technical Detail)

### Step-by-Step Process

1. **Student submits answer** (typed or handwritten image)
2. **Handwriting Engine** converts image to text (if applicable)
3. **Embedding Engine** converts question into vector representation
4. **Retrieval Engine** searches vector database for relevant ZIMSEC marking schemes
5. **Reasoning Engine** analyzes student answer against retrieved evidence
6. **Validation Engine** checks AI output for consistency, rubric compliance, mark bounds
7. **Audit Engine** logs all inputs, outputs, evidence, and validation results
8. **Result returned** to student (if validation passes) or queued for manual review (if validation fails)

### Evidence-Based Operation (REG)

ZimPrep enforces **Retrieve-Evidence-Generate** (REG):
- **Retrieve:** AI fetches verified ZIMSEC marking schemes from vector store
- **Evidence:** AI uses retrieved evidence as the authoritative source
- **Generate:** AI produces marks and feedback strictly based on evidence

**Zero Hallucination Policy:** AI cannot "invent" marks or rubric criteria. Outputs without evidence citations are automatically rejected.

---

## 5. AI Capabilities and Limitations

### 5.1 What AI Can Do

✅ **Mark practice exam answers** based on ZIMSEC marking schemes  
✅ **Generate examiner-style feedback** explaining mark allocation  
✅ **Identify topic strengths and weaknesses** through pattern analysis  
✅ **Recommend resources** aligned with demonstrated gaps  
✅ **Provide consistency** (same answer = same mark every time)  
✅ **Scale efficiently** (handle thousands of submissions concurrently)  

### 5.2 What AI Cannot Do

❌ **Make final pass/fail decisions** for real ZIMSEC exams  
❌ **Predict actual exam outcomes** with statistical confidence  
❌ **Replace teacher judgment** in nuanced or contested cases  
❌ **Operate without validation** (outputs are always checked)  
❌ **Modify marking schemes** (only follows ZIMSEC standards)  
❌ **Provide legal guarantees** of exam success  

### 5.3 Known Limitations

- **Handwriting quality:** Severely illegible handwriting may cause OCR errors
- **Ambiguous answers:** AI may struggle with creative or non-standard responses (flagged for review)
- **Network dependency:** AI marking requires internet connectivity (buffering available for brief disconnects)
- **Cost constraints:** AI usage is rate-limited to control expenses

---

## 6. Validation and Quality Assurance

### 6.1 Automated Validation Rules

Every AI mark is checked for:

1. **Mark bounds:** Marks must be within [0, max_marks]
2. **Rubric compliance:** Marks must align with ZIMSEC marking scheme criteria
3. **Internal consistency:** Subtotal marks must equal total marks
4. **Evidence presence:** AI must cite retrieved ZIMSEC evidence

**Validation failures** result in automatic rejection and manual review queuing.

### 6.2 Human Oversight

- **Appeals process:** Students can request human review (AI does not re-mark)
- **Manual review queue:** Validation failures are escalated to educators
- **Audit access:** Schools can inspect AI marking decisions via audit logs

### 6.3 Model Versioning and Testing

- AI models are **version-controlled** and logged per request
- Model updates undergo **regression testing** before deployment
- **Rollback capability** available if new model introduces errors

---

## 7. Data Handling and Privacy

### 7.1 Student Data Protection

| **Data Type**            | **AI Access**                  | **Storage**                     | **Retention**           |
|--------------------------|--------------------------------|---------------------------------|-------------------------|
| Student answers          | Anonymized (user_id only)      | Encrypted, append-only          | 2 years (configurable)  |
| AI-generated feedback    | Full access for marking        | Encrypted, audit-logged         | 2 years (configurable)  |
| Student PII (name, etc.) | **Not accessible to AI**       | Separate User DB                | Per institution policy  |
| Handwriting images       | OCR processing only            | Encrypted, append-only          | 2 years (configurable)  |

### 7.2 Third-Party AI Providers

- **OpenAI:** Used for LLM reasoning (GPT-4)
  - **Data Processing Agreement:** In place
  - **Training on student data:** **Prohibited** by contract
  - **Data residency:** US-based (Zimbabwe compliance under review)

- **Sentence Transformers:** Open-source, self-hosted
  - **No external data sharing**

### 7.3 Institutional Data Ownership

- **Schools own student data** submitted via institutional accounts
- **Individual students own data** submitted via personal accounts
- **ZimPrep retains operational logs** for audit and compliance (anonymized where possible)

---

## 8. Fairness, Bias, and Equity

### 8.1 Bias Mitigation Strategies

- **Deterministic marking:** Same answer produces same mark (no randomness)
- **Evidence-based constraints:** AI cannot introduce subjective bias
- **Handwriting neutrality:** Marks based on content, not penmanship
- **Regional language variations:** AI trained on ZIMSEC standards (Zimbabwean English)

### 8.2 Bias Monitoring

- **Regular audits:** Analyze AI outputs across demographic groups (where data permits)
- **Validation safeguards:** Inconsistent marks flagged automatically
- **Human escalation:** Suspected bias cases reviewed manually

### 8.3 Equity Guarantees

- **No discrimination** based on handwriting style, gender, region, or SES
- **Equal access** to AI marking (no premium-only AI features)
- **Transparent criteria:** All students measured against same ZIMSEC rubrics

---

## 9. Cost and Resource Management

### 9.1 AI Usage Costs

- **Caching:** Identical questions/answers reuse cached results (cost = $0)
- **Cost tracking:** Every AI call logged with expenditure ($USD per request)
- **Budget controls:** Institutions can set spending limits

### 9.2 Resource Allocation

- **Rate limiting:** Prevents abuse and controls costs
- **Priority queues:** Institutional accounts may receive prioritized processing
- **Fallback to manual review:** If AI budget exhausted, queue for human marking

---

## 10. Institutional Controls and Configuration

### 10.1 Feature Flags

Schools can configure:

| **Feature**                  | **Control Level**              | **Default**  |
|------------------------------|--------------------------------|--------------|
| AI marking enabled           | Institution-wide ON/OFF        | ON           |
| Handwriting upload           | Per-subject or per-exam        | ON           |
| Topic recommendations        | Enable/Disable                 | ON           |
| Analytics dashboards         | Role-based access              | Teachers+    |
| AI cost limits               | Budget cap in $USD             | Unlimited    |

### 10.2 Role-Based Access

- **Students:** Submit answers, view AI feedback, request appeals
- **Teachers:** View student analytics, access audit logs (own students)
- **Administrators:** Configure AI settings, view cost reports, manage appeals
- **Regulators (future):** Audit AI usage, inspect compliance records

### 10.3 Institutional Analytics

Schools receive:
- **Aggregate performance metrics** (no individual student PII)
- **AI usage statistics** (marks per day, cost per student, cache hit rates)
- **Topic mastery trends** (which topics students struggle with)
- **Compliance reports** (validation pass/fail rates, appeals resolved)

---

## 11. Appeals and Dispute Resolution

### 11.1 Student Appeal Rights

Students or parents can appeal AI marks if they believe an error occurred.

**Appeal Process:**

1. Student submits appeal via platform (with justification)
2. **Human reviewer** inspects original answer and AI audit log
3. Reviewer uses **immutable audit record** (AI does not re-execute)
4. Reviewer may:
   - **Uphold AI mark** (if correct)
   - **Override AI mark** (if error detected)
   - **Request re-review** by senior examiner
5. Decision communicated to student with explanation

### 11.2 Institutional Appeal Oversight

- Schools can **monitor appeal volumes** (high rates may indicate AI issues)
- Schools can **escalate patterns** to ZimPrep engineering for investigation
- Schools can **disable AI temporarily** if systemic issues detected

---

## 12. Compliance and Regulatory Alignment

### 12.1 ZIMSEC Compliance

- AI follows **official ZIMSEC marking schemes** exclusively
- AI does not create or modify assessment standards
- AI outputs are **advisory** for practice exams (not official results)

### 12.2 Data Protection Compliance

- **Zimbabwe data protection laws:** Compliance under legal review
- **GDPR-style principles:** Data minimization, purpose limitation, user rights
- **Right to deletion:** Students can request data removal (anonymized analytics retained)

### 12.3 Educational AI Ethics

- **Transparency:** Users informed when AI is used
- **Fairness:** No discrimination or bias
- **Accountability:** Human oversight and appeals
- **Privacy:** Student data protected

---

## 13. Incident Response and Escalation

### 13.1 AI Failure Scenarios

| **Scenario**                     | **Institutional Impact**                 | **Response**                              |
|----------------------------------|------------------------------------------|-------------------------------------------|
| AI timeout (>30s)                | Delayed marking                          | Queue for manual review                   |
| Validation rejects AI output      | Delayed marking                          | Queue for manual review                   |
| Repeated validation failures      | Service degradation                      | Engineering alert, possible model rollback|
| Data breach (AI provider)         | Student data exposure risk               | Incident response, regulatory notification|
| Bias detected in AI outputs       | Student harm potential                   | Immediate investigation, human review     |

### 13.2 Institutional Notification

Schools are notified if:
- **AI service outage** exceeds 2 hours
- **Data breach** affects their students
- **Policy changes** impact AI usage
- **Regulatory actions** require institutional response

---

## 14. Institutional Responsibilities

### 14.1 Pre-Deployment

Before deploying ZimPrep, institutions should:

- **Review AI Usage Policy** and ensure alignment with institutional values
- **Inform students and parents** using provided disclosure templates
- **Train teachers** on interpreting AI feedback and handling appeals
- **Configure feature flags** to match institutional requirements

### 14.2 Ongoing Oversight

During operation, institutions should:

- **Monitor appeal rates** (>10% may indicate issues)
- **Review cost reports** (ensure budget alignment)
- **Audit AI feedback quality** (spot-check student results)
- **Update policies** as regulations evolve

### 14.3 Compliance Reporting

Institutions may be required to:

- **Report AI usage** to educational regulators (if mandated)
- **Maintain audit logs** for inspection (ZimPrep provides access)
- **Document incidents** involving AI errors or disputes

---

## 15. Support and Contact

### 15.1 Technical Support

- **Platform issues:** support@zimprep.com (or in-app support)
- **AI errors:** Report via platform incident system
- **Policy questions:** governance@zimprep.com

### 15.2 Training and Resources

- **Teacher training materials:** Available in institutional dashboard
- **Student disclosure templates:** Provided for parent communication
- **Regulatory briefings:** Available upon request

---

## 16. Policy Updates and Versioning

### 16.1 Change Management

Policy updates follow:

1. **Stakeholder review** (schools, regulators, legal)
2. **Impact assessment** (does it affect existing deployments?)
3. **Version control** (new version number, effective date)
4. **Notification** (30 days advance notice where feasible)

### 16.2 Institutional Notification

Schools notified of policy changes via:
- **Email to registered administrators**
- **In-platform announcements**
- **Updated documentation** (clearly marked with version)

---

## 17. Certification and Accreditation

### 17.1 Current Status

ZimPrep is:
- **Self-certified** under internal governance standards
- **Pending external audit** (compliance certification in progress)
- **Not officially endorsed** by ZIMSEC (independent prep tool)

### 17.2 Future Certifications

ZimPrep is pursuing:
- **ISO 27001:** Information security management
- **Educational AI standards:** (if/when established in Zimbabwe)
- **ZIMSEC partnership:** (under discussion)

---

## 18. Consent and Agreement

By deploying ZimPrep institutionally, your school acknowledges:

- Understanding of **how AI is used** in marking and analytics
- Agreement to **inform students and parents** per disclosure templates
- Commitment to **institutional oversight** of AI usage and appeals
- Acceptance of **data handling practices** outlined in this document

If your institution has specific AI usage restrictions, contact governance@zimprep.com before deployment.

---

## Document Control

| **Version** | **Date**       | **Author**              | **Changes**            |
|-------------|----------------|-------------------------|------------------------|
| 1.0         | 2025-12-28     | ZimPrep Governance Team | Initial policy release |

---

**For student-facing disclosure, see [Student AI Disclosure](Student_AI_Disclosure.md).**  
**For full AI governance details, see [AI Usage Policy](AI_Usage_Policy.md).**

---

**END OF INSTITUTION AI DISCLOSURE**
