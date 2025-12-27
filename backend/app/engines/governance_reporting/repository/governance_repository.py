"""Repository for Governance Reports.

PHASE FOUR: Immutable, append-only storage for governance reports.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.engines.governance_reporting.schemas.output import GovernanceReportingOutput
from app.engines.governance_reporting.schemas.input import ReportScope
from app.engines.governance_reporting.errors.exceptions import PersistenceError

logger = logging.getLogger(__name__)


class GovernanceReportingRepository:
    """Repository for persisting governance reports.
    
    CRITICAL RULES:
    - All reports are IMMUTABLE
    - Append-only operations
    - READ-ONLY access to source data
    - NO updates or deletes allowed
    """
    
    COLLECTION_NAME = "governance_reports"
    
    def __init__(self, mongo_client: MongoClient):
        """Initialize repository.
        
        Args:
            mongo_client: MongoDB client instance
        """
        self.db = mongo_client.get_database("zimprep")
        self.collection = self.db[self.COLLECTION_NAME]
    
    def save_report(
        self,
        output: GovernanceReportingOutput,
        trace_id: str
    ) -> str:
        """Save governance report (APPEND-ONLY).
        
        Args:
            output: Governance reporting output
            trace_id: Request trace ID
            
        Returns:
            MongoDB document ID
            
        Raises:
            PersistenceError: If save operation fails
        """
        document = {
            "report_id": output.report_id,
            "report_type": output.report_type.value,
            "scope": output.scope.value,
            "scope_id": output.scope_id,
            "time_period_start": output.time_period_start,
            "time_period_end": output.time_period_end,
            "generated_at": output.generated_at,
            "version": output.engine_version,
            "trace_id": trace_id,
            "_immutable": True
        }
        
        # Add report sections based on what's present
        if output.ai_usage_summary:
            document["ai_usage_summary"] = output.ai_usage_summary.model_dump()
        
        if output.validation_statistics:
            document["validation_statistics"] = output.validation_statistics.model_dump()
        
        if output.appeal_statistics:
            document["appeal_statistics"] = output.appeal_statistics.model_dump()
        
        if output.cost_transparency:
            document["cost_transparency"] = output.cost_transparency.model_dump()
        
        if output.fairness_indicators:
            document["fairness_indicators"] = output.fairness_indicators.model_dump()
        
        if output.system_health:
            document["system_health"] = output.system_health.model_dump()
        
        try:
            result = self.collection.insert_one(document)
            logger.info(
                f"[{trace_id}] Saved governance report: "
                f"report_id={output.report_id}, type={output.report_type.value}, "
                f"scope={output.scope.value}"
            )
            return str(result.inserted_id)
        
        except DuplicateKeyError as e:
            logger.error(
                f"[{trace_id}] Duplicate report_id: {output.report_id}"
            )
            raise PersistenceError(f"Report {output.report_id} already exists") from e
        
        except PyMongoError as e:
            logger.error(
                f"[{trace_id}] Failed to save governance report: {e}"
            )
            raise PersistenceError(f"Failed to save report: {e}") from e
    
    def load_cost_tracking_data(
        self,
        scope: ReportScope,
        scope_id: Optional[str],
        start_date: datetime,
        end_date: datetime,
        trace_id: str
    ) -> List[Dict[str, Any]]:
        """Load AI cost tracking data (READ-ONLY).
        
        Args:
            scope: Report scope
            scope_id: Optional scope identifier
            start_date: Period start
            end_date: Period end
            trace_id: Request trace ID
            
        Returns:
            List of cost tracking documents
        """
        try:
            cost_collection = self.db["ai_cost_tracking"]
            
            query: Dict[str, Any] = {
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
            
            if scope == ReportScope.SCHOOL and scope_id:
                query["school_id"] = scope_id
            
            records = list(cost_collection.find(query))
            
            logger.debug(
                f"[{trace_id}] Loaded {len(records)} cost tracking records"
            )
            
            return records
        
        except PyMongoError as e:
            logger.error(
                f"[{trace_id}] Failed to load cost tracking data: {e}"
            )
            return []
    
    def load_audit_records(
        self,
        scope: ReportScope,
        scope_id: Optional[str],
        start_date: datetime,
        end_date: datetime,
        trace_id: str
    ) -> List[Dict[str, Any]]:
        """Load audit trail records (READ-ONLY).
        
        Args:
            scope: Report scope
            scope_id: Optional scope identifier
            start_date: Period start
            end_date: Period end
            trace_id: Request trace ID
            
        Returns:
            List of audit trail documents
        """
        try:
            audit_collection = self.db["audit_trail"]
            
            query: Dict[str, Any] = {
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
            
            if scope == ReportScope.SCHOOL and scope_id:
                query["context.school_id"] = scope_id
            
            records = list(audit_collection.find(query))
            
            logger.debug(
                f"[{trace_id}] Loaded {len(records)} audit records"
            )
            
            return records
        
        except PyMongoError as e:
            logger.error(
                f"[{trace_id}] Failed to load audit records: {e}"
            )
            return []
    
    def load_exam_results(
        self,
        scope: ReportScope,
        scope_id: Optional[str],
        start_date: datetime,
        end_date: datetime,
        trace_id: str
    ) -> List[Dict[str, Any]]:
        """Load exam results (READ-ONLY).
        
        Args:
            scope: Report scope
            scope_id: Optional scope identifier
            start_date: Period start
            end_date: Period end
            trace_id: Request trace ID
            
        Returns:
            List of exam result documents
        """
        try:
            results_collection = self.db["exam_results"]
            
            query: Dict[str, Any] = {
                "issued_at": {"$gte": start_date, "$lte": end_date}
            }
            
            if scope == ReportScope.SCHOOL and scope_id:
                query["school_id"] = scope_id
            
            results = list(results_collection.find(query))
            
            logger.debug(
                f"[{trace_id}] Loaded {len(results)} exam results"
            )
            
            return results
        
        except PyMongoError as e:
            logger.error(
                f"[{trace_id}] Failed to load exam results: {e}"
            )
            return []
