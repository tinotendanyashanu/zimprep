# ZimPrep AI Usage Policy

**Version:** 1.0  
**Effective Date:** 2025-12-28  
**Classification:** AUTHORITATIVE GOVERNANCE DOCUMENT  
**Review Cycle:** Annual or upon regulatory change

---

## 1. Purpose and Scope

This policy defines **how, when, and why** artificial intelligence is used within ZimPrep, establishes boundaries for AI involvement in assessment processes, and ensures compliance with educational regulations and ethical standards.

**Scope:** All AI-assisted operations within ZimPrep including marking, feedback generation, evidence retrieval, and analytics.

---

## 2. AI Roles and Boundaries

### 2.1 What AI Does

AI systems within ZimPrep are used to:

- **Assist marking** by analyzing student responses against ZIMSEC marking schemes
- **Generate feedback** aligned with examiner-style commentary standards
- **Retrieve evidence** from verified ZIMSEC marking schemes and examiner reports
- **Analyze patterns** in student performance for diagnostic purposes
- **Recommend resources** based on demonstrated strengths and weaknesses

### 2.2 What AI Does NOT Do

AI systems within ZimPrep **explicitly do not**:

- Make **final assessment decisions** (all AI outputs are validated)
- **Predict final exam outcomes** or provide pass/fail forecasts
- Make **admissions or progression decisions**
- **Replace human oversight** in appeals or disputes
- **Store or process** AI outputs without validation approval

### 2.3 Human Oversight and Veto Authority

- **Every AI output** passes through the Validation & Consistency Engine
- **Validation failures** result in automatic rejection (AI veto power)
- **Human override** is preserved for all contested decisions
- **Appeals process** does not re-execute AI; uses immutable audit records

---

## 3. AI Technology Stack

### 3.1 Models Used

- **Primary LLM:** OpenAI GPT-4 (or equivalent) for reasoning and feedback generation
- **Embedding Model:** Sentence Transformers (all-MiniLM-L6-v2) for vector search
- **Retrieval:** MongoDB Atlas Vector Search for evidence retrieval

### 3.2 Model Selection Criteria

AI models must:
- Support educational assessment use cases
- Provide deterministic outputs via temperature=0 and seed control
- Enable cost tracking and usage auditing
- Comply with data residency requirements (when applicable)

### 3.3 Model Update Protocol

- Model version changes require **governance review**
- **Regression testing** mandatory before deployment
- **Audit trail** must capture model version per request
- **Rollback capability** required for 90 days post-deployment

---

## 4. Evidence-Based Operation (REG)

### 4.1 Retrieve-Evidence-Generate Mandate

All AI marking operations **must**:

1. **Retrieve** verified ZIMSEC evidence from the vector store
2. Use retrieved **Evidence** as the authoritative source
3. **Generate** outputs strictly constrained by retrieved evidence

### 4.2 Evidence Requirements

- Evidence must be **ZIMSEC-certified** (marking schemes, examiner reports, model answers)
- Evidence must be **version-controlled** and **immutable** once ingested
- Evidence retrieval must be **logged** with `trace_id` for audit

### 4.3 Zero Hallucination Tolerance

- AI outputs **without evidence citations** are rejected by validation
- AI outputs **contradicting evidence** are rejected by validation
- Validation engine enforces **evidence presence** as a hard constraint

---

## 5. Cost and Performance Controls

### 5.1 AI Usage Limits

- **Caching mandatory** for identical inputs (enforced by `CachedReasoningService`)
- **Cost tracking** required per request (logged to `ai_cost_log`)
- **Rate limiting** enforced to prevent abuse
- **Budget controls** available for institutional deployments

### 5.2 Performance Guarantees

- **AI timeout:** 30 seconds maximum per marking operation
- **Retry logic:** Up to 2 retries on timeout or transient failure
- **Fallback:** Manual review queue if AI fails consistently

---

## 6. Transparency and Explainability

### 6.1 Output Attribution

All AI-generated content must be:
- **Clearly labeled** as AI-assisted (in UI and reports)
- **Traceable** via audit records to specific AI calls
- **Reversible** via human review processes

### 6.2 Decision Explanations

AI marking outputs include:
- **Marks awarded** with breakdowns per rubric criterion
- **Feedback** explaining mark allocation
- **Evidence citations** linking to authoritative ZIMSEC sources

### 6.3 Black-Box Prohibition

- AI reasoning must be **interpretable** by educators
- "Magic number" marks without explanation are **prohibited**
- Feedback must align with **ZIMSEC examiner standards**

---

## 7. Bias and Fairness Controls

### 7.1 Bias Monitoring

- **Regular audits** of AI outputs across demographic groups (where data permits)
- **Validation rules** ensure consistency regardless of handwriting quality
- **Human review** of flagged cases showing potential bias

