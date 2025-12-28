# ZimPrep Rollout Playbook

**Version:** 1.0  
**Effective Date:** 2025-12-28  
**Classification:** OPERATIONAL GOVERNANCE DOCUMENT  
**Review Cycle:** Per rollout phase

---

## 1. Purpose and Scope

This playbook defines the **phased rollout strategy** for ZimPrep, ensuring safe, monitored, and legally defensible deployment from pilot to national scale.

**Core Principle:** Rollout progresses only when safety, quality, and regulatory requirements are met.

---

## 2. Rollout Philosophy

### 2.1 Risk-Based Progression

- **Start small:** Controlled pilot with heavy monitoring
- **Validate:** Ensure AI quality, user satisfaction, operational stability
- **Scale gradually:** Expand only after validation gates passed
- **Maintain rollback capability:** Every phase can revert to previous phase

### 2.2 Non-Negotiable Gates

Each rollout phase has **exit criteria** that must be met before progression:
- ✅ **Quality metrics** (AI accuracy, validation pass rates)
- ✅ **User satisfaction** (student and teacher feedback)
- ✅ **Operational stability** (uptime, error rates)
- ✅ **Regulatory compliance** (if applicable)

**Failure to meet gates = rollout paused.**

---

## 3. Rollout Mode 1: Internal Pilot

### 3.1 Objectives

- **Test core functionality** in real-world conditions
- **Validate AI marking accuracy** against human examiners
- **Identify edge cases** and failure modes
- **Refine user experience** based on feedback

---

### 3.2 Scope

| **Parameter**          | **Value**                          |
|------------------------|-------------------------------------|
| **Users**              | 20-50 internal testers (ZimPrep team, family, friends) |
| **Subjects**           | 2-3 subjects (e.g., Math, English) |
| **Duration**           | 4 weeks                             |
| **Feature Exposure**   | All features enabled (test everything) |
| **Monitoring**         | Manual review of every AI output    |

---

### 3.3 Entry Criteria

- ✅ All Phase 0-6 engines operational
- ✅ Phase 7 governance policies published
- ✅ Validation engine passing >90% of test cases
- ✅ Audit trail functional
- ✅ Appeals process ready

---

### 3.4 Operations

#### Daily Activities:
1. **Monitor AI outputs** (review random sample of 50%)
2. **Collect user feedback** (survey after each session)
3. **Track validation failures** (investigate all rejections)
4. **Log incidents** (AI errors, crashes, bugs)

#### Weekly Activities:
1. **Engineering review** (fix critical bugs, tune AI prompts)
2. **Governance review** (ensure policy compliance)
3. **Metrics dashboard** (uptime, AI accuracy, user satisfaction)

---

### 3.5 Success Metrics

| **Metric**                     | **Target**       | **Measurement**                          |
|--------------------------------|------------------|------------------------------------------|
| AI marking accuracy            | >85% vs. human   | Human expert compares AI marks to gold standard |
| Validation pass rate           | >95%             | % of AI outputs accepted by validation   |
| User satisfaction (NPS)        | >50              | Net Promoter Score from surveys          |
| System uptime                  | >99%             | Monitored via uptime tracking            |
| Appeal overturn rate           | <10%             | % of appeals where AI mark was wrong     |

---

### 3.6 Exit Criteria (Gate 1)

To proceed to **School Pilot**, must achieve:

- ✅ **All success metrics met** for 2 consecutive weeks
- ✅ **No critical bugs** outstanding
- ✅ **Positive user feedback** (majority of users recommend platform)
- ✅ **Appeals process validated** (at least 5 appeals successfully resolved)
- ✅ **Governance team approval**

**Decision Authority:** ZimPrep Governance Board

---

### 3.7 Rollback Conditions

Revert to development if:
- ❌ AI accuracy <70%
- ❌ Validation rejects >20% of outputs
- ❌ Data breach or security incident
- ❌ Critical bug causing user harm

---

## 4. Rollout Mode 2: School Pilot

### 4.1 Objectives

- **Validate at institutional scale** (50-200 students)
- **Test teacher workflows** (analytics, appeals, reporting)
- **Refine cohort analytics** (school-level insights)
- **Build case studies** (evidence for national rollout)

---

### 4.2 Scope

| **Parameter**          | **Value**                          |
|------------------------|-------------------------------------|
| **Users**              | 3-5 pilot schools (50-200 students each) |
| **Subjects**           | 3-5 subjects (expand from internal pilot) |
| **Duration**           | 12 weeks (1 academic term)          |
| **Feature Exposure**   | All features (institutional analytics added) |
| **Monitoring**         | Automated validation + spot-checking (10% manual review) |

