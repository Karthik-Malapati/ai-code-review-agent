import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.review import (
    FileReviewResult,
    MultiFileReviewResponse,
)
from app.services.ai_reviewer import MODEL_NAME, review_code


router = APIRouter(
    prefix="/api/multi-uploads",
    tags=["Multi-File Review"],
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
MAX_FILES = 10

# Limit the number of AI reviews running simultaneously.
MAX_CONCURRENT_REVIEWS = 3

review_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REVIEWS)


async def review_uploaded_file(
    file: UploadFile,
) -> FileReviewResult:
    """
    Validate and review one uploaded source-code file.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Every uploaded file must have a filename.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type for {file.filename}. "
                f"Allowed extensions: {allowed}"
            ),
        )

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                f"{file.filename} is too large. "
                "Maximum size is 1 MB per file."
            ),
        )

    try:
        code = file_content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=400,
            detail=f"{file.filename} must contain UTF-8 text.",
        ) from error

    if not code.strip():
        raise HTTPException(
            status_code=400,
            detail=f"{file.filename} is empty.",
        )

    language = ALLOWED_EXTENSIONS[extension]

    try:
        async with review_semaphore:
            result = await review_code(
                code=code,
                language=language,
            )

    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Invalid AI response while reviewing "
                f"{file.filename}: {error}"
            ),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=(
                f"The AI review service failed while reviewing "
                f"{file.filename}."
            ),
        ) from error

    return FileReviewResult(
        filename=file.filename,
        language=language,
        summary=result.summary,
        issues=result.issues,
    )


@router.post(
    "/review",
    response_model=MultiFileReviewResponse,
)
async def review_multiple_files(
    files: Annotated[list[UploadFile], File()],
) -> MultiFileReviewResponse:
    """
    Upload and review multiple source-code files concurrently.
    """

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one file must be uploaded.",
        )

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"A maximum of {MAX_FILES} files may be uploaded.",
        )

    review_tasks = [
        review_uploaded_file(file)
        for file in files
    ]

    reviewed_files = await asyncio.gather(*review_tasks)

    total_issues = sum(
        len(file_result.issues)
        for file_result in reviewed_files
    )

    return MultiFileReviewResponse(
        model=MODEL_NAME,
        total_files=len(reviewed_files),
        total_issues=total_issues,
        files=reviewed_files,
    )