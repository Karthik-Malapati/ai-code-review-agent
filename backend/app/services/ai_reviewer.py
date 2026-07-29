import json
from json import JSONDecodeError

from ollama import AsyncClient, ResponseError
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.core.config import (
    AI_PROVIDER,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)
from app.schemas.repository import RepositorySummary
from app.schemas.review import CodeReviewResult

ollama_client = AsyncClient(
    host=OLLAMA_HOST,
    timeout=120.0,
)

openrouter_client = None

if AI_PROVIDER == "openrouter" and OPENROUTER_API_KEY:
    openrouter_client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

MODEL_NAME = OPENROUTER_MODEL if AI_PROVIDER == "openrouter" else OLLAMA_MODEL


async def call_ai(prompt: str) -> str:
    """
    Send a prompt to the configured AI provider
    and return the raw text response.
    """

    if AI_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        response = await openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_format={
                "type": "json_object",
            },
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("OpenRouter returned an empty response.")

        return content.strip()

    try:
        response = await ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format="json",
        )
    except ResponseError as error:
        raise RuntimeError(f"Ollama returned an error: {error}") from error
    except TimeoutError as error:
        raise RuntimeError("Ollama request timed out.") from error
    except Exception as error:
        raise RuntimeError("Unable to connect to the Ollama service.") from error

    return response["message"]["content"].strip()


def clean_json_response(raw_response: str) -> dict:
    """
    Clean common model formatting and parse JSON.
    """

    raw_response = raw_response.strip()

    if raw_response.startswith("```json"):
        raw_response = raw_response.removeprefix("```json").strip()

    if raw_response.startswith("```"):
        raw_response = raw_response.removeprefix("```").strip()

    if raw_response.endswith("```"):
        raw_response = raw_response.removesuffix("```").strip()

    json_start = raw_response.find("{")
    json_end = raw_response.rfind("}")

    if json_start != -1 and json_end != -1:
        raw_response = raw_response[json_start : json_end + 1]

    try:
        return json.loads(raw_response)
    except JSONDecodeError as error:
        raise ValueError(f"The AI returned invalid JSON: {raw_response}") from error


async def review_code(
    code: str,
    language: str,
) -> CodeReviewResult:
    """
    Review source code using the configured AI provider.
    """

    prompt = f"""
You are a senior software engineer performing a code review.

Review the following {language} code.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": "string",
  "issues": [
    {{
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "category": "string",
      "line": null,
      "title": "string",
      "description": "string",
      "recommendation": "string"
    }}
  ]
}}

Rules:
- Return only valid JSON.
- Do not include markdown.
- Do not include code fences.
- Do not include explanations outside the JSON.
- If there are no issues, return an empty issues list.

Code:

{code}
"""

    raw_response = await call_ai(prompt)
    parsed_response = clean_json_response(raw_response)

    try:
        return CodeReviewResult.model_validate(parsed_response)
    except ValidationError as error:
        raise ValueError("The AI returned JSON with an invalid structure.") from error


async def summarize_repository(
    file_reviews: list[dict],
) -> RepositorySummary:
    """
    Generate a repository-level summary.
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
- Return only valid JSON.
- Do not include markdown.
- Do not include code fences.
- Do not add text outside the JSON.
- Keep top_risks to a maximum of 5 items.
- Keep top_recommendations to a maximum of 5 items.
- Base the summary only on the supplied review results.

File review results:

{json.dumps(file_reviews, indent=2)}
"""

    raw_response = await call_ai(prompt)
    parsed_response = clean_json_response(raw_response)

    try:
        return RepositorySummary.model_validate(parsed_response)
    except ValidationError as error:
        raise ValueError(
            "The AI returned a repository summary with an invalid structure."
        ) from error
