"""
Configuration validation tests for Azure settings

Tests production validation of Azure credentials and environment configuration.
"""

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


class TestAzureConfiguration:
    """Test Azure configuration validation."""
    
    def test_production_fails_without_azure_account_name(self, monkeypatch):
        """Test production startup fails if AZURE_STORAGE_ACCOUNT_NAME is missing."""
        # Setup production environment without Azure account name
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_NAME", "")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_KEY", "testkey")
        
        # Execute & Verify
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        assert any(
            "AZURE_STORAGE_ACCOUNT_NAME" in str(error) 
            for error in errors
        )
    
    def test_production_fails_without_azure_account_key(self, monkeypatch):
        """Test production startup fails if AZURE_STORAGE_ACCOUNT_KEY is missing."""
        # Setup production environment without Azure account key
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_NAME", "testaccount")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_KEY", "")
        
        # Execute & Verify
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        assert any(
            "AZURE_STORAGE_ACCOUNT_KEY" in str(error)
            for error in errors
        )
    
    def test_development_allows_empty_azure_credentials(self, monkeypatch):
        """Test development/local environments allow empty Azure credentials."""
        # Setup development environment
        monkeypatch.setenv("ENV", "development")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_NAME", "")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_KEY", "")
        
        # Execute - should not raise
        settings = Settings()
        
        # Verify
        assert settings.AZURE_STORAGE_ACCOUNT_NAME == ""
        assert settings.AZURE_STORAGE_ACCOUNT_KEY == ""
    
    def test_default_container_is_zimprep_exports(self, monkeypatch):
        """Test default Azure container is 'zimprep-exports'."""
        monkeypatch.setenv("ENV", "development")
        
        settings = Settings()
        
        assert settings.AZURE_EXPORT_CONTAINER == "zimprep-exports"
    
    def test_default_sas_expiry_is_900_seconds(self, monkeypatch):
        """Test default SAS expiry is 900 seconds (15 minutes)."""
        monkeypatch.setenv("ENV", "development")
        
        settings = Settings()
        
        assert settings.AZURE_EXPORT_SAS_EXPIRY_SECONDS == 900
    
    def test_custom_sas_expiry_respected(self, monkeypatch):
        """Test custom SAS expiry setting is respected."""
        monkeypatch.setenv("ENV", "development")
        monkeypatch.setenv("AZURE_EXPORT_SAS_EXPIRY_SECONDS", "1800")  # 30 minutes
        
        settings = Settings()
        
        assert settings.AZURE_EXPORT_SAS_EXPIRY_SECONDS == 1800
    
    def test_production_succeeds_with_all_azure_credentials(self, monkeypatch):
        """Test production startup succeeds with all Azure credentials."""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("JWT_SECRET", "a" * 32)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("BILLING_WEBHOOK_SECRET", "webhook_secret")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_NAME", "prodaccount")
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_KEY", "prodkey123")
        
        # Execute - should not raise
        settings = Settings()
        
        # Verify
        assert settings.AZURE_STORAGE_ACCOUNT_NAME == "prodaccount"
        assert settings.AZURE_STORAGE_ACCOUNT_KEY == "prodkey123"
