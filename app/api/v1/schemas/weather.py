from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class WeatherDaily(BaseModel):
    """Daily weather forecast."""
    date_: str = Field(..., alias="date", description="Date of forecast")
    temp_max: float = Field(..., description="Maximum temperature (Celsius)")
    temp_min: float = Field(..., description="Minimum temperature (Celsius)")
    precipitation: float = Field(..., description="Expected precipitation (mm)")
    precipitation_probability: float = Field(..., description="Chance of rain (%)")
    humidity: Optional[float] = Field(None, description="Humidity (%)")
    weather_code: int = Field(..., description="WMO weather code")


class WeatherResponse(BaseModel):
    """Weather API response."""
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country name")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    daily_forecast: List[WeatherDaily] = Field(..., description="7-day forecast")
    cached: bool = Field(default=False, description="Whether data is from cache")


class CurrentWeather(BaseModel):
    """Current weather snapshot."""
    temperature: float = Field(..., description="Current temperature (Celsius)")
    humidity: float = Field(..., description="Current humidity (%)")
    precipitation: float = Field(..., description="Current precipitation (mm)")
    weather_description: str = Field(..., description="Weather description")
