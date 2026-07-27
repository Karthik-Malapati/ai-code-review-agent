from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.reviews import router as reviews_router

app = FastAPI(
    title="AI Code Review Agent",
    description="An AI-powered application that reviews source code.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(reviews_router)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "AI Code Review Agent API",
        "documentation": "/docs",
    }