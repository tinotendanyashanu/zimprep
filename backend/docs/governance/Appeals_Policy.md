# ZimPrep Assessment & Appeals Policy

**Version:** 1.0  
**Effective Date:** 2025-12-28  
**Classification:** AUTHORITATIVE GOVERNANCE DOCUMENT  
**Review Cycle:** Annual or upon regulatory change

---

## 1. Purpose and Scope

This policy defines **how students can appeal AI-generated practice exam marks**, establishes guarantees for deterministic replay, and ensures fairness, transparency, and auditability in dispute resolution.

**Scope:** All appeals related to AI marking decisions within ZimPrep.

---

## 2. Core Principle

> **Appeals are resolved using immutable audit records, not AI re-execution. Students have the right to human review of contested marks.**

Appeals must be:
- **Evidence-based** (original answer and audit log reviewed)
- **Deterministic** (same evidence = same outcome)
- **Human-adjudicated** (no AI re-marking)
- **Transparent** (decision reasoning provided)

---

## 3. What Can Be Appealed

### 3.1 Appealable Decisions

Students **may** appeal:

✅ **Mark allocation** – If they believe the AI awarded incorrect marks based on the rubric  
✅ **Rubric interpretation** – If they believe the AI misinterpreted the marking scheme  
✅ **Evidence mismatch** – If they believe the AI used the wrong marking scheme  
✅ **Calculation errors** – If subtotal marks do not match total marks  
✅ **Missing credit** – If they believe they met a rubric criterion but received no marks  

### 3.2 Non-Appealable Decisions

Students **cannot** appeal:

❌ **Rubric criteria themselves** – ZimPrep uses official ZIMSEC marking schemes (not modifiable)  
❌ **Subjective preferences** – "I think my answer deserves more marks" without rubric basis  
❌ **Comparisons to other students** – Appeals are individual, not comparative  
❌ **AI model choice** – Students cannot request a different AI model for re-marking  
❌ **Historical marks** – Appeals must be filed within 30 days of receiving feedback  

---

## 4. Appeal Rights

### 4.1 Who Can Appeal

- **Students** who submitted the answer (via their account)
- **Parents/Guardians** (for students under 18, via student account or institutional liaison)
- **School representatives** (if student is institutionally enrolled and authorizes appeal)

### 4.2 When Appeals Are Allowed

- **Timeframe:** Within **30 days** of receiving the original mark
- **Frequency:** Students may appeal the same answer **once only**
- **Restrictions:** Appeals not permitted if answer was flagged for academic integrity violations

### 4.3 Appeal Submission Requirements

Students must provide:

1. **Original submission ID** (automatically populated via UI)
2. **Specific rubric criteria** in dispute
3. **Justification** – Why the original mark is believed to be incorrect (with reference to marking scheme)
4. **Supporting evidence** (optional) – e.g., citation of ZIMSEC marking scheme section

---

## 5. Appeal Process

### 5.1 Step-by-Step Workflow

#### **Step 1: Student Submits Appeal**
- Student clicks "Appeal this mark" button on results page
- Student completes appeal form (justification required)
- Appeal logged in `appeals` collection (append-only)

#### **Step 2: Automated Eligibility Check**
- System verifies:
  - Appeal filed within 30-day window
  - Student has not already appealed this submission
  - Submission is not flagged for academic integrity issues
- If ineligible: Appeal rejected with explanation
- If eligible: Proceeds to Step 3

#### **Step 3: Human Reviewer Assignment**
- Appeal assigned to **qualified human reviewer** (teacher, examiner, or ZimPrep specialist)
- Reviewer accesses:
  - **Original student answer** (immutable)
  - **AI audit log** (marking decision trace)
  - **Retrieved evidence** (ZIMSEC marking scheme used by AI)
  - **Validation results** (why AI output was accepted/rejected)

#### **Step 4: Human Review**
- Reviewer **does not re-execute AI**
- Reviewer evaluates:
  - Did AI correctly apply the rubric?
  - Did AI use the correct marking scheme?
  - Are there calculation errors?
  - Did AI miss valid content in the student answer?
- Reviewer makes one of three decisions:
  1. **Uphold original mark** (AI was correct)
  2. **Override mark** (AI made an error; new mark assigned)
  3. **Escalate for senior review** (complex or ambiguous case)

#### **Step 5: Decision Communication**
- Decision logged in `appeals` collection with:
  - **Outcome** (upheld/overridden/escalated)
  - **Reasoning** (explanation of decision)
  - **Revised mark** (if applicable)
  - **Reviewer ID** (for accountability)
