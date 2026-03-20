from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "zimprep"
    openai_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Anthropic (Claude)
    anthropic_api_key: str = ""

    # Google Cloud Vision — JSON string of service account key OR file path
    google_application_credentials: str = ""

    # Flutterwave
    flutterwave_secret_key: str = ""
    billing_webhook_secret: str = ""  # must match the "verif-hash" in Flutterwave dashboard

    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000"

    # Auth / misc (accepted from .env but not used by the app directly)
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    env: str = "development"
    log_level: str = "INFO"
    paystack_secret_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
