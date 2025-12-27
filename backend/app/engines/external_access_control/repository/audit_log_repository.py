"""Repository for external API audit logging.

Handles immutable logging of external API requests to MongoDB.
"""

import logging
import secrets
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.engines.external_access_control.schemas import ExternalAPIAuditLog


logger = logging.getLogger(__name__)


class AuditLogRepository:
    """Repository for external API audit logs."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize repository.
        
        Args:
            db: MongoDB database instance
        """
        self.collection = db["external_api_audit_logs"]
    
    async def log_external_request(
        self,
        trace_id: str,
        partner_id: str,
        api_key_id: str,
        endpoint: str,
        response_status: str,
        request_metadata: dict,
        pipeline: Optional[str] = None
    ) -> str:
        """Log an external API request (immutable).
        
        Args:
            trace_id: Request trace ID
            partner_id: Partner identifier
            api_key_id: API key used
            endpoint: Endpoint accessed
            response_status: "success" | "denied" | "rate_limited"
            request_metadata: Request context (IP, user-agent, etc.)
            pipeline: Pipeline executed (if any)
            
        Returns:
            Audit log ID
        """
        # Generate unique audit ID
        audit_id = f"audit_{secrets.token_hex(16)}"
        
        # Create audit log
        log = ExternalAPIAuditLog(
            audit_id=audit_id,
            trace_id=trace_id,
            partner_id=partner_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            pipeline=pipeline,
            response_status=response_status,
            request_metadata=request_metadata,
            timestamp=datetime.utcnow(),
            immutable=True
        )
        
        # Insert into MongoDB (write-once)
        await self.collection.insert_one(log.dict())
        
        logger.info(
            f"Logged external request: {audit_id} | "
            f"partner={partner_id} | endpoint={endpoint} | status={response_status}"
        )
        
        return audit_id
    
    async def get_by_trace_id(self, trace_id: str) -> list[ExternalAPIAuditLog]:
        """Retrieve audit logs by trace ID.
        
        Args:
            trace_id: Request trace ID
            
        Returns:
            List of ExternalAPIAuditLog
        """
        cursor = self.collection.find({"trace_id": trace_id})
        docs = await cursor.to_list(length=1000)
        
        return [ExternalAPIAuditLog(**doc) for doc in docs]
    
    async def get_by_partner(
        self,
        partner_id: str,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[ExternalAPIAuditLog]:
        """Retrieve audit logs for a partner.
        
        Args:
            partner_id: Partner identifier
            limit: Maximum number of logs to return
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of ExternalAPIAuditLog
        """
        query = {"partner_id": partner_id}
        
        # Add date range filter if provided
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        return [ExternalAPIAuditLog(**doc) for doc in docs]
    
    async def get_by_endpoint(
        self,
        endpoint: str,
        limit: int = 100
    ) -> list[ExternalAPIAuditLog]:
        """Retrieve audit logs for a specific endpoint.
        
        Args:
            endpoint: Endpoint path
            limit: Maximum number of logs to return
            
        Returns:
            List of ExternalAPIAuditLog
        """
        cursor = self.collection.find({"endpoint": endpoint}).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        return [ExternalAPIAuditLog(**doc) for doc in docs]
    
    async def count_requests(
        self,
        partner_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        response_status: Optional[str] = None
    ) -> int:
        """Count external requests matching filters.
        
        Args:
            partner_id: Optional partner filter
            start_date: Optional start date
            end_date: Optional end date
            response_status: Optional status filter
            
        Returns:
            Count of matching logs
        """
        query = {}
        
        if partner_id:
            query["partner_id"] = partner_id
        
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        if response_status:
            query["response_status"] = response_status
        
        count = await self.collection.count_documents(query)
        return count
