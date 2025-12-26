# Practice Assembly Engine

## Overview

The **Practice Assembly Engine** is a production-grade Core (Non-AI) engine that assembles intelligent practice sessions by selecting questions, balancing difficulty, and creating personalized study experiences.

## Responsibility

**ONE AND ONLY ONE RESPONSIBILITY**: Assemble practice sessions by selecting and organizing questions.

This engine:
- ✅ Selects questions for practice sessions
- ✅ Balances difficulty (default: 40% easy, 40% medium, 20% hard)
- ✅ Expands topics using Topic Intelligence
- ✅ Supports 3 session types (targeted, mixed, exam simulation)
- ✅ Respects student history (avoids recently seen questions)
- ✅ Enforces time limits and question counts
- ❌ Does NOT: Mark answers (Reasoning & Marking Engine does that)
- ❌ Does NOT: Embed topics (Topic Intelligence Engine does that)
- ❌ Does NOT: Call other engines directly (orchestrator handles that)

## Session Types

### 1. Targeted Practice
- **Purpose**: Master a specific topic
- **Topics**: 1 primary + related topics (via Topic Intelligence)
- **Ordering**: Progressive (easy → medium → hard)
- **Time**: Usually untimed
- **Questions**: 10-20

### 2. Mixed Review
- **Purpose**: Maintain breadth across topics
- **Topics**: 3-5 topics
- **Ordering**: Random shuffle
- **Time**: Time-boxed (30-60 min)
- **Questions**: 15-30

### 3. Exam Simulation
- **Purpose**: Practice under exam conditions
- **Topics**: Full syllabus
- **Ordering**: Exam-style (progressive with mixing)
- **Time**: Strict exam time limit
- **Questions**: Matches real exam count

## Input Contract

```python
PracticeAssemblyInput(
    trace_id: str,
    user_id: str,
    session_type: Literal["targeted", "mixed", "exam_simulation"],
    
    # Topic selection
    primary_topic_ids: List[str],
    include_related_topics: bool = True,
    similarity_threshold: float = 0.7,
    
    # Question criteria
    subject: str,
    syllabus_version: str,
    difficulty_distribution: Dict[str, float] = {
        "easy": 0.4,
        "medium": 0.4,
        "hard": 0.2
    },
    
    # Session config
    max_questions: int = 20,
    time_limit_minutes: int | None = None,
    
    # Personalization
    exclude_recent_days: int = 7,
    preferred_question_types: List[str] | None = None,
)
```

## Output Contract

```python
PracticeAssemblyOutput(
    trace_id: str,
    session_id: str,
    practice_session: PracticeSession,
    topics_included: List[str],
    related_topics_added: List[str],
    total_questions: int,
    estimated_duration_minutes: int,
    difficulty_breakdown: Dict[str, int],
    engine_version: str,
)
```

## Execution Flow (7 Steps)

1. **Validate Input Schema**  
   Strict Pydantic validation

2. **Expand Topics (if enabled)**  
   Call Topic Intelligence Engine via orchestrator to find related topics

3. **Query Available Questions**  
   Fetch questions from MongoDB matching topics, subject, syllabus

4. **Filter Questions**  
   - Remove questions attempted in last N days
   - Filter by preferred question types
   - Remove questions in active sessions

5. **Balance Difficulty**  
   Select questions to match target distribution (40/40/20)

6. **Build Session**  
   - Order questions based on session type
   - Calculate estimated duration
   - Generate session ID

7. **Return Session**  
   Complete PracticeSession with metadata

## Difficulty Distribution

### Default: 40/40/20
- **Easy**: 40% - Foundation building, confidence
- **Medium**: 40% - Consolidation, skill building
- **Hard**: 20% - Challenge, mastery

### Rationale
- Starts with confidence (easy questions)
- Solidifies understanding (medium)
- Pushes boundaries (hard)
- Avoids frustration (not too many hard)

### Customizable
- Students can adjust distribution
- Premium tier: adaptive based on performance

## Question Ordering

### Targeted Practice: Progressive
```
Easy → Easy → Easy → Medium → Medium → Medium → Hard → Hard
```
Builds confidence, then challenges.

### Mixed Review: Random
```
Medium → Easy → Hard → Easy → Medium → ...
```
Keeps students engaged with variety.

### Exam Simulation: Exam-Style
```
Easy → Easy → Medium → Easy → Medium → Hard → Medium → Hard → Hard
```
Matches real exam patterns.

## Recency Filter

**Default**: 7 days

Questions attempted in the last 7 days are excluded to:
- Prevent repetition fatigue
- Ensure variety
- Support spaced repetition

**Customizable**: Can be set to 0 (no filtering) for quick review.

## Integration with Topic Intelligence

This engine calls Topic Intelligence for topic expansion:

```python
# Example: Student selects "Algebra" for practice

# 1. Practice Assembly calls Topic Intelligence
related_topics = orchestrator.execute_engine(
    engine_name="topic_intelligence",
    payload={
        "operation": "find_similar",
        "query_topic_id": "algebra_001",
        "similarity_threshold": 0.7,
        "max_results": 3,
    }
)

# Returns: ["Linear Equations", "Quadratic Equations", "Factorization"]

# 2. Practice Assembly selects questions from ALL topics
questions = select_questions(
    topics=["Algebra"] + related_topics
)

# Result: Richer, more comprehensive practice session
```

## MongoDB Collections

### questions
```json
{
    "_id": "question_001",
    "question_text": "Solve x² + 5x + 6 = 0",
    "question_type": "calculation",
    "topic_id": "topic_002",
    "topic_name": "Quadratic Equations",
    "subject": "Mathematics",
    "syllabus_version": "2025_v1",
   "difficulty": "medium",
    "max_marks": 5,
    "estimated_minutes": 8
}
```

### practice_sessions
```json
{
    "_id": "session_abc123",
    "user_id": "student_456",
    "session_type": "targeted",
    "topics": ["Algebra", "Quadratic Equations"],
    "questions": ["question_001", "question_002", ...],
    "total_questions": 15,
    "estimated_duration_minutes": 90,
    "created_at": "2025-12-25T22:00:00Z",
    "status": "active"
}
```

### user_question_history
```json
{
    "_id": "history_001",
    "user_id": "student_456",
    "question_id": "question_001",
    "attempted_at": "2025-12-20T10:00:00Z",
    "score": 4.5,
    "max_marks": 5
}
```

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| **Query Questions** | ~50ms | MongoDB indexed query |
| **Balance Difficulty** | ~5ms | In-memory sorting |
| **Build Session** | ~10ms | Ordering + metadata |
| **Total** | ~65ms | Fast enough for sync API |

## Legal Defensibility

### Deterministic Selection
- Same input → same output (modulo randomization seed)
- Randomization is seeded by trace_id (reproducible)
- Audit trail captures all decisions

### Personalization Transparency
- Recency filter logged
- Topic expansion logged
- Difficulty breakdown captured

### Student History Respect
- Recency filter prevents repetition
- Transparent to students
- Can be disabled for review

## Version

**Engine Version**: 1.0.0  
**Last Updated**: 2025-12-25

## Testing

```bash
python -m pytest app/engines/core/practice_assembly/tests/test_engine.py -v
```

## Future Enhancements

1. **Adaptive Difficulty**: Adjust based on student performance
2. **Spaced Repetition**: Scientific scheduling (Anki-style)
3. **Weak Area Focus**: Prioritize topics with low scores
4. **Time Optimization**: Recommend questions for available time
5. **Peer Comparison**: Include challenging questions
