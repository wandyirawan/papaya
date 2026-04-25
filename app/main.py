from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os

from app.config import get_settings
from app.db.database import init_db
from app.api.router import router as api_router
from app.api.v1.endpoints.pages import router as pages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    
    app = FastAPI(
        title="Papaya AI",
        description="AI-powered farming assistant for sustainable agriculture",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/v1/docs" if settings.DEBUG else None,
        redoc_url="/api/v1/redoc" if settings.DEBUG else None,
    )
    
    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Include API router
    app.include_router(api_router, prefix="/api")
    
    # Include pages router for root paths
    app.include_router(pages_router)
    
    return app


app = create_app()


if __name__ == "__main__":
    from granian import Granian
    
    Granian(
        "app.main:app",
        interface="asgi",
        host="0.0.0.0",
        port=8000,
        workers=1,
        threads=1,
    ).serve()
