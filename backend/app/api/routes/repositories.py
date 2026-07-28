import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, HTTPException

from app.schemas.repository import (
    RepositoryCloneResponse,
    RepositoryFileInfo,
    RepositoryFileReview,
    RepositoryReviewRequest,
    RepositoryReviewResponse,
    RepositoryScanResponse,
)
from app.services.ai_reviewer import MODEL_NAME, review_code
from app.services.repository_scanner import (
    RepositoryCloneError,
    clone_repository,
    get_repository_name,
    scan_repository,
)

router = APIRouter(
    prefix="/api/repositories",
    tags=["Repository Review"],
)


MAX_REPOSITORY_FILES = 10
MAX_CONCURRENT_REVIEWS = 3

repository_review_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REVIEWS)


@router.post(
    "/clone",
    response_model=RepositoryCloneResponse,
)
async def clone_github_repository(
    request: RepositoryReviewRequest,
) -> RepositoryCloneResponse:
    """
    Validate and temporarily clone a public GitHub repository.
    """

    repository_url = str(request.repository_url)

    try:
        with TemporaryDirectory(prefix="ai-code-review-") as temporary_directory:
            temporary_path = Path(temporary_directory)

            clone_repository(
                repository_url=repository_url,
                destination=temporary_path,
            )

            repository_name = get_repository_name(repository_url)

            return RepositoryCloneResponse(
                repository_url=repository_url,
                repository_name=repository_name,
                message="Repository cloned successfully.",
            )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RepositoryCloneError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.post(
    "/scan",
    response_model=RepositoryScanResponse,
)
async def scan_github_repository(
    request: RepositoryReviewRequest,
) -> RepositoryScanResponse:
    """
    Clone a repository and discover supported source files.
    """

    repository_url = str(request.repository_url)

    try:
        with TemporaryDirectory(prefix="ai-code-review-") as temporary_directory:
            temporary_path = Path(temporary_directory)

            repository_path = clone_repository(
                repository_url=repository_url,
                destination=temporary_path,
            )

            source_files = scan_repository(
                repository_path=repository_path,
            )

            files = [
                RepositoryFileInfo(
                    path=str(file_path.relative_to(repository_path)),
                    language=language,
                )
                for file_path, language in source_files
            ]

            return RepositoryScanResponse(
                repository_url=repository_url,
                repository_name=get_repository_name(repository_url),
                total_source_files=len(files),
                files=files,
            )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RepositoryCloneError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


async def review_repository_file(
    file_path: Path,
    repository_path: Path,
    language: str,
) -> RepositoryFileReview:
    """
    Read and review one repository source file.
    """

    try:
        code = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{file_path.name} is not valid UTF-8 text.") from error

    if not code.strip():
        return RepositoryFileReview(
            path=str(file_path.relative_to(repository_path)),
            language=language,
            summary="File is empty. No review required.",
            issues=[],
        )

    async with repository_review_semaphore:
        result = await review_code(
            code=code,
            language=language,
        )

    return RepositoryFileReview(
        path=str(file_path.relative_to(repository_path)),
        language=language,
        summary=result.summary,
        issues=result.issues,
    )


@router.post(
    "/review",
    response_model=RepositoryReviewResponse,
)
async def review_github_repository(
    request: RepositoryReviewRequest,
) -> RepositoryReviewResponse:
    """
    Clone, scan, and AI-review a GitHub repository.
    """

    repository_url = str(request.repository_url)

    try:
        with TemporaryDirectory(prefix="ai-code-review-") as temporary_directory:
            temporary_path = Path(temporary_directory)

            repository_path = clone_repository(
                repository_url=repository_url,
                destination=temporary_path,
            )

            source_files = scan_repository(
                repository_path=repository_path,
            )

            total_files_scanned = len(source_files)

            files_to_review = source_files[:MAX_REPOSITORY_FILES]

            tasks = [
                review_repository_file(
                    file_path=file_path,
                    repository_path=repository_path,
                    language=language,
                )
                for file_path, language in files_to_review
            ]

            reviewed_files = await asyncio.gather(*tasks)

            total_issues = sum(
                len(file_review.issues) for file_review in reviewed_files
            )

            return RepositoryReviewResponse(
                repository_url=repository_url,
                repository_name=get_repository_name(repository_url),
                model=MODEL_NAME,
                total_files_scanned=total_files_scanned,
                total_files_reviewed=len(reviewed_files),
                total_issues=total_issues,
                files=reviewed_files,
            )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RepositoryCloneError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=(f"The repository AI review failed: {error}"),
        ) from error
