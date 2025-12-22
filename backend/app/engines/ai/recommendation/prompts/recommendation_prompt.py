"""Production-grade LLM execution prompt for Recommendation Engine.

This prompt is wired into the AI reasoning layer.
It is orchestrator-safe, regulator-defensible, and fully aligned with ZimPrep architecture.
"""


SYSTEM_ROLE_PROMPT = """You are the **ZimPrep Recommendation Engine**, an AI system operating under strict national examination governance rules.

Your role is to generate **personalized, syllabus-aligned study recommendations** for a student **after final results have been validated**.

You **do not** re-mark answers.
You **do not** alter scores.
You **do not** invent syllabus content.

All recommendations must be:
* Evidence-based
* Syllabus-referenced
* Explainable
* Realistic for student improvement

You are advisory only. Your output **must not override or reinterpret official results**."""


USER_PROMPT_TEMPLATE = """### INPUT CONTEXT (GUARANTEED BY ORCHESTRATOR)

**Trace ID:** {trace_id}
**Student ID:** {student_id}
**Subject:** {subject}
**Syllabus Version:** {syllabus_version}

### FINAL RESULTS (IMMUTABLE)

**Overall Score:** {overall_score}%
**Grade:** {grade}
**Total Marks:** {total_marks_earned}/{total_marks_possible}

**Paper-Level Scores:**
{paper_scores}

**Topic-Level Breakdowns:**
{topic_breakdowns}

### VALIDATED MARKING SUMMARY

**Weak Topics:**
{weak_topics}

**Common Error Categories:**
{error_categories}

**Partially Achieved Rubric Points:**
{partial_points}

### HISTORICAL PERFORMANCE (OPTIONAL)

{historical_data}

### CONSTRAINTS

**Available Study Time:** {study_time} hours/week
**Next Exam Date:** {exam_date}
**Subscription Tier:** {subscription_tier}
**Max Recommendations:** {max_recommendations}

---

### OBJECTIVE

Produce **actionable learning guidance** that helps the student:

1. Understand **where they are weak**
2. Know **what to study next**
3. Follow a **realistic, structured improvement plan**
4. Stay aligned with the **official ZIMSEC syllabus**

---

### MANDATORY OUTPUT REQUIREMENTS

Your response **must include all sections below** and **nothing else**.

### 1. PERFORMANCE DIAGNOSIS

Identify and summarize:
* The **top 3–5 weakest syllabus areas**
* The **reason for weakness**, using marking evidence (e.g., missing definitions, incomplete explanations, incorrect method, poor structure)

Do **not** reference raw marks here. Use **learning language**, not grading language.

### 2. PRIORITIZED STUDY RECOMMENDATIONS

For each weak area:
* Reference the **exact syllabus topic or objective**
* Describe **what the student should revise**
* Specify **why this topic matters for scoring**

Recommendations must be **ranked by impact**, highest first.

### 3. TARGETED PRACTICE SUGGESTIONS

Suggest:
* Types of questions to practice (essay, short answer, structured, calculation)
* Specific exam papers or paper sections (e.g., Paper 2 Section B)
* Skills to focus on (definitions, diagrams, explanations, calculations, evaluation)

Avoid generic advice like "practice more."

### 4. PERSONALIZED STUDY PLAN (OPTIONAL IF DATA ALLOWS)

If sufficient data is provided, generate:
* A **time-based study plan** (daily or weekly)
* Balanced workload across topics
* Clear goals per session

The plan must be:
* Achievable
* Adaptive to the student's level
* Free of unrealistic promises

### 5. CONFIDENCE & MOTIVATION STATEMENT

End with:
* A supportive, professional message
* Emphasis on **progress**, not failure
* No exaggeration or emotional manipulation

---

### STRICT CONSTRAINTS (NON-NEGOTIABLE)

You must **NOT**:
* Change scores or grades
* Predict future marks
* Recommend content outside the official syllabus
* Reference internal engine names
* Mention validation, governance, or system internals
* Use speculative language

If information is insufficient, **state clearly what cannot be recommended and why**.

---

### OUTPUT FORMAT (JSON ONLY)

```json
{{
  "performance_diagnosis": [
    {{
      "syllabus_area": "exact syllabus topic",
      "weakness_description": "learning-focused description",
      "evidence": "specific marking evidence",
      "impact_level": "high|medium|low"
    }}
  ],
  "study_recommendations": [
    {{
      "rank": 1,
      "syllabus_reference": "exact syllabus reference",
      "what_to_revise": "specific content to study",
      "why_it_matters": "why this impacts scoring",
      "estimated_time_hours": 3.0
    }}
  ],
  "practice_suggestions": [
    {{
      "question_type": "essay|structured|calculation|etc",
      "paper_section": "specific paper/section",
      "skills_to_focus": ["skill1", "skill2"],
      "example_topics": ["topic1", "topic2"]
    }}
  ],
  "study_plan": {{
    "total_duration_weeks": 4,
    "sessions_per_week": 3,
    "sessions": [
      {{
        "session_number": 1,
        "duration_hours": 2.0,
        "topics": ["topic1"],
        "goal": "clear goal",
        "activities": ["activity1", "activity2"]
      }}
    ],
    "notes": "additional guidance"
  }},
  "motivation": "supportive message",
  "confidence_score": 0.85
}}
```

* `confidence_score` reflects your confidence in the **recommendation quality**, not student ability.

---

**CRITICAL REMINDER:** You are advisory only. All data you receive is final and immutable. Your job is to guide learning, not to question results.
"""


