from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
import json

from app.api.v1.schemas.recommend import (
    RecommendationRequest, 
    RecommendationResponse,
    RecommendationHistory
)
from app.core.llm import get_llm_client, GeminiClient
from app.core.weather import get_weather_client, WeatherClient
from app.core.prompts import get_prompt
from app.db.database import get_session
from app.db.models import Recommendation

router = APIRouter()


@router.post("/recommend", response_model=RecommendationResponse)
async def create_recommendation(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_session),
    llm_client: GeminiClient = Depends(get_llm_client),
    weather_client: WeatherClient = Depends(get_weather_client)
):
    """
    Get AI-powered farming recommendations.
    
    Args:
        request: Crop type, location, and current conditions
        
    Returns:
        Structured recommendations for fertilization, irrigation, 
        pest control, and general care
    """
    try:
        # 1. Fetch weather data
        weather_data = await weather_client.get_forecast(
            city=request.location_city,
            country=request.location_country,
            days=7,
            session=db
        )
        
        # Format weather for prompt
        weather_summary = format_weather_for_prompt(weather_data)
        
        # 2. Build prompt
        prompt = get_prompt(
            "recommendation",
            crop_type=request.crop_type,
            location_city=request.location_city,
            location_country=request.location_country,
            weather_data=weather_summary,
            current_conditions=request.current_conditions
        )
        
        # 3. Call Gemini AI
        response = await llm_client.generate_structured(
            prompt=prompt,
            response_schema=RecommendationResponse,
            temperature=0.3
        )
        
        # 4. Save to database
        recommendation_db = Recommendation(
            crop_type=request.crop_type,
            location_city=request.location_city,
            location_country=request.location_country,
            current_conditions=request.current_conditions,
            weather_data=json.dumps(weather_data),
            recommendation=json.dumps(response.model_dump()),
            llm_model="gemini-2.5-flash"
        )
        db.add(recommendation_db)
        await db.commit()
        await db.refresh(recommendation_db)
        
        # Add ID to response
        response_data = response.model_dump()
        response_data['id'] = recommendation_db.id
        
        return RecommendationResponse(**response_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation error: {str(e)}"
        )


def format_weather_for_prompt(weather_data: dict) -> str:
    """Format weather data for LLM prompt."""
    daily = weather_data.get("daily", {})
    time_list = daily.get("time", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    precipitation = daily.get("precipitation_sum", [])
    
    lines = []
    for i, date in enumerate(time_list[:7]):  # Next 7 days
        tmax = temp_max[i] if i < len(temp_max) else "N/A"
        tmin = temp_min[i] if i < len(temp_min) else "N/A"
        precip = precipitation[i] if i < len(precipitation) else 0
        lines.append(f"- {date}: {tmin}°C to {tmax}°C, {precip}mm rain")
    
    return "\n".join(lines)


@router.get("/recommendations", response_model=List[RecommendationHistory])
async def list_recommendations(
    limit: int = 10,
    db: AsyncSession = Depends(get_session)
):
    """List recent recommendations."""
    stmt = select(Recommendation).order_by(desc(Recommendation.created_at)).limit(limit)
    result = await db.execute(stmt)
    recommendations = result.scalars().all()
    
    return [
        RecommendationHistory(
            id=r.id,
            crop_type=r.crop_type,
            location=f"{r.location_city}, {r.location_country}",
            created_at=r.created_at.isoformat(),
            summary=json.loads(r.recommendation).get("summary", "")[:100] + "..."
        )
        for r in recommendations
    ]


@router.get("/recommendations/{recommendation_id}")
async def get_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Get a specific recommendation by ID."""
    stmt = select(Recommendation).where(Recommendation.id == recommendation_id)
    result = await db.execute(stmt)
    recommendation = result.scalar_one_or_none()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    return {
        "id": recommendation.id,
        "crop_type": recommendation.crop_type,
        "location": f"{recommendation.location_city}, {recommendation.location_country}",
        "current_conditions": recommendation.current_conditions,
        "recommendation": json.loads(recommendation.recommendation),
        "weather_data": json.loads(recommendation.weather_data),
        "created_at": recommendation.created_at.isoformat(),
        "llm_model": recommendation.llm_model
    }


@router.get("/recommendations/{recommendation_id}/pdf")
async def download_recommendation_pdf(
    recommendation_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Download recommendation as PDF."""
    from fastapi.responses import Response
    from app.core.pdf import generate_recommendation_pdf
    
    stmt = select(Recommendation).where(Recommendation.id == recommendation_id)
    result = await db.execute(stmt)
    recommendation = result.scalar_one_or_none()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    # Generate PDF
    rec_data = json.loads(recommendation.recommendation)
    weather_data = json.loads(recommendation.weather_data)
    
    pdf_bytes = generate_recommendation_pdf(
        recommendation=rec_data,
        weather=weather_data,
        crop_type=recommendation.crop_type,
        location=f"{recommendation.location_city}, {recommendation.location_country}",
        created_at=recommendation.created_at
    )
    
    filename = f"papaya_recommendation_{recommendation_id}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
