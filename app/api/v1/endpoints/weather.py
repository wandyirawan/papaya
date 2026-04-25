from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api.v1.schemas.weather import WeatherResponse
from app.core.weather import get_weather_client, WeatherClient
from app.db.database import get_session

router = APIRouter()


@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    city: str,
    country: str,
    days: int = 7,
    skip_cache: bool = False,
    client: WeatherClient = Depends(get_weather_client)
):
    """
    Get weather forecast for a location.
    
    Args:
        city: City name (e.g., "Jakarta")
        country: Country name (e.g., "Indonesia")
        days: Number of forecast days (1-14, default 7)
        skip_cache: Force refresh from API
        
    Returns:
        Weather forecast with daily breakdown
    """
    if days < 1 or days > 14:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 14"
        )
    
    try:
        forecast_data = await client.get_forecast(
            city=city, 
            country=country, 
            days=days,
            skip_cache=skip_cache
        )
        
        # Parse daily data
        daily_list = []
        daily = forecast_data.get("daily", {})
        time_list = daily.get("time", [])
        
        for i, date_str in enumerate(time_list):
            daily_list.append({
                "date": date_str,
                "temp_max": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else 0,
                "temp_min": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else 0,
                "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
                "precipitation_probability": daily.get("precipitation_probability_max", [])[i] if i < len(daily.get("precipitation_probability_max", [])) else 0,
                "humidity": None,
                "weather_code": daily.get("weathercode", [])[i] if i < len(daily.get("weathercode", [])) else 0
            })
        
        return {
            "city": city,
            "country": country,
            "latitude": forecast_data.get("latitude", 0),
            "longitude": forecast_data.get("longitude", 0),
            "daily_forecast": daily_list,
            "cached": forecast_data.get("_cached", False)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Weather service error: {str(e)}"
        )
