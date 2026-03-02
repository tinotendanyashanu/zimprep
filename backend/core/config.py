from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017" # Should be overridden by .env
    mongo_db: str = "zimprep"
    openai_api_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
