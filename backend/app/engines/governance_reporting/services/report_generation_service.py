"""Report Generation Service - Consolidated governance reporting logic.

PHASE FOUR: Deterministic report generation from audit data.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from statistics import mean

from app.engines.governance_reporting.schemas.output import (
    AIUsageSummary,
    EscalationReason,
    ValidationStatistics,
    VetoReason,
    AppealStatistics,
    CostTransparency,
    ModelCostBreakdown,
    FairnessIndicators,
    TopicDifficulty,
    SystemHealth,
    FailureBreakdown
)

logger = logging.getLogger(__name__)


class ReportGenerationService:
    """Service for generating governance reports from audit data.
    
    CRITICAL RULES:
    - NO AI involved
    - DETERMINISTIC calculations only
    - NO student-identifiable data
    - Full explainability
    """
    
    @staticmethod
    def generate_ai_usage_summary(
        cost_tracking_records: List[Dict[str, Any]],
        trace_id: str
    ) -> AIUsageSummary:
        """Generate AI usage summary from cost tracking data.
        
        Args:
            cost_tracking_records: AI cost tracking documents
            trace_id: Request trace ID
            
        Returns:
            AI usage summary
        """
        total_calls = len(cost_tracking_records)
        oss_calls = sum(1 for rec in cost_tracking_records if "oss" in rec.get("model", "").lower())
        paid_calls = total_calls - oss_calls
        
        cache_hits = sum(1 for rec in cost_tracking_records if rec.get("cache_hit", False))
        cache_hit_rate = (cache_hits / total_calls) if total_calls > 0 else 0.0
        
        # Aggregate escalation reasons
        escalation_counts: Dict[str, int] = defaultdict(int)
        for rec in cost_tracking_records:
            reason = rec.get("escalation_reason")
            if reason:
                escalation_counts[reason] += 1
        
        escalation_reasons = [
            EscalationReason(reason=reason, count=count)
            for reason, count in escalation_counts.items()
        ]
        
        logger.debug(
            f"[{trace_id}] AI usage: total={total_calls}, oss={oss_calls}, "
            f"paid={paid_calls}, cache_hit_rate={cache_hit_rate:.2%}"
        )
        
        return AIUsageSummary(
            total_ai_calls=total_calls,
            oss_model_calls=oss_calls,
            paid_model_calls=paid_calls,
            cache_hit_rate=cache_hit_rate,
            escalation_reasons=escalation_reasons
        )
    
    @staticmethod
    def generate_validation_statistics(
        audit_records: List[Dict[str, Any]],
        trace_id: str
    ) -> ValidationStatistics:
        """Generate validation statistics from audit trail.
        
        Args:
            audit_records: Audit trail documents
            trace_id: Request trace ID
            
        Returns:
            Validation statistics
        """
        # Filter for validation engine records
        validation_records = [
            rec for rec in audit_records
            if rec.get("engine_name") == "validation"
        ]
        
        total_validations = len(validation_records)
        
        # Count vetoes (validation failures)
        vetoes = [
            rec for rec in validation_records
            if not rec.get("engine_output", {}).get("passed", True)
        ]
        veto_count = len(vetoes)
        veto_rate = (veto_count / total_validations) if total_validations > 0 else 0.0
        
        # Aggregate veto reasons
        veto_reason_counts: Dict[str, int] = defaultdict(int)
        for veto in vetoes:
            violations = veto.get("engine_output", {}).get("violations", [])
            for violation in violations:
                rule = violation.get("rule_name", "unknown")
                veto_reason_counts[rule] += 1
        
        veto_reasons = [
            VetoReason(reason=reason, count=count)
            for reason, count in veto_reason_counts.items()
        ]
        
        logger.debug(
            f"[{trace_id}] Validation: total={total_validations}, "
            f"vetoes={veto_count}, rate={veto_rate:.2%}"
        )
        
        return ValidationStatistics(
            total_validations=total_validations,
            veto_count=veto_count,
            veto_rate=veto_rate,
            veto_reasons=veto_reasons
        )
    
    @staticmethod
    def generate_appeal_statistics(
        appeal_records: List[Dict[str, Any]],
        trace_id: str
    ) -> AppealStatistics:
        """Generate appeal statistics.
        
        Args:
            appeal_records: Appeal reconstruction documents
            trace_id: Request trace ID
            
        Returns:
            Appeal statistics
        """
        total_appeals = len(appeal_records)
        
        # Simplified: In production, query appeal status
        granted = sum(1 for rec in appeal_records if rec.get("status") == "granted")
        denied = sum(1 for rec in appeal_records if rec.get("status") == "denied")
        pending = total_appeals - granted - denied
        
        # Calculate average resolution time
        resolution_times = []
        for rec in appeal_records:
            created_at = rec.get("created_at")
            resolved_at = rec.get("resolved_at")
            if created_at and resolved_at:
                delta = (resolved_at - created_at).total_seconds() / 3600  # hours
                resolution_times.append(delta)
        
        avg_resolution_hours = mean(resolution_times) if resolution_times else 0.0
        
        logger.debug(
            f"[{trace_id}] Appeals: total={total_appeals}, granted={granted}, "
            f"denied={denied}, avg_resolution={avg_resolution_hours:.1f}h"
        )
        
        return AppealStatistics(
            total_appeals=total_appeals,
            appeals_granted=granted,
            appeals_denied=denied,
            appeals_pending=pending,
            average_resolution_time_hours=avg_resolution_hours
        )
    
    @staticmethod
    def generate_cost_transparency(
        cost_tracking_records: List[Dict[str, Any]],
        trace_id: str
    ) -> CostTransparency:
        """Generate cost transparency summary.
        
        Args:
            cost_tracking_records: AI cost tracking documents
            trace_id: Request trace ID
            
        Returns:
            Cost transparency summary
        """
        total_cost = sum(rec.get("cost_usd", 0.0) for rec in cost_tracking_records)
        
        # Get unique student and exam counts
        unique_students = len(set(rec.get("user_id") for rec in cost_tracking_records))
        unique_exams = len(set(rec.get("trace_id") for rec in cost_tracking_records))
        
        cost_per_student = (total_cost / unique_students) if unique_students > 0 else 0.0
        cost_per_exam = (total_cost / unique_exams) if unique_exams > 0 else 0.0
        
        # Aggregate by model
        model_costs: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "cost": 0.0})
        for rec in cost_tracking_records:
            model = rec.get("model", "unknown")
            model_costs[model]["count"] += 1
            model_costs[model]["cost"] += rec.get("cost_usd", 0.0)
        
        model_breakdown = [
            ModelCostBreakdown(
                model_name=model,
                usage_count=data["count"],
                total_cost=data["cost"]
            )
            for model, data in model_costs.items()
        ]
        
        logger.debug(
            f"[{trace_id}] Cost: total=${total_cost:.2f}, "
            f"per_student=${cost_per_student:.2f}, per_exam=${cost_per_exam:.2f}"
        )
        
        return CostTransparency(
            total_cost_usd=total_cost,
            cost_per_student=cost_per_student,
            cost_per_exam=cost_per_exam,
            model_breakdown=model_breakdown
        )
    
    @staticmethod
    def generate_fairness_indicators(
        exam_results: List[Dict[str, Any]],
        trace_id: str
    ) -> FairnessIndicators:
        """Generate fairness indicators (DESCRIPTIVE ONLY).
        
        Args:
            exam_results: Exam result documents
            trace_id: Request trace ID
            
        Returns:
            Fairness indicators
        """
        # Calculate mark distribution variance
        all_percentages = [rec.get("percentage", 0.0) for rec in exam_results]
        
        if len(all_percentages) > 1:
            avg = mean(all_percentages)
            variance = sum((x - avg) ** 2 for x in all_percentages) / len(all_percentages)
        else:
            variance = 0.0
        
        # Topic difficulty consistency (simplified)
        # In production, group by cohort and calculate variance
        topic_difficulty: List[TopicDifficulty] = []
        
        logger.debug(
            f"[{trace_id}] Fairness: mark_variance={variance:.2f}"
        )
        
        return FairnessIndicators(
            mark_distribution_variance=variance,
            topic_difficulty_consistency=topic_difficulty
        )
    
    @staticmethod
    def generate_system_health(
        audit_records: List[Dict[str, Any]],
        trace_id: str
    ) -> SystemHealth:
        """Generate system health metrics.
        
        Args:
            audit_records: Audit trail documents
            trace_id: Request trace ID
            
        Returns:
            System health metrics
        """
        total_requests = len(audit_records)
        
        # Count successes/failures
        successes = sum(1 for rec in audit_records if rec.get("status") == "success")
        success_rate = (successes / total_requests) if total_requests > 0 else 0.0
        
        # Calculate average latency
        latencies = [
            rec.get("execution_time_ms", 0.0)
            for rec in audit_records
            if rec.get("execution_time_ms")
        ]
        avg_latency = mean(latencies) if latencies else 0.0
        
        # Aggregate failure types
        failure_counts: Dict[str, int] = defaultdict(int)
        for rec in audit_records:
            if rec.get("status") == "failure":
                error_type = rec.get("error_type", "unknown")
                failure_counts[error_type] += 1
        
        failure_breakdown = [
            FailureBreakdown(error_type=error_type, count=count)
            for error_type, count in failure_counts.items()
        ]
        
        logger.debug(
            f"[{trace_id}] Health: requests={total_requests}, "
            f"success_rate={success_rate:.2%}, latency={avg_latency:.1f}ms"
        )
        
        return SystemHealth(
            total_requests=total_requests,
            success_rate=success_rate,
            average_latency_ms=avg_latency,
            failure_breakdown=failure_breakdown
        )
