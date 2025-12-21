from pydantic import BaseModel
from datetime import datetime


class EngineTrace(BaseModel):
    """Trace information for engine execution."""
    
    trace_id: str
    engine_name: str
    engine_version: str
    timestamp: datetime
    confidence: float
