from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using Pydantic Settings."""
    
    # API Keys
    GEMINI_API_KEY: str
    
    # Database
    DATABASE_URL: str = "sqlite:///./papaya.db"
    
    # Cache
    WEATHER_CACHE_MINUTES: int = 30
    
    # Debug
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
