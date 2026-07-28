from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.review import CodeReviewResponse
from app.services.ai_reviewer import MODEL_NAME, review_code

router = APIRouter(
    prefix="/api/uploads",
    tags=["File Upload Review"],
)


ALLOWED_EXTENSIONS = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
}


MAX_FILE_SIZE = 1_000_000


@router.post(
    "/review",
    response_model=CodeReviewResponse,
)
async def review_uploaded_file(
    file: Annotated[UploadFile, File()],
) -> CodeReviewResponse:
    """
    Upload a source-code file and receive a structured AI review.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file must have a filename.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed extensions: {allowed}",
        )

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The uploaded file is too large. Maximum size is 1 MB.",
        )

    try:
        code = file_content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file must contain UTF-8 text.",
        ) from error

    if not code.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    language = ALLOWED_EXTENSIONS[extension]

    try:
        result = await review_code(
            code=code,
            language=language,
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
        language=language,
        model=MODEL_NAME,
        summary=result.summary,
        issues=result.issues,
    )
