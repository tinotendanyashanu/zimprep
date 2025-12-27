"""Engine Registry for ZimPrep.

PHASE ZERO: COMPLETE ENGINE REGISTRATION

This module is responsible for:
1. Registering ALL engines required by pipeline definitions
2. Providing centralized engine access to the orchestrator
3. Validating registry completeness on startup

CRITICAL RULES:
- ALL engines MUST be registered (no conditional registration)
- Registry MUST be complete before orchestrator can execute
- Missing engines = FATAL startup error
"""

import logging

logger = logging.getLogger(__name__)


class EngineRegistry:
    """Registry for managing and accessing engines.
    
    PHASE ZERO: This registry MUST contain all engines referenced
    in pipeline definitions. Incomplete registry = startup failure.
    """
    
    def __init__(self):
        self._engines = {}

    def register(self, name: str, engine):
        """Register an engine by name.
        
        Args:
            name: Engine name (must match pipeline definitions)
            engine: Engine instance
        """
        self._engines[name] = engine
        logger.debug(f"Registered engine: {name}")

    def get(self, name: str):
        """Get an engine by name.
        
        Args:
            name: Engine name
            
        Returns:
            Engine instance or None if not found
        """
        return self._engines.get(name)
    
    def validate_completeness(self, required_engines: set[str]) -> None:
        """Validate that all required engines are registered.
        
        PHASE ZERO: FAIL-FAST validation.
        
        Args:
            required_engines: Set of engine names that MUST be registered
            
        Raises:
            RuntimeError: If any required engine is missing
        """
        registered = set(self._engines.keys())
        missing = required_engines - registered
        
        if missing:
            raise RuntimeError(
                f"FATAL: {len(missing)} required engines not registered: {sorted(missing)}"
            )
        
        logger.info(
            f"Engine registry completeness validated: "
            f"{len(registered)} engines registered"
        )


# Global registry instance
engine_registry = EngineRegistry()


