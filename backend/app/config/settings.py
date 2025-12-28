"""Production-grade settings with environment validation and audit mode support.

PHASE B5: This module implements:
1. Complete environment variable definitions
2. Environment type validation (local, staging, production, audit)
3. Startup validation that aborts on missing required secrets
4. Audit mode flag for read-only compliance operations
5. Environment fingerprint logging (without exposing secrets)
"""

import sys
import logging
from typing import Literal
from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


# Valid environment types for deployment
EnvironmentType = Literal["local", "development", "staging", "production", "audit"]


class Settings(BaseSettings):
    """Application settings with mandatory validation.
    
    CRITICAL: Application will abort startup if required variables are missing.
    This ensures fail-safe deployment and prevents silent failures.
    """
    
    # ===== ENVIRONMENT CONFIGURATION =====
    ENV: EnvironmentType = "development"
    
    # PHASE B5: Audit mode flag
    # When True, all write operations are blocked (read-only mode)
    AUDIT_MODE: bool = False
    
    # ===== DATABASE CONFIGURATION (REQUIRED) =====
    # PostgreSQL connection string
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    
    # MongoDB connection string (REQUIRED in production)
    MONGODB_URI: str = "mongodb://zimprep:zimprep@localhost:27017/zimprep?authSource=admin"
    
    # Redis for caching and rate limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ===== AI CONFIGURATION (REQUIRED) =====
    # OpenAI API key for AI engines (embedding, retrieval, reasoning, recommendation)
    OPENAI_API_KEY: str = ""
    
    # ===== AUTHENTICATION (REQUIRED) =====
    # JWT secret for token signing (MUST be 32+ chars in production)
    JWT_SECRET: str = "CHANGE-THIS-IN-PRODUCTION-USE-LONG-RANDOM-STRING-MIN-32-CHARS"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # ===== AI ENGINE TIMEOUTS (PHASE 6) =====
    # Maximum time to wait for AI API responses before failing gracefully
    AI_TIMEOUT_SECONDS: int = 30
    
    # ===== AZURE BLOB STORAGE (EXPORT PERSISTENCE) =====
    # Azure Storage Account credentials for export persistence
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_EXPORT_CONTAINER: str = "zimprep-exports"
    AZURE_EXPORT_SAS_EXPIRY_SECONDS: int = 900  # 15 minutes
    
    # ===== BILLING INTEGRATION (REQUIRED) =====
    # Webhook secret for billing provider callbacks
    BILLING_WEBHOOK_SECRET: str = ""
    
    # ===== IDENTITY & SUBSCRIPTION ENGINE =====
    IDENTITY_CACHE_TTL_SECONDS: int = 300  # 5 minutes
    RATE_LIMIT_WINDOW_SECONDS: int = 86400  # 24 hours
    
    # ===== OBSERVABILITY =====
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"
    
    # ===== VALIDATORS =====
    
    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Ensure JWT secret is strong enough for production."""
        env = info.data.get("ENV", "development")
        if env in ["production", "staging"] and len(v) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters in production/staging"
            )
        if env in ["production", "staging"] and "CHANGE-THIS" in v:
            raise ValueError(
                "JWT_SECRET must be changed from default value in production/staging"
            )
        return v
    
    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str, info) -> str:
        """Ensure OpenAI API key is set in non-local environments."""
        env = info.data.get("ENV", "development")
        if env in ["production", "staging"] and not v:
            raise ValueError(
                "OPENAI_API_KEY is required in production/staging environments"
            )
        return v
    
    @field_validator("MONGODB_URI")
    @classmethod
    def validate_mongodb_uri(cls, v: str, info) -> str:
        """Ensure MongoDB URI is properly configured."""
        env = info.data.get("ENV", "development")
        if env in ["production", "staging"] and "localhost" in v:
            logger.warning(
                "MongoDB URI contains 'localhost' in production/staging - "
                "ensure this is intentional"
            )
        return v
    
    @field_validator("AZURE_STORAGE_ACCOUNT_NAME")
    @classmethod
    def validate_azure_account_name(cls, v: str, info) -> str:
        """Ensure Azure storage account name is set in production."""
        env = info.data.get("ENV", "development")
        if env == "production" and not v:
            raise ValueError(
                "AZURE_STORAGE_ACCOUNT_NAME is required in production for export persistence"
            )
        return v
    
    @field_validator("AZURE_STORAGE_ACCOUNT_KEY")
    @classmethod
    def validate_azure_account_key(cls, v: str, info) -> str:
        """Ensure Azure storage account key is set in production."""
        env = info.data.get("ENV", "development")
        if env == "production" and not v:
            raise ValueError(
                "AZURE_STORAGE_ACCOUNT_KEY is required in production for export persistence"
            )
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def validate_environment() -> Settings:
    """Validate environment configuration on startup.
    
    CRITICAL: This function MUST be called on application startup.
    It will abort the application if required environment variables are missing.
    
    Returns:
        Settings: Validated settings instance
        
    Raises:
        SystemExit: If validation fails
    """
    try:
        settings_instance = Settings()
        
        # Log environment fingerprint (without secrets)
        logger.info(
            "Environment validated successfully",
            extra={
                "environment": settings_instance.ENV,
                "audit_mode": settings_instance.AUDIT_MODE,
                "database_type": "postgresql" if "postgresql" in settings_instance.DATABASE_URL 
                               else "sqlite" if "sqlite" in settings_instance.DATABASE_URL
                               else "unknown",
                "mongodb_configured": bool(settings_instance.MONGODB_URI),
                "redis_configured": bool(settings_instance.REDIS_URL),
                "openai_configured": bool(settings_instance.OPENAI_API_KEY),
                "billing_configured": bool(settings_instance.BILLING_WEBHOOK_SECRET),
                "azure_storage_configured": bool(settings_instance.AZURE_STORAGE_ACCOUNT_NAME and settings_instance.AZURE_STORAGE_ACCOUNT_KEY),
            }
        )
        
        # Additional production checks
        if settings_instance.ENV == "production":
            if settings_instance.AUDIT_MODE:
                logger.warning("⚠️  AUDIT MODE ENABLED - All writes will be blocked")
            
            missing_secrets = []
            if not settings_instance.OPENAI_API_KEY:
                missing_secrets.append("OPENAI_API_KEY")
            if not settings_instance.BILLING_WEBHOOK_SECRET:
                missing_secrets.append("BILLING_WEBHOOK_SECRET")
            
            if missing_secrets:
                logger.error(
                    f"Production deployment missing required secrets: {missing_secrets}"
                )
                sys.exit(1)
        
        return settings_instance
        
    except ValidationError as e:
        logger.error(
            "❌ Environment validation failed - application cannot start",
            extra={"validation_errors": str(e)}
        )
        print("\n❌ STARTUP FAILED: Environment validation errors\n", file=sys.stderr)
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            print(f"  • {field}: {message}", file=sys.stderr)
        print("\nPlease fix the above errors and restart the application.\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during environment validation")
        print(f"\n❌ STARTUP FAILED: {e}\n", file=sys.stderr)
        sys.exit(1)


# Global settings instance (validated on import)
settings = validate_environment()
