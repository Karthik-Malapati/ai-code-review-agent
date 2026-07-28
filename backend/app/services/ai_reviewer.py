import json
import os
from json import JSONDecodeError

from ollama import AsyncClient, ResponseError
from pydantic import ValidationError

from app.schemas.repository import RepositorySummary
from app.schemas.review import CodeReviewResult

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434",
)

MODEL_NAME = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5-coder:7b",
)

client = AsyncClient(
    host=OLLAMA_HOST,
    timeout=120.0,
)


async def review_code(
    code: str,
    language: str,
) -> CodeReviewResult:
    """
    Review source code using the local Ollama model.
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

    try:
        response = await client.chat(
            model=MODEL_NAME,
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
        raise RuntimeError("Ollama timed out while reviewing the code.") from error
    except Exception as error:
        raise RuntimeError("Unable to connect to the Ollama service.") from error

    raw_response = response["message"]["content"].strip()

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
        parsed_response = json.loads(raw_response)
    except JSONDecodeError as error:
        raise ValueError(
            f"The AI model returned invalid JSON: {raw_response}"
        ) from error

    try:
        return CodeReviewResult.model_validate(parsed_response)
    except ValidationError as error:
        print("\n===== INVALID AI RESPONSE =====")
        print(
            json.dumps(
                parsed_response,
                indent=2,
            )
        )
        print("\n===== PYDANTIC VALIDATION ERROR =====")
        print(error)
        print("====================================\n")

        raise ValueError("The AI returned JSON with an invalid structure.") from error


async def summarize_repository(
    file_reviews: list[dict],
) -> RepositorySummary:
    """
    Generate an overall repository-level summary.
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

    try:
        response = await client.chat(
            model=MODEL_NAME,
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
        raise RuntimeError(
            "Ollama timed out while generating the repository summary."
        ) from error
    except Exception as error:
        raise RuntimeError("Unable to connect to the Ollama service.") from error

    raw_response = response["message"]["content"].strip()

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
        parsed_response = json.loads(raw_response)
    except JSONDecodeError as error:
        raise ValueError(
            f"The AI returned an invalid repository summary: {raw_response}"
        ) from error

    try:
        return RepositorySummary.model_validate(parsed_response)
    except ValidationError as error:
        raise ValueError(
            "The AI returned a repository summary with an invalid structure."
        ) from error
