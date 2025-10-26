from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Database
    # SQLite for development (no PostgreSQL installation needed!)
    # For production, use PostgreSQL: postgresql://user:pass@host:5432/dbname
    database_url: str = "sqlite:///./trial_edu.db"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Optional: AI API Keys (add when ready to implement agents)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    
    # File Upload
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
