from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


class CodeReviewRequest(BaseModel):
    language: str = Field(
        ...,
        min_length=1,
        description="Programming language of the submitted code.",
    )
    code: str = Field(
        ...,
        min_length=1,
        description="Source code that should be reviewed.",
    )


class ReviewIssue(BaseModel):
    severity: Severity
    category: str
    line: int | None = None
    title: str
    description: str
    recommendation: str


class CodeReviewResult(BaseModel):
    summary: str
    issues: list[ReviewIssue]


class CodeReviewResponse(BaseModel):
    language: str
    model: str
    summary: str
    issues: list[ReviewIssue]


class FileReviewResult(BaseModel):
    filename: str
    language: str
    summary: str
    issues: list[ReviewIssue]


class MultiFileReviewResponse(BaseModel):
    model: str
    total_files: int
    total_issues: int
    files: list[FileReviewResult]