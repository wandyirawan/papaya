import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.db.models import WeatherCache


class WeatherClient:
    """Async client for wttr.in weather API (free, unlimited, no API key)."""
    
    BASE_URL = "https://wttr.in"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def _get_coordinates(self, city: str, country: str) -> Optional[tuple[float, float]]:
        """Get latitude and longitude using Open-Meteo geocoding."""
        params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        try:
            response = await self.client.get("https://geocoding-api.open-meteo.com/v1/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                return (result["latitude"], result["longitude"])
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    async def _fetch_forecast(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """Fetch weather forecast from wttr.in."""
        # wttr.in returns JSON with ?format=j1
        url = f"{self.BASE_URL}/{lat},{lon}?format=j1&lang=en"
        
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Transform wttr.in response to our format
        weather_data = {
            "latitude": lat,
            "longitude": lon,
            "daily": {
                "time": [],
                "temperature_2m_max": [],
                "temperature_2m_min": [],
                "precipitation_sum": [],
                "precipitation_probability_max": [],
                "relative_humidity_2m_mean": [],
                "weathercode": []
            }
        }
        
        # wttr.in gives 3 days forecast in weather
        for day in data.get("weather", []):
            weather_data["daily"]["time"].append(day.get("date", ""))
            weather_data["daily"]["temperature_2m_max"].append(float(day.get("maxtempC", 0)))
            weather_data["daily"]["temperature_2m_min"].append(float(day.get("mintempC", 0)))
            weather_data["daily"]["precipitation_sum"].append(float(day.get("totalSnow_cm", 0)))
            weather_data["daily"]["precipitation_probability_max"].append(float(day.get("uvIndex", 0)))
            weather_data["daily"]["relative_humidity_2m_mean"].append(float(day.get("avgHumidity", 0)))
            weather_data["daily"]["weathercode"].append(int(day.get("weatherCode", 0)))
        
        return weather_data
    
    async def get_forecast(
        self, 
        city: str, 
        country: str, 
        days: int = 7,
        skip_cache: bool = False,
        session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Get weather forecast with caching.
        
        Args:
            city: City name
            country: Country name
            days: Number of forecast days (1-14)
            skip_cache: Force refresh from API
            session: Optional database session for caching
            
        Returns:
            Weather forecast data
        """
        from sqlalchemy import select
        from datetime import datetime, timedelta
        
        # Check cache first
        if not skip_cache and session:
            stmt = select(WeatherCache).where(
                WeatherCache.city == city.lower(),
                WeatherCache.country == country.lower(),
                WeatherCache.expires_at > datetime.now(tz=None)
            )
            result = await session.execute(stmt)
            cached = result.scalar_one_or_none()
            
            if cached:
                return json.loads(cached.data)
        
        # Fetch from API
        coords = await self._get_coordinates(city, country)
        if not coords:
            raise ValueError(f"Could not find coordinates for {city}, {country}")
        
        lat, lon = coords
        forecast_data = await self._fetch_forecast(lat, lon, days)
        
        # Cache result if session provided
        if session:
            # Delete old cache
            stmt = select(WeatherCache).where(
                WeatherCache.city == city.lower(),
                WeatherCache.country == country.lower()
            )
            result = await session.execute(stmt)
            old_cache = result.scalar_one_or_none()
            if old_cache:
                await session.delete(old_cache)
            
            # Create new cache
            cache = WeatherCache(
                city=city.lower(),
                country=country.lower(),
                data=json.dumps(forecast_data),
                expires_at=datetime.now(tz=None) + timedelta(minutes=30)
            )
            session.add(cache)
            await session.commit()
        
        return forecast_data
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global client instance
_weather_client: WeatherClient | None = None


async def get_weather_client() -> WeatherClient:
    """Get or create weather client."""
    global _weather_client
    if _weather_client is None:
        _weather_client = WeatherClient()
    return _weather_client
