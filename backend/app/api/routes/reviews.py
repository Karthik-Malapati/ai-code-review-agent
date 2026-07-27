from fastapi import APIRouter, HTTPException

from app.schemas.review import CodeReviewRequest, CodeReviewResponse
from app.services.ai_reviewer import MODEL_NAME, review_code

router = APIRouter(
    prefix="/api/reviews",
    tags=["Code Reviews"],
)


@router.post("", response_model=CodeReviewResponse)
async def create_code_review(request: CodeReviewRequest):
    try:
        review = await review_code(
            code=request.code,
            language=request.language,
        )

        return CodeReviewResponse(
            language=request.language,
            model=MODEL_NAME,
            review=review,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    