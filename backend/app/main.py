from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.uploads import router as uploads_router

app = FastAPI(
    title="AI Code Review Agent",
    description="A local AI-powered code review API using FastAPI and Ollama.",
    version="1.0.0",
)

app.include_router(health_router)
app.include_router(reviews_router)
app.include_router(uploads_router)