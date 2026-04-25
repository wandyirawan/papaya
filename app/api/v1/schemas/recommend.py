from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class FertilizationRecommendation(BaseModel):
    """Fertilization recommendation from AI."""
    recommended_type: str = Field(..., description="Type of fertilizer to use")
    timing: str = Field(..., description="When to apply the fertilizer")
    dosage: str = Field(..., description="How much fertilizer to apply")
    notes: str = Field(..., description="Additional notes and warnings")


class IrrigationRecommendation(BaseModel):
    """Irrigation recommendation from AI."""
    should_irrigate: bool = Field(..., description="Whether irrigation is needed")
    timing: str = Field(..., description="When to irrigate")
    amount: str = Field(..., description="How much water to apply")
    reason: str = Field(..., description="Explanation for the recommendation")


class PestDiseaseAlert(BaseModel):
    """Pest and disease risk assessment from AI."""
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Risk level")
    potential_issues: List[str] = Field(..., description="Potential pest/disease issues")
    preventive_measures: List[str] = Field(..., description="Prevention steps to take")


class GeneralCare(BaseModel):
    """General care recommendations from AI."""
    daily_tasks: List[str] = Field(..., description="Daily tasks to perform")
    weekly_tasks: List[str] = Field(..., description="Weekly tasks to perform")
    warnings: List[str] = Field(..., description="Warnings and cautions")


class RecommendationResponse(BaseModel):
    """Complete AI recommendation response."""
    id: Optional[int] = Field(default=None, description="Recommendation ID (set after saving)")
    crop_type: str = Field(..., description="Type of crop")
    location: str = Field(..., description="Location (city, country)")
    summary: str = Field(..., description="Executive summary of recommendations")
    fertilization: FertilizationRecommendation
    irrigation: IrrigationRecommendation
    pest_disease: PestDiseaseAlert
    general_care: GeneralCare
    weather_context: str = Field(..., description="Weather data considered")
    confidence: float = Field(..., ge=0, le=1, description="AI confidence score")


class RecommendationRequest(BaseModel):
    """Request for AI recommendation."""
    crop_type: Literal["rice", "corn", "soybean", "wheat", "tomato", "chili"] = Field(
        ..., description="Type of crop"
    )
    location_city: str = Field(..., min_length=2, description="City name")
    location_country: str = Field(..., min_length=2, description="Country name")
    current_conditions: str = Field(
        ..., 
        min_length=10, 
        description="Current field conditions (soil, plant health, etc.)"
    )


class RecommendationHistory(BaseModel):
    """History entry for recommendations."""
    id: int
    crop_type: str
    location: str
    created_at: str
    summary: str
