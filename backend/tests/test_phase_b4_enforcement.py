"""Integration tests for Phase B4 feature enforcement.

Tests the orchestrator's centralized entitlement enforcement:
1. Appeal access blocked for FREE tier
2. PDF/CSV export enforcement
3. Audit includes entitlement snapshot
"""

import pytest
from datetime import datetime
from app.orchestrator.orchestrator import orchestrator, AccessDeniedError
from app.orchestrator.execution_context import ExecutionContext


class TestPhaseB4Enforcement:
    """Integration tests for Phase B4 entitlement enforcement."""
    
    @pytest.mark.asyncio
    async def test_appeal_blocked_on_free_tier(self):
        """Test that appeal pipeline blocks FREE tier users before any engine runs."""
        # Create context with FREE tier (appeal_access = False)
        context = ExecutionContext.create(user_id="free_user")
        context.feature_flags_snapshot = {
            "ai_marking_basic": True,
            "appeal_access": False,  # FREE tier doesn't have appeals
            "report_export_pdf": False,
            "report_export_csv": False,
        }
        
        # Attempt to execute appeal reconstruction pipeline
        with pytest.raises(AccessDeniedError) as exc_info:
            await orchestrator.execute_pipeline(
                "appeal_reconstruction_v1",
                payload={"exam_id": "test123"},
                context=context
            )
        
        # Verify error message
        assert "appeal_access" in str(exc_info.value)
        assert exc_info.value.required_feature == "appeal_access"
        assert exc_info.value.trace_id == context.trace_id
    
    @pytest.mark.asyncio
    async def test_appeal_allowed_for_student_plus(self):
        """Test that STUDENT_PLUS users can access appeals."""
        # Create context with STUDENT_PLUS tier (appeal_access = True)
        context = ExecutionContext.create(user_id="plus_user")
        context.feature_flags_snapshot = {
            "ai_marking_basic": True,
            "ai_marking_detailed": True,
            "appeal_access": True,  # STUDENT_PLUS has appeals
            "report_export_pdf": True,
            "report_export_csv": False,
        }
        
        # This should NOT raise AccessDeniedError
        # NOTE: Will still fail if engines aren't properly set up, but that's expected
        try:
            result = await orchestrator.execute_pipeline(
                "appeal_reconstruction_v1",
                payload={
                    "exam_id": "test123",
                    "original_trace_id": "original_trace",
                },
                context=context
            )
            # If we get here, entitlement check passed
            assert True
        except AccessDeniedError:
            pytest.fail("STUDENT_PLUS user should have appeal access")
        except Exception as e:
            # Other errors (missing engines, etc.) are acceptable for this test
            # We only care that AccessDeniedError was NOT raised
            pass
    
    @pytest.mark.asyncio
    async def test_pdf_export_blocked_without_flag(self):
        """Test that PDF export is blocked for users without report_export_pdf."""
        context = ExecutionContext.create(user_id="free_user")
        context.feature_flags_snapshot = {
            "ai_marking_basic": True,
            "report_export_pdf": False,  # FREE tier doesn't have PDF export
        }
        
        # Simulate PDF export request (would be called by reporting/export endpoint)
        with pytest.raises(AccessDeniedError) as exc_info:
            orchestrator._enforce_feature(
                "report_export_pdf",
                context,
                context.trace_id
            )
        
        assert "report_export_pdf" in str(exc_info.value)
        assert exc_info.value.required_feature == "report_export_pdf"
    
    @pytest.mark.asyncio
    async def test_csv_export_school_only(self):
        """Test that CSV export requires SCHOOL tier."""
        # STUDENT_PLUS tier (no CSV)
        context_plus = ExecutionContext.create(user_id="plus_user")
        context_plus.feature_flags_snapshot = {
            "report_export_pdf": True,
            "report_export_csv": False,  # STUDENT_PLUS doesn't have CSV
        }
        
        with pytest.raises(AccessDeniedError):
            orchestrator._enforce_feature(
                "report_export_csv",
                context_plus,
                context_plus.trace_id
            )
        
        # SCHOOL tier (has CSV)
        context_school = ExecutionContext.create(user_id="school_user")
        context_school.feature_flags_snapshot = {
            "report_export_pdf": True,
            "report_export_csv": True,  # SCHOOL has CSV
        }
        
        # Should NOT raise
        try:
            orchestrator._enforce_feature(
                "report_export_csv",
                context_school,
                context_school.trace_id
            )
        except AccessDeniedError:
            pytest.fail("SCHOOL tier should have CSV export access")
    
    def test_audit_includes_entitlements(self):
        """Test that audit input schema accepts entitlement fields."""
        from app.engines.audit_compliance.schemas.input import AuditComplianceInput
        from app.engines.audit_compliance.schemas.cost_metadata import AICostMetadata
        AuditComplianceInput.model_rebuild()
        
        # Create audit input with entitlements
        audit_data = {
            "trace_id": "test_trace",
            "student_id": "student123",
            "exam_id": "exam456",
            "session_id": "session789",
            "submission_id": "sub001",
            "engine_execution_log": [],
            "ai_evidence_refs": [],
            "validation_decisions": [],
            "policy_metadata": {
                "platform_version": "1.0.0",
                "marking_scheme_version": "2024",
                "syllabus_version": "2024",
                "exam_regulations_version": "2024.1",
                "policy_effective_date": datetime.utcnow(),
            },
            "final_grade": "A",
            "final_score": 85.5,
            "feature_flags": {},
            # PHASE B4 fields
            "subscription_tier": "student_plus",
            "feature_flags_snapshot": {
                "ai_marking_basic": True,
                "ai_marking_detailed": True,
                "appeal_access": True,
                "report_export_pdf": True,
                "report_export_csv": False,
            }
        }
        
        # Should validate without errors
        audit_input = AuditComplianceInput(**audit_data)
        
        # Verify fields are populated
        assert audit_input.subscription_tier == "student_plus"
        assert audit_input.feature_flags_snapshot["appeal_access"] == True
        assert audit_input.feature_flags_snapshot["report_export_csv"] == False
        
        print("✅ Audit schema accepts entitlement fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
