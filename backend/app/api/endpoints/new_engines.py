"""API endpoints for new ZimPrep engines.

Provides REST API access to:
- Handwriting Interpretation
- AI Routing & Cost Control  
- Topic Intelligence
- Practice Assembly
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from app.orchestrator.engine_registry import EngineRegistry
from app.orchestrator.execution_context import ExecutionContext
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/engines", tags=["New Engines"])


# ========================================
# Handwriting Interpretation Endpoints
# ========================================

@router.post("/handwriting/interpret")
async def interpret_handwriting(
    payload: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Interpret handwritten exam answer.
    
    Request body:
    {
        "image_reference": "data:image/png;base64,...",
        "question_id": "q_001",
        "answer_type": "calculation",
        "expected_format": "step_by_step"
    }
    
    Returns:
    {
        "structured_answer": {...},
        "confidence_score": 0.85,
        "requires_manual_review": false,
        "cost_tracking": {...}
    }
    """
    try:
        engine_registry = EngineRegistry()
        engine = engine_registry.get("handwriting_interpretation")
        
        context = ExecutionContext(
            trace_id=f"hw_{datetime.utcnow().timestamp()}",
            user_id=current_user["user_id"],
            role=current_user["role"],
            timestamp=datetime.utcnow()
        )
        
        response = await engine.run(payload, context)
        
        if response.success:
            return {
                "success": True,
                "data": response.data,
                "trace_id": response.trace.trace_id
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Topic Intelligence Endpoints
# ========================================

@router.post("/topics/embed")
async def embed_topic(
    topic_text: str,
    topic_id: str,
    syllabus_version: str,
    current_user: Dict = Depends(get_current_user)
):
    """Generate 384-dim embedding for a topic."""
    try:
        engine_registry = EngineRegistry()
        engine = engine_registry.get("topic_intelligence")
        
        context = ExecutionContext(
            trace_id=f"topic_embed_{datetime.utcnow().timestamp()}",
            user_id=current_user["user_id"],
            role=current_user["role"],
            timestamp=datetime.utcnow()
        )
        
        payload = {
            "operation": "embed_topic",
            "topic_text": topic_text,
            "topic_id": topic_id,
            "syllabus_version": syllabus_version
        }
        
        response = await engine.run(payload, context)
        
        if response.success:
            return {
                "success": True,
                "topic_id": response.data["topic_id"],
                "embedding_dimension": len(response.data["topic_embedding"]),
                "trace_id": response.trace.trace_id
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topics/find-similar")
async def find_similar_topics(
    query_topic_id: str,
    similarity_threshold: float = 0.7,
    max_results: int = 10,
    current_user: Dict = Depends(get_current_user)
):
    """Find topics similar to a query topic."""
    try:
        engine_registry = EngineRegistry()
        engine = engine_registry.get("topic_intelligence")
        
        context = ExecutionContext(
            trace_id=f"topic_similar_{datetime.utcnow().timestamp()}",
            user_id=current_user["user_id"],
            role=current_user["role"],
            timestamp=datetime.utcnow()
        )
        
        payload = {
            "operation": "find_similar",
            "query_topic_id": query_topic_id,
            "similarity_threshold": similarity_threshold,
            "max_results": max_results
        }
        
        response = await engine.run(payload, context)
        
        if response.success:
            return {
                "success": True,
                "similar_topics": response.data["similar_topics"],
                "count": len(response.data["similar_topics"]),
                "trace_id": response.trace.trace_id
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topics/match-question")
async def match_question_to_topics(
    question_text: str,
    max_results: int = 5,
    current_user: Dict = Depends(get_current_user)
):
    """Match a question to relevant topics (auto-tagging)."""
    try:
        engine_registry = EngineRegistry()
        engine = engine_registry.get("topic_intelligence")
        
        context = ExecutionContext(
            trace_id=f"topic_match_{datetime.utcnow().timestamp()}",
            user_id=current_user["user_id"],
            role=current_user["role"],
            timestamp=datetime.utcnow()
        )
        
        payload = {
            "operation": "match_question",
            "question_text": question_text,
            "max_results": max_results
        }
        
        response = await engine.run(payload, context)
        
        if response.success:
            return {
                "success": True,
                "matched_topics": response.data["matched_topics"],
                "count": len(response.data["matched_topics"]),
                "trace_id": response.trace.trace_id
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Practice Assembly Endpoints
# ========================================

@router.post("/practice/create-session")
async def create_practice_session(
    payload: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Create a personalized practice session.
    
    Request body:
    {
        "session_type": "targeted",  # or "mixed", "exam_simulation"
        "primary_topic_ids": ["topic_001"],
        "subject": "Mathematics",
        "syllabus_version": "2025_v1",
        "max_questions": 20,
        "difficulty_distribution": {"easy": 0.4, "medium": 0.4, "hard": 0.2}
    }
    
    Returns complete practice session with questions.
    """
    try:
        engine_registry = EngineRegistry()
        engine = engine_registry.get("practice_assembly")
        
        # Add user_id to payload
        payload["user_id"] = current_user["user_id"]
        
        context = ExecutionContext(
            trace_id=f"practice_{datetime.utcnow().timestamp()}",
            user_id=current_user["user_id"],
            role=current_user["role"],
            timestamp=datetime.utcnow()
        )
        
        response = await engine.run(payload, context)
        
        if response.success:
            return {
                "success": True,
                "session": response.data["practice_session"],
                "metadata": {
                    "total_questions": response.data["total_questions"],
                    "estimated_duration_minutes": response.data["estimated_duration_minutes"],
                    "difficulty_breakdown": response.data["difficulty_breakdown"],
                    "related_topics_added": response.data["related_topics_added"]
                },
                "trace_id": response.trace.trace_id
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# AI Routing Endpoints (Admin/Monitoring)
# ========================================

@router.post("/routing/check")
async def check_routing(
    payload: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Check AI routing decision (for monitoring/debugging).
    
    Request body:
    {
        "request_type": "marking",
        "prompt_hash": "abc123...",
        "evidence_hash": "def456...",
        "user_tier": "free"
    }
    
    Returns routing decision (cache hit, model selection, cost estimate).
    """
    try:
        engine_registry = EngineRegistry()
        engine = engine_registry.get("ai_routing_cost_control")
        
        # Add required fields
        payload["user_id"] = current_user["user_id"]
        payload["school_id"] = current_user.get("school_id", "unknown")
        
        # Default cost policy
        if "cost_policy" not in payload:
            payload["cost_policy"] = {
                "daily_limit_usd": 5.0,
                "monthly_limit_usd": 150.0,
                "school_monthly_limit_usd": 10000.0,
                "allow_oss_models": True,
                "auto_escalate_on_low_confidence": True,
                "escalation_confidence_threshold": 0.7,
                "emergency_kill_switch": False
            }
        
        context = ExecutionContext(
            trace_id=f"routing_{datetime.utcnow().timestamp()}",
            user_id=current_user["user_id"],
            role=current_user["role"],
            timestamp=datetime.utcnow()
        )
        
        response = await engine.run(payload, context)
        
        if response.success:
            return {
                "success": True,
                "routing_decision": response.data["routing_decision"],
                "cache_decision": response.data["cache_decision"],
                "model_selection": response.data.get("model_selection"),
                "cost_estimate_usd": response.data["cost_estimate_usd"],
                "budget_remaining": {
                    "daily": response.data["cost_limit_remaining_usd"],
                    "school_monthly": response.data["school_cost_remaining_usd"]
                },
                "trace_id": response.trace.trace_id
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
