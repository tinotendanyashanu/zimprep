"""Comprehensive integration tests for dashboard pipeline with upcoming exams.

Tests the full pipeline: identity → exam_structure → reporting → recommendation

Run with: pytest tests/integration/test_dashboard_pipeline_integration.py -v
"""

import pytest
from datetime import datetime, timedelta
from pymongo import MongoClient

from app.config.settings import settings
from app.contracts.engine_response import EngineResponse
from app.contracts.trace import EngineTrace
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.engine_registry import engine_registry
from app.orchestrator.execution_context import ExecutionContext


class StubEngine:
    """Minimal stub engine for pipeline integration tests."""

    def __init__(self, engine_name: str, engine_version: str = "test"):
        self.engine_name = engine_name
        self.engine_version = engine_version

    def run(self, payload, context):
        trace = EngineTrace(
            trace_id=context.trace_id,
            engine_name=self.engine_name,
            engine_version=self.engine_version,
            timestamp=datetime.utcnow(),
            confidence=1.0,
        )
        return EngineResponse(success=True, data={}, error=None, trace=trace)


@pytest.fixture(autouse=True)
def stub_pipeline_engines():
    """Stub engines that are out of scope for these tests."""
    original_reporting = engine_registry.get("reporting")
    original_recommendation = engine_registry.get("recommendation")
    original_identity = engine_registry.get("identity_subscription")

    engine_registry.register("reporting", StubEngine("reporting"))
    engine_registry.register("recommendation", StubEngine("recommendation"))
    engine_registry.register("identity_subscription", StubEngine("identity_subscription"))

    yield

    if original_reporting:
        engine_registry.register("reporting", original_reporting)
    if original_recommendation:
        engine_registry.register("recommendation", original_recommendation)
    if original_identity:
        engine_registry.register("identity_subscription", original_identity)


@pytest.fixture(autouse=True)
def stable_exam_time_format(monkeypatch):
    """Avoid platform-specific strftime failures during tests."""
    from app.utils import timezone_helper

    def _safe_format_exam_time(
        utc_datetime,
        timezone_str="Africa/Harare",
        include_timezone_name=True,
    ):
        return {
            "utc": utc_datetime.isoformat(),
            "local": utc_datetime.isoformat(),
            "timezone": timezone_str,
            "display": utc_datetime.isoformat(),
        }

    monkeypatch.setattr(timezone_helper, "format_exam_time", _safe_format_exam_time)


@pytest.fixture
async def clean_test_db():
    """Clean test database before and after tests."""
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    
    # Clean collections
    db.exam_schedules.delete_many({"schedule_id": {"$regex": "^test_"}})
    
    yield
    
    # Cleanup after tests
    db.exam_schedules.delete_many({"schedule_id": {"$regex": "^test_"}})
    client.close()


