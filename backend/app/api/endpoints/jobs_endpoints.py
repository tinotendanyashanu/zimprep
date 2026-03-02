"""API endpoints for background job management."""

from fastapi import APIRouter, HTTPException, Depends
from app.core.background import job_manager

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a background job.
    
    PHASE 3: Traceability & Async Safety
    Allows querying the status of long-running background tasks.
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return job