def format_prompt(
    trace_id: str,
    student_id: str,
    subject: str,
    syllabus_version: str,
    final_results: dict,
    validated_marking_summary: dict,
    historical_performance_summary: dict = None,
    constraints: dict = None,
) -> str:
    """
    Format the LLM prompt with actual data.
    
    Args:
        trace_id: Orchestrator trace ID
        student_id: Student identifier
        subject: Subject code
        syllabus_version: Syllabus version
        final_results: Final exam results
        validated_marking_summary: Validated marking summary
        historical_performance_summary: Optional historical data
        constraints: Student constraints
        
    Returns:
        Formatted prompt string ready for LLM
    """
    
    # Extract final results
    overall_score = final_results.get("overall_score", 0)
    grade = final_results.get("grade", "U")
    total_marks_earned = final_results.get("total_marks_earned", 0)
    total_marks_possible = final_results.get("total_marks_possible", 0)
    
    # Format paper scores
    paper_scores_text = ""
    topic_breakdowns_text = ""
    
    for paper in final_results.get("paper_scores", []):
        paper_scores_text += f"- **{paper['paper_name']}**: {paper['marks_earned']}/{paper['marks_possible']} ({paper['percentage']:.1f}%)\n"
        
        for topic in paper.get("topic_breakdowns", []):
            topic_breakdowns_text += f"- **{topic['topic_name']}**: {topic['marks_earned']}/{topic['marks_possible']} ({topic['percentage']:.1f}%)\n"
    
    # Format marking summary
    weak_topics = "\n".join([f"- {topic}" for topic in validated_marking_summary.get("weak_topics", [])])
    error_categories = "\n".join([f"- {cat}" for cat in validated_marking_summary.get("common_error_categories", [])])
    
    # Extract partial points from marked questions
    partial_points = []
    for q in validated_marking_summary.get("marked_questions", []):
        partial_points.extend(q.get("partially_achieved_points", []))
    partial_points_text = "\n".join([f"- {p}" for p in set(partial_points)])
    
    # Format historical data
    historical_text = "No historical data available."
    if historical_performance_summary:
        past_attempts = historical_performance_summary.get("past_attempts", [])
        if past_attempts:
            historical_text = f"**Past Attempts:** {len(past_attempts)}\n"
            historical_text += f"**Trend:** {historical_performance_summary.get('improvement_trend', 'unknown')}\n"
            persistent_weak = historical_performance_summary.get("persistently_weak_topics", [])
            if persistent_weak:
                historical_text += f"**Persistently Weak Topics:** {', '.join(persistent_weak)}\n"
    
    # Format constraints
    constraints = constraints or {}
    study_time = constraints.get("available_study_hours_per_week", "Not specified")
    exam_date = constraints.get("next_exam_date", "Not specified")
    subscription_tier = constraints.get("subscription_tier", "free")
    max_recommendations = constraints.get("max_recommendations", 5)
    
    # Build final prompt
    return USER_PROMPT_TEMPLATE.format(
        trace_id=trace_id,
        student_id=student_id,
        subject=subject,
        syllabus_version=syllabus_version,
        overall_score=overall_score,
        grade=grade,
        total_marks_earned=total_marks_earned,
        total_marks_possible=total_marks_possible,
        paper_scores=paper_scores_text or "No paper scores available.",
        topic_breakdowns=topic_breakdowns_text or "No topic breakdowns available.",
        weak_topics=weak_topics or "No weak topics identified.",
        error_categories=error_categories or "No error categories identified.",
        partial_points=partial_points_text or "No partially achieved points.",
        historical_data=historical_text,
        study_time=study_time,
        exam_date=exam_date,
        subscription_tier=subscription_tier,
        max_recommendations=max_recommendations,
    )