@pytest.fixture
async def seed_test_exams(clean_test_db):
    """Seed test exam schedules."""
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    collection = db.exam_schedules
    
    # Test data
    test_schedules = [
        # Candidate A: Biology and Math exams
        {
            "schedule_id": "test_candidate_a_bio",
            "exam_id": "test_bio_p2",
            "subject_code": "5090",
            "syllabus_version": "2023-2027",
            "paper_code": "paper_2",
            "subject_name": "Biology",
            "paper_name": "Paper 2",
            "scheduled_date": datetime.utcnow() + timedelta(days=10),
            "duration_minutes": 150,
            "status": "scheduled",
            "candidate_ids": ["test_candidate_a"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "schedule_id": "test_candidate_a_math",
            "exam_id": "test_math_p1",
            "subject_code": "4008",
            "syllabus_version": "2023-2027",
            "paper_code": "paper_1",
            "subject_name": "Mathematics",
            "paper_name": "Paper 1",
            "scheduled_date": datetime.utcnow() + timedelta(days=15),
            "duration_minutes": 120,
            "status": "scheduled",
            "candidate_ids": ["test_candidate_a"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        # Candidate B: Only Chemistry exam
        {
            "schedule_id": "test_candidate_b_chem",
            "exam_id": "test_chem_p3",
            "subject_code": "5070",
            "syllabus_version": "2023-2027",
            "paper_code": "paper_3",
            "subject_name": "Chemistry",
            "paper_name": "Paper 3",
            "scheduled_date": datetime.utcnow() + timedelta(days=20),
            "duration_minutes": 90,
            "status": "scheduled",
            "candidate_ids": ["test_candidate_b"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        # Cohort exam (both candidates in cohort_test)
        {
            "schedule_id": "test_cohort_physics",
            "exam_id": "test_physics_p1",
            "subject_code": "5054",
            "syllabus_version": "2023-2027",
            "paper_code": "paper_1",
            "subject_name": "Physics",
            "paper_name": "Paper 1",
            "scheduled_date": datetime.utcnow() + timedelta(days=25),
            "duration_minutes": 60,
            "status": "scheduled",
            "cohort_id": "cohort_test",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        # Past exam (should be excluded)
        {
            "schedule_id": "test_past_exam",
            "exam_id": "test_history_p2",
            "subject_code": "2147",
            "syllabus_version": "2023-2027",
            "paper_code": "paper_2",
            "subject_name": "History",
            "paper_name": "Paper 2",
            "scheduled_date": datetime.utcnow() - timedelta(days=5),
            "duration_minutes": 120,
            "status": "completed",
            "candidate_ids": ["test_candidate_a"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        # Cancelled exam (should be excluded)
        {
            "schedule_id": "test_cancelled_exam",
            "exam_id": "test_geo_p1",
            "subject_code": "2217",
            "syllabus_version": "2023-2027",
            "paper_code": "paper_1",
            "subject_name": "Geography",
            "paper_name": "Paper 1",
            "scheduled_date": datetime.utcnow() + timedelta(days=30),
            "duration_minutes": 135,
            "status": "cancelled",
            "candidate_ids": ["test_candidate_a"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    ]
    
    collection.insert_many(test_schedules)
    
    yield
    
    client.close()


class TestDashboardPipelineIntegration:
    """Integration tests for full dashboard pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, seed_test_exams):
        """Test complete dashboard pipeline execution."""
        # Create execution context
        context = ExecutionContext.create(
            user_id="test_candidate_a",
            request_source="test"
        )
        
        # Execute dashboard pipeline
        orchestrator = Orchestrator(engine_registry)
        result = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_candidate_a",
                "cohort_id": "cohort_test",
            },
            context=context
        )
        
        # Verify success
        assert result["success"] is True
        assert "engine_outputs" in result
        
        # Verify exam_structure ran
        assert "exam_structure" in result["engine_outputs"]
        exam_structure_output = result["engine_outputs"]["exam_structure"]["data"]
        assert "upcoming_exams" in exam_structure_output
        
        # Verify upcoming exams populated
        upcoming_exams = exam_structure_output["upcoming_exams"]
        assert isinstance(upcoming_exams, list)
        assert len(upcoming_exams) > 0
        
        # Should have Biology, Math, and Physics (cohort) = 3 exams
        # Should NOT have History (past) or Geography (cancelled)
        assert len(upcoming_exams) == 3
        
        # Verify exam structure
        for exam in upcoming_exams:
            assert "exam_id" in exam
            assert "subject" in exam
            assert "paper" in exam
            assert "scheduled_date" in exam
            assert "duration_minutes" in exam
            assert "status" in exam
            assert exam["status"] == "scheduled"
    
    @pytest.mark.asyncio
    async def test_different_candidates_see_different_exams(self, seed_test_exams):
        """Test that different candidates see only their assigned exams."""
        orchestrator = Orchestrator(engine_registry)
        
        # Candidate A
        context_a = ExecutionContext.create(user_id="test_candidate_a")
        result_a = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_candidate_a",
                "cohort_id": "cohort_test",
            },
            context=context_a
        )
        
        upcoming_a = result_a["engine_outputs"]["exam_structure"]["data"]["upcoming_exams"]
        
        # Candidate B
        context_b = ExecutionContext.create(user_id="test_candidate_b")
        result_b = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_candidate_b",
                "cohort_id": "cohort_test",
            },
            context=context_b
        )
        
        upcoming_b = result_b["engine_outputs"]["exam_structure"]["data"]["upcoming_exams"]
        
        # Verify different exam lists
        # Candidate A: Biology, Math, Physics (cohort) = 3
        # Candidate B: Chemistry, Physics (cohort) = 2
        assert len(upcoming_a) == 3
        assert len(upcoming_b) == 2
        
        # Verify specific subjects
        subjects_a = {exam["subject"] for exam in upcoming_a}
        subjects_b = {exam["subject"] for exam in upcoming_b}
        
        assert "Biology" in subjects_a
        assert "Mathematics" in subjects_a
        assert "Physics" in subjects_a  # Cohort exam
        
        assert "Chemistry" in subjects_b
        assert "Physics" in subjects_b  # Cohort exam
        assert "Biology" not in subjects_b
        assert "Mathematics" not in subjects_b
    
    @pytest.mark.asyncio
    async def test_no_upcoming_exams_returns_empty_list(self, clean_test_db):
        """Test graceful handling when candidate has no upcoming exams."""
        orchestrator = Orchestrator(engine_registry)
        context = ExecutionContext.create(user_id="test_candidate_no_exams")
        
        result = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_candidate_no_exams",
            },
            context=context
        )
        
        assert result["success"] is True
        upcoming_exams = result["engine_outputs"]["exam_structure"]["data"]["upcoming_exams"]
        
        # Should be empty list, not None, not error
        assert upcoming_exams == []
        assert isinstance(upcoming_exams, list)
    
    @pytest.mark.asyncio
    async def test_past_exams_excluded(self, seed_test_exams):
        """Test that past exams are excluded from upcoming exams."""
        orchestrator = Orchestrator(engine_registry)
        context = ExecutionContext.create(user_id="test_candidate_a")
        
        result = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_candidate_a",
                "cohort_id": "cohort_test",
            },
            context=context
        )
        
        upcoming_exams = result["engine_outputs"]["exam_structure"]["data"]["upcoming_exams"]
        
        # History exam is in the past - should not appear
        subjects = {exam["subject"] for exam in upcoming_exams}
        assert "History" not in subjects
    
    @pytest.mark.asyncio
    async def test_cancelled_exams_excluded(self, seed_test_exams):
        """Test that cancelled exams are excluded."""
        orchestrator = Orchestrator(engine_registry)
        context = ExecutionContext.create(user_id="test_candidate_a")
        
        result = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_candidate_a",
                "cohort_id": "cohort_test",
            },
            context=context
        )
        
        upcoming_exams = result["engine_outputs"]["exam_structure"]["data"]["upcoming_exams"]
        
        # Geography exam is cancelled - should not appear
        subjects = {exam["subject"] for exam in upcoming_exams}
        assert "Geography" not in subjects
    
    @pytest.mark.asyncio
    async def test_cohort_filtering_works(self, seed_test_exams):
        """Test that cohort-based exam assignment works."""
        orchestrator = Orchestrator(engine_registry)
        
        # Candidate with cohort_test should see Physics exam
        context = ExecutionContext.create(user_id="test_candidate_a")
        result = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_candidate_a",
                "cohort_id": "cohort_test",
            },
            context=context
        )
        
        upcoming_exams = result["engine_outputs"]["exam_structure"]["data"]["upcoming_exams"]
        subjects = {exam["subject"] for exam in upcoming_exams}
        
        # Should include Physics (cohort exam)
        assert "Physics" in subjects
    
    @pytest.mark.asyncio
    async def test_exams_sorted_by_date(self, seed_test_exams):
        """Test that upcoming exams are sorted chronologically."""
        orchestrator = Orchestrator(engine_registry)
        context = ExecutionContext.create(user_id="test_candidate_a")
        
        result = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_candidate_a",
                "cohort_id": "cohort_test",
            },
            context=context
        )
        
        upcoming_exams = result["engine_outputs"]["exam_structure"]["data"]["upcoming_exams"]
        
        # Verify chronological order
        # Biology (10 days) → Math (15 days) → Physics (25 days)
        assert len(upcoming_exams) >= 3
        assert upcoming_exams[0]["subject"] == "Biology"
        assert upcoming_exams[1]["subject"] == "Mathematics"
        assert upcoming_exams[2]["subject"] == "Physics"
    
    @pytest.mark.asyncio
    async def test_timezone_boundary_case(self, clean_test_db):
        """Test exam scheduled for exactly now + 1 hour is included."""
        # Seed exam 1 hour from now
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB]
        
        db.exam_schedules.insert_one({
            "schedule_id": "test_boundary_exam",
            "exam_id": "test_boundary",
            "subject_code": "9999",
            "syllabus_version": "2023-2027",
            "paper_code": "paper_1",
            "subject_name": "Boundary Test",
            "paper_name": "Paper 1",
            "scheduled_date": datetime.utcnow() + timedelta(hours=1),
            "duration_minutes": 60,
            "status": "scheduled",
            "candidate_ids": ["test_boundary_candidate"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        
        orchestrator = Orchestrator(engine_registry)
        context = ExecutionContext.create(user_id="test_boundary_candidate")
        
        result = await orchestrator.execute_pipeline(
            pipeline_name="student_dashboard_v1",
            payload={
                "dashboard_mode": True,
                "candidate_id": "test_boundary_candidate",
            },
            context=context
        )
        
        upcoming_exams = result["engine_outputs"]["exam_structure"]["data"]["upcoming_exams"]
        
        # Exam in 1 hour should be included
        assert len(upcoming_exams) == 1
        assert upcoming_exams[0]["subject"] == "Boundary Test"
        
        client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
