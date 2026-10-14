import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SATRA Tortoise Management API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database URL from Render environment or local SQLite fallback
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./satra_local.db")
    
    # Fix Render postgres:// prefix to postgresql:// for SQLAlchemy if needed
    @property
    def sqlalchemy_database_uri(self) -> str:
        uri = self.DATABASE_URL
        if uri and uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        return uri

    class Config:
        case_sensitive = True

settings = Settings()
