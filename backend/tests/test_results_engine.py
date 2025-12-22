"""Comprehensive tests for the Results Engine.

Tests all components: schemas, services, repository, and engine.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from app.engines.results.schemas.input import (
    ResultsInput,
    PaperInput,
    SectionBreakdown,
)
from app.engines.results.schemas.output import (
    ResultsOutput,
    PaperResult,
    TopicBreakdown,
)
from app.engines.results.schemas.grading import (
    GradeBoundary,
    GradingScale,
)
from app.engines.results.services.aggregation_service import AggregationService
from app.engines.results.services.grading_service import GradingService
from app.engines.results.services.breakdown_service import BreakdownService
from app.engines.results.repository.results_repo import ResultsRepository
from app.engines.results.engine import ResultsEngine
from app.engines.results.errors.exceptions import (
    MarkOverflowError,
    InvalidWeightingError,
    DuplicateResultError,
)
from app.orchestrator.execution_context import ExecutionContext


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_grading_scale():
    """Sample grading scale for testing."""
    return GradingScale(
        subject_code="MATH",
        syllabus_version="2024",
        boundaries=[
            GradeBoundary(grade="A*", min_marks=90, max_marks=100),
            GradeBoundary(grade="A", min_marks=80, max_marks=89),
            GradeBoundary(grade="B", min_marks=70, max_marks=79),
            GradeBoundary(grade="C", min_marks=60, max_marks=69),
            GradeBoundary(grade="D", min_marks=50, max_marks=59),
            GradeBoundary(grade="E", min_marks=40, max_marks=49),
            GradeBoundary(grade="U", min_marks=0, max_marks=39),
        ],
        pass_mark=40.0,
        max_total_marks=100.0
    )


@pytest.fixture
def sample_papers():
    """Sample paper inputs for testing."""
    return [
        PaperInput(
            paper_code="P1",
            paper_name="Paper 1: Pure Mathematics",
            max_marks=100.0,
            awarded_marks=75.0,
            weighting=0.5,
            section_breakdown=[
                SectionBreakdown(
                    topic_code="ALG",
                    topic_name="Algebra",
                    max_marks=50.0,
                    awarded_marks=40.0
                ),
                SectionBreakdown(
                    topic_code="CALC",
                    topic_name="Calculus",
                    max_marks=50.0,
                    awarded_marks=35.0
                ),
            ]
        ),
        PaperInput(
            paper_code="P2",
            paper_name="Paper 2: Statistics & Mechanics",
            max_marks=100.0,
            awarded_marks=85.0,
            weighting=0.5,
            section_breakdown=[
                SectionBreakdown(
                    topic_code="STATS",
                    topic_name="Statistics",
                    max_marks=60.0,
                    awarded_marks=50.0
                ),
                SectionBreakdown(
                    topic_code="MECH",
                    topic_name="Mechanics",
                    max_marks=40.0,
                    awarded_marks=35.0
                ),
            ]
        ),
    ]


@pytest.fixture
def sample_results_input(sample_papers, sample_grading_scale):
    """Sample ResultsInput for testing."""
    return ResultsInput(
        trace_id="test-trace-123",
        candidate_id="candidate-456",
        exam_id="exam-789",
        subject_code="MATH",
        subject_name="Mathematics",
        syllabus_version="2024",
        papers=sample_papers,
        grading_scale=sample_grading_scale,
        issued_at=datetime.utcnow()
    )


# ============================================================================
# SCHEMA VALIDATION TESTS
# ============================================================================

class TestSchemaValidation:
    """Test schema validation rules."""
    
    def test_valid_input_accepted(self, sample_results_input):
        """Test that valid input is accepted."""
        assert sample_results_input.trace_id == "test-trace-123"
        assert len(sample_results_input.papers) == 2
    
    def test_paper_weightings_must_sum_to_one(self, sample_grading_scale):
        """Test that paper weightings must sum to 1.0."""
        with pytest.raises(ValueError, match="sum to"):
            ResultsInput(
                trace_id="test",
                candidate_id="c1",
                exam_id="e1",
                subject_code="MATH",
                subject_name="Mathematics",
                syllabus_version="2024",
                papers=[
                    PaperInput(
                        paper_code="P1",
                        paper_name="Paper 1",
                        max_marks=100.0,
                        awarded_marks=75.0,
                        weighting=0.6,  # Wrong!
                        section_breakdown=[]
                    ),
                    PaperInput(
                        paper_code="P2",
                        paper_name="Paper 2",
                        max_marks=100.0,
                        awarded_marks=85.0,
                        weighting=0.5,  # Sums to 1.1
                        section_breakdown=[]
                    ),
                ],
                grading_scale=sample_grading_scale,
                issued_at=datetime.utcnow()
            )
    
    def test_awarded_marks_cannot_exceed_max(self):
        """Test that awarded marks validation catches overflow."""
        with pytest.raises(ValueError, match="exceed"):
            SectionBreakdown(
                topic_code="ALG",
                topic_name="Algebra",
                max_marks=50.0,
                awarded_marks=60.0  # Overflow!
            )
    
    def test_grading_scale_boundaries_validated(self):
        """Test that grading scale boundaries are validated."""
        # This should work
        scale = GradingScale(
            subject_code="MATH",
            syllabus_version="2024",
            boundaries=[
                GradeBoundary(grade="A", min_marks=80, max_marks=100),
                GradeBoundary(grade="B", min_marks=60, max_marks=79),
                GradeBoundary(grade="C", min_marks=0, max_marks=59),
            ],
            pass_mark=60.0,
            max_total_marks=100.0
        )
        assert scale.subject_code == "MATH"


# ============================================================================
# AGGREGATION SERVICE TESTS
# ============================================================================

class TestAggregationService:
    """Test aggregation service calculations."""
    
    def test_aggregate_section_marks(self):
        """Test section mark aggregation."""
        sections = [
            SectionBreakdown(
                topic_code="ALG",
                topic_name="Algebra",
                max_marks=50.0,
                awarded_marks=40.0
            ),
            SectionBreakdown(
                topic_code="CALC",
                topic_name="Calculus",
                max_marks=50.0,
                awarded_marks=35.0
            ),
        ]
        
        max_total, awarded_total = AggregationService.aggregate_section_marks(sections)
        
        assert max_total == 100.0
        assert awarded_total == 75.0
    
    def test_apply_paper_weighting(self):
        """Test paper weighting calculation."""
        # Paper: 75/100 marks, weighting 0.5 (50%)
        # Expected: (75/100) * (100 * 0.5) = 37.5
        
        weighted = AggregationService.apply_paper_weighting(
            awarded_marks=75.0,
            max_marks=100.0,
            weighting=0.5
        )
        
        assert weighted == 37.5
    
    def test_calculate_subject_total(self, sample_papers):
        """Test subject total calculation."""
        # P1: 75/100 * 0.5 = 37.5
        # P2: 85/100 * 0.5 = 42.5
        # Total: 80.0
        
        total = AggregationService.calculate_subject_total(sample_papers)
        
        assert total == 80.0
    
    def test_calculate_percentage(self):
        """Test percentage calculation."""
        percentage = AggregationService.calculate_percentage(
            awarded_marks=80.0,
            max_marks=100.0
        )
        
        assert percentage == 80.0
    
    def test_decimal_precision(self):
        """Test that calculations use proper decimal precision."""
        # Test a case that would fail with floating point
        weighted = AggregationService.apply_paper_weighting(
            awarded_marks=77.77,
            max_marks=100.0,
            weighting=0.333
        )
        
        # Should be rounded to 2 decimal places
        assert isinstance(weighted, float)
        assert len(str(weighted).split('.')[-1]) <= 2


# ============================================================================
# GRADING SERVICE TESTS
# ============================================================================

class TestGradingService:
    """Test grading service."""
    
    def test_resolve_grade_a_star(self, sample_grading_scale):
        """Test grade resolution for A* boundary."""
        grade = GradingService.resolve_grade(95.0, sample_grading_scale)
        assert grade == "A*"
    
    def test_resolve_grade_a(self, sample_grading_scale):
        """Test grade resolution for A boundary."""
        grade = GradingService.resolve_grade(85.0, sample_grading_scale)
        assert grade == "A"
    
    def test_resolve_grade_boundary_edge_case(self, sample_grading_scale):
        """Test grade resolution at exact boundary."""
        # 80 is the minimum for A
        grade = GradingService.resolve_grade(80.0, sample_grading_scale)
        assert grade == "A"
        
        # 79 is the maximum for B
        grade = GradingService.resolve_grade(79.0, sample_grading_scale)
        assert grade == "B"
    
    def test_determine_pass_status_pass(self, sample_grading_scale):
        """Test pass determination - passing case."""
        is_pass = GradingService.determine_pass_status(50.0, sample_grading_scale)
        assert is_pass is True
    
    def test_determine_pass_status_fail(self, sample_grading_scale):
        """Test pass determination - failing case."""
        is_pass = GradingService.determine_pass_status(35.0, sample_grading_scale)
        assert is_pass is False
    
    def test_get_grade_info(self, sample_grading_scale):
        """Test comprehensive grade info."""
        info = GradingService.get_grade_info(85.0, sample_grading_scale)
        
        assert info["grade"] == "A"
        assert info["pass_status"] is True
        assert info["total_marks"] == 85.0
        assert info["boundary_info"]["min_marks"] == 80.0


# ============================================================================
# BREAKDOWN SERVICE TESTS
# ============================================================================

class TestBreakdownService:
    """Test breakdown service."""
    
    def test_build_paper_breakdown(self, sample_papers):
        """Test paper breakdown generation."""
        results = BreakdownService.build_paper_breakdown(sample_papers)
        
        assert len(results) == 2
        assert results[0].paper_code == "P1"
        assert results[0].percentage == 75.0
        assert results[0].weighted_contribution == 37.5
        assert results[1].paper_code == "P2"
        assert results[1].percentage == 85.0
        assert results[1].weighted_contribution == 42.5
    
    def test_build_topic_breakdown(self, sample_papers):
        """Test topic breakdown generation."""
        breakdowns = BreakdownService.build_topic_breakdown(sample_papers)
        
        assert len(breakdowns) == 4  # ALG, CALC, STATS, MECH
        
        # Find algebra topic
        alg = next(b for b in breakdowns if b.topic_code == "ALG")
        assert alg.total_max_marks == 50.0
        assert alg.total_awarded_marks == 40.0
        assert alg.percentage == 80.0
        assert "P1" in alg.papers_covered
    
    def test_build_complete_breakdown(self, sample_papers):
        """Test complete breakdown."""
        paper_results, topic_breakdowns = BreakdownService.build_complete_breakdown(
            sample_papers
        )
        
        assert len(paper_results) == 2
        assert len(topic_breakdowns) == 4


# ============================================================================
# REPOSITORY TESTS
# ============================================================================

class TestResultsRepository:
    """Test results repository (with mocked MongoDB)."""
    
    @pytest.fixture
    def mock_mongo(self):
        """Mock MongoDB client."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        return mock_client, mock_collection
    
    def test_save_result_success(self, mock_mongo):
        """Test successful result persistence."""
        mock_client, mock_collection = mock_mongo
        repo = ResultsRepository(mock_client)
        
        # Mock successful insert
        mock_collection.insert_one.return_value = MagicMock(inserted_id="doc_123")
        
        output = ResultsOutput(
            trace_id="trace123",
            engine_name="results",
            engine_version="1.0.0",
            candidate_id="c1",
            exam_id="e1",
            subject_code="MATH",
            subject_name="Mathematics",
            syllabus_version="2024",
            total_marks=80.0,
            max_total_marks=100.0,
            percentage=80.0,
            grade="A",
            pass_status=True,
            paper_results=[],
            topic_breakdown=[],
            issued_at=datetime.utcnow()
        )
        
        doc_id = repo.save_result(output, "trace123")
        
        assert doc_id == "doc_123"
        mock_collection.insert_one.assert_called_once()
    
    def test_exists_check(self, mock_mongo):
        """Test existence check."""
        mock_client, mock_collection = mock_mongo
        repo = ResultsRepository(mock_client)
        
        mock_collection.count_documents.return_value = 1
        
        exists = repo.exists("c1", "e1", "MATH")
        
        assert exists is True
        mock_collection.count_documents.assert_called_once()


