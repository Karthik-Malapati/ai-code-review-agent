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


async def call_ai(
    prompt: str,
    response_schema: str = "code_review",
) -> str:
    if AI_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        if openrouter_client is None:
            raise RuntimeError("OpenRouter client could not be initialized.")

        if response_schema == "repository_summary":
            json_schema = {
                "name": "repository_summary",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "overall_quality": {
                            "type": "string",
                        },
                        "security_assessment": {
                            "type": "string",
                        },
                        "maintainability_assessment": {
                            "type": "string",
                        },
                        "top_risks": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                            "maxItems": 5,
                        },
                        "top_recommendations": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                            "maxItems": 5,
                        },
                    },
                    "required": [
                        "overall_quality",
                        "security_assessment",
                        "maintainability_assessment",
                        "top_risks",
                        "top_recommendations",
                    ],
                    "additionalProperties": False,
                },
            }
        else:
            json_schema = {
                "name": "code_review",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                        },
                        "issues": {
                            "type": "array",
                            "maxItems": 3,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": [
                                            "CRITICAL",
                                            "HIGH",
                                            "MEDIUM",
                                            "LOW",
                                            "INFO",
                                        ],
                                    },
                                    "category": {
                                        "type": "string",
                                    },
                                    "line": {
                                        "type": [
                                            "integer",
                                            "null",
                                        ],
                                    },
                                    "title": {
                                        "type": "string",
                                    },
                                    "description": {
                                        "type": "string",
                                    },
                                    "recommendation": {
                                        "type": "string",
                                    },
                                },
                                "required": [
                                    "severity",
                                    "category",
                                    "line",
                                    "title",
                                    "description",
                                    "recommendation",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": [
                        "summary",
                        "issues",
                    ],
                    "additionalProperties": False,
                },
            }

        response = await openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": json_schema,
            },
            temperature=0.1,
            max_tokens=1200,
        )

        content = response.choices[0].message.content

        if content:
            return content.strip()

        retry_response = await openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        prompt + "\n\nIMPORTANT: Return ONLY valid JSON. "
                        "Do not include markdown or explanations."
                    ),
                }
            ],
            response_format={
                "type": "json_object",
            },
            temperature=0.1,
            max_tokens=1200,
        )

        retry_content = retry_response.choices[0].message.content

        if not retry_content:
            raise RuntimeError("OpenRouter returned an empty response after retry.")

        return retry_content.strip()

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
    except Exception as error:
        raise RuntimeError("Unable to connect to the Ollama service.") from error

    return response["message"]["content"].strip()


def clean_json_response(
    raw_response: str,
) -> dict:
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
- Return at most 3 issues.
- Keep each description under 40 words.
- Keep each recommendation under 30 words.
- Do not return metadata or extra fields.
- Never truncate strings.

Code:

{code}
"""

    raw_response = await call_ai(
        prompt,
        response_schema="code_review",
    )

    parsed_response = clean_json_response(raw_response)

    try:
        return CodeReviewResult.model_validate(parsed_response)
    except ValidationError as error:
        raise ValueError("The AI returned JSON with an invalid structure.") from error


async def summarize_repository(
    file_reviews: list[dict],
) -> RepositorySummary:
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

    raw_response = await call_ai(
        prompt,
        response_schema="repository_summary",
    )

    parsed_response = clean_json_response(raw_response)

    try:
        return RepositorySummary.model_validate(parsed_response)
    except ValidationError as error:
        raise ValueError(
            "The AI returned a repository summary with an invalid structure."
        ) from error
