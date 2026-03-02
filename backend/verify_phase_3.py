"""Verification Script for Phase 3: Traceability & Async Safety."""
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase3_verification")

async def verify_phase_3():
    logger.info("Starting Phase 3 Verification...")
    
    # 1. Mock Dependencies
    mock_db = AsyncMock()
    mock_collection = AsyncMock()
    mock_db.background_jobs = mock_collection
    
    # Mock background tasks
    mock_bg_tasks = MagicMock()
    
    # Mock Orchestrator
    mock_orchestrator = AsyncMock()
    mock_orchestrator.execute_pipeline.return_value = {
        "success": True,
        "total_duration_ms": 100
    }
    
    # Import relevant modules (mocking settings/imports where needed)
    with patch("motor.motor_asyncio.AsyncIOMotorClient") as MockClient, \
         patch("app.orchestrator.orchestrator.orchestrator", mock_orchestrator):
        
        MockClient.return_value.get_database.return_value = mock_db
        
        from app.core.background import BackgroundJobManager, JobStatus
        from app.orchestrator.execution_context import ExecutionContext
        
        # Instantiate Manager
        manager = BackgroundJobManager()
        manager.initialize()
        
        # Test Data
        context = ExecutionContext(
            trace_id="test-trace-123",
            request_id="test-req-123",
            request_timestamp=datetime.utcnow(),
            request_source="verification_script"
        )
        payload = {"data": "test"}
        pipeline_name = "test_pipeline"
        
        # TEST 1: Enqueue Job
        logger.info("[TEST 1] Enqueue Job...")
        job_id = await manager.enqueue_job(mock_bg_tasks, pipeline_name, payload, context)
        
        # Verify job ID format
        assert job_id.startswith("job_"), "Job ID should start with job_"
        logger.info(f"✓ Job Enqueued: {job_id}")
        
        # Verify DB Insert
        mock_collection.insert_one.assert_called_once()
        inserted_doc = mock_collection.insert_one.call_args[0][0]
        assert inserted_doc["trace_id"] == "test-trace-123", "Trace ID must be preserved in DB"
        assert inserted_doc["status"] == JobStatus.PENDING, "Initial status must be PENDING"
        logger.info("✓ DB Insert Verified (Trace ID preserved)")
        
        # Verify Background Task Added
        mock_bg_tasks.add_task.assert_called_once()
        task_func = mock_bg_tasks.add_task.call_args[0][0]
        logger.info("✓ Background Task Added")
        
        # TEST 2: Run Job Wrapper (Simulate Background Execution)
        logger.info("[TEST 2] Simulate Background Execution...")
        await manager._run_job_wrapper(job_id, pipeline_name, payload, context)
        
        # Verify Orchestrator Call
        mock_orchestrator.execute_pipeline.assert_awaited_once_with(
            pipeline_name=pipeline_name,
            payload=payload,
            context=context
        )
        logger.info("✓ Orchestrator Executed with Correct Context")
        
        # Verify Status Updates
        # Should update to RUNNING then COMPLETED (2 updates total)
        assert mock_collection.update_one.call_count == 2
        
        # Check Final Update
        final_update_args = mock_collection.update_one.call_args_list[-1]
        final_query = final_update_args[0][0]
        final_update = final_update_args[0][1]
        
        assert final_query["job_id"] == job_id
        assert final_update["$set"]["status"] == JobStatus.COMPLETED
        logger.info("✓ Job Status Updated to COMPLETED")

        # TEST 3: Failure Handling
        logger.info("[TEST 3] Failure Handling...")
        mock_orchestrator.execute_pipeline.side_effect = Exception("Simulated Crash")
        
        job_id_fail = "job_fail_test"
        await manager._run_job_wrapper(job_id_fail, pipeline_name, payload, context)
        
        # Check Final Update for Failure
        fail_update_args = mock_collection.update_one.call_args_list[-1]
        fail_update = fail_update_args[0][1]
        
        assert fail_update["$set"]["status"] == JobStatus.FAILED
        assert "Simulated Crash" in fail_update["$set"]["error"]
        logger.info("✓ Job Status Updated to FAILED on crash")
        
    logger.info("PHASE 3 VERIFICATION COMPLETE: ALL CHECKS PASSED")

if __name__ == "__main__":
    asyncio.run(verify_phase_3())
