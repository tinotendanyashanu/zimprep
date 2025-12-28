"""
Unit tests for Azure Export Storage Service

Tests the Azure Blob Storage integration for export persistence,
including blob path generation, SAS URL creation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from app.engines.reporting_analytics.services.azure_export_storage_service import (
    AzureExportStorageService,
)


class TestAzureExportStorageService:
    """Test suite for Azure Export Storage Service."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with Azure credentials."""
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.settings') as mock_settings:
            mock_settings.AZURE_STORAGE_ACCOUNT_NAME = "testaccount"
            mock_settings.AZURE_STORAGE_ACCOUNT_KEY = "dGVzdGtleQ=="  # base64 "testkey"
            mock_settings.AZURE_EXPORT_CONTAINER = "zimprep-exports"
            mock_settings.AZURE_EXPORT_SAS_EXPIRY_SECONDS = 900
            yield mock_settings
    
    @pytest.fixture
    def mock_blob_service(self):
        """Mock Azure BlobServiceClient."""
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.BlobServiceClient') as mock_service:
            yield mock_service
    
    def test_blob_path_generation_follows_convention(self, mock_settings, mock_blob_service):
        """Test blob path follows exports/{user_id}/{trace_id}/{export_type}.{ext}"""
        # Setup
        service = AzureExportStorageService()
        user_id = "student_123"
        trace_id = str(uuid4())
        
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client
        
        # Execute
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.generate_blob_sas') as mock_sas:
            mock_sas.return_value = "sas_token"
            result = service.save_export(
                content=b"test content",
                content_type="application/pdf",
                user_id=user_id,
                trace_id=trace_id,
                export_type="pdf",
                filename="test.pdf",
            )
        
        # Verify blob path
        expected_path = f"exports/{user_id}/{trace_id}/pdf.pdf"
        assert result is not None
        assert result["blob_path"] == expected_path
    
    def test_sas_url_has_read_only_permissions(self, mock_settings, mock_blob_service):
        """Test SAS token has read-only permissions."""
        # Setup
        service = AzureExportStorageService()
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client
        
        # Execute
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.generate_blob_sas') as mock_sas:
            mock_sas.return_value = "sas_token"
            service.save_export(
                content=b"test",
                content_type="application/pdf",
                user_id="user_1",
                trace_id=str(uuid4()),
                export_type="pdf",
                filename="test.pdf",
            )
            
            # Verify SAS permissions
            call_args = mock_sas.call_args
            permissions = call_args.kwargs['permission']
            assert permissions.read is True
            assert not hasattr(permissions, 'write') or permissions.write is False
    
    def test_sas_expiry_defaults_to_15_minutes(self, mock_settings, mock_blob_service):
        """Test SAS token expires in 15 minutes (900 seconds)."""
        # Setup
        service = AzureExportStorageService()
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client
        
        # Execute
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.generate_blob_sas') as mock_sas:
            mock_sas.return_value = "sas_token"
            before_time = datetime.utcnow()
            
            service.save_export(
                content=b"test",
                content_type="application/pdf",
                user_id="user_1",
                trace_id=str(uuid4()),
                export_type="pdf",
                filename="test.pdf",
            )
            
            after_time = datetime.utcnow()
            
            # Verify expiry is approximately 15 minutes from now
            call_args = mock_sas.call_args
            expiry = call_args.kwargs['expiry']
            
            expected_expiry_min = before_time + timedelta(seconds=900)
            expected_expiry_max = after_time + timedelta(seconds=900)
            
            assert expected_expiry_min <= expiry <= expected_expiry_max
    
    def test_content_headers_set_correctly(self, mock_settings, mock_blob_service):
        """Test content type and content disposition headers are set."""
        # Setup
        service = AzureExportStorageService()
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client
        
        # Execute
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.generate_blob_sas') as mock_sas:
            mock_sas.return_value = "sas_token"
            service.save_export(
                content=b"test content",
                content_type="application/pdf",
                user_id="user_1",
                trace_id=str(uuid4()),
                export_type="pdf",
                filename="report.pdf",
            )
            
            # Verify content settings in upload_blob call
            upload_call = mock_blob_client.upload_blob.call_args
            content_settings = upload_call.kwargs['content_settings']
            
            assert content_settings['content_type'] == "application/pdf"
            assert 'attachment' in content_settings['content_disposition']
            assert 'report.pdf' in content_settings['content_disposition']
    
    def test_azure_error_returns_none(self, mock_settings, mock_blob_service):
        """Test graceful failure when Azure SDK raises error."""
        from azure.core.exceptions import AzureError
        
        # Setup
        service = AzureExportStorageService()
        mock_blob_client = MagicMock()
        mock_blob_client.upload_blob.side_effect = AzureError("Upload failed")
        mock_blob_service.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client
        
        # Execute
        result = service.save_export(
            content=b"test",
            content_type="application/pdf",
            user_id="user_1",
            trace_id=str(uuid4()),
            export_type="pdf",
            filename="test.pdf",
        )
        
        # Verify returns None on error
        assert result is None
    
    def test_multiple_exports_same_trace_id(self, mock_settings, mock_blob_service):
        """Test multiple export types can be saved for same trace_id."""
        # Setup
        service = AzureExportStorageService()
        trace_id = str(uuid4())
        user_id = "student_123"
        
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client
        
        # Execute multiple exports
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.generate_blob_sas') as mock_sas:
            mock_sas.return_value = "sas_token"
            
            pdf_result = service.save_export(
                content=b"pdf content",
                content_type="application/pdf",
                user_id=user_id,
                trace_id=trace_id,
                export_type="pdf",
                filename="report.pdf",
            )
            
            csv_result = service.save_export(
                content=b"csv content",
                content_type="text/csv",
                user_id=user_id,
                trace_id=trace_id,
                export_type="csv",
                filename="report.csv",
            )
            
            json_result = service.save_export(
                content=b"json content",
                content_type="application/json",
                user_id=user_id,
                trace_id=trace_id,
                export_type="json",
                filename="report.json",
            )
        
        # Verify all exports succeeded and have correct paths
        assert pdf_result is not None
        assert csv_result is not None
        assert json_result is not None
        
        assert f"{trace_id}/pdf.pdf" in pdf_result["blob_path"]
        assert f"{trace_id}/csv.csv" in csv_result["blob_path"]
        assert f"{trace_id}/json.json" in json_result["blob_path"]
    
    def test_no_azure_credentials_returns_none(self):
        """Test service returns None when Azure not configured."""
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.settings') as mock_settings:
            mock_settings.AZURE_STORAGE_ACCOUNT_NAME = ""
            mock_settings.AZURE_STORAGE_ACCOUNT_KEY = ""
            mock_settings.AZURE_EXPORT_CONTAINER = "zimprep-exports"
            mock_settings.AZURE_EXPORT_SAS_EXPIRY_SECONDS = 900
            
            service = AzureExportStorageService()
            
            result = service.save_export(
                content=b"test",
                content_type="application/pdf",
                user_id="user_1",
                trace_id=str(uuid4()),
                export_type="pdf",
                filename="test.pdf",
            )
            
            assert result is None
    
    def test_metadata_includes_trace_info(self, mock_settings, mock_blob_service):
        """Test blob metadata includes trace_id and user_id."""
        # Setup
        service = AzureExportStorageService()
        user_id = "student_123"
        trace_id = str(uuid4())
        
        mock_blob_client = MagicMock()
        mock_blob_service.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client
        
        # Execute
        with patch('app.engines.reporting_analytics.services.azure_export_storage_service.generate_blob_sas') as mock_sas:
            mock_sas.return_value = "sas_token"
            service.save_export(
                content=b"test",
                content_type="application/pdf",
                user_id=user_id,
                trace_id=trace_id,
                export_type="pdf",
                filename="test.pdf",
            )
            
            # Verify metadata in upload call
            upload_call = mock_blob_client.upload_blob.call_args
            metadata = upload_call.kwargs['metadata']
            
            assert metadata['trace_id'] == trace_id
            assert metadata['user_id'] == user_id
            assert metadata['export_type'] == "pdf"
            assert 'uploaded_at' in metadata