- Student notified via platform and email
- Original audit record **remains immutable**; override stored separately

#### **Step 6: Appeal Closure**
- Appeal marked as **resolved**
- Student may view decision reasoning via platform
- If student remains dissatisfied, **escalation to senior review** is available (one-time)

---

### 5.2 Appeal Timelines

| **Stage**                     | **Maximum Duration**        |
|-------------------------------|-----------------------------|
| Eligibility check             | Instant (automated)         |
| Reviewer assignment           | 24 hours                    |
| Human review                  | 72 hours (3 business days)  |
| Senior review (if escalated)  | 5 business days             |
| Student notification          | Immediate (upon decision)   |

**Urgent appeals** (e.g., high-stakes institutional use) may be prioritized at school request.

---

## 6. Appeal Guarantees

### 6.1 No AI Re-Execution

**Critical Guarantee:** AI is **never** asked to re-mark the answer during appeals.

**Why:**
- AI re-execution could produce different results (even with same inputs, due to LLM variance)
- Appeals must be **deterministic** – same evidence always yields same decision
- Human reviewers use **audit logs** to understand AI's original reasoning

### 6.2 Immutable Evidence

**All appeal decisions** are based on:
- **Original student answer** (stored in `student_responses` collection – immutable)
- **Original AI output** (stored in `ai_reasoning_outputs` – immutable)
- **Original retrieved evidence** (stored in `marking_evidence_retrieval` – immutable)
- **Original validation result** (stored in `validation_results` – immutable)

**No evidence can be altered** post-submission to influence appeals.

### 6.3 Audit Trail Preservation

- Every appeal generates a **new audit record** (does not overwrite original)
- If mark is overridden, **both original and revised marks** are stored
- Appeals themselves are **append-only** (cannot be deleted or edited)

### 6.4 Transparent Reasoning

- Students receive **written explanation** of appeal decision
- Explanation includes:
  - Which rubric criteria were reconsidered
  - Why original mark was upheld or overridden
  - Reference to ZIMSEC marking scheme (if relevant)

---

## 7. Appeal Outcomes and Mark Changes

### 7.1 Mark Adjustments

If appeal is **upheld** (AI was correct):
- **No change** to original mark
- Student receives explanation confirming AI decision

If appeal is **overridden** (AI made an error):
- **New mark assigned** by human reviewer
- New mark replaces original in student's visible results
- **Both marks logged** in audit trail for compliance

### 7.2 Mark Change Limits

- Human reviewer can **increase or decrease** marks based on evidence
- Mark changes must be **justified by rubric** (not subjective favoritism)
- If mark is decreased, student is **notified and given explanation**

### 7.3 Analytics Impact

- **Topic mastery analytics** updated to reflect revised mark
- **Institutional dashboards** reflect corrected data
- **AI cost logs** remain unchanged (appeal does not incur new AI costs)

---

## 8. Appeal Escalation

### 8.1 Senior Review Requests

Students may request **senior review** if:
- They disagree with initial appeal decision
- They believe reviewer made an error
- Case involves complex or ambiguous rubric interpretation

**Escalation Process:**
- Student submits escalation request (via platform)
- **Senior examiner** or **governance team member** assigned
- Senior reviewer has **final authority** (no further appeals after this stage)

### 8.2 Institutional Appeals

Schools may escalate **patterns of disputed marks** to ZimPrep governance if:
- Multiple students appeal similar topics (suggests systemic AI error)
- Validation failures exceed 10% for specific questions
- Rubric interpretation appears inconsistent

**Institutional escalation** triggers:
- **Engineering investigation** (model review, evidence quality check)
- **Potential model rollback** if systemic issue confirmed
- **Notification to all affected students** with revised marks

---

## 9. Appeal Monitoring and Quality Assurance

### 9.1 Appeal Rate Tracking

ZimPrep monitors:
- **Appeal volume** (% of submissions appealed)
- **Appeal outcomes** (upheld vs. overridden rates)
- **Topics with high appeal rates** (may indicate AI struggles)

**Threshold alerts:**
- If **>10% of submissions** for a topic are appealed → Investigation triggered
- If **>50% of appeals** are overridden → Model review required

### 9.2 Reviewer Quality Control

- Human reviewers are **calibrated** against ZIMSEC standards
- **Random sampling** of appeal decisions reviewed for consistency
- Reviewers with **high overturn rates** receive additional training

### 9.3 Bias Detection

- Appeal outcomes analyzed for **demographic bias** (if data permits)
- If certain student groups have disproportionately overturned appeals → Investigation triggered

