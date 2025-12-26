"""Model selection service for AI routing.

Selects the appropriate AI model based on request type, user tier, and cost policies.
"""

import logging
from typing import Literal

from app.engines.ai.ai_routing_cost_control.schemas.decision import ModelSelection, CostPolicy
from app.engines.ai.ai_routing_cost_control.errors import ModelSelectionError

logger = logging.getLogger(__name__)


class ModelSelector:
    """Service for selecting AI models based on request type and policies.
    
    Model Selection Rules:
    - **Marking**: OSS for free tier, paid for premium/enterprise
    - **OCR**: Always paid (GPT-4o Vision) for accuracy
    - **Embedding**: Always OSS (sentence-transformers) - cheap enough
    - **Recommendation**: Paid (requires reasoning capabilities)
    - **Escalation**: Paid model if OSS confidence < threshold
    """
    
    # Model definitions
    MODELS = {
        "oss": {
            "marking": "mixtral-8x7b",  # Placeholder OSS model
            "embedding": "sentence-transformers/all-MiniLM-L6-v2",
        },
        "paid": {
            "marking": "gpt-4o",
            "ocr": "gpt-4o",
            "recommendation": "gpt-4o",
            "embedding": "text-embedding-3-small",  # OpenAI embedding
        }
    }
    
    # Cost estimates (USD per request, approximate)
    COST_ESTIMATES = {
        "mixtral-8x7b": 0.001,          # OSS marking
        "gpt-4o": 0.02,                  # Paid marking/OCR/recommendation
        "sentence-transformers/all-MiniLM-L6-v2": 0.0,  # Free (self-hosted)
        "text-embedding-3-small": 0.0001,  # Paid embedding (very cheap)
    }
    
    def select_model(
        self,
        request_type: Literal["marking", "embedding", "ocr", "recommendation"],
        user_tier: Literal["free", "premium", "enterprise"],
        cost_policy: CostPolicy,
        is_escalation: bool = False
    ) -> ModelSelection:
        """Select appropriate model for the request.
        
        Args:
            request_type: Type of AI request
            user_tier: User subscription tier
            cost_policy: Cost policy configuration
            is_escalation: True if this is an escalation from OSS to paid
            
        Returns:
            ModelSelection with selected model and cost estimate
            
        Raises:
            ModelSelectionError: If model selection fails
        """
        logger.info(
            f"Selecting model for {request_type} (tier={user_tier}, escalation={is_escalation})"
        )
        
        # Rule 1: OCR always uses paid model (accuracy critical)
        if request_type == "ocr":
            return self._build_selection(
                model="gpt-4o",
                tier="paid",
                reason="OCR requires premium model for accuracy"
            )
        
        # Rule 2: Recommendation always uses paid model (reasoning required)
        if request_type == "recommendation":
            return self._build_selection(
                model="gpt-4o",
                tier="paid",
                reason="Recommendation requires reasoning capabilities"
            )
        
        # Rule 3: Embedding - prefer OSS (cheap enough, good quality)
        if request_type == "embedding":
            if cost_policy.allow_oss_models:
                return self._build_selection(
                    model="sentence-transformers/all-MiniLM-L6-v2",
                    tier="oss",
                    reason="OSS embedding model is sufficient and free"
                )
            else:
                return self._build_selection(
                    model="text-embedding-3-small",
                    tier="paid",
                    reason="Paid embedding requested by policy"
                )
        
        # Rule 4: Marking - tier-based selection
        if request_type == "marking":
            # Escalation overrides tier
            if is_escalation:
                return self._build_selection(
                    model="gpt-4o",
                    tier="paid",
                    reason="Escalated from OSS due to low confidence"
                )
            
            # Premium/enterprise tiers use paid models
            if user_tier in ["premium", "enterprise"]:
                return self._build_selection(
                    model="gpt-4o",
                    tier="paid",
                    reason=f"{user_tier} tier uses premium marking model"
                )
            
            # Free tier uses OSS if allowed
            if cost_policy.allow_oss_models:
                return self._build_selection(
                    model="mixtral-8x7b",
                    tier="oss",
                    reason="Free tier uses OSS marking model"
                )
            else:
                return self._build_selection(
                    model="gpt-4o",
                    tier="paid",
                    reason="OSS models disabled by policy"
                )
        
        # Should never reach here
        raise ModelSelectionError(
            request_type=request_type,
            reason=f"No model selection rule for request type: {request_type}"
        )
    
    def _build_selection(
        self,
        model: str,
        tier: Literal["oss", "paid"],
        reason: str
    ) -> ModelSelection:
        """Build ModelSelection object."""
        cost_estimate = self.COST_ESTIMATES.get(model, 0.0)
        
        return ModelSelection(
            selected_model=model,
            model_tier=tier,
            selection_reason=reason,
            estimated_cost_usd=cost_estimate
        )
    
    def should_escalate(
        self,
        confidence: float,
        cost_policy: CostPolicy
    ) -> bool:
        """Determine if OSS result should escalate to paid model.
        
        Args:
            confidence: Confidence score from OSS model
            cost_policy: Cost policy with escalation threshold
            
        Returns:
            True if escalation recommended
        """
        if not cost_policy.auto_escalate_on_low_confidence:
            return False
        
        return confidence < cost_policy.escalation_confidence_threshold
