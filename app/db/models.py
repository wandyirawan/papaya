from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Recommendation(SQLModel, table=True):
    """AI recommendation history."""
    __tablename__ = "recommendations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    crop_type: str = Field(index=True)
    location_city: str
    location_country: str
    current_conditions: str
    weather_data: str  # JSON string
    recommendation: str  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    llm_model: str = "gemini-3-flash-preview"


class WeatherCache(SQLModel, table=True):
    """Weather data cache."""
    __tablename__ = "weather_cache"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    city: str = Field(index=True)
    country: str = Field(index=True)
    data: str  # JSON string
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(index=True)
