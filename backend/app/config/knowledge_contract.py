"""Canonical Knowledge Contract.

Defines the authoritative collection names for ingestion data.
Runtime engines MUST import collection names from this module.

NO hard-coded collection name strings are allowed in engines.
"""

# ═══════════════════════════════════════════════════════════════════════════
# INGESTION COLLECTIONS (READ-ONLY for runtime)
# ═══════════════════════════════════════════════════════════════════════════
# These collections are populated by the ingestion pipeline and consumed by
# runtime engines. Runtime MUST NOT write to these collections.

CANONICAL_QUESTIONS = "canonical_questions"
"""Canonical question bank with marking schemes and metadata.

Schema:
- question_id: str
- text: str (question text)
- subject: str
- level: str (syllabus version)
- has_graph: bool
- graph_refs: list[str]
- marking_scheme: dict
- metadata: dict
"""

SYLLABUS_SECTIONS = "syllabus_sections"
"""Syllabus sections with topic hierarchy and embeddings.

Schema:
- section_id: str
- subject: str
- level: str (syllabus version)
- topic: str
- subtopic: str
- content: str
- embedding: list[float] (384 dimensions)
- metadata: dict
"""

QUESTION_EMBEDDINGS = "question_embeddings"
"""Vector embeddings for questions (384 dimensions).

Schema:
- question_id: str
- embedding: list[float] (384 dimensions)
- subject: str
- level: str
- metadata: dict
"""

SYLLABUS_EMBEDDINGS = "syllabus_embeddings"
"""Vector embeddings for syllabus sections (384 dimensions).

Schema:
- section_id: str
- embedding: list[float] (384 dimensions)
- subject: str
- level: str
- topic: str
- subtopic: str
- metadata: dict
"""


# ═══════════════════════════════════════════════════════════════════════════
# RUNTIME COLLECTIONS (READ-WRITE for runtime)
# ═══════════════════════════════════════════════════════════════════════════
# These collections are managed by runtime engines for operational data.

SUBMISSIONS = "submissions"
ANSWERS = "answers"
SESSIONS = "sessions"
EXAM_SCHEDULES = "exam_schedules"
AUDIT_RECORDS = "audit_records"
AI_EVIDENCE = "ai_evidence"
COMPLIANCE_SNAPSHOTS = "compliance_snapshots"
QUESTION_DELIVERY_PROGRESS = "question_delivery_progress"
EXAM_RESULTS = "exam_results"
AI_COST_TRACKING = "ai_cost_tracking"
AUDIT_TRAIL = "audit_trail"
LEARNING_ANALYTICS_SNAPSHOTS = "learning_analytics_snapshots"
TOPIC_MASTERY_STATES = "topic_mastery_states"
INSTITUTIONAL_ANALYTICS = "institutional_analytics"
GOVERNANCE_REPORTS = "governance_reports"
EXTERNAL_ACCESS_KEYS = "external_access_keys"
EXTERNAL_API_AUDIT_LOGS = "external_api_audit_logs"
RESCHEDULE_REQUESTS = "reschedule_requests"
DEVICE_CONNECTIVITY_EVENTS = "device_connectivity_events"
AI_REASONING_CACHE = "ai_reasoning_cache"
ANSWER_BUFFERS = "answer_buffers"


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

INGESTION_COLLECTIONS = {
    CANONICAL_QUESTIONS,
    SYLLABUS_SECTIONS,
    QUESTION_EMBEDDINGS,
    SYLLABUS_EMBEDDINGS,
}

RUNTIME_COLLECTIONS = {
    SUBMISSIONS,
    ANSWERS,
    SESSIONS,
    EXAM_SCHEDULES,
    AUDIT_RECORDS,
    AI_EVIDENCE,
    COMPLIANCE_SNAPSHOTS,
    QUESTION_DELIVERY_PROGRESS,
    EXAM_RESULTS,
    AI_COST_TRACKING,
    AUDIT_TRAIL,
    LEARNING_ANALYTICS_SNAPSHOTS,
    TOPIC_MASTERY_STATES,
    INSTITUTIONAL_ANALYTICS,
    GOVERNANCE_REPORTS,
    EXTERNAL_ACCESS_KEYS,
    EXTERNAL_API_AUDIT_LOGS,
    RESCHEDULE_REQUESTS,
    DEVICE_CONNECTIVITY_EVENTS,
    AI_REASONING_CACHE,
    ANSWER_BUFFERS,
}
