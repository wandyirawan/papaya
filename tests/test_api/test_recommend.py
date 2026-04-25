from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from app.db.database import get_session
from app.db.models import Recommendation
from datetime import datetime, timezone
import json


MOCK_WEATHER_DATA = {
    "daily": {
        "time": ["2026-04-24", "2026-04-25", "2026-04-26"],
        "temperature_2m_max": [32.0, 31.0, 33.0],
        "temperature_2m_min": [24.0, 23.0, 25.0],
        "precipitation_sum": [5.0, 0.0, 10.0],
        "precipitation_probability_max": [60.0, 20.0, 80.0],
        "relative_humidity_2m_mean": [75.0, 70.0, 80.0],
        "weathercode": [61, 0, 63],
    }
}

MOCK_LLM_RESPONSE = {
    "crop_type": "rice",
    "location": "Jakarta, Indonesia",
    "summary": "Good conditions for rice growth with adequate rainfall expected.",
    "fertilization": {
        "recommended_type": "NPK 16-16-16",
        "timing": "Apply 2 weeks after transplanting",
        "dosage": "200 kg per hectare",
        "notes": "Ensure soil is moist before application",
    },
    "irrigation": {
        "should_irrigate": False,
        "timing": "Not needed this week",
        "amount": "0 mm",
        "reason": "Adequate rainfall expected (15mm total)",
    },
    "pest_disease": {
        "risk_level": "medium",
        "potential_issues": ["Brown planthopper", "Leaf blast"],
        "preventive_measures": [
            "Monitor fields weekly",
            "Apply preventive fungicide if humidity exceeds 80%",
        ],
    },
    "general_care": {
        "daily_tasks": ["Check water level", "Inspect for pests"],
        "weekly_tasks": ["Apply foliar fertilizer", "Weed control"],
        "warnings": ["Watch for sudden temperature drops"],
    },
    "weather_context": "Warm and humid with intermittent rain",
    "confidence": 0.85,
}


@pytest.fixture
async def test_app_with_mocks():
    """Create a test app with mocked dependencies and isolated DB."""
    from app.core.llm import GeminiClient
    from app.core.weather import WeatherClient
    from app.api.v1.schemas.recommend import RecommendationResponse
    from app.api.router import router as api_router
    from sqlmodel import SQLModel
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async def override_get_session():
        async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session

    mock_weather_client = WeatherClient()
    mock_weather_client.get_forecast = AsyncMock(return_value=MOCK_WEATHER_DATA)

    mock_llm_response = RecommendationResponse(**MOCK_LLM_RESPONSE)
    mock_llm_client = GeminiClient(api_key="test-key")
    mock_llm_client.generate_structured = AsyncMock(return_value=mock_llm_response)

    test_app = FastAPI(
        title="Papaya AI Test",
        version="0.1.0",
    )

    test_app.include_router(api_router, prefix="/api")

    test_app.dependency_overrides[get_session] = override_get_session

    from app.api.v1.endpoints.recommend import get_llm_client, get_weather_client
    test_app.dependency_overrides[get_llm_client] = lambda: mock_llm_client
    test_app.dependency_overrides[get_weather_client] = lambda: mock_weather_client

    yield test_app, mock_llm_client, mock_weather_client


@pytest.fixture
async def client(test_app_with_mocks):
    test_app, mock_llm, mock_weather = test_app_with_mocks
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c, mock_llm, mock_weather


@pytest.mark.asyncio
async def test_create_recommendation_success(client):
    """Test successful recommendation creation."""
    client, mock_llm, mock_weather = client

    payload = {
        "crop_type": "rice",
        "location_city": "Jakarta",
        "location_country": "Indonesia",
        "current_conditions": "Soil is loamy with good drainage, plants are 3 weeks old and healthy",
    }

    response = await client.post("/api/v1/recommend", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["crop_type"] == "rice"
    assert data["location"] == "Jakarta, Indonesia"
    assert data["summary"] == MOCK_LLM_RESPONSE["summary"]
    assert data["fertilization"]["recommended_type"] == "NPK 16-16-16"
    assert data["irrigation"]["should_irrigate"] is False
    assert data["pest_disease"]["risk_level"] == "medium"
    assert data["confidence"] == 0.85

    mock_weather.get_forecast.assert_called_once_with(
        city="Jakarta", country="Indonesia", days=7
    )
    mock_llm.generate_structured.assert_called_once()


@pytest.mark.asyncio
async def test_create_recommendation_invalid_crop(client):
    """Test validation error for invalid crop type."""
    client, _, _ = client

    payload = {
        "crop_type": "potato",
        "location_city": "Jakarta",
        "location_country": "Indonesia",
        "current_conditions": "Soil is loamy with good drainage",
    }

    response = await client.post("/api/v1/recommend", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_recommendation_missing_fields(client):
    """Test validation error for missing required fields."""
    client, _, _ = client

    payload = {"crop_type": "rice"}

    response = await client.post("/api/v1/recommend", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_recommendation_short_conditions(client):
    """Test validation error for too short current_conditions."""
    client, _, _ = client

    payload = {
        "crop_type": "rice",
        "location_city": "Jakarta",
        "location_country": "Indonesia",
        "current_conditions": "ok",
    }

    response = await client.post("/api/v1/recommend", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_recommendations_empty(client):
    """Test listing recommendations when database is empty."""
    client, _, _ = client

    response = await client.get("/api/v1/recommendations")

    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_recommendation_not_found(client):
    """Test getting a non-existent recommendation."""
    client, _, _ = client

    response = await client.get("/api/v1/recommendations/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recommendation not found"