---

### 4.3 Entry Criteria

- ✅ **Internal Pilot Gate 1 passed**
- ✅ **Institutional features ready** (cohort analytics, teacher dashboards)
- ✅ **School partnerships secured** (MOUs signed)
- ✅ **Teacher training completed** (how to interpret AI feedback, handle appeals)
- ✅ **Parent consent obtained** (for students under 18)

---

### 4.4 Operations

#### Daily Activities:
1. **Automated monitoring** (validation pass rates, error logs)
2. **School support** (respond to teacher questions within 24hrs)

#### Weekly Activities:
1. **Spot-check AI outputs** (random 10% sample per school)
2. **Teacher feedback sessions** (what's working, what's not?)
3. **Student surveys** (every 2 weeks)

#### Monthly Activities:
1. **School performance reviews** (are students improving?)
2. **Governance audit** (policy compliance check)
3. **Engineering retrospective** (fix reported issues)

---

### 4.5 Success Metrics

| **Metric**                     | **Target**       | **Measurement**                          |
|--------------------------------|------------------|------------------------------------------|
| AI marking accuracy            | >90% vs. human   | Expert validation (larger sample)        |
| Validation pass rate           | >97%             | Automated validation tracking            |
| Teacher satisfaction           | >70% positive    | End-of-term survey                       |
| Student engagement             | >60% weekly use  | Active users per week                    |
| Appeal overturn rate           | <8%              | % of appeals overturning AI marks        |
| System uptime                  | >99.5%           | Monitored via uptime tracking            |

---

### 4.6 Exit Criteria (Gate 2)

To proceed to **Regional/National Rollout**, must achieve:

- ✅ **All success metrics met** for 8 consecutive weeks
- ✅ **Teacher endorsements** (majority recommend ZimPrep to other schools)
- ✅ **Case studies published** (evidence of student improvement or engagement)
- ✅ **Regulatory review** (if ZIMSEC liaison involved)
- ✅ **No unresolved critical incidents**
- ✅ **Governance team approval**

**Decision Authority:** ZimPrep Governance Board + External Advisory Board (if applicable)

---

### 4.7 Rollback Conditions

Revert to **Internal Pilot** if:
- ❌ AI accuracy drops below 80%
- ❌ Teacher satisfaction <50%
- ❌ Student harm reported (incorrect marks causing distress)
- ❌ Regulatory concerns raised

---

## 5. Rollout Mode 3: Regional/National Rollout

### 5.1 Objectives

- **Scale to national audience** (thousands of students)
- **Operate autonomously** (minimal manual intervention)
- **Demonstrate educational impact** (measurable student improvement)
- **Achieve regulatory recognition** (ZIMSEC endorsement, if applicable)

---

### 5.2 Scope

| **Parameter**          | **Value**                          |
|------------------------|-------------------------------------|
| **Users**              | Unlimited (all Zimbabwean students eligible) |
| **Subjects**           | All ZIMSEC O-Level and A-Level subjects |
| **Duration**           | Ongoing (production deployment)     |
| **Feature Exposure**   | All features (Free, Premium, Institutional tiers) |
| **Monitoring**         | Fully automated + alerts for anomalies |

---

### 5.3 Entry Criteria

- ✅ **School Pilot Gate 2 passed**
- ✅ **Infrastructure scaled** (cloud auto-scaling, load balancing)
- ✅ **Support team ready** (customer support, technical support)
- ✅ **Billing system operational** (subscription management, payments)
- ✅ **Marketing approved** (messaging complies with policies)
- ✅ **Legal compliance confirmed** (Terms of Service, Privacy Policy reviewed)

---

### 5.4 Operations

#### Daily Activities:
1. **Automated monitoring dashboards** (AI accuracy, uptime, error rates)
2. **Support ticket triage** (respond to urgent issues within 4 hours)

#### Weekly Activities:
1. **Performance review** (are metrics stable?)
2. **Feature usage analysis** (which features are used most?)
3. **Security audit** (vulnerability scanning)

#### Monthly Activities:
1. **Governance audit** (compliance with policies)
2. **Product improvements** (based on user feedback and data)
3. **Stakeholder reporting** (to schools, investors, regulators)

---

### 5.5 Success Metrics (Ongoing)

