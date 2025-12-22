from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Authentication
    JWT_SECRET: str = "CHANGE-THIS-IN-PRODUCTION-USE-LONG-RANDOM-STRING"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # Identity & Subscription Engine
    IDENTITY_CACHE_TTL_SECONDS: int = 300  # 5 minutes
    RATE_LIMIT_WINDOW_SECONDS: int = 86400  # 24 hours

    class Config:
        env_file = ".env"


settings = Settings()
