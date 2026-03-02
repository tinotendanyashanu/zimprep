# ZimPrep Deployment Readiness Plan

This document defines the **authoritative, phased fix plan** to take ZimPrep from its current audited state to **initial production deployment readiness**.

The plan is strictly aligned with:
- ZimPrep Architecture Audit Report
- ZimPrep Authoritative Engine Architecture
- ZimPrep Master Blueprint

No new features are introduced. This plan only **fixes, hardens, and gates** existing components.

---

## Phase 0 — System Unblock (Boot Safety)
**Goal:** System must start and execute pipelines without crashing

**Deployment Allowed:** No

### P0.1 Fix Pipeline–Registry Engine Name Mismatch
**Problem**
- Pipelines reference engine name `identity`
- Engine registry only registers `identity_subscription`
- Causes runtime failure on startup

**Action**
- Register `identity` as an alias of `IdentitySubscriptionEngine`
- Do not modify pipeline definitions

**Done When**
- Backend boots with no RuntimeError
- Pipelines execute successfully:
  - exam_attempt_v1
  - handwriting_exam_attempt_v1
  - topic_practice_v1

---

## Phase 1 — Architectural Integrity Lock
**Goal:** Enforce engine isolation and orchestration purity

**Deployment Allowed:** No

### P1.1 Remove Engine Isolation Violations
**Problems**
- practice_assembly engine contains commented orchestrator calls
- Engine constructors accept orchestrator dependencies
- Recommendation engine exposes standalone FastAPI routes

**Actions**
1. Remove commented orchestrator calls from practice_assembly
2. Remove orchestrator dependency from all engine constructors
3. Remove standalone Recommendation Engine routes
4. Route all execution exclusively through orchestrator pipelines

**Pipeline Adjustment**
- Add topic_intelligence before practice_assembly
- Pass topic expansion results as explicit engine input

**Done When**
- No engine references orchestrator
- No engine exposes direct API routes
- All execution flows through orchestrator

---

## Phase 2 — RAG Defensive Hardening
**Goal:** Make AI marking failure-safe and regulator-proof

**Deployment Allowed:** Internal only

### P1.2 Inter-Engine Data Validation Layer
**Problems**
- No enforcement that retrieved evidence exists before reasoning
- No validation of embedding dimensions
- Potential silent AI failure paths

**Actions**
- Introduce orchestrator-level data validation layer
- Validate:
  - Embedding dimensions before retrieval
  - Non-empty evidence before reasoning
  - Presence of marks before validation
  - Validation veto always aborts pipeline

**Done When**
- Invalid data never reaches downstream engines
- All failures are explicit, logged, and traceable

---

## Phase 3 — Traceability and Async Safety
**Goal:** Preserve trace_id across synchronous and async execution

**Deployment Allowed:** Yes (Initial Deployment)

### P1.3 Background Processing Integration
**Problems**
- Background jobs not integrated into pipelines
- trace_id may be lost during async execution

**Actions**
- Allow orchestrator to enqueue background jobs
- Preserve originating trace_id in all async jobs
- Expose job status query endpoint

**Minimum Required Scope**
- Async marking
- Async ingestion
- Trace continuity

**Done When**
- All background jobs retain original trace_id
- Job status is queryable

---

## Phase 4 — Initial Deployment Gate
**Goal:** System is legally and operationally deployable

**Deployment Allowed:** Yes

### Included at Initial Deployment
- Exam practice (typed and handwritten)
- RAG-based marking with validation
- Recommendation engine via pipelines
- Full audit trail
- Cost-aware AI routing
- Locked offline ingestion pipeline

### Explicitly Excluded (Deferred)
- Distributed tracing UI
- Schema registry and versioning
- Regulator-facing audit dashboards
- SQL datastore usage
- Advanced analytics

---

## Phase 5 — Post-Deployment Hardening (Optional)
**Goal:** Scale and regulatory expansion

**Deployment Impact:** None

- Distributed tracing (OpenTelemetry / Jaeger)
- Schema registry and contract versioning
- Audit query APIs
- GDPR tooling
- SQL vs MongoDB architectural decision record

---

## Deployment Readiness Checklist

Deployment is valid **only if all conditions are true**:

- Backend boots with no registry errors
- No engine calls another engine
- No standalone engine routes exist
- Validation engine can veto and stop pipelines
- All execution paths have a trace_id
- Background jobs preserve trace_id
- Ingestion runs offline only

If any condition fails, deployment is invalid by design.

---

## Final Statement

ZimPrep is stabilised through **controlled, phased hardening**, not feature expansion.

This plan is authoritative and should be used as the **single reference document** for deployment readiness.