### 7.2 Prohibited Discrimination

AI systems must not:
- Advantage or disadvantage students based on **handwriting style**
- Introduce **gender, regional, or socioeconomic bias**
- Penalize students for **linguistic variations** (within ZIMSEC standards)

### 7.3 Fairness Guarantees

- **Identical inputs** produce **identical outputs** (determinism enforced)
- **Rubric adherence** is the sole basis for mark allocation
- **Evidence-based marking** eliminates subjective interpretation

---

## 8. Data Handling and Privacy

### 8.1 Student Data Protection

- AI systems **do not store** student identifiable information beyond `user_id`
- Student responses are **anonymized** before AI processing
- AI responses are **encrypted in transit and at rest**

### 8.2 Data Retention

- AI inputs and outputs retained per [Data Retention Policy](Data_Retention_Policy.md)
- Vector embeddings **do not contain** student-specific data
- Audit logs include `trace_id`, not PII

### 8.3 Third-Party AI Providers

- **Data Processing Agreements** required for all AI vendors
- **No training on student data** without explicit consent
- **Data residency** compliance for Zimbabwe regulations

---

## 9. Incident Response

### 9.1 AI Failure Scenarios

**Scenario 1:** AI timeout or unavailability
- **Response:** Queue for manual review, notify student of delay

**Scenario 2:** Validation rejects AI output
- **Response:** Log incident, queue for manual review, alert engineering

**Scenario 3:** AI produces inconsistent marks
- **Response:** Immediate investigation, potential model rollback

### 9.2 Escalation Path

1. **Automated detection** via validation engine
2. **Engineering alert** for repeated failures
3. **Governance review** if pattern indicates systemic issue
4. **Regulatory notification** if student harm detected

---

## 10. Compliance and Audit

### 10.1 Auditability Requirements

Every AI operation must:
- Generate a **unique `trace_id`**
- Log **input, output, evidence, and validation results**
- Store records in **append-only audit collections**
- Enable **deterministic replay** for investigations

### 10.2 Regulatory Compliance

This policy ensures compliance with:
- **ZIMSEC assessment standards** (AI assists, does not decide)
- **Zimbabwe data protection laws** (student privacy preserved)
- **Educational AI ethics guidelines** (transparency, fairness, human oversight)

### 10.3 Audit Rights

Regulators and schools may:
- **Inspect AI audit logs** with appropriate authorization
- **Request explanations** for AI-generated marks
- **Verify evidence sources** and retrieval logic

---

## 11. Policy Governance

### 11.1 Policy Ownership

- **Owner:** ZimPrep Governance Board
- **Approvers:** Legal, Education Standards, Engineering Leadership
- **Reviewers:** ZIMSEC Liaison (if applicable)

### 11.2 Amendment Process

Policy changes require:
- **Impact assessment** on existing marking operations
- **Stakeholder review** (students, schools, regulators)
- **Version control** with effective date tracking
- **User notification** 30 days prior to enforcement (where feasible)

### 11.3 Enforcement

- **Validation engine** enforces technical controls
- **Orchestrator** enforces pipeline constraints
- **Audit trail** enables compliance verification
- **Incident response** addresses violations

---

## 12. User Rights

### 12.1 Students

Students have the right to:
- **Know when AI is used** in marking their work
- **Receive explanations** for AI-generated marks
- **Appeal AI decisions** via human review
- **Access audit records** of their own assessments (via school)

### 12.2 Schools and Institutions

Institutions have the right to:
- **Configure AI usage limits** within their deployments
- **Access aggregate analytics** on AI performance
- **Request human review** for contested cases
- **Audit AI usage** within their student cohorts

### 12.3 Regulators

Regulators have the right to:
- **Inspect AI governance processes**
- **Audit AI outputs** for compliance
- **Request policy amendments** to meet regulatory requirements
- **Suspend AI usage** if systemic issues detected

---

## 13. Prohibited Uses

AI within ZimPrep **must never**:

- Make **final pass/fail decisions** without human oversight
- **Predict future exam performance** with stated confidence levels
- **Rank or compare** students beyond stated rubric criteria
- **Generate marks** without evidence-based justification
- **Operate** in violation of validation constraints

---

## 14. Future AI Enhancements

Any new AI capabilities must:

1. **Undergo governance review** before development
2. **Pass security and privacy assessments**
3. **Receive regulatory approval** (if applicable)
4. **Update this policy** before deployment
5. **Notify affected users** of changes

---

## Document Control

| **Version** | **Date**       | **Author**              | **Changes**            |
|-------------|----------------|-------------------------|------------------------|
| 1.0         | 2025-12-28     | ZimPrep Governance Team | Initial policy release |

---

**END OF AI USAGE POLICY**