def _register_engines():
    """Register ALL engines in the system.
    
    PHASE ZERO: This function registers ALL 18+ engines.
    NO conditional registration allowed.
    NO environment-based skipping allowed.
    
    Missing engines = FATAL startup error.
    """
    logger.info("Starting engine registration...")
    
    # =============================================================================
    # CORE ENGINES (9 engines)
    # =============================================================================
    
    # Engine 1: Exam Structure
    from app.engines.exam_structure.engine import ExamStructureEngine
    engine_registry.register("exam_structure", ExamStructureEngine())
    
    # Engine 2: Session Timing
    from app.engines.session_timing.engine import SessionTimingEngine
    engine_registry.register("session_timing", SessionTimingEngine())
    
    # Engine 3: Question Delivery
    from app.engines.question_delivery.engine import QuestionDeliveryEngine
    engine_registry.register("question_delivery", QuestionDeliveryEngine())
    
    # Engine 4: Submission
    from app.engines.submission.engine import SubmissionEngine
    engine_registry.register("submission", SubmissionEngine())
    
    # Engine 5: Results
    from app.engines.results.engine import ResultsEngine
    engine_registry.register("results", ResultsEngine())
    
    # Engine 6: Reporting & Analytics
    from app.engines.reporting_analytics.engine import ReportingAnalyticsEngine
    engine_registry.register("reporting", ReportingAnalyticsEngine())
    
    # Engine 7: Audit & Compliance
    from app.engines.audit_compliance.engine import AuditComplianceEngine
    engine_registry.register("audit_compliance", AuditComplianceEngine())
    
    # Engine 8: Background Processing
    from app.engines.background_processing.engine import BackgroundProcessingEngine
    engine_registry.register("background_processing", BackgroundProcessingEngine())
    
    # Engine 9: Identity & Subscription
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine
    engine_registry.register("identity_subscription", IdentitySubscriptionEngine())
    
    # =============================================================================
    # AI ENGINES (8 engines)
    # =============================================================================
    
    # AI Engine 1: Embedding
    from app.engines.ai.embedding.engine import EmbeddingEngine
    engine_registry.register("embedding", EmbeddingEngine())
    
    # AI Engine 2: Retrieval
    from app.engines.ai.retrieval.engine import RetrievalEngine
    engine_registry.register("retrieval", RetrievalEngine())
    
    # AI Engine 3: Reasoning & Marking
    from app.engines.ai.reasoning_marking.engine import ReasoningMarkingEngine
    engine_registry.register("reasoning_marking", ReasoningMarkingEngine())
    
    # AI Engine 4: Validation & Consistency
    from app.engines.ai.validation_consistency.engine import ValidationConsistencyEngine
    engine_registry.register("validation", ValidationConsistencyEngine())
    
    # AI Engine 5: Recommendation (uses adapter for orchestrator compatibility)
    from app.engines.ai.recommendation.adapter import RecommendationEngineAdapter
    engine_registry.register("recommendation", RecommendationEngineAdapter())
    
    # AI Engine 6: Handwriting Interpretation
    from app.engines.ai.handwriting_interpretation.engine import HandwritingInterpretationEngine
    engine_registry.register("handwriting_interpretation", HandwritingInterpretationEngine())
    
    # AI Engine 7: AI Routing & Cost Control
    from app.engines.ai.ai_routing_cost_control.engine import AIRoutingCostControlEngine
    engine_registry.register("ai_routing_cost_control", AIRoutingCostControlEngine())
    
    # AI Engine 8: Topic Intelligence
    from app.engines.ai.topic_intelligence.engine import TopicIntelligenceEngine
    engine_registry.register("topic_intelligence", TopicIntelligenceEngine())
    
    # =============================================================================
    # INTELLIGENCE / ASSEMBLY ENGINES (2 engines)
    # =============================================================================
    
    # Intelligence Engine 1: Practice Assembly
    from app.engines.core.practice_assembly.engine import PracticeAssemblyEngine
    engine_registry.register("practice_assembly", PracticeAssemblyEngine())
    
    # Intelligence Engine 2: Appeal Reconstruction
    from app.engines.appeal_reconstruction.engine import AppealReconstructionEngine
    engine_registry.register("appeal_reconstruction", AppealReconstructionEngine())
    
    # =============================================================================
    # PHASE THREE: LEARNING ANALYTICS ENGINES (2 engines)
    # =============================================================================
    
    # Analytics Engine 1: Learning Analytics
    from app.engines.learning_analytics.engine import LearningAnalyticsEngine
    engine_registry.register("learning_analytics", LearningAnalyticsEngine())
    
    # Analytics Engine 2: Mastery Modeling
    from app.engines.mastery_modeling.engine import MasteryModelingEngine
    engine_registry.register("mastery_modeling", MasteryModelingEngine())
    
    # =============================================================================
    # PHASE FOUR: INSTITUTIONAL & GOVERNANCE ANALYTICS (2 engines)
    # =============================================================================
    
    # Analytics Engine 3: Institutional Analytics
    from app.engines.institutional_analytics.engine import InstitutionalAnalyticsEngine
    engine_registry.register("institutional_analytics", InstitutionalAnalyticsEngine())
    
    # Analytics Engine 4: Governance Reporting
    from app.engines.governance_reporting.engine import GovernanceReportingEngine
    engine_registry.register("governance_reporting", GovernanceReportingEngine())
    
    # =============================================================================
    # REGISTRATION COMPLETE
    # =============================================================================
    
    total_engines = len(engine_registry._engines)
    logger.info(f"✓ Engine registration complete: {total_engines} engines registered")
    logger.info(f"✓ Registered engines: {sorted(engine_registry._engines.keys())}")


# CRITICAL: Call registration on module import
# This ensures engines are available when orchestrator initializes
_register_engines()
