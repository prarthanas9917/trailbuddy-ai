from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.ai import generate_suggestions

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="TrailBuddy AI",
    description="A local AI assistant for outdoor activities."
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class SuggestionRequest(BaseModel):
    location: str = Field(default="Nearby", min_length=1, max_length=100)
    interests: str = Field(default="Nature walks", min_length=1, max_length=200)
    duration: str = Field(default="1 hour", min_length=1, max_length=40)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.post("/api/suggest")
async def suggest(data: SuggestionRequest):
    return generate_suggestions(
        location=data.location,
        interests=data.interests,
        duration=data.duration
    )


@app.get("/health")
async def health():
    return {"status": "ok", "application": "TrailBuddy AI"}
