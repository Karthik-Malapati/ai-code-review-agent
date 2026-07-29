import os

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5-coder:7b",
)

MAX_REPOSITORY_FILES = int(os.getenv("MAX_REPOSITORY_FILES", "10"))

MAX_CONCURRENT_REVIEWS = int(os.getenv("MAX_CONCURRENT_REVIEWS", "3"))

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)
