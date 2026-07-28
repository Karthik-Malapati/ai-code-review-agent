from fastapi import FastAPI

from app.api.routes import (
    health,
    multi_uploads,
    repositories,
    reviews,
    uploads,
)

app = FastAPI(
    title="AI Code Review Agent",
    description=(
        "An AI-powered code review service using FastAPI, Ollama, and Qwen2.5-Coder."
    ),
    version="1.0.0",
)


app.include_router(health.router)
app.include_router(reviews.router)
app.include_router(uploads.router)
app.include_router(multi_uploads.router)
app.include_router(repositories.router)
