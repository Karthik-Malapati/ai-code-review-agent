from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check() -> dict[str, str]:
    """Confirm that the API is running."""
    return {
        "status": "healthy",
        "service": "AI Code Review Agent",
    }