---

## 10. Appeal Data Retention

### 10.1 Retention Period

- **Active appeals:** Retained until resolution
- **Resolved appeals:** Retained for **2 years** from resolution date
- **Escalated appeals:** Retained for **5 years** (regulatory compliance)

### 10.2 Deletion Rights

- Students may request **deletion of personal data** per [Data Retention Policy](Data_Retention_Policy.md)
- **Anonymized appeal metadata** retained for analytics (no student identifiers)

---

## 11. Institutional Appeal Configuration

### 11.1 School-Managed Appeals

Schools may opt to:
- **Handle first-tier appeals internally** (using ZimPrep audit logs)
- **Route appeals** to school-designated examiners (with appropriate training)
- **Request ZimPrep support** for complex cases

### 11.2 Appeal Reporting

Schools receive:
- **Monthly appeal summaries** (volume, outcomes, topics)
- **Trend analysis** (are appeals increasing/decreasing?)
- **Action recommendations** (e.g., "Review Topic X marking scheme")

---

## 12. Regulatory Compliance

### 12.1 Fair Appeals Process

ZimPrep appeals comply with:
- **Educational fairness standards** (right to challenge decisions)
- **Transparency requirements** (students informed of process)
- **Auditability mandates** (regulators can inspect appeal logs)

### 12.2 Audit Access

Regulators may:
- **Inspect appeal records** with appropriate authorization
- **Verify human review quality**
- **Request systemic issue reports** (if appeal patterns suggest problems)

---

## 13. Appeals vs. Academic Integrity

### 13.1 Prohibited Appeals

Appeals are **not permitted** if:
- Student's answer is flagged for **plagiarism** or **cheating**
- Student is under **academic integrity investigation**
- Submission violates **ZimPrep Terms of Service**

### 13.2 Good Faith Requirement

Appeals must be submitted **in good faith**:
- **Frivolous appeals** (e.g., no justification provided) may be rejected
- **Repeated bad-faith appeals** may result in account warnings
- **Abuse of appeal system** (e.g., appealing every submission) may result in suspension

---

## 14. Cost and Resource Allocation

### 14.1 Appeal Costs

- **Students:** Appeals are **free** (no additional charges)
- **Institutions:** Appeals are **included** in platform subscription
- **ZimPrep:** Appeal review is a **cost of quality assurance**

### 14.2 Resource Prioritization

- **High-stakes appeals** (institutional exams) prioritized
- **Batch appeals** (multiple students, same question) handled collectively
- **Low-complexity appeals** (calculation errors) auto-resolved where possible

---

## 15. Continuous Improvement

### 15.1 Feedback Loop

- Appeal outcomes **inform AI model tuning**
- Frequently overturned decisions → **Evidence or prompt refinement**
- Validation rules updated to **catch errors before delivery**

### 15.2 Policy Updates

- Appeal policy reviewed **annually** or after **significant system changes**
- Student and school feedback solicited for policy improvements

---

## 16. User Rights Summary

### 16.1 Students

Students have the right to:
- **Appeal any AI mark** within 30 days
- **Receive human review** of their appeal
- **Understand the decision** (written explanation provided)
- **Escalate to senior review** (one time)
- **Access appeal records** (via their account)

### 16.2 Schools

Schools have the right to:
- **Monitor appeal trends** for their students
- **Escalate systemic issues** to ZimPrep governance
- **Configure appeal workflows** (internal vs. ZimPrep-managed)
- **Audit appeal quality** for institutional compliance

---

## 17. Policy Governance

### 17.1 Policy Ownership

- **Owner:** ZimPrep Governance Board
- **Approvers:** Legal, Education Standards, Operations
- **Reviewers:** Student Representatives (if applicable), ZIMSEC Liaison

### 17.2 Amendment Process

Policy changes require:
- **User impact assessment** (does it affect active appeals?)
- **Regulatory review** (compliance with education laws)
- **Version control** with clear changelog
- **User notification** 30 days prior to enforcement

---

## Document Control

| **Version** | **Date**       | **Author**              | **Changes**            |
|-------------|----------------|-------------------------|------------------------|
| 1.0         | 2025-12-28     | ZimPrep Governance Team | Initial policy release |

---

**Related Policies:**  
- [AI Usage Policy](AI_Usage_Policy.md)  
- [Feedback Policy](Feedback_Policy.md)  
- [Data Retention Policy](Data_Retention_Policy.md)

---

**END OF ASSESSMENT & APPEALS POLICY**