| **Metric**                     | **Target**       | **Measurement**                          |
|--------------------------------|------------------|------------------------------------------|
| AI marking accuracy            | >92%             | Continuous validation against expert marks |
| Validation pass rate           | >98%             | Automated tracking                       |
| Monthly active users (MAU)     | Growth >10%/mo   | User analytics                           |
| User retention (3-month)       | >50%             | % of users still active after 3 months   |
| Appeal overturn rate           | <5%              | Appeals resolved in favor of student     |
| System uptime                  | >99.9%           | SLA target                               |
| Customer support response time | <24 hours        | Median time to first response            |

---

### 5.6 Continuous Improvement

National rollout is **not the end**:
- **Product iteration:** New features based on user needs
- **AI model updates:** Periodic upgrades (with regression testing)
- **Policy refinement:** Update governance as regulations evolve
- **Partnerships:** Collaborate with ZIMSEC, schools, educators

---

### 5.7 Rollback/Degradation Conditions

In case of systemic issues:

**Partial Degradation:**
- Disable specific features (e.g., handwriting upload) if causing problems
- Throttle new user signups if infrastructure strained

**Full Rollback to School Pilot:**
- ❌ AI accuracy drops below 75% (systemic failure)
- ❌ Data breach affecting >1000 users
- ❌ Regulatory injunction (ZIMSEC orders suspension)

---

## 6. Cross-Phase Operational Standards

### 6.1 Monitoring (All Phases)

**Required Dashboards:**
1. **AI Performance:** Accuracy, validation pass rate, appeal overturn rate
2. **System Health:** Uptime, latency, error rates
3. **User Engagement:** Active users, submissions per day, retention
4. **Compliance:** Audit log integrity, policy violations

**Alert Thresholds:**
- 🚨 **Critical:** AI accuracy <80%, uptime <95%, data breach
- ⚠️ **Warning:** Validation failures >5%, appeal overturn >15%, latency >2s

---

### 6.2 Incident Response (All Phases)

**Severity Levels:**

| **Severity** | **Definition**                       | **Response Time** | **Escalation**                  |
|--------------|--------------------------------------|-------------------|---------------------------------|
| **P0**       | Total outage, data breach, AI failure| Immediate         | CEO, CTO, Legal notified        |
| **P1**       | Partial outage, high error rates     | <1 hour           | Engineering lead, on-call team  |
| **P2**       | Feature degradation, isolated bugs   | <24 hours         | Product team                    |
| **P3**       | Minor issues, feature requests       | <1 week           | Backlog prioritization          |

---

### 6.3 Communication (All Phases)

**Stakeholder Updates:**

| **Stakeholder**       | **Frequency**      | **Format**                              |
|-----------------------|--------------------|-----------------------------------------|
| Pilot users           | Weekly (pilot)     | Email summary + in-app notification     |
| School admins         | Bi-weekly          | Dashboard + email report                |
| Regulators (if any)   | Monthly            | Formal compliance report                |
| Internal team         | Daily              | Slack updates, weekly all-hands         |

---

## 7. Feature Rollout Within Phases

### 7.1 Progressive Feature Activation

Even within a rollout phase, features can be staged:

**Example: School Pilot Phase**

| **Week** | **Features Enabled**                                 |
|----------|------------------------------------------------------|
| 1-2      | AI marking (text only), basic analytics              |
| 3-4      | Handwriting upload (limited schools)                 |
| 5-8      | Topic recommendations, trend analytics               |
| 9-12     | Full institutional reporting, appeals fully staffed  |

**Why:** Reduces complexity, allows focused testing of each feature.

---

### 7.2 Beta Features (Post-National Rollout)

New features released as **opt-in beta** before general availability:
- **Example:** Voice-to-text answer submission (experimental)
- **Beta users:** Premium subscribers who opt in
- **Feedback loop:** Beta users provide feedback before wide release

---

## 8. Regulatory and Partnership Milestones

### 8.1 ZIMSEC Engagement

**Goal:** Achieve ZIMSEC recognition or endorsement (if feasible).

**Milestones:**

| **Phase**              | **ZIMSEC Engagement**                               |
|------------------------|-----------------------------------------------------|
| Internal Pilot         | No formal engagement (independent testing)          |
| School Pilot           | Informal liaison (share results, seek feedback)     |
| National Rollout       | Formal partnership discussions (if positive results)|

**Note:** ZimPrep is **not an official ZIMSEC product** but seeks alignment with standards.

---

### 8.2 Ministry of Education (if applicable)

- **Pilot phase:** Notify Ministry of pilot programs (transparency)
- **National rollout:** Seek approval or partnership (if regulatory requirement)

---

## 9. Rollout Timeline (Estimated)

