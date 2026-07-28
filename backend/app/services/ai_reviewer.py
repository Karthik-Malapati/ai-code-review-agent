import json
from json import JSONDecodeError

from ollama import AsyncClient
from pydantic import ValidationError

from app.schemas.repository import RepositorySummary
from app.schemas.review import CodeReviewResult

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen2.5-coder:7b"

client = AsyncClient(host=OLLAMA_HOST)


SYSTEM_PROMPT = """
You are an experienced software engineer performing a professional code review.

Review the submitted code for:

1. Correctness and bugs
2. Security vulnerabilities
3. Error handling
4. Performance
5. Maintainability
6. Readability
7. Missing tests

Return only valid JSON.

Do not include Markdown.
Do not include code fences.
Do not include explanations outside the JSON.

Use exactly this structure:

{
  "summary": "A short summary of the overall review.",
  "issues": [
    {
      "severity": "CRITICAL",
      "category": "Security",
      "line": 10,
      "title": "Short issue title",
      "description": "Clear explanation of the issue.",
      "recommendation": "Specific recommendation for fixing it."
    }
  ]
}

Allowed severity values:

CRITICAL
HIGH
MEDIUM
LOW
INFO

Use null for the line number when the exact line cannot be identified.

If no issues are found, return:

{
  "summary": "No significant issues were found.",
  "issues": []
}
""".strip()


def extract_json_content(content: str) -> str:
    """
    Remove accidental Markdown code fences from the model response.
    """

    cleaned = content.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json") :]

    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```") :]

    cleaned = cleaned.removesuffix("```")

    return cleaned.strip()


async def review_code(
    code: str,
    language: str,
) -> CodeReviewResult:
    """
    Send source code to Ollama and return a validated structured review.
    """

    user_prompt = f"""
Programming language: {language}

Review the following source code:

{code}
""".strip()

    response = await client.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        options={
            "temperature": 0.1,
        },
    )

    raw_content = response["message"]["content"]
    json_content = extract_json_content(raw_content)

    try:
        parsed_content = json.loads(json_content)
    except JSONDecodeError as error:
        raise ValueError(
            f"The AI model returned invalid JSON: {json_content}"
        ) from error

    try:
        return CodeReviewResult.model_validate(parsed_content)
    except ValidationError as error:
        raise ValueError(
            f"The AI response did not match the required structure: {json_content}"
        ) from error


async def summarize_repository(
    file_reviews: list[dict],
) -> RepositorySummary:
    """
    Generate an overall repository-level summary
    from individual file review results.
    """

    prompt = f"""
You are a senior software engineer performing a repository-wide code review.

Analyze the following file review results and produce one overall repository summary.

Return ONLY valid JSON using exactly this structure:

{{
  "overall_quality": "string",
  "security_assessment": "string",
  "maintainability_assessment": "string",
  "top_risks": [
    "string"
  ],
  "top_recommendations": [
    "string"
  ]
}}

Rules:
- Do not include markdown.
- Do not include code fences.
- Do not add text outside the JSON.
- Keep top_risks to a maximum of 5 items.
- Keep top_recommendations to a maximum of 5 items.
- Base the summary only on the supplied review results.

File review results:

{json.dumps(file_reviews, indent=2)}
"""

    response = await client.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    raw_response = response["message"]["content"].strip()

    if raw_response.startswith("```json"):
        raw_response = raw_response.removeprefix("```json").strip()

    if raw_response.startswith("```"):
        raw_response = raw_response.removeprefix("```").strip()

    if raw_response.endswith("```"):
        raw_response = raw_response.removesuffix("```").strip()

    try:
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"The AI returned an invalid repository summary: {raw_response}"
        ) from error

    return RepositorySummary.model_validate(parsed_response)
