from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    health,
    multi_uploads,
    repositories,
    reviews,
    uploads,
)
from app.core.config import FRONTEND_URL

app = FastAPI(
    title="AI Code Review Agent",
    description=(
        "An AI-powered code review service using FastAPI, Ollama, and Qwen2.5-Coder."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-code-review-agent-phi.vercel.app",
    ],
    allow_origin_regex=(
        r"https://ai-code-review-agent-[a-zA-Z0-9-]+"
        r"-karthik-6732\.vercel\.app"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(reviews.router)
app.include_router(uploads.router)
app.include_router(multi_uploads.router)
app.include_router(repositories.router)
