from fastapi import APIRouter
from app.api.v1.endpoints import health, weather, recommend, pages

router = APIRouter(prefix="/v1")

router.include_router(health.router, tags=["health"])
router.include_router(weather.router, tags=["weather"])
router.include_router(recommend.router, prefix="/recommendations", tags=["recommendations"])
router.include_router(pages.router, prefix="/pages", tags=["pages"])
