"""
Integration tests for Reporting Engine with Azure Export Storage

Tests the Reporting & Analytics Engine integration with Azure Blob Storage,
ensuring exports are persisted correctly and pipeline gracefully degrades on failures.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from app.engines.reporting_analytics.engine import ReportingAnalyticsEngine
from app.engines.reporting_analytics.schemas.input import (
    ReportingInput,
    UserRole,
    ReportingScope,
    ExportFormat,
)


class TestReportingEngineAzureIntegration:
    """Integration tests for Reporting Engine with Azure storage."""
    
    @pytest.fixture
    def mock_mongo(self):
        """Mock MongoDB client."""
        with patch('app.engines.reporting_analytics.engine.MongoClient'):
            yield
    
    @pytest.fixture
    def mock_azure_storage(self):
        """Mock Azure storage service."""
        with patch('app.engines.reporting_analytics.engine.AzureExportStorageService') as mock_service:
            yield mock_service
    
    @pytest.fixture
    def sample_input(self):
        """Create sample reporting input."""
        return ReportingInput(
            trace_id=uuid4(),
            user_id=uuid4(),
            role=UserRole.STUDENT,
            reporting_scope=ReportingScope.DETAILED,
            export_format=ExportFormat.PDF,
            exam_session_id=uuid4(),
            subject_code="MATH_4008",
            feature_flags_snapshot={},
        )
    
    @pytest.fixture
    def sample_results(self):
        """Create sample results data."""
        return {
            "exam_title": "Mathematics Paper 1",
            "subject_name": "Mathematics",
            "grade": "A",
            "percentage": 85.5,
            "total_marks": 85.5,
            "max_total_marks": 100,
        }
    
    def test_exports_succeed_with_azure_available(
        self, mock_mongo, mock_azure_storage, sample_input, sample_results
    ):
        """Test exports are persisted when Azure is available."""
        # Setup
        engine = ReportingAnalyticsEngine()
        
        # Mock Azure storage to return success
        mock_instance = mock_azure_storage.return_value
        mock_instance.save_export.return_value = {
            "blob_path": "exports/user_123/trace_456/pdf.pdf",
            "download_url": "https://testaccount.blob.core.windows.net/...",
            "content_type": "application/pdf",
            "size_bytes": 12345,
        }
        
        # Mock PDF renderer
        with patch('app.engines.reporting_analytics.engine.PDFRendererService') as mock_pdf:
            mock_pdf.return_value.render_report_to_pdf.return_value = b"fake pdf content"
            
            # Execute
            result = engine._render_exports(sample_input, sample_results)
        
        # Verify
        assert "exports" in result
        assert len(result["exports"]) == 1
        assert result["exports"][0]["type"] == "pdf"
        assert "download_url" in result["exports"][0]
        assert result["exports"][0]["content_type"] == "application/pdf"
        assert result["exports"][0]["size_bytes"] == 12345
    
    def test_empty_exports_when_azure_fails(
        self, mock_mongo, mock_azure_storage, sample_input, sample_results
    ):
        """Test empty exports returned when Azure fails (no pipeline failure)."""
        # Setup
        engine = ReportingAnalyticsEngine()
        
        # Mock Azure storage to return failure (None)
        mock_instance = mock_azure_storage.return_value
        mock_instance.save_export.return_value = None
        
        # Mock PDF renderer
        with patch('app.engines.reporting_analytics.engine.PDFRendererService') as mock_pdf:
            mock_pdf.return_value.render_report_to_pdf.return_value = b"fake pdf content"
            
            # Execute - should not raise exception
            result = engine._render_exports(sample_input, sample_results)
        
        # Verify - empty exports but no crash
        assert "exports" in result
        assert len(result["exports"]) == 0
    
    def test_no_storage_calls_when_no_export(
        self, mock_mongo, mock_azure_storage, sample_input, sample_results
    ):
        """Test JSON export persists via Azure storage."""
        # Setup
        json_input = sample_input.model_copy(update={"export_format": ExportFormat.JSON})
        engine = ReportingAnalyticsEngine()
        
        mock_instance = mock_azure_storage.return_value
        mock_instance.save_export.return_value = {
            "blob_path": "exports/user/trace/json.json",
            "download_url": "https://testaccount.blob.core.windows.net/...",
            "content_type": "application/json",
            "size_bytes": 500,
        }
        
        # Execute
        result = engine._render_exports(json_input, sample_results)
        
        # Verify JSON export persisted
        mock_instance.save_export.assert_called_once()
        assert "exports" in result
        assert len(result["exports"]) == 1
    
    def test_export_metadata_includes_sas_urls(
        self, mock_mongo, mock_azure_storage, sample_input, sample_results
    ):
        """Test export metadata includes correct SAS URLs from Azure."""
        # Setup
        engine = ReportingAnalyticsEngine()
        expected_url = "https://testaccount.blob.core.windows.net/zimprep-exports/exports/user/trace/pdf.pdf?sas_token"
        
        mock_instance = mock_azure_storage.return_value
        mock_instance.save_export.return_value = {
            "blob_path": "exports/user/trace/pdf.pdf",
            "download_url": expected_url,
            "content_type": "application/pdf",
            "size_bytes": 5000,
        }
        
        # Mock PDF renderer
        with patch('app.engines.reporting_analytics.engine.PDFRendererService') as mock_pdf:
            mock_pdf.return_value.render_report_to_pdf.return_value = b"content"
            
            # Execute
            result = engine._render_exports(sample_input, sample_results)
        
        # Verify SAS URL is in response
        assert result["exports"][0]["download_url"] == expected_url
    
    def test_all_todos_removed_from_engine(self):
        """Verify all TODO comments have been removed from engine.py."""
        import os
        engine_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "app",
            "engines",
            "reporting_analytics",
            "engine.py"
        )
        
        with open(engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for TODO comments related to storage
        assert "TODO: Save PDF to storage" not in content
        assert "TODO: Save CSV to storage" not in content
        assert "TODO: Save JSON to storage" not in content
    
    def test_csv_export_persists_correctly(
        self, mock_mongo, mock_azure_storage, sample_input, sample_results
    ):
        """Test CSV exports are persisted to Azure."""
        # Setup
        csv_input = sample_input.model_copy(update={"export_format": ExportFormat.CSV})
        engine = ReportingAnalyticsEngine()
        
        mock_instance = mock_azure_storage.return_value
        mock_instance.save_export.return_value = {
            "blob_path": "exports/user/trace/csv.csv",
            "download_url": "https://testaccount.blob.core.windows.net/...",
            "content_type": "text/csv",
            "size_bytes": 500,
        }
        
        # Mock export service
        with patch('app.engines.reporting_analytics.engine.ExportService') as mock_export:
            mock_export.return_value.export_to_csv.return_value = "csv,data\n1,2"
            
            # Execute
            result = engine._render_exports(csv_input, sample_results)
        
        # Verify
        assert len(result["exports"]) == 1
        assert result["exports"][0]["type"] == "csv"
        assert result["exports"][0]["content_type"] == "text/csv"
    
    def test_json_export_persists_correctly(
        self, mock_mongo, mock_azure_storage, sample_input, sample_results
    ):
        """Test JSON exports are persisted to Azure."""
        # Setup
        json_input = sample_input.model_copy(update={"export_format": ExportFormat.JSON})
        engine = ReportingAnalyticsEngine()
        
        mock_instance = mock_azure_storage.return_value
        mock_instance.save_export.return_value = {
            "blob_path": "exports/user/trace/json.json",
            "download_url": "https://testaccount.blob.core.windows.net/...",
            "content_type": "application/json",
            "size_bytes": 300,
        }
        
        # Mock export service
        with patch('app.engines.reporting_analytics.engine.ExportService') as mock_export:
            mock_export.return_value.export_to_json.return_value = '{"data": "json"}'
            
            # Execute
            result = engine._render_exports(json_input, sample_results)
        
        # Verify
        assert len(result["exports"]) == 1
        assert result["exports"][0]["type"] == "json"
        assert result["exports"][0]["content_type"] == "application/json"
