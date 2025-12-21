from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from app.contracts.trace import EngineTrace


T = TypeVar("T")


class EngineResponse(BaseModel, Generic[T]):
    """Standardized response from any engine."""
    
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    trace: EngineTrace