| **Phase**              | **Duration**       | **Cumulative Timeline** |
|------------------------|--------------------|-------------------------|
| Internal Pilot         | 4 weeks            | Week 1-4                |
| Gate 1 Review          | 1 week             | Week 5                  |
| School Pilot           | 12 weeks           | Week 6-17               |
| Gate 2 Review          | 2 weeks            | Week 18-19              |
| National Rollout Prep  | 4 weeks            | Week 20-23              |
| National Rollout Launch| Ongoing            | Week 24+                |

**Total Time to National Launch:** ~6 months (best case)

**Contingency:** Add 25% buffer for unexpected issues (7-8 months realistic)

---

## 10. Budget and Resource Allocation

### 10.1 Cost Estimates Per Phase

| **Phase**              | **AI Costs** | **Infrastructure** | **Support Staff** | **Total/Month** |
|------------------------|--------------|--------------------|--------------------|-----------------|
| Internal Pilot         | $100         | $200               | $0 (volunteer)     | $300            |
| School Pilot           | $1,000       | $500               | $2,000 (part-time) | $3,500          |
| National Rollout       | $10,000+     | $2,000+            | $5,000+ (full-time)| $17,000+        |

**Note:** Costs scale with usage. Free tier students subsidized by Premium tier revenue.

---

### 10.2 Staffing Per Phase

| **Role**               | **Internal Pilot** | **School Pilot** | **National Rollout** |
|------------------------|---------------------|------------------|----------------------|
| Engineering            | 2 full-time         | 3 full-time      | 5+ full-time         |
| Product/Design         | 1 part-time         | 1 full-time      | 2 full-time          |
| Support                | Volunteer           | 1 part-time      | 3+ full-time         |
| Governance/Legal       | Consultant          | Consultant       | 1 full-time          |
| Marketing              | None                | Consultant       | 2 full-time          |

---

## 11. Risk Management

### 11.1 Top Risks Per Phase

#### Internal Pilot:
- **Risk:** AI accuracy lower than expected → **Mitigation:** Extend pilot, tune AI prompts
- **Risk:** Users find UX confusing → **Mitigation:** Rapid iteration on UI

#### School Pilot:
- **Risk:** Teachers distrust AI → **Mitigation:** Transparency, training, human override
- **Risk:** Negative publicity ("AI replacing teachers") → **Mitigation:** Messaging: AI assists, doesn't replace

#### National Rollout:
- **Risk:** Infrastructure overload → **Mitigation:** Auto-scaling, load testing
- **Risk:** Regulatory pushback → **Mitigation:** Proactive engagement, compliance documentation

---

### 11.2 Contingency Plans

**Scenario: AI Model Underperforms**
- **Action:** Revert to previous model version, re-train with more data
- **Timeline:** 2-4 weeks

**Scenario: Security Breach**
- **Action:** Incident response protocol (see [Incident_Response.md](TBD))
- **Timeline:** Immediate containment, notification within 72 hours

**Scenario: Regulatory Ban**
- **Action:** Engage legal counsel, seek negotiation, worst-case: suspend operations
- **Timeline:** Dependent on regulatory process

---

## 12. Success Definition

### 12.1 Internal Pilot Success

- ZimPrep works technically (AI marks, validation enforces, audits log)
- Users find it valuable (positive feedback)
- No critical blockers to school pilot

### 12.2 School Pilot Success

- Schools endorse ZimPrep (willing to pay or recommend)
- Students show improvement or engagement
- Operational stability proven at institutional scale

### 12.3 National Rollout Success

- **Thousands of active users** monthly
- **Revenue sustainable** (covers costs + growth)
- **Regulatory acceptance** (no legal challenges)
- **Educational impact** (evidence of student benefit)

---

## 13. Policy Governance

### 13.1 Playbook Ownership

- **Owner:** ZimPrep Operations Lead
- **Approvers:** Governance Board, Engineering, Product
- **Reviewers:** School Partners (during pilot phases)

### 13.2 Amendment Process

Playbook updated after **each phase completion**:
- **Retrospective:** What worked, what didn't?
- **Lessons learned:** Document for next phase
- **Version control:** Clear changelog per phase

---

## Document Control

| **Version** | **Date**       | **Author**              | **Changes**            |
|-------------|----------------|-------------------------|------------------------|
| 1.0         | 2025-12-28     | ZimPrep Governance Team | Initial playbook       |

---

**Related Policies:**  
- [Go-Live Decision Gate](Go_Live_Gate.md)  
- [Feature Governance Matrix](Feature_Governance_Matrix.md)  
- [Certification Checklist](Certification_Checklist.md)

---

**END OF ROLLOUT PLAYBOOK**
