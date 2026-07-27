from pydantic import BaseModel, Field


class CodeReviewRequest(BaseModel):
    language: str = Field(
        min_length=1,
        max_length=50,
        examples=["python"],
    )
    code: str = Field(
        min_length=1,
        max_length=50000,
        examples=[
            "def divide(a, b):\n    return a / b"
        ],
    )


class CodeReviewResponse(BaseModel):
    language: str
    model: str
    review: str
    