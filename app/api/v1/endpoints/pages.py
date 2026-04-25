from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import FileSystemLoader, Environment

router = APIRouter()

# Create Jinja2 environment without caching to avoid cache issues
env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=True,
    cache_size=0  # Disable caching
)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Homepage with recommendation form."""
    template = env.get_template("index.html")
    html = template.render(request=request)
    return HTMLResponse(content=html)


@router.get("/recommendations", response_class=HTMLResponse)
async def list_recommendations_ui(request: Request):
    """List all recommendations (UI view)."""
    template = env.get_template("recommendations.html")
    html = template.render(request=request)
    return HTMLResponse(content=html)