# ============================================================================
# ENGINE INTEGRATION TESTS
# ============================================================================

class TestResultsEngine:
    """Test Results Engine end-to-end."""
    
    @pytest.fixture
    def mock_engine(self):
        """Mock engine without repository."""
        return ResultsEngine(mongo_client=None)
    
    def test_successful_execution(self, mock_engine, sample_results_input):
        """Test successful engine execution."""
        context = ExecutionContext.create()
        
        payload = sample_results_input.model_dump()
        payload["trace_id"] = context.trace_id
        
        response = mock_engine.run(payload, context)
        
        assert response.success is True
        assert response.data is not None
        assert response.data.grade == "A"  # 80% = A
        assert response.data.total_marks == 80.0
        assert response.data.confidence == 1.0
        assert response.trace.engine_name == "results"
    
    def test_invalid_input_handling(self, mock_engine):
        """Test handling of invalid input."""
        context = ExecutionContext.create()
        
        # Missing required fields
        payload = {
            "trace_id": context.trace_id,
            "candidate_id": "c1",
            # Missing other required fields
        }
        
        response = mock_engine.run(payload, context)
        
        assert response.success is False
        assert response.error is not None
        assert "validation failed" in response.error.lower()
    
    def test_mark_overflow_handling(self, mock_engine, sample_grading_scale):
        """Test handling of mark overflow."""
        context = ExecutionContext.create()
        
        payload = {
            "trace_id": context.trace_id,
            "candidate_id": "c1",
            "exam_id": "e1",
            "subject_code": "MATH",
            "subject_name": "Mathematics",
            "syllabus_version": "2024",
            "papers": [
                {
                    "paper_code": "P1",
                    "paper_name": "Paper 1",
                    "max_marks": 100.0,
                    "awarded_marks": 150.0,  # OVERFLOW!
                    "weighting": 1.0,
                    "section_breakdown": []
                }
            ],
            "grading_scale": sample_grading_scale.model_dump(),
            "issued_at": datetime.utcnow().isoformat()
        }
        
        response = mock_engine.run(payload, context)
        
        assert response.success is False
        assert "exceed" in response.error.lower()
    
    def test_trace_id_propagation(self, mock_engine, sample_results_input):
        """Test that trace_id is propagated throughout execution."""
        context = ExecutionContext.create()
        
        payload = sample_results_input.model_dump()
        payload["trace_id"] = context.trace_id
        
        response = mock_engine.run(payload, context)
        
        assert response.success is True
        assert response.trace.trace_id == context.trace_id
        assert response.data.trace_id == context.trace_id
    
    def test_determinism(self, mock_engine, sample_results_input):
        """Test that same input produces same output."""
        context = ExecutionContext.create()
        
        payload = sample_results_input.model_dump()
        payload["trace_id"] = context.trace_id
        
        # Run twice
        response1 = mock_engine.run(payload, context)
        response2 = mock_engine.run(payload, context)
        
        assert response1.success is True
        assert response2.success is True
        
        # Results should be identical
        assert response1.data.total_marks == response2.data.total_marks
        assert response1.data.grade == response2.data.grade
        assert response1.data.percentage == response2.data.percentage


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test fail-closed error handling."""
    
    def test_mark_overflow_error_structure(self):
        """Test MarkOverflowError has proper structure."""
        error = MarkOverflowError(
            paper_code="P1",
            awarded_marks=150.0,
            max_marks=100.0,
            trace_id="trace123"
        )
        
        assert "P1" in str(error)
        assert "150" in str(error)
        assert error.trace_id == "trace123"
    
    def test_invalid_weighting_error_structure(self):
        """Test InvalidWeightingError has proper structure."""
        error = InvalidWeightingError(
            actual_sum=1.1,
            expected_sum=1.0,
            trace_id="trace123"
        )
        
        assert "1.1" in str(error)
        assert error.trace_id == "trace123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
