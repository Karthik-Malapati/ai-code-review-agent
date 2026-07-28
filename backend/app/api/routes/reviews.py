from fastapi import APIRouter, HTTPException

from app.schemas.review import CodeReviewRequest, CodeReviewResponse
from app.services.ai_reviewer import MODEL_NAME, review_code

router = APIRouter(
    prefix="/api/reviews",
    tags=["Code Review"],
)


@router.post(
    "",
    response_model=CodeReviewResponse,
)
async def create_code_review(
    request: CodeReviewRequest,
) -> CodeReviewResponse:
    """
    Review code submitted directly in the request body.
    """

    try:
        result = await review_code(
            code=request.code,
            language=request.language,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="The AI review service is currently unavailable.",
        ) from error

    return CodeReviewResponse(
        language=request.language,
        model=MODEL_NAME,
        summary=result.summary,
        issues=result.issues,
    )
