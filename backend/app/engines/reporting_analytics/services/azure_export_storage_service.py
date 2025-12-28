"""
Azure Blob Storage Service for Export Persistence

This service handles the durable, immutable persistence of ZimPrep exports
(PDF/CSV/JSON) to Azure Blob Storage.

CRITICAL CONSTRAINTS:
- Exports are legal artifacts and must be immutable
- All exports are traceable via trace_id
- SAS tokens are read-only and time-limited
- Storage failures must not crash the pipeline
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.core.exceptions import AzureError

from app.config.settings import settings

logger = logging.getLogger(__name__)


class AzureExportStorageService:
    """
    Service for persisting exports to Azure Blob Storage.
    
    Responsibilities:
    - Upload export content (PDF/CSV/JSON) to Azure Blob Storage
    - Generate time-limited SAS URLs for download
    - Track export metadata for audit trails
    - Fail gracefully on Azure errors
    
    CRITICAL: This service must NEVER expose Azure credentials to clients.
    Only SAS URLs are returned.
    """
    
    def __init__(self):
        """Initialize the Azure Blob Storage service."""
        self.account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self.account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
        self.container_name = settings.AZURE_EXPORT_CONTAINER
        self.sas_expiry_seconds = settings.AZURE_EXPORT_SAS_EXPIRY_SECONDS
        
        # Initialize blob service client (lazy - only if credentials exist)
        self._blob_service_client = None
        
        if self.account_name and self.account_key:
            try:
                connection_string = (
                    f"DefaultEndpointsProtocol=https;"
                    f"AccountName={self.account_name};"
                    f"AccountKey={self.account_key};"
                    f"EndpointSuffix=core.windows.net"
                )
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    connection_string
                )
                logger.info(
                    "Azure Blob Storage initialized",
                    extra={
                        "account_name": self.account_name,
                        "container": self.container_name,
                    }
                )
            except Exception as e:
                logger.error(
                    "Failed to initialize Azure Blob Storage",
                    extra={"error": str(e)},
                    exc_info=True
                )
                self._blob_service_client = None
    
    def save_export(
        self,
        *,
        content: bytes,
        content_type: str,
        user_id: str,
        trace_id: str,
        export_type: str,  # "pdf" | "csv" | "json"
        filename: str,
    ) -> Dict[str, Any] | None:
        """
        Persist export to Azure Blob Storage and return metadata.
        
        Args:
            content: The export content as bytes
            content_type: MIME type (e.g., "application/pdf")
            user_id: User ID for path generation
            trace_id: Trace ID for audit linking
            export_type: Type of export ("pdf", "csv", "json")
            filename: Filename for content disposition header
            
        Returns:
            Metadata dictionary with download URL and size, or None on failure:
            {
                "blob_path": "exports/user_123/trace_456/dashboard.pdf",
                "download_url": "https://<account>.blob.core.windows.net/...",
                "content_type": "application/pdf",
                "size_bytes": 12345
            }
        """
        # Fail safely if Azure not configured
        if not self._blob_service_client:
            logger.warning(
                "Azure Blob Storage not configured - export not persisted",
                extra={"trace_id": trace_id, "export_type": export_type}
            )
            return None
        
        try:
            # Generate blob path following convention:
            # exports/{user_id}/{trace_id}/{export_type}.{ext}
            ext_map = {"pdf": "pdf", "csv": "csv", "json": "json"}
            ext = ext_map.get(export_type, export_type)
            blob_path = f"exports/{user_id}/{trace_id}/{export_type}.{ext}"
            
            # Get blob client
            blob_client = self._blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            # Upload with metadata
            blob_client.upload_blob(
                content,
                overwrite=False,  # Immutable - no overwrites allowed
                content_settings={
                    "content_type": content_type,
                    "content_disposition": f'attachment; filename="{filename}"',
                },
                metadata={
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "export_type": export_type,
                    "uploaded_at": datetime.utcnow().isoformat(),
                }
            )
            
            # Generate read-only SAS token
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                account_key=self.account_key,
                container_name=self.container_name,
                blob_name=blob_path,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=self.sas_expiry_seconds),
            )
            
            # Construct download URL
            download_url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_path}?{sas_token}"
            
            logger.info(
                "Export persisted to Azure Blob Storage",
                extra={
                    "trace_id": trace_id,
                    "blob_path": blob_path,
                    "size_bytes": len(content),
                }
            )
            
            return {
                "blob_path": blob_path,
                "download_url": download_url,
                "content_type": content_type,
                "size_bytes": len(content),
            }
            
        except AzureError as e:
            logger.error(
                "Azure Blob Storage upload failed",
                extra={
                    "trace_id": trace_id,
                    "export_type": export_type,
                    "error": str(e),
                },
                exc_info=True
            )
            return None
        
        except Exception as e:
            logger.error(
                "Unexpected error during export upload",
                extra={
                    "trace_id": trace_id,
                    "export_type": export_type,
                    "error": str(e),
                },
                exc_info=True
            )
            return None
