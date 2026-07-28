from pydantic import BaseModel, Field, HttpUrl

from app.schemas.review import ReviewIssue


class RepositoryReviewRequest(BaseModel):
    repository_url: HttpUrl = Field(
        description="Public GitHub repository HTTPS URL",
        examples=[
            "https://github.com/Karthik-Malapati/ai-code-review-agent"
        ],
    )


class RepositoryCloneResponse(BaseModel):
    repository_url: str
    repository_name: str
    message: str


class RepositoryFileInfo(BaseModel):
    path: str
    language: str


class RepositoryScanResponse(BaseModel):
    repository_url: str
    repository_name: str
    total_source_files: int
    files: list[RepositoryFileInfo]


class RepositoryFileReview(BaseModel):
    path: str
    language: str
    summary: str
    issues: list[ReviewIssue]


class RepositoryReviewResponse(BaseModel):
    repository_url: str
    repository_name: str
    model: str
    total_files_scanned: int
    total_files_reviewed: int
    total_issues: int
    files: list[RepositoryFileReview]